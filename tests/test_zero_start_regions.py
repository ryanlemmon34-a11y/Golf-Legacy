"""The zero-start audit by region and circuit: every full-time amateur season counted once (the cells add up to
the cohort), and the affordability evidence read from a world's save without changing it.

Run from the project folder:  python -m unittest tests.test_zero_start_regions -v
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
from golfsim.population import generate_world                         # noqa: E402
from golfsim.session import Session                                   # noqa: E402
import zero_start_audit as Z                                          # noqa: E402


class Audit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        s = Session.create(cls.tmp / 'w', seed=71, workers=1, world=generate_world(seed=71, scale=0.03))
        s.advance(2 * 52 + 1)
        cls.amateurs = sum(1 for g in s.season.world.golfers if g.status == 'amateur' and g.lifestyle == 'full_time'
                           and not (g.tour or '').startswith('CO_'))
        s.close()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_cells_add_up(self):
        r = Z.audit(self.tmp / 'w' / 'archive')
        cells = r['cells']
        self.assertEqual(sum(c['seasons'] for c in cells.values()), r['totals']['full-time amateur'])
        self.assertEqual(sum(c['zero'] for c in cells.values()), r['zeros']['full-time amateur'])
        for c in cells.values():
            self.assertEqual(c['all_weeks']['recorded'], c['all_weeks']['played'] + c['all_weeks']['injured']
                             + sum(v for k, v in c['all_weeks'].items() if k not in ('recorded', 'played', 'injured')))
        self.assertIn('by region and circuit', Z.report(r))

    def test_affordability_reads_the_save_only(self):
        w = self.tmp / 'w'
        before = {p: p.stat().st_mtime_ns for p in w.rglob('*') if p.is_file()}
        a = Z.affordability(w)
        self.assertEqual(sum(r['n'] for r in a['rows'].values()), self.amateurs)
        self.assertEqual({p: p.stat().st_mtime_ns for p in w.rglob('*') if p.is_file()}, before)
        self.assertIn('Cannot afford even that', Z.affordability_report(a))


if __name__ == '__main__':
    unittest.main()
