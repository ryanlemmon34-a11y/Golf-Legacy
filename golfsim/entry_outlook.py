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

STATUSES = ('injured', 'not_eligible', 'cannot_afford', 'holds_place', 'rule_selected', 'quota_limited',
            'open_last_time', 'near_capacity_last_time', 'ahead_of_last_cutoff', 'at_last_cutoff',
            'behind_last_cutoff', 'unknown')
NEAR = 0.8                 # requests at or above this share of the places: 'near capacity' though the field did not fill

LABELS = {
    'injured': 'Unavailable: injured',
    'not_eligible': 'Not eligible to request entry',
    'cannot_afford': 'Eligible, but the trip is not affordable now',
    'holds_place': 'You hold a place under the event\'s rules',
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
