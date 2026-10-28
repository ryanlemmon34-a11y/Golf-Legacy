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

    def test_pressure_skills_need_competition(self):
        """Practice builds technique; composure, management and tournament consistency need recent
        competitive rounds, and the mental game matures each year only with the rounds played."""
        self.assertEqual(D.experience_factor(0), 0.0)
        self.assertEqual(D.experience_factor(D.EXPERIENCE_ROUNDS * 2), 1.0)
        fresh, seasoned = golfer(20, 12), golfer(20, 12)
        b = dict(fresh.attrs)
        for _ in range(10):
            D.develop_week(fresh, 'train', 20, 'mental', experience=0.0)
            D.develop_week(seasoned, 'train', 20, 'mental', experience=1.0)
        self.assertEqual({k: fresh.attrs[k] for k in D.CATEGORIES['mental']}, {k: b[k] for k in D.CATEGORIES['mental']})
        self.assertTrue(all(seasoned.attrs[k] > b[k] for k in D.CATEGORIES['mental']))
        fresh, seasoned = golfer(20, 12), golfer(20, 12)
        for _ in range(10):
            for g, e in ((fresh, 0.0), (seasoned, 1.0)):
                for cat in ('long_game', 'putting'):
                    D.develop_week(g, 'train', 20, cat, experience=e)
        for k in ('driving_accuracy', 'mid_irons', 'short_putting', 'lag_putting'):   # technique: the same
            self.assertAlmostEqual(fresh.attrs[k], seasoned.attrs[k])
        for k in ('striking_consistency', 'putting_consistency'):        # practice alone: a little
            self.assertGreater(fresh.attrs[k], b[k])
            self.assertLess(fresh.attrs[k] - b[k], 0.3 * (seasoned.attrs[k] - b[k]))
        idle, active = golfer(25, 5), golfer(25, 5)
        m0 = S.mean(idle.attrs[k] for k in D.CATEGORIES['mental'])
        D.age_year(idle, 26, random.Random(3), experience=0.0)
        D.age_year(active, 26, random.Random(3), experience=1.0)
        self.assertEqual(S.mean(idle.attrs[k] for k in D.CATEGORIES['mental']), m0)
        self.assertGreater(S.mean(active.attrs[k] for k in D.CATEGORIES['mental']), m0)

    def test_balanced_schedules_develop_best(self):
        """18 to 30: a mix of training and competition beats either alone, and a golfer with no events
        (blocked or by choice: development only sees what they did) falls well short."""
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
        from development_audit import path_years
        end = {}
        for name, events, train in (('balanced', 20, 26), ('tournaments', 25, 0), ('training', 0, 46), ('none', 0, 0)):
            xs = []
            for i in range(8):
                g = golfer(18, 15)
                path_years(g, 18, 12, events, train, random.Random(i))
                xs.append(g.overall)
            end[name] = S.mean(xs)
        self.assertGreater(end['balanced'], end['tournaments'])
        self.assertGreater(end['balanced'], end['training'] + 2)
        self.assertGreater(end['training'], end['none'])
        self.assertGreater(end['tournaments'], end['none'])

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

    def test_adult_amateurs_take_jobs(self):
        """Non-college amateurs living on savings take a job and keep playing: likelier with age and
        debt, less likely with money to keep going; recorded as a career transition."""
        s = Season(generate_world(), seed=8, development=True, workers=1)
        ams = [g for g in s.world.golfers if g.status == 'amateur' and not g.tour.startswith('CO_')
               and g.lifestyle == 'full_time'][:300]
        def share(age, cash):
            t = copy.deepcopy(s)
            gs = [t.g[g.id] for g in ams]
            for g in gs:
                g.born, g.cash, g.backing = 2027 - age, cash, 0.0
                t.am_pos.pop(g.id, None)                      # no hope of turning pro from the rankings
            decide(t, 2027, t.season_snapshot(2027))
            took = [g for g in gs if g.lifestyle == 'part_time' and g.status == 'amateur']
            if took:
                self.assertTrue(any(x['kind'] == 'amateur took a job' and x['gid'] == took[0].id
                                    for x in t.transitions[2027]))
                self.assertTrue(any('Took a job' in txt for _, _, txt in t.history[took[0].id]))
            return len(took) / len(gs)
        self.assertLess(share(20, 5000), share(24, 5000))
        self.assertLess(share(24, 200000), share(24, 5000))
        self.assertLess(share(24, 5000), share(24, -20000))
        self.assertLess(share(19, 5000), 0.2)
        self.assertGreater(share(27, -20000), 0.8)
        self.assertEqual(FIN.weekly_living(ams[0]), (0.0, 0.0))
        ams[0].lifestyle = 'part_time'
        self.assertEqual(FIN.weekly_living(ams[0]), (FIN.SALARY['part_time'] / 52, FIN.LIVING_WORKING / 52))


class InvitationTests(unittest.TestCase):
    def test_invitations_follow_the_entry_affordability_rule(self):
        """An invited golfer who cannot pay the trip declines and the next in line takes the place; the
        same rule as a regular entry. School-paid college events are never out of reach."""
        from collections import defaultdict
        s = Season(generate_world(), seed=9, development=True, workers=1)
        eds = s.cal.editions(2027)
        busy = defaultdict(set)
        rng = random.Random(1)
        for ed in (e for e in eds if e.series.category in ('elite_amateur', 'national_amateur')):
            first = s.special_field(ed, 2027, ed.week, rng, busy)[0]
            if len(first) == ed.series.field:                            # more eligible than places
                break
        broke = s.g[first[0]]
        broke.cash, broke.backing = -1e6, 0.0
        again = s.special_field(ed, 2027, ed.week, rng, busy)[0]
        self.assertNotIn(broke.id, again)
        self.assertIn(ed.series.series_id, s.declined[2027][broke.id])
        self.assertEqual(len(again), len(first))                         # the next in line took the place
        city = s.lib.venues(2027)[ed.event_id][0].city
        self.assertFalse(s.can_afford(broke, ed.series, city, s.spendable(broke, 2027)))
        # a college golfer deep in debt still plays school events, and the school is recorded as payer
        col = next(e for e in eds if e.series.category == 'college_postseason'
                   and e.series.series_id == 'SMALL_COLLEGE_CHAMPIONSHIP')
        top = s.special_field(col, 2027, col.week, rng, busy)[0]
        student = s.g[top[0]]
        student.cash = -1e6
        self.assertIn(student.id, s.special_field(col, 2027, col.week, rng, busy)[0])
        self.assertTrue(s.can_afford(student, col.series, s.lib.venues(2027)[col.event_id][0].city, -1e6))


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
