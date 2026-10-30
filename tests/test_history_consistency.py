"""The observer's history is one consistent snapshot: what another session publishes, rolls back or
backfills meanwhile never mixes into it, and it shows the newer history only after a reload, all at once.
Snapshots release their index connections when replaced.

Run from the project folder:  python -m unittest discover -s tests -v
"""
from __future__ import annotations

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
from golfsim import archive_index as AI                               # noqa: E402
from golfsim.history_stats import BOARDS, HistoryStats, board         # noqa: E402
from golfsim.population import generate_world                         # noqa: E402
from golfsim.session import Session                                   # noqa: E402
import observer                                                       # noqa: E402


def view(w, pid):
    """Everything the observer shows that history feeds: a profile, starts, records, prize totals,
    weeks at No. 1, moments and the overview."""
    return {'profile': observer.golfer(w, {}, str(pid))[1], 'starts': list(w.stats.starts[pid]),
            'boards': {name: board(w.stats, name, n=30)[1] for name in BOARDS},
            'prize': w.stats.most_prize(50), 'no1': w.a.weeks_at_number_one(),
            'moments': w.a.moments(), 'overview': observer.overview(w, {})[1],
            'results': w.a.results(pid), 'career': w.a.playing_career(pid), 'years': list(w.a.years)}


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


class SnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.base = cls.tmp / 'base'                                    # one archived season
        s = Session.create(cls.base, seed=21, workers=1, world=generate_world(seed=21, scale=0.05))
        s.advance(52)
        s.close()
        cls.two = cls.tmp / 'two'                                      # and a second one
        shutil.copytree(cls.base, cls.two)
        s = Session.open(cls.two, workers=1)
        s.advance(52)
        s.close()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def copy(self, src, name):
        d = self.tmp / name
        shutil.copytree(src, d)
        return d

    def test_a_season_published_by_another_session_stays_out_until_reload(self):
        d = self.copy(self.base, 'publish')
        w = observer.World(d / 'archive')
        self.addCleanup(w.close)
        pid = board(w.stats, 'most-starts', n=1)[1][0]['person']
        before = view(w, pid)
        s = Session.open(d, workers=1)                                 # a separate session publishes 2028
        s.advance(52)
        self.assertEqual(view(w, pid), before)                         # profiles, starts, records, prize, No. 1
        w.reload()                                                     # the next page: all of 2028 at once
        after = view(w, pid)
        self.assertEqual(after['years'], [2027, 2028])
        with A.Archive(d / 'archive') as fresh:                        # identical to a fresh reading
            stats = HistoryStats(fresh)
            self.assertEqual(after['results'], fresh.results(pid))
            self.assertEqual(after['no1'], fresh.weeks_at_number_one())
            self.assertEqual(after['starts'], list(stats.starts[pid]))
            self.assertEqual(after['prize'], stats.most_prize(50))
            for name in BOARDS:
                self.assertEqual(after['boards'][name], board(stats, name, n=30)[1], name)
        self.assertGreater(len(after['results']), len(before['results']))
        s.close()
        w.close()

    def test_rollback_and_replay_never_mix_into_an_open_snapshot(self):
        d = self.copy(self.two, 'rollback')
        w = observer.World(d / 'archive')
        self.addCleanup(w.close)
        pid = board(w.stats, 'most-starts', n=1)[1][0]['person']
        before = view(w, pid)
        gen = int((d / 'CURRENT').read_text().split('"generation": ')[1].split(',')[0])
        (d / f'gen_{gen:06d}' / 'state.pkl.gz').write_bytes(b'damaged')  # 2028's commit is lost
        s = Session.open(d, workers=1)                                 # recovery rolls the history back
        self.assertEqual(view(w, pid)['results'], before['results'])   # the snapshot's index is unchanged
        self.assertEqual(w.a.weeks_at_number_one(), before['no1'])
        recap = w.a.recap(2028)
        w.a._years.clear()
        self.assertEqual(w.a.recap(2028), recap)                       # its own 2028 file: whole, unchanged
        old = w.a
        w.reload()
        self.assertEqual(w.a.years, [2027])
        self.assertTrue(all(r['year'] == 2027 for r in w.a.results(pid)))
        s.advance(52)                                                  # replayed and republished
        w.reload()
        self.assertEqual(w.a.years, [2027, 2028])
        self.assertIsNone(old.index)                                   # the replaced snapshot was closed
        self.assertEqual(view(w, pid), before | {'profile': view(w, pid)['profile'],
                                                 'overview': view(w, pid)['overview']})
        s.close()
        w.close()

    def test_an_interrupted_backfill_is_never_half_used_and_is_finished_later(self):
        d = self.copy(self.two, 'backfill')
        with A.Archive(d / 'archive') as a:
            reference = (a.weeks_at_number_one(), {pid: a.playing_career(pid) for pid in list(a.people)[:40]})
        idx = AI.ArchiveIndex(d / 'archive' / 'index.sqlite')
        with idx.db:                                                   # an index from before schema 2
            idx.db.execute('DELETE FROM careers')
            idx.db.execute('DELETE FROM number_one')
            idx.db.execute("DELETE FROM meta WHERE key LIKE 'derived:%'")
        idx.close()
        real = AI.ArchiveIndex._derived
        calls = []

        def interrupted(self, year, chunk):
            calls.append(year)
            if len(calls) == 2:
                raise KeyboardInterrupt                                # stopped after the first season
            return real(self, year, chunk)
        with mock.patch.object(AI.ArchiveIndex, '_derived', interrupted):
            with self.assertRaises(KeyboardInterrupt):
                Session.open(d, workers=1)
        with A.Archive(d / 'archive') as half:
            self.assertTrue(half.index.derived_complete([2027]))
            self.assertFalse(half.index.derived_complete(half.years))   # so the season files answer
            self.assertEqual(half.weeks_at_number_one(), reference[0])
            self.assertEqual({pid: half.playing_career(pid) for pid in reference[1]}, reference[1])
        Session.open(d, workers=1).close()                              # the owner finishes it
        with A.Archive(d / 'archive') as done:
            self.assertTrue(done.index.derived_complete(done.years))
            self.assertEqual(done.weeks_at_number_one(), reference[0])
            self.assertEqual({pid: done.playing_career(pid) for pid in reference[1]}, reference[1])

    def test_reloads_release_their_connections(self):
        d = self.copy(self.base, 'reloads')
        w = observer.World(d / 'archive')
        self.addCleanup(w.close)
        w.stats
        start = index_fds()
        pub = d / 'archive' / 'MANIFEST.json'
        text = pub.read_text()
        for i in range(12):                                            # twelve newly published manifests
            pub.write_text(text + ' ' * (i + 1))
            w.reload()
            observer.record(w, {}, 'most-wins')
        if start is not None:
            self.assertLessEqual(index_fds(), start + 1)               # (SQLite may defer one close)
        w.close()
        if start is not None:
            self.assertEqual(index_fds(), 0)


if __name__ == '__main__':
    unittest.main()
