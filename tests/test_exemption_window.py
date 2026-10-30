"""The USA Open champions' place (route U1, "USA Open champions, last 10 years"): a champion of year Y is exempt
from the Y+1 through the Y+10 USA Open and not in Y+11 (unless they win again); the evidence a place shows agrees
with the place itself; and the routes that count the current year keep their window.

Run from the project folder:  python -m unittest tests.test_exemption_window -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from golfsim import qualification as Q                                    # noqa: E402


class Ctx:
    """The facts winners_of and evidence read: who won which edition."""

    def __init__(self, wins):
        self.wins = dict(wins)                                            # {(series, year): golfer}
        self.results = {k: True for k in self.wins}
        self.tour_of = {}

    def winner(self, sid, year):
        return self.wins.get((sid, year))

    def edition_week(self, sid, year):
        return 25


def route(code, version='v2', major='USA_OPEN'):
    return next(r for r in Q.rules_for(version)[major] if r.code == code)


class USAOpenChampions(unittest.TestCase):
    def test_a_champion_holds_the_place_through_the_tenth_anniversary(self):
        for version in ('v1', 'v2'):
            u1 = route('U1', version)
            ctx = Ctx({('USA_OPEN', 2040): 7})
            self.assertNotIn(7, u1.select(ctx, 2040), version)            # (their own year: they are the champion)
            for y in range(2041, 2051):                                   # Y+1 .. Y+10
                self.assertIn(7, u1.select(ctx, y), (version, y))
            self.assertNotIn(7, u1.select(ctx, 2051), version)            # Y+11: expired
            self.assertNotIn(7, u1.select(ctx, 2060), version)

    def test_a_new_win_renews_the_place(self):
        u1 = route('U1')
        ctx = Ctx({('USA_OPEN', 2040): 7, ('USA_OPEN', 2048): 7, ('USA_OPEN', 2049): 9})
        for y in range(2049, 2059):                                       # through 2048 + 10
            self.assertIn(7, u1.select(ctx, y), y)
        self.assertNotIn(7, u1.select(ctx, 2059))
        self.assertEqual(u1.select(ctx, 2050), [9, 7])                    # newest champion first, each once

    def test_the_evidence_names_the_win_behind_the_place(self):
        u1 = route('U1')
        ctx = Ctx({('USA_OPEN', 2040): 7})
        self.assertEqual(Q.evidence(u1, 7, 2050, ctx), [('2040:USA_OPEN (won)', (2040, 25))])   # the tenth year
        self.assertEqual(Q.evidence(u1, 7, 2051, ctx), [])

    def test_routes_that_count_the_current_year_keep_their_window(self):
        u5 = route('U5')                                                  # other majors' champions, last 5 years
        sids = sorted(Q.OTHER_MAJORS['USA_OPEN'])
        ctx = Ctx({(sids[0], 2045): 3, (sids[0], 2040): 4, (sids[0], 2039): 5})
        got = u5.select(ctx, 2045)
        self.assertEqual(got, [3, 4])                                     # this year's (already played) back to 2040
        self.assertNotIn(5, got)


if __name__ == '__main__':
    unittest.main()
