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


def _make_golfer(i, row, year, seed, profiles, taken, in_use=None):
    country, age, pot, peak, cur, status, aging = row
    prof = profiles[country]
    grng = random.Random(f'{seed}:golfer:{i}')
    arch = _pick_archetype(prof.style, grng)
    attrs = _build_attrs(cur, arch, prof.style, age, peak, grng)
    pers = _personality(arch, cur, grng)
    g = Golfer(make_name(country, grng, taken, in_use), attrs, pers, archetype=arch, id=i, country=country,
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
    from .finance import SELF_FUNDED_SEASONS, backer_deal, initial_backing, initial_cash, seeded_losses
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
        if g.status == 'pro' and g.lifestyle == 'full_time' and t and t.tier >= 2:
            # professionals below the Premier Tour may already be backed (no record yet: a middling one);
            # the deal is their backing (family money included), not an extra pot
            b = random.Random(f'{seed}:backers:{g.id}')
            g.backer = backer_deal(age, 0.4, b.random(), b.random())
            if g.backer and g.cash >= SELF_FUNDED_SEASONS * seeded_losses(g, t.tier):
                g.backer = 0.0                        # their own savings already pay for the chase: backers
                                                      # come only if they later need them (careers)
            if g.backer:
                g.backing, g.backer_patience = 0.0, b.random()
    return world


JUNIOR_SHARE = 1 / 31.25          # share of a nation's candidates who are 18 in any one year (see _age)


# ---- the yearly entrant cohorts and each nation's share of them (rules 2026-11-05, owner decision D7) -------------
# Two pathways bring new golfers into the world each year: the junior class (18-year-old amateurs) and the new
# professionals from outside the tracked amateur game (21-26). The EXISTING rule for each: every nation draws
# a fixed number of candidates (from its pool) around a mean potential set by its development, and keeps those
# who pass the pathway's filter. Since rules 2026-11-05 that rule fixes only the year's TOTAL, and nations
# share it:
#   1. total      what the existing rule creates that year from the BASELINE nation profiles (fixed when the
#                 world began), with the existing per-nation random streams: today's year-to-year variation,
#                 never anything to do with prestige;
#   2. shares     each nation's expected share of the golfers the existing rule creates (expected_shares:
#                 candidates x the chance one passes the filter), times its participation multiplier from
#                 national prestige (participation.py), normalised to 100 %;
#   3. allocation the total split by those shares, largest remainders first (ties: larger quota, then name);
#   4. generation each nation draws candidates from its own existing distribution (the same mean from its
#                 development, the same filter) until exactly its allocation has passed: first the existing
#                 rule's own draws, then further draws continuing the same stream (seed, pathway, year,
#                 nation), so a share changes how many golfers come from a nation -- never their talent, and
#                 never the total.
#   5. no cap     a nation's stream continues until its allocation has passed, however long that takes: the
#                 quota is always met exactly, from the nation's own conditional distribution, and the actual
#                 number created is always the fixed total. It terminates: draws are independent and each
#                 passes with probability p > 0 (pass_chance; rising with development, about 1 in 100,400
#                 for new professionals and 1 in 9,300 for juniors even at development 0), so the draws a
#                 nation needs for m more golfers are negative binomial: finite with probability 1, m/p on
#                 average, and more than N draws only with probability below m(1-p)^(N/m). The rarest real
#                 nation is Turkey's new professionals, 1 in 658 (Czechia 1 in 316). Until 2026-11 the draws stopped at
#                 400 per golfer owed + 1000 and raised RuntimeError, which a rare but valid tail reached
#                 (Czechia, seed 99, new professionals 2029: its first passer is draw 2161; the cap was 1590).
#                 Lifting the cap changes nothing a cap-respecting run produced: the same stream, the same draws.
# Nothing here reads or changes a nation's pool or development beyond the existing rule's own use of them.

PATHWAYS = ('juniors', 'new_pros')


def _cand_n(kind, prof):
    """Candidates a nation draws a year under the existing rule."""
    scale = NEW_PRO_SCALE if kind == 'new_pros' else 1.0
    return max(0, round(prof.pool * CANDIDATES_PER_POOL * JUNIOR_SHARE * scale))


def _mu(prof):
    return BASE_POTENTIAL + DEV_EFFECT * (prof.development - 60)


def _junior_draw(crng, country, mu):
    """One junior candidate, exactly as the existing rule draws it: the kept row, or None."""
    pot = crng.gauss(mu, POTENTIAL_SD)
    peak = crng.gauss(27.0, 2.0)
    aging = math.exp(crng.gauss(0, 0.3))
    cur = pot - age_deficit(18, peak, aging) + crng.gauss(0, CAREER_LUCK_SD)
    if cur < KEEP_OVERALL:
        return None
    cur = min(cur, 99.0)
    pot = max(min(pot, 99.0), cur)
    if _keep_young(cur, 18, crng.random(), crng.gauss(0, SCOUTING_SD)):
        return (country, 18, pot, peak, cur, 'amateur', aging)
    return None


def _new_pro_draw(crng, country, mu, prof):
    """One new-professional candidate, exactly as the existing rule draws it: the kept row, or None."""
    pot = crng.gauss(mu, POTENTIAL_SD)
    peak = crng.gauss(27.0, 2.0)
    aging = math.exp(crng.gauss(0, 0.3))
    luck = crng.gauss(0, CAREER_LUCK_SD)
    age = crng.choice(NEW_PRO_AGES)
    cur18 = pot - age_deficit(18, peak, aging) + luck
    tracked = cur18 >= KEEP_OVERALL and _keep_young(cur18, 18, crng.random(), crng.gauss(0, SCOUTING_SD))
    cur = pot - age_deficit(age, peak, aging) + luck
    if tracked or cur < KEEP_OVERALL:
        return None
    cur = min(cur, 99.0)
    pot = max(min(pot, 99.0), cur)
    if _status(max(age, 23), cur, prof, crng.random(), crng) != 'pro':
        return None
    if crng.random() < _keep_probability('pro', age, cur):
        return (country, age, pot, peak, cur, 'pro', aging)
    return None


class _Stream:
    """A nation's candidates for one pathway and year, in draw order: the existing rule's random stream
    (`{seed}:juniors:{year}:{country}` or `{seed}:new-pros:{year}:{country}`), which simply continues past the
    existing rule's last draw when more are needed. Draw d is fixed by (seed, pathway, year, nation, d)."""

    def __init__(self, kind, year, seed, country, prof):
        tag = 'juniors' if kind == 'juniors' else 'new-pros'
        self.rng = random.Random(f'{seed}:{tag}:{year}:{country}')
        self.kind, self.country, self.prof, self.mu = kind, country, prof, _mu(prof)
        self.draws = 0

    def draw(self):
        self.draws += 1
        if self.kind == 'juniors':
            return _junior_draw(self.rng, self.country, self.mu)
        return _new_pro_draw(self.rng, self.country, self.mu, self.prof)

    def passers(self, n):
        """The kept rows among the next n draws."""
        return [r for r in (self.draw() for _ in range(n)) if r is not None]


def existing_rule(kind, year, seed, profiles):
    """The existing rule, nation by nation: {country: (kept rows, its stream after the rule's draws)}."""
    out = {}
    for country, prof in profiles.items():
        st = _Stream(kind, year, seed, country, prof)
        out[country] = (st.passers(_cand_n(kind, prof)), st)
    return out


def allocate(total, shares):
    """Split `total` places by `shares` ({country: share}, summing to 1): each nation's whole quota, then one
    more place to the largest remainders until the total is reached; ties by the larger quota, then the
    nation's name (reproducible)."""
    shares = normalised(shares)
    quota = {c: total * s for c, s in shares.items()}
    out = {c: int(math.floor(q)) for c, q in quota.items()}
    left = total - sum(out.values())                     # (0 <= left < number of nations: the quotas sum to total)
    order = sorted(quota, key=lambda c: (-(quota[c] - out[c]), -quota[c], c))
    for c in order[:max(0, left)]:
        out[c] += 1
    return out


def normalised(weights):
    tot = sum(weights.values())
    return {c: (w / tot if tot > 0 else 0.0) for c, w in weights.items()}


def entrant_rows(kind, year, seed, profiles, baseline=None, shares=None, report=None):
    """This year's entrant rows for a pathway under the cohort-share rule (see the block comment above).
    profiles: the nations now (each nation's own distribution); baseline: the profiles the world began with
    (the total; default `profiles`); shares: {country: share} (default: the expected shares of the existing
    rule, expected_shares). Every nation gets exactly its allocation and the rows number exactly the total.
    `report` (a dict) receives 'total', 'existing' (the existing rule's count per nation), 'allocated' and
    'draws'."""
    baseline = baseline or profiles
    if set(baseline) != set(profiles):
        raise ValueError('the baseline and current nation profiles must name the same nations')
    base = existing_rule(kind, year, seed, baseline)
    total = sum(len(rows) for rows, _ in base.values())
    shares = shares if shares is not None else expected_shares(kind, baseline)
    if set(shares) != set(profiles):
        raise ValueError('a share is needed for every nation')
    alloc = allocate(total, shares)
    rows = []
    draws = {}
    for country, prof in profiles.items():
        k = alloc.get(country, 0)
        if country in base and _same_distribution(baseline[country], prof):
            got, st = base[country]
            got = list(got)
        else:                                            # a nation whose profile changed: its own stream anew
            st = _Stream(kind, year, seed, country, prof)
            got = []
        while len(got) < k:                              # step 5: no cap (terminates: see the block comment)
            r = st.draw()
            if r is not None:
                got.append(r)
        rows.extend(got[:k])
        draws[country] = st.draws
    if report is not None:
        report.update(total=total, existing={c: len(r) for c, (r, _) in base.items()}, allocated=alloc, draws=draws)
    return rows


def _same_distribution(a, b):
    return a.pool == b.pool and a.development == b.development


# ---- expected shares of the existing rule (numerical integration; no random draws) --------------------------------
# A candidate passes or not depending only on X = potential + career luck (normal: mean from development, sd
# sqrt(POTENTIAL_SD^2 + CAREER_LUCK_SD^2)), the peak age, the aging rate, the age (new professionals) and the
# filters' own scouting noise and coin flips. So the chance of passing is the integral of
# normal(X; mu, sd) x g(X), where g -- the chance of passing given X -- is the same for every nation and is
# tabulated once per process. Expected count = candidates x chance; a nation's share = its expected count / all.
_X_LO, _X_HI, _X_STEP = 22.0, 152.0, 0.2
_TABLES = {}


def _normal_nodes(mean, sd, half=6.0, step=0.25):
    """Simpson nodes and weights (summing to 1) for a normal variable, over mean +- half sd."""
    n = int(round(2 * half / step))
    n += n % 2
    xs = [-half + i * 2 * half / n for i in range(n + 1)]
    ws = [(1 if i in (0, n) else 4 if i % 2 else 2) * math.exp(-x * x / 2) for i, x in enumerate(xs)]
    tot = sum(ws)
    return [(mean + sd * x, w / tot) for x, w in zip(xs, ws)]


def _young_keep_table():
    """K(c): the chance _keep_young keeps a golfer whose overall at 18 is c (scouting noise integrated), on a
    grid from KEEP_OVERALL up (linear interpolation; 1.0 beyond the grid, where every golfer is kept)."""
    d = age_deficit(18, 27.0)
    noise = _normal_nodes(0.0, SCOUTING_SD)
    step, lo, hi = 0.05, KEEP_OVERALL, _X_HI + 1
    vals = []
    c = lo
    while c <= hi + 1e-9:
        k = 0.0
        for e, w in noise:
            proj = c + d + e
            k += w * _keep_probability('pro' if proj >= PRO_LINE + 3 else 'amateur', 27, proj)
        vals.append(k)
        c += step
    return lo, step, vals


def _interp(table, c):
    lo, step, vals = table
    x = (c - lo) / step
    i = int(x)
    if i >= len(vals) - 1:
        return 1.0
    f = x - i
    return vals[i] * (1 - f) + vals[i + 1] * f


def _pass_given_x():
    """{pathway: [g(X) on the X grid]} (computed once per process)."""
    if 'g' in _TABLES:
        return _TABLES['g']
    K = _young_keep_table()
    peaks = _normal_nodes(27.0, 2.0)
    agings = [(math.exp(z), w) for z, w in _normal_nodes(0.0, 0.3, half=3.0, step=1.0)]   # (peaks below 19 only:
                                                                                        # under 1 in 30,000)
    xs = []
    x = _X_LO
    while x <= _X_HI + 1e-9:
        xs.append(x)
        x += _X_STEP
    gj, gp = [], []
    for X in xs:
        j = p = 0.0
        for peak, wp in peaks:
            # junior: overall at 18 (no decline at 18 for any peak in the integration range)
            c = X - age_deficit(18, peak)
            if c >= KEEP_OVERALL:
                j += wp * _interp(K, min(c, 99.0))
            # new professional: aging matters only where an age 21-26 is past the peak + 7 (very early peaks)
            for aging, wa in (agings if peak < NEW_PRO_AGES[-1] - 7 else ((1.0, 1.0),)):
                c18 = X - age_deficit(18, peak, aging)
                tracked = _interp(K, c18) if c18 >= KEEP_OVERALL else 0.0
                if tracked >= 1.0:
                    continue
                s = 0.0
                for age in NEW_PRO_AGES:
                    ca = X - age_deficit(age, peak, aging)
                    if ca < KEEP_OVERALL:
                        continue
                    ca = min(ca, 99.0)
                    p_pro = 1 / (1 + math.exp(-(ca - PRO_LINE) / 3.0))      # _status, ages 23-50
                    s += p_pro * _keep_probability('pro', age, ca)
                p += wp * wa * (1 - tracked) * s / len(NEW_PRO_AGES)
        gj.append(j)
        gp.append(p)
    _TABLES['g'] = {'juniors': gj, 'new_pros': gp, 'x': xs}
    return _TABLES['g']


def pass_chance(kind, development):
    """The chance one candidate of a nation with this development passes the pathway's filter (existing rule)."""
    key = (kind, float(development))
    if key in _TABLES:
        return _TABLES[key]
    t = _pass_given_x()
    mu = BASE_POTENTIAL + DEV_EFFECT * (development - 60)
    sd = math.hypot(POTENTIAL_SD, CAREER_LUCK_SD)
    xs, g = t['x'], t[kind]
    dens = [math.exp(-((x - mu) / sd) ** 2 / 2) / (sd * math.sqrt(2 * math.pi)) for x in xs]
    tot = sum((dens[i] * g[i] + dens[i + 1] * g[i + 1]) / 2 * _X_STEP for i in range(len(xs) - 1))
    tail = g[-1] * 0.5 * math.erfc((xs[-1] - mu) / (sd * math.sqrt(2)))    # beyond the grid: g is flat there
    _TABLES[key] = tot + tail
    return tot + tail


def expected_counts(kind, profiles):
    """{country: expected golfers a year} under the existing rule: candidates x the chance one passes."""
    return {c: _cand_n(kind, p) * pass_chance(kind, p.development) for c, p in profiles.items()}


def expected_shares(kind, profiles):
    """{country: expected share of the pathway's golfers} under the existing rule (sums to 1)."""
    return normalised(expected_counts(kind, profiles))


def junior_class(year, seed, profiles, start_id, taken, in_use=None, baseline=None, shares=None, report=None):
    """This year's 18-year-olds from every nation (amateurs: college or amateur golf), by the cohort-share
    rule (entrant_rows: the total from the baseline profiles, split by `shares`). Names: see
    names.make_name (`taken`: every name used so far; `in_use`: those of people active now)."""
    rows = entrant_rows('juniors', year, seed, profiles, baseline, shares, report)
    rows.sort(key=lambda r: -r[4])
    golfers = [_make_golfer(start_id + i, row, year, f'{seed}:j{year}', profiles, taken, in_use)
               for i, row in enumerate(rows)]
    rng = random.Random(f'{seed}:junior-tours:{year}')
    am_series = {c: k for k, t in TOUR_BY_KEY.items() if t.tier == 6 for c, _ in t.countries}
    for g in golfers:
        g.tour = _college_or_series(g, profiles[g.country], rng, am_series)
    return golfers


NEW_PRO_SCALE = 5.5               # aspiring professionals a year, in birth cohorts' worth of candidates (see below)
NEW_PRO_AGES = (21, 22, 23, 24, 25, 26)


def new_professionals(year, seed, profiles, start_id, taken, in_use=None, baseline=None, shares=None, report=None):
    """This year's new professionals from outside the tracked amateur game.

    The junior class follows one route into professional golf in detail (college and national amateur
    golf). Real lower tours are refilled every year by a much wider base: small colleges, academies,
    club and late-developing golfers, players from countries without college golf. Without them the
    lower tours empty, because their players stop chasing within a few years while the starting world
    (where every golfer at professional level is a touring pro) assumes they stay. Each nation sends
    golfers in proportion to its golf scene, drawn exactly as the starting world draws its young
    professionals (ability for their age, the professional status rule and the same keep rule for
    the many weaker professionals): NEW_PRO_SCALE birth cohorts' worth of candidates aged 21-26. Golfers
    the junior class would have kept are left out (they are already in the world). Nothing here
    depends on how many golfers the tours hold now: it is a steady flow, not a top-up.
    Since rules 2026-11-05 that flow's yearly total is split between nations by the cohort-share rule
    (entrant_rows), like the junior class."""
    rows = entrant_rows('new_pros', year, seed, profiles, baseline, shares, report)
    rows.sort(key=lambda r: -r[4])
    golfers = [_make_golfer(start_id + i, row, year, f'{seed}:p{year}', profiles, taken, in_use)
               for i, row in enumerate(rows)]
    for g in golfers:
        g.turned_pro = year
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
