"""The long runs' stopping conditions (docs/LONG_RUN_PLAN.md, tools/long_world.safeguards): a season over the
runaway limit, any failed reconciliation (cash, family and backers' money, staff payments, amateur support,
development evidence, the population's accounting) and low disk stop a run; a population change above 20 % is a
recorded flag, not a stop.

Run from the project folder:  python -m unittest tests.test_long_run_safeguards -v
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
import long_world as LW                                                   # noqa: E402


def ok(**kw):
    ch = {'reconcile_errors': 0, 'support_errors': 0, 'support_cap_errors': 0, 'development_errors': 0,
          'staff_violations': 0, 'caddie_paid': 10.0, 'caddie_received': 10.0, 'coach_paid': 5.0,
          'coach_received': 5.0, 'population_ok': True, 'active_before': 1000, 'exits': 50, 'juniors': 50,
          'active_after': 1000}
    ch.update(kw)
    return ch


class Safeguards(unittest.TestCase):
    def setUp(self):
        self.out = Path(tempfile.mkdtemp())

    def test_a_good_season_passes(self):
        data = {}
        LW.safeguards(data, 2030, ok(), 200.0, self.out, 1000)
        self.assertNotIn('flags', data)

    def test_runaway_season_stops(self):
        with self.assertRaisesRegex(LW.Stop, 'took 421 s'):
            LW.safeguards({}, 2030, ok(), 421.0, self.out, 1000)

    def test_every_reconciliation_stops(self):
        for kw in ({'reconcile_errors': 1}, {'support_errors': 2}, {'support_cap_errors': 1},
                   {'development_errors': 3}, {'staff_violations': 1}, {'caddie_received': 9.0},
                   {'population_ok': False}):
            with self.assertRaises(LW.Stop, msg=kw):
                LW.safeguards({}, 2030, ok(**kw), 100.0, self.out, 1000)

    def test_low_disk_stops(self):
        with mock.patch.object(LW.shutil, 'disk_usage', return_value=mock.Mock(free=2.5e9)):
            with self.assertRaisesRegex(LW.Stop, 'GB free'):
                LW.safeguards({}, 2030, ok(), 100.0, self.out, 1000)

    def test_population_change_is_a_flag(self):
        data = {}
        LW.safeguards(data, 2030, ok(active_after=1250, juniors=300), 100.0, self.out, 1000)
        self.assertIn('+25%', data['flags'][2030])
        LW.safeguards(data, 2031, ok(active_after=1150), 100.0, self.out, 1000)
        self.assertNotIn(2031, data['flags'])


if __name__ == '__main__':
    unittest.main()
