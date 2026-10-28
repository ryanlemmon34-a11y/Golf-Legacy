"""A throwaway observer prototype: browse a world's history and advance it, in a web browser.

    python tools/world.py worlds/demo create --seed 2027      # once
    python tools/observer.py worlds/demo                      # then open http://localhost:8765

    python tools/observer.py path/to/archive_2027             # or browse any history archive (read-only)

Standard library only (http.server, the session, the archive and its index). It exists to try the first
usable slice of the V1 UI baseline (docs/UI_REQUIREMENTS_V1.md) — Overview, a golfer profile, a tournament
and its editions, a course, records lists with evidence, search, Advance Week — before the owner chooses
the real framework and packaging. It is not that choice. Pages are server-rendered HTML with plain links,
so every person, edition, tournament and course links to its page.
"""
from __future__ import annotations

import argparse
import html
import sys
import threading
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from golfsim.archive import Archive                                   # noqa: E402
from golfsim.history_stats import BOARDS, DEFINITIONS, HistoryStats, board   # noqa: E402

CSS = """
:root { --bg:#fbfaf7; --fg:#1d2420; --muted:#5c6660; --line:#d9dcd6; --accent:#1f6b45; --panel:#ffffff; }
@media (prefers-color-scheme: dark) { :root { --bg:#141816; --fg:#e8ece9; --muted:#9aa59f; --line:#2c3430;
  --accent:#6fcf9d; --panel:#1b201d; } }
* { box-sizing: border-box; }
body { margin:0; background:var(--bg); color:var(--fg); font:15px/1.5 system-ui, -apple-system, Segoe UI, sans-serif; }
header { display:flex; gap:16px; align-items:center; padding:10px 16px; border-bottom:1px solid var(--line);
  background:var(--panel); position:sticky; top:0; flex-wrap:wrap; }
header .date { font-weight:600; }
header form { margin:0; display:flex; gap:6px; }
nav { width:200px; padding:12px 16px; border-right:1px solid var(--line); min-height:100vh; }
nav h4 { margin:14px 0 4px; font-size:12px; text-transform:uppercase; letter-spacing:.05em; color:var(--muted); }
nav a { display:block; padding:2px 0; }
.layout { display:flex; }
main { padding:16px 24px; flex:1; min-width:0; max-width:1100px; }
a { color:var(--accent); text-decoration:none; } a:hover { text-decoration:underline; }
a:focus-visible, button:focus-visible, input:focus-visible { outline:2px solid var(--accent); outline-offset:2px; }
table { border-collapse:collapse; width:100%; margin:8px 0 18px; }
th, td { text-align:left; padding:4px 8px; border-bottom:1px solid var(--line); vertical-align:top; }
th { font-size:12px; text-transform:uppercase; letter-spacing:.04em; color:var(--muted); }
td.n, th.n { text-align:right; font-variant-numeric:tabular-nums; }
.muted { color:var(--muted); } .tag { font-size:12px; border:1px solid var(--line); border-radius:4px; padding:0 4px; }
button { font:inherit; padding:4px 10px; border:1px solid var(--line); background:var(--panel); color:var(--fg);
  border-radius:4px; cursor:pointer; }
input { font:inherit; padding:4px 8px; border:1px solid var(--line); border-radius:4px; background:var(--panel); color:var(--fg); }
@media (max-width: 720px) { nav { display:none; } main { padding:12px 16px; } }
"""


def esc(x):
    return html.escape('' if x is None else str(x))


class World:
    """What the pages read: a session (live, can advance) or an archive alone (read-only)."""

    def __init__(self, path):
        p = Path(path)
        self.session = None
        if (p / 'CURRENT').exists():
            from golfsim.session import Session
            self.session = Session.open(p)
            self.archive_dir = p / 'archive'
        else:
            self.archive_dir = p
        self.lock = threading.Lock()
        self.reload()

    def submit(self, form):
        """An Advance form: {'weeks': '1' | '4' | 'season', 'year', 'week', 'phase', 'op'} (lists, as
        parse_qs gives them). The session refuses a form drawn at another cursor (StaleCursor: the world
        has moved on, nothing to do) and recognises a resubmitted one by its key."""
        from golfsim.session import StaleCursor
        one = lambda k, d=None: (form.get(k) or [d])[0]
        v = one('weeks', '1')
        expected = ({'year': int(one('year')), 'week': int(one('week')), 'phase': one('phase')}
                    if one('year') is not None else None)
        with self.lock:
            c = self.session.cursor
            weeks = 53 - c['week'] if v == 'season' else int(v)
            try:
                self.session.advance(weeks, expected=expected, op_key=one('op'))
            except StaleCursor:
                pass
            self.reload()

    def reload(self):
        """Read the history again only if what is published has changed (a season was archived): the
        archive's season list and published generation. Records are then brought up to date with the
        new seasons only (HistoryStats.extend); they are built at all only when first asked for."""
        import json
        wj = self.archive_dir / 'world.json'
        seasons = json.loads(wj.read_text()).get('years') if wj.exists() else None
        pub = self.archive_dir / 'PUBLISHED'
        stamp = (tuple(seasons or ()), pub.read_text() if pub.exists() else None)
        if stamp == getattr(self, '_stamp', None):
            return
        self._stamp = stamp
        self.a = Archive(self.archive_dir) if seasons else None     # nothing archived before the first season ends
        if getattr(self, '_stats', None) is not None and self.a:
            self._stats.extend(self.a)
        elif not self.a:
            self._stats = None

    @property
    def stats(self):
        if getattr(self, '_stats', None) is None and self.a:
            self._stats = HistoryStats(self.a)
        return getattr(self, '_stats', None)

    def name(self, pid):
        if self.a and pid in self.a.people:
            return self.a.name(pid)
        if self.session and pid in self.session.season.g:
            g = self.session.season.g[pid]
            return f'{g.name} ({g.country})'
        return f'#{pid}'

    def person_link(self, pid):
        return f'<a href="/golfer/{pid}">{esc(self.name(pid))}</a>' if pid else '<span class="muted">—</span>'

    def series_name(self, sid):
        if self.session:
            s = self.session.season.cal.by_id.get(sid)
            if s:
                return s.name
        if self.a:
            return self.a.world['series'].get(sid, {}).get('name', sid)
        return sid


def event_link(w, eid):
    sid = eid.split(':', 1)[1]
    return f'<a href="/event/{quote(eid)}">{esc(eid.split(":")[0])} {esc(w.series_name(sid))}</a>'


def page(w, title, body):
    if w.session:
        c = w.session.cursor
        date = f'{c["year"]}, week {c["week"]}' + (' (1 January next)' if c['phase'] == 'start' else '')
        # the form carries the cursor it was drawn at and a one-time key: a resubmitted or refreshed form
        # (or one from a page drawn before another advance) advances nothing
        hidden = ''.join(f'<input type="hidden" name="{k}" value="{esc(v)}">' for k, v in
                         (('year', c['year']), ('week', c['week']), ('phase', c['phase']), ('op', uuid.uuid4().hex)))
        controls = (f'<form method="post" action="/advance">{hidden}<button name="weeks" value="1">Advance week</button>'
                    '<button name="weeks" value="4">4 weeks</button><button name="weeks" value="season">'
                    'To end of season</button></form>')
    else:
        date, controls = 'read-only archive', ''
    nav = ('<nav aria-label="Sections"><h4>World</h4><a href="/">Overview</a><a href="/rankings">Rankings</a>'
           '<h4>Explore</h4><a href="/search">Golfers</a><a href="/tournaments">Tournaments</a>'
           '<h4>History</h4><a href="/records">Records &amp; frivolities</a><a href="/moments">Moments</a></nav>')
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" '
            f'content="width=device-width, initial-scale=1"><title>{esc(title)} — Golf Legacy</title>'
            f'<style>{CSS}</style></head><body><header><strong>Golf Legacy</strong><span class="date">{esc(date)}</span>'
            f'<form action="/search"><input name="q" placeholder="Search golfers" aria-label="Search golfers"></form>'
            f'{controls}</header><div class="layout">{nav}<main><h1>{esc(title)}</h1>{body}</main></div></body></html>')


# ---- pages --------------------------------------------------------------------------------------------------
def overview(w, q):
    out = []
    if w.session:
        s = w.session.season
        year = w.session.cursor['year']
        recent = sorted((r for r in s.results.values() if r.year == year and r.winner()), key=lambda r: -r.week)[:20]
        top = sorted(s.wr_pos.items(), key=lambda x: x[1])[:10]
        out.append('<h2>World ranking</h2><table><tr><th class="n">#</th><th>Golfer</th></tr>' +
                   ''.join(f'<tr><td class="n">{p}</td><td>{w.person_link(g)}</td></tr>' for g, p in top) + '</table>')
        out.append(f'<h2>Latest winners in {year}</h2><table><tr><th>Week</th><th>Event</th><th>Winner</th></tr>' +
                   ''.join(f'<tr><td>{r.week}</td><td>{event_link(w, r.event_id)}</td><td>{w.person_link(r.winner())}</td></tr>'
                           for r in recent) + '</table>' if recent else
                   f'<p class="muted">No events completed yet in {year}.</p>')
    if w.a:
        y = w.a.years[-1]
        facts = w.a.recap(y)
        out.append(f'<h2>{y} season recap</h2><ul>' + ''.join(
            f'<li>{esc(f["text"])}' + (f' — {w.person_link(f["golfer"])}' if f.get('golfer') else '') +
            (f' — {event_link(w, f["event"])}' if f.get('event') else '') + '</li>' for f in facts) + '</ul>')
        out.append('<p>Archived seasons: ' + ', '.join(str(x) for x in w.a.years) + '</p>')
    else:
        out.append('<p class="muted">No season has finished yet: history pages fill in at the end of the first season.</p>')
    return 'Overview', ''.join(out)


def rankings(w, q):
    if not w.session:
        y = w.a.years[-1]
        top = w.a.ranking(y, 52)
        rows = [(i + 1, g) for i, g in enumerate(top)]
    else:
        rows = sorted(((p, g) for g, p in w.session.season.wr_pos.items()), key=lambda x: x[0])[:100]
    return 'World ranking', '<table><tr><th class="n">#</th><th>Golfer</th></tr>' + ''.join(
        f'<tr><td class="n">{p}</td><td>{w.person_link(g)}</td></tr>' for p, g in rows) + '</table>'


def search(w, q):
    term = (q.get('q') or [''])[0].strip().lower()
    if not term:
        return 'Golfers', '<p>Search by name in the bar above.</p>'
    people = w.a.people.items() if w.a else []
    hits = [(pid, p) for pid, p in people if term in p['name'].lower()][:100]
    if w.session:
        known = {pid for pid, _ in hits}
        hits += [(g.id, {'name': g.name, 'country': g.country, 'born': g.born}) for g in w.session.season.world.golfers
                 if term in g.name.lower() and g.id not in known][:100 - len(hits)]
    return f'Golfers matching “{term}”', '<table><tr><th>Name</th><th>Country</th><th class="n">Born</th></tr>' + ''.join(
        f'<tr><td><a href="/golfer/{pid}">{esc(p["name"])}</a></td><td>{esc(p.get("country"))}</td>'
        f'<td class="n">{esc(p.get("born"))}</td></tr>' for pid, p in hits) + '</table>'


def golfer(w, q, pid):
    pid = int(pid)
    out = []
    p = w.a.people.get(pid) if w.a else None
    g = w.session.season.g.get(pid) if w.session else None
    country = (p or {}).get('country') or (g.country if g else '')
    born = (p or {}).get('born') or (g.born if g else '')
    roles = w.a.roles(pid) if p else ['golfer']
    out.append(f'<p>{esc(country)} · born {esc(born)} · roles: {esc(", ".join(roles))}'
               + (' · <span class="tag">career began before the archive</span>' if p and p.get('initial') else '')
               + '</p>')
    if g:
        out.append(f'<p>Now: {esc(g.status)}, {esc(g.lifestyle)}, {esc(g.tour or "no tour")}'
                   + (f', world No. {w.session.season.wr_pos[pid]}' if pid in w.session.season.wr_pos else '') + '</p>')
    if w.a and w.a.index:
        seasons = w.a.index.seasons(pid)
        if seasons:
            out.append('<h2>Career</h2><table><tr><th>Season</th><th>Tour</th><th>Status</th><th class="n">Starts</th>'
                       '<th class="n">Wins</th><th class="n">Prize</th><th class="n">World</th></tr>' + ''.join(
                           f'<tr><td>{r["year"]}</td><td>{esc(r["tour"])}</td><td>{esc(r["status"])} / {esc(r["lifestyle"])}</td>'
                           f'<td class="n">{r["events"]}</td><td class="n">{r["wins"]}</td><td class="n">${(r["prize"] or 0):,}</td>'
                           f'<td class="n">{r["wr_end"] or "—"}</td></tr>' for r in seasons) + '</table>')
        stints = w.a.golfer_staff(pid)
        if stints:
            out.append('<h2>Team history</h2><table><tr><th>Role</th><th>Who</th><th>From</th><th>To</th><th>Why it ended</th></tr>' +
                       ''.join(f'<tr><td>{esc(s.kind)}</td><td>{w.person_link(s.staff) if s.staff else esc(s.arrangement)}</td>'
                               f'<td>{s.start[0]} wk {s.start[1]}</td><td>{f"{s.end[0]} wk {s.end[1]}" if s.end else "now"}</td>'
                               f'<td>{esc(s.reason_end or "")}</td></tr>' for s in stints) + '</table>')
        for role in ('coach', 'caddie'):
            if p and role in p:
                rows = w.a.staff_clients(pid, role)
                out.append(f'<h2>As a {role}</h2><table><tr><th>Player</th><th>From</th><th>To</th><th class="n">Starts together</th>'
                           '<th class="n">Wins</th></tr>' + ''.join(
                               f'<tr><td>{w.person_link(c["stint"].golfer)}</td><td>{c["stint"].start[0]}</td>'
                               f'<td>{c["stint"].end[0] if c["stint"].end else "now"}</td><td class="n">{c["starts"]}</td>'
                               f'<td class="n">{len(c["wins"])}</td></tr>' for c in rows) + '</table>'
                           '<p class="muted">Results during a partnership are association, not proof of cause.</p>')
        res = w.a.index.results(pid)
        page_no = int((q.get('page') or ['1'])[0])
        chunk = list(reversed(res))[(page_no - 1) * 50:page_no * 50]
        if res:
            out.append(f'<h2>Results ({len(res)} archived starts)</h2><table><tr><th>Event</th><th class="n">Pos</th>'
                       '<th>Coach</th><th>Caddie</th><th>How they got in</th></tr>' + ''.join(
                           f'<tr><td>{event_link(w, r["event"])}</td><td class="n">{r["pos"] or "MC"}</td>'
                           f'<td>{w.person_link(r["coach"])}</td><td>{w.person_link(r["caddie"])}</td>'
                           f'<td class="muted">{esc(r["route"])}</td></tr>' for r in chunk) + '</table>')
            if len(res) > page_no * 50:
                out.append(f'<p><a href="/golfer/{pid}?page={page_no + 1}">Older results</a></p>')
        moments = w.a.index.moments(person=pid)
        if moments:
            out.append('<h2>Moments</h2><ul>' + ''.join(f'<li>{esc(m["kind"])} — {event_link(w, m["event"])}</li>'
                                                     for m in moments) + '</ul>')
    return w.name(pid), ''.join(out)


def event(w, q, eid):
    eid = unquote(eid)
    sid = eid.split(':', 1)[1]
    out = [f'<p><a href="/series/{quote(sid)}">All editions of the {esc(w.series_name(sid))}</a></p>']
    rows = w.a.index.leaderboard(eid) if w.a and w.a.index else []
    if not rows and w.session and eid in w.session.season.results:
        r = w.session.season.results[eid]
        team = r.team
        rows = [{'person': g, 'site': k, 'pos': pos, 'total': tot, 'coach': team.get(g, (0, 0))[0],
                 'caddie': team.get(g, (0, 0))[1], 'route': None} for k, site in enumerate(r.finish) for g, pos, tot in site]
    if w.a and w.a.index:
        sites = w.a.index.db.execute('SELECT s.site, s.course, s.layout, s.city FROM sites s JOIN editions e USING(eid) '
                                     'WHERE e.event_id = ?', (eid,)).fetchall()
        out.append('<p>' + ' · '.join(f'<a href="/course/{quote(c)}">{esc(w.a.world["courses"].get(c, {}).get("name", c))}</a> '
                                      f'({esc(lay)}, {esc(city)})' for _, c, lay, city in sites) + '</p>')
    out.append('<table><tr><th class="n">Pos</th><th>Golfer</th><th class="n">Total</th><th>Coach</th><th>Caddie</th>'
               '<th>How they got in</th></tr>' + ''.join(
                   f'<tr><td class="n">{r["pos"] or "MC"}</td><td>{w.person_link(r["person"])}</td><td class="n">{r["total"] or ""}</td>'
                   f'<td>{w.person_link(r["coach"])}</td><td>{w.person_link(r["caddie"])}</td><td class="muted">{esc(r["route"])}</td></tr>'
                   for r in rows) + '</table>')
    return f'{eid.split(":")[0]} {w.series_name(sid)}', ''.join(out)


def series(w, q, sid):
    sid = unquote(sid)
    eds = w.a.index.editions(sid) if w.a and w.a.index else []
    return w.series_name(sid), ('<table><tr><th>Edition</th><th>Winner</th><th class="n">Field</th><th>Tour then</th></tr>' + ''.join(
        f'<tr><td>{event_link(w, e["event"])}</td><td>{w.person_link(e["winner"])}</td><td class="n">{e["field"]}</td>'
        f'<td class="muted">{esc(e["tour"])}</td></tr>' for e in eds) + '</table>') if eds else \
        '<p class="muted">No archived editions yet.</p>'


def tournaments(w, q):
    if not (w.a and w.a.index):
        return 'Tournaments', '<p class="muted">No archived seasons yet.</p>'
    rows = w.a.index.db.execute('SELECT series, MAX(name), COUNT(*), MAX(prestige) FROM editions GROUP BY series '
                                'ORDER BY MAX(prestige) DESC LIMIT 200').fetchall()
    return 'Tournaments', '<table><tr><th>Tournament</th><th class="n">Editions</th><th class="n">Prestige</th></tr>' + ''.join(
        f'<tr><td><a href="/series/{quote(sid)}">{esc(name)}</a></td><td class="n">{n}</td><td class="n">{p:.0f}</td></tr>'
        for sid, name, n, p in rows) + '</table><p class="muted">The 200 most prestigious.</p>'


def course(w, q, cid):
    cid = unquote(cid)
    c = w.a.world['courses'].get(cid, {})
    eds = w.a.index.course_editions(cid)
    recs = {lid: r for lid, r in w.a.records.items() if lid.split(':')[0] == cid}
    out = [f'<p>{esc(c.get("city"))}, {esc(c.get("country"))} · {esc(c.get("class"))} · architect {esc(c.get("architect"))}'
           f' · opened {esc(c.get("opened"))}</p>']
    for lid, r in recs.items():
        cr = r.get('course_record')
        if cr:
            out.append(f'<p>{esc(lid.split(":")[1])} layout record: {cr["score"]} by {w.person_link(cr.get("golfer_id"))} '
                       f'({event_link(w, cr["event_id"])})</p>')
    out.append('<h2>Editions hosted</h2><table><tr><th>Edition</th><th>Layout</th><th>Winner</th></tr>' + ''.join(
        f'<tr><td>{event_link(w, e["event"])}</td><td>{esc(e["layout"])}</td><td>{w.person_link(e["winner"])}</td></tr>'
        for e in eds) + '</table>')
    return c.get('name', cid), ''.join(out)


def records(w, q):
    return 'Records & frivolities', ('<ul>' + ''.join(f'<li><a href="/records/{k}">{esc(t)}</a></li>' for k, (t, _, _) in BOARDS.items())
                                     + '</ul><h2>Definitions</h2><dl>' + ''.join(f'<dt>{esc(k)}</dt><dd class="muted">{esc(v)}</dd>'
                                                                              for k, v in DEFINITIONS.items()) + '</dl>')


def record(w, q, name):
    if not w.stats:
        return 'Records', '<p class="muted">No archived seasons yet.</p>'
    title, rows = board(w.stats, name, n=50)
    return title, ('<p class="muted">Active = still competing (may change). Partial = began before the archive; earlier '
                   'results are not included.</p><table><tr><th class="n">#</th><th>Golfer</th><th class="n">Value</th>'
                   '<th></th><th>Evidence</th></tr>' + ''.join(
                       f'<tr><td class="n">{i}</td><td>{w.person_link(r["person"])}</td><td class="n">{esc(r["value"])}</td>'
                       f'<td>{"<span class=tag>active</span> " if r["active"] else ""}{"<span class=tag>partial</span>" if r["partial"] else ""}</td>'
                       f'<td>{", ".join(event_link(w, e) for e in r["evidence"][:3])}</td></tr>'
                       for i, r in enumerate(rows, 1)) + '</table>')


def moments(w, q):
    if not (w.a and w.a.index):
        return 'Moments', '<p class="muted">No archived seasons yet.</p>'
    ms = list(reversed(w.a.index.moments()))[:200]
    return 'Moments', '<table><tr><th>Season</th><th>What</th><th>Golfer</th><th>Event</th></tr>' + ''.join(
        f'<tr><td>{m["year"]}</td><td>{esc(m["kind"])}</td><td>{w.person_link(m["person"])}</td><td>{event_link(w, m["event"])}</td></tr>'
        for m in ms) + '</table>'


ROUTES = [('/golfer/', golfer), ('/event/', event), ('/series/', series), ('/course/', course), ('/records/', record)]
PAGES = {'/': overview, '/rankings': rankings, '/search': search, '/records': records, '/moments': moments,
         '/tournaments': tournaments}


def make_handler(w):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            u = urlparse(self.path)
            q = parse_qs(u.query)
            try:
                with w.lock:
                    if u.path in PAGES:
                        title, body = PAGES[u.path](w, q)
                    else:
                        fn = next((f for prefix, f in ROUTES if u.path.startswith(prefix)), None)
                        if fn is None:
                            return self.send_error(404)
                        title, body = fn(w, q, u.path.split('/', 2)[2])
                    out = page(w, title, body)
            except Exception as e:                           # a prototype: show the problem, keep serving
                out = page(w, 'Something went wrong', f'<pre>{esc(repr(e))}</pre>')
            data = out.encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_POST(self):
            if self.path != '/advance' or not w.session:
                return self.send_error(404)
            n = int(self.headers.get('Content-Length', 0))
            w.submit(parse_qs(self.rfile.read(n).decode()))
            self.send_response(303)
            self.send_header('Location', '/')
            self.end_headers()

        def log_message(self, *args):
            pass
    return Handler


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('path', help='a session directory (tools/world.py create) or a history archive directory')
    ap.add_argument('--port', type=int, default=8765)
    a = ap.parse_args()
    w = World(a.path)
    print(f'Golf Legacy observer prototype: http://localhost:{a.port}  (Ctrl-C to stop)')
    HTTPServer(('127.0.0.1', a.port), make_handler(w)).serve_forever()


if __name__ == '__main__':
    main()
