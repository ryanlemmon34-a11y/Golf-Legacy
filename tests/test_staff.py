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
from golfsim import finance as FIN                                     # noqa: E402
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

    def test_scouts_judge_what_they_can_see_not_hidden_potential(self):
        """Coaches do not read hidden potential: changing it changes nothing. They do notice a young
        player who improved a lot over the last year."""
        def approaches(potential_shift, improved):
            s = fresh(23)
            young = [g for g in s.world.golfers if g.age(2027) <= 20 and g.status == 'amateur'][:600]
            s.overall_start[2026] = {}
            for i, g in enumerate(young):
                g.cash, g.backing = 0.0, 0.0                             # cannot pay anyone
                g.potential = min(99.0, g.potential + potential_shift)
                s.overall_start[2026][g.id] = g.overall - (6.0 if improved and i % 2 else 1.0)
            s.start_finances(2027)
            return Counter(i % 2 for i, g in enumerate(young) if s.staff.deal.get(g.id) == 'share')
        self.assertEqual(approaches(0.0, False), approaches(25.0, False))     # hidden potential is invisible
        got = approaches(0.0, True)
        self.assertGreater(got[1], 1.5 * max(1, got[0]))                     # fast improvers stand out


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
        g.status, g.tour = 'pro', ''                                                 # no school or local baseline
        self.assertEqual(st.coaching(g, 'putting', 19), ST.SELF_TEACHING)          # no coach yet
        st.assign_coach(None, g, c, 'fee', (2027, 1), 'golfer', 'test')
        eff = st.rel.effectiveness('coach', c.id, g.id, 2027)
        q = lambda raw: ST.SELF_TEACHING + (raw - ST.SELF_TEACHING) * eff
        self.assertAlmostEqual(st.coaching(g, 'putting', 19, 2027), q(0.9))       # speciality + youth
        self.assertAlmostEqual(st.coaching(g, 'long_game', 19, 2027), q(0.75))
        self.assertAlmostEqual(st.coaching(g, 'long_game', 30, 2027), q(0.6))
        coached, alone = self._young(), self._young()
        for _ in range(10):
            D.develop_week(coached, 'train', 19, 'putting', coach=st.coaching(g, 'putting', 19, 2027))
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
        k, view = st.caddies[kid], st.bag(SEASON.g[gid], 2027)
        eff = st.rel.effectiveness('caddie', kid, gid, 2027)
        self.assertEqual(view.name, k.name)
        self.assertIs(view.familiarity, k.familiarity)                       # their course knowledge is their own
        for sk, v in k.skills.items():                                       # skills reach the player through the pair
            self.assertAlmostEqual(view.skills[sk], 50 + (v - 50) * eff)
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


class MoneyTests(unittest.TestCase):
    def test_player_payments_equal_staff_receipts(self):
        s = fresh(26)
        s.start_finances(2027)
        eds = s.cal.editions(2027)
        for w in (1, 2, 3):
            s.run_week(2027, w, [e for e in eds if e.week == w])
        led = s.ledgers[2027].values()
        rec = s.staff_receipts[2027]
        caddie_paid = sum(l.caddie + l.caddie_share for l in led)
        coach_paid = sum(l.coaching + l.coach_share for l in led)
        self.assertGreater(caddie_paid, 0)
        self.assertAlmostEqual(caddie_paid, sum(v for (kind, _), v in rec.items() if kind == 'caddie'), places=4)
        self.assertAlmostEqual(coach_paid, sum(v for (kind, _), v in rec.items() if kind == 'coach'), places=4)
        for g in s.world.golfers:                                            # and every golfer still reconciles
            l = s.ledgers[2027].get(g.id)
            self.assertAlmostEqual(g.cash, s.cash_start[2027][g.id] + (l.net if l else 0.0), places=6)

    def test_contracted_coaching_is_reserved_before_travel(self):
        s = fresh(27)
        s.start_finances(2027)
        gid = next(g for g, d in s.staff.deal.items() if d == 'fee')
        g = s.g[gid]
        with_coach = s.spendable(g, 2027)
        c = s.staff.coach(gid)
        self.assertAlmostEqual(s.committed_weekly(g) - c.fee / 52, max(0.0, FIN.weekly_living(g)[1] - FIN.weekly_living(g)[0]))
        del s.staff.coach_of[gid], s.staff.deal[gid]
        self.assertAlmostEqual(s.spendable(g, 2027) - with_coach, FIN.RESERVE_WEEKS * c.fee / 52)

    def test_a_golfer_who_cannot_pay_loses_their_coach_midseason(self):
        s = fresh(28)
        s.start_finances(2027)
        payers = [gid for gid, d in s.staff.deal.items() if d == 'fee'][:20]
        scouted = [gid for gid, d in s.staff.deal.items() if d == 'share'][:20]
        for gid in payers + scouted:
            s.g[gid].cash, s.g[gid].backing = -10 ** 6, 0.0
        s.plan_block(2027, 5)
        self.assertTrue(all(gid not in s.staff.coach_of for gid in payers))
        self.assertTrue(all(gid in s.staff.coach_of for gid in scouted))   # a share deal costs nothing now
        self.assertTrue(all(any('could no longer pay the fee' in t for _, _, t in s.history[gid]) for gid in payers))
        ended = [x for gid in payers for x in s.staff.rel.of_golfer(gid, 'coach') if x.end]
        self.assertTrue(all(x.end == (2027, 5) and x.ended_by == 'golfer' for x in ended))   # a dated mid-season end


class LifecycleTests(unittest.TestCase):
    def test_caddie_experience_comes_from_work_and_keeps_high_skills(self):
        s = fresh(29)
        s.start_finances(2027)
        busy, idle, expert = list(s.staff.caddies.values())[:3]
        busy.rounds_worked, idle.rounds_worked, expert.rounds_worked = 60.0, 0.0, 60.0
        busy.born = idle.born = expert.born = 1990
        expert.skills['strategy'] = 97.0
        before = dict(busy.skills), dict(idle.skills)
        ST.end_of_season(s, 2027, s.season_snapshot(2027))
        self.assertAlmostEqual(busy.skills['strategy'], min(95.0, before[0]['strategy'] + 0.3), places=2)
        self.assertEqual(idle.skills['strategy'], before[1]['strategy'])    # no work, no experience
        self.assertEqual(expert.skills['strategy'], 97.0)                    # never clamped down
        self.assertEqual((busy.seasons, idle.seasons), (1, 0))

    def test_staff_invariants_across_rollovers(self):
        s = fresh(30)
        def check(st):
            load = Counter(st.coach_of.values())
            self.assertTrue(all(n <= st.coaches[cid].capacity for cid, n in load.items()))
            self.assertEqual(len(set(st.caddie_of.values())), len(st.caddie_of))
            self.assertTrue(all(st.coaches[cid].status == 'active' for cid in st.coach_of.values()))
            self.assertTrue(all(st.caddies[kid].status == 'active' for kid in st.caddie_of.values()))
            self.assertTrue(all(s.g[gid].lifestyle != 'retired' for gid in list(st.coach_of) + list(st.caddie_of)))
            self.assertEqual(set(st.deal), set(st.coach_of))
        for year in (2027, 2028, 2029):
            s.refresh_people(year)
            s.start_finances(year)
            st = s.staff
            check(st)
            load = Counter(st.coach_of.values())
            self.assertTrue(all(n <= st.coaches[cid].capacity for cid, n in load.items()))
            self.assertEqual(len(set(st.caddie_of.values())), len(st.caddie_of))      # one golfer per caddie
            self.assertTrue(all(st.coaches[cid].status == 'active' for cid in st.coach_of.values()))
            self.assertTrue(all(st.caddies[kid].status == 'active' for kid in st.caddie_of.values()))
            self.assertTrue(all(s.g[gid].lifestyle != 'retired' for gid in list(st.coach_of) + list(st.caddie_of)))
            self.assertEqual(set(st.deal), set(st.coach_of))
            s.end_of_season(year)
            check(st)                                                        # and between seasons too
        former = [p for p in list(st.coaches.values()) + list(st.caddies.values()) if p.former_golfer]
        self.assertTrue(former)
        for p in former:                                                     # identity and history kept
            g = s.g[p.former_golfer]
            self.assertEqual(p.name, g.name)
            self.assertEqual(g.lifestyle, 'retired')
            self.assertTrue(any(t.startswith('Became a') for _, _, t in s.history[g.id]))
            self.assertTrue(p.history and p.history[0][1].startswith('Became a'))
        self.assertTrue(any(c.status == 'retired' for c in st.coaches.values()))
        self.assertTrue(s.juniors_added)

    def test_outside_coaches_only_answer_paying_demand(self):
        s = fresh(32)
        s.start_finances(2027)
        st = s.staff
        st.unserved[2027] = {}
        n0 = len(st.coaches)
        ST.end_of_season(s, 2027, s.season_snapshot(2027))
        self.assertEqual(sum(1 for c in st.coaches.values() if 'outside recruit' in c.background), 0)
        st.unserved[2028] = {'USA': 12}
        ST.end_of_season(s, 2028, s.season_snapshot(2028))
        new = [c for c in st.coaches.values() if 'outside recruit' in c.background]
        self.assertEqual(len(new), 2)
        self.assertTrue(all(c.country == 'USA' for c in new))

    def test_match_play_holes_teach_the_course(self):
        s = fresh(31)
        ed = next(e for e in s.cal.editions(2027) if e.series.series_id == 'USA_AMATEUR')
        ams = [g.id for g in s.world.golfers if g.status == 'amateur'][:80]
        k = next(iter(s.staff.caddies.values()))
        s.staff.assign_caddie(None, s.g[ams[0]], k, (2027, 1))              # one of them brings a caddie
        venues = s.lib.venues(2027)
        s.play_week(2027, ed.week, [ed], {ed.event_id: [ams]}, venues)
        key = s.lib.course(venues[ed.event_id][0]).familiarity_key
        fam = [s.g[gid].familiarity.get(key, 0) for gid in ams]
        self.assertTrue(all(f >= 2 for f in fam))                            # two stroke-play rounds each
        self.assertTrue(any(f > 2 for f in fam))                             # plus match-play holes
        self.assertAlmostEqual(k.familiarity.get(key, 0), s.g[ams[0]].familiarity[key])
        self.assertAlmostEqual(k.rounds_worked, s.g[ams[0]].familiarity[key])


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
            s.prize_record[g.id] = {4: [0.0, 20]}                     # earns nothing (proven)
        n0, k0 = len(s.staff.coaches), len(s.staff.caddies)
        counts = decide(s, 2027, s.season_snapshot(2027))
        self.assertGreater(counts.get('became coach', 0) + counts.get('became caddie', 0), 5)
        self.assertEqual(len(s.staff.coaches) - n0, counts.get('became coach', 0))
        self.assertEqual(len(s.staff.caddies) - k0, counts.get('became caddie', 0))
        new = [k for k in s.staff.caddies.values() if k.former_golfer]
        self.assertTrue(all(s.g[k.former_golfer].lifestyle == 'retired' for k in new))


if __name__ == '__main__':
    unittest.main()
