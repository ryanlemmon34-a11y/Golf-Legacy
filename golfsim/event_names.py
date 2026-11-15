"""Distinctive fictional names for the ordinary numbered events of a new (v3) calendar.

v1 and v2 calendars keep their names ("Sunbelt Mini Tour Event 7"). A v3 calendar (new worlds only) gives each
ordinary numbered event a place name instead: the town it is first played in, an optional course-style feature and a
suffix that fits the kind of event -- "Tucson Desert Classic", "Bergen Fjord Open", "Ames Collegiate". Only names
change: series ids, weeks, venues, fields, the calendar's placement keys (Premier events and anchors keep their
names) and every random draw are untouched. Deterministic from the calendar's own seed and the series ids, unique
within the calendar, no real brands or sponsors.
"""
from __future__ import annotations

import random
import re

GENERIC = re.compile(r'\bEvent \d+\b')

SUFFIXES = {
    'pro': ('Open', 'Classic', 'Championship', 'Invitational', 'Trophy', 'Cup', 'Challenge', 'International'),
    'mini': ('Classic', 'Shootout', 'Challenge', 'Open', 'Pro-Am', 'Charity Classic', 'Players Cup'),
    'club': ('Club Professional Classic', 'Pro Championship', 'Professionals\' Open', 'Section Championship'),
    'amateur': ('Amateur', 'Amateur Classic', 'Invitational Amateur', 'Amateur Cup', 'Amateur Trophy'),
    'college': ('Intercollegiate', 'Collegiate', 'Collegiate Classic', 'Invitational', 'Cup'),
}
FEATURES = ('Links', 'Pines', 'Dunes', 'Valley', 'Lakes', 'Ridge', 'Heath', 'Harbour', 'Oaks', 'Highlands', 'Bay',
            'Canyon', 'Meadows', 'Downs', 'Cliffs', 'Forest', 'Springs', 'Hills', 'River', 'Coast')


def _kind(s):
    if s.kind == 'college':
        return 'college'
    if s.eligibility == 'club_pro':
        return 'club'
    if s.kind == 'amateur' or s.eligibility == 'amateur':
        return 'amateur'
    if s.tier >= 4:
        return 'mini'
    return 'pro'


# places too closely tied to real, famous events to name an ordinary one after (the event still plays there)
AVOID = {'Augusta', 'Pebble Beach', 'St Andrews', 'Carnoustie', 'Muirfield', 'Pinehurst', 'Ponte Vedra Beach',
         'Wentworth', 'Sawgrass'}


def _town(city):
    return city.split(',')[0].strip()


def _place(s):
    for c in s.cities or ():
        t = _town(c)
        if t not in AVOID:
            return t
    return s.host_country


def fictional_names(series, seed):
    """{series id: name} for every ordinary numbered event of `series` (oldest id first), unique and stable."""
    taken = {s.name for s in series if not GENERIC.search(s.name)}
    out = {}
    for s in sorted(series, key=lambda s: s.series_id):
        if s.category != 'regular' or not GENERIC.search(s.name):
            continue
        rng = random.Random(f'{seed}:event-name:{s.series_id}')
        town = _place(s)
        suff = SUFFIXES[_kind(s)]
        tries = [f'{town} {rng.choice(suff)}'] + \
                [f'{town} {f} {x}' for f in rng.sample(FEATURES, len(FEATURES)) for x in rng.sample(suff, len(suff))]
        name = next((t for t in tries if t not in taken), None)
        if name is None:                                   # (every combination used: the numbered name stays)
            continue
        taken.add(name)
        out[s.series_id] = name
    return out
