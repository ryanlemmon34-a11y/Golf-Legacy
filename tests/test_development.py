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
        self.assertGreater(D.learning_rate(18), D.learning_rate(25) > D.learning_rate(35) > D.learning_rate(50))

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
        self.assertTrue(D.serious_injury(g, 20, random.Random(1)))
        self.assertLess(g.attrs['power'], p)

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
        s = Season(generate_world(), seed=5, development=True, workers=1)
        minis = [g for g in s.world.golfers if g.status == 'pro' and g.lifestyle == 'full_time'
                 and TOUR_BY_KEY[g.tour].tier == 4][:400]
        young, older = minis[:200], minis[200:]
        for grp, age in ((young, 22), (older, 28)):
            for g in grp:
                g.born = 2027 - age
                g.cash = -30000
                s.ledger(2027, g.id).living = 40000
        decide(s, 2027)
        quit_young = sum(1 for g in young if g.lifestyle != 'full_time')
        quit_older = sum(1 for g in older if g.lifestyle != 'full_time')
        self.assertLess(quit_young, 20)
        self.assertGreater(quit_older, 3 * max(1, quit_young))
        for g in older:
            if g.lifestyle == 'part_time':
                self.assertTrue(any('Stopped chasing' in t for _, _, t in s.history[g.id]))

    def test_graduates_and_juniors(self):
        s = Season(generate_world(), seed=6, development=True, workers=1)
        grads = [g for g in s.world.golfers if g.tour == 'CO_US_D1'][:60]
        for i, g in enumerate(grads):
            g.born = 2027 - 22
            s.am_pos[g.id] = i + 1
        decide(s, 2027)
        self.assertGreater(sum(1 for g in grads if g.status == 'pro'), 40)
        from golfsim.careers import add_juniors
        n = add_juniors(s, 2028)
        new = s.world.golfers[-n:]
        self.assertTrue(120 <= n <= 260)
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
