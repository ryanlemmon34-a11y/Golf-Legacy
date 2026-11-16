"""Invitations sent in advance (calendar v4; docs/career/ADVANCE_INVITATIONS.md).

Invitation fields -- the national amateur championships and the elite amateur championships chosen by ranking (not
the USA Amateur, which is reached through qualifying and exemptions) -- are no longer picked, accepted and played in one
week. For an edition in week E:

1. offer week O = E - LEAD (national 4, elite 6 weeks; an early-season event is offered in the December before): the
   selection snapshot, by the same rule the event-week selection used (amateur ranking, then observed form, then id;
   host country first, then its region up to a quarter of the field; elite regions; mid-amateurs by age): the first
   `field` golfers are invited, the next quarter of the field are alternates, in order;
2. response deadline R = O + RESPOND: every answer is applied at the start of week R -- an AI golfer's by one fixed
   rule (`rule_answer`), the player's as given (career decision 'invitation', due at R), or by the same rule under
   the career's explicit 'auto' setting; declined or expired places pass to alternates on stand-by, in order
   ('promoted');
3. event week E: every entrant is checked again -- still eligible, not injured, not already taken those days by a field
   set earlier that week, the trip possible and affordable now; anyone who fails is withdrawn (with the reason) and
   only that genuine vacancy goes to the next alternate on stand-by who passes the same checks ('late_replacement').

No random draw anywhere; costs are charged only when the golfer plays (the season's reserve-and-charge path), so a
declined, expired or withdrawn place costs nothing. Qualifiers and earned places (exemptions, orders of merit, the
college postseason, tour finals) are unchanged.
"""
from __future__ import annotations

LEAD = {'national_amateur': 4, 'elite_amateur': 6}       # weeks between the offers and the event
RESPOND = 2                                               # weeks to answer (the deadline is in week O + RESPOND)
ALTERNATES = 4                                            # the alternates: a quarter of the field (at least 4)
NOT_INVITATION = ('USA_AMATEUR',)                         # reached through qualifying and exemptions

TAKEN = ('accepted', 'promoted', 'late_replacement')      # the statuses that hold a place before the event
STATUS_TEXT = {
    'offered': 'offered', 'accepted': 'accepted', 'declined': 'declined', 'expired': 'expired (no valid answer)',
    'standby': 'alternate on stand-by', 'promoted': 'accepted (promoted from the alternates)',
    'late_replacement': 'accepted in the event week (a place came free)', 'unused': 'alternate not needed',
    'entered': 'entered', 'withdrawn': 'withdrawn',
}


def applies(season, s):
    sp = getattr(getattr(season, 'cal', None), 'spec', None)
    return bool(sp is not None and sp.advance_invitations and s.category in LEAD and s.series_id not in NOT_INVITATION)


def _abs(season, y, w):
    return season.abs_week(y, w)


def _date(season, a):
    """[year, week] of an absolute week."""
    y = season.first_year + (a - 1) // 52
    return [y, a - (y - season.first_year) * 52]


def offer_week(season, ed):
    return _date(season, _abs(season, ed.year, ed.week) - LEAD[ed.series.category])


def deadline(season, ed):
    return _date(season, _abs(season, ed.year, ed.week) - LEAD[ed.series.category] + RESPOND)


def ledger(season):
    return season.__dict__.setdefault('invitations', {})


def _pred(season, s, year):
    """Whether golfer g meets the invitation's own criteria (amateur, active, the region / host / age rule) -- the
    event-week selection rule's criteria, applied at the snapshot and again in the event week."""
    from .season import ELITE_AMATEUR_REGIONS, MID_AMATEUR_MIN_AGE, region_of
    from .geography import COUNTRIES
    base = lambda g: g.status == 'amateur' and g.lifestyle != 'retired'
    if s.category == 'elite_amateur':
        if s.eligibility == 'mid_amateur':
            return lambda g: base(g) and g.age(year) >= MID_AMATEUR_MIN_AGE
        regions = ELITE_AMATEUR_REGIONS.get(s.series_id)
        return (lambda g: base(g) and region_of(g) in regions) if regions else base
    host, reg = s.host_country, COUNTRIES[s.host_country].region
    return lambda g: base(g) and (g.country == host or region_of(g) == reg)


def snapshot(season, ed, y, w):
    """The selection at the offer week (the same order and quotas as the event-week selection)."""
    from .season import region_of
    from .geography import COUNTRIES
    s, n = ed.series, ed.series.field
    alts = max(ALTERNATES, n // 4)
    if s.category == 'national_amateur':
        host = season.ranked_amateurs(lambda g: g.lifestyle != 'retired' and g.country == s.host_country)
        reg = season.ranked_amateurs(lambda g: g.lifestyle != 'retired' and g.country != s.host_country
                                     and region_of(g) == COUNTRIES[s.host_country].region)
        invited = [g.id for g in host[:n]]
        quota = max(0, min(n - len(invited), n // 4))
        invited += [g.id for g in reg[:quota]]
        alternates = [g.id for g in host[n:]] + [g.id for g in reg[quota:quota + max(0, n // 4 - quota)]]
    else:
        pred = _pred(season, s, ed.year)
        ranked = season.ranked_amateurs(pred)
        invited = [g.id for g in ranked[:n]]
        alternates = [g.id for g in ranked[n:]]
    alternates = alternates[:alts]
    rec = {'event_id': ed.event_id, 'series_id': s.series_id, 'name': s.name, 'category': s.category,
           'year': ed.year, 'week': ed.week, 'days': sorted(s.day_set), 'field': n,
           'offer_at': [y, w], 'deadline': deadline(season, ed),
           'entries': [{'golfer_id': gid, 'role': 'invited', 'order': k + 1, 'status': 'offered', 'answered_at': None,
                        'by': None, 'reason': None} for k, gid in enumerate(invited)]
                      + [{'golfer_id': gid, 'role': 'alternate', 'order': k + 1, 'status': 'offered',
                          'answered_at': None, 'by': None, 'reason': None} for k, gid in enumerate(alternates)],
           'log': [{'date': [y, w], 'golfer_id': None, 'event': 'offers_sent',
                    'reason': f'{len(invited)} invited, {len(alternates)} alternates'}]}
    return rec


def _city(season, rec):
    return season.venues(rec['year'])[rec['event_id']][0].city


def cost_estimate(season, g, rec):
    """The trip's cost to this golfer now (travel and fees, plus a caddie's week): checked again in the event week."""
    from . import finance as FIN
    
    s = season.cal.by_id[rec['series_id']]
    city = _city(season, rec)
    k = season.staff.caddie(g.id)
    return round(FIN.event_cost(g, s, city, season.home_country(g)) + (k.weekly_fee if k is not None else 0.0), 2)


def conflicts(season, gid, rec, upto=None):
    """Other places this golfer holds (accepted / promoted) for the same week whose days overlap or whose travel the
    engine would not allow: [{kind, event_id, name, text}]."""
    from .geography import CITY_BY_NAME
    from .geography import COUNTRIES
    out = []
    here = CITY_BY_NAME[_city(season, rec)].country
    days = set(rec['days'])
    for other in ledger(season).values():
        if other is rec or (other['year'], other['week']) != (rec['year'], rec['week']):
            continue
        if not any(e['golfer_id'] == gid and e['status'] in TAKEN for e in other['entries']):
            continue
        there = CITY_BY_NAME[_city(season, other)].country
        od = set(other['days'])
        if od & days:
            out.append({'kind': 'invitation', 'event_id': other['event_id'], 'name': other['name'],
                        'text': f'{other["name"]} is on the same days.'})
            continue
        gap = (min(days) - max(od) - 1) if min(days) > max(od) else (min(od) - max(days) - 1)
        same = COUNTRIES[here].region == COUNTRIES[there].region
        need = (season.TRAVEL_DAYS['country'] if here == there
                else season.TRAVEL_DAYS['region' if same else 'world'])
        if season.cal.spec.travel and gap < need:
            out.append({'kind': 'invitation', 'event_id': other['event_id'], 'name': other['name'],
                        'text': f'{other["name"]} the same week leaves no time to travel.'})
    return out


def rule_answer(season, g, rec, entry, year):
    """(answer, reason) by the one fixed rule every AI golfer -- and the player's explicit 'auto' -- answers with: yes
    ('accept' for an invited place, 'standby' for an alternate) when still eligible, not injured past the event on
    the recorded injury, able to afford the trip now, and free of a clash with places already held that week."""
    yes = 'accept' if entry['role'] == 'invited' else 'standby'
    s = season.cal.by_id[rec['series_id']]
    if not _pred(season, s, rec['year'])(g):
        return None, 'no longer meets the entry criteria'
    inj = season.injured.get(g.id)
    if inj is not None and inj[0] > _abs(season, rec['year'], rec['week']):
        return 'decline', 'injured past the event'
    if not season.can_afford(g, s, _city(season, rec), season.spendable(g, year)):
        return 'decline', 'cannot afford the trip'
    c = conflicts(season, g.id, rec)
    if c:
        return 'decline', c[0]['text']
    return yes, None


def _controlled(season, gid):
    c = getattr(season, 'career', None)
    return c if c is not None and c.status == 'active' and c.controls(gid) else None


def respond(season, rec, y, w):
    """Apply every answer to this edition's offers (the deadline week, before any field is set)."""
    for e in rec['entries']:
        if e['status'] != 'offered':
            continue
        g = season.g.get(e['golfer_id'])
        c = _controlled(season, e['golfer_id'])
        if g is None:
            ans, why, by = None, 'no longer playing', None
        elif c is not None and getattr(c, 'invitation_policy', 'ask') != 'auto':
            ans = getattr(c, 'invitation_answers', {}).get(rec['event_id'])
            why, by = (None, 'player') if ans is not None else ('no answer by the deadline', None)
            if ans is not None and not _pred(season, season.cal.by_id[rec['series_id']], rec['year'])(g):
                ans, why = None, 'no longer meets the entry criteria'
        else:
            ans, why = rule_answer(season, g, rec, e, y)
            by = 'auto' if c is not None else 'ai'
        if ans is None:
            e['status'] = 'expired'
        elif ans == 'decline':
            e['status'] = 'declined'
            if why == 'cannot afford the trip':
                season.declined[rec['year']][e['golfer_id']].append(rec['series_id'])
        else:
            e['status'] = 'accepted' if ans == 'accept' else 'standby'
        e['answered_at'], e['by'], e['reason'] = [y, w], by, why
        rec['log'].append({'date': [y, w], 'golfer_id': e['golfer_id'], 'event': e['status'], 'reason': why})
    _promote(season, rec, y, w)


def _promote(season, rec, y, w):
    """Places not taken at the deadline go to alternates on stand-by, in order."""
    open_places = rec['field'] - sum(1 for e in rec['entries'] if e['status'] in TAKEN)
    for e in rec['entries']:
        if open_places <= 0:
            break
        if e['role'] == 'alternate' and e['status'] == 'standby':
            e['status'] = 'promoted'
            open_places -= 1
            rec['log'].append({'date': [y, w], 'golfer_id': e['golfer_id'], 'event': 'promoted',
                               'reason': 'a place was declined or expired'})


def step(season, year, week):
    """The week's invitation work, at its start (before any field is set): offers due this week (this season's
    editions and next season's early ones), then the answers due this week. Once per week; never twice."""
    if not getattr(season.cal.spec, 'advance_invitations', False):
        return
    led = ledger(season)
    done = season.__dict__.setdefault('_invitation_steps', set())
    if (year, week) in done:
        return
    for y in (year, year + 1):
        for ed in season.cal.editions(y):
            if applies(season, ed.series) and ed.event_id not in led and offer_week(season, ed) == [year, week]:
                led[ed.event_id] = snapshot(season, ed, year, week)
    for rec in sorted(led.values(), key=lambda r: (r['year'], r['week'], r['series_id'])):
        if rec['deadline'] == [year, week]:
            respond(season, rec, year, week)
    done.add((year, week))
    if len(done) > 120:
        for k in sorted(done)[:-60]:
            done.discard(k)


def late_editions(season, ed):
    """An edition whose offer week passed before this world began (or before it ran v4 rules): no ledger. The
    event-week selection then runs as before (recorded as such)."""
    return ed.event_id not in ledger(season)


def event_field(season, ed, year, week, busy):
    """The field in the event week: the places taken, each checked again; a genuine vacancy to the next alternate on
    stand-by who passes the same checks. Returns the golfer ids (one site)."""
    from .geography import CITY_BY_NAME
    rec = ledger(season)[ed.event_id]
    s = ed.series
    city = _city(season, rec)
    countries = (CITY_BY_NAME[city].country,)
    pred = _pred(season, s, year)

    def check(gid):
        g = season.g.get(gid)
        if g is None or not pred(g):
            return 'no longer meets the entry criteria'
        if gid in season.injured:
            return 'injured'
        if busy[gid] & s.day_set:
            return 'already playing another event those days'
        if season.cal.spec.travel and not season.can_travel(gid, s.day_set, countries):
            return 'no time to travel from another event this week'
        if not season.can_afford(g, s, city, season.spendable(g, year)):
            return 'cannot afford the trip now'
        return None
    take = []
    vacancies = 0
    for e in rec['entries']:
        if e['status'] not in TAKEN:
            continue
        why = check(e['golfer_id'])
        if why is None:
            take.append(e['golfer_id'])
            e['status_before'] = e['status']
            e['status'] = 'entered'
        else:
            e['status_before'] = e['status']
            e['status'], e['reason'] = 'withdrawn', why
            vacancies += 1
            rec['log'].append({'date': [year, week], 'golfer_id': e['golfer_id'], 'event': 'withdrawn',
                               'reason': why})
            if why == 'cannot afford the trip now':
                season.declined[year][e['golfer_id']].append(s.series_id)
    for e in rec['entries']:
        if e['role'] != 'alternate' or e['status'] != 'standby':
            continue
        if vacancies <= 0:
            e['status'] = 'unused'
            continue
        why = check(e['golfer_id'])
        if why is None:
            take.append(e['golfer_id'])
            e['status_before'] = 'standby'
            e['status'], e['reason'] = 'entered', 'late replacement: a place came free'
            e['late'] = True
            vacancies -= 1
            rec['log'].append({'date': [year, week], 'golfer_id': e['golfer_id'], 'event': 'late_replacement',
                               'reason': 'a place came free'})
        else:
            e['status'], e['reason'] = 'unused', f'not available for the late place: {why}'
    rec['played'] = [year, week]
    return take


def prune(season, year):
    led = ledger(season)
    for k in [k for k, r in led.items() if r['year'] < year - 1]:
        del led[k]
