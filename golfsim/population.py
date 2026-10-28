"""World population: every competitive golfer in the world, generated nation by nation.

How a world is made
    1. Talent. Each nation has a pool of serious golfers (its `pool`). Every one gets a hidden
       potential (the overall rating they can reach in their prime) drawn around a mean set by the
       nation's `development`, and an age.
    2. Age. Golfers are still improving until their mid/late twenties (strength, then technique,
       then experience) and decline from their late thirties (strength first; touch and course
       management last). Current overall = potential adjusted for age, plus a little career luck.
    3. Only competitive golfers are kept (overall >= KEEP_OVERALL). Everyone else is a weekend golfer.
    4. Status. Good players turn professional after college; the best college-age players may turn
       pro early; those who don't make it become club professionals or stay amateur.
    5. Attributes. The nation's style and an archetype shape the 21 attributes around the overall;
       age shifts physical attributes down and mental attributes up with experience.
    6. Membership. Professionals are sorted by reputation and fill the Premier Tour, then their
       region's Challenger, Regional and Mini tours; college players join US Division I, US small
       college or international university golf; amateurs join their region's amateur series.

Everything is deterministic for a given seed. Development over time (training, coaches, aging year to
year) and the nation-improvement model come later; `potential`, `peak_age` and the personality traits
`work_ethic` and `coachability` are stored now so they can drive them.
"""
from __future__ import annotations

import math
import random
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from .calendar import TOUR_BY_KEY
from .geography import CITIES_BY_COUNTRY, COUNTRIES
from .golfer import ARCHETYPES, OVERALL_WEIGHTS, Golfer, overall_rating
from .names import make_name
from .nations import STYLES, nations as starting_nations
from .ratings import ATTRIBUTE_KEYS, PERSONALITY_KEYS

# ---- talent model (tuned by tools/world_report.py against the real world ranking) ------------------
CANDIDATES_PER_POOL = 900      # candidate golfers per unit of nation pool
BASE_POTENTIAL = 33.0          # mean potential for a development-60 nation
DEV_EFFECT = 0.55              # potential points per development point
POTENTIAL_SD = 13.0
KEEP_OVERALL = 22.0            # below this: a weekend golfer, not part of the competitive world
CAREER_LUCK_SD = 2.0
PRO_LINE = 47.0               # overall at which half of golfers over 22 have turned professional
# Sampling of weaker golfers: (overall at which everyone is kept, decay of the share kept below it,
# minimum share kept)
KEEP_RULES = {'pro': (71.0, 7.0, 0.03), 'college_age': (74.0, 11.0, 0.0), 'amateur': (100.0, 14.0, 0.0),
              'club_pro': (65.0, 6.0, 0.0)}

PHYSICAL = ('power', 'stamina', 'recovery_rate', 'injury_resistance')
MENTAL = ('composure', 'resilience', 'management', 'focus', 'green_reading')

# Tour membership capacity: field size x this factor (not every member plays every week).
MEMBERS_PER_FIELD = 1.35
PREMIER_MEMBERS = 300
FOREIGN_SHARE = {2: 0.40, 3: 0.25}   # most of a Challenger or Regional tour's members are from its own countries
MIN_REPUTATION = {2: 55.0, 3: 42.0}  # below this, a player starts on a mini tour even if a place is free
PREMIER_AMERICAS_TOP = 125     # the best players worldwide gravitate to the strongest circuit

REGION_CIRCUIT = {'North America': 'PT_AMERICAS', 'Latin America': 'PT_AMERICAS', 'Europe': 'PT_EUROPE',
                  'Africa': 'PT_EUROPE', 'Middle East': 'PT_EUROPE', 'Asia': 'PT_ASIA_PACIFIC',
                  'Oceania': 'PT_ASIA_PACIFIC'}
CHALLENGER_BY_REGION = {'North America': ('CH_AMERICAS', 'CH_LATAM_CANADA'),
                        'Latin America': ('CH_LATAM_CANADA', 'CH_AMERICAS'),
                        'Europe': ('CH_EUROPE',), 'Africa': ('CH_EUROPE',), 'Middle East': ('CH_EUROPE', 'CH_ASIA'),
                        'Asia': ('CH_ASIA',), 'Oceania': ('CH_ASIA', 'CH_EUROPE')}
CHALLENGER_BY_COUNTRY = {'Japan': ('CH_JAPAN', 'CH_ASIA'), 'South Korea': ('CH_ASIA', 'CH_JAPAN'),
                         'Canada': ('CH_LATAM_CANADA', 'CH_AMERICAS')}
REGIONAL_BY_COUNTRY = {
    **{c: 'RG_SOUTHERN_AFRICA' for c in ('South Africa', 'Zimbabwe', 'Namibia', 'Zambia', 'Mauritius', 'Kenya', 'Nigeria')},
    **{c: 'RG_AUSTRALASIA' for c in ('Australia', 'New Zealand', 'Fiji')},
    'South Korea': 'RG_KOREA', 'India': 'RG_INDIA', 'China': 'RG_CHINA', 'Taiwan': 'RG_CHINA',
    **{c: 'RG_MENA' for c in ('United Arab Emirates', 'Qatar', 'Saudi Arabia', 'Bahrain', 'Oman', 'Egypt', 'Morocco')},
}
# Regional tours also take players from neighbouring countries once their own have been placed.
REGIONAL_BY_REGION = {'Africa': ('RG_SOUTHERN_AFRICA', 'RG_MENA'), 'Middle East': ('RG_MENA',),
                      'Europe': ('RG_MENA', 'RG_SOUTHERN_AFRICA'), 'Asia': ('RG_CHINA',),
                      'Oceania': ('RG_AUSTRALASIA',), 'North America': (), 'Latin America': ()}
MINI_BY_REGION = {'North America': ('MN_US_SUNBELT', 'MN_US_DESERT', 'MN_US_MIDWEST', 'MN_US_NORTHEAST'),
                  'Latin America': ('MN_MEXICO_CARIBBEAN', 'MN_SOUTHERN_CONE'), 'Europe': ('MN_GERMANY', 'MN_ALPS'),
                  'Africa': ('MN_EAST_AFRICA',), 'Middle East': ('MN_SE_ASIA',), 'Asia': ('MN_SE_ASIA',),
                  'Oceania': ('MN_AUSTRALIA',)}
AMATEUR_BY_REGION = {'North America': 'AM_NORTH_AMERICA', 'Latin America': 'AM_LATAM', 'Europe': 'AM_EUROPE',
                     'Africa': 'AM_AFRICA', 'Middle East': 'AM_ASIA', 'Asia': 'AM_ASIA', 'Oceania': 'AM_OCEANIA'}


def age_deficit(age, peak_age, aging_rate=1.0):
    """Overall points below potential at this age: still improving when young, declining when old.

    A golfer with a prime starting at 27 is ~12 points short at 18, ~4 at 23 and at full strength from
    27 to ~34; then declines ~2 points by 40, ~7 by 45 and ~13 by 50 (times their own aging rate:
    some golfers stay competitive into their fifties, others fade early).
    """
    young = max(0.0, peak_age - age)
    grow = 0.36 * young ** 1.55
    old = max(0.0, age - (peak_age + 7))
    decline = 0.15 * aging_rate * old ** 1.6
    return grow + decline


def age_attribute_shift(key, age, peak_age):
    """How an attribute sits relative to the golfer's overall at this age (before re-centring)."""
    if key in PHYSICAL:
        # strength and stamina peak early and fade first
        return max(-12.0, min(5.0, 0.35 * (29 - age))) if age > 24 else 3.0
    if key in MENTAL:
        # experience: composure and management keep improving into the forties
        return max(-6.0, min(5.0, 0.25 * (age - 30)))
    return 0.0


@dataclass
class World:
    year: int
    seed: int
    nations: dict
    golfers: list = field(default_factory=list)

    def __post_init__(self):
        self.by_id = {g.id: g for g in self.golfers}
        # one person-id space for the whole world: golfers, coaches and caddies (a golfer who becomes a
        # coach keeps their id); ids are never reused
        self.next_id = max((g.id for g in self.golfers), default=0) + 1

    def new_id(self):
        self.next_id += 1
        return self.next_id - 1

    def pros(self):
        return [g for g in self.golfers if g.status == 'pro']

    def members(self, tour):
        return [g for g in self.golfers if g.tour == tour]

    def ranked(self, golfers=None):
        return sorted(golfers if golfers is not None else self.golfers, key=lambda g: -g.overall)


def _clamp(x, lo=1.0, hi=99.0):
    return lo if x < lo else hi if x > hi else x


def _build_attrs(overall, archetype, style, age, peak_age, rng):
    offsets, _ = ARCHETYPES[archetype]
    tilt = STYLES[style][0]
    attrs = {}
    for k in ATTRIBUTE_KEYS:
        attrs[k] = (overall + offsets.get(k, 0.0) + tilt.get(k, 0.0) + age_attribute_shift(k, age, peak_age)
                    + rng.gauss(0, 5.0))
    for _ in range(10):                                # re-centre so the overall is exactly right
        shift = overall - overall_rating(attrs)
        attrs = {k: _clamp(v + shift) for k, v in attrs.items()}
    return {k: round(v, 1) for k, v in attrs.items()}


def _personality(archetype, overall, rng):
    base = dict(ARCHETYPES[archetype][1])
    p = {}
    for k in PERSONALITY_KEYS:
        mean = base.get(k, 50.0)
        p[k] = round(_clamp(rng.gauss(mean, 14)), 1)
    return p


def _pick_archetype(style, rng):
    mult = STYLES[style][1]
    names = list(ARCHETYPES)
    return rng.choices(names, [mult.get(n, 1.0) for n in names])[0]


def _age(rng):
    """Competitive golfers by age: many in their twenties, thinning out into the fifties."""
    while True:
        a = rng.uniform(18, 62)
        if rng.random() < (1.0 if a < 30 else max(0.25, 1 - (a - 30) / 40)):
            return int(a)


SCOUTING_SD = 4.0             # how far a young golfer's apparent trajectory can be from their own


def _keep_young(cur, age, u, noise):
    """Whether a golfer aged 22 or under is part of the competitive world. Judged as coaches and
    scouts would: on their current level plus the growth a typical golfer makes from this age, with
    the noise of judging teenagers — never on their hidden potential. Some golfers kept will never
    become what they seemed; some late developers are missed and arrive later (if at all)."""
    projected = cur + age_deficit(age, 27.0) + noise
    status = 'pro' if projected >= PRO_LINE + 3 else 'amateur'
    return u < _keep_probability(status, 27, projected)


def _keep_probability(status, age, cur):
    """The world holds every good golfer and a sample of the many weaker competitive golfers.

    Below the full-membership line each status keeps a falling share, so the world has roughly the
    number of golfers its tours and events can hold (see the KEEP_* settings).
    """
    full, decay, floor = KEEP_RULES[status if status != 'amateur' else ('college_age' if age <= 22 else 'amateur')]
    return 1.0 if cur >= full else max(floor, math.exp((cur - full) / decay))


def candidates(year, seed, profiles, scale=1.0):
    """Stage 1 (numbers only, fast): (country, age, potential, peak age, current overall, status,
    aging rate) for every golfer the world keeps."""
    out = []
    for country, prof in profiles.items():
        n = max(1, round(prof.pool * CANDIDATES_PER_POOL * scale))
        mu = BASE_POTENTIAL + DEV_EFFECT * (prof.development - 60)
        crng = random.Random(f'{seed}:talent:{country}')
        for _ in range(n):
            age = _age(crng)
            pot = crng.gauss(mu, POTENTIAL_SD)
            peak = crng.gauss(27.0, 2.0)
            aging = math.exp(crng.gauss(0, 0.3))
            cur = pot - age_deficit(age, peak, aging) + crng.gauss(0, CAREER_LUCK_SD)
            if cur < KEEP_OVERALL:
                continue
            cur = min(cur, 99.0)                     # the rating scale tops out at 99
            pot = max(min(pot, 99.0), cur)
            status = _status(age, cur, prof, crng.random(), crng)
            keep = _keep_young(cur, age, crng.random(), crng.gauss(0, SCOUTING_SD)) \
                if age <= 22 and status == 'amateur' else crng.random() < _keep_probability(status, age, cur)
            if keep:
                out.append((country, age, pot, peak, cur, status, aging))
    out.sort(key=lambda r: -r[4])
    return out


def _make_golfer(i, row, year, seed, profiles, taken):
    country, age, pot, peak, cur, status, aging = row
    prof = profiles[country]
    grng = random.Random(f'{seed}:golfer:{i}')
    arch = _pick_archetype(prof.style, grng)
    attrs = _build_attrs(cur, arch, prof.style, age, peak, grng)
    pers = _personality(arch, cur, grng)
    g = Golfer(make_name(country, grng, taken), attrs, pers, archetype=arch, id=i, country=country,
               born=year - age, hometown=grng.choice(CITIES_BY_COUNTRY[country]).name, status=status,
               height_cm=int(round(grng.gauss(180, 6.5) + 0.12 * (attrs['power'] - 60))),
               hand='L' if grng.random() < 0.07 else 'R',
               potential=math.ceil(max(pot, overall_rating(attrs)) * 10) / 10, peak_age=round(peak, 1),
               aging_rate=round(aging, 2))
    if status == 'pro':
        g.turned_pro = year - max(0, age - grng.choice((21, 22, 22, 22, 23, 24)))
    return g


def generate_world(year=2027, seed=2027, nation_profiles=None, scale=1.0):
    """Generate every competitive golfer in the world. `scale` multiplies the number of candidates."""
    from .development import init_ceilings
    from .finance import initial_backing, initial_cash
    profiles = nation_profiles or starting_nations()
    taken = set()
    golfers = [_make_golfer(i, row, year, seed, profiles, taken)
               for i, row in enumerate(candidates(year, seed, profiles, scale), 1)]
    world = World(year, seed, profiles, golfers)
    _assign_memberships(world, random.Random(f'{seed}:tours'))
    rng = random.Random(f'{seed}:careers')
    for g in golfers:
        age = g.age(year)
        init_ceilings(g, age, rng)
        g.cash = initial_cash(g, age, rng.random())
        g.backing = initial_backing(age, rng.random(), rng.random())
        t = TOUR_BY_KEY.get(g.tour)
        if g.status == 'club_pro' or (g.status == 'amateur' and age > 22 and not g.tour.startswith('CO_')):
            g.lifestyle = 'part_time'                 # they have a job
        elif g.status == 'pro' and t and t.tier == 4 and age >= 28 and g.overall < 52 and rng.random() < 0.5:
            g.lifestyle = 'part_time'                 # already stopped chasing; plays a few local events
    return world


JUNIOR_SHARE = 1 / 31.25          # share of a nation's candidates who are 18 in any one year (see _age)


def junior_class(year, seed, profiles, start_id, taken):
    """This year's 18-year-olds from every nation (amateurs: college or amateur golf)."""
    rows = []
    for country, prof in profiles.items():
        n = max(0, round(prof.pool * CANDIDATES_PER_POOL * JUNIOR_SHARE))
        mu = BASE_POTENTIAL + DEV_EFFECT * (prof.development - 60)
        crng = random.Random(f'{seed}:juniors:{year}:{country}')
        for _ in range(n):
            pot = crng.gauss(mu, POTENTIAL_SD)
            peak = crng.gauss(27.0, 2.0)
            aging = math.exp(crng.gauss(0, 0.3))
            cur = pot - age_deficit(18, peak, aging) + crng.gauss(0, CAREER_LUCK_SD)
            if cur < KEEP_OVERALL:
                continue
            cur = min(cur, 99.0)
            pot = max(min(pot, 99.0), cur)
            if _keep_young(cur, 18, crng.random(), crng.gauss(0, SCOUTING_SD)):
                rows.append((country, 18, pot, peak, cur, 'amateur', aging))
    rows.sort(key=lambda r: -r[4])
    golfers = [_make_golfer(start_id + i, row, year, f'{seed}:j{year}', profiles, taken) for i, row in enumerate(rows)]
    rng = random.Random(f'{seed}:junior-tours:{year}')
    am_series = {c: k for k, t in TOUR_BY_KEY.items() if t.tier == 6 for c, _ in t.countries}
    for g in golfers:
        g.tour = _college_or_series(g, profiles[g.country], rng, am_series)
    return golfers


def _college_or_series(g, prof, rng, am_series):
    region = COUNTRIES[g.country].region
    if g.overall >= 30:
        if g.country == 'USA' or rng.random() < prof.pathway / 100 * 0.45:
            return 'CO_US_D1' if g.overall >= 44 else 'CO_US_SMALL'
        if rng.random() < 0.6:
            return 'CO_INTL'
    return am_series.get(g.country, AMATEUR_BY_REGION[region])


def _status(age, cur, prof, u, rng):
    if age <= 22:
        # The very best turn professional before or during college.
        if cur >= 66 and u < 0.25 + 0.06 * (cur - 66) + 0.05 * (age - 19):
            return 'pro'
        return 'amateur'
    p_pro = 1 / (1 + math.exp(-(cur - PRO_LINE) / 3.0))
    if age > 50:
        p_pro *= 0.4
    if u < p_pro:
        return 'pro'
    if age >= 26 and cur >= 36 and rng.random() < 0.30:
        return 'club_pro'
    return 'amateur'


def _assign_memberships(world, rng):
    region = lambda g: COUNTRIES[g.country].region
    cap = {k: round(t.field * MEMBERS_PER_FIELD) for k, t in TOUR_BY_KEY.items() if t.tier in (2, 3)}
    used = Counter()
    pros = [g for g in world.golfers if g.status == 'pro']
    # reputation: ability plus a little career luck (results, connections, sponsor invitations)
    rep = {g.id: g.overall + rng.gauss(0, 2.5) + 0.08 * min(10, g.age(world.year) - 21) for g in pros}
    pros.sort(key=lambda g: -rep[g.id])
    for i, g in enumerate(pros):
        if i < PREMIER_MEMBERS:
            g.tour = 'PT_AMERICAS' if i < PREMIER_AMERICAS_TOP else REGION_CIRCUIT[region(g)]
            continue
        options = CHALLENGER_BY_COUNTRY.get(g.country, CHALLENGER_BY_REGION[region(g)])
        options = options + ((REGIONAL_BY_COUNTRY[g.country],) if g.country in REGIONAL_BY_COUNTRY else ())
        options = options + tuple(t for t in REGIONAL_BY_REGION[region(g)] if t not in options)
        for t in options:
            tour = TOUR_BY_KEY[t]
            foreign = all(c != g.country for c, _ in tour.countries)
            if rep[g.id] < MIN_REPUTATION[tour.tier]:
                continue
            if used[t] < cap[t] and (not foreign or used[(t, 'foreign')] < cap[t] * FOREIGN_SHARE[tour.tier]):
                g.tour = t
                used[t] += 1
                used[(t, 'foreign')] += foreign
                break
        else:
            minis = [k for k, t in TOUR_BY_KEY.items() if t.tier == 4 and any(c == g.country for c, _ in t.countries)]
            g.tour = rng.choice(minis or list(MINI_BY_REGION[region(g)]))
    am_series = {c: k for k, t in TOUR_BY_KEY.items() if t.tier == 6 for c, _ in t.countries}
    for g in world.golfers:
        if g.status == 'club_pro':
            g.tour = ''
        elif g.status == 'amateur':
            age = g.age(world.year)
            prof = world.nations[g.country]
            if age <= 22 and g.overall >= 30:
                g.tour = _college_or_series(g, prof, rng, am_series)
            else:
                g.tour = am_series.get(g.country, AMATEUR_BY_REGION[region(g)])


def level_of(g):
    """Plain-language level of a golfer from their membership."""
    if g.status == 'club_pro':
        return 'Club professional'
    t = TOUR_BY_KEY.get(g.tour)
    if t is None:
        return 'Unattached'
    return {1: 'Premier Tour', 2: 'Challenger', 3: 'Regional', 4: 'Mini tour', 5: 'College', 6: 'Amateur'}[t.tier]
