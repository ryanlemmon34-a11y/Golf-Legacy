"""A golfer's season, week by week: what they played, or why they did not -- the evidence behind every
"no starts" explanation (roadmap v14: a season with unaffordable or full-field weeks is not "voluntary").

Each week is classified once when it is played (Season.record_access, in this order: played; injured; not
admitted -- every acceptable field full, or not picked for the college lineup; no suitable event scheduled;
not eligible for the events scheduled; could not afford any event; declined the events on offer; chose to
train, rest or work -- the last three only when an affordable event they could enter existed that week).
The season's counts are archived with each golfer's season (careers 'access'), so the ledger below can be
read for any archived season; nothing is inferred beyond what each week recorded.

Groups:
- **played**
- **injured**
- **barriers** (the golfer could not play that week): not admitted, no suitable event, not eligible,
  could not afford any event
- **choices** (an affordable event they could enter existed): declined the events on offer, trained,
  rested or worked
"""
from __future__ import annotations

PLAYED = ('played: first choice', 'played: alternative', 'played: selected field')
INJURED = ('injured',)
BARRIERS = {
    'not admitted': ('shut out: every acceptable field full', 'not selected for the college lineup'),
    'no suitable event': ('no suitable event scheduled',),
    'not eligible': ('not eligible for the events scheduled',),
    'unaffordable': ('could not afford any event',),
}
CHOICES = {
    'declined': ('declined the events on offer',),
    'trained, rested or worked': ('chose to train', 'chose to rest', 'chose to work'),
}
STAGE = {'not admitted': 'entry (the field was full or the lineup chosen)', 'no suitable event': 'calendar',
         'not eligible': 'eligibility', 'unaffordable': 'money', 'declined': 'their own choice',
         'trained, rested or worked': 'their own plan'}


def ledger(weeks):
    """{'weeks': total weeks recorded, 'played', 'injured', 'barrier', 'choice' (week counts), 'groups':
    {group: weeks}, 'detail': {recorded outcome: weeks}} from a season's weekly counts."""
    weeks = {k: int(v) for k, v in (weeks or {}).items() if v}
    groups = {}
    for name, keys in list(BARRIERS.items()) + list(CHOICES.items()):
        n = sum(weeks.get(k, 0) for k in keys)
        if n:
            groups[name] = n
    return {'weeks': sum(weeks.values()), 'played': sum(weeks.get(k, 0) for k in PLAYED),
            'injured': sum(weeks.get(k, 0) for k in INJURED),
            'barrier': sum(groups.get(k, 0) for k in BARRIERS), 'choice': sum(groups.get(k, 0) for k in CHOICES),
            'groups': groups, 'detail': weeks}


def zero_start_summary(weeks, injury_weeks=0, lifestyle=None):
    """(kind, text) for a season without a start, from its weekly evidence. kind: 'injured' (most weeks),
    'barriers' (only barriers kept them out), 'choices' (an affordable event they could enter existed every
    week they did not play), 'mixed' (both: never called voluntary), or 'not recorded'. The text gives every
    contributing cause with its weeks, out of the weeks recorded."""
    lg = ledger(weeks)
    n = lg['weeks']
    if not n:
        return 'not recorded', 'no starts (the weeks were not recorded)'
    if lg['injured'] * 2 >= n:
        kind = 'injured'
    elif lg['barrier'] and lg['choice']:
        kind = 'mixed'
    elif lg['barrier']:
        kind = 'barriers'
    elif lg['choice']:
        kind = 'choices'
    else:
        kind = 'injured' if lg['injured'] else 'not recorded'
    parts = []
    if lg['injured']:
        parts.append(f'injured {lg["injured"]}')
    bar = [f'{k} {v}' for k, v in lg['groups'].items() if k in BARRIERS]
    cho = [f'{k} {v}' for k, v in lg['groups'].items() if k in CHOICES]
    if bar:
        parts.append(f'barriers {lg["barrier"]} ({", ".join(bar)})')
    if cho:
        parts.append(f'choices {lg["choice"]} ({", ".join(cho)})')
    lead = {'injured': 'mostly injured', 'barriers': 'kept out by barriers', 'choices': 'chose not to play',
            'mixed': 'barriers and choices', 'not recorded': 'not recorded'}[kind]
    if kind == 'choices' and lifestyle == 'part_time':
        lead = 'part-timer: chose not to play'
    return kind, f'{lead}: {"; ".join(parts)} -- weeks out of {n} recorded'
