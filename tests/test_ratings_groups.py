"""Ratings group views: Physical, Technical and Mental beside Overall and the single attributes in the profile's
Ratings over time and a season's ratings table. The groups are the simulation's own (golfsim.ratings' Physical and
Mental groups, the same attributes as golfsim.development's physical and mental training categories; Technical is
every other attribute), each value is the plain mean of its attributes' recorded ratings (as the page says), a
season without a recorded attribute shows nothing in its place, and drawing them changes nothing the simulation
keeps.

Run from the project folder:  python -m unittest tests.test_ratings_groups -v
"""
from __future__ import annotations

import hashlib
import html
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
from golfsim import development as D                                  # noqa: E402
from golfsim.population import generate_world                         # noqa: E402
from golfsim.ratings import ATTRIBUTE_GROUPS, ATTRIBUTE_KEYS          # noqa: E402
from golfsim.session import Session                                   # noqa: E402
import equivalence_check as EQ                                        # noqa: E402
import observer as O                                                  # noqa: E402
import observer_data as OD                                            # noqa: E402


def mean(xs):
    return sum(xs) / len(xs)


def bars(page):
    """{season label: (bar label, value shown in the title)} of the Ratings over time chart."""
    out = {}
    for t in re.findall(r'<div class="rbar[^"]*" title="([^"]+)"', page):
        t = html.unescape(t)
        m = re.match(r'(\S+) · (.+?) · (.+?) (-?\d+\.\d)(?: \(|$)', t)
        if m:
            out[m.group(1)] = (m.group(2), m.group(3), float(m.group(4)))
    return out


class RatingsGroups(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.path = cls.tmp / 'w'
        s = Session.create(cls.path, seed=43, workers=1, world=generate_world(seed=43, scale=0.03))
        s.advance(2 * 52 + 4)                                           # two archived seasons, four weeks played
        s.close()
        cls.w = O.World(cls.path, workers=1)
        cls.w.reload()
        y = cls.year = cls.w.a.years[-1]
        first, last = cls.w.a.year(y - 1)['careers'], cls.w.a.year(y)['careers']
        cls.pid = next(int(g) for g, r in sorted(last.items(), key=lambda x: int(x[0]))
                       if r.get('ratings') and (first.get(g) or first.get(int(g)) or {}).get('ratings')
                       and (cls.w.live.people.get(int(g)) or {}).get('ratings'))
        keys = cls.w.a.world['rating_keys']
        cls.earlier = dict(zip(keys, (first.get(cls.pid) or first.get(str(cls.pid)))['ratings']))   # start of y
        cls.archived = dict(zip(keys, last[cls.pid]['ratings']))                                    # start of y + 1

    @classmethod
    def tearDownClass(cls):
        cls.w.close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def page(self, path):
        u = urlparse(path)
        return O.render(self.w, u.path, parse_qs(u.query))[1]

    def test_the_groups_are_the_simulations(self):
        g = {k: set(ks) for k, (_, ks) in OD.RATING_GROUPS.items()}
        self.assertEqual(g['physical'], {k for k in ATTRIBUTE_KEYS if ATTRIBUTE_GROUPS[k] == 'Physical'})
        self.assertEqual(g['mental'], {k for k in ATTRIBUTE_KEYS if ATTRIBUTE_GROUPS[k] == 'Mental'})
        self.assertEqual(g['physical'], set(D.CATEGORIES['physical']))
        self.assertEqual(g['mental'], set(D.CATEGORIES['mental']))
        self.assertEqual(g['technical'], set(ATTRIBUTE_KEYS) - g['physical'] - g['mental'])
        self.assertEqual(g['technical'], set(D.CATEGORIES['long_game']) | set(D.CATEGORIES['short_game'])
                         | set(D.CATEGORIES['putting']))
        self.assertEqual(sum(len(x) for x in g.values()), len(ATTRIBUTE_KEYS))   # every attribute in one group

    def test_values_are_the_mean_of_the_recorded_attributes(self):
        y = self.year
        live = dict(zip(['overall', *ATTRIBUTE_KEYS], self.w.live.people[self.pid]['ratings']))
        for g, (label, ks) in OD.RATING_GROUPS.items():
            got = bars(self.page(f'/golfer/{self.pid}?rh={g}'))
            want = mean([self.earlier[k] for k in ks])                 # from the season file's recorded ratings
            self.assertEqual(OD.with_groups(self.earlier)[g], want)
            self.assertEqual(got[str(y)], (f'start of {y}', label, round(want, 1)))
            # (the current season's slot: the current ratings, the start of the season named)
            label_y, name, shown = got[str(y + 1)]
            self.assertEqual(name, label)
            self.assertEqual(shown, round(mean([live[k] for k in ks]), 1))
            self.assertIn(f'started the season at {self.archived["overall"]:.1f}', label_y)
        # an archived season's ratings table: its start and its end (the next season's start), from the season files
        page = self.page(f'/golfer/{self.pid}?tab=season&year={y}')
        for g, (label, ks) in OD.RATING_GROUPS.items():
            row = re.search(rf'<td>{label} \(group mean\)</td><td[^>]*>([\d.]+)</td><td[^>]*>([\d.]+)</td>', page)
            self.assertIsNotNone(row, label)
            self.assertEqual(float(row.group(1)), round(mean([self.earlier[k] for k in ks]), 1))
            self.assertEqual(float(row.group(2)), round(mean([self.archived[k] for k in ks]), 1))
        # the current season's table: its start and now
        page = self.page(f'/golfer/{self.pid}?tab=season&year={y + 1}')
        for g, (label, ks) in OD.RATING_GROUPS.items():
            row = re.search(rf'<td>{label} \(group mean\)</td><td[^>]*>([\d.]+)</td><td[^>]*>([\d.]+)</td>', page)
            self.assertEqual(float(row.group(1)), round(mean([self.archived[k] for k in ks]), 1))
            self.assertEqual(float(row.group(2)), round(mean([live[k] for k in ks]), 1))

    def test_the_page_says_how(self):
        page = self.page(f'/golfer/{self.pid}?rh=technical')
        self.assertIn('<option value="technical" selected>Technical</option>', page)
        self.assertIn('plain mean of their attributes', html.unescape(page))
        self.assertIn('Overall is not their mean', html.unescape(page))
        for g in ('physical', 'mental', 'overall', 'power'):
            self.assertIn(f'<option value="{g}"', page)
        self.assertIn('plain mean of their attributes', html.unescape(self.page(f'/golfer/{self.pid}?tab=season&year={self.year + 1}')))

    def test_change_mode_and_unknown_choices(self):
        page = self.page(f'/golfer/{self.pid}?rh=mental&rm=change')
        self.assertIn('rchart chg', page)
        self.assertIn('<option value="mental" selected>Mental</option>', page)
        page = self.page(f'/golfer/{self.pid}?rh=nonsense')
        self.assertIn('<option value="overall" selected>Overall</option>', page)

    def test_an_unrecorded_attribute_leaves_its_group_unrecorded(self):
        d = dict(self.archived)
        del d['focus']
        got = OD.with_groups(d)
        self.assertIsNone(got['mental'])
        self.assertIsNotNone(got['physical'])
        self.assertIsNone(OD.with_groups(None))

    def test_drawing_changes_nothing(self):
        def state():
            files = {p.relative_to(self.path).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in sorted(self.path.rglob('*')) if p.is_file() and not p.name.startswith('observer')}
            return EQ.parts(self.w.session, self.path), files
        before = state()
        for g in ('overall', *OD.RATING_GROUPS, 'power'):
            for m in ('level', 'change'):
                self.page(f'/golfer/{self.pid}?rh={g}&rm={m}')
        self.page(f'/golfer/{self.pid}?tab=season&year={self.year}')
        self.page(f'/golfer/{self.pid}?tab=season&year={self.year + 1}')
        self.assertEqual(state(), before)


if __name__ == '__main__':
    unittest.main()
