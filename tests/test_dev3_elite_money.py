"""Development rules dev-3 (golfsim/realism.py section 3; rules 2026-11-17): the elite tail, prodigy readiness and
seeded money by standing in the professional pool (finance.MoneyStanding). Earlier worlds keep dev-1 / dev-2."""
from __future__ import annotations

import copy
import math
import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from golfsim import development as D                                   # noqa: E402
from golfsim import finance as FIN                                     # noqa: E402
from golfsim import population as P                                    # noqa: E402
from golfsim import realism as RZ                                      # noqa: E402
from golfsim.golfer import Golfer                                      # noqa: E402
from golfsim.nations import nations as starting_nations                # noqa: E402
from golfsim.ratings import ATTRIBUTE_KEYS                             # noqa: E402


def golfer(rating, status='pro', lifestyle='full_time', gid=1, born=1995):
    g = Golfer(f'G{gid}', {k: float(rating) for k in ATTRIBUTE_KEYS}, id=gid, born=born, status=status)
    g.lifestyle = lifestyle
    return g


class Versions(unittest.TestCase):
    def test_new_worlds_are_dev3_and_earlier_versions_keep_their_families(self):
        self.assertEqual(RZ.CURRENT, RZ.DEV3)
        self.assertEqual(P.generate_world(seed=5, scale=0.02).dev_rules, RZ.DEV3)
        self.assertIn(RZ.DEV2, RZ.ATTRIBUTE_AGING)              # dev-2 must not fall back to dev-1 aging now that it
        self.assertIn(RZ.DEV2, RZ.READY_RULES)                  # is no longer CURRENT
        self.assertNotIn(RZ.DEV2, RZ.ELITE_RULES)
        self.assertNotIn(RZ.LEGACY, RZ.ATTRIBUTE_AGING + RZ.READY_RULES + RZ.ELITE_RULES)

    def test_dev2_world_ages_with_dev2_rules_not_dev1(self):
        def run(rules):
            g = golfer(80, gid=7)
            g.ceilings = dict(g.attrs)
            g.peak_age, g.aging_rate = 27.0, 1.0
            for age in range(30, 50):
                D.age_year(g, age, random.Random(age), 1.0, rules=rules)
            return g.attrs
        self.assertNotEqual(run(RZ.DEV2), run(RZ.LEGACY))
        self.assertEqual(run(RZ.DEV2), run(RZ.DEV3))           # no experience taper: dev-3 ages exactly as dev-2


class EliteTail(unittest.TestCase):
    def test_compression_is_identity_below_the_knee_monotone_and_bounded(self):
        self.assertEqual(RZ.elite_potential(RZ.ELITE_KNEE), RZ.ELITE_KNEE)
        self.assertEqual(RZ.elite_potential(70.0), 70.0)
        xs = [RZ.ELITE_KNEE + i * 0.05 for i in range(400)]
        ys = [RZ.elite_potential(x) for x in xs]
        self.assertTrue(all(b > a for a, b in zip(ys, ys[1:])))                        # a better talent stays better
        self.assertLess(max(ys), RZ.ELITE_KNEE + RZ.ELITE_SPAN)
        self.assertAlmostEqual((RZ.elite_potential(RZ.ELITE_KNEE + 1e-4) - RZ.ELITE_KNEE) / 1e-4, 1.0, places=3)
        self.assertAlmostEqual(RZ.elite_potential(99.0), 93.87, places=2)

    def test_prodigy_floor(self):
        for pot in (60, 80, 85):
            self.assertEqual(RZ.prodigy_floor(pot, 18), RZ.ready_floor(18))            # ordinary juniors: dev-2's
        self.assertAlmostEqual(RZ.prodigy_floor(94, 18), 9.0)
        self.assertAlmostEqual(RZ.prodigy_floor(94, 19), 4.5)
        self.assertEqual(RZ.prodigy_floor(94, 20), 0.0)
        self.assertEqual(RZ.generated_level(70.0, 80.0, 30, RZ.DEV3), (70.0, 80.0))     # adults below the knee
        self.assertEqual(RZ.generated_level(70.0, 99.0, 25, RZ.DEV2), (70.0, 99.0))     # dev-2: no elite tail

    def test_junior_classes_keep_every_golfer_and_path(self):
        nations = starting_nations()
        seen_elite = 0
        for seed, year in ((416342, 2040), (11, 2044), (7, 2031), (386509, 2036)):
            a = P.junior_class(year, seed, nations, 1, set(), rules=RZ.DEV2)
            b = P.junior_class(year, seed, nations, 1, set(), rules=RZ.DEV3)
            key = lambda g: (g.id, g.name, g.country, g.born, g.peak_age, g.aging_rate, g.archetype, g.tour,
                             g.status, tuple(sorted(g.personality.items())))
            self.assertEqual([key(g) for g in a], [key(g) for g in b], (seed, year))
            for x, y in zip(a, b):
                if x.potential <= RZ.ELITE_KNEE:
                    self.assertEqual(x.potential, y.potential)
                else:
                    seen_elite += 1
                    self.assertLess(y.potential, x.potential)
                self.assertLessEqual(y.overall, x.overall + 0.15)
                floor = RZ.prodigy_floor(y.potential, 18)
                self.assertGreater(y.potential - y.overall, floor - 1.0)     # (softplus: never far below the floor)
            na = P.new_professionals(year, seed, nations, 1, set(), rules=RZ.DEV2)
            nb = P.new_professionals(year, seed, nations, 1, set(), rules=RZ.DEV3)
            self.assertEqual([key(g) for g in na], [key(g) for g in nb])
        self.assertGreater(seen_elite, 0)

    def test_james_garside_class(self):
        """Seed 416342, 2040 (Test3's James Garside entered at 94.11 with potential 99): dev-3 keeps him the class's
        best potential but enters him with room to grow."""
        nations = starting_nations()
        a = P.junior_class(2040, 416342, nations, 1, set(), rules=RZ.DEV2)
        b = P.junior_class(2040, 416342, nations, 1, set(), rules=RZ.DEV3)
        top_a = max(a, key=lambda g: g.potential)
        top_b = next(g for g in b if g.id == top_a.id)
        self.assertEqual(top_b.id, max(b, key=lambda g: g.potential).id)
        self.assertLess(top_b.potential, 95.0)
        self.assertGreater(top_b.potential - top_b.overall, 8.0)

    def test_starting_world_416342(self):
        a = P.generate_world(seed=416342, dev_rules=RZ.DEV2)
        b = P.generate_world(seed=416342, dev_rules=RZ.DEV3)
        self.assertEqual([(g.id, g.status, g.tour, g.lifestyle) for g in a.golfers],
                         [(g.id, g.status, g.tour, g.lifestyle) for g in b.golfers])
        ta = sorted(a.golfers, key=lambda g: -g.overall)
        tb = sorted(b.golfers, key=lambda g: -g.overall)
        self.assertGreater(ta[0].overall - ta[1].overall, 8.0)          # Rory Wilson, 98.6 vs 90.5 (dev-2)
        self.assertEqual(ta[0].id, tb[0].id)                              # still the world's best
        self.assertLess(tb[0].overall, 95.0)
        self.assertLess(tb[0].overall - tb[1].overall, 4.0)
        changed = sum(x.attrs != y.attrs for x, y in zip(a.golfers, b.golfers))
        self.assertLess(changed, 15)                                      # only the elite tail and teenage prodigies


class MoneyStanding(unittest.TestCase):
    def test_equivalent_standing_on_different_rating_scales(self):
        """Ryan: an 80 that is top of its class is treated as a 90 that is top of its class."""
        base = [52.0, 60.5, 61.0, 66.0, 70.0, 74.5, 80.0]
        low, high = FIN.MoneyStanding(base), FIN.MoneyStanding([v + 10 for v in base])
        for v in base:
            self.assertEqual(low.standing(v), high.standing(v + 10))
            self.assertEqual(low.reference(v), high.reference(v + 10))
        stretched = FIN.MoneyStanding([40 + 1.3 * (v - 40) for v in base])    # any order-preserving rescale
        self.assertEqual([low.standing(v) for v in base], [stretched.standing(40 + 1.3 * (v - 40)) for v in base])
        # whole golfers: the best of each pool starts with the same savings
        g80, g90 = golfer(80, born=1997), golfer(90, born=1997)
        self.assertEqual(FIN.initial_cash(g80, 30, 0.5, low), FIN.initial_cash(g90, 30, 0.5, high))
        self.assertEqual(FIN.seeded_losses(g80, 2, low), FIN.seeded_losses(g90, 2, high))
        self.assertNotEqual(FIN.initial_cash(g80, 30, 0.5), FIN.initial_cash(g90, 30, 0.5))   # absolute (dev-1/2)

    def test_ties_share_one_standing(self):
        m = FIN.MoneyStanding([70, 75, 75, 75, 80])
        self.assertEqual(m.standing(75), 0.5)
        a, b = golfer(75, gid=1), golfer(75, gid=2)
        self.assertEqual(FIN.initial_cash(a, 30, 0.3, m), FIN.initial_cash(b, 30, 0.3, m))

    def test_empty_and_small_pools(self):
        self.assertEqual(FIN.MoneyStanding([]).standing(80), 0.5)                   # nobody to compare with
        self.assertEqual(FIN.MoneyStanding([]).standing(80, member=False), 0.5)
        self.assertEqual(FIN.MoneyStanding([65]).standing(65), 0.5)                 # a pool of one
        two = FIN.MoneyStanding([60, 70])
        self.assertEqual((two.standing(60), two.standing(70)), (0.25, 0.75))
        self.assertEqual(two.standing(75, member=False), 2.5 / 3)                   # a newcomer above both
        self.assertEqual(two.standing(70, member=False), 2 / 3)                     # a newcomer level with the top
        self.assertEqual(two.standing(50, member=False), 0.5 / 3)
        self.assertTrue(math.isfinite(FIN.initial_cash(golfer(70), 30, 0.5, FIN.MoneyStanding([]))))

    def test_standing_is_monotone_and_the_reference_is_a_valid_ladder(self):
        ref = FIN.MONEY_REFERENCE
        self.assertEqual((ref[0][0], ref[-1][0]), (0.0, 1.0))
        self.assertTrue(all(q1 > q0 and v1 >= v0 for (q0, v0), (q1, v1) in zip(ref, ref[1:])))
        m = FIN.MoneyStanding([random.Random(i).uniform(30, 95) for i in range(500)])
        xs = sorted(m.vals)
        self.assertTrue(all(m.reference(b) >= m.reference(a) for a, b in zip(xs, xs[1:])))
        self.assertLess(m.reference(xs[-1]), 93.0)                                  # the top of any pool reads as
        self.assertGreater(m.reference(xs[-1]), 85.0)                               # a typical world's very best

    def test_experience_and_status_are_kept(self):
        m = FIN.MoneyStanding([60, 70, 80, 90])
        top = golfer(90)
        self.assertLess(FIN.initial_cash(top, 22, 0.5, m), FIN.initial_cash(top, 30, 0.5, m))  # one year vs eight
        self.assertEqual(FIN.initial_cash(top, 21, 0.5, m), 15000)                             # none yet on tour
        am, club = golfer(90, status='amateur'), golfer(90, status='club_pro')
        self.assertEqual(FIN.initial_cash(am, 20, 0.5, m), FIN.initial_cash(am, 20, 0.5))       # flat, as before
        self.assertEqual(FIN.initial_cash(club, 40, 0.5, m), FIN.initial_cash(club, 40, 0.5))
        retired = golfer(90, lifestyle='retired')
        self.assertFalse(FIN.in_money_pool(retired))
        self.assertFalse(FIN.in_money_pool(am))

    def test_worlds_use_standing_only_under_dev3(self):
        a = P.generate_world(seed=416342, dev_rules=RZ.DEV2)
        b = P.generate_world(seed=416342, dev_rules=RZ.DEV3)
        rory_a = max(a.golfers, key=lambda g: g.overall)
        rory_b = b.by_id[rory_a.id]
        self.assertGreater(rory_a.cash, 50e6)                 # dev-2: about $70M a year at 98.6, eight years of it
        self.assertLess(rory_b.cash, rory_a.cash / 2)         # dev-3: a typical world's #1
        pool = FIN.MoneyStanding(g.overall for g in b.golfers if FIN.in_money_pool(g))
        self.assertAlmostEqual(FIN.money_overall(rory_b, pool), FIN.MONEY_REFERENCE[-1][1], delta=0.1)
        for x, y in zip(a.golfers, b.golfers):                # amateurs' and club professionals' money untouched
            if x.status in ('amateur', 'club_pro'):
                self.assertEqual(x.cash, y.cash)

    def test_newcomer_is_placed_as_if_already_in_the_pool(self):
        """member=False (a new professional judged against the world they join) equals adding them to the pool."""
        pool = [55.0, 62.5, 62.5, 70.0, 70.0, 81.25, 90.0]
        m = FIN.MoneyStanding(pool)
        for x in (40.0, 55.0, 62.5, 66.0, 70.0, 85.0, 90.0, 95.0):
            joined = FIN.MoneyStanding(pool + [x])
            self.assertEqual(m.standing(x, member=False), joined.standing(x), x)
            g = golfer(x, born=1999)
            joined = FIN.MoneyStanding(pool + [g.overall])            # (the golfer's Overall as computed, to the bit)
            self.assertEqual(FIN.initial_cash(g, 26, 0.4, m, member=False), FIN.initial_cash(g, 26, 0.4, joined), x)
            self.assertEqual(FIN.seeded_losses(g, 3, m, member=False), FIN.seeded_losses(g, 3, joined), x)
        self.assertEqual(FIN.MoneyStanding([]).standing(70, member=False), FIN.MoneyStanding([70]).standing(70))

    def test_seeded_fame_is_exactly_scale_free_under_dev3(self):
        """Two dev-3 worlds identical but for every golfer's ratings moved down by 5 (order unchanged) seed exactly
        the same fame for every golfer; under dev-2 (absolute Overall) they do not."""
        from golfsim import prestige as PR
        from golfsim.season import Season

        def seeded(rules, shift):
            w = P.generate_world(seed=5, scale=0.05, dev_rules=rules)
            for g in w.golfers:
                g.attrs = {k: v - shift for k, v in g.attrs.items()}
            s = Season(w, seed=5, workers=1)
            return s, {g.id: list(s.fame_log[g.id]) for g in s.world.golfers}

        s0, a = seeded(RZ.DEV3, 0.0)
        _, b = seeded(RZ.DEV3, 5.0)
        self.assertEqual(a, b)
        s2, c = seeded(RZ.DEV2, 0.0)
        _, d = seeded(RZ.DEV2, 5.0)
        self.assertNotEqual(c, d)
        # and the value is the formula's: the best professional's six entries sum to seeded_fame of the reference
        # Overall at their standing, for this world's own draw u (recovered from the dev-2 world, which shares the
        # stream: same seed, same golfers, same order)
        pros = [g for g in s0.world.golfers if FIN.in_money_pool(g)]
        top = max(pros, key=lambda g: g.overall)
        ref = FIN.MoneyStanding(g.overall for g in pros).reference(top.overall)
        absolute = sum(v for _, v in c[top.id])                     # dev-2: seeded_fame(Overall, u)
        base = PR.seeded_fame(s2.world.by_id[top.id].overall, 0.0) / 0.6           # (this golfer's dev-2 Overall)
        share = absolute / base                                     # 0.6 + 0.8 u
        self.assertAlmostEqual(sum(v for _, v in a[top.id]), PR.seeded_fame(ref, (share - 0.6) / 0.8), places=6)

if __name__ == '__main__':
    unittest.main()
