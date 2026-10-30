"""Where are they now: a field or cohort followed through the rest of their careers -- every member by id (missed
cuts, the unsuccessful, amateurs, club professionals and the retired included), figures read from the history,
complete results whatever an earlier build's Hide results setting said, and an older history without newer facts shown as not recorded.

Run from the project folder:  python -m unittest tests.test_cohort -v
"""
from __future__ import annotations

import re
import shutil
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from urllib.parse import parse_qs, quote, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
from golfsim.population import generate_world                         # noqa: E402
from golfsim.session import Session                                   # noqa: E402
import observer as O                                                  # noqa: E402
import observer_cohort as OC                                          # noqa: E402


def plant_old_hiding(world_dir, since=(0, 0)):
    """The removed Hide results setting as an earlier build wrote it (everything hidden, nothing revealed)."""
    import json
    (Path(world_dir) / 'observer_spoilers.json').write_text(json.dumps(
        {'format': 'golf-legacy-spoilers/1', 'hide': True, 'from': list(since), 'revealed': {}}))


class Cohorts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        s = Session.create(cls.tmp / 'w', seed=37, workers=1, world=generate_world(seed=37, scale=0.03))
        s.advance(2 * 52 + 4)                                           # two archived seasons and four weeks
        s.close()
        cls.w = O.World(cls.tmp / 'w', workers=1)
        cls.w.reload()

    @classmethod
    def tearDownClass(cls):
        cls.w.close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def page(self, path):
        u = urlparse(path)
        return O.render(self.w, u.path, parse_qs(u.query))[1]

    def rows(self, html):
        return re.findall(r'<tr><td><a href="/golfer/(\d+)">', html.split('<table>')[1].split('</table>')[0])

    def field(self, sid='COLLEGE_NATIONAL_CHAMPIONSHIP'):
        e = next(e for e in self.w.editions_of(sid) if e['year'] == self.w.a.years[0])
        return self.w.edition(e['event'])

    def test_a_field_lists_every_entrant_by_id(self):
        e = self.field()
        url = f'/cohort?event={quote(e["id"])}'
        html = self.page(url)
        ids = {r['person'] for r in e['rows']}
        listed = self.rows(html)
        if len(ids) > O.PAGE_SIZE:
            listed += self.rows(self.page(url + '&page=2'))
        self.assertEqual(sorted(map(int, listed)), sorted(ids))         # one row per person, each by id
        self.assertEqual(len(listed), len(set(listed)))
        missed = [r['person'] for r in e['rows'] if r['pos'] is None]
        if missed:
            self.assertIn('>MC', html.replace('<td>MC', '>MC'))         # missed cuts are part of the field
        self.assertIn(f'{len(ids):,} people', html)
        self.assertIn('where is this field now?', self.page(f'/event/{quote(e["id"])}'))

    def test_figures_come_from_the_history(self):
        e = self.field()
        since = e['year']
        fol = OC.follow(self.w, [r['person'] for r in e['rows']], since)
        idx = self.w.a.index
        for pid, f in list(fol.items())[:40]:
            rows = idx.seasons(pid)
            got = [r for r in rows if r['year'] >= since]
            self.assertEqual(f['seasons'] - (1 if f['last'] == self.w.live.cursor['year'] and
                                             self.w.live.cursor['year'] not in {r['year'] for r in got if r['events']}
                                             else 0),
                             sum(1 for r in got if r['events']))
            self.assertEqual(f['prize'], sum(r['prize'] or 0 for r in got))
            self.assertEqual(f['best_wr'], min((r['wr_end'] for r in got if r['wr_end']), default=None))
            live = self.w.live.people[pid]                               # where they are now: today's snapshot
            kind = f['now']
            if live.get('lifestyle') == 'retired':
                self.assertEqual(kind, 'retired')
            elif live.get('status') == 'amateur':
                self.assertEqual(kind, 'amateur')
            elif live.get('status') == 'club_pro':
                self.assertEqual(kind, 'club')
            else:
                self.assertIn(kind, ('premier', 'tour'))

    def test_every_outcome_is_counted(self):
        html = self.page(f'/cohort?tour=CO_US_D1&year={self.w.a.years[0]}')
        members = {p for p, r in self.w.a.year(self.w.a.years[0])['careers'].items() if r.get('tour') == 'CO_US_D1'}
        self.assertIn(f'{len(members):,} people', html)
        fol = OC.follow(self.w, members, self.w.a.years[0])
        summary = html.split('<strong>Now</strong>: ')[1].split('.')[0]
        for k, label in OC.NOW_KINDS:
            n = sum(1 for f in fol.values() if f['now'] == k)
            if n:
                self.assertIn(f'{label}: {n}', summary)
        self.assertEqual(sum(int(x) for x in re.findall(r': (\d+)', summary)), len(members))   # nobody left out

    def test_turned_pro_and_born_cohorts(self):
        y = self.w.a.years[0]
        tp = {pid for pid, p in self.w.live.people.items() if p.get('turned_pro') == y}
        if tp:
            self.assertIn(f'{len(tp):,} people', self.page(f'/cohort?turned_pro={y}'))
        born = next(p['born'] for p in self.w.live.people.values() if p.get('status') == 'pro')
        n = sum(1 for p in self.w.live.people.values() if p.get('born') == born and p.get('status') is not None)
        self.assertIn(f'{n:,} people', self.page(f'/cohort?born={born}'))

    def test_sorting_both_ways(self):
        e = self.field()
        most = self.page(f'/cohort?event={quote(e["id"])}&sort=prize')
        least = self.page(f'/cohort?event={quote(e["id"])}&sort=prize&dir=asc')
        fol = OC.follow(self.w, [r['person'] for r in e['rows']], e['year'])
        top = max(fol.values(), key=lambda f: f['prize'])['prize']
        first = int(self.rows(most)[0])
        self.assertEqual(fol[first]['prize'], top)
        self.assertEqual(fol[int(self.rows(least)[0])]['prize'], min(f['prize'] for f in fol.values()))

    def test_old_hiding_settings_change_nothing(self):
        e = self.field()
        before = self.page(f'/cohort?event={quote(e["id"])}')
        plant_old_hiding(self.tmp / 'w')
        self.addCleanup((self.tmp / 'w' / 'observer_spoilers.json').unlink)
        html = self.page(f'/cohort?event={quote(e["id"])}')
        self.assertEqual(html, before)
        table = html.split('<table>')[1].split('</table>')[0]
        self.assertIn('<td>1 ·', table)                                 # the winner's finish, shown
        self.assertNotIn('hidden', table)

    def test_an_older_index_shows_peaks_as_not_recorded(self):
        e = self.field()
        idx = self.w.a.index
        real = idx.db

        class Old:
            def execute(self, sql, *a):
                if 'FROM careers' in sql:
                    raise sqlite3.OperationalError('no such table: careers')
                return real.execute(sql, *a)
        with mock.patch.object(idx, 'db', Old()), mock.patch.object(self.w, 'live', None):
            peaks = OC._peaks(self.w, [r['person'] for r in e['rows']])
        last = self.w.a.year(self.w.a.years[-1])['careers']
        for pid in (r['person'] for r in e['rows']):
            self.assertEqual(peaks.get(pid), tuple(last[pid]['peak']) if (last.get(pid) or {}).get('peak') else None)


if __name__ == '__main__':
    unittest.main()
