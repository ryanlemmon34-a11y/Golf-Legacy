"""Where are they now: follow a historical field or cohort through the rest of their careers.

A cohort is a set of people fixed at one moment, each by their id (names can repeat; ids never do):

* ``?event=YEAR:SERIES``      -- the field of one edition (every entrant, missed cuts included), e.g. a college
                                 championship, a qualifying school or a major;
* ``?tour=KEY&year=YEAR``     -- the golfers on one tour that season (their season row's tour), e.g. a college
                                 division's class;
* ``?turned_pro=YEAR``        -- everyone who turned professional that year;
* ``?born=YEAR[&nation=XX]``  -- an age group (optionally one nation's).

For each member it shows where they were then and what is recorded since: the seasons they played, wins (any
event, at any level), majors, the best season-end world ranking, the highest level they played, prize money,
the Recorded Peak Overall, and where they are now -- including the unsuccessful, the retired and those on lower
tours, never only the stars. Everything is read from the history (and the current season's snapshot): nothing
is estimated, and what is not recorded is shown as not recorded.
"""
from __future__ import annotations

from collections import defaultdict
from urllib.parse import quote, urlencode

FEATURED = ('COLLEGE_NATIONAL_CHAMPIONSHIP', 'SMALL_COLLEGE_CHAMPIONSHIP', 'INTL_UNIVERSITY_CHAMPIONSHIP',
            'AM_NORTH_AMERICA_CHAMPIONSHIP', 'AM_EUROPE_CHAMPIONSHIP', 'AM_ASIA_CHAMPIONSHIP',
            'AM_OCEANIA_CHAMPIONSHIP', 'AM_AFRICA_CHAMPIONSHIP', 'AM_LATAM_CHAMPIONSHIP', 'BRITANNIA_AMATEUR',
            'USA_AMATEUR', 'EUROPEAN_AMATEUR', 'ASIA_PACIFIC_AMATEUR')
NOW_KINDS = (('premier', 'On a Premier tour'), ('tour', 'On another professional tour'),
             ('amateur', 'Amateur or college'), ('club', 'Club professional'), ('retired', 'Retired'),
             ('gone', 'No longer recorded'))
SORTS = ('then', 'name', 'age', 'now', 'last', 'seasons', 'wins', 'majors', 'best_wr', 'level', 'prize', 'peak')
MORE_FIRST = ('last', 'seasons', 'wins', 'majors', 'prize', 'peak')


def _o():
    import observer as O
    return O


# ---- who is in the cohort -------------------------------------------------------------------------------------------
def members(w, q):
    """(title, description, year, {pid: then}) for the cohort a query names, or None if it names none. `then`
    holds what is known of each member at the cohort's moment: {'text', 'sort'}."""
    O = _o()
    eid = O.one(q, 'event')
    if eid:
        e = w.edition(eid)
        if e is None:
            return None
        out = {}
        for r in e['rows']:
            pos = r.get('pos')
            route = r.get('route') or ''
            text = ('MC' if pos is None else str(pos)) + (f' · {route.lower()}' if route else '')
            out[r['person']] = {'text': text, 'sort': (1 if pos is None else 0, pos or 0)}
        name = f'{e["year"]} {w.series_name(e["series"])}'
        return (f'Where are they now: the {name} field',
                f'Every entrant of the <a href="/event/{quote(eid)}">{O.esc(name)}</a> (week {e.get("week")}), missed '
                'cuts included.',
                e['year'], out)
    tour, year = O.one(q, 'tour'), O.one(q, 'year')
    if tour and year and year.isdigit():
        y = int(year)
        rows = _season_rows_of(w, y, tour=tour)
        tname = w.tours().get(tour, {}).get('name', tour)
        out = {pid: {'text': f'{r.get("status") or ""} · {r.get("events") or 0} starts', 'sort': (0, -(r.get('events') or 0)),
                     } for pid, r in rows.items() if r.get('status') is not None}
        return (f'Where are they now: {tname}, {y}', f'Every golfer on the {O.esc(tname)} in {y} (their season’s tour).',
                y, out)
    tp = O.one(q, 'turned_pro')
    if tp and tp.isdigit():
        y = int(tp)
        that = _season_rows_of(w, y)
        out = {pid: _then(w, that.get(pid)) for pid, g in _golfers(w) if g.get('turned_pro') == y}
        return (f'Where are they now: turned professional in {y}', f'Every golfer who turned professional in {y}.',
                y, out)
    born = O.one(q, 'born')
    if born and born.isdigit():
        y, nation = int(born), (O.one(q, 'nation') or '').upper()
        first = min(w.a.years) if w.a else (w.live.cursor['year'] if w.live else y)
        at = max(first, y + 18)                                         # (their first recorded adult season)
        that = _season_rows_of(w, at)
        out = {pid: _then(w, that.get(pid)) for pid, g in _golfers(w)
               if (w.person(pid) or {}).get('born') == y and (not nation or (w.person(pid) or {}).get('country') == nation)}
        return (f'Where are they now: born in {y}' + (f' ({nation})' if nation else ''),
                f'Every golfer born in {y}' + (f' from {O.esc(nation)}' if nation else '')
                + f' (then: their season {at}, the year they turned 18 or the first recorded).', at, out)
    return None


def _golfers(w):
    """(pid, golfer record) for every golfer in the history and the current season."""
    seen = set()
    if w.live is not None:
        for pid, p in w.live.people.items():
            if p.get('status') is not None:
                seen.add(pid)
                yield pid, {'turned_pro': p.get('turned_pro'), 'status': p.get('status')}
    if w.a:
        for pid, p in w.a.people.items():
            if pid not in seen and 'golfer' in p:
                yield pid, p['golfer']


def _then(w, row):
    """A member's season at the cohort's moment: status and tour (or not recorded that season)."""
    if not row:
        return {'text': 'not recorded that season', 'sort': (9, '')}
    t = w.tours().get(row.get('tour'), {})
    return {'text': f'{row.get("status") or ""} · {t.get("name", row.get("tour") or "no tour")}',
            'sort': (t.get('tier', 9), t.get('name', ''))}


def _season_rows_of(w, y, tour=None):
    """{pid: season row} of season y (archived: the index or the season file; the current season: the snapshot)."""
    if w.live is not None and y == w.live.cursor['year'] and (not w.a or y not in w.a.years):
        out = {}
        for pid, p in w.live.people.items():
            if p.get('status') is None or (tour and p.get('tour') != tour):
                continue
            out[pid] = {'tour': p.get('tour'), 'status': p.get('status'), 'lifestyle': p.get('lifestyle'),
                        'events': len(w.live.results(pid))}
        return out
    if not w.a or y not in w.a.years:
        return {}
    idx = w.a.index
    if idx is not None:
        sql = 'SELECT person, tour, status, lifestyle, events, wins, prize, wr_end FROM seasons WHERE year = ?'
        args = [y]
        if tour:
            sql, args = sql + ' AND tour = ?', args + [tour]
        return {r[0]: dict(zip(('tour', 'status', 'lifestyle', 'events', 'wins', 'prize', 'wr_end'), r[1:]))
                for r in idx.db.execute(sql + idx.upto(), args)}
    return {pid: r for pid, r in w.a.year(y)['careers'].items() if not tour or r.get('tour') == tour}


# ---- what became of them -------------------------------------------------------------------------------------------
def follow(w, pids, since):
    """{pid: {...}}: each member's recorded seasons from `since` (that season included) to now."""
    import observer_history as OH
    pids = list(pids)
    seasons = defaultdict(list)
    if w.a:
        idx = w.a.index
        if idx is not None:
            for i in range(0, len(pids), 500):
                chunk = pids[i:i + 500]
                for r in idx.db.execute(
                        'SELECT person, year, tour, status, lifestyle, events, wins, prize, wr_end FROM seasons WHERE '
                        f'person IN ({",".join("?" * len(chunk))}) AND year >= ?' + idx.upto() + ' ORDER BY year',
                        chunk + [since]):
                    seasons[r[0]].append(dict(zip(('year', 'tour', 'status', 'lifestyle', 'events', 'wins', 'prize',
                                                   'wr_end'), r[1:])))
        else:
            want = set(pids)
            for y in w.a.years:
                if y >= since:
                    for pid, r in w.a.year(y)['careers'].items():
                        if pid in want:
                            seasons[pid].append({**r, 'year': y})
    import observer_data as OD
    peaks = OD.recorded_peaks(w, pids)                 # (the profile's Recorded Peak, for each member)
    majors = defaultdict(int)
    for y, wk, eid, sid, win in OH.major_wins(w):
        if y >= since:
            majors[win] += 1
    tours = w.tours()
    cur = w.live.cursor['year'] if w.live else None
    if w.a and cur in w.a.years:                       # (the season is archived: counted once, from its rows)
        cur = None
    out = {}
    for pid in pids:
        rows = seasons.get(pid, [])
        live = w.live.people.get(pid) if w.live else None
        live_starts = w.live.results(pid) if (w.live and cur is not None and cur >= since) else []
        played = [r for r in rows if r.get('events')]
        wins = sum(r.get('wins') or 0 for r in rows)
        wins += sum(1 for r in live_starts if r['pos'] == 1
                    and (w.edition(r['event']) or {}).get('category') not in ('qualifier', 'q_school'))
        prize = sum(r.get('prize') or 0 for r in rows)
        prize_known = all(r.get('prize') is not None for r in played)     # (a season that did not record it)
        if live_starts:                                # the current season so far (a golfer with no ledger this
            prize += w.live.prize.get(pid, 0.0)        # season has been paid nothing: the archive records 0 too)
        best = min((r['wr_end'] for r in rows if r.get('wr_end')), default=None)
        levels = [(tours.get(r.get('tour'), {}).get('tier', 9), r.get('tour')) for r in played
                  if r.get('status') in ('pro', 'club_pro')]
        level = min(levels) if levels else None
        last = max([r['year'] for r in played] + ([cur] if live_starts else []), default=None)
        kind, text = _now(w, pid, live, last)
        p = w.person(pid) or {}
        out[pid] = {'seasons': len(played) + (1 if live_starts and cur not in {r['year'] for r in played} else 0),
                    'wins': wins, 'majors': majors.get(pid, 0), 'best_wr': best, 'prize': prize, 'prize_known': prize_known,
                    'level': level, 'last': last, 'now': kind, 'now_text': text, 'peak': peaks.get(pid),
                    'born': p.get('born'), 'country': p.get('country')}
    return out


def _now(w, pid, live, last_played):
    """(kind, text): where a member is now -- the current season's snapshot; for a history alone, the status the
    history last recorded for them (as of its latest season)."""
    tours = w.tours()
    src = live if live is not None else ((w.a.people.get(pid) or {}).get('golfer') if w.a else None)
    if src is None:
        return 'gone', 'No longer recorded' + (f' (last played {last_played})' if last_played else '')
    status, lifestyle, tour = src.get('status'), src.get('lifestyle'), src.get('tour')
    tname = tours.get(tour, {}).get('name', tour.replace('_', ' ').title() if tour else '')
    as_of = '' if live is not None else f' (as of {w.a.years[-1]})'
    if lifestyle == 'retired' or status == 'retired':
        return 'retired', 'Retired' + (f' (last played {last_played})' if last_played else '') + as_of
    if status == 'club_pro':
        return 'club', 'Club professional' + (f' · {tname}' if tname else '') + as_of
    if status == 'amateur':
        return 'amateur', 'Amateur' + (f' · {tname}' if tname else '') + as_of
    tier = tours.get(tour, {}).get('tier', 9)
    part = ' (part-time)' if lifestyle == 'part_time' else ''
    return ('premier' if tier == 1 else 'tour'), (tname or 'Professional, no tour') + part + as_of


# ---- the page ------------------------------------------------------------------------------------------------------
def cohort_page(w, q):
    O = _o()
    got = members(w, q)
    if got is None:
        return 'Where are they now', index(w, q)
    title, desc, year, then = got
    if not then:
        return title, f'<p>{desc}</p><p class="muted">Nobody recorded.</p>' + _back()
    fol = follow(w, then, year)
    sort = O.one(q, 'sort', 'then' if O.one(q, 'event') else 'level')
    sort = sort if sort in SORTS else 'then'
    desc_ = (O.one(q, 'dir', '') or ('desc' if sort in MORE_FIRST else 'asc')) == 'desc'
    tiers = {k: t.get('tier', 9) for k, t in w.tours().items()}
    nowrank = {k: i for i, (k, _) in enumerate(NOW_KINDS)}
    def key(pid):
        f = fol[pid]
        if sort == 'then':
            v = then[pid]['sort']
        elif sort == 'name':
            v = w.name(pid)
        elif sort == 'age':
            v = (year - f['born']) if f['born'] else None
        elif sort == 'now':
            v = (nowrank[f['now']], f['now_text'])
        elif sort == 'level':
            v = f['level']
        elif sort == 'best_wr':
            v = f['best_wr']
        elif sort == 'peak':
            v = f['peak'][0] if f['peak'] else None
        else:
            v = f.get(sort)
        return v
    pids = sorted(then, key=lambda p: (w.name(p), p))
    known = sorted((p for p in pids if key(p) is not None), key=key, reverse=desc_)
    rows = known + [p for p in pids if key(p) is None]
    chunk, pager = O.paged(rows, q, '/cohort')
    keep = {k: v[0] for k, v in q.items() if k not in ('sort', 'dir', 'page') and v and v[0]}

    def th(k, label, n=False):
        """Sorts by the column (most first for counts, money, peak and last season; otherwise ascending); the
        active heading turns the order around."""
        on = k == sort
        first = 'desc' if k in MORE_FIRST else 'asc'
        nxt = ('asc' if desc_ else 'desc') if on else first
        args = {**keep, 'sort': k, **({'dir': nxt} if nxt != first else {})}
        mark = (' ▼' if desc_ else ' ▲') if on else ''
        return f'<th{" class=n" if n else ""}><a href="/cohort?{urlencode(args)}">{O.esc(label)}{mark}</a></th>'
    head = ('<tr>' + th('name', 'Golfer') + '<th>Nation</th>' + th('then', 'Then') + th('age', 'Age then', True)
            + th('now', 'Now') + th('last', 'Last season', True) + th('seasons', 'Seasons', True)
            + th('wins', 'Wins', True) + th('majors', 'Majors', True) + th('best_wr', 'Best rank', True)
            + th('level', 'Highest level') + th('prize', 'Prize money', True) + th('peak', 'Peak Overall', True) + '</tr>')
    body = []
    for pid in chunk:
        f = fol[pid]
        lvl = f['level']
        body.append(
            f'<tr><td>{w.person_link(pid)}</td><td>{O.nation_link(f["country"])}</td><td>{O.esc(then[pid]["text"])}</td>'
            f'<td class="n">{(year - f["born"]) if f["born"] else "—"}</td><td>{O.esc(f["now_text"])}</td>'
            f'<td class="n">{f["last"] or "—"}</td><td class="n">{f["seasons"]}</td>'
            f'<td class="n">{O.results_link(pid, str(f["wins"]), outcome="win") if f["wins"] else "0"}</td>'
            f'<td class="n">{f["majors"]}</td><td class="n">{f["best_wr"] or "—"}</td>'
            f'<td>{O.tour_link(w, lvl[1]) if lvl else "<span class=muted>none as a professional</span>"}</td>'
            f'<td class="n">{O.money(f["prize"])}'
            + ('' if f['prize_known'] else ' <span class="muted">(partial: a season did not record it)</span>') + '</td>'
            f'<td class="n">{_peak(f["peak"])}</td></tr>')
    counts = defaultdict(int)
    for pid in then:
        counts[fol[pid]['now']] += 1
    summary = ' · '.join(f'{label}: {counts[k]}' for k, label in NOW_KINDS if counts[k])
    reached = sum(1 for p in then if fol[p]['level'] and tiers.get(fol[p]['level'][1]) == 1)
    winners = sum(1 for p in then if fol[p]['wins'])
    champs = sum(1 for p in then if fol[p]['majors'])
    return title, (f'<p>{desc} {len(then):,} people. From {year} on (that season included).</p>'
                   + f'<p><strong>Now</strong>: {summary}.<br>Played a Premier tour as a professional: {reached} · won '
                     f'anything since: {winners} · major champions since: {champs}.</p>'
                   + f'<div class="scroll"><table>{head}{"".join(body)}</table></div>' + pager
                   + '<p class="muted">Then: at the cohort’s moment (an entrant’s finish and entry route; a tour '
                     'cohort’s status and starts that season). Seasons: seasons with at least one start, from the '
                     'cohort’s season on. Wins: events won at any level (college and amateur events included); '
                     'Majors: major championships won. Best rank: the best season-end world ranking. Highest level: '
                     'the highest tour they played as a professional. Prize money: as recorded each season. Peak '
                     'Overall: the Recorded Peak Overall and the season it was reached (unavailable where it was not '
                     'recorded). Now: the current season’s status (for a history alone, the status it last recorded, as of its latest season).</p>' + _back())


def _peak(pk):
    return f'{pk[0]:.1f} ({pk[1]})' if pk else '<span class="muted">not recorded</span>'


def _back():
    return '<p><a href="/cohort">Other fields and cohorts</a></p>'


def index(w, q):
    """Pick a field or cohort: featured championships by season, a tour and season, a turning-pro class, an age group."""
    O = _o()
    years = sorted(set(w.a.years if w.a else []) | ({w.live.cursor['year']} if w.live else set()), reverse=True)
    out = ['<p>Follow a field or a cohort through the rest of their careers: the unsuccessful, the retired and '
           'those on lower tours as well as the stars.</p>']
    rows = []
    for sid in FEATURED:
        eds = [e for e in (w.editions_of(sid) or []) if e.get('event')]
        if eds:
            links = ' '.join(f'<a href="/cohort?event={quote(e["event"])}">{e["year"]}</a>' for e in reversed(eds[-12:]))
            rows.append([f'<a href="/series/{quote(sid)}">{O.esc(w.series_name(sid))}</a>', links])
    if rows:
        out.append('<h2>Championship fields</h2>' + O.table(['Championship', 'Season (latest first)'], rows)
                   + '<p class="muted">Any edition: its event page links to its field’s careers.</p>')
    yopts = [(str(y), str(y)) for y in years]
    tours = sorted(w.tours().items(), key=lambda x: (x[1].get('tier', 9), x[1].get('name', x[0])))
    out.append('<h2>A tour’s golfers in a season</h2>' + O.filters('/cohort', q, [
        ('tour', 'Tour', [(k, t.get('name', k)) for k, t in tours]), ('year', 'Season', yopts)]))
    out.append('<h2>Turned professional in</h2>' + O.filters('/cohort', q, [('turned_pro', 'Year', yopts)]))
    out.append('<h2>Born in</h2>' + O.filters('/cohort', q, [('born', 'Year', None), ('nation', 'Nation (code)', None)]))
    return ''.join(out)
