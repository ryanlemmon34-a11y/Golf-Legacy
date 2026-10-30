"""Golf statistics, world ranking points and the records built on them, as HTML fragments for the observer.

- Golf statistics (golfsim.golfstats): a golfer's figures season by season and over a career, and the Stats
  directory's golf view, always from summed counts and opportunities (never averages of averages), with the
  sample beside each figure and "not recorded" for seasons played before the counts were kept.
- World ranking points (rules: world-ranking): the ranking as of any recorded week (each week's top 200 with
  average, events and divisor), and a golfer's ranking worked out from the points each start earned, start
  by start, with the weight each still carries -- the same arithmetic as the engine (golfsim.prestige).
- Records: longest drives, event / season / career driving averages (with sample qualification), largest
  stroke-play winning margins (regulation; a playoff is a margin of zero) and largest match-play wins.

Nothing here changes the world: it reads what the archive and the live snapshot recorded.
"""
from __future__ import annotations

import json
from collections import defaultdict
from urllib.parse import quote, urlencode

from golfsim import golfstats as GS
from golfsim import prestige as PR

NOT_RECORDED = '<span class="muted">not recorded</span>'
# the figures shown in golf tables, in order
SHOWN = ('scoring', 'distance', 'fairways', 'gir', 'scrambling', 'sand', 'putts_round', 'putts_gir', 'birdies',
         'bogeys', 'sg_total')
SHORT = {'scoring': 'Scoring', 'distance': 'Driving dist.', 'fairways': 'Fairways', 'gir': 'GIR',
         'scrambling': 'Scrambling', 'sand': 'Sand saves', 'putts_round': 'Putts/rd', 'putts_gir': 'Putts/GIR',
         'birdies': 'Birdies+/rd', 'bogeys': 'Bogeys+/rd', 'sg_total': 'SG/rd (engine)'}
# Proposed sample qualifications (for the owner's review; not real-world rules): see records and Stats.
QUALIFY = {'event_drives': 20, 'season_drives': 200, 'career_drives': 1000, 'season_rounds': 20, 'career_rounds': 100}
DEFINITIONS_NOTE = ('Golf statistics are counted from every simulated shot of completed 18-hole stroke-play rounds and '
                    'added up as counts over opportunities (1 of 2 plus 8 of 10 is 9 of 12, 75%, never the average of 50% '
                    'and 80%). Definitions: <a href="/rules#golf-statistics">golf statistics</a>. N/A: no opportunities '
                    '(not zero). Seasons played before these counts were kept show “not recorded”. Strokes gained is '
                    'against the engine\'s own expected-strokes table, not a validated real-world baseline. Qualifying '
                    'stages are not included.')


def _o():
    import observer
    return observer


def _st():
    import observer_stats
    return observer_stats


def _counters(row):
    return {k: row.get(k, 0) or 0 for k in GS.FIELDS}


def _add(into, row):
    for k in GS.FIELDS:
        into[k] = into.get(k, 0) + (row.get(k, 0) or 0)
    into['golf_starts'] = into.get('golf_starts', 0) + (row.get('golf_starts', 0) or 0)
    into['starts'] = into.get('starts', 0) + (row.get('starts', 0) or 0)
    return into


def figure_cells(c):
    """The SHOWN figures of a counters dict, formatted (N/A where there were no opportunities)."""
    return [GS.fmt(k, GS.metric(k, c)) for k in SHOWN]


# ---- a golfer's golf statistics -------------------------------------------------------------------------------------
def person_golf(w, pid):
    """{year: {'all': counters+starts, 'tours': {tour: counters+starts}, 'live': bool}} from the statistics store and
    the live season (None while the store is being built)."""
    db, building = w.statistics()
    out = {}
    if db is not None:
        for y, s in _st().person_seasons(db, pid).items():
            d = out.setdefault(y, {'all': {}, 'tours': {}, 'live': False})
            for t, row in s['tours'].items():
                d['tours'][t] = _add({}, row)
                _add(d['all'], row)
    elif building:
        return None
    live = w.live_statistics() if w.live else None
    if live is not None:
        y = w.live.cursor['year']
        if not (w.a and y in w.a.years):
            for (gid, t), row in live[0].items():
                if gid == pid:
                    d = out.setdefault(y, {'all': {}, 'tours': {}, 'live': True})
                    d['tours'][t] = _add({}, row)
                    _add(d['all'], row)
    return out


def golf_section(w, pid):
    """The profile's golf statistics: each season (all tours), then the career and the career by tour."""
    O = _o()
    data = person_golf(w, pid)
    if data is None:
        return '<h2>Golf statistics</h2><p class="muted">Working out the statistics from the history…</p>'
    if not data:
        return ''
    head = ['Season', 'Starts', 'Rounds'] + [SHORT[k] for k in SHOWN] + ['Coverage']
    rows, career, by_tour = [], {}, defaultdict(dict)
    for y in sorted(data):
        d = data[y]
        a = d['all']
        if not a.get('starts'):
            continue
        label = str(y) + (' <span class="tag">so far</span>' if d['live'] else '')
        if not a.get('golf_starts'):
            rows.append([label, str(a['starts']), '—'] + [NOT_RECORDED] + [''] * (len(SHOWN) - 1) + [_coverage(a)])
            continue
        _add(career, a)
        for t, row in d['tours'].items():
            _add(by_tour[t], row)
        rows.append([label, str(a['starts']), str(a['rounds'])] + figure_cells(a) + [_coverage(a)])
    if not rows:
        return ''
    if career.get('golf_starts'):
        rows.append(['<strong>Career</strong>', str(career['starts']), str(career['rounds'])] + figure_cells(career)
                    + [_coverage(career)])
        if len(by_tour) > 1:
            for t, c in sorted(by_tour.items(), key=lambda x: (w.tours().get(x[0], {}).get('tier', 9), x[0])):
                if c.get('golf_starts'):
                    rows.append(['&nbsp;&nbsp;career ↳ ' + O.tour_link(w, t), str(c['starts']), str(c['rounds'])]
                                + figure_cells(c) + [_coverage(c)])
    return ('<h2>Golf statistics</h2>' + O.table(head, rows, numeric=tuple(range(1, len(head) - 1)))
            + f'<p class="muted">{DEFINITIONS_NOTE} Coverage: starts with recorded statistics / starts. The career rows '
              'add only recorded seasons. <a href="/stats?show=golf">Compare in the Stats directory</a>.</p>')


def _coverage(c):
    return f'{c.get("golf_starts", 0)}/{c.get("starts", 0)} starts'


# ---- the Stats directory's golf view --------------------------------------------------------------------------------
def stats_rows(w, data, sort, qualify):
    """Rows [(pid, counters)] with recorded golf statistics, qualified by rounds, sorted by `sort` (a METRICS key:
    best first; missing values last) or by rounds."""
    rows = [(pid, r) for pid, r in data.items() if r.get('golf_starts') and r.get('rounds', 0) >= qualify]
    if sort in GS.METRICS:
        better = GS.METRICS[sort][3]
        def key(x):
            v = GS.metric(sort, x[1])
            return (v is None, -(v or 0) if better else (v or 0), x[0])
        rows.sort(key=key)
    else:
        rows.sort(key=lambda x: (-(x[1].get(sort) or 0), x[0]))
    return rows


def golf_table(w, q, data, path, keep, cur_note, single_season):
    O = _o()
    sort = O.one(q, 'sort', 'scoring')
    sort = sort if sort in GS.METRICS or sort in ('rounds', 'golf_starts') else 'scoring'
    default = QUALIFY['season_rounds'] if single_season else QUALIFY['career_rounds']
    try:
        qualify = max(0, int(O.one(q, 'min', str(default)) or default))
    except ValueError:
        qualify = default
    rows = stats_rows(w, data, sort, qualify)
    unqualified = sum(1 for r in data.values() if r.get('golf_starts')) - len(rows)
    chunk, pager = O.paged(rows, q, path)
    start = (max(1, int(O.one(q, 'page', '1') or 1)) - 1) * O.PAGE_SIZE
    keep = {k: v for k, v in keep.items() if k not in ('sort', 'page')}
    def th(k, label):
        mark = ' ▼' if k == sort else ''
        return f'<th class="n"><a href="{path}?{urlencode({**keep, "sort": k})}">{O.esc(label)}{mark}</a></th>'
    head = ('<tr><th class="n">#</th><th>Golfer</th><th>Nation</th>' + th('golf_starts', 'Starts') + th('rounds', 'Rounds')
            + ''.join(th(k, SHORT[k]) for k in SHOWN) + '</tr>')
    body = []
    for i, (pid, r) in enumerate(chunk, start + 1):
        body.append(f'<tr><td class="n">{i}</td><td>{w.person_link(pid)}</td>'
                    f'<td>{O.nation_link((w.person(pid) or {}).get("country"))}</td>'
                    f'<td class="n">{r["golf_starts"]}</td><td class="n">{r["rounds"]}</td>'
                    + ''.join(f'<td class="n">{c}</td>' for c in figure_cells(r)) + '</tr>')
    qual = (f'Qualified: at least {qualify} recorded rounds ({unqualified:,} golfers with fewer left out; '
            + (f'<a href="{path}?{urlencode({**keep, "sort": sort, "min": 0})}">include everyone</a>' if qualify else
               f'<a href="{path}?{urlencode({**keep, "sort": sort})}">qualified only</a>')
            + f'). Proposed thresholds: {QUALIFY["season_rounds"]} rounds for a season, {QUALIFY["career_rounds"]} '
              'all-time, for review.')
    return (f'<p>{cur_note} · {len(rows):,} golfers · {qual}</p>'
            + f'<div class="scroll"><table>{head}{"".join(body)}</table></div>' + pager
            + f'<p class="muted">{DEFINITIONS_NOTE} Sorted best first (lowest first for scoring, putts and bogeys); '
              'N/A last.</p>')


# ---- world ranking points ------------------------------------------------------------------------------------------
def last_played(w):
    """(year, week) of the latest week played in the snapshot (the ranking the snapshot shows)."""
    if w.live is None:
        return (w.a.years[-1], 52) if w.a else None
    y, wk = w.live.cursor['year'], w.live.cursor['week']
    return (y, wk - 1) if wk > 1 else (y - 1, 52)


def first_year(w):
    if w.live is not None and getattr(w.live, 'first_year', None):
        return w.live.first_year
    return w.a.years[0] if w.a else None


def _abs(w, y, wk):
    return (y - first_year(w)) * 52 + wk


def point_rows(w, pid, at):
    """([(year, week, event id, position, points)] of the golfer's counted starts in the 104 weeks to `at`, in the
    order they were earned, seeded rows as (None, abs week, None, None, points)), and the seasons in that window
    whose points were not recorded."""
    y_at, w_at = at
    years = [y for y in (y_at - 2, y_at - 1, y_at) if y >= first_year(w)]
    rows, missing = [], []
    live_year = w.live.year if w.live is not None else None
    for y in years:
        if live_year == y and not (w.a and y in w.a.years):
            for eid, k, pos in w.live.by_person.get(pid, ()):
                e = w.live.editions[eid]
                pts = e.get('points')
                if pts and k < len(pts) and str(pid) in pts[k]:
                    rows.append((y, e['week'], eid, pos, pts[k][str(pid)]))
            continue
        if not (w.a and y in w.a.years):
            continue
        got = _archived_points(w, pid, y)
        if got is None:
            missing.append(y)
        else:
            rows += got
    seeds = []
    if first_year(w) >= y_at - 2:
        seed = (w.live.wr_seed if w.live is not None and getattr(w.live, 'wr_seed', None) else None)
        if not seed and w.a and w.a.years and w.a.years[0] == first_year(w):
            seed = (_season_file(w, w.a.years[0]) or {}).get('ranking_seed', {})
        got = (seed.get(pid) or seed.get(str(pid)) or []) if seed else []
        seeds = [(None, aw, None, None, p) for aw, p in got]              # in the order they were seeded
    rows.sort(key=lambda r: (r[0], r[1], r[2]))
    return seeds + rows, missing


def _season_file(w, y):
    import observer_history as OH
    return OH._season_file(w, y)


def _archived_points(w, pid, y):
    """The golfer's counted starts of an archived season with their points, or None where the season did not
    record points."""
    idx = w.a.index
    if idx is not None and getattr(idx, 'has_points', False):
        if idx.db.execute('SELECT 1 FROM starts WHERE year = ? AND points IS NOT NULL LIMIT 1', (y,)).fetchone() is None:
            return None
        return [(y, wk, eid, pos, pts) for wk, eid, pos, pts in idx.db.execute(
            'SELECT s.week, e.event_id, s.pos, s.points FROM starts s JOIN editions e USING(eid) WHERE s.person = ? '
            'AND s.year = ? AND s.points IS NOT NULL ORDER BY s.week, e.event_id', (pid, y))]
    d = _season_file(w, y)
    evs = (d or {}).get('events', [])
    if not any(e.get('points') for e in evs):
        return None
    out = []
    for e in evs:
        for k, site in enumerate(e.get('points') or []):
            if str(pid) in site:
                pos = next((p for g, p, _ in e['finish'][k] if g == pid), None)
                out.append((y, e['week'], e['id'], pos, site[str(pid)]))
    out.sort(key=lambda r: (r[1], r[2]))
    return out


def ranking_at(w, pid, at):
    """The golfer's world ranking arithmetic at week `at`: {'total', 'events', 'divisor', 'average', 'rows':
    [(year, week, event, pos, points, age, weight)], 'missing': [years]} -- exactly the engine's sums."""
    rows, missing = point_rows(w, pid, at)
    now = _abs(w, *at)
    window = []
    for y, wk, eid, pos, pts in rows:
        aw = wk if y is None else _abs(w, y, wk)
        age = now - aw
        if 0 <= age < PR.RANK_WEEKS:
            window.append((y, wk, eid, pos, pts, age, PR.ranking_weight(age), aw))
    total, n = PR.ranking_total([(r[7], r[4]) for r in window], now)
    div = PR.ranking_divisor(n)
    return {'total': total, 'events': n, 'divisor': div, 'average': total / div if total > 0 else 0.0,
            'rows': window, 'missing': missing}


def ranking_section(w, pid):
    """A golfer's world ranking now, with every counted start (points earned, weight now, points counted)."""
    O = _o()
    at = last_played(w)
    if at is None or first_year(w) is None:
        return ''
    r = ranking_at(w, pid, at)
    pos = w.live.wr.get(pid) if w.live is not None else None
    if not r['rows'] and not pos:
        return ''
    head = (f'<h2>World ranking points</h2><p>As of {at[0]} week {at[1]}: '
            + (f'No. {pos} · ' if pos else 'unranked · ')
            + f'average <strong>{r["average"]:.3f}</strong> = {r["total"]:.2f} points / {r["divisor"]} '
              f'({r["events"]} counted start{"s" if r["events"] != 1 else ""} in the last 104 weeks; the divisor is the '
              f'starts, at least 40 and at most 52) · <a href="/rules#world-ranking">how the ranking works</a></p>')
    if r['missing']:
        head += (f'<p class="muted">Points were not recorded for {", ".join(map(str, r["missing"]))} (played before they '
                 'were kept): the average above leaves those starts out and is not the ranking of the time.</p>')
    rows = []
    for y, wk, eid, pos_, pts, age, wt, _ in reversed(r['rows']):
        what = (O.event_link(w, eid) if eid else '<span class="muted">seeded when the world began</span>')
        rows.append([f'{y} wk {wk}' if y else '—', what, O.esc(pos_ or ('—' if eid is None else 'MC')),
                     f'{pts:.2f}', f'{age} wk', f'{wt:.3f}', f'{pts * wt:.2f}'])
    return head + O.table(['When', 'Event', 'Pos', 'Points earned', 'Age', 'Weight now', 'Counted'], rows,
                          numeric=(2, 3, 4, 5, 6))


def rankings_points_page(w, q):
    """The world ranking as of a recorded week: position, average, total, counted starts and divisor."""
    O = _o()
    at = last_played(w)
    years = (list(w.a.years) if w.a else []) + ([w.live.year] if w.live is not None and not (w.a and w.live.year in w.a.years) else [])
    if not years:
        return '<p class="muted">No week has been played yet.</p>'
    try:
        y = int(O.one(q, 'year', str(at[0])) or at[0])
        wk = int(O.one(q, 'week', str(at[1])) or at[1])
    except ValueError:
        y, wk = at
    if w.live is not None and y == w.live.year and not (w.a and y in w.a.years):
        snap = w.live.rank_top.get(wk)
    else:
        snap = ((_season_file(w, y) or {}).get('ranking_points') or {}).get(str(wk)) if w.a and y in w.a.years else None
    f = O.filters('/rankings', q, [('kind', 'Ranking', [('points', 'World (points)')]),
                                    ('year', 'Season', [(str(x), str(x)) for x in reversed(years)]),
                                    ('week', 'Week', [(str(x), str(x)) for x in range(1, 53)])])
    if not snap:
        return f + (f'<p class="muted">No ranking recorded for {y} week {wk}: weekly averages are kept from the golf-statistics '
                    'update on (earlier seasons keep the order of the top 100 only: <a href="/rankings?kind=world">the '
                    'ranking</a>), and a week not yet played has none.</p>')
    rows = [[str(i), w.person_link(g), f'{a:.3f}', f'{a * PR.ranking_divisor(n):.2f}', str(n), str(PR.ranking_divisor(n))]
            for i, (g, a, n) in enumerate(snap, 1)]
    return (f + f'<p>{y} week {wk}: the top {len(snap)} by average points (kept each week).</p>'
            + O.table(['#', 'Golfer', 'Average', 'Points (weighted)', 'Counted starts', 'Divisor'], rows,
                      numeric=(0, 2, 3, 4, 5))
            + '<p class="muted">Average = weighted points / divisor; the divisor is the starts counted in the last 104 '
              'weeks, at least 40 and at most 52. Points: <a href="/rules#world-ranking">world ranking rule</a>. Each '
              'golfer\'s profile lists the starts behind their points.</p>')


# ---- records ------------------------------------------------------------------------------------------------------
GOLF_RECORDS = {
    'longest-drive': ('Longest drives', 'yards, one measured drive (carry and roll)'),
    'event-driving-average': ('Highest driving average in an event', 'yards per measured drive in one edition'),
    'season-driving-average': ('Highest driving average in a season', 'yards per measured drive in one season'),
    'career-driving-average': ('Highest career driving average', 'yards per measured drive over the recorded career'),
    'largest-margin': ('Largest winning margins (stroke play)', 'strokes ahead of the next finisher after regulation'),
    'largest-match-win': ('Largest match-play wins', 'holes up with holes to play'),
}


def records_list():
    return ''.join(f'<li><a href="/golf-records/{k}">{_o().esc(t)}</a></li>' for k, (t, _) in GOLF_RECORDS.items())


def golf_record(w, q, name):
    O = _o()
    if name not in GOLF_RECORDS:
        return 'Records', '<p class="muted">No such list.</p>'
    title, unit = GOLF_RECORDS[name]
    db, building = w.statistics()
    if db is None:
        return title, (O.no_history() if not w.a else '<p>Working out the statistics from the history…</p>'
                       '<meta http-equiv="refresh" content="3">')
    tour = O.one(q, 'tour', '') or ''
    tours = sorted(((k, t.get('name', k)) for k, t in w.tours().items()), key=lambda x: x[1])
    fields = [('tour', 'Tour', [('', 'all tours')] + tours)]
    where, args = ('tour = ?', [tour]) if tour else ('1', [])
    years = list(w.a.years)
    recorded = [y for (y,) in db.execute('SELECT DISTINCT year FROM agg WHERE golf_starts > 0 ORDER BY year')]
    cov = (f'Recorded seasons: {O.span(recorded, False)}' if recorded else 'No season with recorded golf statistics yet')
    cov += f' (of {O.span(years, False)}); the current season counts once it ends.'
    active = lambda pid: ((w.person(pid) or {}).get('golfer') or {}).get('lifestyle') not in (None, 'retired')
    now_text = lambda pid: 'competing' if active(pid) else 'closed (retired)'
    rows, head, numeric, note = [], [], (), ''
    if name == 'longest-drive':
        q_ = f'SELECT person, year, event_id, week, tenths, round, hole FROM long_drives WHERE {where} ORDER BY tenths DESC, person LIMIT 100'
        for i, (pid, y, eid, wk, t, rd, hole) in enumerate(db.execute(q_, args), 1):
            rows.append([str(i), w.person_link(pid), f'{t / 10:.1f}', f'{y} wk {wk}', O.event_link(w, eid),
                         _venue(w, eid), f'R{rd}, hole {hole}', 'fixed (a single shot)'])
        head, numeric = ['#', 'Golfer', 'Yards', 'When', 'Event', 'Course', 'Round, hole', 'Now'], (0, 2)
        note = 'Each golfer\'s longest measured drive of an event: the first driver tee shot on a par 4 or 5, where it finished.'
    elif name == 'event-driving-average':
        tiers = _st().EVENT_DRIVE_TIERS
        asked = _min(q, QUALIFY['event_drives'], tiers[0])
        mn = max(t for t in tiers if t <= asked)               # the lists are kept for these thresholds
        fields.append(('min', 'Measured drives at least', [(str(x), str(x)) for x in
                                                           sorted(tiers, key=lambda t: (t != QUALIFY['event_drives'], t))]))
        q_ = (f'SELECT person, year, event_id, week, tenths, drives FROM event_drives WHERE {where} AND tier = ? '
              'ORDER BY CAST(tenths AS REAL) / drives DESC, person LIMIT 100')
        for i, (pid, y, eid, wk, t, n) in enumerate(db.execute(q_, args + [mn]), 1):
            rows.append([str(i), w.person_link(pid), f'{t / 10 / n:.1f}', str(n), f'{y} wk {wk}', O.event_link(w, eid),
                         _venue(w, eid), 'fixed (one event)'])
        head, numeric = ['#', 'Golfer', 'Yards per drive', 'Drives', 'When', 'Event', 'Course', 'Now'], (0, 2, 3)
        note = (f'Qualified: at least {mn} measured drives in the edition (proposed: {QUALIFY["event_drives"]}, about two '
                f'rounds; lists are kept for {", ".join(map(str, tiers))} drives, each qualified before its leaders are '
                'kept). Not the edition\'s longest single drive.')
    elif name in ('season-driving-average', 'career-driving-average'):
        season = name.startswith('season')
        key = 'season_drives' if season else 'career_drives'
        mn = _min(q, QUALIFY[key], 1)
        fields.append(('min', 'Measured drives at least', [(str(x), str(x)) for x in
                                                           ((200, 400, 100, 1) if season else (1000, 2000, 500, 1))]))
        group = 'person, year' if season else 'person'
        q_ = (f'SELECT {group}, SUM(drive_tenths), SUM(drives), SUM(golf_starts), MIN(year), MAX(year) FROM agg '
              f'WHERE {where} AND golf_starts > 0 GROUP BY {group} HAVING SUM(drives) >= ? '
              'ORDER BY CAST(SUM(drive_tenths) AS REAL) / SUM(drives) DESC, person LIMIT 100')
        for i, r in enumerate(db.execute(q_, args + [mn]), 1):
            if season:
                pid, y, t, n, starts, _, _ = r
                ev = O.results_link(pid, f'{starts} starts', year=y, tour=tour or None)
                rows.append([str(i), w.person_link(pid), f'{t / 10 / n:.1f}', f'{n:,}', str(y), ev,
                             'fixed (a completed season)'])
            else:
                pid, t, n, starts, y0, y1 = r
                ev = O.results_link(pid, f'{starts} starts', tour=tour or None)
                began = db.execute('SELECT MIN(year) FROM agg WHERE person = ?', (pid,)).fetchone()[0]
                partial = bool(w.a.people.get(pid, {}).get('initial')) or (began is not None and began < y0)
                rows.append([str(i), w.person_link(pid), f'{t / 10 / n:.1f}', f'{n:,}', f'{y0}–{y1}' if y1 != y0 else str(y0),
                             ev, now_text(pid) + (' <span class="tag">partial</span>' if partial else '')])
        head = ['#', 'Golfer', 'Yards per drive', 'Drives', 'Season' if season else 'Recorded seasons', 'Evidence', 'Now']
        numeric = (0, 2, 3)
        note = (f'Total yards of every measured drive over the {"season" if season else "recorded career"} divided by the '
                f'number of drives (never an average of event averages). Qualified: at least {mn:,} measured drives '
                f'(proposed: {QUALIFY[key]:,}). ' + ('' if season else 'Partial: the career began before the world\'s records '
                                                      'or before golf statistics were recorded, so earlier seasons are '
                                                      'missing. An active career is unfinished.'))
    elif name == 'largest-margin':
        rounds = O.one(q, 'rounds', '4') or '4'
        major = O.one(q, 'major', '') == '1'
        try:
            min_field = int(O.one(q, 'field', '30') or 30)
        except ValueError:
            min_field = 30
        fields += [('rounds', 'Length', [('4', '72 holes'), ('3', '54 holes'), ('2', '36 holes'), ('1', '18 holes')]),
                   ('major', 'Events', [('', 'all'), ('1', 'majors only')]),
                   ('field', 'Field at least', [(str(x), str(x)) for x in (30, 60, 100, 2)])]
        q_ = (f'SELECT year, event_id, week, winner, win_total, runner_total, margin, runners_up, playoff, field FROM margins '
              f'WHERE {where} AND rounds = ? AND field >= ?' + (' AND major = 1' if major else '')
              + ' ORDER BY margin DESC, year, event_id LIMIT 100')
        for i, (y, eid, wk, win, wt, rt, m, ru, po, fld) in enumerate(db.execute(q_, args + [int(rounds), min_field]), 1):
            age = _age(w, win, y)
            rows.append([str(i), w.person_link(win), str(m), f'{wt} / {rt}',
                         ', '.join(w.person_link(g) for g in json.loads(ru)), f'{y} wk {wk}', O.event_link(w, eid),
                         _venue(w, eid), age, str(fld), f'playoff, {po} holes' if po else '—'])
        head = ['#', 'Winner', 'Margin', 'Winning / next total', 'Next best (all tied)', 'When', 'Event', 'Course',
                'Age*', 'Field', 'Playoff']
        numeric = (0, 2, 8, 9)
        note = ('Regulation strokes between the winner and the next finisher: every golfer tied on that total is listed. A '
                'playoff win had a regulation margin of zero (the playoff is shown apart). Events of different lengths are '
                'kept apart (choose the length); single-site editions only; qualifying stages excluded. Margins come from '
                'the recorded final totals, so they cover every archived season. *Age: season year minus birth year.')
    elif name == 'largest-match-win':
        stage = O.one(q, 'stage', '') or ''
        fields.append(('stage', 'Matches', [('', 'all matches'), ('final', 'finals only')]))
        q_ = (f'SELECT year, event_id, week, stage, winner, loser, result, holes, up, remaining FROM matches WHERE {where}'
              + (" AND stage = 'final'" if stage == 'final' else '') + ' ORDER BY up DESC, remaining DESC, year LIMIT 100')
        for i, (y, eid, wk, stg, win, lose, res, holes, up, rem) in enumerate(db.execute(q_, args), 1):
            rows.append([str(i), w.person_link(win), O.esc(res), w.person_link(lose), O.esc(stg), f'{holes} holes',
                         f'{y} wk {wk}', O.event_link(w, eid), _venue(w, eid)])
        head = ['#', 'Winner', 'Result', 'Beaten', 'Round', 'Scheduled', 'When', 'Event', 'Course']
        numeric = (0,)
        note = ('Holes up with holes left to play (7&6: seven up with six to play); “2 up” went the distance; “19 holes”: '
                'won at an extra hole. Never converted to strokes. A match win is not a championship: the final is the '
                'championship match (choose “finals only”). Recorded from the golf-statistics update on.')
    f = O.filters(f'/golf-records/{name}', q, fields)
    return title, (f + f'<p class="muted">{O.esc(cov)} Counted in {O.esc(unit)}.</p>'
                   + (O.table(head, rows, numeric=numeric) if rows else '<p class="muted">Nobody qualifies yet.</p>')
                   + f'<p class="muted">{note} Definitions: <a href="/rules#golf-statistics">golf statistics</a>.</p>')


def _min(q, default, floor):
    try:
        return max(floor, int(_o().one(q, 'min', str(default)) or default))
    except ValueError:
        return default


def _age(w, pid, y):
    born = (w.person(pid) or {}).get('born')
    return str(y - born) if born else '—'


def _venue(w, eid):
    O = _o()
    e = w.edition(eid)
    if not e:
        return '—'
    return ' · '.join(O.course_link(w, c, lay) for c, lay, _ in e['sites'])


# ---- an edition's statistics -------------------------------------------------------------------------------------
def edition_stats(w, e):
    """Each golfer's statistics in one edition (their rounds there), with their longest drive."""
    import observer_history as OH
    O = _o()
    full = OH.full_edition(w, e)
    golf = (full or {}).get('golf')
    if not golf:
        return ('<p class="muted">Golf statistics were not recorded for this edition (played before they were kept); '
                'they are never estimated from scores or ratings.</p>')
    rows = []
    pos = {(g, k): p for k, site in enumerate(full['finish']) for g, p, _ in site}
    for k, site in enumerate(golf):
        for g, v in site.items():
            c = GS.as_dict(v[:GS.N])
            long = f'{v[GS.N] / 10:.1f} (R{v[GS.N + 1]}, hole {v[GS.N + 2]})' if len(v) > GS.N and v[GS.N] else '—'
            p = pos.get((int(g), k))
            rows.append((p is None, p or 0, [O.esc(p or 'MC'), w.person_link(int(g)), str(c['rounds'])]
                         + figure_cells(c) + [long]))
    rows.sort(key=lambda r: (r[0], r[1]))
    return (O.table(['Pos', 'Golfer', 'Rounds'] + [SHORT[k] for k in SHOWN] + ['Longest drive (yds)'], [r[2] for r in rows],
                    numeric=tuple(range(2, 3 + len(SHOWN))))
            + f'<p class="muted">Each golfer\'s stroke-play rounds in this edition. {DEFINITIONS_NOTE}</p>')
