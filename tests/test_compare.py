"""Career comparisons: up to four golfers side by side; totals, seasons and same-age rows read from the records;
current, historical-snapshot and Recorded Peak Overall kept apart; missing history shown as unavailable.

Run from the project folder:  python -m unittest tests.test_compare -v
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
from golfsim.population import generate_world                         # noqa: E402
from golfsim.session import Session                                   # noqa: E402
import observer as O                                                  # noqa: E402
import observer_compare as C                                          # noqa: E402
import observer_data as OD                                            # noqa: E402
import observer_history as OH                                         # noqa: E402


def plant_old_hiding(world_dir, since=(0, 0)):
    """The removed Hide results setting as an earlier build wrote it (everything hidden, nothing revealed)."""
    import json
    (Path(world_dir) / 'observer_spoilers.json').write_text(json.dumps(
        {'format': 'golf-legacy-spoilers/1', 'hide': True, 'from': list(since), 'revealed': {}}))


class Compare(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        s = Session.create(cls.tmp / 'w', seed=47, workers=1, world=generate_world(seed=47, scale=0.03))
        s.advance(2 * 52 + 6)
        s.close()
        cls.w = O.World(cls.tmp / 'w', workers=1)
        cls.w.reload()
        lv = cls.w.live
        ranked = sorted(lv.wr, key=lv.wr.get)
        cls.a, cls.b = ranked[0], ranked[1]
        cls.champ = next((m[4] for m in OH.major_wins(cls.w)), cls.a)

    @classmethod
    def tearDownClass(cls):
        cls.w.close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def page(self, path):
        u = urlparse(path)
        return O.render(self.w, u.path, parse_qs(u.query))[1]

    def cells(self, html, label):
        row = re.search(r'<tr><th scope="row">' + re.escape(label) + r'.*?</tr>', html, re.S).group(0)
        return [re.sub(r'<[^>]+>', '', c).strip() for c in re.findall(r'<td>(.*?)</td>', row, re.S)]

    def test_totals_come_from_the_records(self):
        html = self.page(f'/compare?ids={self.a},{self.champ}')
        for i, pid in enumerate((self.a, self.champ)):
            rows = OD.career_rows(self.w, pid)
            live = self.w.live.results(pid)
            self.assertEqual(int(self.cells(html, 'Starts')[i].replace(',', '')),
                             sum(r.get('events') or 0 for _, r in rows) + len(live))
            self.assertEqual(int(self.cells(html, 'Majors')[i]),
                             sum(1 for m in OH.major_wins(self.w) if m[4] == pid))
        self.assertIn('the highest recorded', html)

    def test_three_kinds_of_overall_are_kept_apart(self):
        html = self.page(f'/compare?ids={self.a},{self.b}')
        lp = self.w.live.people[self.a]
        self.assertTrue(self.cells(html, 'Current Overall')[0].startswith(f'{lp["ratings"][0]:.1f} (now:'))
        pk = OD.recorded_peak(self.w, self.a)
        self.assertTrue(self.cells(html, 'Peak Overall')[0].startswith(f'{pk["value"]:.1f}'))
        snaps = OD.rating_snapshots(self.w, self.a)
        season = html.split('<h2>Season by season</h2>')[1].split('</table>')[0]
        for y, r in snaps.items():                                     # the snapshot at the start of each season
            row = re.search(rf'<th scope="row">{y}.*?</tr>', season, re.S).group(0)
            self.assertIn(f'Overall {r[0]:.1f} at the start', row)
        first = min(self.w.a.years)
        if first not in snaps:                                          # the world's first season: none recorded
            row = re.search(rf'<th scope="row">{first}.*?</tr>', season, re.S).group(0)
            self.assertIn('Overall at the start: not recorded', row)
        self.assertIn('not the current rating and not the peak', html)

    def test_same_age_rows(self):
        html = self.page(f'/compare?ids={self.a},{self.b}')
        same = html.split('<h2>At the same age</h2>')[1].split('</table>')[0]
        for pid, col in ((self.a, 0), (self.b, 1)):
            born = self.w.person(pid)['born']
            for y in C.seasons(self.w, pid):
                row = re.search(rf'<tr><th scope="row">{y - born}</th>(.*?)</tr>', same, re.S).group(1)
                cell = re.findall(r'<td>(.*?)</td>', row, re.S)[col]
                self.assertTrue(cell.startswith(f'{y}<br>'), (pid, y, cell[:40]))
        ages = [int(x) for x in re.findall(r'<tr><th scope="row">(\d+)</th>', same)]
        self.assertEqual(ages, sorted(ages))
        self.assertTrue('before the world’s records' in same or 'no season recorded' in same
                        or len({self.w.person(p)['born'] for p in (self.a, self.b)}) == 1)

    def test_every_major_counts_whatever_old_settings_say(self):
        plant_old_hiding(self.tmp / 'w')
        self.addCleanup((self.tmp / 'w' / 'observer_spoilers.json').unlink)
        html = self.page(f'/compare?ids={self.champ}')
        self.assertEqual(int(self.cells(html, 'Majors')[0]), sum(1 for m in OH.major_wins(self.w) if m[4] == self.champ))
        self.assertGreater(int(self.cells(html, 'Majors')[0]), 0)
        self.assertNotIn('hidden', html.lower().replace('type="hidden"', ''))

    def test_choosing_golfers(self):
        name = self.w.live.people[self.b]['name'].split()[-1]
        html = self.page(f'/compare?ids={self.a}&find={name}')
        self.assertIn(f'ids={self.a}%2C{self.b}', html)
        self.assertEqual(C.ids({'ids': ['1,2,3,4,5,2']}), [1, 2, 3, 4])
        self.assertIn('compare</a>', self.page(f'/golfer/{self.a}'))
        self.assertIn('Choose up to four golfers', self.page('/compare'))


if __name__ == '__main__':
    unittest.main()
