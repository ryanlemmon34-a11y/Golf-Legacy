"""History reading at scale: the index answers what used to need every season decoded, with exactly the
same answers; decoded seasons are bounded; derived tables follow recovery.

Run from the project folder:  python -m unittest discover -s tests -v
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from golfsim import archive as A                                      # noqa: E402
from golfsim.archive_index import ArchiveIndex                        # noqa: E402
from golfsim.history_stats import BOARDS, HistoryStats, board         # noqa: E402
from golfsim.population import generate_world                         # noqa: E402
from golfsim.session import Session                                   # noqa: E402


class IndexedHistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.dir = cls.tmp / 'world'
        s = Session.create(cls.dir, seed=21, workers=1, world=generate_world(seed=21, scale=0.1))
        s.advance(52)                                                    # two seasons, archived, each its
        s.advance(52)                                                    # own committed generation
        s.close()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _archives(self):
        """The same archive read with its index and without (a copy whose index is removed)."""
        plain = self.tmp / 'plain'
        if not plain.exists():
            shutil.copytree(self.dir / 'archive', plain)
            (plain / 'index.sqlite').unlink()
        return self.open_archive(self.dir / 'archive'), self.open_archive(plain)

    def open_archive(self, path):
        a = A.Archive(path)
        self.addCleanup(a.close)                                        # (releases its index connection)
        return a

    def test_indexed_records_equal_records_read_from_the_season_files(self):
        idx, files = self._archives()
        self.assertIsNotNone(idx.index)
        self.assertIsNone(files.index)
        a, b = HistoryStats(idx), HistoryStats(files)
        for name in BOARDS:
            self.assertEqual(board(a, name, n=100)[1], board(b, name, n=100)[1], name)
        for pid in list(b.starts)[:200]:
            self.assertEqual(a.starts[pid], b.starts[pid])               # the same starts, the same order
        self.assertEqual(idx.weeks_at_number_one(), files.weeks_at_number_one())
        for y in idx.years:
            self.assertEqual(idx.recap(y), files.recap(y))
            self.assertEqual(idx.moments(year=y), files.moments(year=y))
        pid = board(b, 'most-starts', n=1)[1][0]['person']
        self.assertEqual(idx.playing_career(pid), files.playing_career(pid))
        self.assertEqual(idx.moments(person=pid), files.moments(person=pid))
        for cid in sorted(idx.world['courses'])[:20]:
            self.assertEqual(idx.course(cid), files.course(cid))

    def test_decoded_seasons_are_bounded(self):
        _, files = self._archives()
        files.CACHE_SEASONS = 1
        HistoryStats(files)
        files.weeks_at_number_one()
        self.assertLessEqual(len(files._years), 1)

    def test_a_winner_at_any_site_counts_as_a_winner(self):
        """Multi-site events have a winner per site; the index answers for every site, not only the
        edition's first winner."""
        idx, files = self._archives()
        y, e = next((y, e) for y, e in files.events() if len(e['finish']) > 1 and e['finish'][1]
                    and any(p == 1 for _, p, _ in e['finish'][1]))
        for arc in (idx, files):                                         # read it as a professional event
            arc.world['series'][e['series']]['tier'] = 3
        second = next(g for g, p, _ in e['finish'][1] if p == 1)
        first = next(g for g, p, _ in e['finish'][0] if p == 1)
        self.assertNotEqual(second, first)
        self.assertIn(second, idx.professional_winners({second}, y))
        self.assertEqual(idx.professional_winners({second}, y), files.professional_winners({second}, y))

    def test_the_observer_opens_cold_and_warm_and_its_pages_work(self):
        import observer
        w = observer.World(self.dir)                                     # cold: nothing read yet
        title, html = observer.overview(w, {})
        self.assertIn('season recap', html)
        pid = board(w.stats, 'most-wins', n=1)[1][0]['person']
        self.assertIn('Career', observer.golfer(w, {}, str(pid))[1])
        self.assertTrue(observer.record(w, {}, 'most-wins')[1])
        stats = w.stats
        w.reload()                                                      # warm: nothing changed
        self.assertIs(w.stats, stats)
        self.assertLessEqual(len(w.a._years), A.Archive.CACHE_SEASONS)
        w.close()

    def test_derived_tables_follow_rollback_and_replay(self):
        d = self.tmp / 'replay'
        shutil.copytree(self.dir, d)
        gen = int((d / 'CURRENT').read_text().split('"generation": ')[1].split(',')[0])
        (d / f'gen_{gen:06d}' / 'state.pkl.gz').write_bytes(b'damaged')  # the second season's end is lost
        s = Session.open(d, workers=1)
        idx = ArchiveIndex(d / 'archive' / 'index.sqlite')
        years = idx.years()
        self.assertEqual({y for (y,) in idx.db.execute('SELECT DISTINCT year FROM careers')}, set(years))
        self.assertEqual({y for (y,) in idx.db.execute('SELECT DISTINCT year FROM number_one')}, set(years))
        self.assertTrue(idx.derived_complete(years))
        idx.close()
        self.assertEqual(years, [2027])                                 # the lost season is gone everywhere
        s.advance(52)                                                   # replay it
        idx = ArchiveIndex(d / 'archive' / 'index.sqlite')
        self.assertTrue(idx.derived_complete(idx.years()))
        self.assertEqual(idx.years(), [2027, 2028])
        idx.close()
        fresh = HistoryStats(self.open_archive(d / 'archive'))
        self.assertEqual(board(fresh, 'most-wins', n=50)[1],
                         board(HistoryStats(self.open_archive(self.dir / 'archive')), 'most-wins', n=50)[1])
        s.close()

    def test_an_index_from_before_schema_2_is_completed_by_its_session(self):
        d = self.tmp / 'old_index'
        shutil.copytree(self.dir, d)
        idx = ArchiveIndex(d / 'archive' / 'index.sqlite')
        with idx.db:                                                    # as written by an older engine
            idx.db.execute('DELETE FROM careers')
            idx.db.execute('DELETE FROM number_one')
            idx.db.execute("DELETE FROM meta WHERE key LIKE 'derived:%'")
        idx.close()
        before = self.open_archive(d / 'archive')
        self.assertFalse(before.index.derived_complete(before.years))   # readers fall back to the files
        answer = before.weeks_at_number_one()
        s = Session.open(d, workers=1)                                  # the owner completes it, once
        after = self.open_archive(d / 'archive')
        self.assertTrue(after.index.derived_complete(after.years))
        self.assertEqual(after.weeks_at_number_one(), answer)
        s.close()


if __name__ == '__main__':
    unittest.main()
