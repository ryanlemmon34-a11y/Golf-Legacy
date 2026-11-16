"""Entry outlook: qualitative, transparent guidance on an entry request (read only; docs/career/ENTRY_OUTLOOK.md).

From three recorded or rule facts only, never this year's other entrants (unknown until the entries close) and never a
percentage:

* whether the golfer may enter and can pay now (career.week_options: the engine's own checks);
* the golfer's entry class for this event now (Season.priority's first element: playing rights, own tour, home
  open, higher / same / lower tour, amateur in a professional event) -- the order the engine admits classes in;
* how the event's field closed at its last recorded edition (Season.note_cutoff via opportunities.field_history):
  whether it filled, and the class of the last golfer taken.

Eligible is not admitted, and holding a place is not having played: `holds_place` comes from the recorded places the
rules give (opportunities.held_places); admission is only ever reported after the field is decided
(career.week_entry). When the facts do not support a judgement the status is `unknown`, with the reason.
"""
from __future__ import annotations

STATUSES = ('injured', 'not_eligible', 'cannot_afford', 'holds_place', 'assured_by_rules', 'unless_qualified_earlier',
            'invitations_later', 'invited', 'accepted', 'alternate_standby', 'declined', 'not_invited', 'expired',
            'withdrawn', 'alternate_unused', 'rule_selected', 'quota_limited',
            'open_last_time', 'near_capacity_last_time', 'ahead_of_last_cutoff', 'at_last_cutoff',
            'behind_last_cutoff', 'unknown')
NEAR = 0.8                 # requests at or above this share of the places: 'near capacity' though the field did not fill

LABELS = {
    'injured': 'Unavailable: injured',
    'not_eligible': 'Not eligible to request entry',
    'cannot_afford': 'Eligible, but the trip is not affordable now',
    'holds_place': 'You hold a place under the event\'s rules',
    'assured_by_rules': 'The rules enter you',
    'unless_qualified_earlier': 'Entered unless you qualify earlier',
    'invitations_later': 'Invitations not yet sent',
    'invited': 'Invited: your answer is due',
    'accepted': 'Invitation accepted',
    'alternate_standby': 'Alternate on stand-by',
    'declined': 'Invitation declined',
    'not_invited': 'Not among those invited',
    'expired': 'Invitation expired',
    'withdrawn': 'Withdrawn from the field',
    'alternate_unused': 'Alternate: no place came free',
    'rule_selected': 'The event selects its own field',
    'quota_limited': 'Limited places for golfers like you',
    'open_last_time': 'Places were left last edition',
    'near_capacity_last_time': 'Requests nearly matched the places last edition',
    'ahead_of_last_cutoff': 'Ahead of last edition\'s cut-off',
    'at_last_cutoff': 'At last edition\'s cut-off',
    'behind_last_cutoff': 'Behind last edition\'s cut-off',
    'unknown': 'No basis for a judgement',
}

UNCERTAINTY = ('This year\'s entrants, the field size and any amateur or visitor limits can differ from last time, '
               'and rankings move before entries close. Guidance, not a probability; entry is decided when the field '
               'is set.')


def _out(status, reason, cls=None, cls_label=None, last=None, uncertainty=UNCERTAINTY):
    return {'status': status, 'label': LABELS[status], 'your_class': cls, 'your_class_label': cls_label,
            'last_edition': last, 'reason': reason, 'uncertainty': uncertainty}


def outlook(season, g, year, week, row, held=None, injured=None):
    """The entry outlook for one week_options row (an ordinary event row, or a rule-selected one with 'rule')."""
    from . import opportunities as O
    sid = row['event_id'].split(':', 1)[1]
    s = season.cal.by_id.get(sid)
    if injured:
        return _out('injured', 'An injury keeps the golfer out of entries this week.', uncertainty=None)
    if 'rule' in row:                                   # a rule-selected field (or qualifying the entrant decides)
        cq = college_qualifier(season, g, sid, year, week)
        if cq is not None:
            return cq
        iv = invitation(season, g, row['event_id'], s)
        if iv is not None:
            return iv
        held = O.held_places(season, g.id, year, week) if held is None else held
        mine = held.get((sid, year))
        if mine:
            return _out('holds_place', 'Recorded: ' + '; '.join(x['label'] for x in mine) + '.', uncertainty=
                        'A held place still needs your period policy to accept it; playing it is reported afterwards.')
        return _out('rule_selected', f'{row["rule"]}. Being eligible does not mean being selected or qualified.',
                    uncertainty='Selection follows the event\'s own rules when its field is built.')
    if not row.get('eligible'):
        return _out('not_eligible', row.get('why') or 'The event\'s entry rules do not admit this golfer now.',
                    uncertainty=None)
    if not row.get('affordable', True):
        return _out('cannot_afford', row.get('why') or 'Not affordable now.', uncertainty=None)
    cls = cls_label = None
    if s is not None and getattr(season, 'year', None) == year:
        cls = season.priority(g, s)[0]
        cls_label = season.entry_class_label(cls)
    last = O.field_history(season, sid, year)
    if s is not None and (cls == 19 or season._visitor(g.id, s)):
        who = 'amateurs in a professional event' if cls == 19 else 'Premier members in a Challenger event'
        return _out('quota_limited', f'Only a limited number of places go to {who}; the record of past editions does '
                    'not show how those places were shared, so no judgement is given.', cls, cls_label, last)
    if last is None:
        return _out('unknown', 'No previous edition of this event is recorded in this world (a new event, an older '
                    'save, or more than a season ago).', cls, cls_label)
    if not last['full']:
        near = last['asked'] >= NEAR * last['capacity']
        return _out('near_capacity_last_time' if near else 'open_last_time',
                    f'In {last["year"]} the field did not fill: {last["admitted"]} taken of {last["capacity"]} places '
                    f'from {last["asked"]} requests' + ('; demand was close to the places, so a small rise fills it.'
                                                         if near else '.'), cls, cls_label, last)
    rec = season.__dict__.get('field_cutoffs', {}).get(last['year'], {}).get(sid, {})
    cut = rec.get('last_class')
    if cut is None or cls is None:
        return _out('unknown', 'The field filled last time, but the class it closed at is not recorded'
                    + ('' if cls is not None else ' (and your class is judged only in the current season)') + '.',
                    cls, cls_label, last)
    if cls < cut:
        st, why = 'ahead_of_last_cutoff', 'Your entry class comes before the class the field closed at last time.'
    elif cls == cut:
        st, why = 'at_last_cutoff', ('Your entry class is the one the field closed at last time: within it, order '
                                     'goes by ranking (or rotation and the entry draw where those rules apply).')
    else:
        st, why = 'behind_last_cutoff', 'Your entry class comes after the class the field closed at last time.'
    return _out(st, f'{why} Last time: {last["admitted"]} taken of {last["capacity"]} places from {last["asked"]} '
                f'requests, closing at {last["closed_at"] or "an unrecorded class"}.', cls, cls_label, last)


def college_qualifier(season, g, sid, year, week):
    """v3 college qualifiers (Season.college_postseason): every active US college golfer not yet qualified by the
    qualifiers already played is entered -- nobody is left out of the heats. So, from the rules and records alone:

    * `assured_by_rules` when every earlier qualifier has been played and the golfer is not among the qualified;
    * `unless_qualified_earlier` while an earlier qualifier is still to be played: a place then, unless they qualify
      there first (a future assumption, never a promise);
    * `not_eligible` (not a US college golfer now, retired, or already qualified) / `injured` (out that week).

    Either place still needs the period policy to accept rule-selected places, and is taken only if no other place the
    same days comes first (rule-selected events are set before ordinary entries). None when this is not a college
    qualifier of a world with them (v1/v2: no change)."""
    sp = getattr(getattr(season, 'cal', None), 'spec', None)
    if sp is None or not sp.college_qualifiers or not sid.startswith('COLLEGE_QUALIFIER_'):
        return None
    ids = [x for x, _, _ in sp.college_qualifiers]
    if sid not in ids:
        return None
    k = ids.index(sid) + 1
    caveat = ('Needs your period policy to accept rule-selected places, and no other place on the same days taken '
              'first; injury or leaving US college golf before then ends it.')
    if g.lifestyle == 'retired' or g.tour not in season.US_COLLEGE:
        return _out('not_eligible', 'Only active US college golfers are entered in the college qualifiers.',
                    uncertainty=None)
    done = season.college_qualified(year, k - 1)
    if g.id in done:
        q = done[g.id]
        return _out('not_eligible', f'Already qualified for the college championship (qualifier {q[0]}, heat {q[1]}, '
                    f'{q[2]}): not entered again.', uncertainty=None)
    from .career import injured_until
    if injured_until(season, g.id, year, week) is not None:
        return _out('injured', 'Injured that week on the recorded injury: not available for this qualifier.',
                    uncertainty=None)
    pending = [j for j, x in enumerate(ids[:k - 1], 1) if f'{year}:{x}' not in season.results]
    if pending:
        return _out('unless_qualified_earlier', f'Every US college golfer not yet qualified is entered. Qualifier'
                    f'{"s" if len(pending) > 1 else ""} {", ".join(map(str, pending))} come'
                    f'{"" if len(pending) > 1 else "s"} first: qualify there and you are not entered in this one.',
                    uncertainty=caveat)
    return _out('assured_by_rules', 'Every US college golfer not yet qualified is entered, and you have not qualified '
                'in the qualifiers played so far.', uncertainty=caveat)


def invitation(season, g, event_id, s):
    """v4 invitation fields (golfsim/invitations.py): where this golfer stands, from the recorded offers and answers
    only. None when the field is not an advance invitation (earlier calendars, qualifiers, earned places)."""
    from . import invitations as INV
    if s is None or not INV.applies(season, s):
        return None
    rec = INV.ledger(season).get(event_id)
    ed = next((e for e in season.cal.editions(int(event_id.split(':', 1)[0])) if e.event_id == event_id), None)
    if rec is None:
        if ed is None:
            return None
        o = INV.offer_week(season, ed)
        if tuple(o) < (season.year, getattr(season, 'week', 1)):
            return None                                 # (sent before this world began: selected in the event week)
        return _out('invitations_later', f'Invitations go out in week {o[1]} of {o[0]}, by amateur ranking'
                    + (' (host country first, then its region)' if s.category == 'national_amateur' else '')
                    + '; no forecast of the selection is made.',
                    uncertainty='The selection is made from the rankings as they stand then.')
    e = next((x for x in rec['entries'] if x['golfer_id'] == g.id), None)
    sent = f'week {rec["offer_at"][1]} of {rec["offer_at"][0]}'
    due = f'week {rec["deadline"][1]} of {rec["deadline"][0]}'
    if e is None:
        return _out('not_invited', f'The selection made in {sent} ({rec["field"]} invited and the alternates, by '
                    'amateur ranking) did not include you.', uncertainty=None)
    st = e['status']
    alt = e['role'] == 'alternate'
    check = 'Every entrant is checked again in the event week (eligible, fit, free those days, able to pay).'
    if st == 'offered':
        return _out('invited', (f'Alternate number {e["order"]}' if alt else 'Invited')
                    + f' in {sent}; answer by {due}.', uncertainty=check)
    if st in ('accepted', 'promoted', 'entered'):
        how = ' (promoted from the alternates)' if st == 'promoted' or e.get('status_before') == 'promoted' else ''
        return _out('accepted', f'Accepted{how}: your place in the field.', uncertainty=check)
    if st == 'standby':
        return _out('alternate_standby', f'Alternate number {e["order"]}, on stand-by: a place goes to you only if '
                    'one comes free and you pass the event-week checks.', uncertainty=check)
    if st == 'declined':
        return _out('declined', 'Declined' + (f': {e["reason"]}' if e.get('reason') else '') + '.', uncertainty=None)
    if st == 'expired':
        return _out('expired', 'Expired' + (f': {e["reason"]}' if e.get('reason') else '') + '.', uncertainty=None)
    if st == 'withdrawn':
        return _out('withdrawn', f'Withdrawn in the event week: {e.get("reason")}.', uncertainty=None)
    return _out('alternate_unused', 'Alternate: no place came free' + (f' ({e["reason"]})' if e.get('reason') else '')
                + '.', uncertainty=None)


def route(season, row):
    """How a planner row's place is reached: 'entry' (an ordinary entry request), 'invitation' (v4 advance
    invitation), 'qualifier' (the entrant decides to try), 'earned' (a field chosen by the event's rules from
    results, exemptions or standings)."""
    from . import invitations as INV
    from .career import entrant_decides
    if 'rule' not in row and not row.get('selected_field'):
        return 'entry'
    s = season.cal.by_id.get(row['event_id'].split(':', 1)[1])
    if s is None:
        return 'earned'
    if INV.applies(season, s):
        return 'invitation'
    if entrant_decides(s):
        return 'qualifier'
    return 'earned'
