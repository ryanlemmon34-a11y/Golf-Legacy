"""World population: nations, names, attributes, levels and memberships.

Run from the project folder:  python -m unittest discover -s tests -v
"""
from __future__ import annotations

import statistics as S
import sys
import time
import unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from golfsim.calendar import TOUR_BY_KEY                                     # noqa: E402
from golfsim.geography import CITY_BY_NAME, COUNTRIES                        # noqa: E402
from golfsim.golfer import overall_rating                                    # noqa: E402
from golfsim.names import FAMOUS, NATION_BANKS                               # noqa: E402
from golfsim.nations import NATIONS, REAL_TOP200, nations                    # noqa: E402
from golfsim.population import (MEMBERS_PER_FIELD, PREMIER_MEMBERS, age_deficit,  # noqa: E402
                                candidates, generate_world, level_of)
from golfsim.ratings import ATTRIBUTE_KEYS, PERSONALITY_KEYS                 # noqa: E402

T0 = time.perf_counter()
WORLD = generate_world()
GEN_SECONDS = time.perf_counter() - T0


class PopulationTests(unittest.TestCase):
    def test_fast_and_deterministic(self):
        self.assertLess(GEN_SECONDS, 15)
        other = generate_world()
        self.assertEqual([g.name for g in other.golfers[:200]], [g.name for g in WORLD.golfers[:200]])
        self.assertEqual(other.golfers[50].attrs, WORLD.golfers[50].attrs)
        self.assertNotEqual([g.name for g in generate_world(seed=99).golfers[:50]], [g.name for g in WORLD.golfers[:50]])

    def test_every_golfer_is_complete_and_valid(self):
        names = set()
        for g in WORLD.golfers:
            self.assertIn(g.country, COUNTRIES)
            self.assertEqual(CITY_BY_NAME[g.hometown].country, g.country)
            self.assertEqual(set(g.attrs), set(ATTRIBUTE_KEYS))
            self.assertEqual(set(g.personality), set(PERSONALITY_KEYS))
            self.assertTrue(all(1 <= v <= 99 for v in g.attrs.values()))
            self.assertGreaterEqual(g.potential + 0.05, g.overall)
            self.assertIn(g.status, ('pro', 'amateur', 'club_pro'))
            self.assertTrue(18 <= g.age(WORLD.year) <= 62)
            self.assertNotIn(g.name.lower(), FAMOUS)
            names.add(g.name)
        self.assertEqual(len(names), len(WORLD.golfers))
        self.assertEqual(set(NATION_BANKS), set(COUNTRIES))
        self.assertEqual(set(NATIONS), set(COUNTRIES))

    def test_size_and_level_ladder(self):
        self.assertTrue(4500 <= len(WORLD.golfers) <= 8000, len(WORLD.golfers))
        mean = {lv: S.mean(g.overall for g in WORLD.golfers if level_of(g) == lv)
                for lv in ('Premier Tour', 'Challenger', 'Regional', 'Mini tour', 'College', 'Amateur')}
        self.assertGreater(mean['Premier Tour'], mean['Challenger'] + 6)
        self.assertGreater(mean['Challenger'], mean['Regional'] + 5)
        self.assertGreater(mean['Mini tour'], mean['College'])
        self.assertGreater(mean['College'], mean['Amateur'])
        self.assertTrue(71 <= mean['Premier Tour'] <= 80)
        pros = WORLD.ranked(WORLD.pros())
        self.assertTrue(68 <= pros[299].overall <= 76)

    def test_no_ceiling_eras_vary(self):
        """Nothing caps the best players: some worlds have a weak era, some a golden one."""
        tops = []
        for seed in range(10):
            pros = [r for r in candidates(2027, 500 + seed, nations()) if r[5] == 'pro']
            tops.append(pros[0][4])
        self.assertTrue(89 <= S.median(tops) <= 96, tops)
        self.assertGreater(max(tops) - min(tops), 3, tops)

    def test_memberships(self):
        members = Counter(g.tour for g in WORLD.golfers)
        self.assertEqual(sum(n for t, n in members.items() if t.startswith('PT_')), PREMIER_MEMBERS)
        for key, t in TOUR_BY_KEY.items():
            if t.tier in (2, 3):
                self.assertLessEqual(members[key], round(t.field * MEMBERS_PER_FIELD), key)
        for g in WORLD.golfers:
            t = TOUR_BY_KEY.get(g.tour)
            if g.status == 'pro':
                self.assertTrue(t and t.tier <= 4, g)
            elif g.status == 'amateur':
                self.assertTrue(t and t.tier in (5, 6), g)
                if t.tier == 5:
                    self.assertLessEqual(g.age(WORLD.year), 22)
            if g.tour == 'CH_JAPAN':
                self.assertIn(g.country, ('Japan', 'South Korea'))
        # the best players gather on the strongest circuit
        top = WORLD.ranked(WORLD.pros())[:60]
        self.assertGreater(sum(g.tour == 'PT_AMERICAS' for g in top), 50)
        d1 = [g for g in WORLD.golfers if g.tour == 'CO_US_D1']
        self.assertGreater(sum(g.country != 'USA' for g in d1), 20)       # international college pathway

    def test_nations_match_the_real_world_ranking(self):
        tot = Counter()
        for s in range(6):
            c = candidates(2027, 7000 + s, nations())
            tot.update(r[0] for r in [r for r in c if r[5] == 'pro'][:200])
        avg = {c: n / 6 for c, n in tot.items()}
        self.assertTrue(65 <= avg['USA'] <= 90, avg['USA'])
        for country in ('England', 'Japan', 'Australia', 'South Africa', 'South Korea'):
            self.assertTrue(5 <= avg.get(country, 0) <= 20, (country, avg.get(country)))
        # every country with real top-200 players produces some; minnows rarely do
        self.assertLess(sum(avg.get(c, 0) for c in COUNTRIES if c not in REAL_TOP200), 6)

    def test_age_profile(self):
        top = WORLD.ranked(WORLD.pros())[:200]
        self.assertTrue(29 <= S.mean(g.age(WORLD.year) for g in top) <= 34)
        self.assertGreater(age_deficit(18, 27), age_deficit(23, 27))
        self.assertEqual(age_deficit(30, 27), 0)
        self.assertGreater(age_deficit(50, 27), age_deficit(42, 27))
        self.assertGreater(age_deficit(48, 27, aging_rate=1.5), age_deficit(48, 27, aging_rate=0.7))
        young = [g for g in WORLD.pros() if g.age(WORLD.year) <= 24]
        old = [g for g in WORLD.pros() if g.age(WORLD.year) >= 42]
        rel = lambda gs, k: S.mean(g.attrs[k] - g.overall for g in gs)
        self.assertGreater(rel(young, 'power'), rel(old, 'power') + 4)        # strength fades first
        self.assertGreater(rel(old, 'composure'), rel(young, 'composure') + 3)  # experience grows

    def test_styles_shape_attributes(self):
        rel = lambda country, k: S.mean(g.attrs[k] - g.overall for g in WORLD.golfers if g.country == country)
        self.assertGreater(rel('USA', 'power'), rel('Japan', 'power') + 4)
        self.assertGreater(rel('Scotland', 'ball_flight'), rel('USA', 'ball_flight') + 2)
        self.assertGreater(rel('Spain', 'chipping'), rel('Germany', 'chipping') + 2)

    def test_overall_is_exact(self):
        for g in WORLD.golfers[::97]:
            self.assertAlmostEqual(overall_rating(g.attrs), g.overall, places=6)


if __name__ == '__main__':
    unittest.main()
