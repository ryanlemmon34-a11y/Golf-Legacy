"""Historical identity, relationships, continuity, archives and saves.

Run from the project folder:  python -m unittest discover -s tests -v
"""
from __future__ import annotations

import copy
import random
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from golfsim import history as H                                      # noqa: E402
from golfsim import staff as ST                                       # noqa: E402
from golfsim.archive import Archive, write_archive                    # noqa: E402
from golfsim.calendar import TOUR_BY_KEY                              # noqa: E402
from golfsim.population import generate_world                         # noqa: E402
from golfsim.savegame import load_simulation, save_simulation        # noqa: E402
from golfsim.season import Season                                     # noqa: E402


def fresh(seed):
    s = Season(generate_world(seed=seed), seed=seed, development=True, workers=1)
    s.refresh_people(2027)
    return s


def run_weeks(s, weeks, year=2027):
    eds = s.cal.editions(year)
    for w in weeks:
        s.run_week(year, w, [e for e in eds if e.week == w])


def pro(s, tier):
    return [g for g in s.world.golfers if g.status == 'pro' and g.lifestyle == 'full_time'
            and TOUR_BY_KEY.get(g.tour) and TOUR_BY_KEY[g.tour].tier == tier]


class IdentityTests(unittest.TestCase):
    def test_one_person_id_space(self):
        s = fresh(51)
        ids = list(s.g) + list(s.staff.coaches) + list(s.staff.caddies)
        self.assertEqual(len(ids), len(set(ids)))
        n = len(s.world.golfers)
        from golfsim.careers import add_juniors
        add_juniors(s, 2028)
        new = s.world.golfers[n:]
        self.assertTrue(new and all(g.id not in s.staff.coaches and g.id not in s.staff.caddies for g in new))

    def test_duplicate_names_never_merge_people(self):
        s = fresh(52)
        s.start_finances(2027)
        a, b = pro(s, 2)[:2]
        b.name = a.name                                                     # two different people, one name
        c1, c2 = [c for c in s.staff.coaches.values() if c.status == 'active'][:2]
        for g in (a, b):
            if g.id in s.staff.coach_of:
                s.staff.end_coach(None, g.id, (2027, 1), 'test', 'golfer')
        s.staff.assign_coach(None, a, c1, 'fee', (2027, 2), 'golfer', 'test')
        s.staff.assign_coach(None, b, c2, 'fee', (2027, 2), 'golfer', 'test')
        s.snapshots[2027] = s.season_snapshot(2027)
        with tempfile.TemporaryDirectory() as d:
            arc = Archive(write_archive(s, d))
            self.assertEqual(sorted(arc.find(a.name)), sorted([a.id, b.id]))
            self.assertEqual([x.staff for x in arc.golfer_staff(a.id) if x.kind == 'coach'][-1], c1.id)
            self.assertEqual([x.staff for x in arc.golfer_staff(b.id) if x.kind == 'coach'][-1], c2.id)

    def test_a_former_player_becomes_staff_as_the_same_person(self):
        from golfsim.careers import decide
        s = fresh(53)
        minis = pro(s, 4)[:600]
        for g in minis:                                                     # a controlled fixture: rare transitions
            g.cash, g.backing, g.born = -40000.0, 0.0, 2027 - 30
            g.attrs.update(management=85.0, composure=85.0, green_reading=85.0)
            g.personality.update(coachability=85.0, work_ethic=85.0)
            s.prize_record[g.id] = {4: [0.0, 20]}                     # earns nothing (proven)
        s.snapshots[2027] = snap = s.season_snapshot(2027)
        decide(s, 2027, snap)
        staff = [p for p in list(s.staff.coaches.values()) + list(s.staff.caddies.values()) if p.former_golfer]
        self.assertTrue(staff)
        for p in staff:
            self.assertEqual(p.id, p.former_golfer)                         # same person id
            self.assertIn(p.id, s.g)                                        # the player still exists
            self.assertEqual(s.g[p.id].lifestyle, 'retired')                # retired from playing, not deleted
        with tempfile.TemporaryDirectory() as d:
            arc = Archive(write_archive(s, d))
            p = staff[0]
            roles = arc.roles(p.id)
            self.assertIn('golfer', roles)
            self.assertTrue('coach' in roles or 'caddie' in roles)
            self.assertTrue(arc.playing_career(p.id))                       # the playing view survives


class RelationshipTests(unittest.TestCase):
    def setUp(self):
        self.st = ST.Staff(seed=1)
        self.rng = random.Random(1)
        self.c = self.st.new_coach(self.rng, 'USA', 2027, 45, 60, 50, 'putting', False, 50, 'test')
        self.k = self.st.new_caddie(self.rng, 'USA', 2027, 40, {x: 60 for x in ('strategy', 'green_reading', 'yardage',
                                    'course_knowledge', 'mental_support', 'communication')}, 50, 'test')
        w = generate_world(seed=54)
        self.golfers = [g for g in w.golfers if g.status == 'pro'][:8]

    def test_both_profiles_read_the_same_stint(self):
        g = self.golfers[0]
        self.st.assign_coach(None, g, self.c, 'fee', (2027, 1), 'golfer', 'test')
        a = self.st.rel.of_golfer(g.id, 'coach')
        b = self.st.rel.of_staff(self.c.id, 'coach')
        self.assertEqual(len(a), 1)
        self.assertIs(a[0], b[0])

    def test_a_coach_works_with_several_clients(self):
        for g in self.golfers[:6]:
            self.st.assign_coach(None, g, self.c, 'fee', (2027, 1), 'golfer', 'test')
        self.assertEqual(sum(1 for cid in self.st.coach_of.values() if cid == self.c.id), 6)
        self.assertEqual(len([s for s in self.st.rel.of_staff(self.c.id) if s.end is None]), 6)

    def test_capacity_is_separate_from_teaching(self):
        st = ST.Staff()
        rng = random.Random(3)
        cs = [st.generated_coach(rng, 'USA', 2027) for _ in range(400)]
        clients = [c.clients for c in cs]
        self.assertTrue(all(ST.CLIENTS_MIN <= n <= ST.CLIENTS_MAX for n in clients))
        self.assertAlmostEqual(sum(clients) / len(clients), ST.CLIENTS_MEAN, delta=0.4)
        good = [c.clients for c in cs if c.teaching > 65]
        poor = [c.clients for c in cs if c.teaching < 35]
        self.assertAlmostEqual(sum(good) / len(good), sum(poor) / len(poor), delta=0.6)   # no link to skill

    def test_one_touring_golfer_per_caddie(self):
        a, b = self.golfers[:2]
        self.st.assign_caddie(None, a, self.k, (2027, 1))
        with self.assertRaises(ValueError):
            self.st.assign_caddie(None, b, self.k, (2027, 1))

    def test_an_agreed_fee_holds_when_the_coach_becomes_famous(self):
        g = self.golfers[0]
        self.st.assign_coach(None, g, self.c, 'fee', (2027, 1), 'golfer', 'test')
        agreed = self.st.agreed_fee(g.id)
        self.c.reputation = 95.0                                             # their students start winning
        self.assertEqual(self.st.agreed_fee(g.id), agreed)                   # existing clients keep their terms
        self.assertGreater(self.c.fee, agreed)                               # new clients pay the new rate

    def test_departure_reunion_and_retirement_keep_everything(self):
        g = self.golfers[0]
        st = self.st
        st.assign_coach(None, g, self.c, 'fee', (2027, 1), 'golfer', 'test')
        for _ in range(40):
            st.rel.add_work('coach', g.id, 1.0, 2027)
        st.end_coach(None, g.id, (2027, 53), 'the golfer wanted a change', 'golfer')
        before = st.rel.rapport('coach', self.c.id, g.id, 2028)
        st.assign_coach(None, g, self.c, 'fee', (2030, 1), 'golfer', 'reunited')
        after = st.rel.rapport('coach', self.c.id, g.id, 2030)
        stints = st.rel.of_golfer(g.id, 'coach')
        self.assertEqual(len(stints), 2)                                    # two stints, both kept
        self.assertEqual(stints[0].reason_end, 'the golfer wanted a change')
        self.assertLess(after, before)                                      # time apart wears it down
        self.assertGreater(after, 0)                                        # but not to nothing
        self.c.status = 'retired'
        from types import SimpleNamespace
        season = SimpleNamespace(g={g.id: g}, staff=st, log=lambda *a: None)   # a minimal season for release
        ST.release_departed(season, 2031, 53)
        self.assertNotIn(g.id, st.coach_of)
        self.assertEqual(stints[1].reason_end, 'coach retired')
        self.assertIn(self.c.id, st.coaches)                                # retired, not deleted
        self.assertEqual(len(st.rel.of_staff(self.c.id)), 2)


class ContinuityTests(unittest.TestCase):
    def test_bounds_and_diminishing_returns(self):
        r = H.Relations(seed=2)
        r.begin('coach', 1, 2, (2027, 1), 'fee', 'golfer')
        levels = []
        for week in range(200):
            r.add_work('coach', 2, 1.0, 2027 + week // 50)
            levels.append(r.rapport('coach', 1, 2, 2027 + week // 50))
        gains = [b - a for a, b in zip(levels, levels[1:])]
        self.assertTrue(all(0 <= x < 1 for x in levels))
        self.assertTrue(all(g2 <= g1 + 1e-12 for g1, g2 in zip(gains, gains[1:])))   # each week adds less
        eff = [r.effectiveness('coach', 1, 2, y) for y in range(2027, 2031)]
        self.assertTrue(all(0.6 < e < 1.1 for e in eff))

    def test_calendar_time_alone_adds_nothing(self):
        r = H.Relations(seed=3)
        r.begin('caddie', 1, 2, (2027, 1), 'tour bag', 'golfer')
        r.add_work('caddie', 2, 40.0, 2027)
        now = r.rapport('caddie', 1, 2, 2027)
        self.assertLessEqual(r.rapport('caddie', 1, 2, 2028), now)          # a year of not working together
        self.assertLess(r.rapport('caddie', 1, 2, 2035), now)

    def test_familiarity_does_not_beat_a_clearly_better_coach(self):
        st = ST.Staff(seed=4)
        rng = random.Random(4)
        avg = st.new_coach(rng, 'USA', 2027, 50, 50, 50, 'mental', False, 50, 'average')
        good = st.new_coach(rng, 'USA', 2027, 50, 80, 50, 'mental', False, 70, 'good')
        g1, g2 = [copy.deepcopy(g) for g in generate_world(seed=55).golfers if g.status == 'pro'][:2]
        for g in (g1, g2):
            g.tour = ''
        g2.attrs, g2.ceilings, g2.personality = dict(g1.attrs), dict(g1.ceilings), dict(g1.personality)
        st.assign_coach(None, g1, avg, 'fee', (2020, 1), 'golfer', 'long-standing')
        for _ in range(500):
            st.rel.add_work('coach', g1.id, 1.0, 2027)                     # years together
        st.assign_coach(None, g2, good, 'fee', (2027, 1), 'golfer', 'brand new')
        self.assertGreater(st.coaching(g2, 'long_game', 28, 2027), st.coaching(g1, 'long_game', 28, 2027))

    def test_hiring_or_firing_changes_no_attributes(self):
        s = fresh(56)
        s.start_finances(2027)
        g = pro(s, 2)[0]
        before = (dict(g.attrs), dict(g.ceilings), g.overall)
        c = next(c for c in s.staff.coaches.values() if c.status == 'active' and c.id != s.staff.coach_of.get(g.id))
        if g.id in s.staff.coach_of:
            s.staff.end_coach(s, g.id, (2027, 2), 'test', 'golfer')
        s.staff.assign_coach(s, g, c, 'fee', (2027, 2), 'golfer', 'test')
        if g.id in s.staff.caddie_of:
            s.staff.end_caddie(s, g.id, (2027, 2), 'test', 'golfer')
        self.assertEqual((dict(g.attrs), dict(g.ceilings), g.overall), before)


class DepartureTests(unittest.TestCase):
    def test_share_deals_are_judged_over_an_observation_period(self):
        p = ST.p_coach_moves_on
        one_bad = p('share', -0.4, 1.0, 0.0)
        three_flat = p('share', 0.0, 3.0, 0.0)
        three_bad = p('share', -0.4, 3.0, 0.0)
        improving = p('share', 0.6, 3.0, 0.0)
        self.assertLess(one_bad, three_flat)                                # one bad year is not failure
        self.assertLess(three_flat, three_bad)
        self.assertLess(improving, three_flat)
        self.assertEqual(p('share', -1.0, 0.4, 0.0), 0.0)                    # too little evidence to judge
        self.assertLess(p('fee', 0.0, 3.0, 0.0), 0.02)                       # paying clients rarely dropped

    def test_injury_or_no_play_is_weak_evidence(self):
        s = fresh(57)
        g = next(x for x in s.world.golfers if x.status == 'amateur' and x.age(2027) <= 21)
        healthy = {'events': 10, 'injury_weeks': 0, 'am_start': 400, 'am_end': 600}
        hurt = dict(healthy, injury_weeks=30)
        idle = dict(healthy, events=1)
        w = lambda row: ST.observed_progress(s, g, row, 2027)[1]
        self.assertGreater(w(healthy), w(hurt))
        self.assertGreater(w(healthy), w(idle))
        better = dict(healthy, am_end=200)                                  # amateur results count
        self.assertGreater(ST.observed_progress(s, g, better, 2027)[0], ST.observed_progress(s, g, healthy, 2027)[0])


class SchoolTests(unittest.TestCase):
    def test_college_events_with_zero_and_negative_balances(self):
        """School-paid college events: a golfer's personal balance (zero or deep debt) never blocks them."""
        starts = {}
        for cash in (0.0, -50000.0):
            s = fresh(58)
            s.start_finances(2027)
            col = [g for g in s.world.golfers if g.tour == 'CO_US_D1'][:60]
            for g in col:
                g.cash, g.backing = cash, 0.0
            run_weeks(s, range(1, 9))
            ids = {g.id for g in col}
            starts[cash] = sum(1 for r in s.results.values() if s.cal.by_id[r.series_id].tier == 5
                               for site in r.finish for gid, _, _ in site if gid in ids)
            self.assertGreater(starts[cash], 60, cash)
        self.assertGreater(starts[-50000.0], 0.8 * starts[0.0])                 # debt changes nothing material

    def test_school_coaching_is_a_baseline_and_does_not_stack(self):
        s = fresh(59)
        s.start_finances(2027)
        g = next(x for x in s.world.golfers if x.tour == 'CO_US_D1' and x.id not in s.staff.coach_of)
        self.assertEqual(s.staff.coaching(g, 'putting', g.age(2027), 2027), ST.COLLEGE_TEAM)
        weak = next(c for c in s.staff.coaches.values() if c.teaching < 30 and not c.youth)
        s.staff.assign_coach(s, g, weak, 'fee', (2027, 2), 'golfer', 'test')
        self.assertEqual(s.staff.coaching(g, 'long_game', g.age(2027), 2027), ST.COLLEGE_TEAM)   # the better, not both
        self.assertTrue(s.staff.rel.current('school', g.id))

    def test_leaving_college_is_a_recorded_transition(self):
        s = fresh(60)
        s.start_finances(2027)
        g = next(x for x in s.world.golfers if x.tour == 'CO_US_D1')
        before = dict(g.attrs)
        g.status, g.tour = 'pro', 'MN_US_SUNBELT'
        ST.sync_school(s, 2027, 53, closing=True)
        school = s.staff.rel.of_golfer(g.id, 'school')
        self.assertEqual(school[-1].reason_end, 'turned professional')
        self.assertEqual(g.attrs, before)


class AttributionTests(unittest.TestCase):
    def test_results_keep_the_team_of_the_week(self):
        s = fresh(61)
        s.start_finances(2027)
        g = next(x for x in pro(s, 2) if x.id in s.staff.coach_of)
        first = s.staff.coach_of[g.id]
        run_weeks(s, range(1, 7))
        early = [r for r in s.results.values() if any(gid == g.id for site in r.finish for gid, _, _ in site)]
        other = next(c for c in s.staff.coaches.values() if c.status == 'active' and c.id != first)
        s.staff.end_coach(s, g.id, (2027, 7), 'test', 'golfer')
        s.staff.assign_coach(s, g, other, 'fee', (2027, 7), 'golfer', 'test')
        run_weeks(s, range(7, 13))
        late = [r for r in s.results.values() if r.week >= 7 and any(gid == g.id for site in r.finish for gid, _, _ in site)]
        self.assertTrue(early and late)
        self.assertTrue(all(r.team[g.id][0] == first for r in early))      # not rewritten by the change
        self.assertTrue(all(r.team[g.id][0] == other.id for r in late))
        s.snapshots[2027] = s.season_snapshot(2027)
        with tempfile.TemporaryDirectory() as d:
            arc = Archive(write_archive(s, d))
            starts = {c['stint'].staff: c['starts'] for st_id in (first, other.id) for c in arc.staff_clients(st_id)
                      if c['stint'].golfer == g.id}
            self.assertEqual(starts[first], len(early))
            self.assertEqual(starts[other.id], len(late))
            self.assertEqual(arc.team_at(g.id, early[0].event_id)[0], first)

    def test_course_records_link_golfer_and_event(self):
        s = fresh(62)
        run_weeks(s, (1, 2))
        lay = next(r for r in s.records.layouts.values() if r.course_record)
        m = lay.course_record
        self.assertIn(m.golfer_id, s.g)
        self.assertEqual(s.g[m.golfer_id].name, m.golfer)
        self.assertIn(m.event_id, s.results)


class ArchiveAndSaveTests(unittest.TestCase):
    def test_archive_round_trip(self):
        s = fresh(63)
        s.start_finances(2027)
        run_weeks(s, range(1, 5))
        s.snapshots[2027] = s.season_snapshot(2027)
        with tempfile.TemporaryDirectory() as d:
            arc = Archive(write_archive(s, d))
            people = set(s.g) | set(s.staff.coaches) | set(s.staff.caddies)
            self.assertEqual(set(arc.people), people)
            self.assertEqual(len(arc.rel.stints), len(s.staff.rel.stints))
            self.assertEqual([x.__dict__ for x in arc.rel.stints[:20]],
                             [x.__dict__ | {'start': tuple(x.start), 'end': tuple(x.end) if x.end else None,
                                            'seasons': [list(v) for v in x.seasons]} for x in s.staff.rel.stints[:20]])
            self.assertEqual(len(arc.year(2027)['events']), sum(1 for r in s.results.values() if r.year == 2027))
            cid = next(iter(s.records.layouts)).split(':')[0]
            self.assertTrue(arc.course(cid)['records'])
            self.assertTrue(arc.recap(2027))

    def test_a_saved_simulation_resumes_exactly(self):
        s = fresh(64)
        s.start_finances(2027)
        run_weeks(s, (1, 2))
        with tempfile.TemporaryDirectory() as d:
            save_simulation(s, Path(d) / 'w.save')
            s2, meta = load_simulation(Path(d) / 'w.save')
        for x in (s, s2):
            run_weeks(x, (3, 4))
        self.assertEqual({k: r.finish for k, r in s.results.items()}, {k: r.finish for k, r in s2.results.items()})
        self.assertEqual([(g.id, round(g.cash, 6), g.attrs) for g in s.world.golfers],
                         [(g.id, round(g.cash, 6), g.attrs) for g in s2.world.golfers])
        self.assertEqual(len(s.staff.rel.stints), len(s2.staff.rel.stints))


if __name__ == '__main__':
    unittest.main()
