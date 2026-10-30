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
import observer_data as OD                                            # noqa: E402


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
            live_prize = self.w.live.prize.get(pid, 0.0) if self.w.live.results(pid) else 0.0
            self.assertEqual(f['prize'], sum(r['prize'] or 0 for r in got) + live_prize)   # this season's so far too
            pk = OD.recorded_peak(self.w, pid)                           # the profile's Recorded Peak
            self.assertEqual(f['peak'], (pk['value'], pk['year'], pk['week']) if pk else None)
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

    def test_an_older_index_shows_the_profiles_peak(self):
        e = self.field()
        pids = [r['person'] for r in e['rows']]
        a = self.w.a
        a.__dict__.pop('_peak_memo', None)
        self.addCleanup(a.__dict__.pop, '_peak_memo', None)
        with mock.patch.object(a.index, 'derived_complete', lambda years: False), mock.patch.object(self.w, 'live', None):
            peaks = OC.follow(self.w, pids, e['year'])
            for pid in pids:                                            # an index from before the full rows: the
                pk = OD.recorded_peak(self.w, pid)                      # profile records no peak, and neither does
                self.assertIsNone(pk)                                   # the cohort (never another season's value)
                self.assertIsNone(peaks[pid]['peak'])

    def test_this_seasons_prize_money_counts(self):
        lv = self.w.live
        paid = [e for e in lv.editions.values() if e['finish'] and e.get('category') not in ('qualifier', 'q_school')
                and any(p == 1 and lv.prize.get(g) for g, p, _ in e['finish'][0])]
        self.assertTrue(paid)
        e = paid[0]                                                     # a field from this season: no archived season
        win = next(g for g, p, _ in e['finish'][0] if p == 1)
        url = f'/cohort?event={quote(e["id"])}'
        fol = OC.follow(self.w, [g for site in e['finish'] for g, _, _ in site], lv.cursor['year'])
        self.assertGreater(fol[win]['prize'], 0)                        # a first-season paid winner
        self.assertEqual(fol[win]['prize'], lv.prize[win])
        self.assertGreaterEqual(fol[win]['wins'], 1)
        self.assertEqual(fol[win]['seasons'], 1)
        self.assertTrue(fol[win]['prize_known'])
        self.assertIn(f'<td class="n">{O.money(lv.prize[win])}</td>', self.member_row(self.page(url), win))
        ams = sorted(g for g, p in lv.people.items() if p.get('status') == 'amateur' and lv.results(g)
                     and not lv.prize.get(g))[:20]
        self.assertTrue(ams)
        for g, f in OC.follow(self.w, ams, lv.cursor['year']).items():  # an amateur paid nothing: $0, and known
            self.assertEqual(f['prize'], 0)
            self.assertTrue(f['prize_known'])
            self.assertEqual(f['seasons'], 1)
        for g in (win, ams[0]):                                         # the golfer's season page says the same
            season = self.page(f'/golfer/{g}?tab=season&year={lv.cursor["year"]}')
            got = re.search(r'Prize money so far</[^>]+>\s*<[^>]+>(.*?)</', season, re.S).group(1)
            self.assertEqual(got, O.money(lv.prize.get(g, 0.0)))
        old = self.field()                                              # a multi-season career
        fol = OC.follow(self.w, [r['person'] for r in old['rows']], old['year'])
        many = [g for g, f in fol.items() if f['seasons'] >= 3 and lv.results(g)]
        self.assertTrue(many)
        for g in many[:10]:
            rows = [r for r in self.w.a.index.seasons(g) if r['year'] >= old['year']]
            self.assertEqual(fol[g]['prize'], sum(r['prize'] or 0 for r in rows) + lv.prize.get(g, 0.0))
        self.assertEqual(OC.follow(self.w, many, old['year']), {g: fol[g] for g in many})   # (a refresh: the same)

    def test_a_season_that_did_not_record_prize_money_is_not_zero(self):
        old = self.field()
        pids = [r['person'] for r in old['rows']]
        idx = self.w.a.index
        real = idx.db
        url = f'/cohort?event={quote(old["id"])}&sort=name'
        shown = [int(x) for x in self.rows(self.page(url))]
        gap = next(g for g in shown if any(r['events'] and r['prize'] for r in idx.seasons(g)))

        class Older:                                                    # that golfer's seasons without prize money
            def execute(self, sql, *a):
                cur = real.execute(sql, *a)
                if 'FROM seasons WHERE person IN' not in sql:
                    return cur
                return [r[:7] + (None,) + r[8:] if r[0] == gap else r for r in cur]
        with mock.patch.object(idx, 'db', Older()):
            fol = OC.follow(self.w, pids, old['year'])
            html = self.page(url)
        self.assertFalse(fol[gap]['prize_known'])                       # unknown, not silently $0
        self.assertTrue(all(f['prize_known'] for g, f in fol.items() if g != gap))
        self.assertIn('partial: a season did not record it', self.member_row(html, gap))

    def member_row(self, html, pid):
        return re.search(rf'<tr><td><a href="/golfer/{pid}">.*?</tr>', html, re.S).group(0)


class SeasonEnd(unittest.TestCase):
    """Prize money across a season end: the season counted once -- from the live snapshot while it is played, from
    its archived row once it ends -- and the same after a refresh."""

    def test_prize_money_across_the_season_end(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        s = Session.create(tmp / 'w', seed=71, workers=1, world=generate_world(seed=71, scale=0.02))
        s.advance(51)                                                   # to the last week of the first season
        s.close()
        w = O.World(tmp / 'w', workers=1)
        w.reload()
        y = w.live.cursor['year']
        self.assertEqual(w.live.cursor['week'], 52)
        paid = sorted(g for g, v in w.live.prize.items() if v)[:60]
        self.assertTrue(paid)
        before = OC.follow(w, paid, y)
        for g in paid:
            self.assertEqual(before[g]['prize'], w.live.prize[g])
        w.close()
        s = Session.open(tmp / 'w', workers=1)
        s.advance(1)                                                    # week 52: the season ends and is archived
        s.close()
        w = O.World(tmp / 'w', workers=1)
        self.addCleanup(w.close)
        w.reload()
        self.assertEqual(w.live.cursor['year'], y + 1)
        self.assertIn(y, w.a.years)
        after = OC.follow(w, paid, y)
        for g in paid:
            row = next(r for r in w.a.index.seasons(g) if r['year'] == y)
            self.assertEqual(after[g]['prize'], row['prize'] + w.live.prize.get(g, 0.0))   # once, from the archive
            self.assertGreaterEqual(round(after[g]['prize']), round(before[g]['prize']))   # (archived: whole dollars)
            self.assertEqual(after[g]['seasons'], 1)
        w.reload()                                                      # a refresh: the same figures
        self.assertEqual(OC.follow(w, paid, y), after)
        live = w.live                                                   # the snapshot still naming the archived
        with mock.patch.object(live, 'cursor', {'year': y, 'week': 52}), \
                mock.patch.object(live, 'prize', {g: before[g]['prize'] for g in paid}):   # season: not added again
            again = OC.follow(w, paid, y)
        for g in paid:
            row = next(r for r in w.a.index.seasons(g) if r['year'] == y)
            self.assertEqual(again[g]['prize'], row['prize'])


if __name__ == '__main__':
    unittest.main()
