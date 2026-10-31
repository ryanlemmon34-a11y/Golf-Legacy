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


class ResumedSupportSetting(unittest.TestCase):
    """A resumed run keeps its world's amateur-support setting: a mismatched flag is refused, never relabelled."""

    def test_a_mismatch_is_refused(self):
        for saved, asked in ((False, True), (True, False)):
            with self.assertRaises(SystemExit):
                LW.check_support(saved, asked, 'seed 2027')
        LW.check_support(False, False, 'seed 2027')
        LW.check_support(True, True, 'seed 2027')

    def test_the_command_line_refuses_a_support_off_folder_resumed_with_defaults(self):
        import json
        out = Path(tempfile.mkdtemp())
        (out / 'manifest.json').write_text(json.dumps({'amateur_support': False, 'seeds': {'2027': {}}}))
        argv = ['long_world.py', '--session', '--resume', '--seeds', '2027', '--out', str(out)]
        with mock.patch.object(sys, 'argv', argv), mock.patch.object(LW, 'git_state', return_value=('x', False)), \
                mock.patch('golfsim.savegame.engine_id', return_value='e'), \
                mock.patch.object(LW, 'run_world_session') as run:
            json_man = json.loads((out / 'manifest.json').read_text())
            json_man['engine'] = 'e'
            (out / 'manifest.json').write_text(json.dumps(json_man))
            with self.assertRaisesRegex(SystemExit, 'amateur support off'):
                LW.main()
            run.assert_not_called()
        self.assertFalse(json.loads((out / 'manifest.json').read_text())['amateur_support'])   # left as it was


class WorldRulesRecorded(unittest.TestCase):
    """Both run modes record the world's work-pathway minimum age for the report, after creating or resuming the
    world; a world without the setting (started before rules 2026-11-10) records 21, the report's own fallback."""

    def test_the_age_in_force_is_recorded(self):
        from types import SimpleNamespace as NS
        for season, want in ((NS(work_pathway_min_age=18), 18), (NS(work_pathway_min_age=21), 21), (NS(), 21)):
            data = {}
            LW.record_world_rules(data, season)
            self.assertEqual(data['work_pathway_min_age'], want)

    def test_both_modes_record_it(self):
        import inspect
        for fn in (LW.run_world, LW.run_world_session):           # (the default mode and --session)
            src = inspect.getsource(fn)
            self.assertIn('record_world_rules(data, ', src, fn.__name__)
            self.assertLess(src.index("first = data['first']") if fn is LW.run_world else src.index('check_support('),
                            src.index('record_world_rules(data, '), fn.__name__)   # after create or resume
            loop = 'for y in range(' if fn is LW.run_world else "while data['years'] < years"
            self.assertLess(src.index('record_world_rules(data, '), src.index(loop), fn.__name__)   # before play

    def test_a_new_world_records_18(self):
        from golfsim.population import generate_world
        from golfsim.season import Season
        s = Season(generate_world(seed=5, scale=0.01), seed=5, development=True, workers=1)
        data = {}
        LW.record_world_rules(data, s)
        self.assertEqual(data['work_pathway_min_age'], 18)


class ComparisonArms(unittest.TestCase):
    """A controlled comparison arm sets the named per-world settings before the world plays and keeps them in the
    run state; a resume asking for another arm is refused; unnamed settings keep the build's defaults."""

    def test_settings_applied_and_kept(self):
        from types import SimpleNamespace as NS
        season, data = NS(work_pathway_min_age=18, college_open_access=True), {}
        LW.apply_arm(data, season, {'work_pathway_min_age': 21, 'college_open_access': False})
        self.assertEqual((season.work_pathway_min_age, season.college_open_access), (21, False))
        self.assertEqual(data['arm'], {'work_pathway_min_age': 21, 'college_open_access': False})
        LW.record_world_rules(data, season)
        self.assertEqual(data['work_pathway_min_age'], 21)              # the report reads the arm's age

    def test_unnamed_settings_keep_the_defaults(self):
        from types import SimpleNamespace as NS
        season, data = NS(work_pathway_min_age=18, college_open_access=True), {}
        LW.apply_arm(data, season, {'work_pathway_min_age': None, 'college_open_access': None})
        self.assertEqual((season.work_pathway_min_age, season.college_open_access), (18, True))
        self.assertEqual(data['arm'], {})

    def test_a_resume_must_ask_for_the_same_arm(self):
        from types import SimpleNamespace as NS
        season, data = NS(work_pathway_min_age=18, college_open_access=True), {'arm': {'work_pathway_min_age': 21}}
        with self.assertRaisesRegex(SystemExit, 'same settings'):
            LW.apply_arm(data, season, {'work_pathway_min_age': 18})
        LW.apply_arm(data, season, {'work_pathway_min_age': 21})         # the same arm: fine
        self.assertEqual(season.work_pathway_min_age, 21)


if __name__ == '__main__':
    unittest.main()
