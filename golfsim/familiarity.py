"""Course familiarity and its regional baseline (rules 2026-11-08; docs/FAMILIARITY_AND_AGGRESSION.md).

Familiarity is competitive rounds played on a course (any layout: `Course.familiarity_key`), kept on the
golfer and the caddie. The engine turns rounds into a 0..1 value, `value(rounds) = 1 - exp(-rounds / 15)`,
which gives small, bounded help: steadier decisions, slightly closer approaches and better reads.

Regional baseline
    A golfer knows the courses where they come from and where they live a little before ever playing them in
    competition. For a course in the same state / province (or equivalent) as the golfer's birthplace or
    current residence, the engine plays as if they had at least REGION_ROUNDS rounds there; where the
    state / province is unknown on either side (a birthplace recorded by country only, a course outside the
    geography), the same country gives COUNTRY_ROUNDS. It is a floor, never added on top: effective rounds
    are max(rounds played, baseline), so real experience always counts in full and the baseline never gives
    more than a few real rounds would. Birthplace and residence are matched separately and the larger match
    is used once: living where one was born counts once, not twice. There is no other home advantage.
    People whose places were never recorded (legacy) get no baseline. The record of rounds played is never
    changed by the baseline: it only changes what the engine is given for that start.
"""
from __future__ import annotations

import math

SCALE = 15.0               # rounds for familiarity to reach 1 - 1/e (the engine's curve)
REGION_ROUNDS = 3.0        # baseline for a course in the golfer's own state / province (value about 0.18)
COUNTRY_ROUNDS = 1.5       # same country where the state / province is unknown on either side (about 0.10)


def value(rounds):
    """Familiarity (0..1) from competitive rounds on a course, as the engine uses it."""
    return 1 - math.exp(-max(0.0, rounds) / SCALE)


def baseline(course_place, places):
    """(rounds, basis) of the regional baseline for a course at `course_place` (country, subdivision or None)
    for a person whose places (birthplace, residence; each (country, subdivision or None) or None) are given.
    basis: 'region' (same state / province), 'country' (same country, subdivision unknown on a side) or None.
    Identical places count once; the larger match is used, never a sum."""
    if not course_place or not course_place[0]:
        return 0.0, None
    best = (0.0, None)
    seen = []
    for p in places:
        if not p or not p[0] or p in seen:
            continue
        seen.append(p)
        if p[0] != course_place[0]:
            continue
        if p[1] and course_place[1]:
            if p[1] != course_place[1]:
                continue
            cand = (REGION_ROUNDS, 'region')
        else:
            cand = (COUNTRY_ROUNDS, 'country')
        if cand[0] > best[0]:
            best = cand
    return best


def effective_rounds(played, base_rounds):
    """What the engine is given: rounds played, or the baseline if that is more (a floor, never a sum)."""
    return max(played or 0.0, base_rounds or 0.0)


def top_courses(familiarity, n=10):
    """The n courses a golfer has played most: [(course key, rounds)], most first, ties by key (stable)."""
    rows = [(k, r) for k, r in familiarity.items() if r and r > 0]
    rows.sort(key=lambda x: (-x[1], str(x[0])))
    return rows[:n]
