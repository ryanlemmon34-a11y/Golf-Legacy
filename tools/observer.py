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
import observer_data as OD                                            # noqa: E402
import observer_history as OH                                         # noqa: E402
import observer_golf as OG                                            # noqa: E402
from golfsim import scopes as SC                                      # noqa: E402
import observer_views as V                                            # noqa: E402
import observer_cohort as OC                                          # noqa: E402
import observer_compare as OCMP                                       # noqa: E402
import observer_goat as GOAT                                          # noqa: E402
import observer_qual as OQ                                            # noqa: E402

PAGE_SIZE = 100

CSS = """
.rgrid { display:grid; grid-template-columns:repeat(auto-fill, minmax(290px, 1fr)); gap:10px; margin:6px 0; }
.rgrid .card { margin:0; padding:8px 10px; } .rgrid h4 { margin:0 0 4px; font-size:13px; color:var(--muted); text-transform:uppercase; letter-spacing:.04em; }
table.mini { margin:0; font-size:13px; } table.mini td, table.mini th { padding:1px 4px; border:none; }
form.inline { display:inline; margin-left:8px; } form.inline button { font-size:13px; padding:1px 8px; }
.views { margin:4px 0 10px; font-size:13px; } .views > a { margin-right:6px; padding:1px 8px; border:1px solid var(--line); border-radius:10px; }
.views > a.on { background:var(--panel); font-weight:600; } .views input { font-size:13px; width:11em; }
p.back { margin:0 0 4px; font-size:13px; }
p.notice { padding:6px 10px; border:1px solid var(--line); border-radius:4px; background:var(--panel); }
.up { color:var(--accent); } .down { color:#b3412f; } p.lead { font-size:16px; }
table.sortable th { cursor:pointer; } table.sortable th[aria-sort=ascending]::after { content:" ▲"; }
table.sortable th[aria-sort=descending]::after { content:" ▼"; }
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
main { padding:16px 32px; flex:1; min-width:0; }   /* wide screens: the page uses the width it has */
main p, main > ul, main > ol, main li, dl.kv, .banner { max-width:110ch; }   /* prose at a reading width */
main td p, main td li { max-width:none; }
main td { max-width:80ch; } main td:has(table, .scroll, svg) { max-width:none; }   /* a text column wraps at a reading width instead of running across a wide screen */
a { color:var(--accent); text-decoration:none; } a:hover { text-decoration:underline; }
a:focus-visible, button:focus-visible, input:focus-visible, select:focus-visible { outline:2px solid var(--accent); outline-offset:2px; }
.scroll { overflow-x:auto; }
table { border-collapse:collapse; width:auto; min-width:min(100%, 760px); margin:8px 0 18px; }   /* columns as wide as they need: a short table is not stretched across a wide screen */
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
        self._builder, self._stats_db = None, None
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

    def statistics(self):
        """(store connection, None) when the statistics cover every season of this snapshot's history; (None,
        progress) while they are built in the background (started here); (None, None) without history."""
        if not self.a:
            return None, None
        import observer_stats as ST
        path = ST.cache_path(self)
        if self._builder is None:
            self._builder = ST.Builder(self.archive_dir, path)
        if self._stats_db is None and path.exists():
            self._stats_db = ST.StatsStore(path).db
        want = {y: ST.season_source(self.a, y) for y in self.a.years}
        have = dict(self._stats_db.execute('SELECT year, source FROM years')) if self._stats_db else {}
        if all(have.get(y) == v for y, v in want.items()):
            return self._stats_db, None
        b = self._builder
        state = b.poll(want, have)
        if not b.running() and not (state.get('error') and state.get('for') == want):
            state['for'] = want
            b.start()
        return None, b.state

    def live_statistics(self):
        """The current season's statistics so far (observer_stats.live_tables), per snapshot."""
        if self.live is None:
            return None
        import observer_stats as ST
        if getattr(self, '_live_stats', (None,))[0] != self.live.generation:
            self._live_stats = (self.live.generation, ST.live_tables(self.live))
        return self._live_stats[1]

    def close(self):
        if self._stats is not None and self.a is not None:
            self._save_history_cache()                   # seasons read since: next time from the cache
        if self._builder is not None:
            self._builder.stop()
        if self._stats_db is not None:
            self._stats_db.close()
            self._stats_db = None
        if self.a is not None:
            self.a.close()
            self.a = None
        self._stats = None
        if self.session is not None:
            self.session.close()

    @property
    def stats(self):
        """The records' statistics over the published history: read from the cache beside the world when it
        matches (each season's signature), else from the history, and the cache written again."""
        if self._stats is None and self.a:
            path = self._history_cache()
            st = HistoryStats.from_cache(path, self.a) if path is not None else None
            if st is None:
                st = HistoryStats(self.a)
                st.dirty = True
            self._stats = st
            self._save_history_cache()
        return self._stats

    def _history_cache(self):
        import observer_stats as ST
        try:
            p = ST.cache_path(self)                       # (per world: the store's own name with another ending)
            return p.with_name(p.name.replace('stats.sqlite', 'history_stats.pkl')) if self.archive_dir else None
        except Exception:
            return None

    def _save_history_cache(self):
        st, path = self._stats, self._history_cache()
        if st is not None and path is not None and getattr(st, 'dirty', False):
            try:
                st.dump(path)
            except OSError:
                pass                                     # a cache only: the statistics stand without it

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

    @property
    def calendar_version(self):
        """The calendar this world plays (schedule.py): the running world's, else its history's (a history
        written before calendar versions is the classic calendar)."""
        v = getattr(self.live, 'calendar_version', None) if self.live is not None else None
        return v or ((self.a.world.get('calendar') if self.a else None) or 'v1')

    def major_rights(self, year, major):
        """{gid: right} of the rights ledger for one major edition (the running season's, else its season
        file's); {} where the season did not record one."""
        if self.live is not None and year == self.live.cursor['year']:
            book = getattr(self.live, 'major_rights', {}) or {}
            return OD.int_keys(book.get(major, {}))
        if self.a and year in self.a.years:
            book = self.a.year(year).get('major_rights') or {}
            return OD.int_keys(book.get(major, {}))
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
            coach, caddie = OD.by_person(e['team'], gid, (0, 0))
            out.append({'person': gid, 'site': k, 'pos': pos, 'total': tot, 'coach': coach, 'caddie': caddie,
                        'route': OD.by_person(e['routes'], gid)})
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
           '<a href="/rankings">Rankings</a><a href="/qualification">Qualification</a><a href="/stats">Stats</a>'
           '<a href="/money">Prize money</a>'
           '<h4>Explore</h4><a href="/golfers">Golfers</a><a href="/coaches">Coaches</a><a href="/caddies">Caddies</a>'
           '<a href="/courses">Courses</a><a href="/nations">Nations</a><a href="/tours">Tours</a>'
           '<a href="/tournaments">Tournaments</a>' + my_world_link(w) + '<a href="/views">Saved views</a>'
           '<h4>History</h4><a href="/seasons">Seasons</a><a href="/records">Record Book</a>'
           '<a href="/grand-slam">Career Grand Slam</a><a href="/moments">Moments</a><a href="/cohort">Where are they now</a>'
           '<a href="/compare">Compare careers</a><a href="/goat">GOAT Lab</a>'
           '<a href="/rules">Rules</a>'
           '<h4>Worlds</h4><a href="/worlds">World library</a><a href="/export">Report a problem</a>'
           '<a href="/job">Last operation</a></nav>')
    banners = ''.join(f'<div class="banner {esc(kind)}" role="status">{text}</div>' for kind, text in notices)
    running = job is not None and job.get('state') == 'running'
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" '
            f'content="width=device-width, initial-scale=1"><title>{esc(title)} — Golf Legacy</title>'
            f'<style>{CSS}</style></head><body><header><strong>Golf Legacy</strong>{world}'
            f'<span class="date">{esc(date)}</span>{search}{advance_controls(w, job)}</header>'
            f'<div class="layout">{nav}<main>{banners}<h1>{esc(title)}</h1>{body}'
            f'{history_note(w) if w is not None else ""}</main></div>{POLL_JS if running else ""}{V.SORT_JS}</body></html>')


def my_world_link(w):
    """The menu's My World entry, with a quiet count of digest items new since last read (no pop-ups)."""
    n = 0
    if w is not None and not w.read_only:
        import observer_myworld as MW
        key = (getattr(w.live, 'generation', None), w.a.stamp if w.a else None, json.dumps(shortlist(w)),
               json.dumps(shortlist_seen(w)))
        got = w.__dict__.get('_mw_count')
        if got is None or got[0] != key:
            got = (key, MW.new_count(w))
            w._mw_count = got
        n = got[1]
    return '<a href="/my-world">My World' + (f' <span class="muted">({n} new)</span>' if n else '') + '</a>'


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
    """headers: [label]; rows: [[cell html]]; numeric: column indexes right-aligned. Every table sorts by any
    column in the browser (numbers as numbers, missing values last; on a paged list, the page shown)."""
    h = ''.join(f'<th{" class=n" if i in numeric else ""} title="Sort by this column">{esc(x)}</th>'
                for i, x in enumerate(headers))
    body = ''.join('<tr>' + ''.join(f'<td{" class=n" if i in numeric else ""}>{c}</td>' for i, c in enumerate(r)) + '</tr>'
                   for r in rows)
    return f'<div class="scroll"><table class="sortable"><thead><tr>{h}</tr></thead><tbody>{body}</tbody></table></div>'


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
        out.append(f'<a href="{path}?default=1">Clear</a>')
    return ''.join(out) + '</form>'


SHORTLIST = 'observer_shortlist.json'
SHORT_TYPES = {'person': ('People', '/golfer/'), 'course': ('Courses', '/course/'), 'nation': ('Nations', '/nation/'),
               'tour': ('Tours', '/tour/'), 'series': ('Tournaments', '/series/'), 'edition': ('Editions', '/event/')}


def _shortlist_file(w):
    try:
        raw = json.loads((w.path / SHORTLIST).read_text())
    except (OSError, ValueError):
        return {'items': [], 'seen': None, 'flags': {}}
    items = [tuple(x) + ('',) * (4 - len(x)) for x in raw.get('items') or []]   # (format 1: no group)
    return {'items': [x[:4] for x in items], 'seen': raw.get('seen'), 'flags': dict(raw.get('flags') or {})}


def shortlist(w):
    """[(type, id, added, group)] kept for this world (a file in its folder: it travels with copies and diagnostic
    packages; names are looked up when shown, so they stay current and retired people stay listed). Everything
    shortlisted is followed in My World; group '' is ungrouped."""
    if w is None or w.read_only:
        return []
    return _shortlist_file(w)['items']


def shortlist_seen(w):
    """[year, week]: My World's digest was last marked read after that week (None: never)."""
    if w is None or w.read_only:
        return None
    return _shortlist_file(w)['seen']


def shortlist_flags(w):
    """{name: value}: My World's own notes (e.g. a dismissed notice)."""
    if w is None or w.read_only:
        return {}
    return _shortlist_file(w)['flags']


def _write_shortlist(w, items, seen, flags=None):
    import os
    flags = _shortlist_file(w)['flags'] if flags is None else flags
    tmp = w.path / (SHORTLIST + '.tmp')
    tmp.write_text(json.dumps({'format': 'golf-legacy-shortlist/2', 'items': [list(x) for x in items], 'seen': seen,
                               'flags': flags}, indent=1))
    os.replace(tmp, w.path / SHORTLIST)
    w.__dict__.pop('_mw_count', None)


def set_shortlist(w, kind, ident, on, group=None):
    if w is None or w.read_only or kind not in SHORT_TYPES:
        return False
    import time as _t
    f = _shortlist_file(w)
    old = next((x for x in f['items'] if x[0] == kind and str(x[1]) == str(ident)), None)
    items = [x for x in f['items'] if x is not old]
    if on:
        items.append((kind, str(ident), old[2] if old else _t.strftime('%Y-%m-%d %H:%M'),
                      (group if group is not None else (old[3] if old else '')).strip()[:40]))
    _write_shortlist(w, items, f['seen'])
    return True


def dismiss_hidden_period(w):
    """My World: stop offering the period an earlier version's results setting may have kept from the digest."""
    if w is None or w.read_only:
        return False
    f = _shortlist_file(w)
    _write_shortlist(w, f['items'], f['seen'], {**f['flags'], 'hidden_period_dismissed': True})
    return True


def mark_read(w):
    """My World: the digest is read up to the latest week played."""
    if w is None or w.read_only:
        return False
    import observer_myworld as MW
    f = _shortlist_file(w)
    _write_shortlist(w, f['items'], list(MW.now(w)))
    return True


def shortlist_button(w, kind, ident):
    if w is None or w.read_only:
        return ''
    on = any(k == kind and str(i) == str(ident) for k, i, *_ in shortlist(w))
    return (f'<form method="post" action="/shortlist" class="inline"><input type="hidden" name="kind" value="{esc(kind)}">'
            f'<input type="hidden" name="id" value="{esc(ident)}"><input type="hidden" name="on" value="{"0" if on else "1"}">'
            f'<button title="{"Remove from" if on else "Add to"} this world’s shortlist">{"★ Shortlisted" if on else "☆ Shortlist"}'
            '</button></form>')


def shortlist_page(w, q):
    import observer_myworld as MW
    return MW.page(w, q)


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
                [str(e['week']), event_link(w, e['id']), tour_link(w, e['tour']),
                 w.person_link(_winner(e))] for e in recent]))
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
                                           for k, t in (('world', 'World'), ('points', 'World: points by week'),
                                                        ('amateur', 'Amateur'))) + '</div>')
    if kind == 'points':
        return 'World ranking points', tabs + OG.rankings_points_page(w, q)
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
    clients = {}
    if w.live and role in ('coach', 'caddie'):
        for g, s_ in (w.live.coach_of if role == 'coach' else w.live.caddie_of).items():
            clients[s_] = clients.get(s_, 0) + 1
    rep_of = lambda r: (r[1].get(role) or {}).get('reputation') if role in ('coach', 'caddie') else None
    key = {'name': lambda r: (r[1]['name'], r[0]), 'born': lambda r: (-(r[1].get('born') or 0), r[0]),
           'rank': lambda r: (wr.get(r[0], 10 ** 9), r[1]['name'], r[0]),
           'reputation': lambda r: (rep_of(r) is None, -(rep_of(r) or 0), r[1]['name'], r[0]),
           'clients': lambda r: (-clients.get(r[0], 0), r[1]['name'], r[0])}.get(sort, lambda r: (r[1]['name'], r[0]))
    rows.sort(key=key)
    nations = sorted({p.get('country') for _, p, _ in rows} | ({nation} if nation else set()) - {None})
    path = {None: '/golfers', 'golfer': '/golfers', 'coach': '/coaches', 'caddie': '/caddies'}[role]
    statuses = sorted({s for _, _, s in rows if s} | ({status} if status else set()))
    fields = [('q', 'Name contains', None), ('nation', 'Nation', [('', 'any')] + [(n, n) for n in nations])]
    if role == 'golfer':
        fields.append(('tour', 'Tour now', [('', 'any')] + sorted(((k, t.get('name', k)) for k, t in w.tours().items()),
                                                                 key=lambda x: x[1])))
    fields.append(('status', 'Status now', [('', 'any')] + [(s, s) for s in statuses]))
    fields.append(('sort', 'Sort', [(k, t) for k, t in (('rank', 'world ranking'), ('name', 'name'), ('born', 'youngest first'),
                                                       ('reputation', 'reputation'), ('clients', 'clients now'))
                                    if (role == 'golfer' and k in ('rank', 'name', 'born'))
                                    or (role in ('coach', 'caddie') and k != 'rank') or (role is None and k in ('name', 'born'))]))
    chunk, pager = paged(rows, q, path)
    if role in ('coach', 'caddie'):
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


def now_year(w):
    if w.live is not None:
        return w.live.cursor['year']
    return (w.a.years[-1] + 1) if w.a else None


AGE_NOTE = ('Ages are the season’s year minus the birth year: birth dates are not recorded, so an age can be one '
            'year more than the true one (approximate).')


def age_text(w, born, year=None):
    year = year or now_year(w)
    return f'{year - born}*' if born and year else '—'


def money(x, known=True):
    """Dollars, the world's one currency: $1,234,567 (-$1,234 below zero); unknown kept apart from zero."""
    if not known or x is None:
        return '<span class="muted" title="could not be reconciled with the money paid">unknown</span>'
    return f'-${-x:,.0f}' if x < 0 else f'${x:,.0f}'


def results_link(pid, label, **filters):
    qs = urlencode({'tab': 'results', **{k: v for k, v in filters.items() if v not in (None, '')}})
    return f'<a href="/golfer/{pid}?{qs}">{label}</a>'


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
    if tab == 'season':
        tabs.insert(1, ('season', f'Season {esc(one(q, "year", ""))}', 'golfer'))
    out = []
    a = w.a
    initial = a and pid in a.people and a.people[pid].get('initial')
    out.append(f'<p class="lead">Age {age_text(w, p.get("born"))} · born {esc(p.get("born"))} · '
               f'{nation_link(p.get("country"))} · {esc(", ".join(roles))}'
               + (' · <span class="tag">career began before the archive</span>' if initial else '')
               + (' · <span class="tag">retired</span>' if OD.playing_status(p.get('golfer'))[0] == 'retired' else '')
               + (f' · <a href="/compare?ids={pid}">compare</a>' if 'golfer' in roles else '')
               + '</p>' + shortlist_button(w, 'person', pid))
    geo = w.geography(pid)
    if geo:
        out.append(f'<p>Nationality: {esc(p.get("country"))} · born in {esc(where(geo["birthplace"]))}'
                   f' · lives in {esc(where(geo["residence"]))}</p>')
    gs = p.get('golfer')
    if gs and w.live and pid in w.live.people:
        coach, caddie = w.live.coach_of.get(pid), w.live.caddie_of.get(pid)
        now = [f'world No. {w.live.wr[pid]}'] if pid in w.live.wr else []
        now += ([f'coach {w.person_link(coach)}'] if coach else []) + ([f'caddie {w.person_link(caddie)}'] if caddie else [])
        if now:
            out.append('<p>Now: ' + ' · '.join(now) + '</p>')
    out.append('<div class="tabs">' + ''.join(
        f'<a href="/golfer/{pid}?tab={k}{"&year=" + quote(one(q, "year", "")) if k == "season" else ""}" '
        f'class="{"on" if k == tab else ""}">{t}</a>' for k, t, r in tabs if r in roles) + '</div>')
    if tab == 'playing':
        out.append(_playing(w, q, pid, p))
        out.append(OH.residence_section(w, pid, p, geo))
    elif tab == 'season':
        out.append(OH.season_view(w, q, pid, p))
    elif tab == 'results':
        out.append(_results(w, q, pid))
    elif tab == 'team':
        out.append(OH.team_history(w, pid))
    elif tab in ('coaching', 'caddying'):
        out.append(_staff(w, pid, 'coach' if tab == 'coaching' else 'caddie'))
        if 'golfer' not in roles:
            out.append(OH.residence_section(w, pid, p, geo))
    if a and a.index and tab == 'playing':
        moments_ = a.index.moments(person=pid)
        if moments_:
            out.append('<h2>Moments</h2>' + table(['Season', 'What', 'Event', 'Venue'], [
                [esc(m['year']), esc(m['kind']), event_link(w, m['event']), venue_link(w, m.get('layout'))]
                for m in moments_], numeric=(0,)))
    out.append(f'<p class="muted">* {AGE_NOTE}</p>')
    return w.name(pid), ''.join(out)


def when(t):
    """A (year, week) date; week 53 is the season's end."""
    return f'end of {t[0]}' if t[1] >= 53 else f'{t[0]} wk {t[1]}'


def venue_link(w, layout_id):
    """A moment's course and layout ('course:layout'), or not applicable."""
    if not layout_id or ':' not in str(layout_id):
        return '<span class="muted">not applicable</span>'
    cid, lay = str(layout_id).split(':', 1)
    return course_link(w, cid, lay)


def _ratings(w, pid, p):
    from golfsim.ratings import ATTRIBUTE_GROUPS, ATTRIBUTE_KEYS, ATTRIBUTE_LABELS
    keys = (w.a.world.get('rating_keys') if w.a else None) or ['overall', *ATTRIBUTE_KEYS]
    lp = w.live.people.get(pid, {}) if w.live else {}
    cur = lp.get('ratings')
    snaps = OD.rating_snapshots(w, pid)
    y = now_year(w)
    peak = peak_line(w, pid, p)
    if cur is None:
        if snaps:
            last = max(snaps)
            return (f'<h2>Ratings</h2><p class="muted">No current ratings (not competing). Last recorded at the start of '
                    f'{last}: overall {snaps[last][0]}.</p>' + peak)
        return ('<h2>Ratings</h2>' + peak) if peak else ''
    now = dict(zip(['overall', *ATTRIBUTE_KEYS], cur))
    base = dict(zip(keys, snaps[y])) if y in snaps else None
    prev = dict(zip(keys, snaps[y - 1])) if (y - 1) in snaps else None

    def delta(a, b):
        if a is None or b is None:
            return '<span class="muted">unavailable</span>'
        d = round(a - b, 1)
        cls = 'up' if d > 0 else 'down' if d < 0 else 'muted'
        return f'<span class="{cls}">{d:+.1f}</span>'
    groups = {}
    for k in ATTRIBUTE_KEYS:
        groups.setdefault(ATTRIBUTE_GROUPS[k], []).append(k)
    cards = []
    for g, ks in groups.items():
        rows = ''.join(f'<tr><td>{esc(ATTRIBUTE_LABELS[k])}</td><td class="n"><strong>{now[k]:.1f}</strong></td>'
                       f'<td class="n">{delta(now[k], base and base.get(k))}</td>'
                       f'<td class="n">{delta(base and base.get(k), prev and prev.get(k))}</td></tr>' for k in ks)
        cards.append(f'<div class="card"><h4>{esc(g)}</h4><table class="mini"><tr><th></th><th class="n">Now</th>'
                     f'<th class="n">Season</th><th class="n">Last</th></tr>{rows}</table></div>')
    arche = lp.get('archetype')
    note = (f'Season: change since the start of {y}. Last: from the start of {y - 1} to the start of {y}. Ratings at the '
            'start of a season are recorded when the season before it is archived (after its season-end aging); '
            '“unavailable” where there is no such record (the world’s first season, or seasons archived before '
            'ratings were recorded). Potential is never shown.')
    return (f'<h2>Ratings</h2><p>Overall <strong>{now["overall"]:.1f}</strong> · this season '
            f'{delta(now["overall"], base and base.get("overall"))} · last season '
            f'{delta(base and base.get("overall"), prev and prev.get("overall"))}'
            + (f' · archetype {esc(arche)}' if arche else '') + '</p>' + peak
            + f'<div class="rgrid">{"".join(cards)}</div><p class="muted">{note}</p>')


def peak_line(w, pid, p):
    """The profile's Peak Overall: the highest recorded base Overall, when it was first recorded and the age then,
    with how much of the career the records cover (a partial record says "Recorded Peak Overall")."""
    pk = OD.recorded_peak(w, pid)
    if pk is None:
        return ''
    y, wk = pk['year'], pk['week']
    when = (f'the start of {y}' if wk == 0 else f'the end of the {y} season' if wk >= 52 else f'{y}, week {wk}')
    if pk['source'] == 'current':
        when = f'now ({y}, week {wk})'
    born = p.get('born')
    age = f', age {y - born}*' if born else ''
    label = 'Peak Overall' if pk['complete'] else 'Recorded Peak Overall'
    if pk['complete']:
        cover = (f'covers the whole career: ratings are noted from {pk["first"]}, when this golfer arrived, just '
                 'before every lasting injury and at every season’s end before and after aging (the only times they '
                 'can fall), so the peak is exact')
    elif pk['since'] is not None:
        cover = (f'noted since {pk["since"]} (before every lasting injury and at every season’s end, before and '
                 'after aging)'
                 + (f'; before that, start-of-season ratings from {pk["snapshots"][0]}' if pk['snapshots']
                    and pk['snapshots'][0] < pk['since'] else '')
                 + ('; the career began before the world’s records, so an earlier peak is not known' if pk['initial']
                    else '; earlier seasons were played before peaks were kept' if pk['first'] is not None
                    and pk['first'] < pk['since'] else ''))
    elif pk['snapshots']:
        cover = (f'from start-of-season ratings only ({span(pk["snapshots"], False)})'
                 + (' and the current rating' if pk['source'] == 'current' or (w.live and w.live.people.get(pid, {})
                                                                                .get('ratings')) else '')
                 + ': the peak between them is not known')
    else:
        cover = 'only the current rating is recorded: the peak may have been higher'
    return (f'<p>{label} <strong>{pk["value"]:.1f}</strong> · first recorded at {esc(when)}{age}</p>'
            f'<p class="muted">The base Overall (no form, staff or play effects); a value reached again keeps its first '
            f'date. Coverage: {esc(cover)}. {esc(AGE_NOTE)}</p>')


def _honors(w, pid, rows, active):
    hs = OD.honors(rows)
    if not hs:
        return '<h2>Career honors</h2><p class="muted">None recorded yet.</p>'
    out = []
    for key, label, wins in hs:
        years = [y for y, _ in wins]
        eds = ', '.join(event_link(w, e) for _, e in wins[-3:])
        out.append([esc(label), results_link(pid, str(len(wins)), outcome='win', honor=key), str(min(years)),
                    str(max(years)), eds + (f' … {results_link(pid, "all", outcome="win", honor=key)}' if len(wins) > 3 else '')])
    initial = w.a and pid in w.a.people and w.a.people[pid].get('initial')
    return ('<h2>Career honors</h2>' + table(['Honor', 'Wins', 'First', 'Latest' if active else 'Last', 'Most recent'],
                                              out, numeric=(1, 2, 3))
            + '<p class="muted">From recorded wins, by each event’s classification when it was played'
            + ('; this career began before the world’s records, so earlier wins are not included' if initial else '')
            + '.</p>')


def _season_history(w, q, pid, p, rows):
    db, building = w.statistics()
    mp = one(q, 'scope') == SC.MAJORS_PREMIER          # the shared Majors + Premier scope: those editions only
    if mp:
        keep = SC.majors_premier_tours()
        rows = [r for r in rows if (r['tour'] or '') in keep]
    OD.cut_flags(w, rows, db)
    roll = OD.season_rollup(rows)
    seasons = {r['year']: r for r in (w.a.index.seasons(pid) if w.a and w.a.index and pid in w.a.people else [])}
    stored = ST_person_seasons(db, pid) if db is not None else {}
    born = p.get('born')
    expand = one(q, 'tours') == '1'
    cur_year = w.live.cursor['year'] if w.live else None
    live_prize = w.live.prize.get(pid, 0.0) if w.live else None   # (no ledger yet: paid nothing, as archived)
    live_rec = (w.live_statistics() or [None, {}])[1] if w.live else {}
    out = []
    career = dict.fromkeys(OD.ST.COLUMNS, 0)
    career_prize, prize_unknown = 0.0, False
    by_tour = {}                                     # tour -> [stats, prize so far, all known]

    def cells(y, t, agg, prize_cell):
        scope_t = t or (SC.MAJORS_PREMIER if mp else None)
        link = lambda label, outcome=None: results_link(pid, label, year=y, tour=scope_t, outcome=outcome)
        cut = f'{agg["cuts_made"]}/{agg["cut_events"]}' if agg['cut_events'] else '—'
        missed = link(str(agg['cut_events'] - agg['cuts_made']), 'missed-cut') if agg['cut_events'] else '—'
        return [link(str(agg['starts'])), link(str(agg['wins']), 'win'), link(str(agg['runner_ups']), 'runner-up'),
                link(str(agg['top2']), 'top2'), link(str(agg['top5']), 'top5'), link(str(agg['top10']), 'top10'),
                cut, missed, prize_cell]
    def tour_prize(y, t, live):
        if live:
            known = bool(live_rec.get(pid))
            return ((w.live_statistics()[0].get((pid, t)) or {}).get('prize') if known else None), known
        if y in stored and t in stored[y]['tours']:
            tp = stored[y]['tours'][t]['prize']
            return tp, tp is not None
        return None, False

    for y in sorted(set(roll) | (set() if mp else set(seasons))):
        r = roll.get(y, {'all': dict.fromkeys(OD.ST.COLUMNS, 0), 'tours': {}})
        info = seasons.get(y, {})
        live = y == cur_year
        if mp:                                       # the scope's own events' payouts, where every one is known
            parts = [tour_prize(y, t, live) for t in r['tours']]
            prize = sum(tp or 0.0 for tp, _ in parts) if all(k for _, k in parts) else None
        elif live:
            prize = live_prize
        elif y in stored:
            prize = stored[y]['prize']
        else:
            prize = info.get('prize')
        a = r['all']
        for c in OD.ST.COLUMNS:
            career[c] += a[c]
        if prize is None:
            prize_unknown = prize_unknown or bool(a['starts'])
        else:
            career_prize += prize
        tours = sorted(r['tours'])
        label = (f'<a href="/golfer/{pid}?tab=season&year={y}" title="This season as it was">{y}</a>'
                 + (' <span class="tag">so far</span>' if live else ''))
        tour_cell = ', '.join(tour_link(w, t) for t in tours if t) or (tour_link(w, info.get('tour')) if info.get('tour') else '—')
        out.append([label, age_text(w, born, y), tour_cell, esc(info.get('status') or (p.get('golfer') or {}).get('status')
                                                                if live else info.get('status') or '')]
                   + cells(y, None, a, money(prize) if prize is not None else '<span class="muted">—</span>')
                   + [esc(info.get('wr_end') or (w.live.wr.get(pid) if live and w.live else '') or '—')])
        for t in tours:
            tp, known = tour_prize(y, t, live)
            bt = by_tour.setdefault(t, [dict.fromkeys(OD.ST.COLUMNS, 0), 0.0, True])
            for c in OD.ST.COLUMNS:
                bt[0][c] += r['tours'][t][c]
            if known:
                bt[1] += tp or 0.0
            else:
                bt[2] = False
            if expand and len(tours) > 1:
                out.append(['', '', '&nbsp;&nbsp;↳ ' + tour_link(w, t), ''] + cells(y, t, r['tours'][t],
                                                                                  money(tp, known) if db or live else '…')
                           + [''])
    if not out:
        return '<h2>Season by season</h2><p class="muted">No seasons played yet.</p>'
    out.append(['<strong>Career</strong>', '', f'{len(by_tour)} tour{"s" if len(by_tour) != 1 else ""}', '']
               + cells(None, None, career, money(career_prize, not prize_unknown)) + [''])
    if expand:
        for t, (agg, tp, known) in sorted(by_tour.items(), key=lambda x: (w.tours().get(x[0], {}).get('tier', 9), x[0])):
            out.append(['', '', '&nbsp;&nbsp;career ↳ ' + tour_link(w, t), ''] + cells(None, t, agg, money(tp, known and bool(db or w.live)))
                       + [''])
    sc = {'scope': SC.MAJORS_PREMIER} if mp else {}
    toggle = (f'<a href="/golfer/{pid}?{urlencode({"tab": "playing", **sc})}">hide tours</a>' if expand else
              f'<a href="/golfer/{pid}?{urlencode({"tab": "playing", "tours": 1, **sc})}">show each tour</a>')
    toggle = scope_buttons(f'/golfer/{pid}', {**q, 'tab': ['playing']}, one(q, 'scope'), 'scope') + toggle
    note = ('Click a season to see it as it was (that season\'s tour, rights, ratings, team and decisions). Starts '
            'exclude qualifying stages. Top 2/5/10 include wins (do not add them up); runner-up is a recorded second '
            'place (ties included). Cuts: made / stroke-play events with a cut; missed cuts are the rest of those '
            'events. Prize money is gross tournament prize money; per tour it is each event\'s recorded payout (or, for '
            'seasons played before payouts were recorded, the payouts recomputed and shown only where they match the '
            'money paid). The career row adds every season once; career by tour adds each tour\'s seasons.')
    if mp:
        note += (f' {SC.LABEL}: only majors and Premier events, by each edition\'s classification when played (a '
                 'Challenger member\'s major and Premier starts count; a Premier member\'s regional starts do not); '
                 'prize money is those events\' payouts. World ranking and ratings stay global.')
    if building and expand:
        note += f' Prize money by tour is being worked out ({building["done"]} of {building["total"]} seasons).'
    return (f'<h2>Season by season</h2><p>{toggle}</p>' + table(
        ['Season', 'Age*', 'Tour(s)', 'Status', 'Starts', 'Wins', 'Runner-up', 'Top 2', 'Top 5', 'Top 10', 'Cuts',
         'Missed cuts', 'Prize money', 'World (end)'], out, numeric=(1, 4, 5, 6, 7, 8, 9, 11, 12, 13))
        + f'<p class="muted">{note}</p>')


def ST_person_seasons(db, pid):
    import observer_stats as ST
    return ST.person_seasons(db, pid)


def _playing(w, q, pid, p):
    rows = OD.results(w, pid)
    active = (p.get('golfer') or {}).get('lifestyle') not in (None, 'retired')
    out = [OH.status_section(w, pid, p), _ratings(w, pid, p), _honors(w, pid, rows, active),
           OH.grand_slam_line(w, pid), _season_history(w, q, pid, p, rows),
           OG.golf_section(w, pid, one(q, 'scope'))]
    wins = [r for r in rows if r['pos'] == 1 and not OD.is_qualifying(r)]
    if wins:
        out.append(f'<h2>Wins ({len(wins)})</h2>' + table(['Season', 'Event', 'Tour then'], [
            [esc(r['year']), event_link(w, r['event']), tour_link(w, r['tour'])] for r in reversed(wins)]))
    out.append(OG.ranking_section(w, pid))
    return ''.join(out)


def _results(w, q, pid):
    rows = OD.results(w, pid)
    year, tour, outcome, honor = one(q, 'year'), one(q, 'tour'), one(q, 'outcome'), one(q, 'honor')
    sid = one(q, 'series')
    quals = one(q, 'quals') == '1'                     # qualifying stages: shown only on request (not starts)
    sel = rows if quals else [r for r in rows if not OD.is_qualifying(r)]
    if year:
        sel = [r for r in sel if str(r['year']) == year]
    if sid:
        sel = [r for r in sel if r['series'] == sid]
    if tour:
        within = SC.tours_for(tour)
        sel = [r for r in sel if (r['tour'] or '') in within]
    if outcome in OD.OUTCOMES:
        test = OD.OUTCOMES[outcome]
        sel = [r for r in sel if test(r['pos']) and not OD.is_qualifying(r)]
        if outcome in ('made-cut', 'missed-cut'):
            db, _ = w.statistics()
            sel = [r for r in OD.cut_flags(w, sel, db) if r['cut']]
    if honor:
        tests = {k: t for k, _, t in OD.HONORS}
        keys = [k for k, _, _ in OD.HONORS]
        def first_honor(r):
            for k in keys:
                if tests[k]({'category': r.get('category'), 'tier': r.get('tier'), 'name': r.get('name')}):
                    return k
        sel = [r for r in sel if r['pos'] == 1 and not OD.is_qualifying(r) and first_honor(r) == honor]
    if not rows:
        return '<p class="muted">No starts yet.</p>'
    sel = list(reversed(sel))
    chunk, pager = paged(sel, q, f'/golfer/{pid}', size=50)
    db, _ = w.statistics()
    prizes = OD.start_prizes(w, pid, chunk, db)
    years = sorted({r['year'] for r in rows}, reverse=True)
    tours = sorted({r['tour'] for r in rows if r['tour']})
    f = filters(f'/golfer/{pid}', {**q, 'tab': ['results']}, [
        ('year', 'Season', [('', 'all')] + [(str(y), str(y)) for y in years]),
        ('tour', 'Tour then', [('', 'all'), (SC.MAJORS_PREMIER, SC.LABEL)]
         + [(t, w.tours().get(t, {}).get('name', t)) for t in tours]),
        ('outcome', 'Finish', [('', 'any'), ('win', 'wins'), ('runner-up', 'runner-up'), ('top2', 'top 2'), ('top5', 'top 5'),
                               ('top10', 'top 10'), ('made-cut', 'made cut'), ('missed-cut', 'missed cut')])])
    f = f.replace('<button>Apply</button>', '<input type="hidden" name="tab" value="results">'
                  + ('<input type="hidden" name="quals" value="1">' if quals else '') + '<button>Apply</button>')
    if honor:
        f += f'<p>Honor: {esc(dict((k, l) for k, l, _ in OD.HONORS).get(honor, honor))} · <a href="/golfer/{pid}?tab=results">clear</a></p>'
    if sid:
        f += f'<p>Tournament: <a href="/series/{quote(sid)}">{esc(w.series_name(sid))}</a> · <a href="/golfer/{pid}?tab=results">clear</a></p>'
    n_quals = sum(1 for r in rows if OD.is_qualifying(r))
    toggle = urlencode({**{k: v[0] for k, v in q.items() if k not in ('quals', 'page')}, 'tab': 'results',
                        **({} if quals else {'quals': '1'})})
    scope = (f'qualifying stages included and marked ({n_quals:,}; not starts) · '
             f'<a href="/golfer/{pid}?{toggle}">starts only</a>' if quals else
             f'starts only, as counted on the profile' + (f' · <a href="/golfer/{pid}?{toggle}">include the '
                                                          f'{n_quals:,} qualifying stages</a>' if n_quals else ''))
    shown = (f'{len(sel):,} rows of {len(rows) - n_quals:,} starts and {n_quals:,} qualifying stages' if quals else
             f'{len(sel):,} of {len(rows) - n_quals:,} starts')
    return (f + f'<p>{shown} (archived seasons and the current season; {scope}).</p>' + table(
        ['Season', 'Week', 'Event', 'Tour then', 'Pos', 'Prize', 'Coach', 'Caddie', 'How they got in'],
        [[esc(r['year']), esc(r['week']), event_link(w, r['event']) + (' <span class="tag">qualifying</span>'
                                                                          if OD.is_qualifying(r) else ''),
          tour_link(w, r['tour']), esc(r['pos'] or 'MC'),
          money(prizes[(r['event'], r['site'])]) if (r['event'], r['site']) in prizes
                  else '<span class="muted">—</span>',
          w.person_link(r['coach']), w.person_link(r['caddie']), OH.route_html(r['route'], w.calendar_version)]
         for r in chunk], numeric=(0, 1, 4, 5)) + pager
        + '<p class="muted">Prize: the money paid for the start, as recorded (since rules 2026-10-30); for older seasons '
          'the start’s share of the purse recomputed from the event’s finish and checked against the money paid that '
          'season, “—” where that cannot be confirmed (or the statistics are still being built). How they got in: the '
          'rule in words, linked to the rules page, with the code recorded at the time.</p>')


def _staff(w, pid, role):
    out = []
    p = w.person(pid) or {}
    info = p.get(role, {})
    out.append(f'<p>{esc(role.title())} · status {esc(info.get("status"))}'
               + (f' · reputation {esc(info.get("reputation"))}' if info.get('reputation') is not None else '')
               + (f' · {esc(info.get("background"))}' if info.get('background') else '') + '</p>')
    stints = w.a.staff_clients(pid, role) if w.a and pid in w.a.people else []
    if w.live:
        now = sorted((g for g, s in (w.live.coach_of if role == 'coach' else w.live.caddie_of).items() if s == pid),
                     key=lambda g: (w.live.wr.get(g, 10 ** 9), g))
        since = {c['stint'].golfer: c['stint'].start for c in stints if c['stint'].end is None}
        out.append(f'<h2>Current {"clients" if role == "coach" else "player"} ({len(now)})</h2>' + (table(
            ['Golfer', 'Tour', 'Status', 'World', 'Since'],
            [[w.person_link(g), tour_link(w, w.live.people.get(g, {}).get('tour')),
              esc(f'{w.live.people.get(g, {}).get("status")} / {w.live.people.get(g, {}).get("lifestyle")}'),
              esc(w.live.wr.get(g, '—')), esc(when(since[g]) if g in since else 'this season')]
             for g in now], numeric=(3,)) if now else '<p class="muted">Nobody at the moment.</p>')
            + '<p class="muted">Current assignments as of the date in the header. Dated partnerships below are the '
              'recorded history; results show the team at each event.</p>')
    if stints:
        out.append(f'<h2>All partnerships (through {w.a.years[-1]})</h2>' + table(
            ['Player', 'From', 'To', 'Starts together', 'Wins', 'Majors'],
            [[w.person_link(c['stint'].golfer), when(c['stint'].start),
              when(c['stint'].end) if c['stint'].end else 'still together',
              str(c['starts']), str(len(c['wins'])), str(len(c['majors']))] for c in stints], numeric=(3, 4, 5))
            + '<p class="muted">Results during a partnership are the client’s achievements, association not proof of '
              'cause. Starts together count the archived seasons.</p>')
        out.append(_staff_seasons(w, pid, role, stints))
    if w.a and pid in w.a.people:
        hist = (w.a.people[pid].get(role) or {}).get('history') or []
        if hist:
            out.append('<h2>Staff career</h2><ul>' + ''.join(f'<li>{esc(y)}: {esc(t)}</li>' for y, t in hist) + '</ul>')
    else:
        out.append('<p class="muted">Dated partnerships are archived when the season ends; until then each result shows '
                   'the team that week.</p>')
    return ''.join(out)


def _staff_seasons(w, pid, role, stints):
    """Season by season: clients that season, starts served and wins during the actual partnerships, and the
    staff member's own recorded season (weeks, rounds, reputation, earnings)."""
    import observer_stats as ST
    by = {}
    for c in stints:
        s = c['stint']
        first, last = s.start[0], (s.end[0] if s.end else w.a.years[-1])
        for y in range(first, last + 1):
            by.setdefault(y, {'clients': set(), 'starts': 0, 'wins': 0})['clients'].add(s.golfer)
    kind = 'coach' if role == 'coach' else 'caddie'
    for c in stints:
        s = c['stint']
        for r in w.a.results(s.golfer):
            if r[kind] == pid and (r['year'], r['week']) >= s.start and (s.end is None or (r['year'], r['week']) < s.end):
                d = by.setdefault(r['year'], {'clients': set(), 'starts': 0, 'wins': 0})
                d['starts'] += 1
                d['wins'] += r['pos'] == 1
    db, _ = w.statistics()
    own = ST.staff_seasons(db, pid, kind) if db is not None else {}
    rows = []
    for y in sorted(set(by) | set(own)):
        d, o = by.get(y, {'clients': set(), 'starts': 0, 'wins': 0}), own.get(y, {})
        rows.append([esc(y), str(len(d['clients'])), str(d['starts']), str(d['wins']),
                     esc(o.get('weeks') if o.get('weeks') is not None else '—'),
                     esc(o.get('reputation') if o.get('reputation') is not None else '—'),
                     money(o.get('earnings')) if o.get('earnings') is not None else '<span class="muted">—</span>'])
    return ('<h2>Season by season</h2>' + table(['Season', 'Clients', 'Starts served', 'Client wins', 'Weeks worked',
                                                 'Reputation', 'Earnings'], rows, numeric=(0, 1, 2, 3, 4, 5, 6))
            + '<p class="muted">Clients, starts and wins from the dated partnerships and the team recorded at each event; '
              'weeks, reputation and earnings as recorded for the season (earnings only where two consecutive seasons '
              'recorded career totals).</p>')


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
           f'{"current season" if e["source"] == "current season" else "archived season"} · '
           f'<a href="/cohort?event={quote(eid)}">where is this field now?</a>{shortlist_button(w, "edition", eid)}</p>']
    view = one(q, 'view', 'final')
    replay = view == 'rounds'                          # a replay shows nothing beyond the round shown
    restart = (f' · <a href="/event/{quote(eid)}?view=rounds&amp;round=1">Watch from round 1</a>'
               if not e.get('match_play') else '')     # (the replay always starts again at round one)
    fmt = []
    if e.get('rounds'):
        fmt.append(f'{e["rounds"] * 18} holes')
    if e.get('match_play') is not None:
        fmt.append('match play' if e['match_play'] else 'stroke play')
    out.append(f'<p>{e["year"]} week {e["week"]} · {tour_link(w, e.get("tour"))} · tier {esc(e.get("tier"))} · '
               f'{esc(e.get("category"))} · prestige {esc(e.get("prestige"))}' + (f' · {", ".join(fmt)}' if fmt else '')
               + (f' · playoff{"" if len(e["sites"]) == 1 else " (at least one site)"}' if e.get('playoff') and not replay
                  else '') + '</p>')
    out.append('<p>' + ' · '.join(f'{course_link(w, c, lay)}, {esc(city)}' for c, lay, city in e['sites']) + '</p>')
    rows = e['rows']
    multi = len(e['sites']) > 1
    winners = [r for r in rows if r['pos'] == 1]
    if replay:
        out.append(f'<p>Field {len(rows):,} · {OH.rules_note(w, e["year"])} · <span class="muted">the winner and final '
                   f'places are not shown in the replay until its final round</span>{restart}</p>')
    else:
        out.append(f'<p>Winner: {", ".join(w.person_link(r["person"]) for r in winners) or "—"} · field {len(rows):,} · '
                   f'{OH.rules_note(w, e["year"])}{restart}</p>')
    base = f'/event/{quote(eid)}'
    out.append('<div class="tabs">' + ''.join(f'<a href="{base}?view={k}" class="{"on" if k == view else ""}">{esc(t)}</a>'
                                              for k, t in (('final', 'Final result'), ('rounds', 'Rounds & replay'),
                                                           ('stats', 'Statistics')))
               + '</div>')
    if view in ('rounds', 'stats'):
        out.append(OH.rounds_view(w, q, e) if view == 'rounds' else OG.edition_stats(w, e))
        return f'{eid.split(":")[0]} {e.get("name") or w.series_name(sid)}', ''.join(out)
    prizes = {}
    if any(r.get('prize') is not None for r in rows):
        prizes = {(r['person'], r['site']): r['prize'] for r in rows if r.get('prize') is not None}
    elif e.get('prizes'):
        prizes = {(int(g), k): x for k, site in enumerate(e['prizes']) for g, x in site.items()}
    full = OH.full_edition(w, e) or {'finish': [[(r['person'], r['pos'], r['total']) for r in rows if r['site'] == k]
                                                for k in range(len(e['sites']))], 'playoff': e.get('playoff'),
                                     'rounds': e.get('rounds')}
    for k in range(len(e['sites'])):                   # every playoff, at every site, with everyone in it
        lines = OH.playoff_lines(w, full, k, OH._layout_par(w, full['sites'][k]) if k < len(full.get('sites') or ()) else None)
        if lines:
            out.append((f'<h3>Site {k + 1}</h3>' if multi else '') + lines)
    tag = lambda r: (f' <span class="tag">{esc(OH.playoff_status(full, r["site"], r["person"]))}</span>'
                     if OH.playoff_status(full, r['site'], r['person']) else '')
    out.append(table((['Site'] if multi else []) + ['Pos', 'Golfer', 'Total', 'Prize', 'Coach', 'Caddie', 'How they got in'], [
        ([esc(r['site'] + 1)] if multi else []) +
        [esc(r['pos'] or 'MC') + tag(r), w.person_link(r['person']), esc(r['total'] or ''),
         money(prizes.get((r['person'], r['site']), 0.0)) if prizes else '<span class="muted">not recorded</span>',
         w.person_link(r['coach']), w.person_link(r['caddie']), OH.route_html(r['route'], w.calendar_version)] for r in rows],
        numeric=(1, 3, 4) if multi else (0, 2, 3)))
    if e.get('tier') == 0 or sid in ('TOUR_MASTERS', 'PREMIER_TOUR_CHAMPIONSHIP', 'USA_OPEN', 'BRITANNIA_OPEN'):
        out.append(OH.rights_section(w, e['year'], sid))
    out.append('<p class="muted">Coach and caddie are the team that week. MC: missed the cut (or out before the '
               'final stage). Prize: the money paid, as recorded (since rules 2026-10-30; amateurs are never paid); '
               'earlier editions did not record it. How they got in: the rule in words with the recorded code.</p>')
    return f'{eid.split(":")[0]} {e.get("name") or w.series_name(sid)}', ''.join(out)


def series(w, q, sid):
    sid = unquote(sid)
    info = w.series_info(sid)
    eds = sorted(w.editions_of(sid), key=lambda e: e['year'], reverse=True)
    head = (f'<p>{tour_link(w, info.get("tour"))} · tier {esc(info.get("tier"))} · {esc(info.get("kind"))} · '
            f'{esc(info.get("category"))}'
            + (f' · <a href="/qualification?major={quote(sid)}">qualification</a>' if info.get('kind') == 'major' else '')
            + f'{shortlist_button(w, "series", sid)}</p>') if info else ''
    if not eds:
        return w.series_name(sid), head + '<p class="muted">No editions played yet.</p>'
    venues = {}
    if w.a and w.a.index:
        for eid, c, lay in w.a.index.db.execute('SELECT e.event_id, si.course, si.layout FROM sites si JOIN editions e '
                                               'USING(eid) WHERE e.series = ?' + w.a.index.upto('e.year')
                                               + ' ORDER BY si.site', (sid,)):
            venues.setdefault(eid, []).append((c, lay))
    if w.live:
        for e in w.live.editions.values():
            if e['series'] == sid:
                venues[e['id']] = [(c, lay) for c, lay, _ in e['sites']]
    return w.series_name(sid), head + OH.series_summary(w, sid) + '<h2>Every edition</h2>' + table(
        ['Edition', 'Week', 'Winner', 'Field', 'Course', 'Tour then'], [
            [event_link(w, e['event']), esc(e['week']), w.person_link(e['winner']),
             esc(e['field']), ' · '.join(course_link(w, c, lay) for c, lay in venues.get(e['event'], [])) or '—',
             tour_link(w, e['tour'])]
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
           f'{esc(c.get("architect"))} · opened {esc(c.get("opened"))}{shortlist_button(w, "course", cid)}</p>']
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
    out.append(OH.course_use(w, cid))
    eds = sorted(w.course_editions(cid), key=lambda e: (e['year'], e['event']), reverse=True)
    chunk, pager = paged(eds, q, f'/course/{quote(cid)}')
    out.append('<h2>Editions hosted</h2>' + (table(['Edition', 'Layout', 'Winner'], [
        [event_link(w, e['event']), esc(e['layout']), w.person_link(e['winner'])]
        for e in chunk]) + pager
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
           f'<a href="/caddies?nation={quote(code)}">caddies</a> · <a href="/courses?country={quote(code)}">courses</a>'
           f'{shortlist_button(w, "nation", code)}</p>']
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
           f'<a href="/golfers?tour={quote(key)}">all members</a> · <a href="/stats?tour={quote(key)}">stats</a>'
           f'{shortlist_button(w, "tour", key)}</p>']
    ys = list(reversed(w.a.years))[:12] if w.a else []
    if ys:
        out.append('<p>Where are they now: ' + ' '.join(f'<a href="/cohort?tour={quote(key)}&amp;year={y}">{y}</a>'
                                                       for y in ys) + ' (its golfers that season)</p>')
    if w.live:
        mem = sorted((w.live.wr.get(pid, 10 ** 9), pid) for pid, p in w.live.people.items()
                     if p.get('tour') == key and p.get('lifestyle') != 'retired')
        out.append(f'<h2>Members now ({len(mem)})</h2>' + table(['World', 'Golfer', 'Status'], [
            [esc(r if r < 10 ** 9 else '—'), w.person_link(pid), esc(w.live.people[pid].get('status'))] for r, pid in mem[:50]],
            numeric=(0,)) + (f'<p><a href="/golfers?tour={quote(key)}">All {len(mem)} members</a></p>' if len(mem) > 50 else ''))
        eds = [e for e in w.live.schedule if e['tour'] == key]
        out.append(f'<h2>{w.live.cursor["year"]} events</h2>' + table(['Week', 'Event', 'Winner'], [
            [esc(e['week']), event_link(w, e['id']) if e['status'] == 'played' else esc(e['name']),
             w.person_link(_winner(w.live.editions[e['id']])) if e['status'] == 'played'
             else esc(e['status'])] for e in eds],
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
    rows = [[f'<a href="/season/{y}">{y}</a>', ', '.join(f'{event_link(w, eid)}: {w.person_link(g)}'
                                                         for eid, g in majors[y])]
            for y in reversed(w.a.years)]
    chunk, pager = paged(rows, q, '/seasons', size=25)
    return 'Seasons', ''.join(out) + table(['Season', 'Major champions'], chunk) + pager


def season(w, q, y):
    y = int(y)
    if not w.a or y not in w.a.years:
        return str(y), '<p class="muted">This season is not archived (yet).</p>'
    nav = ' · '.join(x for x in (f'<a href="/season/{y - 1}">← {y - 1}</a>' if y - 1 in w.a.years else '',
                                 f'<a href="/season/{y + 1}">{y + 1} →</a>' if y + 1 in w.a.years else '') if x)
    nav += (' · ' if nav else '') + f'<a href="/cohort?turned_pro={y}">where are the {y} rookies now?</a>'
    return f'{y} season', f'<p>{nav}</p>' + OH.recap(w, y)


STAT_COLUMNS = (('starts', 'Starts', None), ('wins', 'Wins', 'win'), ('runner_ups', 'Runner-up', 'runner-up'),
                ('top2', 'Top 2', 'top2'), ('top5', 'Top 5', 'top5'), ('top10', 'Top 10', 'top10'),
                ('cuts_made', 'Cuts made', 'made-cut'), ('prize', 'Prize money', None))
STATS_NOTE = ('Starts exclude qualifying stages; the simulation has no withdrawals once an event has begun (a golfer '
              'who cannot play withdraws beforehand and is replaced), so a start ends in a position or a missed cut. '
              'Top 2/5/10 include wins: never add them up. Runner-up: a recorded second place, ties included. Match play '
              'records places by round reached (3 = semi-finalist, 5 = quarter-finalist). Cuts made: of stroke-play '
              'events with a cut. Each edition counts once, under the tour it belonged to when played (majors under '
              'Majors), so “all tours” adds every start once. Prize money is gross tournament prize money: all tours, '
              'the money actually paid; one tour, each event’s payouts recomputed and shown only where they match the '
              'money paid (“unknown” otherwise). The current season counts as far as it has been played.')


def tour_scope_name(w, tour):
    if not tour:
        return 'all tours'
    if tour == SC.MAJORS_PREMIER:
        return SC.LABEL + ' (every major and Premier event, by its classification when played)'
    return w.tours().get(tour, {}).get('name', tour)


def scope_buttons(path, q, current, param='tour'):
    """The shared one-click scope control: Majors + Premier, or All tours (the reset). It replaces only the tour
    choice; season, view, sort, minimum and every other filter are kept."""
    keep = {k: v[0] for k, v in q.items() if k not in (param, 'page') and v and v[0]}
    def b(value, label):
        on = (current or '') == value
        href = f'{path}?{urlencode({**keep, **({param: value} if value else {})})}'
        return f'<a href="{href}" class="{"on" if on else ""}" aria-pressed="{"true" if on else "false"}">{esc(label)}</a>'
    return ('<div class="tabs scope" title="Which events count">' + b(SC.MAJORS_PREMIER, SC.LABEL) + b('', 'All tours')
            + '</div>')


def stats_page(w, q, view='stats'):
    """Basketball GM-style statistics: a season or all-time, all tours or one, sorted by any column."""
    import observer_stats as ST
    path = '/money' if view == 'money' else '/stats'
    title = 'Prize money' if view == 'money' else 'Stats'
    db, building = w.statistics()
    live = w.live_statistics()
    cur = w.live.cursor['year'] if w.live else None
    archived = list(w.a.years) if w.a else []
    ysel = one(q, 'year', 'all') or 'all'
    tour = one(q, 'tour', '') or ''
    sort = one(q, 'sort', 'prize' if view == 'money' else 'wins')
    if building and ysel != str(cur):
        return title, (f'<p>Working out the statistics from the history: {building["done"]} of {building["total"]} '
                       f'seasons{" (" + esc(building["error"]) + ")" if building.get("error") else ""}. This page '
                       'refreshes by itself.</p><meta http-equiv="refresh" content="3">')
    played_live = live is not None and any(a['starts'] or a['qualifiers'] for a in live[0].values())
    if ysel == 'all':
        years, with_live = archived, played_live
    elif cur is not None and ysel == str(cur):
        years, with_live = [], True
    else:
        years, with_live = [int(ysel)], False
    show = one(q, 'show', '') if view == 'stats' else ''
    data = ST.query(db, years, tour or None, live if with_live else None,    # only the columns this page shows
                    cols=ST.GOLF if show == 'golf' else ST.COLUMNS)
    tours = sorted(set(ST.tours_in(db)) | ({t for (_, t) in live[0]} if live else set()) - {''},
                   key=lambda t: (w.tours().get(t, {}).get('tier', 9), w.tours().get(t, {}).get('name', t)))
    yopts = [('all', 'all-time')] + ([(str(cur), f'{cur} (so far)')] if cur is not None else []) + \
        [(str(y), str(y)) for y in reversed(archived)]
    f = filters(path, q, [('year', 'Season', yopts),
                          ('tour', 'Tour', [('', 'all tours'), (SC.MAJORS_PREMIER, SC.LABEL)]
                           + [(t, w.tours().get(t, {}).get('name', t.replace('_', ' ').title())) for t in tours])])
    f = scope_buttons(path, q, tour) + f
    f = f.replace('<button>Apply</button>', f'<input type="hidden" name="sort" value="{esc(sort)}">'
                  + ('<input type="hidden" name="show" value="golf">' if show == 'golf' else '')
                  + (f'<input type="hidden" name="min" value="{esc(one(q, "min"))}">' if show == 'golf' and one(q, 'min')
                     else '') + '<button>Apply</button>')
    if view == 'stats':
        base = {k: v[0] for k, v in q.items() if k in ('year', 'tour') and v and v[0]}
        f = ('<div class="tabs">' + ''.join(
            f'<a href="/stats?{urlencode({**base, **({"show": k} if k else {})})}" class="{"on" if k == show else ""}">{t}</a>'
            for k, t in (('', 'Results & prize money'), ('golf', 'Golf statistics'))) + '</div>') + f
    if show == 'golf':
        scope_ = ('all-time' if ysel == 'all' else f'{ysel}' + (' so far' if ysel == str(cur) else ''))
        scope_ += ' · ' + tour_scope_name(w, tour)
        return title, f + OG.golf_table(w, q, data, path, {k: v[0] for k, v in q.items() if v and v[0]}, esc(scope_),
                                        ysel != 'all')
    rows = [(pid, r) for pid, r in data.items() if r['starts'] or r['prize']]
    if view == 'money':
        rows = [(pid, r) for pid, r in rows if r['prize'] or not r['prize_known']]
    ov, ov_label, ov_note = (overall_column(w, db, ysel, cur, [pid for pid, _ in rows]) if view == 'stats'
                             else ({}, '', ''))
    desc = (one(q, 'dir', '') or ('asc' if sort == 'name' else 'desc')) == 'desc'
    value = {'name': lambda x: w.name(x[0]) or '',
             'prize': lambda x: x[1]['prize'] if x[1]['prize_known'] else None,
             'overall': lambda x: ov[x[0]][0] if x[0] in ov else None}.get(sort, lambda x: x[1].get(sort) or 0)
    # the whole result set, before paging: ties by prize money then id (in either direction); missing values last
    rows.sort(key=lambda x: (-(x[1]['prize'] or 0), x[0]))
    known = [x for x in rows if value(x) is not None]
    known.sort(key=value, reverse=desc)                   # (stable: the tie order above is kept)
    rows = known + [x for x in rows if value(x) is None]
    chunk, pager = paged(rows, q, path)
    start = (max(1, int(one(q, 'page', '1') or 1)) - 1) * PAGE_SIZE
    keep = {k: v[0] for k, v in q.items() if k not in ('sort', 'page', 'dir') and v and v[0]}
    cols = STAT_COLUMNS if view == 'stats' else (('prize', 'Prize money', None), ('starts', 'Starts', None),
                                                 ('wins', 'Wins', 'win'))

    def sort_link(k, label):
        """A column heading: sorts by it (descending first; name ascending); the active one shows its direction
        and turns it around."""
        first = 'asc' if k == 'name' else 'desc'
        if k == sort:
            nxt = 'asc' if desc else 'desc'
            mark = ' ▼' if desc else ' ▲'
        else:
            nxt, mark = first, ''
        args = {**keep, 'sort': k, **({'dir': nxt} if nxt != first else {})}
        return (f'<a href="{path}?{urlencode(args)}"' + (f' aria-sort="{"descending" if desc else "ascending"}"'
                                                         if k == sort else '') + f'>{esc(label)}{mark}</a>')
    head = ('<tr><th class="n">#</th><th>' + sort_link('name', 'Golfer') + '</th><th>Nation</th>'
            + (f'<th class="n" title="{esc(ov_note)}">' + sort_link('overall', ov_label) + '</th>' if ov_label else '')
            + ''.join(f'<th class="n">{sort_link(k, label)}</th>' for k, label, _ in cols) + '</tr>')
    yfilter = None if ysel == 'all' else ysel
    body = []
    for i, (pid, r) in enumerate(chunk, start + 1):
        cells = []
        for k, label, outcome in cols:
            if k == 'prize':
                cells.append(money(r['prize'], r['prize_known']))
            elif k == 'cuts_made':
                cells.append(results_link(pid, f'{r["cuts_made"]}/{r["cut_events"]}', year=yfilter, tour=tour,
                                          outcome='made-cut') if r['cut_events'] else '—')
            else:
                cells.append(results_link(pid, str(r[k]), year=yfilter, tour=tour, outcome=outcome))
        if ov_label:
            v = ov.get(pid)
            cells.insert(0, '<span class="muted">—</span>' if v is None else
                         f'{v[0]:.1f}' + (f' <span class="muted" title="last recorded ({esc(v[2])})">†</span>'
                                          if v[1] == 'last' else ''))
        body.append(f'<tr><td class="n">{i}</td><td>{w.person_link(pid)}</td>'
                    f'<td>{nation_link((w.person(pid) or {}).get("country"))}</td>'
                    + ''.join(f'<td class="n">{c}</td>' for c in cells) + '</tr>')
    scope = ('all-time' if ysel == 'all' else f'{ysel}' + (' so far' if ysel == str(cur) else ''))
    scope += ' · ' + tour_scope_name(w, tour)
    other = ('<a href="/money">Prize money leaderboard</a>' if view == 'stats' else '<a href="/stats">All statistics</a>')
    return title, (f + f'<p>{esc(scope)} · {len(rows):,} golfers · {other}</p>'
                   + f'<div class="scroll"><table>{head}{"".join(body)}</table></div>' + pager
                   + f'<p class="muted">{STATS_NOTE}' + (f' {esc(ov_note)}' if ov_note else '') + '</p>')


def overall_column(w, db, ysel, cur, pids):
    """({pid: (Overall, 'current' | 'last' | 'start', when)}, heading, note) for the Stats page. All-time and the
    current season: the current Overall of everyone competing, and the last recorded Overall (marked) of anyone
    retired or not in the running world. A past season: the Overall recorded at that season's start, missing where
    none was recorded (never today's rating). The base rating (no form or staff effect), the same whatever the
    tour scope: it is not an event count."""
    import observer_stats as ST
    out = {}
    if db is None:
        return out, 'Overall', 'Overall: recorded ratings are being worked out from the history.'
    if ysel == 'all' or (cur is not None and ysel == str(cur)):
        people = w.live.people if w.live else {}
        last = ST.overall_last(db)
        for pid in pids:
            r = (people.get(pid) or {}).get('ratings')
            if r:
                out[pid] = (r[0], 'current', 'now')
            elif pid in last:
                v, y = last[pid]
                out[pid] = (v, 'last', f'recorded with the {y} season')
        when = f' ({w.live.cursor["year"]}, week {w.live.cursor["week"]})' if w.live else ''
        return out, 'Overall', (f'Overall: the current base rating{when} (no form or staff effect); † last recorded '
                                'Overall for golfers retired or not competing (their rating when it was last saved). '
                                'A rating, not an event count: the same whatever the tour.')
    y = int(ysel)
    start = ST.overall_start(db, y)
    for pid in pids:
        if pid in start:
            out[pid] = (start[pid], 'start', f'start of {y}')
    return out, f'Overall (start of {y})', (f'Overall (start of {y}): the base rating recorded at the start of the {y} '
                                             'season (after the previous season-end aging), not its end; — where none '
                                             'was recorded (the world’s first season, or seasons archived before '
                                             'ratings were kept). A rating, not an event count: the same whatever the tour.')


def money_page(w, q):
    return stats_page(w, q, 'money')


FEATURED = ('youngest-major-champions', 'oldest-major-champions', 'youngest-premier-debuts', 'oldest-premier-debuts',
            'not-won-yet', 'retired-without-a-win')
SCOPED = {'most-wins', 'most-starts', 'not-won-yet', 'retired-without-a-win', 'starts-before-first-win',
          'youngest-winners', 'oldest-winners', 'longest-wait-between-wins', 'runner-ups-without-a-win'}


def records(w, q):
    first = '<li><a href="/grand-slam">Career Grand Slam</a> — winners of all four majors</li>' + ''.join(f'<li><a href="/records/{k}">{esc(BOARDS[k][0])}</a>'
                    + (' — <span class="muted">by tour: choose a tour on the list</span>' if k in SCOPED else '') + '</li>'
                    for k in FEATURED)
    rest = ''.join(f'<li><a href="/records/{k}">{esc(t)}</a></li>' for k, (t, _, _) in BOARDS.items() if k not in FEATURED)
    through = (f'<p class="muted">From the archived seasons ({span(w.a.years, False)}); the current season counts '
               'once it ends. Ages are the season\'s year minus the birth year (birth dates are not recorded), so an age '
               'can be a year out. Careers that began before the archive are marked partial and left out of debut lists.</p>'
               if w.a else no_history())
    return 'Record Book', (through + '<h2>Start here</h2><ul>' + first + '</ul><h2>Golf statistics and '
                                     'margins</h2><ul>' + OG.records_list() + '</ul><h2>All lists</h2><ul>' + rest +
                                     '</ul><h2>Definitions</h2><dl>' + ''.join(
                                         f'<dt>{esc(k)}</dt><dd class="muted">{esc(v)}</dd>' for k, v in DEFINITIONS.items())
                                     + '</dl>')


def record(w, q, name):
    if name not in BOARDS:
        return 'Records', '<p class="muted">No such list.</p>'
    if not w.stats:
        return BOARDS[name][0], no_history()
    scope = one(q, 'scope', '') or ''
    # the shared Majors + Premier scope is the records' tiers 0-1 ("premier") scope: every major and Premier event
    hs_scope = 'premier' if scope == SC.MAJORS_PREMIER else scope
    over = {'scope': hs_scope} if hs_scope and name in SCOPED else {}
    title, rows = board(w.stats, name, n=100, **over)
    f = ''
    if name in SCOPED:
        tours = sorted(((k, t.get('name', k)) for k, t in w.tours().items()), key=lambda x: x[1])
        names = {'all': 'all events', 'professional': 'professional events', 'premier': SC.LABEL, 'major': 'majors'}
        f = scope_buttons(f'/records/{name}', q, SC.MAJORS_PREMIER if hs_scope == 'premier' else scope, 'scope') + \
            filters(f'/records/{name}', q, [('scope', 'Scope', [('', 'as defined')]
                                             + [(SC.MAJORS_PREMIER if s == 'premier' else s, names.get(s, s)) for s in SCOPES]
                                             + [(k, f'tour: {t}') for k, t in tours])])
        if scope:
            title += f' — {SC.LABEL if hs_scope == "premier" else w.tours().get(scope, {}).get("name", scope)}'
    flag = lambda r: '<span class=tag>partial</span>' if r['partial'] else ''
    context = OH.record_context(w, name, rows)
    value = (lambda r: money(r['value'])) if name == 'most-prize' else (lambda r: esc(r['value']))
    def evidence(r):
        ev = r['evidence']
        more = f' <span class="muted">+{len(ev) - 3} more</span>' if len(ev) > 3 else ''
        return ', '.join(event_link(w, e) for e in ev[:3]) + more
    unit = OH.UNITS.get(name)
    return title, (f + f'<p class="muted">{span(w.a.years)}'
                   + (f'. Counted in {esc(unit)}' if unit else '')
                   + '. When: the date, or the first and latest dates, of the results behind the row. Now: whether the '
                   'person is still pursuing it, as of the date in the header — currently extending (a streak still '
                   'alive, world No. 1 now, a partnership still going), competing (can add to a count), fixed (a single '
                   'result), or closed (retired). Partial = began before the archive; earlier results are not '
                   'included.</p>' + table(
                       ['#', 'Golfer', 'Value', '', 'When', 'Now', 'Evidence'],
                       [[str(i), w.person_link(r['person']) + (f' · with {w.person_link(r["staff"])}' if r.get('staff') else ''),
                         value(r), flag(r), when_, now, evidence(r)]
                        for i, (r, (when_, now)) in enumerate(zip(rows, context), 1)],
                       numeric=(0, 2)) + ('' if rows else '<p class="muted">Nobody qualifies yet.</p>'))


def moments(w, q):
    if not (w.a and w.a.index):
        return 'Moments', no_history()
    kind = one(q, 'kind', '') or ''
    ms = list(reversed(w.a.index.moments(kind=kind or None)))
    kinds = [k for (k,) in w.a.index.db.execute('SELECT DISTINCT kind FROM moments ORDER BY kind')]
    f = filters('/moments', q, [('kind', 'Kind', [('', 'any')] + [(k, k) for k in kinds])])
    chunk, pager = paged(ms, q, '/moments')
    return 'Moments', f + table(['Season', 'What', 'Golfer', 'Event', 'Venue'], [
        [esc(m['year']), esc(m['kind']), w.person_link(m['person']), event_link(w, m['event']),
         venue_link(w, m.get('layout'))] for m in chunk], numeric=(0,)) + pager + (
        '<p class="muted">Venue: the course and layout where it happened, as recorded with the moment.</p>')


ROUTES = [('/golfer/', golfer), ('/event/', event), ('/series/', series), ('/course/', course), ('/records/', record),
          ('/golf-records/', OG.golf_record),
          ('/nation/', nation), ('/tour/', tour), ('/season/', season)]
PAGES = {'/': overview, '/rankings': rankings, '/search': search, '/golfers': golfers, '/coaches': coaches,
         '/caddies': caddies, '/records': records, '/moments': moments, '/tournaments': tournaments,
         '/calendar': calendar, '/courses': courses_page, '/nations': nations, '/tours': tours_page, '/seasons': seasons,
         '/stats': stats_page, '/money': money_page, '/shortlist': shortlist_page, '/my-world': shortlist_page,
         '/rules': OH.rules_page,
         '/grand-slam': OH.grand_slam_page, '/views': V.views_page, '/cohort': OC.cohort_page,
         '/compare': OCMP.compare_page, '/goat': GOAT.goat_page, '/qualification': OQ.qualification_page,
         '/standings': OQ.standings_page}


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
