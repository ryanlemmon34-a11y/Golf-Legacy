"""Records and frivolities: one set of definitions over the history archive.

Run from the project folder:  python -m unittest discover -s tests -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from golfsim.history import Relations                                   # noqa: E402
from golfsim.history_stats import BOARDS, DEFINITIONS, HistoryStats, board   # noqa: E402


class FakeArchive:
    """A tiny hand-made history with known answers."""

    def __init__(self):
        self.world = {'first_year': 2027, 'series': {
            'M': {'name': 'Major', 'tour': 'MAJORS', 'tier': 0, 'kind': 'major', 'category': 'major'},
            'P': {'name': 'Premier', 'tour': 'PT_AMERICAS', 'tier': 1, 'kind': 'premier', 'category': 'standard'},
            'C': {'name': 'Challenger', 'tour': 'CH_EUROPE', 'tier': 2, 'kind': 'pro', 'category': 'regular'},
            'A': {'name': 'Amateur', 'tour': 'AM_EUROPE', 'tier': 6, 'kind': 'amateur', 'category': 'regular'},
            'Q': {'name': 'Qualifier', 'tour': 'QUALIFYING', 'tier': 7, 'kind': 'qualifying', 'category': 'qualifier'}}}
        self.people = {1: {'name': 'Veteran', 'born': 1990, 'initial': True, 'golfer': {'lifestyle': 'full_time'}},
                       2: {'name': 'Rookie', 'born': 2009, 'initial': False, 'golfer': {'lifestyle': 'full_time'}},
                       3: {'name': 'Grinder', 'born': 1995, 'initial': False, 'golfer': {'lifestyle': 'retired'}},
                       9: {'name': 'Coach', 'born': 1970, 'initial': True}}
        self.years = [2027, 2028]
        ev = lambda y, w, s, rows, team=None: {'id': f'{y}:{s}{w}', 'series': s, 'week': w, 'finish': [rows],
                                               'team': team or {}}
        self._ev = {
            2027: [ev(2027, 1, 'C', [(1, 1, 0), (2, 2, 0), (3, None, None)]),
                   ev(2027, 2, 'C', [(2, 1, 0), (1, 2, 0), (3, 2, 0)]),
                   ev(2027, 3, 'Q', [(3, 1, 0)]),                                   # not a start
                   ev(2027, 18, 'M', [(2, 1, 0), (1, 3, 0)], {2: (9, 0)})],
            2028: [ev(2028, 5, 'P', [(3, 2, 0), (1, 1, 0)]),
                   ev(2028, 6, 'A', [(3, 2, 0)]),
                   ev(2028, 18, 'M', [(1, 1, 0), (2, 2, 0)], {1: (9, 0)})]}
        self.rel = Relations()
        self.rel.begin('coach', 9, 2, (2027, 1), 'fee', 'golfer')

    def events(self):
        for y in self.years:
            for e in self._ev[y]:
                yield y, e

    def year(self, y):
        return {'careers': {1: {'prize': 100}, 2: {'prize': 50}}}

    def name(self, pid):
        return self.people[pid]['name']

    def weeks_at_number_one(self, amateur=False):
        return {1: 30, 2: 74}


class HistoryStatsTests(unittest.TestCase):
    def setUp(self):
        self.h = HistoryStats(FakeArchive())

    def test_starts_wins_and_scope_by_classification_when_played(self):
        self.assertEqual(len(self.h.starts[3]), 4)                          # the qualifier is not a start
        wins = {r['person']: r['value'] for r in self.h.most_wins()}
        self.assertEqual(wins, {1: 3, 2: 2})
        self.assertEqual({r['person']: r['value'] for r in self.h.most_wins('major')}, {1: 1, 2: 1})
        self.assertEqual({r['person']: r['value'] for r in self.h.most_wins('CH_EUROPE')}, {1: 1, 2: 1})
        top = self.h.most_wins()[0]
        self.assertEqual(top['evidence'], ['2027:C1', '2028:P5', '2028:M18'])   # every win linked

    def test_ages_debuts_and_flags(self):
        young = self.h.winners_by_age('major')[0]
        self.assertEqual((young['person'], young['value'], young['evidence']), (2, 18, ['2027:M18']))
        old = self.h.winners_by_age('major', youngest=False)[0]
        self.assertEqual((old['person'], old['value']), (1, 38))
        debuts = self.h.debuts_by_age('premier')
        self.assertEqual([r['person'] for r in debuts], [2, 3])              # the veteran's debut is unknown
        self.assertIn(1, [r['person'] for r in self.h.debuts_by_age('premier', include_partial=True)])
        self.assertTrue(next(r for r in self.h.most_wins() if r['person'] == 1)['partial'])

    def test_unfinished_and_finished_careers_are_separate(self):
        self.assertEqual([r['person'] for r in self.h.most_starts_without_win(status='retired')], [3])
        self.assertEqual(self.h.most_starts_without_win(status='active'), [])
        self.assertEqual(self.h.most_runner_ups_without_win()[0]['value'], 3)    # ties for second count
        first = {r['person']: r['value'] for r in self.h.starts_before_first_win()}
        self.assertEqual(first, {2: 1})                                       # partial careers left out

    def test_relationships_and_rankings(self):
        coaches = self.h.coaches_with_most_major_champions()
        self.assertEqual((coaches[0]['person'], coaches[0]['value']), (9, 2))
        self.assertEqual(self.h.weeks_at_number_one()[0]['person'], 2)
        part = self.h.longest_partnerships('coach')[0]
        self.assertEqual((part['person'], part['staff'], part['current']), (2, 9, True))

    def test_every_board_runs_and_is_defined(self):
        for name in BOARDS:
            title, rows = board(self.h, name, n=5)
            self.assertTrue(title)
            for r in rows:
                self.assertTrue({'person', 'value', 'evidence', 'active', 'partial'} <= set(r))
        self.assertTrue({'start', 'win', 'major', 'debut', 'age', 'scope'} <= set(DEFINITIONS))


if __name__ == '__main__':
    unittest.main()
