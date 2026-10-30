"""The five correctness fixes of the pinned pretest review (roadmap, 29 October 2026):

1. a replay reveals nothing beyond the round shown (no winner, final places, playoff or later scorecard rounds);
2. a record's "currently extending" merges this season's results (a streak broken, or a partnership ended, since
   the last archived season is not current);
3. the starts a profile counts and the list its links open use one scope (qualifying stages apart, on request);
4. restoring a removed world keeps it listed in the trash until the move has succeeded;
5. without the history index, results keep their coach, caddie and entry route (integer and string ids alike).

Run from the project folder:  python -m unittest tests.test_pretest_fixes -v
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
from golfsim.history_stats import HistoryStats                         # noqa: E402
from golfsim.population import generate_world                           # noqa: E402
from golfsim.session import Session                                     # noqa: E402
import observer as O                                                    # noqa: E402
import observer_data as OD                                              # noqa: E402
import observer_history as OH                                           # noqa: E402
import observer_worlds as WL                                            # noqa: E402


class WorldFixes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        s = Session.create(cls.tmp / 'w', seed=23, workers=1, world=generate_world(seed=23, scale=0.02))
        s.advance(52 + 3)
        s.close()
        cls.w = O.World(cls.tmp / 'w', workers=1)
        cls.w.reload()

    @classmethod
    def tearDownClass(cls):
        cls.w.close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def page(self, path):
        u = urlparse(path)
        return O.render(self.w, u.path, parse_qs(u.query))[1]

    # 1 ------------------------------------------------------------------------------------------------------------
    def test_replay_reveals_nothing_beyond_the_round_shown(self):
        eid = '2027:TOUR_MASTERS'
        e = self.w.edition(eid)
        winner = next(r['person'] for r in e['rows'] if r['pos'] == 1)
        early = self.page(f'/event/{eid}?view=rounds&round=1')
        self.assertNotIn('Winner:', early)
        self.assertNotIn('final ', early.split('<tbody>')[1].split('</tbody>')[0])   # no final places in the rows
        self.assertNotIn('playoff (', early)
        self.assertIn('not shown in the replay until its final round', early)
        card = self.page(f'/event/{eid}?view=rounds&round=1&player={winner}')
        self.assertIn('<td>R1</td>', card)
        self.assertNotIn('<td>R2</td>', card)                                # later rounds stay hidden
        self.assertIn('Through round 1', card)
        self.assertIn('Winner:', self.page(f'/event/{eid}'))                 # the final result says who won

    def test_opening_the_replay_starts_at_round_one_and_keeps_the_round(self):
        eid = '2027:TOUR_MASTERS'
        e = self.w.edition(eid)
        winner = next(r['person'] for r in e['rows'] if r['pos'] == 1)
        entry = self.page(f'/event/{eid}?view=rounds')                       # the tab's own link: no round given
        self.assertIn('<strong>after round 1</strong>', entry)
        self.assertNotIn('Winner:', entry)
        self.assertNotIn('final ', entry.split('<tbody>')[1].split('</tbody>')[0])
        self.assertNotIn('>R2<', entry)                                      # one round's column only
        self.assertIn('round=1', entry.split('card</a>')[0].rsplit('href=', 1)[1])   # the card keeps round 1
        card = self.page(f'/event/{eid}?view=rounds&player={winner}')        # a card opened without a round: round 1
        self.assertIn('<td>R1</td>', card)
        self.assertNotIn('<td>R2</td>', card)
        self.assertIn('round=1', card.split('← leaderboard')[0])             # and back to the same round
        r2 = self.page(f'/event/{eid}?view=rounds&round=2')
        self.assertIn('<strong>after round 2</strong>', r2)
        self.assertIn('round=2', r2.split('card</a>')[0].rsplit('href=', 1)[1])

    # 3 ------------------------------------------------------------------------------------------------------------
    def test_starts_and_their_list_share_one_scope(self):
        base = {'week': 3, 'series': 'S', 'name': 'x', 'tour': 'PT_AMERICAS', 'category': 'regular', 'site': 0,
                'coach': 0, 'caddie': 0, 'route': None, 'prize': None, 'live': False, 'year': 2027}
        rows = [dict(base, event='2027:A', tier=1, pos=3), dict(base, event='2027:B', tier=1, pos=None),
                dict(base, event='2027:Q', tier=7, pos=2)]                    # a qualifying stage: not a start
        with mock.patch.object(OD, 'results', return_value=rows), \
                mock.patch.object(OD, 'start_prizes', return_value={}):
            starts = O._results(self.w, {'year': ['2027']}, 1)
            self.assertIn('2 of 2 starts', starts)
            self.assertNotIn('2027:Q', starts)
            self.assertIn('include the 1 qualifying stages', starts)
            both = O._results(self.w, {'year': ['2027'], 'quals': ['1']}, 1)
            self.assertIn('3 rows of 2 starts and 1 qualifying stages', both)
            self.assertIn('qualifying</span>', both)

    # 5 ------------------------------------------------------------------------------------------------------------
    def test_results_without_the_index_keep_staff_and_routes(self):
        a = self.w.a
        pid = next(g for g, *_ in a.index.db.execute(
            'SELECT person FROM starts WHERE coach > 0 AND caddie > 0 AND rid IS NOT NULL LIMIT 1'))
        indexed = [(r['event'], r['coach'], r['caddie'], r['route']) for r in OD.results(self.w, pid) if not r['live']]
        with mock.patch.object(a, 'index', None):
            plain = [(r['event'], r['coach'], r['caddie'], r['route']) for r in OD.results(self.w, pid) if not r['live']]
        self.assertTrue(indexed)
        self.assertEqual(sorted(plain), sorted(indexed))
        self.assertTrue(any(c for _, c, _, _ in plain) and any(rt for *_, rt in plain))
        self.assertEqual(OD.by_person({5: 'int'}, 5), 'int')
        self.assertEqual(OD.by_person({'5': 'str'}, 5), 'str')


class RecordStatusFix(unittest.TestCase):
    # 2 ------------------------------------------------------------------------------------------------------------
    def stub(self, live_finishes, coach_of=None):
        starts = {7: [(2030, 40, '2030:A', 'PT_AMERICAS', 1, 'pro', 3), (2030, 41, '2030:B', 'PT_AMERICAS', 1, 'pro', 5)]}
        stats = SimpleNamespace(starts=starts, in_scope=HistoryStats.in_scope)
        editions = {f'2031:E{i}': {'id': f'2031:E{i}', 'week': i, 'tour': 'PT_AMERICAS', 'tier': 1, 'kind': 'pro',
                                   'category': 'regular', 'finish': [[(7, pos, None)]]}
                    for i, pos in enumerate(live_finishes, 1)}
        live = SimpleNamespace(year=2031, editions=editions, coach_of=coach_of or {}, caddie_of={})
        return SimpleNamespace(stats=stats, live=live, a=SimpleNamespace(years=[2030]))

    def test_a_streak_broken_this_season_is_not_current(self):
        ev = ['2030:A', '2030:B']
        self.assertEqual(OH._streak_open(self.stub([]), 7, 'professional', ev, 'consecutive-cuts'), 1)
        self.assertEqual(OH._streak_open(self.stub([4, 9]), 7, 'professional', ev, 'consecutive-cuts'), 3)
        self.assertFalse(OH._streak_open(self.stub([4, None]), 7, 'professional', ev, 'consecutive-cuts'))
        self.assertFalse(OH._streak_open(self.stub([2]), 7, 'professional', ev, 'consecutive-wins'))

    def test_a_partnership_ended_this_season_is_not_current(self):
        row = {'current': True, 'person': 7, 'staff': 99}
        self.assertTrue(OH._together_now(self.stub([], {7: 99}), 'longest-coach-partnerships', row))
        self.assertFalse(OH._together_now(self.stub([], {7: 98}), 'longest-coach-partnerships', row))
        self.assertFalse(OH._together_now(self.stub([]), 'longest-coach-partnerships', dict(row, current=False)))


class RestoreFix(unittest.TestCase):
    # 4 ------------------------------------------------------------------------------------------------------------
    def setUp(self):
        self.lib = Path(tempfile.mkdtemp())
        (self.lib / 'Mine').mkdir()
        (self.lib / 'Mine' / 'CURRENT').write_text(json.dumps({'dir': 'gen-1'}))
        self.addCleanup(shutil.rmtree, self.lib, True)

    def test_a_failed_restore_keeps_the_world_listed_in_the_trash(self):
        WL.remove_world(self.lib, 'Mine')
        folder = WL.trashed(self.lib)[0][0]
        real = os.replace

        def locked(src, dst):
            raise PermissionError('a file is open in another program')
        with mock.patch.object(WL.os, 'replace', locked):
            with self.assertRaises(PermissionError):
                WL.restore_world(self.lib, folder)
        self.assertEqual([t[0] for t in WL.trashed(self.lib)], [folder])     # still listed, still restorable
        self.assertFalse((self.lib / 'Mine').exists())
        self.assertIs(WL.os.replace, real)
        WL.restore_world(self.lib, folder)
        self.assertTrue((self.lib / 'Mine' / 'CURRENT').exists())
        self.assertFalse((self.lib / 'Mine' / WL.REMOVED).exists())
        self.assertEqual(WL.trashed(self.lib), [])

    def test_a_failed_removal_puts_the_world_back(self):
        real_write = Path.write_text

        def failing(self_, *a, **k):
            if self_.name == WL.REMOVED:
                raise OSError('disk full')
            return real_write(self_, *a, **k)
        with mock.patch.object(Path, 'write_text', failing):
            with self.assertRaises(OSError):
                WL.remove_world(self.lib, 'Mine')
        self.assertTrue((self.lib / 'Mine' / 'CURRENT').exists())
        self.assertEqual(WL.trashed(self.lib), [])


if __name__ == '__main__':
    unittest.main()
