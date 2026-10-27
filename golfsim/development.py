"""Player development: how golfers improve, peak and decline.

Every attribute has a hidden **ceiling** (the most it can reach; together they make the golfer's
potential). Each week a golfer does one thing, and it moves their attributes toward their ceilings:

    train a category   the category's attributes grow fastest (physical, long game, short game,
                       putting or mental); coachability makes training count for more
    play a tournament  every skill grows a little, the mental game most; the further a golfer is from
                       their potential (the more raw), the more a tournament teaches them
    rest               no skill growth, but fatigue recovers fully

Growth is proportional to the gap to the ceiling, times a learning rate that is highest in the
teens and falls with age, times work ethic. Young golfers also mature physically on their own, every
week, whatever they are doing (resting and working included): growing up does not need golf.

Golfers do not know their ceilings. Their decisions (what to train, whether a tournament or a training
week helps them more) use a *perceived* gap: the real gap seen through a persistent personal misreading
that is larger for golfers with poor judgement of their own game (management and coachability).

Once a year golfers age: strength and stamina fade first (from a few years after their prime), then
technique; the mental game keeps maturing with experience into the late forties — which is why a
journeyman can be a better competitor at 34 than at 24. Serious injuries can take some strength,
stamina and injury resistance away for good.
"""
from __future__ import annotations

import math
import random

from .golfer import OVERALL_WEIGHTS, overall_rating
from .ratings import ATTRIBUTE_KEYS

CATEGORIES = {
    'physical': ('power', 'stamina', 'recovery_rate', 'injury_resistance'),
    'long_game': ('driving_accuracy', 'long_irons', 'mid_irons', 'ball_flight', 'striking_consistency'),
    'short_game': ('wedges', 'chipping', 'bunker', 'recovery_play'),
    'putting': ('short_putting', 'lag_putting', 'green_reading', 'putting_consistency'),
    'mental': ('composure', 'resilience', 'management', 'focus'),
}
CATEGORY_OF = {k: c for c, ks in CATEGORIES.items() for k in ks}
assert set(CATEGORY_OF) == set(ATTRIBUTE_KEYS)

BASE_TRAIN = 0.016          # share of the gap closed per week of training (before learning rate)
BASE_PLAY = 0.008           # per tournament (four rounds), on every non-physical attribute
MENTAL_PLAY = 1.6           # competition teaches the mental game most
MENTAL_TRAIN = 0.6          # the mental game is harder to train away from competition
MATURING = 0.004            # physical growth per week for teenagers, without training


def learning_rate(age):
    """How quickly a golfer learns at this age (1.2 in the teens, 0.6 at 30, 0.25 at 40)."""
    pts = ((18, 1.2), (21, 1.15), (25, 0.9), (30, 0.6), (35, 0.4), (40, 0.25), (50, 0.1), (70, 0.05))
    if age <= pts[0][0]:
        return pts[0][1]
    for (a0, r0), (a1, r1) in zip(pts, pts[1:]):
        if age <= a1:
            return r0 + (r1 - r0) * (age - a0) / (a1 - a0)
    return pts[-1][1]


def init_ceilings(g, age, rng):
    """Spread the gap between a golfer's overall and potential over their attributes."""
    gap = max(0.0, g.potential - g.overall)
    young = max(0.0, 26 - age) / 8
    ceil = {}
    for k in ATTRIBUTE_KEYS:
        cat = CATEGORY_OF[k]
        mult = 1.0 + (0.4 * young if cat == 'physical' else 0) + (0.3 if cat == 'mental' else 0)
        ceil[k] = min(99.0, g.attrs[k] + gap * mult * math.exp(rng.gauss(0, 0.35)))
    # keep the ceilings' overall close to the golfer's potential
    for _ in range(4):
        over = overall_rating(ceil) - max(g.potential, g.overall)
        if abs(over) < 0.05:
            break
        ceil = {k: max(g.attrs[k], min(99.0, v - over)) for k, v in ceil.items()}
    g.ceilings = {k: round(v, 2) for k, v in ceil.items()}


def coach_multiplier(quality):
    """How much a week of training counts for, by coaching quality (0-1; teaching yourself = 0.3).
    Golfers who teach themselves keep the 1.0 the world's development rates were calibrated on (the
    calibration predates coaches, so it describes a typical golfer's own practice); a coach adds to
    it: an ordinary coach about +10%, a strong specialist in their speciality or a youth specialist
    with a teenager about +30%. A weak coach is no worse than none."""
    return 1.0 + 0.5 * max(0.0, quality - 0.3)


def develop_week(g, activity, age, category=None, rounds=0.0, coach=0.3, scale=1.0):
    """Apply one week of development. activity: 'train', 'play' or 'rest' (a paid work week counts as
    rest). `scale` shrinks training for golfers with a full-time job. Returns overall gained."""
    before = g.overall
    a, c = g.attrs, g.ceilings
    if age < 23:                                  # still growing into their body, whatever the week
        for k in CATEGORIES['physical']:
            gap = c[k] - a[k]
            if gap > 0:
                a[k] = min(99.0, a[k] + MATURING * gap)
    if activity == 'rest':
        return g.overall - before
    lr = learning_rate(age) * (0.5 + g.personality['work_ethic'] / 100) * scale
    if activity == 'train' and category:
        k_train = BASE_TRAIN * lr * (0.6 + 0.8 * g.personality['coachability'] / 100) * coach_multiplier(coach)
        if category == 'mental':
            k_train *= MENTAL_TRAIN
        for k in CATEGORIES[category]:
            gap = c[k] - a[k]
            if gap > 0:
                a[k] = min(99.0, a[k] + k_train * gap)
    elif activity == 'play' and rounds:
        k_play = BASE_PLAY * lr * min(1.0, rounds / 4)
        for k, cat in CATEGORY_OF.items():
            if cat == 'physical':
                continue
            gap = c[k] - a[k]
            if gap > 0:
                a[k] = min(99.0, a[k] + k_play * gap * (MENTAL_PLAY if cat == 'mental' else 1.0))
    return g.overall - before


def judgement(g):
    """How well a golfer reads their own game (0-1)."""
    return (g.attrs['management'] + g.personality['coachability']) / 200


_SELF_VIEW = {}


def perceived_gap(g, k, insight=0.0):
    """The room a golfer *believes* attribute k has left: the true gap seen through a persistent personal
    misreading (fixed per golfer and attribute; wider for poor judges of their own game). A coach's
    `insight` (their teaching skill, 0-1) narrows it when it is better than the golfer's own judgement."""
    z = _SELF_VIEW.get((g.id, k))
    if z is None:
        z = _SELF_VIEW[(g.id, k)] = random.Random(f'{g.id}:{k}:selfview').gauss(0, 1)
    sd = 2.0 + 6.0 * (1 - max(judgement(g), insight))
    return max(0.0, g.ceilings[k] - g.attrs[k] + sd * z)


def development_value(g, activity, age, category=None, insight=0.0, coach=0.3):
    """Overall a golfer expects to gain this week from an activity, from their own (imperfect) view of
    their game (used by the planner)."""
    lr = learning_rate(age) * (0.5 + g.personality['work_ethic'] / 100)
    gain = 0.0
    total_w = sum(OVERALL_WEIGHTS.values())
    if activity == 'train' and category:
        k_train = BASE_TRAIN * lr * (0.6 + 0.8 * g.personality['coachability'] / 100) * coach_multiplier(coach)
        if category == 'mental':
            k_train *= MENTAL_TRAIN
        for k in CATEGORIES[category]:
            gain += OVERALL_WEIGHTS[k] * k_train * perceived_gap(g, k, insight)
    elif activity == 'play':
        k_play = BASE_PLAY * lr
        for k, cat in CATEGORY_OF.items():
            if cat != 'physical':
                gain += OVERALL_WEIGHTS[k] * k_play * perceived_gap(g, k, insight) * (
                    MENTAL_PLAY if cat == 'mental' else 1.0)
    return gain / total_w


def choose_category(g, rng, insight=0.0):
    """What to train: the category with the most to gain (weighted by what matters for scoring).
    Good course managers and coachable golfers read their game better; others guess more."""
    scores = {}
    for cat, ks in CATEGORIES.items():
        gain = sum(OVERALL_WEIGHTS[k] * perceived_gap(g, k, insight) for k in ks)
        if cat == 'mental':
            gain *= MENTAL_TRAIN
        scores[cat] = gain
    noise = 0.25 + 0.75 * (1 - max(judgement(g), insight))
    top = max(scores.values()) or 1.0
    return max(scores, key=lambda c: scores[c] / top + rng.gauss(0, noise))


def age_year(g, age, rng):
    """One year older: physical decline after the prime, then technique; mental growth with experience."""
    a, c = g.attrs, g.ceilings
    rate = g.aging_rate
    x_phys = age - (g.peak_age + 3)
    x_tech = age - (g.peak_age + 8)
    for k, cat in CATEGORY_OF.items():
        d = 0.0
        if cat == 'physical' and x_phys > 0:
            d = -0.30 * rate * x_phys ** 0.7
        elif cat in ('long_game', 'short_game', 'putting') and x_tech > 0:
            d = -0.15 * rate * x_tech ** 0.7
        elif cat == 'mental' or k == 'green_reading':
            if age < 48:
                d = 0.35 * (0.6 + 0.8 * rng.random()) * (1.0 if cat == 'mental' else 0.5)
            elif age > 55:
                d = -0.2 * (age - 55) ** 0.7
        if d:
            a[k] = max(1.0, min(99.0, a[k] + d))
            c[k] = max(1.0, min(99.0, c[k] + d))
            if a[k] > c[k]:
                c[k] = a[k]


def serious_injury(g, weeks, rng):
    """A long injury (10+ weeks) can cost some strength, stamina and resilience to injury for good: the
    longer it is, the likelier (about 15% at 10 weeks, 60% at 20, 85% at 30)."""
    if weeks < 10 or rng.random() > 1 - math.exp(-(weeks - 8) / 12):
        return {}
    lost = {}
    for k in ('power', 'stamina', 'injury_resistance'):
        d = rng.uniform(0.3, 1.0) * min(4.0, weeks / 8)
        g.attrs[k] = max(1.0, g.attrs[k] - d)
        g.ceilings[k] = max(g.attrs[k], g.ceilings[k] - d)
        lost[k] = round(d, 1)
    return lost
