"""Residence-aware amateur golf, the college eligibility ledger and the rules registry (2090 world audit:
Jae-won T. Jung and Lukas Johansson graduated from US colleges, stayed in the USA and were assigned overseas
amateur circuits by nationality, losing their local amateur golf).

Run from the project folder:  python -m unittest tests.test_amateur_residence -v
"""
from __future__ import annotations

import pickle
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from golfsim import careers                                              # noqa: E402
from golfsim import residence as RES                                     # noqa: E402
from golfsim import rules                                                # noqa: E402
from golfsim.calendar import TOUR_BY_KEY                                 # noqa: E402
from golfsim.population import generate_world                            # noqa: E402
from golfsim.qualification import RULES as MAJOR_RULES                  # noqa: E402
from golfsim.season import Season                                        # noqa: E402

WORLD = generate_world(seed=11, scale=0.2)


def season():
    s = Season(pickle.loads(pickle.dumps(WORLD)), seed=11, development=True, workers=1)
    s.refresh_people(2027)
    s.start_finances(2027)
    return s


def foreign_college_golfer(s):
    """A non-American at a US college, living at the college base (a US state)."""
    g = next(g for g in s.world.golfers if g.tour == 'CO_US_D1' and g.country not in ('USA', 'Canada'))
    assert s.places.home[g.id][0] == 'USA'
    return g


def amateur_event(s, tour):
    return next(x for x in s.cal.series if x.tour == tour and x.tier == 6 and x.category not in
                ('national_amateur', 'elite_amateur', 'circuit_championship'))


def graduate(s, g, year=2027):
    """g's college eligibility ends this winter and they stay amateur (turning professional and retiring
    switched off: the career odds are not what is tested)."""
    g.born = year - 22
    snap = s.season_snapshot(year)
    with mock.patch.object(careers, 'p_turn_pro', return_value=0.0), \
            mock.patch.object(careers, 'p_retire', return_value=0.0):
        careers.decide(s, year, snap)
    return snap


class AmateurAccessTests(unittest.TestCase):
    def test_a_graduate_who_stays_keeps_local_amateur_golf(self):
        s = season()
        g = foreign_college_golfer(s)
        home_circuit = careers.amateur_series(g)                             # by nationality
        self.assertNotEqual(home_circuit, 'AM_NORTH_AMERICA')
        graduate(s, g)
        self.assertEqual((g.status, g.lifestyle), ('amateur', 'part_time'))
        self.assertEqual(g.tour, 'AM_NORTH_AMERICA')                         # where they live, not overseas
        self.assertTrue(any('where they live' in t for _, _, t in s.history[g.id]))
        na = amateur_event(s, 'AM_NORTH_AMERICA')
        self.assertTrue(s.eligible(g, na, na.week))
        own = amateur_event(s, home_circuit)                                 # their own country's circuit too
        if g.country in {c for c, _ in TOUR_BY_KEY[home_circuit].countries}:
            self.assertTrue(s.eligible(g, own, own.week))
        self.assertEqual(s.places.home[g.id][0], 'USA')                      # no move invented
        self.assertNotEqual(g.country, 'USA')                                # nationality untouched

    def test_residence_opens_local_amateur_golf_but_not_professional_events(self):
        s = season()
        am = next(g for g in s.world.golfers if g.status == 'amateur' and not g.tour.startswith('CO_')
                  and g.country not in {c for c, _ in TOUR_BY_KEY['AM_EUROPE'].countries}
                  and g.tour != 'AM_EUROPE')
        ev = amateur_event(s, 'AM_EUROPE')
        self.assertFalse(s.eligible(am, ev, ev.week))
        s.places.move(am.id, 2027, 53, ('England', 'Surrey'), 'test')
        self.assertTrue(s.eligible(am, ev, ev.week))                         # lives in England now
        pro = next(g for g in s.world.golfers if g.status == 'pro' and g.tour.startswith('MN_')
                   and g.country == 'USA')
        mini = next(x for x in s.cal.series if x.tier == 4 and 'England' in {c for c, _ in TOUR_BY_KEY[x.tour].countries})
        before = s.eligible(pro, mini, mini.week)
        s.places.move(pro.id, 2027, 53, ('England', 'Surrey'), 'test')
        self.assertEqual(s.eligible(pro, mini, mini.week), before)           # professionals: unchanged

    def test_returning_home_takes_up_the_home_circuit(self):
        s = season()
        g = foreign_college_golfer(s)
        snap = graduate(s, g)
        homeland = s.places.birth[g.id][0]
        g.cash = 1e6                                                         # a move they can pay for
        with mock.patch.object(RES, 'move_odds', return_value=(homeland, 1.0)):
            RES.review_moves(s, 2027, snap)
        self.assertEqual(s.places.home[g.id][0], homeland)
        self.assertEqual(g.tour, careers.amateur_series(g, homeland))
        self.assertTrue(any(t.startswith('Now plays amateur golf on the') for _, _, t in s.history[g.id]))
        moves = [m for m in s.move_log[2027] if m['person'] == g.id]
        self.assertEqual(len(moves), 1)
        self.assertEqual(g.country, s.g[g.id].country)

    def test_amateur_series_falls_back_to_nationality(self):
        g = next(g for g in WORLD.golfers if g.country == 'Sweden')
        self.assertEqual(careers.amateur_series(g), 'AM_EUROPE')
        self.assertEqual(careers.amateur_series(g, 'USA'), 'AM_NORTH_AMERICA')


class CollegeLedgerTests(unittest.TestCase):
    def test_each_season_recorded_once_and_survives_reload(self):
        s = season()
        g = next(g for g in s.world.golfers if g.tour == 'CO_US_D1')
        snap = s.season_snapshot(2027)
        s.record_college(2027, snap)
        s.record_college(2027, snap)                                         # a retried season end
        self.assertEqual(s.college[g.id], [2027])
        t = pickle.loads(pickle.dumps(s))
        t.record_college(2028, {g.id: {'tour': 'CO_US_D1'}})
        self.assertEqual(t.college[g.id], [2027, 2028])
        t.record_college(2029, {})
        self.assertIn(g.id, t.college)                                       # left one season ago: kept
        t.record_college(2030, {})
        self.assertNotIn(g.id, t.college)                                    # the archive has their seasons
        t.close()
        s.close()

    def test_graduation_follows_the_rule_not_the_ledger(self):
        """The ledger records; eligibility still ends after the season a golfer turns 22 (ruleset 1), so
        a golfer already in college when the ledger began is not cut short or extended."""
        s = season()
        g = foreign_college_golfer(s)
        g.born = 2027 - 21
        with mock.patch.object(careers, 'p_turn_pro', return_value=0.0), \
                mock.patch.object(careers, 'p_retire', return_value=0.0):
            careers.decide(s, 2027, s.season_snapshot(2027))
        self.assertEqual(g.tour, 'CO_US_D1')                                 # 21: another season


class RulesTests(unittest.TestCase):
    def test_every_route_the_engine_writes_is_explained(self):
        routes = ['PREMIER EXEMPT', 'PREMIER FULL', 'PREMIER GRADUATE', 'PREMIER CONDITIONAL', 'PREMIER MEMBER',
                  'WINNER EXEMPTION (not a member)', 'PREMIER MEMBER (visitor places)',
                  'PREMIER MEMBER (visitor places) — late entry', 'AMATEUR INVITATION', 'COLLEGE LINEUP',
                  'OPEN AMATEUR ENTRY — late entry', 'CLUB PROFESSIONAL', 'MEMBER', 'MEMBER (draw)', 'HOME PLAYER',
                  'CHALLENGER TOUR EUROPE MEMBER', 'AMATEUR RANKING 12', 'AMATEUR (unranked, by form)',
                  'HOME AMATEUR (amateur ranking 4)', 'HOME AMATEUR (unranked)', 'REGIONAL AMATEUR (amateur ranking 99)',
                  'REGIONAL AMATEUR (unranked)', 'ORDER OF MERIT 3', 'PAST CHAMPION', 'USA AMATEUR CHAMPION 2031',
                  'RUNNER-UP 2030', 'OPEN QUALIFYING ENTRY', 'QUALIFYING SITE 2', 'QUALIFYING SITE 2 (alternate)',
                  'SECTIONAL 4', 'ENTRY', 'COLLEGE POST-SEASON', 'Q-SCHOOL ENTRY', 'PREMIER POINTS LIST',
                  'QUALIFYING ENTRY', 'SELECTED', 'ALT', 'INIT']
        routes += [r.code for rs in MAJOR_RULES.values() for r in rs]
        for r in routes:
            rule, text = rules.explain(r)
            self.assertIn(rule, rules.RULES, r)
            self.assertTrue(text, r)
        self.assertEqual(rules.explain('ORDER OF MERIT 3')[1], "No. 3 on the circuit's order of merit")
        self.assertTrue(rules.explain('MEMBER — late entry')[1].endswith('a late entry'))
        self.assertEqual(rules.explain('U5'), ('major-qualification', 'Major champions, last 5 years'))
        self.assertEqual(rules.explain('something new'), (None, None))

    def test_versions(self):
        self.assertEqual(rules.VERSIONS[-1][0], rules.RULES_VERSION)
        for _, (title, text, since) in rules.RULES.items():
            self.assertTrue(title and text)
            self.assertIn(since, (None, *[v for v, _ in rules.VERSIONS]))


if __name__ == '__main__':
    unittest.main()
