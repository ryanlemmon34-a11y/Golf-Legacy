"""Long histories stay quick to browse: a world's own index is validated when the world opens and any missing
or stale season is rebuilt from the published season files; a history browsed read-only without a usable index
(an export, an unsupported save) gets a side index built in the background outside its folder, which is never
written; exports include the index by default.

Run from the project folder:  python -m unittest tests.test_history_access -v
"""
from __future__ import annotations

import hashlib
import shutil
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
from golfsim.archive import Archive, read_manifest                    # noqa: E402
from golfsim.population import generate_world                         # noqa: E402
from golfsim.session import Session                                   # noqa: E402
import observer as O                                                  # noqa: E402
import observer_data as OD                                            # noqa: E402
import observer_stats as ST                                           # noqa: E402


def digest(d):
    h = hashlib.sha256()
    for p in sorted(Path(d).rglob('*')):
        if p.is_file():
            h.update(str(p.relative_to(d)).encode())
            h.update(p.read_bytes())
    return h.hexdigest()


class Access(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        s = Session.create(cls.tmp / 'w', seed=17, workers=1, world=generate_world(seed=17, scale=0.02))
        s.advance(2 * 52 + 3)                                           # two archived seasons
        s.close()
        cls.a = Archive(cls.tmp / 'w' / 'archive')
        cls.years = cls.a.years
        cls.golfer = next(g for g in sorted(cls.a.people) if len(cls.a.playing_career(g)) == 2)

    @classmethod
    def tearDownClass(cls):
        cls.a.close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def copy(self, name):
        d = self.tmp / name
        shutil.copytree(self.tmp / 'w', d)
        return d

    def test_a_missing_index_is_rebuilt_when_the_world_opens(self):
        d = self.copy('missing')
        for p in (d / 'archive').glob('index.sqlite*'):
            p.unlink()
        self.assertIsNone(Archive(d / 'archive').index)
        Session.open(d, workers=1).close()
        a = Archive(d / 'archive')
        try:
            self.assertIsNotNone(a.index)
            self.assertEqual(a.index.years(), self.years)
            self.assertEqual(a.playing_career(self.golfer), self.a.playing_career(self.golfer))
        finally:
            a.close()

    def test_a_stale_season_is_reindexed(self):
        d = self.copy('stale')
        db = sqlite3.connect(d / 'archive' / 'index.sqlite')
        with db:
            db.execute("UPDATE meta SET value = 'years/elsewhere.json.gz' WHERE key = ?", (f'source:{self.years[0]}',))
            db.execute('DELETE FROM careers WHERE year = ?', (self.years[0],))
        db.close()
        self.assertIsNone(Archive(d / 'archive').index)                 # (a reader refuses it)
        Session.open(d, workers=1).close()
        a = Archive(d / 'archive')
        try:
            self.assertIsNotNone(a.index)
            m = read_manifest(d / 'archive')
            self.assertEqual(a.index.sources(), m['files']['years'])
            self.assertEqual(a.playing_career(self.golfer), self.a.playing_career(self.golfer))
        finally:
            a.close()

    def test_a_read_only_history_gets_a_side_index(self):
        dst = self.tmp / 'exported'
        shutil.copytree(self.tmp / 'w' / 'archive', dst, ignore=shutil.ignore_patterns('index.sqlite*'))
        before = digest(dst)
        w = O.World(dst, workers=1, read_only=True)
        try:
            self.assertIsNone(w.a.index)                                # first: the season files
            side = ST.index_path(w)
            self.assertFalse(str(side).startswith(str(dst)))            # never in the history's folder
            w._indexer.wait(300)
            self.assertTrue(w._indexer.finished())
            w.reload()
            self.assertIsNotNone(w.a.index)                             # then the side index
            self.assertEqual(w.a.index_path, side)
            self.assertEqual(OD.career_rows(w, self.golfer), self.a.playing_career(self.golfer))
            html = O.render(w, f'/golfer/{self.golfer}', {})[1]
            self.assertIn('Ratings over time', html)
        finally:
            w.close()
        self.assertEqual(digest(dst), before)                          # the folder is untouched
        w = O.World(dst, workers=1, read_only=True)                      # reopened: the side index at once
        try:
            self.assertIsNotNone(w.a.index)
            self.assertIsNone(w._indexer)
        finally:
            w.close()
        for p in side.parent.glob(side.name.split('.')[0] + '.*'):
            p.unlink()

    def test_exports_include_the_index_by_default(self):
        import observer_worlds as WL
        import inspect
        self.assertTrue(inspect.signature(WL.export_diagnostic).parameters['include_index'].default)
        src = Path(ROOT / 'tools' / 'observer_app.py').read_text()
        self.assertIn('name="index" value="yes" checked', src)


if __name__ == '__main__':
    unittest.main()
