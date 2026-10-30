"""The observer's server: the world library, background jobs and HTTP (pages are in observer.py).

    python tools/observer.py [WORLD] [--worlds DIR] [--port 8765] [--open] [--workers N]

One world is open at a time. Pages are drawn on one thread (observer_jobs.Renderer) from the open world's
committed snapshot; long operations run as jobs (observer_jobs.Jobs), one at a time. Stop the observer with
Ctrl-C in its window or the Quit button: a running advance first stops after the week it is playing and
saves every completed week. Closing the window instead stops it at once: nothing is half-written (the
world stays at its last committed week; the unfinished advance is reported when the world is next opened).
"""
from __future__ import annotations

import argparse
import json
import os
import random
import shutil
import sys
import threading
import time
import traceback
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
import observer as O                                                 # noqa: E402
import observer_jobs as J                                            # noqa: E402
import observer_worlds as WL                                         # noqa: E402
from observer import esc                                             # noqa: E402

DEFAULT_LIBRARY = ROOT / 'worlds'


class App:
    """The observer: a world library, the open world (or none), and its jobs."""

    def __init__(self, library=DEFAULT_LIBRARY, workers=None):
        self.lib = Path(library)
        self.lib.mkdir(parents=True, exist_ok=True)
        self.workers = workers
        self.world = None                    # an observer.World (touched on the renderer thread only)
        self.jobs = J.Jobs()
        self.renderer = J.Renderer()
        self.notices = []                    # [(kind, html)] shown once on the next page
        self.seen_job = None
        self.quitting = threading.Event()

    # -- state for the pages --------------------------------------------------------------------------------
    def job(self):
        j = self.jobs.current
        return j.as_dict() if j is not None else None

    def status(self):
        j = self.job()
        w = self.world
        lv = getattr(w, 'live', None)
        return {'job': j, 'line': O.job_line(j) if j else '',
                'world': None if w is None else {'name': w.label, 'read_only': w.read_only,
                                                 'cursor': lv.cursor if lv else None,
                                                 'generation': lv.generation if lv else None}}

    def take_notices(self):
        """One-time banners: the result of an operation that finished since the last page."""
        out, self.notices = self.notices, []
        j = self.job()
        if j and j['state'] != 'running' and j['id'] != self.seen_job:
            self.seen_job = j['id']
            kind = {'done': 'ok', 'stopped': 'warn', 'refused': 'warn', 'failed': 'err'}[j['state']]
            text = esc(j['message'])
            if j['state'] == 'failed':
                text += (' <a href="/export">Report this problem</a> (a diagnostic copy of the world, with the log).'
                         if self.world is not None and not self.world.read_only else '')
            out.append((kind, f'<strong>{esc(j["title"])}</strong>: {text}'))
        return out

    # -- the world -----------------------------------------------------------------------------------------
    def _install(self, path, session=None, read_only=False, allow_other_engine=False):
        """(renderer thread) Make `path` the open world."""
        self._close_world()
        self.world = O.World(path, session=session, read_only=read_only, allow_other_engine=allow_other_engine)
        return self.world

    def _close_world(self):
        w, self.world = self.world, None
        if w is not None:
            w.close()

    def open_now(self, path, read_only=False):
        """Open a world here and now (the command line's WORLD argument)."""
        info = WL.inspect(path)
        allow = bool(info and info.get('accepted'))
        return self.renderer.call(self._install, Path(path), None, read_only, allow)

    def start(self, kind, title, fn, op=None, world_dir=None, cancellable=False):
        job = J.Job(kind, title, op_key=op, world_dir=world_dir, cancellable=cancellable)
        return self.jobs.start(job, fn)

    def advance(self, form):
        """Start an advance from a form. Returns a notice for the page, or None if it started (or is the
        running one)."""
        w = self.world
        if w is None or w.read_only:
            return ('warn', 'Open a world to advance it (this one is read-only).')
        run = self.jobs.running()
        op = O.one(form, 'op')
        if run is not None:
            if op and run.op_key == op:
                return None                                 # the same request again: show its progress
            return ('warn', f'{esc(run.title)} is still running: one operation at a time.')
        lv = w.live
        if O.one(form, 'world') not in (None, lv.world_id):
            return ('warn', 'That form belongs to another world: nothing was advanced.')
        plan, op = O.advance_plan(form, lv.cursor)
        weeks = sum(n for n, _ in plan)
        if O.one(form, 'weeks') == 'seasons':
            title = f'Advance {len(plan)} season{"s" if len(plan) != 1 else ""}'
        elif O.one(form, 'weeks') == 'season':
            title = 'Advance to the end of the season'
        else:
            title = {1: 'Advance one week', 4: 'Advance four weeks'}.get(weeks, f'Advance {weeks} weeks')
        self.start('advance', title, lambda job: self._run_advance(job, w, plan, op), op=op,
                   world_dir=w.path, cancellable=True)
        return None

    def _run_advance(self, job, w, plan, op):
        """Run an advance plan: one segment (committed once at its end), or one segment per season, each
        committed and published as its season ends, with the pages' snapshot refreshed between seasons."""
        from golfsim.session import Busy, StaleCursor
        total = sum(n for n, _ in plan)
        multi = len(plan) > 1
        job.update(total=total, phase='starting', seasons=len(plan) if multi else None, season=1)
        t0 = time.perf_counter()
        played, archived, applied = 0, [], 0
        s = w.session
        try:
            for i, (weeks, expected) in enumerate(plan):
                if job.cancel_requested:
                    break
                job.update(season=i + 1)
                with w.session_lock:
                    s = w.session
                    gen0 = s.generation
                    J.record_job(w.path, job, s.cursor, gen0)
                    left = weeks

                    def progress(r):
                        nonlocal left
                        left -= 1
                        phase = 'playing' if left and not job.cancel_requested else (
                            'saving the world and publishing the season' if 'season_end' in r['changes']
                            else 'saving the world')
                        job.update(done=job.done + 1, last=tuple(r['completed']), phase=phase)
                    try:
                        J.ensure_pool(s.season)
                        out = s.advance(weeks, progress=progress, cancel=lambda: job.cancel_requested,
                                        expected=expected, op_key=None if op is None else (f'{op}#{i}' if multi else op))
                    except StaleCursor:
                        if applied and applied == i:            # the earlier segments were this request, done before
                            break
                        job.finish('refused', f'This form was drawn at {O.date_text(expected)}, but the world is at '
                                              f'{O.date_text(s.cursor)}: nothing was advanced.')
                        return
                    except Busy:
                        job.finish('refused', 'Another program is advancing this world right now: nothing was advanced here.')
                        return
                    except Exception as e:
                        J.log(w.path, f'advance failed: {e!r}\n{traceback.format_exc()}')
                        before = (f'{played} week{"s" if played != 1 else ""} played and saved before this'
                                  + (f' (seasons {", ".join(map(str, archived))} archived)' if archived else '') + '. ')
                        if s.generation != gen0:                # committed; only publishing its history failed
                            job.finish('failed', before * bool(played) + f'The advance was saved: the world is at '
                                       f'{O.date_text(s.cursor)} (generation {s.generation}). Publishing its history '
                                       f'failed ({type(e).__name__}: {e}); it is kept in the saved world and published '
                                       'again when the world is next opened or advanced.')
                        else:
                            job.finish('failed', f'{type(e).__name__}: {e}. ' + before * bool(played) + 'The weeks being '
                                       f'played were not kept: the world is at its last committed week, '
                                       f'{O.date_text(s.cursor)} (generation {s.generation}).')
                        return
                    if out and s.generation == gen0:
                        applied += 1                            # a repeat of a segment already committed
                    else:
                        played += len(out)
                        archived += [r['completed'][0] for r in out if 'season_end' in r['changes']]
                if multi and i < len(plan) - 1 and not job.cancel_requested:
                    job.update(phase='refreshing the pages')
                    try:
                        self.renderer.call(w.reload)            # browse the season just saved meanwhile
                    except Exception as e:
                        J.log(w.path, f'refresh between seasons failed: {e!r}')
        finally:
            J.clear_job(w.path)
        el = time.perf_counter() - t0
        s = w.session
        where = f'Now at {O.date_text(s.cursor)} (generation {s.generation}).'
        seasons = (f'; season{"s" if len(archived) != 1 else ""} {archived[0]}' +
                   (f'–{archived[-1]}' if len(archived) > 1 else '') + ' archived') if archived else ''
        if not played and applied:
            job.finish('done', f'Already applied (this request had been completed): the world is at {O.date_text(s.cursor)}.')
        elif job.cancel_requested and played < total:
            job.finish('stopped', f'Stopped at your request after {played} of {total} weeks{seasons}; every completed '
                                  f'week is saved. {where}')
        else:
            job.finish('done', f'{played} week{"s" if played != 1 else ""} played and saved in {el:.0f} s{seasons}. {where}')

    # -- library operations (each a job) --------------------------------------------------------------------
    def create(self, form):
        try:
            d = WL.check_name(self.lib, O.one(form, 'name'))
            seed = O.one(form, 'seed')
            seed = int(seed) if seed not in (None, '') else random.randrange(1, 1000000)
            if not 0 <= seed < 2 ** 31:
                raise ValueError('The seed must be a whole number from 0 to 2147483647.')
            start = int(O.one(form, 'start_year') or 2027)
            if not 1900 <= start <= 2200:
                raise ValueError('The starting year must be from 1900 to 2200.')
            from golfsim import schedule as SCH
            calendar = O.one(form, 'calendar') or SCH.DEFAULT
            if calendar not in SCH.SPECS:
                raise ValueError('Unknown calendar version.')
        except (ValueError, FileExistsError) as e:
            return ('err', esc(e))

        def run(job):
            from golfsim.population import generate_world
            from golfsim.session import Session
            job.update(phase='generating the world and its population')
            s = Session.create(d, seed=seed, workers=self.workers, world=generate_world(year=start, seed=seed),
                               calendar=calendar)
            WL.record_creation(d, seed, start, calendar)
            J.log(d, f'created with seed {seed}, starting in {start}, calendar {calendar}')
            job.update(phase='opening')
            self.renderer.call(self._install, d, s)
            job.finish('done', f'World “{d.name}” created (seed {seed}, starting {start}) at {O.date_text(s.cursor)}.')
        _, started = self.start('create', f'Create world “{d.name}”', run, world_dir=None)
        return None if started else ('warn', 'Another operation is running: one at a time.')

    def open(self, form, read_only=False):
        name = O.one(form, 'name') or ''
        d = self.lib / name
        info = WL.inspect(d) if d.is_dir() and '/' not in name and '\\' not in name else None
        if info is None:
            return ('err', 'No such world.')
        if not read_only and not info['can_resume']:
            return ('err', 'This world cannot be resumed with this engine. Browse its history read-only, or make a copy '
                           'to continue it with this engine.')

        def run(job):
            if read_only or info['kind'] == 'archive':
                job.update(phase='reading the history')
                self.renderer.call(self._install, d, None, True)
                job.finish('done', f'“{d.name}” open read-only: its published history only, nothing can change it.')
                return
            from golfsim.session import Session
            job.update(phase='loading the committed world (and recovering if an advance was interrupted)')
            self.renderer.call(self._close_world)
            s = Session.open(d, workers=self.workers, allow_other_engine=info.get('accepted') is not None)
            job.update(phase='reading its history')
            w = self.renderer.call(self._install, d, s)
            extra = ''
            if w.interrupted:
                extra = (f' An advance started {w.interrupted.get("started")} did not finish (the observer stopped while it '
                         'ran): the weeks being played then were not kept; everything saved before that is here.')
            job.finish('done', f'“{d.name}” open at {O.date_text(s.cursor)} (generation {s.generation}).{extra}')
        _, started = self.start('open', f'Open “{name}”' + (' read-only' if read_only else ''), run,
                                world_dir=None if read_only else d)
        return None if started else ('warn', 'Another operation is running: one at a time.')

    def copy(self, form):
        name = O.one(form, 'name') or ''
        src = self.lib / name
        info = WL.inspect(src) if src.is_dir() and '/' not in name and '\\' not in name else None
        if info is None:
            return ('err', 'No such world.')
        try:
            dst = WL.check_name(self.lib, O.one(form, 'new_name'))
        except (ValueError, FileExistsError) as e:
            return ('err', esc(e))
        accept = O.one(form, 'accept_engine') == 'yes'

        def run(job):
            w = self.world
            same = w is not None and w.path == src and not w.read_only
            if same:
                with w.session_lock:                          # nothing of ours advances it meanwhile
                    WL.copy_world(src, dst, job, accept_engine=accept)
            else:
                WL.copy_world(src, dst, job, accept_engine=accept)
            job.finish('done', f'Copied “{src.name}” to “{dst.name}”' + (
                ' (to be continued with this engine)' if accept else '') + '. The original is unchanged.')
        _, started = self.start('copy', f'Copy “{src.name}” to “{dst.name}”', run, world_dir=None)
        return None if started else ('warn', 'Another operation is running: one at a time.')

    def export(self, form):
        w = self.world
        name = O.one(form, 'name') or (w.label if w else '')
        src = (w.path if w is not None and w.label == name else self.lib / name)
        if WL.inspect(src) is None:
            return ('err', 'No such world.')
        last = self.job()

        def run(job):
            kw = dict(note=O.one(form, 'note', ''), steps=O.one(form, 'steps', ''), expected=O.one(form, 'expected', ''),
                      include_index=O.one(form, 'index') == 'yes', include_previous=O.one(form, 'previous') == 'yes',
                      job=job, last_job=last)
            if w is not None and w.path == src and not w.read_only:
                with w.session_lock:
                    out = WL.export_diagnostic(src, self.lib / WL.DIAGNOSTICS, **kw)
            else:
                out = WL.export_diagnostic(src, self.lib / WL.DIAGNOSTICS, **kw)
            job.result = out.name
            job.finish('done', f'Diagnostic package written: {out} ({out.stat().st_size / 1e6:,.1f} MB). '
                               'Nothing was uploaded; share it yourself if you want us to look.')
        _, started = self.start('export', f'Export a diagnostic copy of “{Path(src).name}”', run, world_dir=src)
        return None if started else ('warn', 'Another operation is running: one at a time.')

    def remove(self, form):
        """Remove a world from the library into the trash (restorable). Never the open world, never while an
        operation runs."""
        name = O.one(form, 'name') or ''
        if O.one(form, 'confirm') != 'yes':
            return ('warn', 'Tick the box to confirm removing the world.')
        if self.jobs.running():
            return ('warn', 'Wait for the running operation to finish (or stop it) first.')
        if self.world is not None and self.world.path == self.lib / name:
            return ('warn', 'Close the world before removing it.')
        try:
            dst = self.renderer.call(WL.remove_world, self.lib, name)
        except (ValueError, OSError) as e:
            return ('err', esc(e))
        return ('ok', f'“{esc(name)}” moved to the trash ({esc(dst.name)}): restore it below, or delete it permanently.')

    def restore(self, form):
        if self.jobs.running():
            return ('warn', 'Wait for the running operation to finish first.')
        try:
            dst = self.renderer.call(WL.restore_world, self.lib, O.one(form, 'folder') or '')
        except (ValueError, OSError) as e:
            return ('err', esc(e))
        return ('ok', f'“{esc(dst.name)}” restored.')

    def purge(self, form):
        if self.jobs.running():
            return ('warn', 'Wait for the running operation to finish first.')
        try:
            name = self.renderer.call(WL.delete_permanently, self.lib, O.one(form, 'folder') or '',
                                      (O.one(form, 'typed') or '').strip())
        except (ValueError, OSError) as e:
            return ('err', esc(e))
        return ('ok', f'“{esc(name)}” deleted permanently from disk.')

    def unlock(self, form):
        """Remove a lock left by a program that no longer runs (the owner asked, after confirming that no other
        Golf Legacy window is open). Never this observer's own lock."""
        name = O.one(form, 'name') or ''
        d = self.lib / name
        if not (d / 'lock').exists() or '/' in name or '\\' in name:
            return ('warn', 'That world is not locked.')
        if O.one(form, 'confirm') != 'yes':
            return ('warn', 'Tick the box to confirm that no other Golf Legacy window is using this world.')
        text = (d / 'lock').read_text().strip()
        from golfsim.session import _lock_owner
        if text == _lock_owner() or self.jobs.running():
            return ('warn', 'This observer is using that world: wait for its operation to finish.')
        aside = d / f'lock.released.{int(time.time())}'
        os.replace(d / 'lock', aside)
        aside.unlink()
        J.log(d, f'lock released by the owner (it named process {text})')
        return ('ok', f'Lock on “{esc(name)}” released (it named process {esc(text)}).')

    def close(self):
        if self.jobs.running():
            return ('warn', 'Wait for the running operation to finish (or stop it) first.')
        self.renderer.call(self._close_world)
        return ('ok', 'World closed. Everything committed is saved.')

    def shutdown(self, wait=True):
        """Stop at a safe boundary: a running advance stops after its week and saves; others finish."""
        run = self.jobs.running()
        if run is not None:
            if run.cancellable:
                run.update(cancel_requested=True, phase='stopping at the end of this week')
            if wait:
                self.jobs.wait()
        try:
            self.renderer.call(self._close_world)
        finally:
            self.renderer.stop()

    # -- pages -------------------------------------------------------------------------------------------------
    def draw(self, path, q=None):
        """(renderer thread) The HTML of a page: None if it needs an open world, 404 if there is none."""
        q = q or {}
        notices = self.take_notices()
        w = self.world
        job = self.job()
        if path == '/worlds':
            return O.page(w, *self.library_page(q), job=job, notices=notices)
        if path == '/export':
            return O.page(w, *self.export_page(q), job=job, notices=notices)
        if path == '/job':
            return O.page(w, *self.job_page(q), job=job, notices=notices)
        if w is None:
            self.notices[:0] = notices                  # not shown yet
            return None
        try:
            q, note = O.V.opened(w, path, q)          # a list page: its last view (browsing state only)
            r = O.render(w, path, q)
            if r is not None and O.V.is_list(path):
                r = (r[0], note + O.V.bar(w, path, q) + r[1])
            elif r is not None:
                r = (r[0], O.V.back_link(w, path) + r[1])
        except Exception as e:
            J.log(w.path, f'page {path} failed: {e!r}\n{traceback.format_exc()}')
            r = ('Something went wrong', f'<div class="banner err">{esc(type(e).__name__)}: {esc(e)}</div>'
                 '<p>The page could not be drawn; the world is unchanged. The error is in the world’s log '
                 '(<a href="/export">report a problem</a> includes it).</p>')
        if r is None:
            return 404
        return O.page(w, *r, job=job, notices=notices)

    def library_page(self, q):
        worlds = WL.list_worlds(self.lib)
        engine, commit = WL.engine_now()
        out = [f'<p>Worlds are folders in <code>{esc(self.lib)}</code>. This engine: <code>{esc(engine[:12])}</code> '
               f'(commit <code>{esc((commit or "")[:10])}</code>). Saves: format {esc(O_session_format())}.</p>']
        rows = []
        for i in worlds:
            name = esc(i['name'])
            if i['kind'] == 'archive':
                state, date = 'history archive (read-only)', (span(i['years']) if i['years'] else '—')
                compat = '<span class="tag">browse only</span>'
            else:
                date = O.date_text(i['cursor']) if i.get('cursor') else '?'
                if not i['format_ok']:
                    compat = f'<span class="tag">unsupported save {esc(i.get("format"))} schema {esc(i.get("schema"))}</span>'
                elif i['same_engine']:
                    compat = '<span class="tag">this engine</span>'
                elif i['accepted']:
                    compat = (f'<span class="tag">continued with this engine</span> <span class="muted">saved by '
                              f'{esc((i["accepted"].get("saved_by_commit") or "")[:10])}</span>')
                else:
                    compat = (f'<span class="tag">other engine</span> <span class="muted">commit '
                              f'{esc((i.get("commit") or "?")[:10])}</span>')
                state = f'generation {esc(i.get("generation"))}, {esc(i.get("weeks_played"))} weeks played'
                if i['years']:
                    state += f'; {span(i["years"])} archived'
                if i['busy']:
                    state += (' · <span class="tag">locked: being advanced by another program</span>'
                              f'<form method="post" action="/worlds/unlock" class="filters"><input type="hidden" '
                              f'name="name" value="{name}"><label class="muted"><input type="checkbox" name="confirm" '
                              'value="yes" required> no other Golf Legacy window is open</label><button>Release the '
                              'lock</button></form>')
                if i['interrupted']:
                    state += ' · <span class="tag">an advance did not finish</span>'
            hidden = f'<input type="hidden" name="name" value="{name}">'
            acts = []
            if i.get('can_resume'):
                acts.append(f'<form method="post" action="/worlds/open">{hidden}<button class="primary">Open</button></form>')
            if i['years'] or i['kind'] == 'archive':
                acts.append(f'<form method="post" action="/worlds/browse">{hidden}<button>Browse history</button></form>')
            other = i['kind'] == 'session' and not i['same_engine'] and not i['accepted'] and i['format_ok']
            acts.append(f'<form method="post" action="/worlds/copy">{hidden}<input name="new_name" required '
                        f'aria-label="Name of the copy" placeholder="name of the copy" size="14" value="{name} copy">'
                        + ('<label class="muted"><input type="checkbox" name="accept_engine" value="yes" required> continue '
                           'with this engine</label>' if other else '') + '<button>Copy</button></form>')
            acts.append(f'<a class="button" href="/export?name={quote(i["name"])}">Report a problem</a>')
            if not (self.world is not None and self.world.path == i['path']):
                acts.append(f'<form method="post" action="/worlds/remove">{hidden}<label class="muted"><input type="checkbox" '
                            'name="confirm" value="yes" required> remove</label><button title="Moves it to the trash: it can '
                            'be restored">Remove…</button></form>')
            seed = i.get('seed')
            rows.append([f'<strong>{name}</strong>' + (' <span class="tag">open</span>' if self.world is not None
                                                       and self.world.path == i['path'] else ''),
                         esc(date), esc(seed if seed is not None else '—'), esc(i.get('start_year') or '—'), compat, state,
                         '<div class="filters">'
                         + ''.join(acts) + '</div>'])
        out.append(O.table(['World', 'Date', 'Seed', 'Start', 'Compatibility', 'State', ''], rows) if rows else
                   '<p class="muted">No worlds yet: create one below.</p>')
        out.append('<p class="muted">A world saved by another engine cannot be resumed in place: browse its history, or '
                   'tick “continue with this engine” to copy it and continue the copy (the copy records which engine '
                   'saved it). The original is never changed.</p>')
        out.append('<h2>Create a world</h2><form method="post" action="/worlds/create" class="filters">'
                   '<label>Name<input name="name" required placeholder="my world"></label>'
                   '<label>Starting year<input name="start_year" type="number" min="1900" max="2200" value="2027"></label>'
                   f'<label>Seed<input name="seed" type="number" min="0" max="2147483647" value="{random.randrange(1, 1000000)}">'
                   '</label><label>Calendar<select name="calendar"><option value="v2" selected>Reference (majors weeks '
                   '15, 20, 25, 30)</option><option value="v1">Classic (majors weeks 18, 24, 25, 30)</option></select>'
                   '</label><button class="primary">Create</button></form>'
                   '<p class="muted">The starting year is the first season’s calendar year (golfers’ ages are set '
                   'from it); the seed is separate. The seed is the world’s starting point: the same seed always makes the same world -- the '
                   'same golfers and, shot for shot, the same history (that is what makes a problem report replayable). '
                   'A new seed is suggested each time; type an earlier world’s seed (shown in the library) to make that '
                   'world again. The whole world is generated: every nation, golfer, coach and caddie. Calendar: new '
                   'worlds play the reference calendar (roadmap v14); the classic calendar is the one earlier worlds '
                   'were played on (for comparison). A world keeps its calendar for good.</p>')
        trash = WL.trashed(self.lib)
        if trash:
            out.append('<h2>Removed worlds (trash)</h2>' + O.table(['World', 'Removed', 'Size', ''], [
                [esc(name), esc(when), f'{mb:,.0f} MB',
                 f'<div class="filters"><form method="post" action="/worlds/restore"><input type="hidden" name="folder" '
                 f'value="{esc(folder)}"><button>Restore</button></form><form method="post" action="/worlds/purge">'
                 f'<input type="hidden" name="folder" value="{esc(folder)}"><input name="typed" required size="14" '
                 f'placeholder="type its name" aria-label="Type the world name to delete it permanently">'
                 '<button>Delete permanently</button></form></div>'] for folder, name, when, mb in trash])
                + '<p class="muted">Removing only moves a world here; it is deleted from disk only by “Delete permanently” '
                  'with its name typed.</p>')
        if self.world is not None:
            out.append('<form method="post" action="/worlds/close"><button>Close the open world</button></form>')
        out.append('<h2>Stop the observer</h2><form method="post" action="/quit"><button>Quit</button></form>'
                   '<p class="muted">Quit stops a running advance after the week it is playing and saves every '
                   'completed week, then closes the program. Reopen it with RUN_OBSERVER_WINDOWS.bat.</p>')
        return 'World library', ''.join(out)

    def export_page(self, q):
        w = self.world
        name = O.one(q, 'name') or (w.label if w else '')
        diags = sorted((self.lib / WL.DIAGNOSTICS).glob('*.zip'), reverse=True) if (self.lib / WL.DIAGNOSTICS).exists() else []
        out = [f'<p>Makes a diagnostic package of <strong>{esc(name) or "(choose a world in the library)"}</strong>: '
               'the committed save, every history file it depends on, the log, versions and your notes, in one zip in '
               f'<code>{esc(self.lib / WL.DIAGNOSTICS)}</code>. Nothing is uploaded and the world is not changed. Keep the '
               'world as it is until we have looked.</p>']
        if name:
            d = w.path if w is not None and w.label == name else self.lib / name
            idx = next((x for x in (d / 'archive' / 'index.sqlite', d / 'index.sqlite') if x.exists()), None)
            idx_mb = f'{idx.stat().st_size / 1e6:,.0f} MB' if idx else 'none'
            out.append(f'<form method="post" action="/export"><input type="hidden" name="name" value="{esc(name)}">'
                       '<p><label>What happened<textarea name="note" required></textarea></label></p>'
                       '<p><label>Steps to reproduce<textarea name="steps"></textarea></label></p>'
                       '<p><label>What you expected<textarea name="expected"></textarea></label></p>'
                       '<p><label><input type="checkbox" name="index" value="yes"> include the history index '
                       f'({idx_mb}; optional: rebuilt from the season files when missing)</label><br>'
                       '<label><input type="checkbox" name="previous" value="yes">'
                       ' include the last known good checkpoint (optional)</label></p>'
                       '<button class="primary">Write the package</button></form>')
        if diags:
            out.append('<h2>Packages written</h2><ul>' + ''.join(
                f'<li><a href="/download/{quote(p.name)}">{esc(p.name)}</a> ({p.stat().st_size / 1e6:,.1f} MB)</li>'
                for p in diags[:20]) + '</ul>')
        return 'Report a problem', ''.join(out)

    def job_page(self, q):
        j = self.job()
        if j is None:
            return 'Last operation', '<p class="muted">Nothing has run since the observer started.</p>'
        return 'Last operation', ('<dl class="kv">' + ''.join(f'<dt>{esc(k)}</dt><dd>{esc(v)}</dd>' for k, v in (
            ('Operation', j['title']), ('State', j['state']), ('Progress', O.job_line(j) if j['state'] == 'running' else
                                                                 f'{j["done"]} of {j["total"]} weeks' if j['total'] else ''),
            ('Message', j['message']), ('Elapsed', f'{j["elapsed"]:.0f} s'))) + '</dl>')


def span(years):
    return f'season {years[0]}' if len(years) == 1 else f'seasons {years[0]}–{years[-1]}'


def O_session_format():
    from golfsim.session import FORMAT, SCHEMA
    return f'{FORMAT} schema {SCHEMA}'


WORLD_FREE = {'/worlds', '/export', '/job'}


def make_handler(app):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, code, body, ctype='text/html; charset=utf-8', headers=()):
            data = body.encode() if isinstance(body, str) else body
            self.send_response(code)
            self.send_header('Content-Type', ctype)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            for k, v in headers:
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(data)

        def _redirect(self, to):
            self.send_response(303)
            self.send_header('Location', to)
            self.send_header('Content-Length', '0')
            self.end_headers()

        def _page(self, path, q):
            out = app.renderer.call(app.draw, path, q)
            if out is None:
                return self._redirect('/worlds')
            if out == 404:
                return self._send(404, O.page(app.world, 'Not found', '<p>No such page.</p>'))
            self._send(200, out)

        def _local(self):
            """Only this computer's browser, on this observer's own pages: the Host must be local (no DNS
            rebinding) and a form must come from the observer itself (another web site cannot post here)."""
            host = (self.headers.get('Host') or '').rsplit(':', 1)[0].strip('[]')
            if host not in ('localhost', '127.0.0.1', '::1'):
                return False
            origin = self.headers.get('Origin')
            if self.command == 'POST' and origin and origin != 'null':
                o = urlparse(origin)
                return o.hostname in ('localhost', '127.0.0.1', '::1') and o.port == self.server.server_address[1]
            return True

        def do_GET(self):
            u = urlparse(self.path)
            q = parse_qs(u.query)
            if not self._local():
                return self._send(403, 'forbidden', 'text/plain')
            try:
                if u.path == '/api/status':
                    return self._send(200, json.dumps(app.status()), 'application/json')
                if u.path.startswith('/download/'):
                    name = Path(u.path.split('/', 2)[2]).name
                    p = app.lib / WL.DIAGNOSTICS / name
                    if not name.endswith('.zip') or not p.is_file():
                        return self._send(404, 'not found', 'text/plain')
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/zip')
                    self.send_header('Content-Length', str(p.stat().st_size))
                    self.send_header('Content-Disposition', f'attachment; filename="{name}"')
                    self.end_headers()
                    with open(p, 'rb') as f:
                        shutil.copyfileobj(f, self.wfile)
                    return
                if u.path == '/favicon.ico':
                    return self._send(404, '', 'text/plain')
                self._page(u.path, q)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def do_POST(self):
            u = urlparse(self.path)
            if not self._local():
                return self._send(403, 'forbidden', 'text/plain')
            n = int(self.headers.get('Content-Length', 0) or 0)
            form = parse_qs(self.rfile.read(n).decode())
            try:
                to, notice = '/', None
                if u.path == '/advance':
                    notice = app.renderer.call(app.advance, form)
                elif u.path == '/cancel':
                    if not app.jobs.cancel(O.one(form, 'job')):
                        notice = ('warn', 'Nothing to stop: the operation had already finished.')
                elif u.path == '/worlds/create':
                    notice, to = app.create(form), '/'
                elif u.path == '/worlds/open':
                    notice, to = app.open(form), '/'
                elif u.path == '/worlds/browse':
                    notice, to = app.open(form, read_only=True), '/'
                elif u.path == '/worlds/copy':
                    notice, to = app.copy(form), '/worlds'
                elif u.path == '/worlds/remove':
                    notice, to = app.remove(form), '/worlds'
                elif u.path == '/worlds/restore':
                    notice, to = app.restore(form), '/worlds'
                elif u.path == '/worlds/purge':
                    notice, to = app.purge(form), '/worlds'
                elif u.path == '/shortlist':
                    w = app.world
                    ok = app.renderer.call(O.set_shortlist, w, O.one(form, 'kind'), O.one(form, 'id'), O.one(form, 'on') == '1')
                    if not ok:
                        notice = ('warn', 'Open a world (not only its history) to keep a shortlist.')
                    ref = self.headers.get('Referer') or ''
                    to = (urlparse(ref).path + ('?' + urlparse(ref).query if urlparse(ref).query else '')) if ref else '/shortlist'
                elif u.path in ('/shortlist/group', '/my-world/read', '/my-world/dismiss'):   # My World (browsing only)
                    w = app.world
                    to = '/my-world'
                    if w is None or w.read_only:
                        notice = ('warn', 'Open a world (not only its history) to follow people and events.')
                    elif u.path == '/my-world/read':
                        app.renderer.call(O.mark_read, w)
                    elif u.path == '/my-world/dismiss':
                        app.renderer.call(O.dismiss_hidden_period, w)
                    else:
                        app.renderer.call(O.set_shortlist, w, O.one(form, 'kind'), O.one(form, 'id'), True,
                                          O.one(form, 'group') or '')
                elif u.path in ('/views/save', '/views/remove', '/views/last'):   # browsing state only
                    w = app.world
                    ref = self.headers.get('Referer') or ''
                    to = (urlparse(ref).path + ('?' + urlparse(ref).query if urlparse(ref).query else '')) if ref else '/views'
                    if w is None:
                        notice = ('warn', 'Open a world first.')
                    elif u.path == '/views/last':
                        app.renderer.call(O.V.remember, w, O.one(form, 'url'))
                        return self._send(204, '', 'text/plain')
                    elif u.path == '/views/save':
                        ok = app.renderer.call(O.V.save, w, O.one(form, 'name'), O.one(form, 'path') or '',
                                               O.one(form, 'query') or '')
                        notice = ('ok', 'View saved.') if ok else ('warn', 'Only a list page’s view can be saved.')
                    else:
                        app.renderer.call(O.V.remove, w, O.one(form, 'id'))
                elif u.path == '/worlds/unlock':
                    notice, to = app.unlock(form), '/worlds'
                elif u.path == '/worlds/close':
                    notice, to = app.close(), '/worlds'
                elif u.path == '/export':
                    notice, to = app.export(form), '/export'
                elif u.path == '/quit':
                    self._send(200, O.page(None, 'Stopping', '<p>The observer is stopping (a running advance first '
                                                             'finishes its week and saves). You can close this tab.</p>'))
                    threading.Thread(target=app.quitting.set, daemon=True).start()
                    return
                else:
                    return self._send(404, 'not found', 'text/plain')
                if notice:
                    app.renderer.call(app.notices.append, notice)
                    if notice[0] == 'err' and to == '/':
                        to = '/worlds'
                ref = self.headers.get('Referer') or ''
                if u.path in ('/advance', '/cancel') and ref:
                    to = urlparse(ref).path + (('?' + urlparse(ref).query) if urlparse(ref).query else '')
                self._redirect(to)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def log_message(self, *args):
            pass
    return Handler


def start_server(app, port=8765):
    """Serve app on 127.0.0.1 (the first free port from `port`; 0: any) in a background thread."""
    httpd = None
    for p in ([0] if port == 0 else range(port, port + 10)):
        try:
            httpd = ThreadingHTTPServer(('127.0.0.1', p), make_handler(app))
            break
        except OSError:
            continue
    if httpd is None:
        raise SystemExit(f'No free port between {port} and {port + 9}: is the observer already running?')
    httpd.daemon_threads = True
    threading.Thread(target=httpd.serve_forever, name='http', daemon=True).start()
    return httpd


def serve(app, port=8765, open_browser=False):
    """Serve until Ctrl-C or Quit; returns the port used."""
    httpd = start_server(app, port)
    url = f'http://localhost:{httpd.server_address[1]}/'
    print(f'Golf Legacy observer: {url}  (worlds in {app.lib})')
    print('Stop it with Ctrl-C here, or the Quit button in the World library.', flush=True)
    if open_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        while not app.quitting.wait(0.5):
            pass
    except KeyboardInterrupt:
        pass
    run = app.jobs.running()
    if run is not None:
        print(f'Stopping: {run.title} ' + ('stops after the week it is playing and saves every completed week…'
                                           if run.cancellable else 'is finishing…'), flush=True)
    try:
        app.shutdown(wait=True)
    except KeyboardInterrupt:
        print('Stopped at once: the world is at its last committed week.', flush=True)
        os._exit(1)
    httpd.shutdown()
    httpd.server_close()
    print('The observer has stopped. Everything committed is saved.', flush=True)
    return httpd.server_address[1]


def main(argv=None):
    # Worker processes are started fresh ('spawn', as on Windows), not forked from this server: a forked
    # worker would inherit the server's threads' locks and its listening socket, and outlive it holding
    # the port if the server were killed. Results do not depend on how workers start.
    import multiprocessing
    multiprocessing.set_start_method('spawn', force=True)
    ap = argparse.ArgumentParser(description='Golf Legacy observer')
    ap.add_argument('path', nargs='?', help='a world (session directory) or a history archive to open now')
    ap.add_argument('--worlds', default=str(DEFAULT_LIBRARY), help='the world library folder (default: worlds/)')
    ap.add_argument('--port', type=int, default=8765)
    ap.add_argument('--workers', type=int, default=None, help='simulation worker processes (default: the engine\'s)')
    ap.add_argument('--open', action='store_true', help='open the browser')
    ap.add_argument('--read-only', action='store_true', help='open PATH read-only (its history only)')
    a = ap.parse_args(argv)
    app = App(a.worlds, workers=a.workers)
    if a.path:
        print(f'Opening {a.path} …', flush=True)
        app.open_now(a.path, read_only=a.read_only)
    serve(app, a.port, a.open)


if __name__ == '__main__':
    main()
