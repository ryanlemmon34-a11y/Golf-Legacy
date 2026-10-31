"""Returning from work to full-time amateur golf (rules 2026-11-06; decisions D5 and D5a): a full season in work, no
debt and a full-time amateur season of golf in hand, results worth going back for, then a chance that falls
smoothly with age (no age excluded, at most CAP); its own random stream; the work start recorded at every way into
work.

Run from the project folder:  python -m unittest tests.test_amateur_return -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from golfsim import amateur_return as AR                                 # noqa: E402
from golfsim import finance as FIN                                       # noqa: E402


class Golfer(NS):
    def age(self, year):
        return year - self.born


def world(cash=20000.0, backing=0.0, born=2004, work_from=(2025, 1), events=16, spent=8000.0):
    """A working amateur and the facts their winter decision reads (p_amateur_job's runway is patched in Return
    tests to a fixed value; see setUp)."""
    g = Golfer(id=1, born=born, cash=cash, backing=backing, tour='AM_X', personality={'work_ethic': 50, 'big_stage': 50})
    led = FIN.Ledger()
    led.events = spent
    s = NS(seed=7, amateur_work_from={1: work_from} if work_from else {}, ledgers={2027: {1: led}})
    row = {'events': events, 'am_end': 150, 'am_start': 180, 'wins': 0, 'top3': 1}
    return s, g, row


def standing(rank):
    from golfsim.careers import amateur_standing
    return amateur_standing(rank)


class Conditions(unittest.TestCase):
    def setUp(self):
        from unittest import mock
        from golfsim import careers
        p = mock.patch.object(careers, 'runway_years', return_value=2.0)    # (needs a whole season otherwise)
        p.start()
        self.addCleanup(p.stop)

    def test_a_supported_return_is_possible_but_never_certain(self):
        s, g, row = world()
        p, facts = AR.chance(s, g, row, 2027, standing(row['am_end']))
        self.assertGreater(p, 0.0)
        self.assertLessEqual(p, AR.CAP)
        self.assertEqual(facts['seasons_in_work'], 3)                   # 2025, 2026, 2027
        self.assertEqual(facts['season_cost'], 16 * 500)                # their own average trip: 8,000 / 16

    def test_a_meaningful_period_in_work(self):
        s, g, row = world(work_from=(2027, 13))                         # took work in week 13 this season
        self.assertEqual(AR.chance(s, g, row, 2027, standing(150))[1]['blocked'], 'not yet a full season in work')
        s, g, row = world(work_from=(2027, 1))                          # (a winter job: worked all of 2027)
        self.assertGreater(AR.chance(s, g, row, 2027, standing(150))[0], 0)
        s, g, row = world(work_from=None)                               # working before the records began
        self.assertGreater(AR.chance(s, g, row, 2027, standing(150))[0], 0)

    def test_sustainable_funding_and_no_debt(self):
        s, g, row = world(cash=-1.0, backing=50000.0)
        self.assertIn('savings', AR.chance(s, g, row, 2027, standing(150))[1]['blocked'])
        s, g, row = world(cash=7000.0)                                  # below one season of golf (8,000)
        self.assertIn('savings', AR.chance(s, g, row, 2027, standing(150))[1]['blocked'])
        s, g, row = world(cash=5000.0, backing=3000.0)                  # family money counts
        self.assertGreater(AR.chance(s, g, row, 2027, standing(150))[0], 0)
        s, g, row = world(events=1, spent=100.0)                        # too few trips: a regional trip's cost
        self.assertEqual(AR.season_cost(s, 1, 2027, row), round(16 * AR.FALLBACK_TRIP, 6))

    def test_results_worth_going_back_for(self):
        s, g, row = world()
        row.update(am_end=900, am_start=950, top3=0)
        self.assertEqual(AR.chance(s, g, row, 2027, standing(900))[1]['blocked'], 'no results to go back for')
        row.update(am_start=1100)                                       # a rise of 200 places
        self.assertGreater(AR.chance(s, g, row, 2027, standing(900))[0], 0)
        row.update(am_start=950, wins=1)
        self.assertGreater(AR.chance(s, g, row, 2027, standing(900))[0], 0)

    def test_the_chance_falls_smoothly_with_age_and_none_is_excluded(self):
        ps = []
        for born in range(2006, 1975, -3):                              # ages 21 .. 51
            s, g, row = world(born=born)
            ps.append(AR.chance(s, g, row, 2027, standing(150))[0])
        self.assertTrue(all(p > 0 for p in ps))
        self.assertTrue(all(a >= b for a, b in zip(ps, ps[1:])))
        self.assertTrue(all(a - b < 0.25 for a, b in zip(ps, ps[1:])))   # no cliff between neighbouring ages
        self.assertLess(ps[-1], 0.01)                                     # at 51 it is rare, never excluded

    def test_no_flip_flopping(self):
        """Where the job decision would put them straight back to work, a return is correspondingly unlikely."""
        from golfsim.careers import p_amateur_job
        for born in (2005, 1999, 1992):
            s, g, row = world(born=born)
            p, facts = AR.chance(s, g, row, 2027, standing(150))
            self.assertAlmostEqual(facts['keep_up'], 1 - p_amateur_job(s, g, row, 2028), places=3)
            self.assertLessEqual(p, facts['keep_up'] + 0.0005)                   # (kept to 3 places)

    def test_its_own_random_stream(self):
        s, g, row = world()
        self.assertEqual(AR.draw(s, 1, 2027), AR.draw(s, 1, 2027))
        self.assertNotEqual(AR.draw(s, 1, 2027), AR.draw(s, 2, 2027))


class WorkStart(unittest.TestCase):
    def test_recorded_dates(self):
        s = NS(amateur_work_from={})
        g = NS(id=5)
        AR.started_work(s, g, 2030, 53)                                 # a winter decision: from next season
        self.assertEqual(s.amateur_work_from[5], (2031, 1))
        self.assertEqual(AR.seasons_in_work(s, 5, 2030), 0)
        self.assertEqual(AR.seasons_in_work(s, 5, 2031), 1)
        AR.started_work(s, g, 2031, 17)                                 # mid-season (the work pathway)
        self.assertEqual(AR.seasons_in_work(s, 5, 2031), 0)
        self.assertEqual(AR.seasons_in_work(s, 5, 2032), 1)

    def test_every_way_into_work_records_it(self):
        import inspect
        from golfsim import careers, work_pathway
        src = inspect.getsource(careers.decide)
        self.assertEqual(src.count("AR.started_work("), 3)              # graduation, took a job, back to amateur
        self.assertIn('AR.started_work(', inspect.getsource(work_pathway.decide))


if __name__ == '__main__':
    unittest.main()
