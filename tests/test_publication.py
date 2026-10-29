"""Publication is one atomic step for readers: a publisher stopped after any step leaves them one whole
published history (people, residence, relationships, records, starts, prizes, rankings all of one
generation), and the next session to open the world completes it. Archives from before manifests are
migrated by their owner, keeping the index they have.

Run from the project folder:  python -m unittest discover -s tests -v
"""
from __future__ import annotations

import gzip
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from golfsim import archive as A                                      # noqa: E402
from golfsim import session as SES                                    # noqa: E402
from golfsim.archive_index import ArchiveIndex                        # noqa: E402
from golfsim.history_stats import HistoryStats                        # noqa: E402
from golfsim.population import generate_world                         # noqa: E402
from golfsim.session import Session                                   # noqa: E402

STEPS = ('season files', 'index', 'index done', 'tables', 'manifest')


def history(d):
    """Everything a reader takes from the published history, by content."""
    with A.Archive(Path(d) / 'archive') as a:
        stats = HistoryStats(a)
        some = sorted(a.people)[::7]
        return {'years': a.years,
                'people': a.people,
                'residence': {pid: a.residence_at(pid, a.years[-1], 52) for pid in some},
                'relations': A._read(a.dir / a.files['relations']),
                'records': a.records,
                'starts': {pid: list(stats.starts[pid]) for pid in sorted(stats.starts)},
                'results': {pid: a.results(pid) for pid in some},
                'prize': stats.most_prize(200),
                'rankings': a.weeks_at_number_one(),
                'index_used': a.index is not None}


def stop_at(step):
    def stop(name):
        if name == step:
            raise KeyboardInterrupt(f'publisher stopped after: {name}')
    return mock.patch.object(SES, '_publication_step', stop)


class PublicationTests(unittest.TestCase):
    def same(self, seen, expected, what=''):
        """Equal histories, reported part by part (the parts are large)."""
        self.assertEqual(seen.keys(), expected.keys())
        for k in expected:
            self.assertTrue(seen[k] == expected[k], f'{what}: {k} differs')

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.base = cls.tmp / 'base'                                    # 2027 published, 2028 about to end
        s = Session.create(cls.base, seed=21, workers=1, world=generate_world(seed=21, scale=0.05))
        s.advance(52 + 51)
        s.close()
        cls.full = cls.tmp / 'full'                                    # the same world with 2028 published
        shutil.copytree(cls.base, cls.full)
        s = Session.open(cls.full, workers=1)
        s.advance(1)
        s.close()
        cls.h27, cls.h28 = history(cls.base), history(cls.full)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def copy(self, src, name):
        d = self.tmp / name
        shutil.copytree(src, d)
        return d

    def test_the_two_histories_differ(self):
        for key in ('years', 'people', 'relations', 'records', 'starts', 'prize', 'rankings'):
            self.assertNotEqual(self.h27[key], self.h28[key], key)
        self.assertTrue(self.h27['index_used'] and self.h28['index_used'])

    def test_a_publisher_stopped_after_any_step_leaves_one_whole_history(self):
        for step in STEPS:
            with self.subTest(step=step):
                d = self.copy(self.base, f'stop-{step}')
                s = Session.open(d, workers=1)
                with stop_at(step), self.assertRaises(KeyboardInterrupt):
                    s.advance(1)                                       # the season ends; publication stops
                s.close()
                seen = history(d)
                expected = self.h28 if step == 'manifest' else self.h27
                self.same(seen, expected, step)                        # everything of one generation, index too
                Session.open(d, workers=1).close()                     # the next owner completes it
                self.same(history(d), self.h28, step)

    def test_a_rollback_stopped_after_any_step_leaves_one_whole_history(self):
        for step in ('season files', 'index done', 'tables', 'manifest'):  # (no season to index)
            with self.subTest(step=step):
                d = self.copy(self.full, f'rollback-{step}')
                gen = json.loads((d / 'CURRENT').read_text())['generation']
                (d / f'gen_{gen:06d}' / 'state.pkl.gz').write_bytes(b'damaged')   # 2028's commit is lost
                with stop_at(step), self.assertRaises(KeyboardInterrupt):
                    Session.open(d, workers=1)                         # recovery publishes 2027's history
                seen = history(d)
                self.assertIn(seen['years'], ([2027], [2027, 2028]))
                self.same(seen, self.h28 if seen['years'] == [2027, 2028] else self.h27, step)
                Session.open(d, workers=1).close()
                self.same(history(d), self.h27, step)

    def test_published_files_are_never_rewritten(self):
        d = self.copy(self.base, 'immutable')
        a = d / 'archive'
        before = {p.name: (p.stat().st_ino, p.stat().st_mtime_ns) for p in a.rglob('*.json*')
                  if not p.name.startswith('MANIFEST')}
        named = set(A.read_manifest(a)['files']['years'].values())
        s = Session.open(d, workers=1)
        s.advance(1)
        s.close()
        for p in a.rglob('*.json*'):
            if p.name in before and p.relative_to(a).as_posix() in named:
                self.assertEqual((p.stat().st_ino, p.stat().st_mtime_ns), before[p.name], p.name)

    def test_an_archive_from_before_manifests_is_migrated_with_its_index(self):
        d = self.copy(self.full, 'legacy')
        a = d / 'archive'
        m = A.read_manifest(a)
        for key, name in A.LEGACY_FILES.items():                       # the layout older versions wrote
            shutil.copyfile(a / m['files'][key], a / name)
        for y, f in m['files']['years'].items():
            shutil.copyfile(a / f, a / 'years' / f'{y}.json.gz')
            (a / f).unlink()
        (a / 'PUBLISHED').write_text(str(m['generation']))
        for p in (a / 'MANIFEST.json', a / 'MANIFEST.prev.json'):
            p.unlink(missing_ok=True)
        with ArchiveIndex(a / 'index.sqlite') as idx, idx.db:
            idx.db.execute("DELETE FROM meta WHERE key LIKE 'source:%'")
        self.same(history(d), self.h28, 'legacy')                      # read as before (read-only)
        gen = json.loads((d / 'CURRENT').read_text())['generation']
        staged = json.loads((d / f'gen_{gen:06d}' / 'meta.json').read_text())['archive_staged']
        real, indexed = ArchiveIndex.index_year, []
        def index_year(idx, year, chunk, source=None):
            indexed.append(year)
            return real(idx, year, chunk, source)
        with mock.patch.object(ArchiveIndex, 'index_year', index_year):
            Session.open(d, workers=1).close()                         # migrated by its owner
        self.assertEqual(sorted(indexed), sorted(staged))              # its other rows kept, not rebuilt
        self.assertLess(len(indexed), len(self.h28['years']))
        self.assertIsNotNone(A.read_manifest(a))
        self.assertFalse((a / 'world.json').exists())
        self.same(history(d), self.h28, 'migrated')


if __name__ == '__main__':
    unittest.main()
