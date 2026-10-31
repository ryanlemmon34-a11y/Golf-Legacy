"""Five-year prestige of events and courses (rules 2026-11-05; golfsim/prestige.py), its record in the archive, and
the observer's Prestige columns and dated history bars on tournament, course and nation pages.

Run from the project folder:  python -m unittest tests.test_world_prestige -v
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
from golfsim import prestige as PR                                     # noqa: E402
from golfsim.calendar import WorldCalendar                              # noqa: E402
from golfsim.population import generate_world                           # noqa: E402
from golfsim.session import Session                                     # noqa: E402

SER = WorldCalendar().by_id['PT_GULF_COAST_CLASSIC']


class EventWindow(unittest.TestCase):
    def test_warm_up_first_edition_carries_a_quarter(self):
        f0 = PR.factors(SER, 70, 80)
        by = PR.seeded_years(f0, 2027)
        self.assertEqual(sorted(by), [2023, 2024, 2025, 2026])
        start = PR.prestige_from([f0])
        by[2027] = [PR.factors(SER, 100, 80)]                           # one great field
        self.assertAlmostEqual(PR.combine(PR.window_factors(by, 2027)) - start, PR.WEIGHTS['field'] * 30 * 1.0 / 4.0)
        for y in range(2028, 2032):                                       # the assumed years leave one a year
            by[y] = [PR.factors(SER, 100, 80)]
        self.assertAlmostEqual(PR.combine(PR.window_factors(by, 2031)) - start, PR.WEIGHTS['field'] * 30)

    def test_recency_weights_and_skipped_years(self):
        by = {2030: [PR.factors(SER, 0, 80)], 2031: [PR.factors(SER, 100, 80)]}
        f = PR.window_factors(by, 2031)
        self.assertAlmostEqual(f[1], 100 * 1.0 / 1.9)                      # weights 1.0 (2031) and 0.9 (2030)
        by = {2027: [PR.factors(SER, 50, 80)], 2029: [PR.factors(SER, 80, 80)]}   # 2028 not held: left out
        self.assertAlmostEqual(PR.window_factors(by, 2029)[1], (80 * 1.0 + 50 * 0.8) / 1.8)
        self.assertIsNone(PR.window_factors({2020: [PR.factors(SER, 50, 80)]}, 2029))   # nothing in five years
        two = {2029: [PR.factors(SER, 40, 80), PR.factors(SER, 60, 80)]}  # two editions in a year: their mean
        self.assertAlmostEqual(PR.window_factors(two, 2029)[1], 50)

    def test_annual_movement_limit(self):
        by = {y: [PR.factors(SER, 100, 100)] for y in range(2027, 2032)}
        raw = PR.combine(PR.window_factors(by, 2031))
        self.assertEqual(PR.event_prestige_after(by, 2031, raw - 20), raw - 20 + PR.EVENT_MAX_MOVE)
        self.assertEqual(PR.event_prestige_after(by, 2031, raw + 20), raw + 20 - PR.EVENT_MAX_MOVE)
        self.assertEqual(PR.event_prestige_after(by, 2031, raw - 1), raw)
        self.assertEqual(PR.event_prestige_after({}, 2031, 42.0), 42.0)


class CourseLag(unittest.TestCase):
    def test_reads_completed_seasons_only_and_moves_slowly(self):
        hosted = {2026: 40.0, 2027: 90.0}
        self.assertAlmostEqual(PR.course_prestige(hosted, 2027, None), 40.0)        # 2027 not yet counted
        self.assertAlmostEqual(PR.course_prestige(hosted, 2028, 40.0), 40.0 + PR.COURSE_MAX_MOVE)
        self.assertAlmostEqual(PR.course_prestige(hosted, 2028, 60.0), (90 * 1.0 + 40 * 0.9) / 1.9)
        self.assertAlmostEqual(PR.course_prestige({2020: 70.0}, 2028, 70.0), 70.0 * PR.COURSE_FADE)   # nothing lately
        self.assertIsNone(PR.course_prestige({}, 2028, None))

    def test_old_saves_migrate(self):
        from golfsim.season import _migrate_event_years
        f0, f1, f2 = PR.factors(SER, 50, 80), PR.factors(SER, 60, 80), PR.factors(SER, 70, 80)
        state = {'first_year': 2027, 'event_factors': {'X': [f0] * 4 + [f1, f2]},
                 'prestige_history': {'X': [(2027, 50.0, 60), (2028, 51.0, 70)]}}
        by = _migrate_event_years(state)['X']
        self.assertEqual(by[2027], [f1])
        self.assertEqual(by[2028], [f2])
        self.assertEqual(sorted(by), [2024, 2025, 2026, 2027, 2028])     # five calendar years kept


class InASession(unittest.TestCase):
    """One small world, a season and three weeks: the season's record and every observer view."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        s = Session.create(cls.tmp / 'w', seed=57, workers=1, world=generate_world(seed=57, scale=0.03))
        cls.start = dict(s.season.event_prestige)
        cls.start_courses = dict(s.season.course_prestige)
        s.advance(52)
        cls.end = dict(s.season.event_prestige)
        cls.end_courses = dict(s.season.course_prestige)
        cls.success = {c: list(v) for c, v in s.season.participation.success.get(2027, {}).items()}
        s.advance(3)
        cls.mid_courses = dict(s.season.course_prestige)
        s.close()
        import observer as O
        cls.O = O
        cls.w = O.World(cls.tmp / 'w', workers=1)
        cls.w.reload()

    @classmethod
    def tearDownClass(cls):
        cls.w.close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_events_move_within_the_yearly_limit(self):
        moved = [abs(self.end[sid] - self.start[sid]) for sid in self.start]
        self.assertTrue(all(m <= PR.EVENT_MAX_MOVE + 1e-9 for m in moved))
        self.assertTrue(any(m > 0.01 for m in moved))

    def test_courses_are_lagged(self):
        self.assertTrue(self.start_courses)
        self.assertEqual(self.mid_courses, self.end_courses)               # nothing moves during a season
        for cid, v in self.end_courses.items():
            if cid in self.start_courses:
                self.assertLessEqual(abs(v - self.start_courses[cid]), PR.COURSE_MAX_MOVE + 1e-9)

    def test_national_prestige_is_zero_sum(self):
        a = sum(x[0] for x in self.success.values())
        e = sum(x[1] for x in self.success.values())
        self.assertGreater(a, 0)
        self.assertAlmostEqual(a, e, delta=1e-6 * a)

    def test_the_season_record(self):
        rec = self.w.a.year(2027)['prestige']
        self.assertEqual(rec['format'], 'golf-legacy-prestige/1')
        self.assertEqual(rec['events'], {k: round(v, 2) for k, v in self.end.items()})
        self.assertEqual(rec['courses'], {k: round(v, 2) for k, v in self.end_courses.items()})
        n = rec['nations']
        self.assertEqual(n['entrant_year'], 2028)
        for kind in ('juniors', 'new_pros'):
            self.assertAlmostEqual(sum(n['shares'][kind].values()), 1.0, places=4)
            self.assertAlmostEqual(sum(n['baseline_shares'][kind].values()), 1.0, places=4)
            self.assertEqual(sum(n['allocated'][kind].values()), n['totals'][kind])
            self.assertEqual(sum(n['existing'][kind].values()), n['totals'][kind])

    def test_observer_columns_and_bars(self):
        O, w = self.O, self.w
        _, html = O.tournaments(w, {})
        self.assertIn('>Prestige</th>', html)
        _, html = O.tournaments(w, {'sort': ['prestige']})
        sid = max(self.end, key=self.end.get)
        self.assertIn(f'/series/{sid}', html.split('</tr>')[1])             # the most prestigious first
        _, html = O.series(w, {}, sid)
        self.assertIn('Prestige over time', html)
        self.assertIn('<span class="ry">2027</span>', html)
        self.assertIn('<span class="ry">now</span>', html)
        _, html = O.courses_page(w, {})
        self.assertIn('>Prestige</th>', html)
        cid = max(self.end_courses, key=self.end_courses.get)
        _, html = O.course(w, {}, cid)
        self.assertIn('Prestige over time', html)
        self.assertIn('<span class="ry">2028</span>', html)                 # set at the end of 2027 for 2028
        _, html = O.nations(w, {})
        for h in ('Prestige', 'Multiplier', 'Share of juniors', 'Starting share', 'Share of new pros'):
            self.assertIn(f'>{h}</th>', html)
        _, html = O.nation(w, {}, 'USA')
        self.assertIn('Share of each year’s juniors', html)
        self.assertIn('Starting share of new golfers', html)


if __name__ == '__main__':
    unittest.main()
