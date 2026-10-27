"""Coaches and caddies: who gets them, what they do, and where they come from.

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
from golfsim import development as D                                  # noqa: E402
from golfsim import staff as ST                                       # noqa: E402
from golfsim.calendar import TOUR_BY_KEY                              # noqa: E402
from golfsim.population import generate_world                         # noqa: E402
from golfsim.season import Season                                     # noqa: E402


def fresh(seed=21):
    s = Season(generate_world(seed=seed), seed=seed, development=True, workers=1)
    s.refresh_people(2027)
    return s


SEASON = fresh()
SEASON.start_finances(2027)                                           # the first hiring market


class MarketTests(unittest.TestCase):
    def test_one_coach_at_a_time_and_one_bag_per_caddie(self):
        st = SEASON.staff
        load = Counter(st.coach_of.values())
        self.assertTrue(all(n <= st.coaches[cid].capacity for cid, n in load.items()))
        self.assertEqual(len(set(st.caddie_of.values())), len(st.caddie_of))
        self.assertTrue(all(ST.wants_caddie(SEASON.g[gid]) for gid in st.caddie_of))

    def test_not_every_college_player_or_amateur_has_a_coach(self):
        st = SEASON.staff
        share = lambda pred: S.mean(g.id in st.coach_of for g in SEASON.world.golfers if pred(g))
        college = share(lambda g: g.tour.startswith('CO_'))
        amateurs = share(lambda g: g.status == 'amateur' and not g.tour.startswith('CO_'))
        premier = share(lambda g: g.tour.startswith('PT_'))
        self.assertLess(college, 0.5)
        self.assertLess(amateurs, 0.3)
        self.assertGreater(premier, max(college, amateurs))

    def test_paid_coaching_needs_money_counterfactual(self):
        def hired(cash):
            s = fresh(22)
            ams = [g for g in s.world.golfers if g.status == 'amateur' and g.age(2027) >= 24][:300]
            for g in ams:
                g.cash, g.backing = cash, 0.0
                g.potential = g.overall                              # no scout would approach them
            s.start_finances(2027)
            return sum(1 for g in ams if s.staff.deal.get(g.id) == 'fee')
        self.assertEqual(hired(-5000.0), 0)
        self.assertGreater(hired(500000.0), 50)

    def test_coaches_approach_young_raw_players_they_believe_in(self):
        """Same world, same young players: alternate ones get high hidden potential. Coaches see only
        through their scouting noise, yet approach the high-potential half far more often."""
        s = fresh(23)
        young = [g for g in s.world.golfers if g.age(2027) <= 20 and g.status == 'amateur'][:600]
        for i, g in enumerate(young):
            g.cash, g.backing = 0.0, 0.0                             # cannot pay anyone
            g.potential = min(99.0, g.overall + (30.0 if i % 2 else 2.0))
        s.start_finances(2027)
        got = Counter(i % 2 for i, g in enumerate(young) if s.staff.deal.get(g.id) == 'share')
        self.assertGreater(got[1], 4 * max(1, got[0]))


class EffectTests(unittest.TestCase):
    def _young(self):
        g = copy.deepcopy(next(x for x in SEASON.world.golfers if x.age(2027) == 19 and x.ceilings))
        g.potential = g.overall + 15
        D.init_ceilings(g, 19, random.Random(5))
        return g

    def test_coaching_quality_speciality_and_youth(self):
        st = ST.Staff()
        rng = random.Random(1)
        c = st.new_coach(rng, 'USA', 2027, 45, 60, 50, 'putting', True, 50, 'test')
        g = self._young()
        self.assertEqual(st.coaching(g, 'putting', 19), ST.SELF_TEACHING)          # no coach yet
        st.coach_of[g.id] = c.id
        self.assertAlmostEqual(st.coaching(g, 'putting', 19), 0.9)                  # speciality + youth
        self.assertAlmostEqual(st.coaching(g, 'long_game', 19), 0.75)
        self.assertAlmostEqual(st.coaching(g, 'long_game', 30), 0.6)
        coached, alone = self._young(), self._young()
        for _ in range(10):
            D.develop_week(coached, 'train', 19, 'putting', coach=st.coaching(g, 'putting', 19))
            D.develop_week(alone, 'train', 19, 'putting', coach=ST.SELF_TEACHING)
        self.assertGreater(coached.overall, alone.overall)

    def test_a_coach_helps_a_golfer_read_their_game(self):
        g = self._young()
        g.attrs['management'], g.personality['coachability'] = 20.0, 20.0           # a poor judge alone
        err = lambda ins: S.mean(abs(D.perceived_gap(g, k, ins) - (g.ceilings[k] - g.attrs[k])) for k in g.attrs)
        self.assertLess(err(0.9), err(0.0))

    def test_caddie_on_the_bag(self):
        st = SEASON.staff
        gid, kid = next(iter(st.caddie_of.items()))
        self.assertIs(st.bag(SEASON.g[gid]), st.caddies[kid])
        loner = next(g for g in SEASON.world.golfers if g.id not in st.caddie_of)
        own = st.bag(loner)
        self.assertEqual(own.skills['strategy'], ST.SELF_CADDIE)
        self.assertLess(own.skills['strategy'], 50)                                  # below an average caddie

    def test_caddies_learn_courses_and_fees_reconcile(self):
        s = fresh(24)
        s.start_finances(2027)
        eds = s.cal.editions(2027)
        before = {k.id: sum(k.familiarity.values()) for k in s.staff.caddies.values()}
        for w in (1, 2):
            s.run_week(2027, w, [e for e in eds if e.week == w])
        worked = [k for k in s.staff.caddies.values() if sum(k.familiarity.values()) > before[k.id]]
        self.assertTrue(worked)
        self.assertTrue(all(k.id in s.staff.caddie_of.values() for k in worked))
        for g in s.world.golfers:
            led = s.ledgers[2027].get(g.id)
            self.assertAlmostEqual(g.cash, s.cash_start[2027][g.id] + (led.net if led else 0.0), places=6)
        paid = [g for g in s.world.golfers if s.staff.deal.get(g.id) == 'fee']
        self.assertTrue(all(s.ledgers[2027][g.id].coaching > 0 for g in paid))


class FormerGolferTests(unittest.TestCase):
    def test_the_best_rarely_become_coaches_or_caddies(self):
        g = copy.deepcopy(next(x for x in SEASON.world.golfers if x.status == 'pro'))
        g.attrs.update(management=80.0, composure=80.0, green_reading=80.0)
        g.personality.update(coachability=80.0, work_ethic=80.0)
        g.cash = 30000.0
        modest = (ST.p_become_coach(g, 35), ST.p_become_caddie(g, 35))
        g.cash = 25_000_000.0
        rich = (ST.p_become_coach(g, 35), ST.p_become_caddie(g, 35))
        self.assertGreater(modest[0], 0.03)
        self.assertGreater(modest[1], 0.03)
        self.assertLess(rich[0], modest[0] / 100)
        self.assertLess(rich[1], modest[1] / 100)

    def test_skills_come_from_their_game(self):
        st = ST.Staff()
        g = copy.deepcopy(next(x for x in SEASON.world.golfers if x.status == 'pro'))
        g.attrs.update(management=90.0, composure=85.0, green_reading=88.0, resilience=80.0)
        k = st.from_golfer(g, 2030, 'caddie', random.Random(2), 'mini-tour')
        self.assertGreater(k.skills['strategy'], 70)
        self.assertEqual(k.former_golfer, g.id)
        c = st.from_golfer(g, 2030, 'coach', random.Random(2), 'mini-tour')
        self.assertIn(c.speciality, ST.SPECIALITIES)
        self.assertEqual(c.name, g.name)

    def test_decide_can_turn_a_quitting_golfer_into_staff(self):
        from golfsim.careers import decide
        s = fresh(25)
        minis = [g for g in s.world.golfers if g.status == 'pro' and g.lifestyle == 'full_time'
                 and TOUR_BY_KEY[g.tour].tier == 4][:600]
        for g in minis:
            g.cash, g.backing, g.born = -40000.0, 0.0, 2027 - 30
            g.attrs.update(management=85.0, composure=85.0, green_reading=85.0)
            g.personality.update(coachability=85.0, work_ethic=85.0)
            s.prize_share[g.id] = 0.0
        n0, k0 = len(s.staff.coaches), len(s.staff.caddies)
        counts = decide(s, 2027, s.season_snapshot(2027))
        self.assertGreater(counts.get('became coach', 0) + counts.get('became caddie', 0), 5)
        self.assertEqual(len(s.staff.coaches) - n0, counts.get('became coach', 0))
        self.assertEqual(len(s.staff.caddies) - k0, counts.get('became caddie', 0))
        new = [k for k in s.staff.caddies.values() if k.former_golfer]
        self.assertTrue(all(s.g[k.former_golfer].lifestyle == 'retired' for k in new))


if __name__ == '__main__':
    unittest.main()
