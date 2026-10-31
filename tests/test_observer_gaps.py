"""Observer gaps from the requirement review: Prestige sorts both ways on every directory (missing values last
either way); a golfer's Prestige shown with its two parts (the last 52 weeks' fame and the fading legacy) where they
are recorded, and "not recorded" otherwise; My World's "first shared major" and "retirement into a staff role"
items, each recorded fact once; and each round's conditions on an edition's pages, from the recorded data (current
season and archived), "not recorded" when absent.

The Unit classes need no world (run them any time); WorldGaps builds a small world (scale 0.03).

Run from the project folder:  python -m unittest tests.test_observer_gaps -v
"""
from __future__ import annotations

import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
import observer as O                                                  # noqa: E402


def text(h):
    return re.sub(r'<[^>]+>', '', h)


def column(html, i):
    """The cells of column i of the page's first table body, as text ('' for an empty cell)."""
    body = html.split('<tbody>', 1)[1].split('</tbody>', 1)[0]
    rows = re.findall(r'<tr>(.*?)</tr>', body, re.S)
    return [text(re.findall(r'<td[^>]*>(.*?)</td>', r, re.S)[i]).strip() for r in rows]


def num(v):
    return float(v) if v not in ('', None) else None


class UnitDirectorySort(unittest.TestCase):
    """directory_sort: numbers both ways, missing values last either way, ties by name then id."""

    rows = [(1, {'name': 'Bea'}, None), (2, {'name': 'Al'}, None), (3, {'name': 'Cy'}, None),
            (4, {'name': 'Di'}, None), (5, {'name': 'Ed'}, None)]
    pres = {1: 50.0, 2: None, 3: 70.5, 4: 50.0, 5: 9.0}
    values = {'reputation': lambda r: UnitDirectorySort.pres[r[0]], 'name': lambda r: r[1]['name'],
              'born': lambda r: None}

    def ids(self, sort, d):
        return [r[0] for r in O.directory_sort(self.rows, sort, d, self.values)]

    def test_prestige_descending_first_missing_last(self):
        self.assertEqual(self.ids('reputation', ''), [3, 1, 4, 5, 2])
        self.assertEqual(self.ids('reputation', 'desc'), [3, 1, 4, 5, 2])

    def test_prestige_ascending_missing_still_last(self):
        self.assertEqual(self.ids('reputation', 'asc'), [5, 1, 4, 3, 2])   # ties (Bea, Di) by name both ways

    def test_names_both_ways_and_unknown_sort(self):
        self.assertEqual(self.ids('name', ''), [2, 1, 3, 4, 5])
        self.assertEqual(self.ids('name', 'desc'), [5, 4, 3, 1, 2])
        self.assertEqual(self.ids('nonsense', 'bogus'), [2, 1, 3, 4, 5])   # (an unknown sort: by name)
        self.assertEqual(self.ids('born', 'asc'), [2, 1, 3, 4, 5])         # nothing recorded: name order


class WorldGaps(unittest.TestCase):
    """One small world: two archived seasons and a few weeks of the third."""

    @classmethod
    def setUpClass(cls):
        from golfsim.population import generate_world
        from golfsim.session import Session
        cls.tmp = Path(tempfile.mkdtemp())
        cls.path = cls.tmp / 'w'
        s = Session.create(cls.path, seed=41, workers=1, world=generate_world(seed=41, scale=0.03))
        s.advance(2 * 52 + 6)
        s.close()
        cls.w = O.World(cls.path, workers=1)
        cls.w.reload()

    @classmethod
    def tearDownClass(cls):
        cls.w.close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def page(self, path):
        u = urlparse(path)
        return O.render(self.w, u.path, parse_qs(u.query))[1]

    def whole(self, path, col):
        """Column `col` over every page of a directory (its whole sorted set)."""
        out, n = [], 1
        while True:
            html = self.page(f'{path}&page={n}')
            out += column(html, col)
            m = re.search(r'page (\d+) of (\d+)', html)
            if not m or int(m.group(1)) >= int(m.group(2)):
                return out
            n += 1

    # ---- 1. Prestige sorts both ways -------------------------------------------------------------------------
    def check_both_ways(self, path, col):
        down = [num(v) for v in self.whole(f'{path}?sort=reputation', col)]
        up = [num(v) for v in self.whole(f'{path}?sort=reputation&dir=asc', col)]
        known_down = [v for v in down if v is not None]
        known_up = [v for v in up if v is not None]
        self.assertTrue(known_down, path)
        self.assertEqual(known_down, sorted(known_down, reverse=True))
        self.assertEqual(known_up, sorted(known_up))
        self.assertEqual(sorted(known_up), sorted(known_down))          # the same people, the other way round
        for vals in (down, up):                                         # missing values last, in either direction
            first_missing = next((i for i, v in enumerate(vals) if v is None), len(vals))
            self.assertTrue(all(v is None for v in vals[first_missing:]), path)
        self.assertEqual(self.whole(f'{path}?sort=reputation&dir=desc', col),
                         self.whole(f'{path}?sort=reputation', col))   # (descending is the usual first direction)

    def test_golfers_prestige_both_ways(self):
        self.check_both_ways('/golfers', 6)
        html = self.page('/golfers?sort=reputation&dir=asc')
        self.assertIn('<option value="asc" selected>', html)
        self.assertIn('listed last either way', html)

    def test_coaches_and_caddies_prestige_both_ways(self):
        self.check_both_ways('/coaches', 4)
        self.check_both_ways('/caddies', 4)


if __name__ == '__main__':
    unittest.main()
