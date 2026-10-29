"""The live observer (opened on a session directory) shows the committed world and its history as one
generation, whatever another process does: an ordinary week, a season's end, a recovery that goes back to
an earlier generation, a publication still in progress. Refreshing never simulates or replays anything;
stale forms stay refused and resubmitted ones are applied once. A failed refresh of the records leaves no
partial statistics behind.

Run from the project folder:  python -m unittest discover -s tests -v
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from golfsim import archive as A                                      # noqa: E402
from golfsim import session as SES                                    # noqa: E402
from golfsim.history_stats import BOARDS, HistoryStats, board         # noqa: E402
from golfsim.population import generate_world                         # noqa: E402
from golfsim.session import Session                                   # noqa: E402
import observer                                                       # noqa: E402


def form(c, op):
    return {'weeks': ['1'], 'year': [str(c['year'])], 'week': [str(c['week'])], 'phase': [c['phase']], 'op': [op]}


def index_fds():
    if not os.path.isdir('/proc/self/fd'):
        return None
    n = 0
    for f in os.listdir('/proc/self/fd'):
        try:
            n += os.readlink(f'/proc/self/fd/{f}').endswith('index.sqlite')
        except OSError:
            pass
    return n


class LiveObserverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.base = cls.tmp / 'base'                                    # 2027 published; 2028 at week 51
        s = Session.create(cls.base, seed=21, workers=1, world=generate_world(seed=21, scale=0.05))
        s.advance(52 + 50)
        s.close()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def world(self, name):
        d = self.tmp / name
        shutil.copytree(self.base, d)
        w = observer.World(d)
        self.addCleanup(w.close)
        return d, w

    def agrees(self, w, other):
        """The observer's live world and history are the other process's committed generation."""
        self.assertEqual(w.session.generation, other.generation)
        self.assertEqual(w.session.cursor, other.cursor)
        self.assertEqual(w.session.season.wr_pos, other.season.wr_pos)
        self.assertEqual(int(w.a.stamp[0]), other.history_generation)
        self.assertEqual(w.a.years, A.read_manifest(other.dir / 'archive')['years'])

    def test_another_process_playing_a_week(self):
        d, w = self.world('week')
        old_form = form(w.session.cursor, 'drawn-before')
        other = Session.open(d, workers=1)
        self.addCleanup(other.close)
        other.advance_one_week()
        with mock.patch.object(SES.Session, '_step', side_effect=AssertionError('simulated')):
            w.reload()                                                 # a page: loaded, never simulated
            self.assertIn('2028, week 52', observer.page(w, 't', '')) # the date shown is the committed one
            fresh = observer.World(d)
            self.addCleanup(fresh.close)
            self.assertEqual(observer.rankings(w, {})[1], observer.rankings(fresh, {})[1])
            w.submit(old_form)                                          # a form drawn before: refused
        self.agrees(w, other)
        f = form(w.session.cursor, 'fresh')
        w.submit(f)
        w.submit(f)                                                    # the same form twice: applied once
        self.assertEqual(w.session.cursor, {'year': 2029, 'week': 1, 'phase': 'start'})
        other.refresh()
        self.agrees(w, other)

    def test_another_process_ending_the_season(self):
        d, w = self.world('season')
        other = Session.open(d, workers=1)
        self.addCleanup(other.close)
        other.advance(2)                                               # weeks 51-52: 2028 ends and is published
        w.reload()
        self.agrees(w, other)
        self.assertEqual(w.a.years, [2027, 2028])
        self.assertEqual(w.session.cursor, {'year': 2029, 'week': 1, 'phase': 'start'})

    def test_another_process_recovering_to_an_earlier_generation(self):
        d, w = self.world('rollback')
        other = Session.open(d, workers=1)
        other.advance(2)
        other.close()
        w.reload()
        self.assertEqual(w.a.years, [2027, 2028])
        gen = json.loads((d / 'CURRENT').read_text())['generation']
        (d / f'gen_{gen:06d}' / 'state.pkl.gz').write_bytes(b'damaged')   # 2028's end is lost
        other = Session.open(d, workers=1)                             # recovery: back to week 51 and 2027
        self.addCleanup(other.close)
        w.reload()
        self.agrees(w, other)
        self.assertEqual(w.a.years, [2027])
        self.assertEqual(w.session.cursor, {'year': 2028, 'week': 51, 'phase': 'week'})

    def test_a_publication_still_in_progress_keeps_the_previous_generation(self):
        d, w = self.world('publishing')
        before = (w.session.generation, w.session.cursor, w.a.stamp)
        other = Session.open(d, workers=1)
        def stop(name):
            if name == 'tables':
                raise KeyboardInterrupt('the owner is still publishing')
        with mock.patch.object(SES, '_publication_step', stop), self.assertRaises(KeyboardInterrupt):
            other.advance(2)                                           # committed; history not yet published
        other.close()
        (d / 'lock').write_text(SES._lock_owner())                     # its owner (alive) still holds the lock
        w.reload()                                                     # its owner holds the lock: wait
        self.assertEqual((w.session.generation, w.session.cursor, w.a.stamp), before)
        self.assertIn('still being published', observer.history_note(w))
        (d / 'lock').unlink()
        w.reload()                                                     # free: the observer completes it
        self.assertIsNone(w.behind)
        self.assertEqual(w.session.cursor, {'year': 2029, 'week': 1, 'phase': 'start'})
        self.assertEqual(w.a.years, [2027, 2028])
        self.assertEqual(int(w.a.stamp[0]), w.session.history_generation)


class RecordsRefreshTests(unittest.TestCase):
    """A failure while the records take in new seasons leaves no partial statistics."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.d = cls.tmp / 'world'
        s = Session.create(cls.d, seed=21, workers=1, world=generate_world(seed=21, scale=0.05))
        s.advance(52)                                                  # 2027
        s.close()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_a_failed_refresh_is_retried_from_scratch(self):
        w = observer.World(self.d / 'archive')
        self.addCleanup(w.close)
        w.stats                                                        # records built for 2027
        old = w.a
        s = Session.open(self.d, workers=1)
        s.advance(104)                                                 # 2028 and 2029 published
        s.close()
        real, calls = HistoryStats._from_index, []
        def fail_on_second(stats, archive, idx, y):
            calls.append(y)
            if len(calls) == 2:
                raise RuntimeError('disk error after one new season was taken in')
            return real(stats, archive, idx, y)
        start = index_fds()
        with mock.patch.object(HistoryStats, '_from_index', fail_on_second), self.assertRaises(RuntimeError):
            w.reload()
        self.assertIs(w.a, old)                                        # the previous snapshot stays, whole
        self.assertEqual(w.a.years, [2027])
        self.assertIsNone(w._stats)                                    # no partial statistics kept
        if start is not None:
            self.assertLessEqual(index_fds(), start + 1)               # the new snapshot was closed (SQLite may defer one)
        w.reload()                                                     # retried
        self.assertEqual(w.a.years, [2027, 2028, 2029])
        with A.Archive(self.d / 'archive') as fresh:
            ref = HistoryStats(fresh)
            for name in BOARDS:
                self.assertEqual(board(w.stats, name, n=50)[1], board(ref, name, n=50)[1], name)
            self.assertEqual(dict(w.stats.starts.items()), dict(ref.starts.items()))

    def test_statistics_extended_after_a_failure_read_everything_again(self):
        with A.Archive(self.d / 'archive') as a:
            stats = HistoryStats(a)
            stats.seen.discard(a.years[-1])                            # as if the last season were new
            with mock.patch.object(HistoryStats, '_from_index', side_effect=RuntimeError('fails')), \
                    self.assertRaises(RuntimeError):
                stats.extend(a)
            self.assertFalse(stats.complete)
            stats.extend(a)
            ref = HistoryStats(a)
            self.assertTrue(stats.complete)
            self.assertEqual(dict(stats.starts.items()), dict(ref.starts.items()))   # nothing counted twice


if __name__ == '__main__':
    unittest.main()
