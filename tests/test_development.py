"""Development, the monthly plan, finances and careers.

Run from the project folder:  python -m unittest discover -s tests -v
"""
from __future__ import annotations

import copy
import random
import statistics as S
import sys
import unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from golfsim import development as D                                   # noqa: E402
from golfsim import finance as FIN                                     # noqa: E402
from golfsim.calendar import TOUR_BY_KEY                               # noqa: E402
from golfsim.careers import decide                                     # noqa: E402
from golfsim.population import generate_world                          # noqa: E402
from golfsim.season import Season                                      # noqa: E402

WORLD = generate_world()


def golfer(age=20, gap=10.0, **pers):
    g = copy.deepcopy(next(x for x in WORLD.golfers if x.age(2027) == age))
    g.potential = g.overall + gap
    g.personality.update(pers)
    D.init_ceilings(g, age, random.Random(1))
    return g


class DevelopmentTests(unittest.TestCase):
    def test_learning_slows_with_age(self):
        rates = [D.learning_rate(a) for a in (18, 25, 35, 50)]
        self.assertEqual(rates, sorted(rates, reverse=True))
        self.assertEqual(len(set(rates)), len(rates))

    def test_ceilings_match_potential(self):
        g = golfer(20, 12)
        self.assertTrue(all(g.ceilings[k] >= g.attrs[k] for k in g.attrs))
        from golfsim.golfer import overall_rating
        self.assertAlmostEqual(overall_rating(g.ceilings), g.potential, delta=1.0)

    def test_training_targets_its_category(self):
        g = golfer(20, 12)
        before = dict(g.attrs)
        for _ in range(10):
            D.develop_week(g, 'train', 25, 'putting')
        for k in D.CATEGORIES['putting']:
            self.assertGreater(g.attrs[k], before[k])
        for k in D.CATEGORIES['long_game']:
            self.assertEqual(g.attrs[k], before[k])

    def test_tournaments_teach_raw_golfers_most(self):
        raw, polished = golfer(20, 15), golfer(20, 2)
        self.assertGreater(D.develop_week(raw, 'play', 20, rounds=4), 3 * D.develop_week(polished, 'play', 20, rounds=4))
        g = golfer(25, 10)
        before = dict(g.attrs)
        D.develop_week(g, 'play', 25, rounds=4)
        mental = S.mean(g.attrs[k] - before[k] for k in D.CATEGORIES['mental'])
        long_game = S.mean(g.attrs[k] - before[k] for k in D.CATEGORIES['long_game'])
        self.assertGreater(mental, long_game)
        self.assertEqual(D.develop_week(g, 'rest', 25), 0.0)

    def test_hard_workers_improve_faster(self):
        lazy, keen = golfer(19, 10, work_ethic=15), golfer(19, 10, work_ethic=90)
        for g in (lazy, keen):
            for _ in range(30):
                D.develop_week(g, 'play', 19, rounds=4)
        self.assertGreater(keen.overall - keen.potential, lazy.overall - lazy.potential)

    def test_aging(self):
        g = golfer(30, 0)
        g.peak_age, g.aging_rate = 27, 1.0
        p0, c0 = g.attrs['power'], g.attrs['composure']
        for age in range(31, 45):
            D.age_year(g, age, random.Random(age))
        self.assertLess(g.attrs['power'], p0 - 5)               # strength fades
        self.assertGreater(g.attrs['composure'], c0 + 2)        # experience grows

    def test_serious_injuries_leave_a_mark(self):
        g = golfer(28, 5)
        p = g.attrs['power']
        self.assertEqual(D.serious_injury(g, 4, random.Random(1)), {})
        marked = [bool(D.serious_injury(copy.deepcopy(g), w, random.Random(i))) for w in (12, 30) for i in range(200)]
        self.assertLess(sum(marked[:200]), sum(marked[200:]))               # longer: likelier to leave a mark
        self.assertTrue(0 < sum(marked[:200]) < 200)
        i, hurt = 0, copy.deepcopy(g)
        while not D.serious_injury(hurt, 20, random.Random(i)):
            i, hurt = i + 1, copy.deepcopy(g)
        self.assertLess(hurt.attrs['power'], p)

    def test_choose_category_reads_the_game(self):
        g = golfer(22, 0, coachability=95)
        g.attrs['management'] = 95
        for k in g.ceilings:
            g.ceilings[k] = g.attrs[k]
        for k in D.CATEGORIES['short_game']:
            g.ceilings[k] = g.attrs[k] + 15
        picks = Counter(D.choose_category(g, random.Random(i)) for i in range(50))
        self.assertGreater(picks['short_game'], 35)


class FinanceTests(unittest.TestCase):
    def test_costs(self):
        cal = __import__('golfsim.calendar', fromlist=['WorldCalendar']).WorldCalendar()
        g = next(x for x in WORLD.golfers if x.status == 'pro' and x.country == 'USA' and x.tour.startswith('MN_'))
        mini = next(s for s in cal.series if s.tour == g.tour)
        home = FIN.event_cost(g, mini, mini.cities[0])
        ch = next(s for s in cal.series if s.tier == 2 and s.host_country == 'Japan')
        self.assertGreater(FIN.event_cost(g, ch, ch.cities[0]), FIN.EVENT_COST[2])     # overseas costs more
        self.assertGreater(home, FIN.EVENT_COST[4])                                   # entry fee
        col = next(x for x in WORLD.golfers if x.tour == 'CO_US_D1')
        cs = next(s for s in cal.series if s.tour == 'CO_US_D1')
        self.assertEqual(FIN.event_cost(col, cs, cs.cities[0]), 0.0)                  # the college pays
        led = FIN.Ledger()
        led.prize, led.events, led.living = 50000, 20000, 32000
        self.assertEqual(led.net, -2000)


class CareerTests(unittest.TestCase):
    def test_money_age_and_hope_decide_who_keeps_chasing(self):
        # the same 400 mini-tour players, in debt with no results, at 22 and at 28 (a counterfactual)
        def quits(age):
            s = Season(generate_world(), seed=5, development=True, workers=1)
            minis = [g for g in s.world.golfers if g.status == 'pro' and g.lifestyle == 'full_time'
                     and TOUR_BY_KEY[g.tour].tier == 4][:400]
            for g in minis:
                g.born = 2027 - age
                g.cash, g.backing = -30000, 0.0
                s.prize_share[g.id] = 0.0
            decide(s, 2027, s.season_snapshot(2027))
            return s, [g for g in minis if g.lifestyle != 'full_time']
        _, young = quits(22)
        s, older = quits(28)
        self.assertGreater(len(young), 0)                        # nobody is immune
        self.assertGreater(len(older), 1.5 * len(young))
        for g in older:
            if g.lifestyle == 'part_time':
                self.assertTrue(any('Stopped chasing' in t for _, _, t in s.history[g.id]))

    def test_graduates_and_juniors(self):
        s = Season(generate_world(), seed=6, development=True, workers=1)
        grads = [g for g in s.world.golfers if g.tour == 'CO_US_D1'][:60]
        for i, g in enumerate(grads):
            g.born = 2027 - 22
            s.am_pos[g.id] = i + 1
        decide(s, 2027, s.season_snapshot(2027))
        self.assertGreater(sum(1 for g in grads if g.status == 'pro'), 35)
        self.assertTrue(all(not g.tour.startswith('CO_') for g in grads))
        from golfsim.careers import add_juniors
        n = add_juniors(s, 2028)
        new = s.world.golfers[-n:]
        self.assertTrue(150 <= n <= 400)
        self.assertTrue(all(g.age(2028) == 18 and g.ceilings and g.status == 'amateur' for g in new))
        self.assertEqual(len({g.name for g in s.world.golfers}), len(s.world.golfers))


class PlanTests(unittest.TestCase):
    def test_monthly_plan_and_development_in_season(self):
        s = Season(generate_world(), seed=7, development=True, workers=2)
        eds = s.cal.editions(2027)
        young = [g for g in s.world.golfers if g.age(2027) <= 20 and g.potential - g.overall > 6][:100]
        before = {g.id: g.overall for g in young}
        tired = next(g for g in s.world.golfers if g.status == 'pro' and g.tour.startswith('CH_'))
        s.fatigue[tired.id] = 0.85
        s.plan_block(2027, 1)
        self.assertEqual(s.plans[tired.id][1][0], 'rest')          # exhausted: a rest week first
        s.fatigue[tired.id] = 0.0
        for w in range(1, 9):
            s.run_week(2027, w, [e for e in eds if e.week == w])
        s.close()
        acts = Counter(a for p in s.plans.values() for a, _ in p.values())
        self.assertTrue(acts['play'] and acts['train'] and acts['rest'])
        self.assertGreater(S.mean(g.overall - before[g.id] for g in young), 0.1)


if __name__ == '__main__':
    unittest.main()
