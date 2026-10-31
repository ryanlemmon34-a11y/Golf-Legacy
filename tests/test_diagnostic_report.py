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


if __name__ == '__main__':
    unittest.main()
