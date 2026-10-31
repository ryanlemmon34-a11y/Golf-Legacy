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
from types import SimpleNamespace as NS                               # noqa: E402
from golfsim import prestige as PR                                    # noqa: E402
import observer as O                                                  # noqa: E402
import observer_history as OH                                         # noqa: E402


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


class UnitPrestigeParts(unittest.TestCase):
    """The two parts of a golfer's Prestige: shown from the running world's figures, "not recorded" without them."""

    def test_parts_from_the_running_world(self):
        fame, legacy = 123.456, 38.8
        w = NS(live=NS(people={7: {'prestige': round(PR.player_prestige(fame, legacy), 1),
                                   'prestige_parts': (fame, legacy)}}))
        self.assertEqual(OH.prestige_parts(w, 7), (fame, legacy))
        h = OH.prestige_parts_html(w, 7)
        self.assertIn(f"results {fame:.1f} fame points (alone, Prestige {PR.player_prestige(fame, 0):.1f})", h)
        self.assertIn(f"legacy {legacy:.1f} points (alone, Prestige {PR.player_prestige(0, legacy):.1f})", h)
        self.assertIn('40 points for a major', h)
        self.assertNotIn('not recorded', h)

    def test_not_recorded_without_them(self):
        for w in (NS(live=None), NS(live=NS(people={})), NS(live=NS(people={7: {'prestige': 50.0}}))):
            self.assertIsNone(OH.prestige_parts(w, 7))
            self.assertIn('not recorded', OH.prestige_parts_html(w, 7))


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

    # ---- 2. Prestige with its parts ---------------------------------------------------------------------------
    def test_prestige_parts_on_the_profile(self):
        season = self.w.session.season
        lv = self.w.live
        shown = 0
        for g in sorted(p for p, x in lv.people.items() if x.get('prestige') is not None)[:40]:
            fame, legacy = lv.people[g]['prestige_parts']
            self.assertEqual((fame, legacy), (season.fame.get(g, 0.0), season.legacy.get(g, 0.0)))   # the engine's
            self.assertEqual(round(PR.player_prestige(fame, legacy), 1), lv.people[g]['prestige'])    # exactly
            html = self.page(f'/golfer/{g}')
            row = html.split('<dt>Prestige</dt><dd>', 1)[1].split('</dd>', 1)[0]
            self.assertTrue(row.startswith(f'{lv.people[g]["prestige"]} '))
            self.assertIn(f'results {fame:.1f} fame points', row)
            self.assertIn(f'legacy {legacy:.1f} points', row)
            shown += 1
        self.assertTrue(shown)
        self.assertTrue(any(season.legacy.get(g, 0) > 0 for g in lv.people))   # (some golfer has a legacy)

    def test_prestige_parts_not_recorded_in_the_history_alone(self):
        arch = O.World(self.path / 'archive', workers=1)                # the published history, no running world
        try:
            g = next(p for p, x in arch.a.people.items() if ((x.get('golfer') or {}).get('prestige')) is not None)
            row = O.render(arch, f'/golfer/{g}', {})[1].split('<dt>Prestige</dt><dd>', 1)[1].split('</dd>', 1)[0]
            self.assertIn('as the published history ends', row)
            self.assertIn('not recorded', row)
            self.assertNotIn('fame points', row)
        finally:
            arch.close()


if __name__ == '__main__':
    unittest.main()
