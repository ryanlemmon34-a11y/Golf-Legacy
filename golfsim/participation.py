"""National prestige and each nation's share of the yearly new-golfer cohorts (rules 2026-11-05; owner decision D7).

No extra golfers because of prestige. How many golfers each pathway creates in a year is the existing rule's
number from the nation profiles the world began with (population.entrant_rows); national prestige only moves
how that fixed number is SHARED between nations. A successful nation gains share at the others' expense; the
total is never more or less. Only future entrants are affected: nobody's nationality ever changes, and no
nation's pool, development or any talent parameter is read or changed here (a nation's entrants are drawn from
its own unchanged distribution, so a larger share means more golfers from it, never better ones).

National prestige (0-100; 50 = exactly as expected)
    Every completed start in an event that counts for fame (not qualifying stages) earns the golfer the event's
    fame points (prestige.fame_points: the event's prestige cubed times the finish's share), so a major counts
    far more than a mini-tour event. Before each event a nation's golfers are EXPECTED to take a part of the
    fame the event hands out, from what is known at the time -- who entered and how good they are then:
        expected share of a golfer = (1 - EXPECT_SKILL) / field size + EXPECT_SKILL x softmax(Overall / EXPECT_TAU)
    (half for being in the field, half by current ability: a favourite who wins earns something, an outsider
    who wins earns much more). Per season and nation: actual fame A, expected fame E (they total the same
    over all nations, so national prestige is zero-sum). Over the last five completed seasons, weighted
    1.0, 0.9, 0.8, 0.7, 0.6 by age (fewer seasons while the world is young):
        R = (A5 + NATION_PSEUDO) / (E5 + NATION_PSEUDO)       (the pseudo-count steadies small samples)
        prestige = 50 + 25 x log2(R), within 0-100     (twice the expected success = 75, half = 25)

Participation multiplier and shares
    target  = MULT_MAX ^ ((prestige - 50) / 50)       0.25 at prestige 0, 1 at 50, 2 at 75, 4 at 100
    m(next) = the target, but at most MULT_STEP times (or 1/MULT_STEP of) this year's multiplier
    share of a nation in a pathway = its starting share x m, normalised so all nations total 100 %.
    Starting shares: each nation's expected share of the golfers the existing rule creates in that pathway
    (population.expected_shares), fixed when the world began. Entrants of season Y+1 use the prestige of the
    seasons through Y (decided at Y's end).

Long-term bounds: a nation's multiplier stays within 0.25-4 of its starting value, and moves at most 10 % a
year, so going from 1 to 4 (or 0.25) takes at least 15 years of sustained prestige 100 (or 0). Because shares
are normalised, a small nation's share relative to its start can reach up to 4 / (the world's average
multiplier): 16 times its starting share if every other nation sat at 0.25, about 4 times when the rest of
the world stays near 1 -- and down to about a quarter (as little as 1/16) the other way. Sustained prestige
75 (twice the expected success for five years) holds a nation at 2x.
"""
from __future__ import annotations

import math
from dataclasses import replace

from .population import PATHWAYS, expected_counts, normalised

# ---- PROPOSED calibration (rules 2026-11-05): national prestige and participation --------------------------------
# Starting values to measure, not proven ones (docs/WORLD_PRESTIGE_PACKAGE.md).
NATION_YEARS = 5                         # completed seasons in a nation's window
NATION_WEIGHTS = (1.0, 0.9, 0.8, 0.7, 0.6)   # by age (the season just completed first), as event prestige
NATION_PSEUDO = 150.0                    # fame points of "as expected" added to A5 and E5 (a major win at
                                         # prestige ~95 is ~86): a small nation needs real success to move far
EXPECT_SKILL = 0.5                       # how much of the expectation comes from ability (the rest: being entered)
EXPECT_TAU = 4.0                         # Overall points per e-fold of a golfer's ability share (softmax)
MULT_MIN, MULT_MAX = 0.25, 4.0           # the multiplier's level bounds (prestige 0 and 100)
MULT_STEP = 1.10                         # most it moves in a year: x 1.10 or / 1.10


def expected_by_golfer(values, overalls):
    """Expected fame of each starter of one event site (lists in the same order), given the fame the site
    actually handed out (the sum of `values`) and each starter's Overall at the time."""
    n = len(values)
    total = sum(values)
    if n == 0 or total <= 0:
        return [0.0] * n
    top = max(overalls)
    soft = [math.exp((o - top) / EXPECT_TAU) for o in overalls]
    s = sum(soft)
    return [total * ((1 - EXPECT_SKILL) / n + EXPECT_SKILL * x / s) for x in soft]


def nation_prestige(seasons):
    """(prestige 0-100, R) from up to NATION_YEARS seasons [(actual, expected)], the latest first."""
    a = sum(w * x[0] for w, x in zip(NATION_WEIGHTS, seasons))
    e = sum(w * x[1] for w, x in zip(NATION_WEIGHTS, seasons))
    r = (a + NATION_PSEUDO) / (e + NATION_PSEUDO)
    return max(0.0, min(100.0, 50 + 25 * math.log2(r))), r


def target_multiplier(prestige):
    return max(MULT_MIN, min(MULT_MAX, MULT_MAX ** ((prestige - 50) / 50)))


def next_multiplier(current, prestige):
    t = target_multiplier(prestige)
    return max(current / MULT_STEP, min(current * MULT_STEP, t))


class Participation:
    """A world's national prestige, participation multipliers and cohort shares (kept with the Season)."""

    def __init__(self, nations, first_year):
        self.first_year = first_year
        # the nation profiles the world began with: the cohorts' totals and the starting shares come from these
        self.baseline = {c: replace(p, history=[]) for c, p in nations.items()}
        self.base_expected = {k: expected_counts(k, self.baseline) for k in PATHWAYS}
        self.base_share = {k: normalised(v) for k, v in self.base_expected.items()}
        self.prestige = {c: 50.0 for c in nations}
        self.ratio = {c: 1.0 for c in nations}
        self.multiplier = {c: 1.0 for c in nations}
        self.success = {}                    # season -> {country: [actual fame, expected fame]}
        self.history = {}                    # entrant season -> what decided its shares, and its allocations
        self.closed = None                   # the last season whose prestige was settled

    # -- evidence ---------------------------------------------------------------------------------------------
    def note_site(self, year, rows):
        """One event site's starters: rows [(country, Overall at the time, fame points earned)]."""
        if not rows:
            return
        exp = expected_by_golfer([v for _, _, v in rows], [o for _, o, _ in rows])
        book = self.success.setdefault(year, {})
        for (c, _, v), e in zip(rows, exp):
            s = book.get(c)
            if s is None:
                s = book[c] = [0.0, 0.0]
            s[0] += v
            s[1] += e

    # -- the season's end ---------------------------------------------------------------------------------------
    def close_season(self, year):
        """Settle national prestige through `year` and the multipliers and shares for season year+1's entrants
        (once per season)."""
        if self.closed is not None and year <= self.closed:
            return
        self.closed = year
        for c in self.baseline:
            seasons = [self.success.get(year - k, {}).get(c, (0.0, 0.0)) for k in range(NATION_YEARS)
                       if year - k >= self.first_year]
            self.prestige[c], self.ratio[c] = nation_prestige(seasons)
            self.multiplier[c] = next_multiplier(self.multiplier[c], self.prestige[c])
        book = self.success.get(year, {})
        self.history[year + 1] = {
            'decided': year,
            'prestige': {c: round(v, 2) for c, v in self.prestige.items()},
            'ratio': {c: round(v, 4) for c, v in self.ratio.items()},
            'multiplier': {c: round(v, 4) for c, v in self.multiplier.items()},
            'shares': {k: {c: round(v, 6) for c, v in self.shares(k).items()} for k in PATHWAYS},
            'season': {c: [round(a, 2), round(e, 2)] for c, (a, e) in sorted(book.items())},
            'totals': {}, 'allocated': {}, 'existing': {}}
        for y in [y for y in self.success if y <= year - NATION_YEARS]:
            del self.success[y]
        for y in [y for y in self.history if y <= year - NATION_YEARS]:
            del self.history[y]

    def shares(self, kind):
        """{country: share of the pathway's golfers} now: starting share x multiplier, normalised to 1."""
        base = self.base_share[kind]
        return normalised({c: base[c] * self.multiplier[c] for c in base})

    def record(self, year, kind, report):
        """What a pathway created for season `year` (population.entrant_rows' report)."""
        h = self.history.setdefault(year, {'decided': None, 'totals': {}, 'allocated': {}, 'existing': {}})
        h['totals'][kind] = report['total']
        h['allocated'][kind] = dict(report['allocated'])
        h['existing'][kind] = dict(report['existing'])

    def starting_table(self):
        """[(country, juniors share, new professionals share, expected juniors, expected new professionals)],
        largest junior share first."""
        rows = [(c, self.base_share['juniors'][c], self.base_share['new_pros'][c],
                 self.base_expected['juniors'][c], self.base_expected['new_pros'][c]) for c in self.baseline]
        return sorted(rows, key=lambda r: (-r[1], r[0]))

    def view(self):
        """Plain data for the observer and the archive: the state as it stands."""
        return {'prestige': {c: round(v, 2) for c, v in self.prestige.items()},
                'ratio': {c: round(v, 4) for c, v in self.ratio.items()},
                'multiplier': {c: round(v, 4) for c, v in self.multiplier.items()},
                'shares': {k: {c: round(v, 6) for c, v in self.shares(k).items()} for k in PATHWAYS},
                'baseline_shares': {k: {c: round(v, 6) for c, v in self.base_share[k].items()} for k in PATHWAYS},
                'closed': self.closed}
