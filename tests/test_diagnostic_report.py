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
    """The saved state keeps a guard stop whatever happened after it, so the report states only what is recorded:
    the seasons recorded of those requested, and the stop kept in the state -- never "resumed" or "ended at", which
    only the Provenance section (segment evidence) can say. Season times are summed over every recorded season."""

    STOP = 'season 2033 took 491 s (limit 420 s)'

    def fake(self, years, stopped=None, asked=10, slow=2033):
        from types import SimpleNamespace as NS
        perf = {y: {'skip': 491.0 if y == slow else 210.0, 'simulate': 190.0, 'save': 10.0, 'publish': 4.0,
                    'archive_mb': 1.0, 'checkpoint_mb': 1.0} for y in years}
        d = {'perf': perf, 'amateur_support': True, **({'stopped': stopped} if stopped else {})}
        return NS(name='B', seed=2027, years=list(years), d=d,
                  man={'commit': '473690a', 'years_requested': asked, 'machine': 'm'})

    def assertNeutral(self, text):
        for word in ('resume', 'completed', 'ended', 'finished', 'running'):
            self.assertNotIn(word, text.lower())

    def test_every_season_recorded_with_an_earlier_guard_stop(self):
        r = self.fake(range(2027, 2037), self.STOP)
        got = DR.ended(r)
        self.assertEqual(got, f'10 of 10 requested seasons recorded; a guard stop is recorded in the saved state '
                              f'({self.STOP})')
        self.assertNeutral(got)
        row = next(l for l in DR.overview([r]) if l.startswith('| B'))
        self.assertIn(f'| {round((9 * 210 + 491) / 60)} min |', row)              # every recorded season's time

    def test_a_guard_on_the_final_requested_season_is_not_called_a_resume(self):
        stop = 'season 2036 took 450 s (limit 420 s)'
        got = DR.ended(self.fake(range(2027, 2037), stop, slow=2036))
        self.assertEqual(got, f'10 of 10 requested seasons recorded; a guard stop is recorded in the saved state ({stop})')
        self.assertNeutral(got)

    def test_an_ongoing_resumed_segment_is_not_shown_as_ended_at_the_stop(self):
        got = DR.ended(self.fake(range(2027, 2055), self.STOP, asked=45))      # run A: 28 recorded, resumed, running
        self.assertTrue(got.startswith('28 of 45 requested seasons recorded'), got)
        self.assertFalse(got.startswith(self.STOP))
        self.assertNeutral(got)

    def test_stopped_and_not_resumed_reads_the_same_way(self):
        got = DR.ended(self.fake(range(2027, 2034), self.STOP))
        self.assertEqual(got, f'7 of 10 requested seasons recorded; a guard stop is recorded in the saved state '
                              f'({self.STOP})')

    def test_no_stop(self):
        self.assertEqual(DR.ended(self.fake(range(2027, 2030), asked=45)), '3 of 45 requested seasons recorded')
        self.assertEqual(DR.ended(self.fake(range(2027, 2037))), '10 of 10 requested seasons recorded')

    def test_a_season_above_the_guard_is_marked(self):
        out = '\n'.join(DR.performance([self.fake(range(2027, 2037), self.STOP)]))
        self.assertIn('491 (above the guard)', out)
        self.assertIn('Seasons above the 420 s guard: B 2033 (491 s)', out)


class ExclusionByGroup(unittest.TestCase):
    """F1.h: no start and financial exclusion are counted apart, each rate with its denominator; cash-blocked weeks are
    counted only for full-time amateurs outside college, so that is their denominator."""

    @staticmethod
    def run_(name, rows):
        from types import SimpleNamespace as NS
        return NS(name=name, years=[2030], amateurs=lambda y: rows)

    # (age, lifestyle, college, rank, events, blocked count, band, drawn, family money, took work, region)
    B = {1: (22, 'full_time', False, 400, 0, 9, None, 0, False, None, 'r'),     # no start, priced out (8+)
         2: (22, 'full_time', False, 410, 0, 0, None, 0, False, None, 'r'),     # no start, never priced out
         3: (22, 'full_time', False, 420, 6, 2, 'C', 5000, False, None, 'r'),   # played, priced out some weeks
         4: (22, 'full_time', True, 430, 0, 0, None, 0, False, None, 'r'),      # college: not tracked
         5: (22, 'part_time', False, 440, 3, 0, None, 0, False, None, 'r'),     # working: not tracked
         6: (22, 'part_time', False, 450, 2, 8, None, 0, False, 30, 'r')}       # took work by the pathway
    C = {1: (22, 'full_time', False, 400, 0, 3, None, 0, False, None, 'r')}

    def table(self):
        out = DR.breakdowns(self.run_('B', self.B), self.run_('C', self.C))
        return [l for l in out if l.startswith('| 21-22 |')]

    def test_rates_with_denominators(self):
        b, c = self.table()
        cells = [x.strip() for x in b.strip('|').split('|')]
        self.assertEqual(cells[:10], ['21-22', 'B', '6', '3 / 6 (50.0%)', '3', '1', '2 / 3 (66.7%)', '1 / 3 (33.3%)',
                                      '1 / 3 (33.3%)', '1 / 3 (33.3%)'])               # the conversion: not tracked
        self.assertEqual(cells[10:], ['1 / 6 (16.7%)', '$5,000', '1 / 1 (100.0%)'])
        cells = [x.strip() for x in c.strip('|').split('|')]
        self.assertEqual(cells, ['21-22', 'C', '1', '1 / 1 (100.0%)', '1', '0', '1 / 1 (100.0%)', '0 / 1 (0.0%)',
                                 '1 / 1 (100.0%)', '0 / 1 (0.0%)', '—', '—', '—'])

    def test_zero_start_is_not_called_financial_exclusion(self):
        text = '\n'.join(DR.breakdowns(self.run_('B', self.B), self.run_('C', self.C)))
        self.assertIn('Starting no event is not the same as being priced out', text)
        self.assertIn('No start, never cash-blocked', text)
        self.assertIn('Pathway conversions excluded from the tracked denominators: B 1, C 0 golfer-seasons.', text)
        self.assertIn('not a paired-person causal estimate', text)
        self.assertIn('golfer-seasons, not unique people', text)

if __name__ == '__main__':
    unittest.main()
