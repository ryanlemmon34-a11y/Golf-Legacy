"""The diagnostic report (tools/diagnostic_report.py): "Overall at 19" is the rating of the season a golfer was
exactly 19, never a later one; a late entrant shows it as unavailable, with their first recorded rating and age
labelled apart.

Run from the project folder:  python -m unittest tests.test_diagnostic_report -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
import diagnostic_report as DR                                           # noqa: E402


class FakeRun:
    """Two golfers who arrived during a run: one at 18, one (a late entrant) at 22."""
    name, years = 'A', [2030, 2031, 2032, 2033, 2034, 2035]

    def __init__(self):
        g = {1: dict(name='Early', country='USA', born=2012, created=2030, initial=False),
             2: dict(name='Late', country='Japan', born=2008, created=2030, initial=False)}
        self.dbg = {y: {1: [60.0 + y - 2030, 70.0, None], 2: [72.0 + (y - 2030) / 2, 75.0, None]} for y in self.years}
        rows = {y: {gid: {'wins': 0, 'majors': 0} for gid in g} for y in self.years}
        self.d = {'golfers': g, 'rows': rows, 'transitions': {}}

    def exits(self):
        return {}


class AtNineteen(unittest.TestCase):
    def test_exact_age_only(self):
        ov = {2030: 60.0, 2031: 61.0, 2032: 62.0}
        self.assertEqual(DR.rating_at_age(ov, 2012, 19), 61.0)
        self.assertIsNone(DR.rating_at_age(ov, 2008, 19))                 # 22-24 in these seasons: not at 19

    def test_the_late_entrant_is_unavailable_and_labelled(self):
        out = '\n'.join(DR.careers(FakeRun()))
        late = next(l for l in out.splitlines() if l.startswith('| Late'))
        early = next(l for l in out.splitlines() if l.startswith('| Early'))
        self.assertEqual(late.split(' | ')[3], '—')                        # Overall at 19: unavailable
        self.assertIn('72.0 at 22', late)                                 # first recorded, with its age
        self.assertEqual(early.split(' | ')[3], '61.0')                    # the season they were 19
        self.assertIn('60.0 at 18', early)


class RunEndings(unittest.TestCase):
    """A safeguard stop stays in a run's saved state when the run is resumed: the report says the run completed after
    a resume (the stop disclosed), sums the season times of every segment, and marks a season above the guard."""

    STOP = 'season 2033 took 491 s (limit 420 s)'

    def fake(self, years, stopped=None, asked=10):
        from types import SimpleNamespace as NS
        perf = {y: {'skip': 491.0 if y == 2033 else 210.0, 'simulate': 190.0, 'save': 10.0, 'publish': 4.0,
                    'archive_mb': 1.0, 'checkpoint_mb': 1.0} for y in years}
        d = {'perf': perf, 'amateur_support': True, **({'stopped': stopped} if stopped else {})}
        return NS(name='B', seed=2027, years=list(years), d=d,
                  man={'commit': '473690a', 'years_requested': asked, 'machine': 'm'})

    def test_resumed_to_completion(self):
        r = self.fake(range(2027, 2037), self.STOP)
        self.assertEqual(DR.ended(r), f'completed after a resume (an earlier segment stopped: {self.STOP})')
        row = next(l for l in DR.overview([r]) if l.startswith('| B'))
        self.assertIn(f'| {round((9 * 210 + 491) / 60)} min |', row)              # every segment's seasons

    def test_stopped_and_not_resumed(self):
        self.assertEqual(DR.ended(self.fake(range(2027, 2034), self.STOP)), self.STOP)

    def test_still_running_or_complete(self):
        self.assertEqual(DR.ended(self.fake(range(2027, 2030), asked=45)), 'not finished (3 of 45 seasons when read)')
        self.assertEqual(DR.ended(self.fake(range(2027, 2037))), 'completed')

    def test_a_season_above_the_guard_is_marked(self):
        out = '\n'.join(DR.performance([self.fake(range(2027, 2037), self.STOP)]))
        self.assertIn('491 (above the guard)', out)
        self.assertIn('Seasons above the 420 s guard: B 2033 (491 s)', out)


if __name__ == '__main__':
    unittest.main()
