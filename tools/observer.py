"""Golf Legacy observer (alpha): create, open and advance worlds, and explore their history, in a web browser.

    python tools/observer.py                       # the world library (worlds/), at http://localhost:8765
    python tools/observer.py --open                # the same, and open the browser (RUN_OBSERVER_WINDOWS.bat)
    python tools/observer.py worlds/demo           # open one world directly (a session directory)
    python tools/observer.py path/to/archive       # or browse any history archive (read-only)

Standard library only (http.server, the session, the archive and its index); local only (127.0.0.1).
Pages are server-rendered HTML with plain links, so every person, edition, tournament, course, nation and
tour links to its page and the browser's Back button keeps filters.

How it stays safe (docs/UI_REQUIREMENTS_V1.md, "Observer alpha"):
- Every page is drawn from one committed generation: a snapshot of the committed world (observer_live)
  and the history published with it. Pages never read the world while it is being advanced.
- Advances (one week, four weeks, to the end of the season) run as background jobs, one at a time, with
  a progress display and a Stop button that stops after the current week and keeps every completed week.
  A form carries the world, the date it was drawn at and a one-time key, so a double click, a refresh or
  a resubmitted form never advances twice, and a form drawn before another advance advances nothing.
- A failed advance reports its error and leaves the world at its last committed week; an advance cut
  short by the observer stopping is reported the next time the world is opened.
"""
from __future__ import annotations

import argparse
import html
import json
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlencode, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
from golfsim.archive import Archive, ArchiveChanged, published_stamp  # noqa: E402
from golfsim.history_stats import BOARDS, DEFINITIONS, SCOPES, HistoryStats, board   # noqa: E402
import observer_jobs as J                                            # noqa: E402
from observer_live import capture                                    # noqa: E402

PAGE_SIZE = 100

CSS = """
:root { --bg:#fbfaf7; --fg:#1d2420; --muted:#5c6660; --line:#d9dcd6; --accent:#1f6b45; --panel:#ffffff;
  --warn-bg:#fff4d6; --warn-fg:#5a4300; --err-bg:#fde4e1; --err-fg:#7a1b12; --ok-bg:#e3f3e8; --ok-fg:#14502f; }
@media (prefers-color-scheme: dark) { :root { --bg:#141816; --fg:#e8ece9; --muted:#9aa59f; --line:#2c3430;
  --accent:#6fcf9d; --panel:#1b201d; --warn-bg:#3a3010; --warn-fg:#f3dc8f; --err-bg:#401a16; --err-fg:#f4b4ab;
  --ok-bg:#163223; --ok-fg:#a8e3c0; } }
* { box-sizing: border-box; }
body { margin:0; background:var(--bg); color:var(--fg); font:15px/1.5 system-ui, -apple-system, Segoe UI, sans-serif; }
header { display:flex; gap:12px 16px; align-items:center; padding:10px 16px; border-bottom:1px solid var(--line);
  background:var(--panel); position:sticky; top:0; flex-wrap:wrap; z-index:1; }
header .date { font-weight:600; }
header form { margin:0; display:flex; gap:6px; flex-wrap:wrap; align-items:center; }
nav { width:200px; flex:none; padding:12px 16px; border-right:1px solid var(--line); min-height:100vh; }
nav h4 { margin:14px 0 4px; font-size:12px; text-transform:uppercase; letter-spacing:.05em; color:var(--muted); }
nav a { display:block; padding:2px 0; }
.layout { display:flex; }
main { padding:16px 24px; flex:1; min-width:0; max-width:1150px; }
a { color:var(--accent); text-decoration:none; } a:hover { text-decoration:underline; }
a:focus-visible, button:focus-visible, input:focus-visible, select:focus-visible { outline:2px solid var(--accent); outline-offset:2px; }
.scroll { overflow-x:auto; }
table { border-collapse:collapse; width:100%; margin:8px 0 18px; }
th, td { text-align:left; padding:4px 8px; border-bottom:1px solid var(--line); vertical-align:top; }
th { font-size:12px; text-transform:uppercase; letter-spacing:.04em; color:var(--muted); }
td.n, th.n { text-align:right; font-variant-numeric:tabular-nums; }
.muted { color:var(--muted); } .tag { font-size:12px; border:1px solid var(--line); border-radius:4px; padding:0 4px; white-space:nowrap; }
button, .button { font:inherit; padding:4px 10px; border:1px solid var(--line); background:var(--panel); color:var(--fg);
  border-radius:4px; cursor:pointer; display:inline-block; }
button.primary { border-color:var(--accent); }
button:disabled { opacity:.5; cursor:default; }
input, select, textarea { font:inherit; padding:4px 8px; border:1px solid var(--line); border-radius:4px; background:var(--panel); color:var(--fg); }
textarea { width:100%; min-height:5em; }
.banner { padding:8px 12px; border-radius:4px; margin:8px 0 12px; border:1px solid var(--line); }
.banner.warn { background:var(--warn-bg); color:var(--warn-fg); } .banner.err { background:var(--err-bg); color:var(--err-fg); }
.banner.ok { background:var(--ok-bg); color:var(--ok-fg); }
.filters { display:flex; flex-wrap:wrap; gap:8px; align-items:end; margin:8px 0; }
.filters label { display:flex; flex-direction:column; font-size:12px; color:var(--muted); }
.tabs { display:flex; gap:4px; border-bottom:1px solid var(--line); margin:8px 0 12px; flex-wrap:wrap; }
.tabs a { padding:4px 10px; border:1px solid transparent; border-bottom:none; border-radius:4px 4px 0 0; }
.tabs a.on { border-color:var(--line); background:var(--panel); color:var(--fg); font-weight:600; }
header .sep { color:var(--muted); }
.card { border:1px solid var(--line); border-radius:6px; padding:10px 14px; margin:10px 0; background:var(--panel); }
progress { width:220px; }
dl.kv { display:grid; grid-template-columns:max-content 1fr; gap:2px 14px; } dl.kv dt { color:var(--muted); }
@media (max-width: 760px) { nav { display:none; } main { padding:12px 16px; } }
"""


def esc(x):
    return html.escape('' if x is None else str(x))


def one(q, k, default=None):
    v = q.get(k)
    return v[0] if v else default


def where(x):
    return (f'{x["region"]}, {x["country"]}' if x.get('region') else x['country']) if x else 'unknown'


# ---- the world a page is drawn from -------------------------------------------------------------------------
class World:
    """What the pages read: one committed generation -- a snapshot of the committed world (`live`, when
    there is a session) and the history published with it (`a`) -- or an archive alone (read-only).

    Pages read `live` and `a` only, never the session's running Season: an advance (a background job, or
    another process) changes that week by week. `session_lock` is held by whoever advances; while it is
    held, pages keep the snapshot they have."""

    def __init__(self, path, allow_other_engine=False, workers=None, session=None, read_only=False):
        p = Path(path)
        self.path = p
        self.session = session
        if session is None and not read_only and (p / 'CURRENT').exists():
            from golfsim.session import Session
            self.session = Session.open(p, workers=workers, allow_other_engine=allow_other_engine)
        self.archive_dir = p / 'archive' if (p / 'CURRENT').exists() else p
        self.label = p.name if p.name != 'archive' else p.parent.name
        self.session_lock = threading.Lock()
        self.lock = self.session_lock                       # (older name)
        self.live = None
        self.a, self._stats, self.behind, self._stamp = None, None, None, None
        self.interrupted = J.interrupted_job(p) if self.session is not None else None
        if self.interrupted is not None:
            J.log(p, f'found an advance that did not finish: {json.dumps(self.interrupted)}')
            J.clear_job(p)
        self.reload()

    @property
    def read_only(self):
        return self.session is None

    # -- following the committed world ----------------------------------------------------------------------
    def submit(self, form):
        """An Advance form, run here and now (tests, tools; the server runs it as a job):
        {'weeks': '1' | '4' | 'season', 'year', 'week', 'phase', 'op'} (lists, as parse_qs gives them).
        The session refuses a form drawn at another cursor (StaleCursor: nothing to do) and recognises a
        resubmitted one by its key."""
        from golfsim.session import StaleCursor
        with self.session_lock:
            weeks, expected, op = advance_request(form, self.session.cursor)
            try:
                self.session.advance(weeks, expected=expected, op_key=op)
            except StaleCursor:
                pass
        self.reload()

    def reload(self):
        """Refresh policy: every page (and every advance) starts here, and the snapshot and its history
        are always one committed generation. If another process committed since (an ordinary week, a
        season's end, a recovery that went back to an earlier generation), the committed world is loaded
        as committed -- never simulated or replayed -- together with that generation's published history
        (Session.refresh; a publication someone left unfinished is completed when the lock is free). While
        its owner is still publishing, the page keeps showing the previous generation, snapshot and
        history alike, and says so. While this observer is advancing the world, the page keeps the
        snapshot it has. A changed history is opened as a new Archive (one snapshot), records are
        brought up to date with it (HistoryStats.extend: new seasons only, or everything after a
        recovery), and only then does it replace the old one, which is closed: a failure on the way leaves
        the previous snapshot in place and the records to be rebuilt, never half-updated."""
        self.behind = None
        if self.session is not None:
            if not self.session_lock.acquire(blocking=False):
                return                                  # being advanced here: keep this snapshot
            try:
                stamp = None
                for _ in range(3):
                    try:
                        ok = self.session.refresh()
                    except Exception as e:                # e.g. publishing the committed history failed
                        J.log(self.path, f'refresh failed: {e!r}')
                        self.behind = (f'The saved world’s history could not be published ({type(e).__name__}: {e}); '
                                       'these pages show the last published state. Nothing is lost: it is published '
                                       'again on the next page or advance. Report a problem if this persists.')
                        if self.live is not None:
                            return
                        self.live = capture(self.session)  # (opening: the committed world, without new history)
                        stamp = published_stamp(self.archive_dir)
                        break
                    if not ok:
                        self.behind = ('The world has moved on and its new history is still being published: '
                                       'this page shows the previous generation.')
                        return
                    stamp = published_stamp(self.archive_dir)
                    if stamp[2] is None or int(stamp[0]) == self.session.history_generation:
                        break                           # (published again meanwhile: follow it)
                if self.live is None or self.live.generation != self.session.generation:
                    self.live = capture(self.session)
                self._swap_history(stamp)
            finally:
                self.session_lock.release()
        else:
            self._swap_history(published_stamp(self.archive_dir))

    def _swap_history(self, stamp):
        if stamp == self._stamp:
            return
        new = Archive(self.archive_dir) if stamp[1] else None   # nothing archived before the first season ends
        try:
            if self._stats is not None and new is not None:
                self._stats.extend(new)
        except BaseException:
            self._stats = None                          # rebuilt from a snapshot when next asked for
            if new is not None:
                new.close()
            raise
        old, self.a = self.a, new
        self._stamp = new.stamp if new is not None else stamp
        if new is None:
            self._stats = None
        if old is not None:
            old.close()

    def close(self):
        if self.a is not None:
            self.a.close()
            self.a = None
        self._stats = None
        if self.session is not None:
            self.session.close()

    @property
    def stats(self):
        if self._stats is None and self.a:
            self._stats = HistoryStats(self.a)
        return self._stats

    # -- one view over the published history and the current season ----------------------------------------
    def person(self, pid):
        """{'name', 'country', 'born', 'roles', 'golfer': {...}, ...}: the archive's record with the snapshot's
        current status over it (None if unknown)."""
        p = dict(self.a.people[pid]) if self.a and pid in self.a.people else None
        lp = self.live.people.get(pid) if self.live else None
        if lp:
            p = p or {'name': lp['name'], 'country': lp['country'], 'born': lp['born']}
            if 'golfer' in lp['roles']:
                p['golfer'] = {**p.get('golfer', {}), **{k: lp[k] for k in ('status', 'lifestyle', 'tour', 'turned_pro')}}
            for r in ('coach', 'caddie'):
                if r in lp:
                    p[r] = {**p.get(r, {}), **lp[r]}
        if p is not None:
            p['roles'] = [r for r in ('golfer', 'coach', 'caddie') if r in p]
        return p

    def name(self, pid):
        if self.live and pid in self.live.people:
            return self.live.name(pid)
        if self.a and pid in self.a.people:
            return self.a.name(pid)
        return f'#{pid}'

    def person_link(self, pid):
        return f'<a href="/golfer/{pid}">{esc(self.name(pid))}</a>' if pid else '<span class="muted">—</span>'

    def series_info(self, sid):
        if self.live and sid in self.live.series:
            return self.live.series[sid]
        if self.a:
            return self.a.world['series'].get(sid, {})
        return {}

    def series_name(self, sid):
        return self.series_info(sid).get('name', sid)

    def courses(self):
        if self.a:
            return self.a.world['courses']
        return self.live.courses if self.live else {}

    def tours(self):
        if self.a:
            return self.a.world['tours']
        return self.live.tours if self.live else {}

    def records_table(self):
        """Course records: the snapshot's (current through its week) or the archive's."""
        if self.live is not None:
            return self.live.records
        return self.a.records if self.a else {}

    def results(self, pid):
        """Every start: archived seasons, then the current season's (one list, oldest first)."""
        out = self.a.results(pid) if self.a and pid in self.a.people else []
        if self.live:
            out = out + self.live.results(pid)
        return out

    def edition(self, eid):
        """One edition: {id, series, year, week, name, tour, tier, category, prestige, playoff, sites,
        rows [{person, site, pos, total, coach, caddie, route}], rounds, match_play, source} or None."""
        y = int(eid.split(':')[0])
        if self.live and eid in self.live.editions:
            e = self.live.editions[eid]
            return {**e, 'year': y, 'source': 'current season', 'rows': _rows(e)}
        if not self.a or y not in self.a.years:
            return None
        idx = self.a.index
        if idx is not None:
            r = idx.db.execute('SELECT eid, series, week, name, tour, tier, category, prestige, playoff, field FROM editions '
                               'WHERE event_id = ?' + idx.upto(), (eid,)).fetchone()
            if r is None:
                return None
            k, series, week, name, tour, tier, cat, prestige, playoff, field = r
            sites = [list(x) for x in idx.db.execute('SELECT course, layout, city FROM sites WHERE eid = ? ORDER BY site', (k,))]
            return {'id': eid, 'series': series, 'year': y, 'week': week, 'name': name, 'tour': tour, 'tier': tier,
                    'category': cat, 'prestige': prestige, 'playoff': playoff, 'sites': sites,
                    'rows': idx.leaderboard(eid), 'rounds': None, 'match_play': None, 'source': 'archive'}
        e = next((e for e in self.a.year(y)['events'] if e['id'] == eid), None)
        return None if e is None else {**e, 'year': y, 'source': 'archive', 'rows': _rows(e)}

    def editions_of(self, sid):
        """A tournament's editions, oldest first: [{event, year, week, winner, field, tour, tier}]."""
        out = []
        if self.a and self.a.index:
            out = self.a.index.editions(sid)
        elif self.a:
            out = [{'event': e['id'], 'year': y, 'week': e['week'], 'winner': _winner(e), 'field': _field(e),
                    'tour': e.get('tour'), 'tier': e.get('tier')} for y, e in self.a.events() if e['series'] == sid]
        if self.live:
            out += [{'event': e['id'], 'year': int(e['id'].split(':')[0]), 'week': e['week'], 'winner': _winner(e),
                     'field': _field(e), 'tour': e['tour'], 'tier': e['tier']}
                    for e in self.live.editions.values() if e['series'] == sid]
        return out

    def course_editions(self, cid):
        out = []
        if self.a and self.a.index:
            out = [dict(r) for r in self.a.index.course_editions(cid)]
        elif self.a:
            out = [{'year': y, 'event': e['id'], 'layout': lay, 'winner': _winner(e)}
                   for y, e in self.a.events() for c, lay, _ in e['sites'] if c == cid]
        if self.live:
            out += [{'year': int(e['id'].split(':')[0]), 'event': e['id'], 'layout': lay, 'winner': _winner(e)}
                    for e in self.live.editions.values() for c, lay, _ in e['sites'] if c == cid]
        return out

    def geography(self, pid):
        if self.live is not None and self.live.geography(pid) is not None:
            return self.live.geography(pid)
        return self.a.geography(pid) if self.a and pid in self.a.people else None

    def all_people(self):
        """{pid: person} over the archive and the snapshot (for directories)."""
        ids = set(self.a.people) if self.a else set()
        if self.live:
            ids |= set(self.live.people)
        return ids


def _rows(e):
    out = []
    for k, site in enumerate(e['finish']):
        for gid, pos, tot in site:
            coach, caddie = e['team'].get(str(gid), (0, 0))
            out.append({'person': gid, 'site': k, 'pos': pos, 'total': tot, 'coach': coach, 'caddie': caddie,
                        'route': e['routes'].get(str(gid))})
    return out


def _winner(e):
    return next((g for g, p, _ in (e['finish'][0] if e['finish'] else []) if p == 1), None)


def _field(e):
    return sum(len(s) for s in e['finish'])


MAX_SEASONS = 1000


def advance_request(form, cursor):
    """(weeks, expected cursor, op key) from an Advance form (a single segment: see advance_plan)."""
    plan, op = advance_plan(form, cursor)
    return plan[0][0], plan[0][1], op


def advance_plan(form, cursor):
    """([(weeks, expected cursor)], op key) from an Advance form: one segment for a week, four weeks or the
    rest of the season; for N seasons, the rest of this season and then N-1 whole seasons, one segment each
    (each committed and published when its season ends). Every segment names the cursor it must start
    from, so a form resubmitted after the advance finished advances nothing, however many seasons ago."""
    v = one(form, 'weeks', '1')
    expected = ({'year': int(one(form, 'year')), 'week': int(one(form, 'week')), 'phase': one(form, 'phase')}
                if one(form, 'year') is not None else None)
    c = expected or cursor
    if v == 'seasons':
        n = max(1, min(MAX_SEASONS, int(one(form, 'seasons', '1') or 1)))
        plan = [(53 - c['week'], expected)]
        plan += [(52, {'year': c['year'] + i, 'week': 1, 'phase': 'start'} if expected is not None else None)
                 for i in range(1, n)]
        return plan, one(form, 'op')
    weeks = 53 - c['week'] if v == 'season' else max(1, min(52, int(v)))
    return [(weeks, expected)], one(form, 'op')


# ---- page frame ---------------------------------------------------------------------------------------------
def date_text(c):
    return f'{c["year"]}, week {c["week"]}' + (' (1 January next)' if c['phase'] == 'start' else '')


def advance_controls(w, job=None):
    """The Advance buttons, or the running operation's progress (with Stop)."""
    if job is not None and job.get('state') == 'running':
        stop = (f'<form method="post" action="/cancel"><input type="hidden" name="job" value="{esc(job["id"])}">'
                f'<button title="Stops after the week being played; every completed week is kept"'
                f'{" disabled" if not job["cancellable"] or job["cancel_requested"] else ""}>'
                'Stop simulation</button></form>') if job['kind'] == 'advance' else ''
        total = job['total'] or 0
        bar = f'<progress max="{total}" value="{job["done"]}"></progress>' if total else '<progress></progress>'
        return (f'<span id="job" data-job="{esc(job["id"])}" role="status" aria-live="polite">{esc(job["title"])}: '
                f'{bar} <span id="job-text">{esc(job_line(job))}</span></span>{stop}')
    if w is None or w.read_only or w.live is None:
        return ''
    c = w.live.cursor
    hidden = ''.join(f'<input type="hidden" name="{k}" value="{esc(v)}">' for k, v in
                     (('world', w.live.world_id), ('year', c['year']), ('week', c['week']), ('phase', c['phase']),
                      ('op', uuid.uuid4().hex)))
    return (f'<form method="post" action="/advance">{hidden}<button name="weeks" value="1" class="primary">Advance week</button>'
            '<button name="weeks" value="4">4 weeks</button><button name="weeks" value="season">'
            'To end of season</button><span class="sep" aria-hidden="true">·</span>'
            f'<input name="seasons" type="number" min="1" max="{MAX_SEASONS}" value="1" aria-label="Number of seasons" '
            'title="Plays to the end of this season, then the rest as whole seasons; each season is saved when it ends" '
            'style="width:5em"><button name="weeks" value="seasons">Advance seasons</button></form>')


def job_line(job):
    if job['state'] != 'running':
        return job['message']
    parts = [job['phase']]
    if job.get('seasons'):
        parts.append(f'season {job["season"]} of {job["seasons"]}')
    if job.get('total'):
        parts.append(f'{job["done"]}/{job["total"]} weeks')
    if job.get('last'):
        parts.append(f'last played {job["last"][0]} week {job["last"][1]}')
    parts.append(f'{job["elapsed"]:.0f} s')
    return ' · '.join(parts)


POLL_JS = """<script>
(function(){ var el=document.getElementById('job'); if(!el) return; var id=el.dataset.job;
 function tick(){ fetch('/api/status').then(function(r){return r.json();}).then(function(s){
   var j=s.job; if(!j||j.id!==id||j.state!=='running'){ location.reload(); return; }
   var t=document.getElementById('job-text'); if(t) t.textContent=s.line;
   var p=el.querySelector('progress'); if(p&&j.total){ p.max=j.total; p.value=j.done; }
   setTimeout(tick, 1000); }).catch(function(){ setTimeout(tick, 3000); }); }
 setTimeout(tick, 1000); })();
</script><noscript><meta http-equiv="refresh" content="3"></noscript>"""


def page(w, title, body, job=None, notices=()):
    if w is not None and w.live is not None:
        date = date_text(w.live.cursor)
    elif w is not None and w.session is not None:
        date = date_text(w.session.cursor)
    elif w is not None:
        date = 'read-only history archive'
    else:
        date = 'no world open'
    world = (f'<a href="/worlds" title="World library">{esc(w.label)}</a>' if w is not None
             else '<a href="/worlds">World library</a>')
    search = ('<form action="/golfers"><input name="q" placeholder="Search people" aria-label="Search people"></form>'
              if w is not None else '')
    nav = ('<nav aria-label="Sections"><h4>World</h4><a href="/">Overview</a><a href="/calendar">Calendar</a>'
           '<a href="/rankings">Rankings</a>'
           '<h4>Explore</h4><a href="/golfers">Golfers</a><a href="/coaches">Coaches</a><a href="/caddies">Caddies</a>'
           '<a href="/courses">Courses</a><a href="/nations">Nations</a><a href="/tours">Tours</a>'
           '<a href="/tournaments">Tournaments</a>'
           '<h4>History</h4><a href="/seasons">Seasons</a><a href="/records">Records &amp; frivolities</a>'
           '<a href="/moments">Moments</a>'
           '<h4>Worlds</h4><a href="/worlds">World library</a><a href="/export">Report a problem</a>'
           '<a href="/job">Last operation</a></nav>')
    banners = ''.join(f'<div class="banner {esc(kind)}" role="status">{text}</div>' for kind, text in notices)
    running = job is not None and job.get('state') == 'running'
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" '
            f'content="width=device-width, initial-scale=1"><title>{esc(title)} — Golf Legacy</title>'
            f'<style>{CSS}</style></head><body><header><strong>Golf Legacy</strong>{world}'
            f'<span class="date">{esc(date)}</span>{search}{advance_controls(w, job)}</header>'
            f'<div class="layout">{nav}<main>{banners}<h1>{esc(title)}</h1>{body}'
            f'{history_note(w) if w is not None else ""}</main></div>{POLL_JS if running else ""}</body></html>')


def history_note(w):
    """Which committed generation the page was drawn from (every part of a page comes from this one)."""
    behind = f'<p class="muted">{esc(w.behind)}</p>' if getattr(w, 'behind', None) else ''
    live = (f'Showing the world as committed at {date_text(w.live.cursor)} (generation {w.live.generation}). '
            if getattr(w, 'live', None) else '')
    if not getattr(w, 'a', None):
        return behind + f'<p class="muted">{esc(live)}No archived seasons yet: the first season is archived when it ends.</p>'
    gen = (w.a.stamp[0] or '').strip() or '?'
    return behind + (f'<p class="muted">{esc(live)}History: {span(w.a.years, False)}, published '
                     f'generation {esc(gen)}.</p>')


def table(headers, rows, numeric=()):
    """headers: [label]; rows: [[cell html]]; numeric: column indexes right-aligned."""
    h = ''.join(f'<th{" class=n" if i in numeric else ""}>{esc(x)}</th>' for i, x in enumerate(headers))
    body = ''.join('<tr>' + ''.join(f'<td{" class=n" if i in numeric else ""}>{c}</td>' for i, c in enumerate(r)) + '</tr>'
                   for r in rows)
    return f'<div class="scroll"><table><tr>{h}</tr>{body}</table></div>'


def paged(rows, q, path, size=PAGE_SIZE):
    """(rows of this page, pager html): ?page=N, other filters kept."""
    n = max(1, int(one(q, 'page', '1') or 1))
    pages = max(1, (len(rows) + size - 1) // size)
    n = min(n, pages)
    keep = {k: v[0] for k, v in q.items() if k != 'page' and v and v[0]}
    link = lambda k, label: f'<a href="{path}?{urlencode({**keep, "page": k})}">{label}</a>'
    nav = []
    if n > 1:
        nav.append(link(n - 1, '← Previous'))
    nav.append(f'<span class="muted">page {n} of {pages} ({len(rows):,} rows)</span>')
    if n < pages:
        nav.append(link(n + 1, 'Next →'))
    return rows[(n - 1) * size:n * size], '<p>' + ' · '.join(nav) + '</p>'


def filters(path, q, fields):
    """A GET form of filters. fields: [(name, label, options or None)]; options: [(value, label)]."""
    out = [f'<form class="filters" action="{path}">']
    for name, label, options in fields:
        cur = one(q, name, '') or ''
        if options is None:
            out.append(f'<label>{esc(label)}<input name="{name}" value="{esc(cur)}"></label>')
        else:
            opts = ''.join(f'<option value="{esc(v)}"{" selected" if str(v) == cur else ""}>{esc(t)}</option>'
                           for v, t in options)
            out.append(f'<label>{esc(label)}<select name="{name}">{opts}</select></label>')
    out.append('<button>Apply</button>')
    if any(one(q, n) for n, _, _ in fields):
        out.append(f'<a href="{path}">Clear</a>')
    return ''.join(out) + '</form>'


def event_link(w, eid):
    sid = eid.split(':', 1)[1]
    return f'<a href="/event/{quote(eid)}">{esc(eid.split(":")[0])} {esc(w.series_name(sid))}</a>'


def course_link(w, cid, layout=None):
    c = w.courses().get(cid, {})
    return (f'<a href="/course/{quote(cid)}">{esc(c.get("name", cid))}</a>'
            + (f' <span class="muted">({esc(layout)})</span>' if layout else ''))


def tour_link(w, key):
    if not key:
        return '<span class="muted">—</span>'
    t = w.tours().get(key, {})
    return f'<a href="/tour/{quote(key)}">{esc(t.get("name", key.replace("_", " ").title()))}</a>'


def nation_link(code):
    return f'<a href="/nation/{quote(code)}">{esc(code)}</a>' if code else ''


def span(years, cap=True):
    word = 'Season' if cap else 'season'
    return f'{word} {years[0]}' if len(years) == 1 else f'{word}s {years[0]}–{years[-1]}'


def no_history(what='archived seasons'):
    return f'<p class="muted">No {what} yet: history pages fill in when the first season ends.</p>'


# ---- pages --------------------------------------------------------------------------------------------------
def overview(w, q):
    out = []
    if w.interrupted:
        i = w.interrupted
        out.append(f'<div class="banner warn">An advance started {esc(i.get("started"))} ({esc(i.get("title"))}) did not '
                   f'finish: the observer stopped while it ran. The world is at its last saved week, '
                   f'{esc(date_text(w.live.cursor) if w.live else "?")}; the weeks being played when it stopped were not '
                   'kept (seasons completed before that were saved as they ended).</div>')
    if w.live:
        lv = w.live
        year = lv.cursor['year']
        recent = sorted((e for e in lv.editions.values() if _winner(e)), key=lambda e: (-e['week'], -(e['prestige'] or 0)))[:20]
        top = sorted(lv.wr.items(), key=lambda x: x[1])[:10]
        out.append('<h2>World ranking</h2>' + table(['#', 'Golfer', 'Tour'], [
            [str(p), w.person_link(g), tour_link(w, lv.people.get(g, {}).get('tour'))] for g, p in top], numeric=(0,))
            + '<p><a href="/rankings">Full ranking</a></p>')
        played = sum(1 for e in lv.schedule if e['status'] == 'played')
        out.append(f'<h2>{year} so far</h2><p>{played} of {len(lv.schedule)} scheduled events played · '
                   f'<a href="/calendar">calendar</a></p>')
        if recent:
            out.append(table(['Week', 'Event', 'Tour', 'Winner'], [
                [str(e['week']), event_link(w, e['id']), tour_link(w, e['tour']), w.person_link(_winner(e))] for e in recent]))
        else:
            out.append(f'<p class="muted">No events completed yet in {year}.</p>')
    if w.a:
        y = w.a.years[-1]
        facts = w.a.recap(y)
        out.append(f'<h2>{y} season recap</h2><ul>' + ''.join(
            f'<li>{esc(f["text"])}' + (f' — {w.person_link(f["golfer"])}' if f.get('golfer') else '') +
            (f' — {event_link(w, f["event"])}' if f.get('event') else '') + '</li>' for f in facts) + '</ul>')
        out.append('<p>Archived seasons: ' + ', '.join(f'<a href="/season/{x}">{x}</a>' for x in w.a.years) + '</p>')
    else:
        out.append('<p class="muted">No season has finished yet: the season recap, records and history pages fill in at '
                   'the end of the first season. Current-season results are already linked.</p>')
    return 'Overview', ''.join(out)


def rankings(w, q):
    kind = one(q, 'kind', 'world')
    tabs = ('<div class="tabs">' + ''.join(f'<a href="/rankings?kind={k}" class="{"on" if k == kind else ""}">{t}</a>'
                                           for k, t in (('world', 'World'), ('amateur', 'Amateur'))) + '</div>')
    if w.live:
        table_ = w.live.wr if kind == 'world' else w.live.am
        rows = sorted(((p, g) for g, p in table_.items()), key=lambda x: x[0])
    elif w.a:
        y = w.a.years[-1]
        rows = [(i + 1, g) for i, g in enumerate(w.a.ranking(y, 52, amateur=kind == 'amateur'))]
    else:
        rows = []
    chunk, pager = paged(rows, q, '/rankings')
    title = 'World ranking' if kind == 'world' else 'Amateur ranking'
    return title, tabs + table(['#', 'Golfer', 'Tour'], [
        [str(p), w.person_link(g), tour_link(w, (w.person(g) or {}).get('golfer', {}).get('tour'))] for p, g in chunk],
        numeric=(0,)) + pager


def search(w, q):
    return directory(w, q, role=None)


ROLE_TITLES = {None: 'People', 'golfer': 'Golfers', 'coach': 'Coaches', 'caddie': 'Caddies'}


def directory(w, q, role='golfer'):
    """People, filtered: name, nation, role, tour, status; sorted by name, birth year or world ranking."""
    term = (one(q, 'q', '') or '').strip().lower()
    nation = one(q, 'nation', '') or ''
    tour = one(q, 'tour', '') or ''
    status = one(q, 'status', '') or ''
    sort = one(q, 'sort', 'rank' if role == 'golfer' else 'name')
    rows = []
    for pid in w.all_people():
        p = w.person(pid)
        if p is None or (role and role not in p['roles']):
            continue
        if term and term not in p['name'].lower():
            continue
        if nation and p.get('country') != nation:
            continue
        gs = p.get('golfer', {})
        if tour and gs.get('tour') != tour:
            continue
        st = (p.get(role, {}).get('status') if role in ('coach', 'caddie') else gs.get('lifestyle') or gs.get('status'))
        if status and st != status:
            continue
        rows.append((pid, p, st))
    wr = w.live.wr if w.live else {}
    key = {'name': lambda r: (r[1]['name'], r[0]), 'born': lambda r: (-(r[1].get('born') or 0), r[0]),
           'rank': lambda r: (wr.get(r[0], 10 ** 9), r[1]['name'], r[0])}.get(sort, lambda r: (r[1]['name'], r[0]))
    rows.sort(key=key)
    nations = sorted({p.get('country') for _, p, _ in rows} | ({nation} if nation else set()) - {None})
    path = {None: '/golfers', 'golfer': '/golfers', 'coach': '/coaches', 'caddie': '/caddies'}[role]
    statuses = sorted({s for _, _, s in rows if s} | ({status} if status else set()))
    fields = [('q', 'Name contains', None), ('nation', 'Nation', [('', 'any')] + [(n, n) for n in nations])]
    if role == 'golfer':
        fields.append(('tour', 'Tour now', [('', 'any')] + sorted(((k, t.get('name', k)) for k, t in w.tours().items()),
                                                                 key=lambda x: x[1])))
    fields.append(('status', 'Status now', [('', 'any')] + [(s, s) for s in statuses]))
    fields.append(('sort', 'Sort', [(k, t) for k, t in (('rank', 'world ranking'), ('name', 'name'), ('born', 'youngest first'))
                                    if role == 'golfer' or k != 'rank']))
    chunk, pager = paged(rows, q, path)
    if role in ('coach', 'caddie'):
        clients = {}
        if w.live:
            for g, s in (w.live.coach_of if role == 'coach' else w.live.caddie_of).items():
                clients[s] = clients.get(s, 0) + 1
        body = table(['Name', 'Nation', 'Born', 'Status', 'Reputation', 'Clients now', 'Also'], [
            [w.person_link(pid), nation_link(p.get('country')), esc(p.get('born')), esc(st),
             esc(p.get(role, {}).get('reputation', '')), str(clients.get(pid, 0)) if w.live else '',
             esc(', '.join(r for r in p['roles'] if r != role))] for pid, p, st in chunk], numeric=(2, 4, 5))
    else:
        body = table(['Name', 'Nation', 'Born', 'Status now', 'Tour now', 'World', 'Roles'], [
            [w.person_link(pid), nation_link(p.get('country')), esc(p.get('born')), esc(st),
             tour_link(w, p.get('golfer', {}).get('tour')), esc(wr.get(pid, '')), esc(', '.join(p['roles']))]
            for pid, p, st in chunk], numeric=(2, 5))
    note = ('<p class="muted">Everyone in the published history and the current world. "Now" is as of the date in the '
            'header; retired people keep their pages.</p>')
    return ROLE_TITLES[role] if not term else f'{ROLE_TITLES[role]} matching “{term}”', \
        filters(path, q, fields) + note + body + pager


def golfers(w, q):
    return directory(w, q, 'golfer')


def coaches(w, q):
    return directory(w, q, 'coach')


def caddies(w, q):
    return directory(w, q, 'caddie')


def golfer(w, q, pid):
    """A person's page: one identity, a tab per career (playing, coaching, caddying)."""
    pid = int(pid)
    p = w.person(pid)
    if p is None:
        return f'#{pid}', '<p class="muted">No such person in this world.</p>'
    roles = p['roles']
    tab = one(q, 'tab', 'playing' if 'golfer' in roles else 'coaching' if 'coach' in roles else 'caddying')
    tabs = [('playing', 'Playing career', 'golfer'), ('results', 'Results', 'golfer'), ('team', 'Coaches & caddies', 'golfer'),
            ('coaching', 'Coaching', 'coach'), ('caddying', 'Caddying', 'caddie')]
    out = []
    a = w.a
    initial = a and pid in a.people and a.people[pid].get('initial')
    out.append(f'<p>{nation_link(p.get("country"))} · born {esc(p.get("born"))} · {esc(", ".join(roles))}'
               + (' · <span class="tag">career began before the archive</span>' if initial else '') + '</p>')
    geo = w.geography(pid)
    if geo:
        out.append(f'<p>Nationality: {esc(p.get("country"))} · born in {esc(where(geo["birthplace"]))}'
                   f' · lives in {esc(where(geo["residence"]))}</p>')
    gs = p.get('golfer')
    if gs and w.live and pid in w.live.people:
        coach, caddie = w.live.coach_of.get(pid), w.live.caddie_of.get(pid)
        out.append(f'<p>Now: {esc(gs.get("status"))}, {esc(gs.get("lifestyle"))}, {tour_link(w, gs.get("tour"))}'
                   + (f', world No. {w.live.wr[pid]}' if pid in w.live.wr else '')
                   + (f' · coach {w.person_link(coach)}' if coach else '') + (f' · caddie {w.person_link(caddie)}' if caddie else '')
                   + '</p>')
    out.append('<div class="tabs">' + ''.join(
        f'<a href="/golfer/{pid}?tab={k}" class="{"on" if k == tab else ""}">{t}</a>' for k, t, r in tabs if r in roles) + '</div>')
    if tab == 'playing':
        out.append(_playing(w, pid))
        if geo and geo['moves']:
            out.append('<h2>Where they have lived</h2>' + table(['When', 'From', 'To', 'Why'], [
                [esc(m['year']), esc(where(m['from'])), esc(where(m['to'])), esc(m['reason'])] for m in geo['moves']]))
    elif tab == 'results':
        out.append(_results(w, q, pid))
    elif tab == 'team':
        out.append(_team(w, pid))
    elif tab in ('coaching', 'caddying'):
        out.append(_staff(w, pid, 'coach' if tab == 'coaching' else 'caddie'))
        if geo and geo['moves'] and 'golfer' not in roles:
            out.append('<h2>Where they have lived</h2>' + table(['When', 'From', 'To', 'Why'], [
                [esc(m['year']), esc(where(m['from'])), esc(where(m['to'])), esc(m['reason'])] for m in geo['moves']]))
    if a and a.index and tab == 'playing':
        moments_ = a.index.moments(person=pid)
        if moments_:
            out.append('<h2>Moments</h2><ul>' + ''.join(f'<li>{esc(m["year"])}: {esc(m["kind"])} — {event_link(w, m["event"])}</li>'
                                                     for m in moments_) + '</ul>')
    return w.name(pid), ''.join(out)


def _playing(w, pid):
    out = []
    a = w.a
    seasons = a.index.seasons(pid) if a and a.index and pid in a.people else []
    if not seasons and a and pid in a.people and not a.index:
        seasons = [dict(r, year=y) for y, r in a.playing_career(pid)]
    rows = [[esc(r['year']), tour_link(w, r['tour']), f'{esc(r["status"])} / {esc(r["lifestyle"])}', esc(r['events']),
             esc(r['wins']), f'${(r["prize"] or 0):,}', esc(r['wr_end'] or '—')] for r in seasons]
    if w.live:
        cur = w.live.results(pid)
        if cur or pid in w.live.people:
            gs = w.live.people.get(pid, {})
            y = w.live.cursor['year']
            rows.append([f'{y} <span class="tag">so far</span>', tour_link(w, gs.get('tour')),
                         f'{esc(gs.get("status"))} / {esc(gs.get("lifestyle"))}', str(len(cur)),
                         str(sum(1 for r in cur if r['pos'] == 1)), '<span class="muted">at season end</span>',
                         esc(w.live.wr.get(pid, '—'))])
    out.append('<h2>Career</h2>' + (table(['Season', 'Tour', 'Status', 'Starts', 'Wins', 'Prize', 'World (end)'], rows,
                                          numeric=(3, 4, 5, 6)) if rows else '<p class="muted">No seasons played yet.</p>'))
    res = w.results(pid)
    wins = [r for r in res if r['pos'] == 1]
    if wins:
        out.append(f'<h2>Wins ({len(wins)})</h2>' + table(['Season', 'Event', 'Tour'], [
            [esc(r['year']), event_link(w, r['event']), tour_link(w, w.series_info(r['series']).get('tour'))]
            for r in reversed(wins)]))
    return ''.join(out)


def _results(w, q, pid):
    res = list(reversed(w.results(pid)))
    if not res:
        return '<p class="muted">No starts yet.</p>'
    chunk, pager = paged(res, q, f'/golfer/{pid}', size=50)
    return (f'<p>{len(res):,} starts (archived seasons and the current season).</p>' + table(
        ['Season', 'Week', 'Event', 'Pos', 'Coach', 'Caddie', 'How they got in'],
        [[esc(r['year']), esc(r['week']), event_link(w, r['event']), esc(r['pos'] or 'MC'), w.person_link(r['coach']),
          w.person_link(r['caddie']), f'<span class="muted">{esc(r["route"])}</span>'] for r in chunk], numeric=(0, 1, 3)) + pager)


def _team(w, pid):
    out = []
    if w.live and pid in w.live.people:
        coach, caddie = w.live.coach_of.get(pid), w.live.caddie_of.get(pid)
        out.append(f'<p>Now: coach {w.person_link(coach) if coach else "none"} · caddie '
                   f'{w.person_link(caddie) if caddie else "none"}.</p>')
    stints = w.a.golfer_staff(pid) if w.a else []
    if stints:
        through = w.a.years[-1]
        out.append(f'<h2>Team history</h2><p class="muted">Stints as recorded at the end of {through}; changes since then '
                   'show under "Now" and in each result\'s team.</p>' + table(
                       ['Role', 'Who', 'From', 'To', 'Why it ended'],
                       [[esc(s.kind), w.person_link(s.staff) if s.staff else esc(s.arrangement),
                         f'{s.start[0]} wk {s.start[1]}', f'{s.end[0]} wk {s.end[1]}' if s.end else 'still together',
                         esc(s.reason_end or '')] for s in stints]))
    elif not w.a:
        out.append('<p class="muted">Dated stints are archived at the end of the first season.</p>')
    return ''.join(out) or '<p class="muted">No coaches or caddies recorded.</p>'


def _staff(w, pid, role):
    out = []
    p = w.person(pid) or {}
    info = p.get(role, {})
    out.append(f'<p>{esc(role.title())} · status {esc(info.get("status"))}'
               + (f' · reputation {esc(info.get("reputation"))}' if info.get('reputation') is not None else '')
               + (f' · {esc(info.get("background"))}' if info.get('background') else '') + '</p>')
    if w.live:
        now = [g for g, s in (w.live.coach_of if role == 'coach' else w.live.caddie_of).items() if s == pid]
        out.append('<p>Working with now: ' + (', '.join(w.person_link(g) for g in sorted(now)) or 'nobody') + '</p>')
    if w.a and pid in w.a.people:
        rows = w.a.staff_clients(pid, role)
        if rows:
            out.append(f'<h2>Players (through {w.a.years[-1]})</h2>' + table(
                ['Player', 'From', 'To', 'Starts together', 'Wins', 'Majors'],
                [[w.person_link(c['stint'].golfer), f'{c["stint"].start[0]} wk {c["stint"].start[1]}',
                  f'{c["stint"].end[0]} wk {c["stint"].end[1]}' if c['stint'].end else 'still together',
                  str(c['starts']), str(len(c['wins'])), str(len(c['majors']))] for c in rows], numeric=(3, 4, 5))
                + '<p class="muted">Results during a partnership are association, not proof of cause. Starts together '
                  'count the archived seasons.</p>')
        hist = (w.a.people[pid].get(role) or {}).get('history') or []
        if hist:
            out.append('<h2>Staff career</h2><ul>' + ''.join(f'<li>{esc(y)}: {esc(t)}</li>' for y, t in hist) + '</ul>')
    else:
        out.append('<p class="muted">Dated partnerships are archived when the season ends; until then each result shows '
                   'the team that week.</p>')
    return ''.join(out)


def event(w, q, eid):
    eid = unquote(eid)
    sid = eid.split(':', 1)[1]
    e = w.edition(eid)
    if e is None:
        sched = next((x for x in (w.live.schedule if w.live else []) if x['id'] == eid), None)
        if sched:
            return f'{eid.split(":")[0]} {sched["name"]}', (
                f'<p><a href="/series/{quote(sid)}">All editions</a></p><p>Week {sched["week"]}, {esc(sched["city"])}, '
                f'{esc(sched["country"])} · {tour_link(w, sched["tour"])} · {esc(sched["status"])}.</p>')
        return eid, '<p class="muted">No such edition in this world’s published history or current season.</p>'
    out = [f'<p><a href="/series/{quote(sid)}">All editions of the {esc(e.get("name") or w.series_name(sid))}</a> · '
           f'{"current season" if e["source"] == "current season" else "archived season"}</p>']
    fmt = []
    if e.get('rounds'):
        fmt.append(f'{e["rounds"] * 18} holes')
    if e.get('match_play') is not None:
        fmt.append('match play' if e['match_play'] else 'stroke play')
    out.append(f'<p>{e["year"]} week {e["week"]} · {tour_link(w, e.get("tour"))} · tier {esc(e.get("tier"))} · '
               f'{esc(e.get("category"))} · prestige {esc(e.get("prestige"))}' + (f' · {", ".join(fmt)}' if fmt else '')
               + (f' · playoff ({e["playoff"]} holes)' if e.get('playoff') else '') + '</p>')
    out.append('<p>' + ' · '.join(f'{course_link(w, c, lay)}, {esc(city)}' for c, lay, city in e['sites']) + '</p>')
    rows = e['rows']
    multi = len(e['sites']) > 1
    out.append(table((['Site'] if multi else []) + ['Pos', 'Golfer', 'Total', 'Coach', 'Caddie', 'How they got in'], [
        ([esc(r['site'] + 1)] if multi else []) +
        [esc(r['pos'] or 'MC'), w.person_link(r['person']), esc(r['total'] or ''), w.person_link(r['coach']),
         w.person_link(r['caddie']), f'<span class="muted">{esc(r["route"])}</span>'] for r in rows],
        numeric=(1, 3) if multi else (0, 2)))
    out.append('<p class="muted">Coach and caddie are the team that week. MC: missed the cut (or out before the '
               'final stage).</p>')
    return f'{eid.split(":")[0]} {e.get("name") or w.series_name(sid)}', ''.join(out)


def series(w, q, sid):
    sid = unquote(sid)
    info = w.series_info(sid)
    eds = sorted(w.editions_of(sid), key=lambda e: e['year'], reverse=True)
    head = (f'<p>{tour_link(w, info.get("tour"))} · tier {esc(info.get("tier"))} · {esc(info.get("kind"))} · '
            f'{esc(info.get("category"))}</p>') if info else ''
    if not eds:
        return w.series_name(sid), head + '<p class="muted">No editions played yet.</p>'
    return w.series_name(sid), head + table(['Edition', 'Week', 'Winner', 'Field', 'Tour then'], [
        [event_link(w, e['event']), esc(e['week']), w.person_link(e['winner']), esc(e['field']), tour_link(w, e['tour'])]
        for e in eds], numeric=(1, 3))


def tournaments(w, q):
    tour = one(q, 'tour', '') or ''
    kind = one(q, 'kind', '') or ''
    allseries = dict(w.a.world['series']) if w.a else {}
    if w.live:
        allseries.update(w.live.series)
    counts = {}
    if w.a and w.a.index:
        counts = {s: n for s, n in w.a.index.db.execute('SELECT series, COUNT(*) FROM editions WHERE 1=1' + w.a.index.upto()
                                                        + ' GROUP BY series')}
    if w.live:
        for e in w.live.editions.values():
            counts[e['series']] = counts.get(e['series'], 0) + 1
    rows = [(sid, s) for sid, s in allseries.items() if (not tour or s.get('tour') == tour) and (not kind or s.get('kind') == kind)]
    rows.sort(key=lambda x: (x[1].get('tier', 9), x[1].get('name', '')))
    kinds = sorted({s.get('kind') for s in allseries.values() if s.get('kind')})
    f = filters('/tournaments', q, [('tour', 'Tour', [('', 'any')] + sorted(((k, t.get('name', k)) for k, t in w.tours().items()),
                                                                             key=lambda x: x[1])),
                                    ('kind', 'Kind', [('', 'any')] + [(k, k) for k in kinds])])
    chunk, pager = paged(rows, q, '/tournaments')
    return 'Tournaments', f + table(['Tournament', 'Tour', 'Tier', 'Kind', 'Category', 'Editions played'], [
        [f'<a href="/series/{quote(sid)}">{esc(s.get("name", sid))}</a>', tour_link(w, s.get('tour')), esc(s.get('tier')),
         esc(s.get('kind')), esc(s.get('category')), str(counts.get(sid, 0))] for sid, s in chunk], numeric=(2, 5)) + pager


def calendar(w, q):
    if not w.live:
        return 'Calendar', '<p class="muted">The calendar belongs to a running world: open the world (not only its archive).</p>'
    tour = one(q, 'tour', '') or ''
    status = one(q, 'status', '') or ''
    rows = [e for e in w.live.schedule if (not tour or e['tour'] == tour) and (not status or e['status'] == status)]
    f = filters('/calendar', q, [('tour', 'Tour', [('', 'any')] + sorted(((k, t.get('name', k)) for k, t in w.tours().items()),
                                                                         key=lambda x: x[1])),
                                 ('status', 'Status', [('', 'any'), ('played', 'played'), ('scheduled', 'scheduled'),
                                                       ('not held', 'not held')])])
    chunk, pager = paged(rows, q, '/calendar', size=200)
    body = table(['Week', 'Event', 'Tour', 'Tier', 'Where', 'Status', 'Winner'], [
        [esc(e['week']), (event_link(w, e['id']) if e['status'] == 'played' else
                          f'<a href="/series/{quote(e["series"])}">{esc(e["name"])}</a>'),
         tour_link(w, e['tour']), esc(e['tier']), f'{esc(e["city"])}, {esc(e["country"])}', esc(e['status']),
         w.person_link(_winner(w.live.editions[e['id']])) if e['status'] == 'played' else '']
        for e in chunk], numeric=(0, 3))
    return f'{w.live.cursor["year"]} calendar', f + body + pager


def courses_page(w, q):
    country = one(q, 'country', '') or ''
    term = (one(q, 'q', '') or '').lower()
    cs = w.courses()
    hosted = {}
    if w.a and w.a.index:
        hosted = {c: n for c, n in w.a.index.db.execute('SELECT course, COUNT(*) FROM sites WHERE 1=1' + w.a.index.upto()
                                                        + ' GROUP BY course')}
    if w.live:
        for e in w.live.editions.values():
            for c, _, _ in e['sites']:
                hosted[c] = hosted.get(c, 0) + 1
    rows = sorted(((cid, c) for cid, c in cs.items() if (not country or c.get('country') == country)
                   and (not term or term in c.get('name', '').lower())), key=lambda x: (x[1].get('country', ''), x[1].get('name', '')))
    f = filters('/courses', q, [('q', 'Name contains', None),
                                ('country', 'Country', [('', 'any')] + [(c, c) for c in sorted({c.get('country') for c in cs.values()})])])
    chunk, pager = paged(rows, q, '/courses')
    return 'Courses', f + table(['Course', 'City', 'Country', 'Class', 'Layouts', 'Editions hosted'], [
        [course_link(w, cid), esc(c.get('city')), nation_link(c.get('country')), esc(c.get('class')),
         esc(', '.join(c.get('layouts', {}))), str(hosted.get(cid, 0))] for cid, c in chunk], numeric=(5,)) + pager


def course(w, q, cid):
    cid = unquote(cid)
    c = w.courses().get(cid)
    if c is None:
        return cid, '<p class="muted">No such course.</p>'
    out = [f'<p>{esc(c.get("city"))}, {nation_link(c.get("country"))} · {esc(c.get("class"))} · architect '
           f'{esc(c.get("architect"))} · opened {esc(c.get("opened"))}</p>']
    out.append('<h2>Layouts</h2>' + table(['Layout', 'Par', 'Yards'], [
        [esc(k), esc(l.get('par')), f'{l.get("yards") or 0:,}'] for k, l in c.get('layouts', {}).items()], numeric=(1, 2)))
    recs = {lid: r for lid, r in w.records_table().items() if lid.split(':')[0] == cid}
    for lid, r in recs.items():
        cr = r.get('course_record')
        if cr:
            out.append(f'<p>{esc(lid.split(":")[1])} layout record: {cr["score"]} by {w.person_link(cr.get("golfer_id"))} '
                       f'({event_link(w, cr["event_id"])})</p>')
        totals = r.get('lowest_totals') or {}
        if totals:
            since = r.get('totals_since')
            out.append(f'<p class="muted">{esc(lid.split(":")[1])} lowest tournament totals'
                       + (f' (recorded since {since})' if since else '') + ': ' + '; '.join(
                           f'{h} holes {m["score"]} ({m["to_par"]:+d}) by {w.person_link(m.get("golfer_id"))}, '
                           f'{event_link(w, m["event_id"])}' for h, m in sorted(totals.items(), key=lambda x: int(x[0])))
                       + '</p>')
    eds = sorted(w.course_editions(cid), key=lambda e: (e['year'], e['event']), reverse=True)
    chunk, pager = paged(eds, q, f'/course/{quote(cid)}')
    out.append('<h2>Editions hosted</h2>' + (table(['Edition', 'Layout', 'Winner'], [
        [event_link(w, e['event']), esc(e['layout']), w.person_link(e['winner'])] for e in chunk]) + pager
        if eds else '<p class="muted">None yet.</p>'))
    return c.get('name', cid), ''.join(out)


def nations(w, q):
    counts = {}
    for pid in w.all_people():
        p = w.person(pid)
        n = p.get('country')
        row = counts.setdefault(n, [0, 0, 0, 0])
        row[0] += 1
        gs = p.get('golfer') or {}
        if gs and gs.get('lifestyle') not in (None, 'retired'):
            row[1] += 1
        if w.live and pid in w.live.wr and w.live.wr[pid] <= 100:
            row[2] += 1
    if w.stats:
        for pid, ss in w.stats.starts.items():
            if any(s[5] == 'major' and s[6] == 1 for s in ss):
                n = (w.person(pid) or {}).get('country')
                counts.setdefault(n, [0, 0, 0, 0])[3] += 1
    rows = sorted(counts.items(), key=lambda x: (-x[1][2], -x[1][1], str(x[0])))
    return 'Nations', ('<p class="muted">Nationality is fixed for life (birthplace); where people live can change.</p>' +
                       table(['Nation', 'People', 'Active golfers', 'In world top 100 now', 'Major champions (archived)'], [
                           [nation_link(n), str(r[0]), str(r[1]), str(r[2]), str(r[3])] for n, r in rows if n],
                           numeric=(1, 2, 3, 4)))


def nation(w, q, code):
    code = unquote(code)
    out = [f'<p><a href="/golfers?nation={quote(code)}">All golfers</a> · <a href="/coaches?nation={quote(code)}">coaches</a> · '
           f'<a href="/caddies?nation={quote(code)}">caddies</a> · <a href="/courses?country={quote(code)}">courses</a></p>']
    if w.live:
        top = sorted((p, g) for g, p in w.live.wr.items() if (w.live.people.get(g) or {}).get('country') == code)[:25]
        out.append('<h2>Highest ranked now</h2>' + (table(['World', 'Golfer', 'Tour'], [
            [str(p), w.person_link(g), tour_link(w, w.live.people[g].get('tour'))] for p, g in top], numeric=(0,))
            if top else '<p class="muted">Nobody in the world ranking.</p>'))
    if w.stats:
        wins = []
        for pid, ss in w.stats.starts.items():
            if (w.person(pid) or {}).get('country') == code:
                wins += [(s[0], s[2], pid) for s in ss if s[5] == 'major' and s[6] == 1]
        out.append('<h2>Major wins (archived seasons)</h2>' + (table(['Season', 'Major', 'Champion'], [
            [str(y), event_link(w, e), w.person_link(pid)] for y, e, pid in sorted(wins, reverse=True)], numeric=(0,))
            if wins else '<p class="muted">None.</p>'))
    return f'Nation: {code}', ''.join(out)


def tours_page(w, q):
    members = {}
    if w.live:
        for pid, p in w.live.people.items():
            if p.get('tour') and p.get('lifestyle') != 'retired':
                members[p['tour']] = members.get(p['tour'], 0) + 1
    events = {}
    for s in (w.live.schedule if w.live else []):
        events[s['tour']] = events.get(s['tour'], 0) + 1
    rows = sorted(w.tours().items(), key=lambda x: (x[1].get('tier', 9), x[1].get('name', '')))
    return 'Tours', ('<p class="muted">A tour is a circuit with members; a tournament is one of its events.</p>' + table(
        ['Tour', 'Tier', 'Members now', 'Events this season'],
        [[tour_link(w, k), esc(t.get('tier')), str(members.get(k, 0)) if w.live else '', str(events.get(k, 0)) if w.live else '']
         for k, t in rows], numeric=(1, 2, 3)))


def tour(w, q, key):
    key = unquote(key)
    t = w.tours().get(key, {})
    out = [f'<p>Tier {esc(t.get("tier"))} · <a href="/tournaments?tour={quote(key)}">its tournaments</a> · '
           f'<a href="/golfers?tour={quote(key)}">all members</a></p>']
    if w.live:
        mem = sorted((w.live.wr.get(pid, 10 ** 9), pid) for pid, p in w.live.people.items()
                     if p.get('tour') == key and p.get('lifestyle') != 'retired')
        out.append(f'<h2>Members now ({len(mem)})</h2>' + table(['World', 'Golfer', 'Status'], [
            [esc(r if r < 10 ** 9 else '—'), w.person_link(pid), esc(w.live.people[pid].get('status'))] for r, pid in mem[:50]],
            numeric=(0,)) + (f'<p><a href="/golfers?tour={quote(key)}">All {len(mem)} members</a></p>' if len(mem) > 50 else ''))
        eds = [e for e in w.live.schedule if e['tour'] == key]
        out.append(f'<h2>{w.live.cursor["year"]} events</h2>' + table(['Week', 'Event', 'Winner'], [
            [esc(e['week']), event_link(w, e['id']) if e['status'] == 'played' else esc(e['name']),
             w.person_link(_winner(w.live.editions[e['id']])) if e['status'] == 'played' else esc(e['status'])] for e in eds],
            numeric=(0,)))
    return t.get('name', key), ''.join(out)


def seasons(w, q):
    out = []
    if w.live:
        out.append(f'<p>Current season: {w.live.cursor["year"]} (<a href="/calendar">calendar</a>, '
                   f'{len(w.live.editions)} events played).</p>')
    if not w.a:
        return 'Seasons', ''.join(out) + no_history()
    majors = {y: [] for y in w.a.years}
    kinds = {sid for sid, m in w.a.world['series'].items() if m.get('kind') == 'major'}
    if w.a.index is not None:                           # one query (the season files would be decoded otherwise)
        for y, eid, winner in w.a.index.db.execute(
                f'SELECT year, event_id, winner FROM editions WHERE series IN ({",".join("?" * len(kinds))})'
                + w.a.index.upto() + ' ORDER BY year, week', sorted(kinds)):
            majors.setdefault(y, []).append((eid, winner))
    else:
        for y, e in w.a.events():
            if e['series'] in kinds:
                majors[y].append((e['id'], _winner(e)))
    rows = [[f'<a href="/season/{y}">{y}</a>', ', '.join(f'{event_link(w, eid)}: {w.person_link(g)}' for eid, g in majors[y])]
            for y in reversed(w.a.years)]
    chunk, pager = paged(rows, q, '/seasons', size=25)
    return 'Seasons', ''.join(out) + table(['Season', 'Major champions'], chunk) + pager


def season(w, q, y):
    y = int(y)
    if not w.a or y not in w.a.years:
        return str(y), '<p class="muted">This season is not archived (yet).</p>'
    facts = w.a.recap(y)
    top = w.a.ranking(y, 52)[:10]
    return f'{y} season', ('<ul>' + ''.join(
        f'<li>{esc(f["text"])}' + (f' — {w.person_link(f["golfer"])}' if f.get('golfer') else '') +
        (f' — {event_link(w, f["event"])}' if f.get('event') else '') + '</li>' for f in facts) + '</ul>'
        + '<h2>World ranking at the end of the season</h2>' + table(['#', 'Golfer'], [
            [str(i), w.person_link(g)] for i, g in enumerate(top, 1)], numeric=(0,)))


FEATURED = ('youngest-major-champions', 'oldest-major-champions', 'youngest-premier-debuts', 'oldest-premier-debuts',
            'not-won-yet', 'retired-without-a-win')
SCOPED = {'most-wins', 'most-starts', 'not-won-yet', 'retired-without-a-win', 'starts-before-first-win',
          'youngest-winners', 'oldest-winners', 'longest-wait-between-wins', 'runner-ups-without-a-win'}


def records(w, q):
    first = ''.join(f'<li><a href="/records/{k}">{esc(BOARDS[k][0])}</a>'
                    + (' — <span class="muted">by tour: choose a tour on the list</span>' if k in SCOPED else '') + '</li>'
                    for k in FEATURED)
    rest = ''.join(f'<li><a href="/records/{k}">{esc(t)}</a></li>' for k, (t, _, _) in BOARDS.items() if k not in FEATURED)
    through = (f'<p class="muted">From the archived seasons ({span(w.a.years, False)}); the current season counts '
               'once it ends. Ages are the season\'s year minus the birth year (birth dates are not recorded), so an age '
               'can be a year out. Careers that began before the archive are marked partial and left out of debut lists.</p>'
               if w.a else no_history())
    return 'Records & frivolities', (through + '<h2>Start here</h2><ul>' + first + '</ul><h2>All lists</h2><ul>' + rest +
                                     '</ul><h2>Definitions</h2><dl>' + ''.join(
                                         f'<dt>{esc(k)}</dt><dd class="muted">{esc(v)}</dd>' for k, v in DEFINITIONS.items())
                                     + '</dl>')


def record(w, q, name):
    if name not in BOARDS:
        return 'Records', '<p class="muted">No such list.</p>'
    if not w.stats:
        return BOARDS[name][0], no_history()
    scope = one(q, 'scope', '') or ''
    over = {'scope': scope} if scope and name in SCOPED else {}
    title, rows = board(w.stats, name, n=100, **over)
    f = ''
    if name in SCOPED:
        tours = sorted(((k, t.get('name', k)) for k, t in w.tours().items()), key=lambda x: x[1])
        f = filters(f'/records/{name}', q, [('scope', 'Scope', [('', 'as defined')] + [(s, s) for s in SCOPES] +
                                                                [(k, f'tour: {t}') for k, t in tours])])
        if scope:
            title += f' — {w.tours().get(scope, {}).get("name", scope)}'
    flag = lambda r: ('<span class=tag>active</span> ' if r['active'] else '') + (
        '<span class=tag>partial</span>' if r['partial'] else '')
    return title, (f + f'<p class="muted">{span(w.a.years)}. Active = still competing (may change). '
                   'Partial = began before the archive; earlier results are not included.</p>' + table(
                       ['#', 'Golfer', 'Value', '', 'When', 'Evidence'],
                       [[str(i), w.person_link(r['person']), esc(r['value']), flag(r), esc(r.get('year', '')),
                         ', '.join(event_link(w, e) for e in r['evidence'][:3])] for i, r in enumerate(rows, 1)],
                       numeric=(0, 2)) + ('' if rows else '<p class="muted">Nobody qualifies yet.</p>'))


def moments(w, q):
    if not (w.a and w.a.index):
        return 'Moments', no_history()
    kind = one(q, 'kind', '') or ''
    ms = list(reversed(w.a.index.moments(kind=kind or None)))
    kinds = [k for (k,) in w.a.index.db.execute('SELECT DISTINCT kind FROM moments ORDER BY kind')]
    f = filters('/moments', q, [('kind', 'Kind', [('', 'any')] + [(k, k) for k in kinds])])
    chunk, pager = paged(ms, q, '/moments')
    return 'Moments', f + table(['Season', 'What', 'Golfer', 'Event'], [
        [esc(m['year']), esc(m['kind']), w.person_link(m['person']), event_link(w, m['event'])] for m in chunk],
        numeric=(0,)) + pager


ROUTES = [('/golfer/', golfer), ('/event/', event), ('/series/', series), ('/course/', course), ('/records/', record),
          ('/nation/', nation), ('/tour/', tour), ('/season/', season)]
PAGES = {'/': overview, '/rankings': rankings, '/search': search, '/golfers': golfers, '/coaches': coaches,
         '/caddies': caddies, '/records': records, '/moments': moments, '/tournaments': tournaments,
         '/calendar': calendar, '/courses': courses_page, '/nations': nations, '/tours': tours_page, '/seasons': seasons}


def render(w, path, q):
    """(title, body) of a page of world w, drawn from one snapshot (redrawn if the history was rolled back
    while it was drawn)."""
    fn = PAGES.get(path) or next((f for prefix, f in ROUTES if path.startswith(prefix)), None)
    if fn is None:
        return None
    args = (w, q) if path in PAGES else (w, q, path.split('/', 2)[2])
    for attempt in range(3):
        w.reload()                                     # the latest committed generation, as one snapshot
        try:
            return fn(*args)
        except ArchiveChanged:                         # rolled back while drawn: draw it again
            if attempt == 2:
                raise


def main():
    import observer_app                                # the server half: world library, jobs, HTTP
    observer_app.main()


if __name__ == '__main__':
    main()
