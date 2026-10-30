"""Facts the observer's profile and statistics pages are drawn from (no HTML here): results with each
edition's classification when played, per-start prize money, career honors, season-by-season and per-tour
rollups, and ratings with their changes. Everything is derived from recorded results and snapshots.
"""
from __future__ import annotations

from collections import defaultdict

import observer_stats as ST

# Career honors: (key, label, test on an edition's classification when it was played). An edition counts in
# one category only (the first that matches); qualifying stages are never honors.
COLLEGE_TITLES = ('National Championship', 'World University Championship')
HONORS = (
    ('major', 'Major winner', lambda e: e['category'] == 'major'),
    ('premier', 'Premier Tour winner', lambda e: e['tier'] == 1),
    ('challenger', 'Challenger Tour winner', lambda e: e['tier'] == 2),
    ('regional', 'Regional tour winner', lambda e: e['tier'] == 3),
    ('mini', 'Mini tour winner', lambda e: e['tier'] == 4),
    ('college_national', 'College national champion',
     lambda e: e['category'] == 'college_postseason' and any(t in (e['name'] or '') for t in COLLEGE_TITLES)),
    ('college_postseason', 'College conference / regional champion', lambda e: e['category'] == 'college_postseason'),
    ('college', 'College event winner', lambda e: e['tier'] == 5),
    ('amateur_championship', 'Amateur championship winner',
     lambda e: e['category'] in ('national_amateur', 'elite_amateur')),
    ('amateur', 'Other amateur event winner', lambda e: e['tier'] == 6),
    ('club_pro', 'Club professional event winner', lambda e: e['tier'] == 8),
)
OUTCOMES = {'win': lambda p: p == 1, 'runner-up': lambda p: p == 2, 'top2': lambda p: p is not None and p <= 2,
            'top5': lambda p: p is not None and p <= 5, 'top10': lambda p: p is not None and p <= 10,
            'made-cut': lambda p: p is not None, 'missed-cut': lambda p: p is None}


def results(w, pid):
    """Every start, oldest first, with the edition's classification when played:
    [{year, week, event, series, name, tour, tier, category, pos, site, coach, caddie, route, prize, live}];
    prize is the money recorded as paid for that start (None where it was not recorded)."""
    out = []
    a = w.a
    if a is not None and pid in a.people:
        idx = a.index
        if idx is not None:
            prize = 's.prize' if getattr(idx, 'has_prize', False) else 'NULL'
            q = ('SELECT s.year, s.week, e.event_id, e.series, e.name, e.tour, e.tier, e.category, s.pos, s.site, s.coach, '
                 f's.caddie, r.text, {prize} FROM starts s JOIN editions e USING(eid) LEFT JOIN routes r USING(rid) '
                 'WHERE s.person = ?' + idx.upto('s.year') + ' ORDER BY s.year, s.week, e.event_id, s.site')
            keys = ('year', 'week', 'event', 'series', 'name', 'tour', 'tier', 'category', 'pos', 'site', 'coach',
                    'caddie', 'route', 'prize')
            out = [dict(zip(keys, r), live=False) for r in idx.db.execute(q, (pid,))]
        else:
            for y, e in a.events():
                for k, site in enumerate(e['finish']):
                    for gid, pos, _ in site:
                        if gid == pid:
                            coach, caddie = by_person(e['team'], pid, (0, 0))
                            out.append({'year': y, 'week': e['week'], 'event': e['id'], 'series': e['series'],
                                        'name': e.get('name'), 'tour': e.get('tour'), 'tier': e.get('tier'),
                                        'category': e.get('category'), 'pos': pos, 'site': k, 'coach': coach,
                                        'caddie': caddie, 'route': by_person(e['routes'], pid),
                                        'prize': _recorded_prize(e, k, pid), 'live': False})
    if w.live is not None:
        for eid, k, pos in w.live.by_person.get(pid, ()):
            e = w.live.editions[eid]
            coach, caddie = by_person(e['team'], pid, (0, 0))
            out.append({'year': int(eid.split(':')[0]), 'week': e['week'], 'event': eid, 'series': e['series'],
                        'name': e['name'], 'tour': e['tour'], 'tier': e['tier'], 'category': e['category'], 'pos': pos,
                        'site': k, 'coach': coach, 'caddie': caddie, 'route': by_person(e['routes'], pid),
                        'prize': _recorded_prize(e, k, pid), 'live': True})
    return out


def by_person(d, pid, default=None):
    """A per-golfer entry of an edition (team, routes...) whether its keys are integers (an archived season as
    the Archive decodes it) or strings (an edition record not yet archived, or read without decoding)."""
    v = d.get(pid)
    if v is None:
        v = d.get(str(pid))
    return default if v is None else v


def _recorded_prize(e, site, pid):
    """The prize money an edition recorded as paid to one golfer at one site (0 for an unpaid start), or None
    for an edition played before payouts were recorded."""
    prizes = e.get('prizes')
    if not prizes or site >= len(prizes):
        return None
    return by_person(prizes[site], pid, 0.0)


def is_qualifying(r):
    return r.get('tier') == 7


def start_prizes(w, pid, rows, db=None):
    """{(event, site): prize} for the given starts of one person where it is known: as recorded when paid
    (since rules 2026-10-30); for older seasons, the event's payouts
    recomputed (observer_stats.payouts) from its recorded finish, the golfers' in-season statuses and its
    purse (as recorded when played, or the calendar's), only for person-seasons whose payouts reconcile with
    the money actually paid. Unknown starts are left out (shown as unknown, never as zero)."""
    out = {}
    live_rec = None
    for r in rows:
        key = (r['event'], r['site'])
        if r.get('prize') is not None:                   # recorded when it was paid
            out[key] = r['prize']
            continue
        if r['live']:
            if live_rec is None:
                live_rec = ST.live_tables(w.live)[1]
            e = w.live.editions[r['event']]
            if not live_rec.get(pid):
                continue
            status = {g: p.get('status') for g, p in w.live.people.items()}
            won = ST.payouts(e['purse'], e['cut_top'], e['field_size'], e['finish'][r['site']],
                             lambda g: None if g not in status else status[g] == 'amateur')
            out[key] = won.get(pid, 0.0)
            continue
        if db is None or w.a is None or w.a.index is None:
            continue
        ok = db.execute('SELECT reconciled FROM season_prize WHERE person = ? AND year = ?', (pid, r['year'])).fetchone()
        m = ST.edition_money(db, r['event'])
        if not ok or not ok[0] or m is None:
            continue
        purse, cut_top, field_size, _ = m
        if not purse:
            out[key] = 0.0
            continue
        board = [x for x in w.a.index.leaderboard(r['event']) if x['site'] == r['site']]
        order = sorted(board, key=lambda x: (x['pos'] is None, x['pos'] if x['pos'] is not None else 0))
        ids = [x['person'] for x in order]
        status = {p: s for p, s in w.a.index.db.execute(
            f'SELECT person, status FROM seasons WHERE year = ? AND person IN ({",".join("?" * len(ids))})',
            [r['year'], *ids])}
        try:
            won = ST.payouts(purse, cut_top, field_size, [(x['person'], x['pos'], x['total']) for x in order],
                             lambda g: None if g not in status else status[g] == 'amateur')
        except KeyError:
            continue
        out[key] = won.get(pid, 0.0)
    return out


def honors(rows):
    """[(key, label, wins [(year, event)])] earned, from wins and each edition's classification when played."""
    got = defaultdict(list)
    for r in rows:
        if r['pos'] != 1 or is_qualifying(r):
            continue
        for key, _, test in HONORS:
            if test({'category': r.get('category'), 'tier': r.get('tier'), 'name': r.get('name')}):
                got[key].append((r['year'], r['event']))
                break
    return [(k, label, got[k]) for k, label, _ in HONORS if got[k]]


def season_rollup(rows):
    """{year: {'all': stats, 'tours': {tour: stats}}} from starts (qualifying counted apart); stats as
    observer_stats.COLUMNS (cuts only for stroke-play events with a cut where the format is known)."""
    out = {}
    for r in rows:
        y = out.setdefault(r['year'], {'all': dict.fromkeys(ST.COLUMNS, 0), 'tours': {}})
        t = y['tours'].setdefault(r['tour'] or '', dict.fromkeys(ST.COLUMNS, 0))
        for agg in (y['all'], t):
            if is_qualifying(r):
                agg['qualifiers'] += 1
                continue
            p = r['pos']
            agg['starts'] += 1
            agg['wins'] += p == 1
            agg['runner_ups'] += p == 2
            agg['top2'] += p is not None and p <= 2
            agg['top5'] += p is not None and p <= 5
            agg['top10'] += p is not None and p <= 10
            if r.get('cut') is not None:
                agg['cut_events'] += r['cut']
                agg['cuts_made'] += r['cut'] and p is not None
    return out


def cut_flags(w, rows, db=None):
    """Mark each start with whether its event had a cut (stroke play with a cut): r['cut'] = 1 / 0 / None.
    The format as played: the current season's editions, else the statistics store (built from the season
    files), else the calendar's -- the store's own source for seasons archived before formats were recorded,
    so a page reads the same before and after the store is built."""
    cal = None
    for r in rows:
        r['cut'] = None
        if r['live']:
            e = w.live.editions[r['event']]
            r['cut'] = int(bool(e.get('cut_top')) and not e.get('match_play'))
            continue
        m = ST.edition_money(db, r['event']) if db is not None else None
        if m is not None:
            r['cut'] = int(bool(m[1]) and not m[3])
            continue
        if cal is None:
            from golfsim.course_library import default_library
            cal = default_library().calendar.by_id
        ser = cal.get(r['series'])
        if ser is not None:
            r['cut'] = int(bool(ser.cut_top) and not ser.match_play)
    return rows


def career_rows(w, pid):
    """[(year, season row)] for a golfer's archived seasons, without decoding season files: the index's full
    rows (schema 2 and later), else its short season rows (tour, status, lifestyle, starts, wins, prize, year-end
    rankings) for an older index opened read-only -- whatever a row lacks shows as not recorded."""
    a = w.a
    if a is None or pid not in a.people:
        return []
    idx = a.index
    if idx is None:
        return a.playing_career(pid)
    if idx.derived_complete(a.years):
        return idx.career(pid)
    return [(r['year'], r) for r in idx.seasons(pid)]


def recorded_peak(w, pid):
    """The highest Overall recorded for a golfer, or None: {'value', 'year', 'week' (when first recorded at that
    value: 0 = the season's start, 52 = its end before aging), 'source' ('noted' -- the engine's prospective peak,
    'start of season' -- an archived start-of-season rating, 'current'), 'since' (first season of the engine's
    noting for this golfer, or None), 'snapshots' (seasons with a start-of-season rating), 'first' (first season
    this golfer was in the world's records), 'initial' (career began before the world's records), 'complete'
    (noting covers the whole career)}. Only recorded ratings: never potential, guessed development or a
    present rating moved into the past. A value equal to one decimal keeps its earliest date."""
    cands = []
    lp = w.live.people.get(pid, {}) if w.live else {}
    rows = career_rows(w, pid)
    noted = [(y, r['peak']) for y, r in rows if r.get('peak')]
    if lp.get('peak'):
        noted.append((None, lp['peak']))
    for _, pk in noted:
        cands.append((round(pk[0], 1), pk[1], pk[2], 'noted'))
    keys = (w.a.world.get('rating_keys') if w.a else None) or ['overall']
    i = keys.index('overall') if 'overall' in keys else 0
    snaps = rating_snapshots(w, pid)
    for y, r in snaps.items():
        cands.append((round(r[i], 1), y, 0, 'start of season'))
    if lp.get('ratings'):
        c = w.live.cursor
        cands.append((round(lp['ratings'][0], 1), c['year'], c['week'], 'current'))
    if not cands:
        return None
    top = max(v for v, *_ in cands)
    v, y, wk, src = min((c for c in cands if c[0] == top), key=lambda c: (c[1], c[2]))
    first = rows[0][0] if rows else (w.live.cursor['year'] if lp else None)
    initial = bool(w.a and pid in w.a.people and w.a.people[pid].get('initial')) or bool(lp.get('initial'))
    # since: the first season the engine was noting this golfer's peak (a season archived with it, or the
    # running world's start of noting); complete: noting began before they arrived, or with the world itself
    began = [y for y, r in rows if r.get('peak')]
    if lp.get('peak') and getattr(w.live, 'peak_since', None) is not None:
        began.append(w.live.peak_since)
    since = max(min(began), first) if began and first is not None else (min(began) if began else None)
    world_first = w.live.first_year if w.live else (w.a.years[0] if w.a and w.a.years else None)
    complete = (not initial and since is not None and first is not None
                and (min(began) < first or min(began) == world_first))
    return {'value': v, 'year': y, 'week': wk, 'source': src, 'since': since, 'snapshots': sorted(snaps),
            'first': first, 'initial': initial, 'complete': complete}


def rating_snapshots(w, pid):
    """{year: [overall, attrs...]}: ratings at the start of each season (recorded when the season before it
    was archived), in the archive's rating_keys order."""
    out = {}
    a = w.a
    if a is None or pid not in a.people or 'rating_keys' not in a.world:
        return out
    for y, row in career_rows(w, pid):
        if row.get('ratings'):
            out[y + 1] = row['ratings']
    return out
