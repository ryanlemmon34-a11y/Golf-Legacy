"""The shared Majors + Premier scope (roadmap v14): one definition on every page that counts events -- every
major and every Premier circuit's events, by each edition's classification when played, each edition once;
a Challenger member's major and Premier starts count, a Premier member's regional starts do not; it replaces
only the tour choice (season, view, sort and other filters are kept) and All tours resets it.

Run from the project folder:  python -m unittest tests.test_scopes -v
"""
from __future__ import annotations

import re
import shutil
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
from golfsim import scopes as SC                                         # noqa: E402
from golfsim.population import generate_world                            # noqa: E402
from golfsim.session import Session                                      # noqa: E402
import observer as O                                                     # noqa: E402
import observer_data as OD                                               # noqa: E402
import observer_stats as ST                                              # noqa: E402

MP = SC.MAJORS_PREMIER


class Scopes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        s = Session.create(cls.tmp / 'w', seed=47, workers=1, world=generate_world(seed=47, scale=0.03))
        s.advance(52 + 12)
        s.close()
        cls.w = O.World(cls.tmp / 'w', workers=1)
        cls.w.reload()
        db, b = cls.w.statistics()
        if db is None:
            cls.w._builder.wait(300)
        cls.db = cls.w.statistics()[0]

    @classmethod
    def tearDownClass(cls):
        cls.w.close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def page(self, path):
        u = urlparse(path)
        return O.render(self.w, u.path, parse_qs(u.query))[1]

    def test_the_scope_is_the_majors_and_every_premier_circuit(self):
        self.assertEqual(SC.majors_premier_tours(), ('MAJORS', 'PT_AMERICAS', 'PT_ASIA_PACIFIC', 'PT_EUROPE'))
        self.assertTrue(SC.in_majors_premier(tier=0, kind='major') and SC.in_majors_premier(tier=1))
        self.assertFalse(SC.in_majors_premier(tier=2) or SC.in_majors_premier(tier=7))

    def test_stats_equal_the_union_of_its_tours_each_edition_once(self):
        years = list(self.w.a.years)
        union = ST.query(self.db, years, MP, cols=ST.COLUMNS + ('golf_starts', 'rounds', 'strokes'))
        parts = Counter()
        for t in SC.majors_premier_tours():
            for pid, r in ST.query(self.db, years, t, cols=ST.COLUMNS).items():
                parts[(pid, 'starts')] += r['starts']
                parts[(pid, 'wins')] += r['wins']
        for pid, r in union.items():
            self.assertEqual(r['starts'], parts[(pid, 'starts')], pid)
            self.assertEqual(r['wins'], parts[(pid, 'wins')], pid)

    def test_membership_does_not_decide_the_scope(self):
        rows_by = {}
        for pid in list(self.w.a.people):
            rows = [r for r in OD.results(self.w, pid) if not OD.is_qualifying(r)]
            if rows:
                rows_by[pid] = rows
        # a non-Premier member with a major or Premier start (event-time tour), and a Premier member's other starts
        outsider = next((pid for pid, rows in rows_by.items()
                         if not (self.w.person(pid)['golfer'].get('tour') or '').startswith('PT_')
                         and any((r['tour'] or '') in SC.majors_premier_tours() for r in rows)), None)
        member = next((pid for pid, rows in rows_by.items()
                       if (self.w.person(pid)['golfer'].get('tour') or '').startswith('PT_')
                       and any((r['tour'] or '') not in SC.majors_premier_tours() for r in rows)), None)
        for pid in [p for p in (outsider, member) if p]:
            want = sum(1 for r in rows_by[pid] if (r['tour'] or '') in SC.majors_premier_tours())
            listed = self.page(f'/golfer/{pid}?tab=results&tour={MP}')
            self.assertIn(f'{want} of ', listed)                            # the list and the count agree
            prof = self.page(f'/golfer/{pid}?tab=playing&scope={MP}')
            m = re.search(r'<strong>Career</strong>.*?<td class=n><a [^>]*>(\d+)</a>', prof, re.S)
            self.assertIsNotNone(m)
            self.assertEqual(int(m.group(1)), want, pid)
        self.assertTrue(outsider or member)

    def test_buttons_keep_the_other_filters_and_reset(self):
        y = str(self.w.a.years[-1])
        body = self.page(f'/stats?year={y}&sort=wins&tour={MP}')
        self.assertIn('aria-pressed="true">Majors + Premier', body)
        reset = re.search(r'href="([^"]*)"[^>]*aria-pressed="false">All tours', body).group(1).replace('&amp;', '&')
        self.assertIn(f'year={y}', reset)
        self.assertIn('sort=wins', reset)
        self.assertNotIn('tour=', reset)
        golf = self.page(f'/stats?show=golf&year={y}&min=0')
        on = re.search(r'href="([^"]*)"[^>]*aria-pressed="false">Majors \+ Premier', golf).group(1).replace('&amp;', '&')
        for part in ('show=golf', f'year={y}', 'min=0', 'tour=majors'):
            self.assertIn(part, on)
        self.assertIn('Majors + Premier', self.page(f'/golf-records/longest-drive?tour={MP}'))
        rec = self.page(f'/records/most-wins?scope={MP}')
        self.assertIn('Majors + Premier', rec)
        from golfsim.history_stats import board
        self.assertEqual(board(self.w.stats, 'most-wins', n=100, scope='premier'),
                         board(self.w.stats, 'most-wins', n=100, scope='premier'))


if __name__ == '__main__':
    unittest.main()
