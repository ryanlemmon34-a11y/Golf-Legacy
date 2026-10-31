"""Observer: five-year prestige of tournaments, courses and nations, and nations' shares of the new-golfer cohorts
(rules 2026-11-05; golfsim/prestige.py and golfsim/participation.py).

Read-only. Every value comes from a season file's `prestige` record (seasons archived under rules 2026-11-05 or
later) or from the committed world's snapshot (`LiveView.prestige`); a season without the record is shown as
"not recorded", never filled from another season.

Dating: an event's prestige is shown as it stood at the end of each season (after that season's edition) and
now; a course's and a nation's as set at the end of a season FOR the next one (a course's prestige and a
nation's shares are lagged: the bar for season Y was decided when season Y-1 ended).
"""
from __future__ import annotations

import html

import observer_data as OD

PATHWAY_LABELS = {'juniors': 'juniors (18)', 'new_pros': 'new professionals (21-26)'}


def esc(x):
    return html.escape('' if x is None else str(x))


def _record(w, y):
    return OD.season_extract(w, y, 'prestige', lambda d: d.get('prestige'))


def _years(w):
    return sorted(w.a.years) if w.a is not None else []


def _live(w):
    return getattr(w.live, 'prestige', None) if w.live is not None else None


def latest(w):
    """{'events', 'courses', 'nations'}: the newest values known (the live world's, else the last archived
    season's record), or None."""
    lv = _live(w)
    if lv:
        return lv
    for y in reversed(_years(w)):
        r = _record(w, y)
        if r:
            n = r.get('nations', {})
            return {'events': r.get('events', {}), 'courses': r.get('courses', {}),
                    'nations': {'prestige': n.get('prestige', {}), 'multiplier': n.get('multiplier', {}),
                                'shares': n.get('shares', {}), 'baseline_shares': n.get('baseline_shares', {})}}
    return None


def cell(v, digits=1):
    """A table cell's text for a prestige value (missing: an empty cell, which sorts last)."""
    return '' if v is None else f'{v:.{digits}f}'


def pct(v, digits=2):
    return '' if v is None else f'{100 * v:.{digits}f}%'


def bars(points, unit='', digits=1, top=None, note=''):
    """Fixed-width dated bars (the observer's ratings chart style): points [(label, value or None, tip)]."""
    vals = [v for _, v, _ in points if v is not None]
    if not vals:
        return '<p class="muted">Not recorded yet: prestige is recorded from rules 2026-11-05, when a season ends.</p>'
    top = top or max(vals) or 1.0
    out = []
    for label, v, tip in points:
        if v is None:
            out.append(f'<div class="rbar gap" title="{esc(label)}: not recorded"><span class="rv">—</span>'
                       f'<span class="rb"></span><span class="ry">{esc(label)}</span></div>')
            continue
        h = max(2, round(150 * v / top))
        now = ' now' if label.startswith('now') else ''
        shown = f'{v:.{digits}f}{unit}'
        out.append(f'<div class="rbar{now}" title="{esc(tip)}"><span class="rv">{shown}</span>'
                   f'<span class="rb lv" style="height:{h}px"></span><span class="ry">{esc(label)}</span></div>')
    return (f'<div class="scroll"><div class="rchart">{"".join(out)}</div></div>'
            + (f'<p class="muted">{note}</p>' if note else ''))


def _series(w, pick, lag):
    """[(label, value or None, tip)] over the archived seasons (lag 1: the value belongs to the next season)."""
    pts = []
    for y in _years(w):
        r = _record(w, y)
        v = pick(r) if r else None
        when = y + lag
        tip = (f'{when}: set at the end of {y}' if lag else f'end of {y}')
        pts.append((str(when), v, f'{tip}: {v:.2f}' if v is not None else tip))
    return pts


def event_section(w, sid):
    pts = _series(w, lambda r: r.get('events', {}).get(sid), 0)
    lv = _live(w)
    if lv and sid in lv.get('events', {}):
        c = w.live.cursor
        v = lv['events'][sid]
        pts.append((f'now', v, f'now ({c["year"]}, week {c["week"]}): {v:.2f}'))
    return ('<h2>Prestige over time</h2>'
            + bars(pts, note='One bar per season: the event’s prestige at the end of that season (after its edition, '
                             'carried into the next), then now. Five calendar years, recency-weighted, moving at most '
                             '6 points a year (rules: event prestige). “—”: not recorded.'))


def course_section(w, cid):
    pts = _series(w, lambda r: r.get('courses', {}).get(cid), 1)
    lv = _live(w)
    if lv and cid in lv.get('courses', {}) and w.live.cursor['year'] not in {int(p[0]) for p in pts}:
        v = lv['courses'][cid]
        pts.append((f'now {w.live.cursor["year"]}', v, f'this season ({w.live.cursor["year"]}): {v:.2f}'))
    return ('<h2>Prestige over time</h2>'
            + bars(pts, note='One bar per season: the course’s prestige for that season, set when the season before it '
                             'ended, from the events it hosted in the five completed seasons before (a lag: what it '
                             'hosts counts from the next season). Separate from its class and layouts, which are its '
                             'physical quality. “—”: not recorded.'))


def nation_section(w, code):
    out = ['<h2>Prestige and share of new golfers</h2>']
    lv = _live(w)
    archived = _years(w)
    rows = []
    for y in archived:
        r = _record(w, y)
        n = (r or {}).get('nations') or {}
        if not n.get('prestige'):
            rows.append((y + 1, None))
            continue
        rows.append((y + 1, n))
    if lv and (lv.get('nations') or {}).get('closed') is not None:
        nv = lv['nations']
        if nv['closed'] + 1 not in {y for y, _ in rows}:
            rows.append((nv['closed'] + 1, {'prestige': nv['prestige'], 'multiplier': nv['multiplier'],
                                            'shares': nv['shares'], 'baseline_shares': nv['baseline_shares']}))
    base = None
    for _, n in rows:
        if n and n.get('baseline_shares'):
            base = n['baseline_shares']
    if base is None and lv:
        base = (lv.get('nations') or {}).get('baseline_shares')
    if base:
        out.append('<p>Starting share of new golfers: ' + ' · '.join(
            f'{esc(PATHWAY_LABELS[k])} {pct(base.get(k, {}).get(code), 3)}' for k in ('juniors', 'new_pros'))
            + ' <span class="muted">(its expected share under the rule that sets each year’s numbers, fixed when the '
              'world began)</span></p>')
    get = lambda n, k: n.get(k, {}).get(code) if n else None

    def share(n, kind='juniors'):
        v = ((n or {}).get('shares') or {}).get(kind, {}).get(code)
        return None if v is None else 100 * v
    out.append('<h3>National prestige</h3>' + bars(
        [(str(y), get(n, 'prestige'), f'for {y} (set at the end of {y - 1}): prestige {get(n, "prestige")}') for y, n in rows],
        top=100, note='50 = exactly the success expected of its golfers before each event; 75 = twice that, 25 = half '
                      '(five completed seasons, steadied for small samples).'))
    sh = [(str(y), share(n), f'{y} (set at the end of {y - 1}): {share(n)}% of the juniors') for y, n in rows]
    out.append('<h3>Share of each year’s juniors</h3>' + bars(sh, unit='%', digits=2,
                                                              note='The nation’s share of the year’s fixed number of new '
                                                                   'juniors (the number itself never depends on prestige).'))
    trs = []
    for y, n in reversed(rows):
        if not n:
            trs.append([str(y)] + ['<span class="muted">not recorded</span>'] + [''] * 5)
            continue
        alloc = n.get('allocated') or {}
        trs.append([str(y), cell(get(n, 'prestige')), cell(get(n, 'multiplier'), 3),
                    pct(None if share(n) is None else share(n) / 100),
                    pct(None if share(n, 'new_pros') is None else share(n, 'new_pros') / 100),
                    esc(alloc.get('juniors', {}).get(code, '')), esc(alloc.get('new_pros', {}).get(code, ''))])
    if trs:
        h = ['Entrant season', 'Prestige', 'Multiplier', 'Share of juniors', 'Share of new pros', 'Juniors', 'New pros']
        out.append('<div class="scroll"><table class="sortable"><thead><tr>'
                   + ''.join(f'<th{" class=n" if i else ""} title="Sort by this column">{esc(x)}</th>' for i, x in enumerate(h))
                   + '</tr></thead><tbody>'
                   + ''.join('<tr>' + ''.join(f'<td{" class=n" if i else ""}>{c}</td>' for i, c in enumerate(r)) + '</tr>'
                             for r in trs) + '</tbody></table></div>')
    out.append('<p class="muted">Each entrant season’s shares were set when the season before it ended, from national '
               'prestige; Juniors and New pros are the golfers the nation actually received that season (the totals '
               'come from the unchanged cohort rule; rules: national prestige and shares of new golfers). Nationality '
               'never changes: shares affect future entrants only.</p>')
    return ''.join(out)
