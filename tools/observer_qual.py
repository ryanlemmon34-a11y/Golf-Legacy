"""Qualification for this season's majors as it stands: earned and conditional places, places still pending a
published list, places still to be decided by qualifying, and -- for information only -- who would be inside a
pending ranking or points cut-off if the list were published now.

`standing(season, year, week)` is worked out when the observer captures a committed week (read only: it applies
the majors' own rules, `golfsim.qualification`, to the facts known before `week`, and changes nothing). A place
decided by a ranking or points list is earned only once that list is published (the end of its cut-off week);
until then it is pending and any projection is labelled as such: the engine never uses a projection, so it never
takes anyone's qualifying attempt away. The classic calendar (v1) and the reference calendar (v2) are read the
same way.
"""
from __future__ import annotations

import re
from urllib.parse import quote

LIST_SOURCES = ('ranking', 'points')


def _n_of(route):
    """How many places a ranking or points route gives (from its label: 'World top 60', 'Top 70, ...')."""
    m = re.search(r'top (\d+)', route.label, re.I)
    return int(m.group(1)) if m else None


def standing(s, year, week):
    """{major: {...}} for each of `year`'s majors whose field is not set yet (see the module note)."""
    from golfsim import qualification as Q
    view = s.ctx.as_of(year, week)
    out = {}
    log = getattr(s, 'stage_log', {})                      # (a save from before stage logs: none recorded)
    for major, rules in Q.rules_for(getattr(s, 'calendar_version', 'v1')).items():
        if (year, major, 'field') in log:
            continue                                        # the field is set: the rights ledger tells the story
        earned, pending, stages, fills = {}, [], [], []
        for route in rules:
            src = route.source[0] if route.source else None
            if route.kind == 'fill':
                fills.append(route.code)
                continue
            if route.kind == 'qualifying':
                continue
            if route.cutoff:
                if src is None or src[0] not in LIST_SOURCES:
                    pending.append({'code': route.code, 'list': 'list', 'week': None, 'year': year,
                                    'n': _n_of(route)})
                    continue
                at = (year + src[2], src[1])
                if at >= (year, week):                     # not published before this week
                    pending.append({'code': route.code, 'list': src[0], 'week': src[1], 'year': at[0],
                                    'n': _n_of(route)})
                    continue
            try:
                ids = route.select(view, year)
            except Q.FutureSnapshot:
                pending.append({'code': route.code, 'list': src[0] if src else 'list', 'week': src[1] if src else None,
                                'year': year, 'n': _n_of(route)})
                continue
            for gid in ids:
                if Q._eligible(view, gid, route, year):
                    earned.setdefault(gid, {'codes': [], 'amateur': True})
                    if route.code not in earned[gid]['codes']:
                        earned[gid]['codes'].append(route.code)
                        earned[gid]['amateur'] &= route.amateur_only
        in_field = set(earned)
        for route in rules:                                  # qualifying events: played (places allocated) or to come
            if route.kind != 'qualifying':
                continue
            eds = [x for x in route.source if x[0] not in ('wins', 'standing', 'ranking', 'points', 'award')]
            if eds and Q._complete(route, view, year):
                try:
                    groups = route.select(view, year)
                except Q.FutureSnapshot:
                    continue
                if groups and isinstance(groups[0], int):
                    groups = [groups]
                per = route.site_spots or (route.spots,) * len(groups)
                for i, group in enumerate(groups):
                    spots, taken = (per[i] if i < len(per) else per[-1]), 0
                    for gid in group:
                        if taken >= spots:
                            break
                        if gid in in_field or not Q._eligible(view, gid, route, year):
                            continue
                        earned[gid] = {'codes': [route.code], 'amateur': route.amateur_only}
                        in_field.add(gid)
                        taken += 1
            else:
                stages.append({'code': route.code, 'spots': route.spots or sum(route.site_spots) or None,
                               'events': [(sid, year + off, s.ctx.edition_week(sid, year + off)) for sid, off in eds]})
        projected = {}
        for p in pending:
            if not p['n'] or p['list'] not in LIST_SOURCES or p['year'] != year:
                continue
            if p['list'] == 'ranking':
                now = [g for g, _ in sorted(s.wr_pos.items(), key=lambda x: x[1])]
            else:
                route = next(r for r in rules if r.code == p['code'])   # (the only points list: Americas)
                now = s.ctx.standing('PT_AMERICAS', year, week - 1) if 'Americas' in route.label else []
            projected[p['code']] = [(g, i + 1) for i, g in enumerate(now[:p['n']]) if g not in earned]
        out[major] = {'week': week, 'earned': earned, 'pending': pending, 'stages': stages, 'fills': fills,
                      'projected': projected}
    return out


# ---- the page -------------------------------------------------------------------------------------------------------
def _o():
    import observer as O
    return O


def qualification_page(w, q):
    O = _o()
    import observer_history as OH
    import observer_spoilers as SP
    from golfsim import qualification as Q
    from golfsim import rules as R
    import golfsim.schedule as SCH
    v = w.calendar_version
    sp = SCH.spec(v)
    rules = Q.rules_for(v)
    cur = w.live.cursor if w.live else None
    year = int(O.one(q, 'year') or (cur['year'] if cur else (w.a.years[-1] if w.a else 0)))
    qual = getattr(w.live, 'qual', None) if (w.live and cur and year == cur['year']) else None
    upcoming = [m for m in rules if qual and m in qual]
    major = O.one(q, 'major') or (upcoming[0] if upcoming else next(iter(rules)))
    if major not in rules:
        return 'Qualification', '<p class="muted">No such major.</p>'
    name = w.series_name(major)
    tabs = '<div class="tabs">' + ''.join(
        f'<a href="/qualification?major={quote(m)}&amp;year={year}" class="{"on" if m == major else ""}">'
        f'{O.esc(w.series_name(m))}</a>' for m in rules) + '</div>'
    eid = f'{year}:{major}'
    played = w.edition(eid) is not None
    out = [tabs, f'<p>The {year} {O.esc(name)}: week {sp.majors.get(major)} · '
                 + (f'<a href="/event/{quote(eid)}">played</a>' if played else 'not played yet')
                 + f' · calendar {O.esc(v)} · <a href="/rules#{quote(major)}">its categories</a> · '
                 '<a href="/standings">when lists lock and rights take effect</a></p>']
    st = (qual or {}).get(major)
    labels = {r.code: r.label for r in rules[major]}
    if st is None:
        out.append('<p class="muted">' + ('Its field is set: the qualification ledger below records every place and '
                                          'how it ended.' if played or (cur and year <= cur['year']) else
                                          'Not this season: places for it are shown once its season is being played '
                                          '(places already earned for it are in the ledger below).') + '</p>')
        out.append(OH.rights_section(w, year, major))
        return f'Qualification: {year} {name}', ''.join(out)
    wk = st['week']
    hide = SP.state(w)['hide']
    this_season = {r.code for r in rules[major] if any((x[0] == 'wins') or (x[0] not in ('standing', 'ranking', 'points', 'award')
                                                                            and len(x) == 2 and x[1] == 0) for x in r.source)}
    held = 0
    rows = []
    for gid, e in sorted(st['earned'].items(), key=lambda kv: (kv[1]['amateur'], [list(labels).index(c) for c in kv[1]['codes']], kv[0])):
        if hide and all(c in this_season for c in e['codes']):
            held += 1                                       # (would name a result of this season)
            continue
        cats = '; '.join(f'{O.esc(labels.get(c, c))} <span class="tag">{O.esc(c)}</span>' for c in e['codes'])
        rows.append([w.person_link(gid), 'conditional (while an amateur)' if e['amateur'] else 'earned', cats])
    out.append(f'<h2>Earned and conditional places, as of week {wk}</h2>'
               + (O.table(['Golfer', 'Place', 'Categories'], rows) if rows else '<p class="muted">None yet.</p>')
               + (f'<p class="muted">Hide results: {held} place{"s" if held != 1 else ""} earned by this season\'s '
                  'results held back.</p>' if held else '')
               + '<p class="muted">Every category whose facts are known before this week, applied by the major\'s own '
                 'rules (one place per golfer however many categories support it). Conditional: an amateur\'s place, '
                 'which lapses on turning professional. A place earned in a qualifying event already played is '
                 'included; one decided by a list not yet published is not.</p>')
    prow = []
    for p in st['pending']:
        when = (f'list published at the end of week {p["week"]}' + (f' of {p["year"]}' if p['year'] != year else '')
                if p['week'] else 'decided when the field is set')
        prow.append([f'{O.esc(labels.get(p["code"], p["code"]))} <span class="tag">{O.esc(p["code"])}</span>',
                     O.esc(p['list']), O.esc(when)])
    for sg in st['stages']:
        evs = ', '.join(f'{O.esc(w.series_name(sid))} {y}' + (f' (week {wkk})' if wkk else '') for sid, y, wkk in sg['events'])
        prow.append([f'{O.esc(labels.get(sg["code"], sg["code"]))} <span class="tag">{O.esc(sg["code"])}</span>',
                     'qualifying' + (f' ({sg["spots"]} places)' if sg['spots'] else ''), evs or 'to be played'])
    for c in st['fills']:
        prow.append([f'{O.esc(labels.get(c, c))} <span class="tag">{O.esc(c)}</span>', 'fill',
                     'places left over, when the field is set'])
    out.append('<h2>Still to be decided</h2>' + O.table(['Category', 'Decided by', 'When'], prow))
    proj = []
    for code, lst in st['projected'].items():
        p = next(x for x in st['pending'] if x['code'] == code)
        for gid, rank in lst:
            if hide:
                continue
            proj.append([w.person_link(gid), str(rank), f'{O.esc(labels.get(code, code))} <span class="tag">{O.esc(code)}</span>',
                         O.esc(f'week {p["week"]}')])
    out.append('<h2>Projected (for information only)</h2><p class="muted"><strong>A projection is not a place.</strong> '
               'These golfers hold no place yet and would be inside a pending cut-off if its list were published now '
               f'(the latest list, after week {wk - 1}). The engine never uses a projection: the place is decided by the '
               'list published at the cut-off, and nobody loses a qualifying attempt because of one.</p>'
               + (O.table(['Golfer', 'Now', 'Cut-off', 'Published'], proj, numeric=(1,)) if proj else
                  '<p class="muted">' + ('Hidden while results are hidden.' if hide and st['projected'] else
                                         'No pending ranking or points cut-off this edition can be projected.') + '</p>'))
    out.append(OH.rights_section(w, year, major))
    return f'Qualification: {year} {name}', SP.aggregate_note(w, 'the rankings and places') + ''.join(out)


_STANDINGS = None


def standings_page(w, q):
    """docs/STANDINGS_AND_RIGHTS.md as a page (worked out from the calendar and card rules, as the document is)."""
    O = _o()
    import html
    import standings_calendar as SC
    global _STANDINGS
    if _STANDINGS is None:                             # (the calendar and card rules cannot change while running)
        _STANDINGS = SC.doc()
    lines, out, table = _STANDINGS.splitlines(), [], []

    def inline(t):
        t = html.escape(t)
        t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
        return re.sub(r'`(.+?)`', r'<code>\1</code>', t)

    def flush():
        if table:
            head, body = table[0], [r for r in table[2:]]
            cells = lambda r: [c.strip() for c in r.strip('|').split('|')]
            out.append(O.table(cells(head), [[inline(c) for c in cells(r)] for r in body]))
            table.clear()
    for line in lines[1:]:
        if line.startswith('|'):
            table.append(line)
            continue
        flush()
        if line.startswith('## '):
            out.append(f'<h2>{inline(line[3:])}</h2>')
        elif line.startswith('- '):
            out.append(f'<p>• {inline(line[2:])}</p>')
        elif line.strip():
            out.append(f'<p>{inline(line)}</p>')
    flush()
    return 'Standings locks and rights', ''.join(out)
