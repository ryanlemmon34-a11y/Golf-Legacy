"""Career comparisons: two to four golfers side by side -- now, their Recorded Peak Overall, career totals, season
by season and at the same age.

Three kinds of rating are kept apart and labelled: the **current** Overall (today's snapshot, for a golfer still
competing), **historical snapshots** (the Overall at the start of each season, recorded when the season before
was archived) and the **Recorded Peak Overall** (the highest Overall recorded, with when and how much of the
career the records cover). Everything else is read from the archived seasons (and the current season so far).
A season or age with nothing recorded says so; nothing is estimated, and a career that began before the world's
records is marked as partial.
"""
from __future__ import annotations

from urllib.parse import urlencode

MAX = 4


def _o():
    import observer as O
    return O


def ids(q):
    O = _o()
    out = []
    for x in (O.one(q, 'ids', '') or '').replace(' ', '').split(','):
        if x.isdigit() and int(x) not in out:
            out.append(int(x))
    return out[:MAX]


def seasons(w, pid):
    """{year: {age, tour, status, starts, wins, top10, majors, prize, wr_end, overall (start of season), source}}:
    archived seasons from the records, and the current season so far from the snapshot."""
    import observer_data as OD
    import observer_history as OH
    p = w.person(pid) or {}
    born = p.get('born')
    snaps = OD.rating_snapshots(w, pid)
    majors = {}                                        # (from the editions, as the Grand Slam page)
    for y, _, _, _, win in OH.major_wins(w):
        if win == pid:
            majors[y] = majors.get(y, 0) + 1
    out = {}
    for y, r in OD.career_rows(w, pid):
        out[y] = {'age': (y - born) if born else None, 'tour': r.get('tour'), 'status': r.get('status'),
                  'starts': r.get('events'), 'wins': r.get('wins'), 'top10': r.get('top10'), 'majors': majors.get(y, 0),
                  'prize': r.get('prize'), 'wr_end': r.get('wr_end'), 'overall': (snaps.get(y) or [None])[0],
                  'source': 'archived'}
    if w.live is not None:
        y = w.live.cursor['year']
        lp = w.live.people.get(pid)
        res = w.live.results(pid)
        if lp is not None and (res or lp.get('lifestyle') != 'retired'):
            cat = lambda r: (w.edition(r['event']) or {}).get('category')
            out[y] = {'age': (y - born) if born else None, 'tour': lp.get('tour'), 'status': lp.get('status'),
                      'starts': len(res), 'wins': sum(1 for r in res if r['pos'] == 1 and cat(r) not in ('qualifier', 'q_school')),
                      'top10': sum(1 for r in res if r['pos'] is not None and r['pos'] <= 10),
                      'majors': majors.get(y, 0),
                      'prize': w.live.prize.get(pid, 0.0), 'wr_end': None, 'overall': (snaps.get(y) or [None])[0],
                      'source': 'so far'}
    return out


def _cell(s, w):
    O = _o()
    if s is None:
        return '<span class="muted">not recorded</span>'
    tours = w.tours()
    t = tours.get(s.get('tour'), {}).get('name', s.get('tour') or 'no tour')
    bits = [f'{O.esc(t)} ({O.esc(s.get("status") or "?")})']
    if s.get('starts') is not None:
        bits.append(f'{s["starts"]} starts, {s.get("wins") or 0} wins' + (f', {s["majors"]} major' + ('s' if s['majors'] != 1 else '')
                                                                         if s.get('majors') else ''))
    if s.get('prize') is not None:
        bits.append(O.money(s['prize']))
    bits.append(f'world No. {s["wr_end"]} at season end' if s.get('wr_end') else
                ('season in progress' if s.get('source') == 'so far' else 'unranked at season end'))
    bits.append(f'Overall {s["overall"]:.1f} at the start' if s.get('overall') is not None
                else '<span class="muted">Overall at the start: not recorded</span>')
    return '<br>'.join(bits)


def totals(w, pid, ss):
    """Career totals over the recorded seasons (and the current season so far)."""
    played = {y: s for y, s in ss.items() if s.get('starts')}
    t = {'seasons': len(played), 'starts': sum(s.get('starts') or 0 for s in ss.values()),
         'wins': sum(s.get('wins') or 0 for s in ss.values()),
         'majors': sum(s.get('majors') or 0 for s in ss.values()),
         'top10': sum(s.get('top10') or 0 for s in ss.values() if s.get('top10') is not None),
         'top10_seasons': sum(1 for s in ss.values() if s.get('top10') is not None),
         'prize': sum(s.get('prize') or 0 for s in ss.values()),
         'best_wr': min((s['wr_end'] for s in ss.values() if s.get('wr_end')), default=None),
         'first': min(ss) if ss else None, 'last': max(played) if played else None}
    return t


def compare_page(w, q):
    O = _o()
    import observer_data as OD
    pids = [p for p in ids(q) if w.person(p) is not None]
    find = (O.one(q, 'find', '') or '').strip()
    add = _finder(w, pids, find)
    if not pids:
        return 'Compare careers', ('<p>Choose up to four golfers to compare side by side: now, their Recorded Peak '
                                   'Overall, career totals, season by season and at the same age. A profile’s '
                                   '<em>Compare</em> link starts here too.</p>' + add)
    head = ''.join(f'<th>{w.person_link(p)} <a href="/compare?{urlencode({"ids": ",".join(str(x) for x in pids if x != p)})}" '
                   f'title="Remove from the comparison">✕</a></th>' for p in pids)
    data = {p: seasons(w, p) for p in pids}
    tot = {p: totals(w, p, data[p]) for p in pids}
    people = {p: w.person(p) or {} for p in pids}
    y_now = O.now_year(w)

    def row(label, fn, note=''):
        return (f'<tr><th scope="row">{O.esc(label)}' + (f'<br><span class="muted">{O.esc(note)}</span>' if note else '')
                + '</th>' + ''.join(f'<td>{fn(p)}</td>' for p in pids) + '</tr>')

    def current(p):
        lp = w.live.people.get(p, {}) if w.live else {}
        if lp.get('ratings'):
            c = w.live.cursor
            return f'<strong>{lp["ratings"][0]:.1f}</strong> <span class="muted">(now: {c["year"]}, week {c["week"]})</span>'
        snaps = OD.rating_snapshots(w, p)
        if snaps:
            last = max(snaps)
            return (f'<span class="muted">not competing: no current rating (last snapshot {snaps[last][0]:.1f}, start of '
                    f'{last})</span>')
        return '<span class="muted">unavailable</span>'

    def peak(p):
        pk = OD.recorded_peak(w, p)
        if pk is None:
            return '<span class="muted">not recorded</span>'
        yy, wk = pk['year'], pk['week']
        when = ('now' if pk['source'] == 'current' else f'start of {yy}' if wk == 0 else
                f'end of {yy}' if wk >= 52 else f'{yy}, week {wk}')
        born = people[p].get('born')
        label = 'Peak' if pk['complete'] else 'Recorded Peak'
        return (f'<strong>{pk["value"]:.1f}</strong> · {O.esc(when)}' + (f', age {yy - born}*' if born else '')
                + f'<br><span class="muted">{label} Overall'
                + ('' if pk['complete'] else ': the records do not cover the whole career') + '</span>')

    def status(p):
        g = people[p].get('golfer') or {}
        if g.get('lifestyle') == 'retired':
            return f'retired (last season {tot[p]["last"] or "—"})'
        t = w.tours().get(g.get('tour'), {}).get('name', g.get('tour') or 'no tour')
        return O.esc(f'{g.get("status") or "?"} · {t}')

    def cover(p):
        t = tot[p]
        if t['first'] is None:
            return '<span class="muted">no season recorded</span>'
        initial = (w.a.people.get(p) or {}).get('initial') if w.a else False
        return O.esc(f'{t["first"]}–{max(data[p])}' + (' (career began before the world’s records: partial)'
                                                       if initial else ''))
    no1 = _weeks_at_no1(w)
    rows = [
        row('Born', lambda p: f'{people[p].get("born") or "—"} · {O.nation_link(people[p].get("country"))}'),
        row('Now', status),
        row('Current Overall', current, 'today’s snapshot'),
        row('Peak Overall', peak, 'the highest recorded'),
        row('Seasons recorded', cover),
        row('Seasons played', lambda p: str(tot[p]['seasons'])),
        row('Starts', lambda p: f'{tot[p]["starts"]:,}'),
        row('Wins', lambda p: O.results_link(p, str(tot[p]['wins']), outcome='win') if tot[p]['wins'] else '0',
            'any event, any level'),
        row('Majors', lambda p: str(tot[p]['majors'])),
        row('Top 10s', lambda p: str(tot[p]['top10']) if tot[p]['top10_seasons'] == len(data[p]) else
            '<span class="muted">not recorded</span>' if not tot[p]['top10_seasons'] else
            f'{tot[p]["top10"]} <span class="muted">(in the {tot[p]["top10_seasons"]} of {len(data[p])} seasons that '
            'record it)</span>'),
        row('Prize money', lambda p: O.money(tot[p]['prize'])),
        row('Best world ranking', lambda p: f'No. {tot[p]["best_wr"]}' if tot[p]['best_wr'] else '—', 'at a season’s end'),
        row('Weeks at world No. 1', lambda p: (str(no1.get(p, 0)) if no1 is not None else
                                               '<a href="/records/weeks-at-number-one">see Records</a>')),
    ]
    out = [add,
           f'<div class="scroll"><table><thead><tr><th></th>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>']
    years = sorted({y for p in pids for y in data[p]})
    if years:
        out.append('<h2>Season by season</h2><div class="scroll"><table><thead><tr><th>Season</th>' + head
                   + '</tr></thead><tbody>' + ''.join(
                       f'<tr><th scope="row">{y}' + (' <span class="muted">(so far)</span>' if y == y_now and w.live else '')
                       + '</th>' + ''.join(f'<td>' + (f'age {data[p][y]["age"]}*<br>' if y in data[p] and data[p][y]['age'] is not None else '')
                                           + _cell(data[p].get(y), w) + '</td>' for p in pids) + '</tr>'
                       for y in reversed(years)) + '</tbody></table></div>')
    ages = sorted({s['age'] for p in pids for s in data[p].values() if s['age'] is not None})
    if ages:
        by_age = {p: {s['age']: (y, s) for y, s in data[p].items() if s['age'] is not None} for p in pids}
        out.append('<h2>At the same age</h2><div class="scroll"><table><thead><tr><th>Age*</th>' + head
                   + '</tr></thead><tbody>' + ''.join(
                       f'<tr><th scope="row">{a}</th>' + ''.join(
                           '<td>' + (f'{by_age[p][a][0]}<br>' + _cell(by_age[p][a][1], w) if a in by_age[p]
                                     else _before(w, p, a, people[p])) + '</td>' for p in pids) + '</tr>'
                       for a in ages) + '</tbody></table></div>')
    out.append('<p class="muted">Overall in the season and age tables is the historical snapshot at the start of that '
               'season (recorded when the season before was archived): not the current rating and not the peak. '
               'Current Overall: today’s snapshot, only for a golfer still competing. Peak Overall: the highest '
               'recorded, with when (and “Recorded Peak” where the records do not cover the whole career). Seasons '
               'are calendar seasons; the current one counts as far as it has been played. Wins count events at any '
               'level, majors included. ' + O.esc(O.AGE_NOTE) + '</p>')
    return 'Compare careers', ''.join(out)


def _before(w, p, age, person):
    """A same-age cell with no season: before the world's records, after the career, or simply none recorded."""
    born = person.get('born')
    if not born:
        return '<span class="muted">not recorded</span>'
    y = born + age
    first = min(w.a.years) if w.a else (w.live.cursor['year'] if w.live else y)
    if y < first:
        return f'<span class="muted">{y}: before the world’s records</span>'
    return f'<span class="muted">{y}: no season recorded</span>'


def _weeks_at_no1(w):
    """{pid: weeks} when the index answers it in one query; None for an older index (the Records page has it)."""
    a = w.a
    if a is None:
        return {}
    if a.index is not None and a.index.derived_complete(a.years):
        got = w.__dict__.get('_no1')
        if got is None or got[0] != a.stamp:
            got = (a.stamp, a.weeks_at_number_one())
            w._no1 = got
        return got[1]
    return None


def _finder(w, pids, find):
    """The form to add a golfer by name, with the matches (people are told apart by id, nation and birth year)."""
    O = _o()
    form = (f'<form class="filters" action="/compare"><input type="hidden" name="ids" value="{",".join(map(str, pids))}">'
            f'<label>Add a golfer<input name="find" value="{O.esc(find)}" placeholder="name"></label><button>Find</button></form>')
    if not find:
        return form if len(pids) < MAX else '<p class="muted">Four golfers at most: remove one (✕) to add another.</p>'
    low = find.lower()
    seen, hits = set(pids), []
    pools = [((pid, p) for pid, p in w.live.people.items())] if w.live else []
    if w.a:
        pools.append(((pid, p) for pid, p in w.a.people.items() if 'golfer' in p))
    for pool in pools:
        for pid, p in pool:
            if pid not in seen and low in (p.get('name') or '').lower() and (p.get('status') is not None or 'golfer' in p):
                seen.add(pid)
                hits.append(pid)
            if len(hits) >= 25:
                break
    if not hits:
        return form + '<p class="muted">No golfer by that name.</p>'
    return form + '<p>' + ' · '.join(
        f'<a href="/compare?{urlencode({"ids": ",".join(str(x) for x in pids + [h])})}">{O.esc(w.name(h))}, '
        f'born {(w.person(h) or {}).get("born")}</a>' for h in hits) + '</p>'
