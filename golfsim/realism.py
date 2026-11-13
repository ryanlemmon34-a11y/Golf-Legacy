"""Development rules for new worlds: readiness at entry and attribute-specific aging (rules 2026-11-16, 'dev-2'),
then the elite tail, prodigy readiness and seeded money by standing (rules 2026-11-17, 'dev-3', section 3).

Worlds keep the development rules they were created with (`World.dev_rules`, `Season.dev_rules`): worlds created
before these rules, and any world asked for `LEGACY`, play the rules of 'dev-1' unchanged; worlds created under
'dev-2' keep 'dev-2' unchanged (sections 1 and 2 only). Plan, targets and
evidence: docs/review/realism/PLAN.md and RESULTS.md.

1. Readiness at entry (teenagers only). The existing generation rule draws a candidate's potential, peak age, aging
   rate and career luck and keeps or drops them by the scouts' rule (population._keep_young), unchanged. Only AFTER
   that, an entrant aged 18 or 19 keeps at least about READY_FLOOR points (18; half at 19) between their entry
   Overall and their potential: a smooth floor on youth headroom (softplus), so the near-finished teenage tail
   becomes "very good and still growing" while every potential, every prodigy (potential is untouched) and every
   cohort count and identity stays exactly as it was. Every decision the existing rule takes on the entry level
   (the starting world's memberships, a junior's college or series) is taken on the existing rule's attributes,
   with the same random streams; the readiness attributes, built from the same draws, are swapped in afterwards
   (population._make_golfer, _apply_ready). Typical entrants (about 10 points of headroom at 18) move by
   about 0.01; a junior with 5 points by about 0.6; one already at potential by 4.5.

2. Attribute-specific, individual aging (population.age_deficit, which sets generated golfers' level for their
   age and the scouts' rule, is unchanged). Each attribute declines from its own onset after the golfer's own peak
   age, at its own rate, times the golfer's own aging rate (both drawn at generation, unchanged) and a per-golfer,
   per-category factor (some keep their speed longer, others their touch), so there is no common age at which
   anything happens. Physical decline starts where it did in 'dev-1' but steepens with the years (so peaks and
   elite numbers are kept while the late thirties and forties cost more);
   part of each year's physical decline (MAINTAIN) is conditioning that physical training can win back, harder
   with age (development.learning_rate). Technique declines by attribute (speed-dependent long irons and
   recovery play earlier, chipping and lag putting latest). Green reading matures with experience like the
   mental game (in 'dev-1' the putting decline branch shadowed it after peak age + 8). Nothing forces
   retirement.
"""
from __future__ import annotations

import math
import random

LEGACY = 'dev-1'
DEV2 = 'dev-2'
DEV3 = 'dev-3'
CURRENT = DEV3
# Which rule families each version uses. Versions are compared by membership, never by `== CURRENT`: when CURRENT
# moves on, a world created under an earlier version must keep exactly its own rules (a dev-2 world keeps dev-2
# readiness and dev-2 aging; it must not fall back to dev-1 because it is no longer CURRENT).
READY_RULES = (DEV2, DEV3)           # readiness floor at entry (section 1)
ATTRIBUTE_AGING = (DEV2, DEV3)       # attribute-specific aging (section 2)
ELITE_RULES = (DEV3,)                # elite tail, prodigy readiness, seeded money by standing (section 3)
KNOWN = (LEGACY, DEV2, DEV3)

# ---- 1. readiness at entry ----------------------------------------------------------------------------------------
READY_FLOOR = 4.5            # youth headroom (potential - Overall) an 18-year-old keeps at least, softly
READY_AGES = (18, 20)        # the full floor at 18, half at 19, none from 20


def ready_floor(age):
    lo, hi = READY_AGES
    return READY_FLOOR * max(0.0, min(1.0, (hi - age) / (hi - lo)))


def _softplus(z):
    return z + math.log1p(math.exp(-z)) if z > 0 else math.log1p(math.exp(z))


def entry_overall(cur, pot, age, rules=DEV2):
    """The entry Overall under the readiness floor: potential minus a headroom that is never far below the floor.
    Increasing in `cur` and in `pot`; equal to `cur` from age 20; never above `cur`. Under dev-3 the floor also
    grows with how far the potential is above PRODIGY_FROM (prodigy_floor)."""
    m = ready_floor(age) if rules not in ELITE_RULES else prodigy_floor(pot, age)
    if m <= 0.0:
        return cur
    s = m / 4.0
    h = max(0.0, pot - cur)
    return min(cur, pot - (m + s * _softplus((h - m) / s)))


# ---- 2. attribute-specific aging ------------------------------------------------------------------------------------
# attribute: (onset in years after the golfer's peak age, decline a year at aging rate 1 one year past onset, shape).
# A year's decline is coef x aging_rate x category factor x (age - peak_age - onset) ** shape. 'dev-1' for
# reference: every physical attribute (3, 0.30, 0.7); every technique attribute (8, 0.15, 0.7). Physical decline
# starts when it did (recovery and injury resistance a year sooner) but steepens (shape 0.9), so the golfer's peak and
# the number who reach elite levels are kept while the late thirties and forties cost more: at aging rate 1, power
# about -27 by 45 (dev-1 -19; about 13 yards of driving distance from 85) and -46 by 50, stamina -31 / -52, recovery
# -39 / -64 (docs/review/realism/RESULTS.md). Technique: speed-dependent long
# irons and recovery play a year earlier, the short putts (nerves) and striking a little stronger, chipping, lag
# putting and wedges later.
AGING = {
    'power': (3.0, 0.28, 0.9), 'stamina': (3.0, 0.32, 0.9), 'recovery_rate': (2.0, 0.36, 0.9),
    'injury_resistance': (2.0, 0.36, 0.9),
    'driving_accuracy': (8.0, 0.15, 0.7), 'long_irons': (7.0, 0.17, 0.7), 'mid_irons': (8.0, 0.15, 0.7),
    'ball_flight': (8.0, 0.15, 0.7), 'striking_consistency': (8.0, 0.16, 0.7),
    'wedges': (9.0, 0.14, 0.7), 'chipping': (10.0, 0.13, 0.7), 'bunker': (9.0, 0.14, 0.7),
    'recovery_play': (7.0, 0.17, 0.7),
    'short_putting': (8.0, 0.17, 0.7), 'lag_putting': (10.0, 0.13, 0.7), 'putting_consistency': (8.0, 0.15, 0.7),
}
EXPERIENCE_KEYS = ('composure', 'resilience', 'management', 'focus', 'green_reading')   # mature with experience
MAINTAIN = 0.30              # share of a year's physical decline that is conditioning (training can win it back)
PROFILE_SD = 0.25            # per-golfer, per-category spread of the decline (log scale, mean factor 1)
PROFILE_CATS = ('physical', 'long_game', 'short_game', 'putting')

_PROFILES = {}


def profile(g):
    """The golfer's own aging factor per category (mean 1): fixed for life, keyed by the person."""
    key = (g.id, g.born)
    p = _PROFILES.get(key)
    if p is None:
        r = random.Random(f'aging-profile:{g.id}:{g.born}')
        p = _PROFILES[key] = {c: math.exp(PROFILE_SD * r.gauss(0.0, 1.0) - PROFILE_SD ** 2 / 2) for c in PROFILE_CATS}
    return p


# ---- 3. the elite tail (dev-3, rules 2026-11-17) ---------------------------------------------------------------------
# Measured on dev-2 (Test3, seed 416342, 55 seasons; and generation over 40 seeds): talent is drawn from a normal
# distribution (sd 13) and the rating scale stops at 99, so the very rare draws far above every other golfer land at
# or near 99 with every skill at 99 (the starting world's Rory Wilson, 98.6 against 90.5; James Garside, potential
# 99, entering at 94.1 at 18 and leading the world by 6-7 for twenty years). The clamp at 99 also ate the youth
# headroom of exactly those draws (their entry level came from the unclamped talent, their potential was cut to 99).
#
# a. Elite tail. Potential above ELITE_KNEE is compressed smoothly towards ELITE_KNEE + ELITE_SPAN:
#        p' = K + S (1 - exp(-(p - K) / S))
#    monotone (a better draw is always better), slope 1 at the knee, unchanged below it. The level moves down by the
#    same amount, so the golfer keeps the growth (or decline) they had for their age. Every generated golfer (the
#    starting world, juniors, new professionals) is treated alike, after every decision the existing rule takes on
#    the entry level (memberships, college or series), so cohorts, identities, paths and nation allocation are
#    unchanged. At K 89, S 6: 90 -> 89.9, 91.8 -> 91.2, 95 -> 92.8, 99 -> 93.9 (asymptote 95).
# b. Prodigy readiness. The 18-year-old floor (READY_FLOOR) grows by PRODIGY_SLOPE per point of potential above
#    PRODIGY_FROM (half at 19, none from 20): a potential-94 teenager keeps at least about 9 points to grow, a
#    potential-88 one about 6, a typical potential-80 one 4.5 as in dev-2. Ordinary juniors are untouched.
# c. Seeded money by standing (finance.MoneyStanding): the starting world's savings, the backers' seeding
#    estimate and fame, and new professionals' savings, follow a golfer's standing in the world's professional pool,
#    not their absolute Overall. Aging is dev-2's, unchanged (no experience taper: owner decision 2026-11-12).
ELITE_KNEE = 89.0
ELITE_SPAN = 6.0
PRODIGY_FROM = 85.0
PRODIGY_SLOPE = 0.5


def elite_potential(pot):
    """The dev-3 potential for a drawn potential (section 3a)."""
    if pot <= ELITE_KNEE:
        return pot
    return ELITE_KNEE + ELITE_SPAN * (1.0 - math.exp(-(pot - ELITE_KNEE) / ELITE_SPAN))


def prodigy_floor(pot, age):
    """The dev-3 readiness floor (section 3b): dev-2's floor plus the prodigy term, both scaled by age."""
    lo, hi = READY_AGES
    share = max(0.0, min(1.0, (hi - age) / (hi - lo)))
    return share * (READY_FLOOR + PRODIGY_SLOPE * max(0.0, pot - PRODIGY_FROM))


def generated_level(cur, pot, age, rules):
    """(entry Overall, potential) for a generated golfer under the world's rules. dev-1: unchanged; dev-2: the
    readiness floor; dev-3: the elite tail, then the readiness floor with the prodigy term on the new scale."""
    if rules in ELITE_RULES:
        new_pot = elite_potential(pot)
        cur = cur - (pot - new_pot)
        return entry_overall(cur, new_pot, age, rules), new_pot
    if rules in READY_RULES:
        return entry_overall(cur, pot, age), pot
    return cur, pot

