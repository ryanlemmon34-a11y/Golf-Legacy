"""GOAT Lab: careers ranked by editable weights (or a safe formula) over components the observer already works out,
with definitions, scope and coverage shown, deterministic ties, invalid formulas reported (never run), and
partial careers and missing figures marked.

Run from the project folder:  python -m unittest tests.test_goat -v
"""
from __future__ import annotations

import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
from golfsim import scopes as SC                                      # noqa: E402
from golfsim.history_stats import board                               # noqa: E402
from golfsim.population import generate_world                         # noqa: E402
from golfsim.session import Session                                   # noqa: E402
import observer as O                                                  # noqa: E402
import observer_goat as G                                             # noqa: E402
import observer_history as OH                                         # noqa: E402
import observer_stats as ST                                           # noqa: E402


def plant_old_hiding(world_dir, since=(0, 0)):
    """The removed Hide results setting as an earlier build wrote it (everything hidden, nothing revealed)."""
    import json
    (Path(world_dir) / 'observer_spoilers.json').write_text(json.dumps(
        {'format': 'golf-legacy-spoilers/1', 'hide': True, 'from': list(since), 'revealed': {}}))


class Formulas(unittest.TestCase):
    def test_only_the_allowed_syntax(self):
        for ok in ('majors', '8*majors + 3*wins', 'max(weeks_no1, 10) - sqrt(starts) / 2', '-wins ** 2', 'log(1 + prize_m)'):
            G.compile_formula(ok)
        for bad in ('__import__("os")', 'wins.real', 'open("x")', '"a"', 'lambda: 1', '[w for w in x]', 'wins if 1 else 2',
                    'unknown + 1', 'wins = 1', 'True', 'majors(1)', 'x' * 500, 'min()'):
            with self.assertRaises(G.FormulaError, msg=bad):
                G.compile_formula(bad)

    def test_values_that_cannot_be_worked_out(self):
        self.assertIsNone(G.evaluate(G.compile_formula('majors / 0'), {'majors': 2}))
        self.assertIsNone(G.evaluate(G.compile_formula('log(0)'), {}))
        self.assertIsNone(G.evaluate(G.compile_formula('wins ** 100'), {'wins': 3}))
        self.assertEqual(G.evaluate(G.compile_formula('2*majors + wins'), {'majors': 2, 'wins': 3, 'peak': None}), 7.0)
        self.assertEqual(G.evaluate(G.compile_formula('peak + 1'), {'peak': None}), 1.0)   # missing counts as 0

    def test_weights(self):
        wt = G.weights({'w_majors': ['abc'], 'w_wins': ['2.5'], 'w_peak': ['inf'], 'w_slam': ['nan']})
        self.assertEqual(wt['majors'], G.COMPONENTS['majors'][4])
        self.assertEqual(wt['wins'], 2.5)
        self.assertEqual(wt['peak'], G.COMPONENTS['peak'][4])
        self.assertEqual(wt['slam'], G.COMPONENTS['slam'][4])


class Lab(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        s = Session.create(cls.tmp / 'w', seed=53, workers=1, world=generate_world(seed=53, scale=0.03))
        s.advance(2 * 52 + 5)
        s.close()
        cls.w = O.World(cls.tmp / 'w', workers=1)
        cls.w.reload()
        if cls.w.statistics()[0] is None:
            cls.w._builder.wait(300)

    @classmethod
    def tearDownClass(cls):
        cls.w.close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def page(self, path):
        u = urlparse(path)
        return O.render(self.w, u.path, parse_qs(u.query))[1]

    def ids(self, html):
        return [int(x) for x in re.findall(r'<td class="n">\d+</td><td><a href="/golfer/(\d+)"', html)]

    def test_ranking_is_deterministic_and_matches_the_components(self):
        vals, _ = G.careers(self.w, SC.MAJORS_PREMIER)
        wt = G.weights({})
        want = sorted(vals, key=lambda p: (-round(sum(wt[k] * (vals[p][k] or 0) for k in G.COMPONENTS), 6),
                                           -vals[p]['majors'], -vals[p]['wins'], p))
        html = self.page('/goat')
        self.assertEqual(self.ids(html), want[:O.PAGE_SIZE])
        self.assertEqual(html, self.page('/goat'))
        self.assertIn('ties broken by majors, then wins, then id', html)

    def test_components_reuse_the_existing_figures(self):
        vals, _ = G.careers(self.w, '')
        db = self.w.statistics()[0]
        st = ST.query(db, list(self.w.a.years), None, self.w.live_statistics(), cols=('starts', 'wins', 'runner_ups', 'top10'))
        majors = {}
        for m in OH.major_wins(self.w):
            majors[m[4]] = majors.get(m[4], 0) + 1
        no1 = {r['person']: r['value'] for r in board(self.w.stats, 'weeks-at-number-one', n=10 ** 6)[1]}
        for pid, v in list(vals.items())[:300]:
            self.assertEqual(v['wins'], st[pid]['wins'])                # the Stats directory (current season included)
            self.assertEqual(v['starts'], st[pid]['starts'])
            self.assertEqual(v['majors'], majors.get(pid, 0))          # the Grand Slam page's majors
            self.assertEqual(v['weeks_no1'], no1.get(pid, 0))          # the Records page's list
        mp, _ = G.careers(self.w, SC.MAJORS_PREMIER)
        self.assertTrue(any(mp[p]['wins'] < vals[p]['wins'] for p in mp if p in vals))   # the scope matters

    def test_formula_and_invalid_formula(self):
        html = self.page('/goat?' + urlencode({'formula': 'wins'}))
        vals, _ = G.careers(self.w, SC.MAJORS_PREMIER)
        top = self.ids(html)[0]
        self.assertEqual(vals[top]['wins'], max(v['wins'] for v in vals.values()))
        marker = self.tmp / 'ran'
        bad = self.page('/goat?' + urlencode({'formula': f'__import__("pathlib").Path("{marker}").touch()'}))
        self.assertIn('Formula not used', bad)
        self.assertFalse(marker.exists())                              # never evaluated
        self.assertEqual(self.ids(bad), self.ids(self.page('/goat')))  # the weighted sum instead
        none = self.page('/goat?' + urlencode({'formula': 'wins / (majors - majors)'}))
        self.assertIn('could not be worked out', none)

    def test_coverage_and_missing_figures(self):
        html = self.page('/goat?' + urlencode({'w_prize_m': 1, 'w_peak': 1, 'status': ''}))
        self.assertIn('<h2>Components</h2>', html)
        for k, c in G.COMPONENTS.items():
            self.assertIn(f'<code>{k}</code>', html)
        vals, missing = G.careers(self.w, SC.MAJORS_PREMIER)
        partial = [p for p in self.ids(html) if (self.w.a.people.get(p) or {}).get('initial')]
        for p in partial[:5]:
            row = re.search(rf'<a href="/golfer/{p}">.*?</tr>', html, re.S).group(0)
            self.assertIn('partial', row)
        gaps = [p for p in self.ids(html) if missing.get(p)]
        for p in gaps[:5]:
            row = re.search(rf'<a href="/golfer/{p}">.*?</tr>', html, re.S).group(0)
            self.assertIn('missing:', row)

    def test_majors_and_slams_count_the_same_history_whatever_old_settings_say(self):
        vals, _ = G.careers(self.w, SC.MAJORS_PREMIER)
        plant_old_hiding(self.tmp / 'w')
        self.addCleanup((self.tmp / 'w' / 'observer_spoilers.json').unlink)
        again, _ = G.careers(self.w, SC.MAJORS_PREMIER)
        self.assertEqual(again, vals)
        idx = self.w.a.index                                            # every major in the history and this season
        n = idx.db.execute("SELECT COUNT(*) FROM editions WHERE category = 'major' AND winner IS NOT NULL").fetchone()[0]
        n += sum(1 for e in self.w.live.editions.values() if e.get('category') == 'major')
        self.assertEqual(sum(v['majors'] for v in vals.values()), n)
        self.assertGreater(n, 0)


if __name__ == '__main__':
    unittest.main()
