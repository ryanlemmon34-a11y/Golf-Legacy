"""Shared statistics scopes (roadmap v14): one definition used by every page that counts events.

**Majors + Premier**: every major and every event of any Premier circuit, by the edition's classification when it
was played (majors are recorded under the MAJORS tour, tier 0; Premier events under their circuit, tier 1) --
not by a golfer's membership. A Challenger member's major and Premier starts belong to it; a Premier member's
regional starts do not. Each edition is recorded under one tour, so the union counts every edition once.
Ratings (Overall) and the world ranking are not event counts: they stay global under any scope.
"""
from __future__ import annotations

from .calendar import TOUR_BY_KEY

MAJORS_PREMIER = 'majors-premier'
LABEL = 'Majors + Premier'
TIERS = (0, 1)


def majors_premier_tours():
    """The tours whose editions make up Majors + Premier (event-time tour keys)."""
    return ('MAJORS',) + tuple(sorted(k for k, t in TOUR_BY_KEY.items() if t.tier == 1))


def in_majors_premier(tier=None, kind=None):
    return kind == 'major' or tier in TIERS


def tours_for(scope):
    """The event-time tours a tour filter value stands for: () for all tours, the union for Majors + Premier,
    else the one tour."""
    if not scope:
        return ()
    if scope == MAJORS_PREMIER:
        return majors_premier_tours()
    return (scope,)
