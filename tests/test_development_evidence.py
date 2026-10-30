"""Development evidence (diagnostics only): how each golfer started in the world's records -- age, attributes and
the hidden facts (potential, ceilings, peak age, aging rate) -- and what each source moved every season
(maturing, training, tournaments, injury, aging), by category and in Overall, with training weeks, coaching and
Overall before and after the winter's aging. Every season's change reconciles with its recorded parts; nothing in
the observer reads it; outcomes are unchanged (tools/equivalence_check.py, run separately).

Run from the project folder:  python -m unittest tests.test_development_evidence -v
"""
from __future__ import annotations

import gzip
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from golfsim import development as D                                    # noqa: E402
from golfsim.population import generate_world                           # noqa: E402
from golfsim.session import Session                                     # noqa: E402

TOL = 0.002                       # archived numbers are rounded (4 places; creation Overall 2 places)


class Evidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        s = Session.create(cls.tmp / 'w', seed=97, workers=1, world=generate_world(seed=97, scale=0.03))
        s.advance(2 * 52 + 2)                                             # two archived seasons
        cls.first = s.season.first_year
        s.close()
        years = sorted((cls.tmp / 'w' / 'archive' / 'years').glob('*.json.gz'))
        cls.seasons = {int(p.name.split('.')[0]): json.loads(gzip.open(p).read()) for p in years}

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def dev(self, y):
        return self.seasons[y]['diagnostics']

    def test_how_golfers_started(self):
        y0, y1 = sorted(self.seasons)
        born0 = self.dev(y0)['created']
        rows0 = self.seasons[y0]['careers']
        self.assertTrue(set(rows0) <= set(born0))                         # every golfer of the first season
        self.assertEqual({r['path'] for r in born0.values()}, {'initial'})
        born1 = self.dev(y1)['created']
        paths = {r['path'] for r in born1.values()}
        self.assertIn('junior', paths)
        for gid, r in born1.items():
            self.assertEqual(r['year'], y1)
            self.assertEqual(len(r['attrs']), 21)
            self.assertEqual(len(r['ceilings']), 21)
            if r['path'] == 'junior':
                self.assertEqual(r['age'], 18)
            for a, c in zip(r['attrs'], r['ceilings']):                   # (hidden: a ceiling is never below)
                self.assertGreaterEqual(c + 0.011, a)

    def test_each_seasons_change_adds_up(self):
        checked = 0
        for y in sorted(self.seasons):
            d = self.dev(y)
            prev = self.seasons.get(y - 1, {}).get('diagnostics', {}).get('development', {})
            for gid, v in d['development'].items():
                if gid in d['created']:
                    start = d['created'][gid]['overall']
                elif gid in prev and prev[gid][D.OV_POST]:
                    start = prev[gid][D.OV_POST]
                else:
                    continue
                before_aging = sum(v[D.OVERALL + i] for i in range(4))   # maturing, training, tournaments, injury
                self.assertAlmostEqual(v[D.OV_PRE] - start, before_aging, delta=TOL + 0.005 * (gid in d['created']),
                                       msg=(y, gid))
                if v[D.OV_POST]:                                          # (retiring golfers skip the aging)
                    self.assertAlmostEqual(v[D.OV_POST] - v[D.OV_PRE], v[D.OVERALL + 4], delta=TOL, msg=(y, gid))
                by_cat = [sum(v[s * 5 + c] for c in range(5)) for s in range(5)]
                self.assertTrue(all(abs(x) < 1e3 for x in by_cat))
                checked += 1
        self.assertGreater(checked, 1000)

    def test_sources_behave_as_the_rules_say(self):
        y = max(self.seasons)
        d = self.dev(y)
        rows = self.seasons[y]['careers']
        trained = [v for v in d['development'].values() if sum(v[D.TRAIN_WEEKS:D.TRAIN_WEEKS + 5])]
        self.assertTrue(trained)
        for v in d['development'].values():
            self.assertGreaterEqual(v[0 * 5 + 0], 0)                      # maturing only ever adds (physical)
            self.assertTrue(all(v[0 * 5 + c] == 0 for c in range(1, 5)))  # ... and only to physical attributes
            self.assertLessEqual(v[3 * 5 + 0], 0)                         # injury only takes away
            self.assertEqual(v[2 * 5 + 0], 0)                             # tournaments teach no physical attribute
            if v[D.COACH_Q]:
                self.assertGreater(sum(v[D.TRAIN_WEEKS:D.TRAIN_WEEKS + 5]), 0)
        juniors = [g for g, r in d['created'].items() if r['path'] == 'junior']
        self.assertTrue(any(d['development'][g][0] > 0 for g in juniors if g in d['development']))   # they mature
        self.assertTrue(rows)

    def test_the_observer_never_reads_it(self):
        for p in (ROOT / 'tools').glob('observer*.py'):
            self.assertNotIn("'diagnostics'", p.read_text(), p.name)      # (hidden facts stay out of the UI)


if __name__ == '__main__':
    unittest.main()
