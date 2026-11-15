"""Opportunities: which upcoming results unlock something, by the rules the engine actually applies (read only).

`opportunities(season, gid, year, from_week)` lists, for the events still to be played this season, every
implemented route by which a result there leads to a place elsewhere:

* major exemption routes reading an edition's finishers (qualification._rules: e.g. "College national champion
  (last season)" -> next season's Tour Masters; "Top 10 and ties, last USA Open" -> next USA Open), with the required
  finish taken from the route's own selector (`select.need`);
* major qualifying routes and their stages (qualification.stages: local -> final -> USA Open; regional -> final ->
  Britannia Open), with the places the rule gives;
* rule-selected championships fed by a qualifier (event_labels.target: USA Amateur Qualifying -> USA Amateur).

Nothing is predicted: no chance, no threshold a rule does not state. `status` is the golfer's standing now:
'already_qualified' (the target place is already held by a recorded route), 'not_eligible' (a restriction of the
route or the event excludes them now), 'awaiting_selection' (the event picks its own field and has not yet), or
'needs_result'. Eligibility is never admission.
"""
from __future__ import annotations

from . import event_labels as EL
from . import qualification as Q
from .career import entrant_decides


def _ev(season, sid, year):
    s = season.cal.by_id.get(sid)
    if s is None:
        return None
    return {'id': f'{year}:{sid}', 'series_id': sid, 'label': EL.label(season.cal, sid), 'week': s.week, 'year': year}


def _restrictions(route):
    out = []
    if route.amateur_only:
        out.append('amateurs only (the place lapses on turning professional)')
    if route.status:
        out.append({'club_pro': 'club professionals only', 'pro': 'professionals only'}.get(route.status,
                                                                                            f'{route.status} only'))
    if route.max_age:
        out.append(f'aged {route.max_age} or under')
    return out


def _condition(route):
    need = getattr(route.select, 'need', None)
    if need is None:
        return None
    if 'positions' in need:
        pos = list(need['positions'])
        text = ('win' if pos == [1] else 'finish runner-up' if pos == [2]
                else 'finish ' + ' or '.join({1: 'first', 2: 'second'}.get(p, str(p)) for p in pos))
        return {'kind': 'win' if pos == [1] else 'finish', 'text': text, 'positions': pos, 'top': None,
                'places': None, 'site_places': None}
    return {'kind': 'finish', 'text': f'finish in the top {need["top"]} (ties included)', 'positions': None,
            'top': need['top'], 'places': None, 'site_places': None}


# the status a selected / qualifying field is drawn from (Series.eligibility); anything else: 'not eligible' is
# judged by the field's own rule when it is chosen, so it is not ruled out here
_STATUS_FIELDS = {'amateur': ('amateur',), 'mid_amateur': ('amateur',), 'club_pro': ('club_pro',), 'pro': ('pro',),
                  'college': ('amateur',)}


def _may_enter(season, g, s):
    """Whether the golfer can be in this event's field at all, now: the ordinary eligibility rule for an event
    golfers enter (Season.eligible); for a field the event selects, only the status it is drawn from (a college
    post-season: a college team member). Never a claim of admission."""
    if g.lifestyle == 'retired':
        return False
    if not season.is_special(s):
        return season.eligible(g, s, s.week)
    need = _STATUS_FIELDS.get(s.eligibility)
    if need is not None and g.status not in need:
        return False
    if s.eligibility == 'college' and not g.tour.startswith('CO_'):
        return False
    if s.eligibility == 'mid_amateur':
        from .season import MID_AMATEUR_MIN_AGE
        if g.age(season.year) < MID_AMATEUR_MIN_AGE:
            return False
    return True


def _person_ok(season, g, route, target_year):
    if route.amateur_only and g.status != 'amateur':
        return False
    if route.status and g.status != route.status:
        return False
    if route.max_age and g.age(target_year) > route.max_age:
        return False
    return True


def _held(season, gid, year, week):
    """{(major, target year): [route codes]} of places this golfer already holds on recorded facts."""
    ctx = season.ctx
    out = {}
    for g2, rows in Q.secured_places(ctx, year).items():
        if g2 == gid:
            for major, routes, _ in rows:
                out[(major, year + 1)] = [code for code, _, _ in routes]
    view = ctx.as_of(year, week)
    for major in Q.rules_for(ctx.version):
        try:
            got, _ = Q.earned_exemptions(major, year, view)
        except Q.FutureSnapshot:
            continue
        if gid in got:
            out.setdefault((major, year), []).extend(got[gid])
    return out


def opportunities(season, gid, year, from_week):
    """[{event, condition, target, route, status, restrictions, decided}] for golfer `gid` (read only)."""
    g = season.g[gid]
    by = season.cal.by_id
    upcoming = {sid for sid, s in by.items() if s.week >= from_week}
    held = _held(season, gid, year, from_week)
    finals = set(Q.stages(season.ctx.version))
    out = []

    def status(event_sid, route, target, target_year):
        if (target, target_year) in held:
            return 'already_qualified'
        if route is not None and not _person_ok(season, g, route, target_year):
            return 'not_eligible'
        s = by[event_sid]
        if not _may_enter(season, g, s):
            return 'not_eligible'
        if season.is_special(s) and not entrant_decides(s):
            return 'awaiting_selection'              # (the event picks its own field; eligible is not admitted)
        if event_sid in finals:
            return 'awaiting_selection'              # (a final stage: earlier-stage advancers and exempt entries)
        return 'needs_result'

    for major, routes in Q.rules_for(season.ctx.version).items():
        for route in routes:
            for src in route.source:
                if src[0] in ('wins', 'standing', 'ranking', 'points', 'award'):
                    continue
                sid, off = src
                if sid not in upcoming:
                    continue
                cond = _condition(route) if route.kind == 'exempt' else None
                if route.kind == 'exempt' and cond is None:
                    continue
                if route.kind != 'exempt':
                    cond = {'kind': 'qualifying_place', 'text': 'finish in a qualifying place',
                            'positions': None, 'top': None, 'places': route.spots or None,
                            'site_places': list(route.site_spots) or None}
                ty = year - off
                out.append({'event': _ev(season, sid, year), 'condition': cond, 'target': _ev(season, major, ty),
                            'route': {'code': route.code, 'label': route.label, 'source': f'qualification.{major}'},
                            'status': status(sid, route, major, ty), 'restrictions': _restrictions(route),
                            'decided': None})
    for final, st in Q.stages(season.ctx.version).items():
        for sid in st['feeders']:
            if sid in upcoming:
                out.append({'event': _ev(season, sid, year),
                            'condition': {'kind': 'qualifying_place', 'text': f'finish in the top {st["per_site"]} at '
                                          'your site', 'positions': None, 'top': None, 'places': None,
                                          'site_places': [st['per_site']]},
                            'target': _ev(season, final, year),
                            'route': {'code': f'STAGE_{final}', 'label': f'{EL.label(season.cal, final)} stage',
                                      'source': 'qualification.stages'},
                            'status': status(sid, None, final, year), 'restrictions': [], 'decided': None})
    sp = season.cal.spec
    for sid, _, label in sp.college_qualifiers:                     # v3: the college championship's qualifiers
        if sid in upcoming:
            done = season.college_qualified(year)
            st = ('already_qualified' if gid in done else
                  'not_eligible' if g.tour not in season.US_COLLEGE or g.lifestyle == 'retired' else 'needs_result')
            out.append({'event': _ev(season, sid, year),
                        'condition': {'kind': 'qualifying_place',
                                      'text': f'finish in your heat\'s share of the qualifier\'s '
                                              f'{sp.college_qualifier_places} places (heats of at most '
                                              f'{sp.college_heat_size}, places in proportion to heat size)',
                                      'positions': None, 'top': None, 'places': sp.college_qualifier_places,
                                      'site_places': None},
                        'target': _ev(season, 'COLLEGE_NATIONAL_CHAMPIONSHIP', year),
                        'route': {'code': 'COLLEGE_QUALIFYING', 'label': 'College championship qualifying',
                                  'source': 'season.college_qualified'},
                        'status': st, 'restrictions': ['US college golfers (any nationality)',
                                                       'not already qualified this season'],
                        'decided': None})
    seen = {(o['event']['series_id'], o['target']['series_id']) for o in out}
    for sid in sorted(upcoming):
        t = EL.target(season.cal, sid)
        if t is None or (sid, t['id']) in seen:
            continue
        out.append({'event': _ev(season, sid, year),
                    'condition': {'kind': 'qualifying_place', 'text': 'finish in a qualifying place (the field rule)',
                                  'positions': None, 'top': None, 'places': None, 'site_places': None},
                    'target': _ev(season, t['id'], year),
                    'route': {'code': f'TARGET_{t["id"]}', 'label': f'qualifying for {t["label"]}',
                              'source': 'event_labels.target'},
                    'status': status(sid, None, t['id'], year), 'restrictions': [], 'decided': None})
    out.sort(key=lambda o: (o['event']['week'], o['event']['series_id'], o['target']['year'], o['target']['series_id'],
                            o['route']['code']))
    return out
