"""Player-facing views of the living world: a golfer's ratings over time (fixed-width bars per season, levels or
changes, unknown seasons as gaps, a retired golfer's final playing ratings dated to the season they retired
after, never a later season); injuries as recorded (announced weeks, entries actually missed, when the golfer
could enter again, their first start back, lasting effects; older seasons say "episodes not recorded"); coach and
caddie profiles (speciality, youth focus, capacity, a caddie's recorded skills; hidden teaching and scouting not
shown) and every partnership's beginning, arrangement, work together and end as recorded.

Run from the project folder:  python -m unittest tests.test_living_views -v
"""
from __future__ import annotations

import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from urllib.parse import parse_qs

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
from golfsim.population import generate_world                         # noqa: E402
from golfsim.session import Session                                   # noqa: E402
import observer as O                                                  # noqa: E402
import observer_data as OD                                            # noqa: E402


class RatingsOverTime(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        s = Session.create(cls.tmp / 'w', seed=99, workers=1, world=generate_world(seed=99, scale=0.03))
        s.advance(3 * 52 + 5)                                           # three archived seasons, five weeks
        s.close()
        cls.w = O.World(cls.tmp / 'w', workers=1)
        cls.w.reload()
        lv, a = cls.w.live, cls.w.a
        cls.y = lv.cursor['year']
        cls.active = min(g for g, p in lv.people.items() if p.get('lifestyle') == 'full_time'
                         and len(OD.rating_snapshots(cls.w, g)) >= 3)
        rows = lambda g: [r for r in a.index.seasons(g)]
        cls.retired = min(g for g, p in lv.people.items() if p.get('lifestyle') == 'retired'
                          and len(OD.rating_snapshots(cls.w, g)) >= 2 and rows(g) and rows(g)[-1]['year'] < cls.y - 1)

    @classmethod
    def tearDownClass(cls):
        cls.w.close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def person(self, g):
        return self.w.person(g)

    def test_an_active_golfer_one_bar_a_season_then_now(self):
        series = O.ratings_series(self.w, self.active, self.person(self.active))
        snaps = OD.rating_snapshots(self.w, self.active)
        years = [int(y) for y, _, _ in series]
        self.assertEqual(years, list(range(min(snaps), self.y + 1)))
        for y, label, v in series:
            if int(y) in snaps and int(y) != self.y:
                self.assertEqual(label, f'start of {y}')
                self.assertEqual(v['overall'], snaps[int(y)][0])
        self.assertTrue(series[-1][1].startswith(f'now ({self.y}, week'))
        self.assertEqual(series[-1][2]['overall'], self.w.live.people[self.active]['ratings'][0])

    def test_a_retired_golfer_ends_at_the_season_they_retired_after(self):
        series = O.ratings_series(self.w, self.retired, self.person(self.retired))
        last_row = self.w.a.index.seasons(self.retired)[-1]['year']
        y, label, v = series[-1]
        self.assertEqual((y, label), (f'{last_row} end', f'final ratings: retired after the {last_row} season'))
        self.assertEqual(v['overall'], OD.rating_snapshots(self.w, self.retired)[last_row + 1][0])   # no aging added
        self.assertFalse(any(y == str(last_row + 1) for y, _, _ in series))   # never a season they did not start
        self.assertFalse(any(label.startswith('now') for _, label, _ in series))

    def test_an_unrecorded_season_is_a_gap(self):
        snaps = OD.rating_snapshots(self.w, self.active)
        hole = sorted(snaps)[1]
        with mock.patch.object(OD, 'rating_snapshots', lambda w, pid: {k: v for k, v in snaps.items() if k != hole}):
            series = O.ratings_series(self.w, self.active, self.person(self.active))
            html = O.render(self.w, f'/golfer/{self.active}', {})[1]
        self.assertIn((str(hole), 'not recorded', None), series)
        self.assertIn(f'title="{hole}: not recorded"', html)

    def test_the_chart_levels_and_changes(self):
        html = O.render(self.w, f'/golfer/{self.active}', {})[1]
        chart = html.split('<h3>Ratings over time</h3>')[1].split('</p>')[0]
        self.assertIn('<div class="scroll"><div class="rchart ">', chart)
        self.assertEqual(len(re.findall(r'class="rbar', chart)), len(O.ratings_series(self.w, self.active,
                                                                                      self.person(self.active))))
        chg = O.render(self.w, f'/golfer/{self.active}', parse_qs('rh=power&rm=change'))[1]
        part = chg.split('<h3>Ratings over time</h3>')[1].split('</p>')[0]
        self.assertIn('rchart chg', part)
        self.assertIn('<option value="power" selected>', part)
        self.assertRegex(part, r'class="rv">[+-]\d+\.\d<')                # signed changes
        self.assertIn('no earlier season to compare', part)              # (the first bar has nothing before it)


    def test_an_exported_history_without_an_index_reads_each_career_once(self):
        dst = self.tmp / 'exported'                                      # (exports leave the index out)
        shutil.copytree(self.tmp / 'w' / 'archive', dst, ignore=shutil.ignore_patterns('index.sqlite*'))
        w = O.World(dst, workers=1, read_only=True)
        try:
            self.assertIsNone(w.a.index)
            g = self.active
            self.assertEqual(OD.career_rows(w, g), OD.career_rows(self.w, g))   # the index's rows exactly
            self.assertEqual(OD.rating_snapshots(w, g), OD.rating_snapshots(self.w, g))
            calls = []
            real = type(w.a).playing_career
            w.a.__dict__.pop('_careers', None)
            with mock.patch.object(type(w.a), 'playing_career', lambda a, pid: calls.append(pid) or real(a, pid)):
                html = O.render(w, f'/golfer/{g}', {})[1]
                O.render(w, f'/golfer/{g}', parse_qs('rh=power&rm=change'))
            self.assertEqual(calls, [g])                                 # once, however many sections read it
            self.assertIn('<h3>Ratings over time</h3>', html)
        finally:
            w.close()


    # ---- injuries -------------------------------------------------------------------------------------------
    def injured_golfers(self):
        import observer_data as OD
        out = []
        for g in sorted(self.w.live.people):
            for y, r in OD.career_rows(self.w, g):
                if r.get('injuries'):
                    out.append((g, y, r))
        return out

    def test_each_episode_adds_up_and_keeps_the_golfer_out(self):
        hurt = self.injured_golfers()
        self.assertTrue(hurt)
        for g, y, r in hurt[:60]:
            self.assertEqual(sum(e['announced'] for e in r['injuries']), r['injury_weeks'], (g, y))
            starts = {(x['year'], x['week']) for x in OD.results(self.w, g)}   # (qualifying stages included)
            for e in r['injuries']:
                self.assertEqual(e['out'], e['announced'])                # n weeks announced, n weeks out
                k = e['week'] + e['announced']
                self.assertEqual(tuple(e['available']), (y + k // 52, k % 52 + 1))   # week W + n + 1
                first = (y, e['week'] + 1)
                blocked = [s for s in starts if first <= s < tuple(e['available'])]
                self.assertEqual(blocked, [], (g, y, e))              # no appearance while they were out

    def test_the_profile_shows_them(self):
        g, y, r = self.injured_golfers()[0]
        html = O.render(self.w, f'/golfer/{g}', {})[1]
        part = html.split('<h2>Injuries</h2>')[1].split('</p>')[-2] if '<h2>Injuries</h2>' in html else ''
        self.assertIn('<h2>Injuries</h2>', html)
        e = r['injuries'][0]
        self.assertIn(f'{y} week {e["week"]}', html)
        self.assertIn(f'{e["available"][0]} week {e["available"][1]}', html)
        self.assertTrue(part)

    def test_the_return_counts_a_qualifying_stage(self):
        g, y, r = self.injured_golfers()[0]
        e = r['injuries'][0]
        back = tuple(e['available'])
        nxt = (back[0], back[1] + 1) if back[1] < 52 else (back[0] + 1, 1)
        qual = {'year': back[0], 'week': back[1], 'event': f'{back[0]}:SOME_QUALIFIER', 'tier': 7}
        main = {'year': nxt[0], 'week': nxt[1], 'event': f'{nxt[0]}:SOME_EVENT', 'tier': 3}
        with mock.patch.object(self.w.live, 'injuries', {}):
            html = O.injuries_section(self.w, g, [qual, main])
            same = O.injuries_section(self.w, g, [main])
        row = re.search(rf'<td>{y} week {e["week"]}</td>.*?</tr>', html, re.S).group(0)
        cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.S)
        self.assertIn('SOME_QUALIFIER', cells[5])                         # first appearance back: the qualifier
        self.assertIn('qualifying', cells[5])
        self.assertIn('SOME_EVENT', cells[6])                             # first main event, labelled apart
        row = re.search(rf'<td>{y} week {e["week"]}</td>.*?</tr>', same, re.S).group(0)
        cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.S)
        self.assertIn('SOME_EVENT', cells[5])
        self.assertEqual(cells[6], 'the same')

    def test_older_seasons_say_episodes_not_recorded(self):
        import observer_data as OD
        g, y, r = self.injured_golfers()[0]
        real = OD.career_rows
        strip = lambda w, pid: [(yy, {k: v for k, v in rr.items() if k != 'injuries'}) for yy, rr in real(w, pid)]
        with mock.patch.object(OD, 'career_rows', strip), mock.patch.object(self.w.live, 'injuries', {}):
            html = O.render(self.w, f'/golfer/{g}', {})[1]
        self.assertIn('episodes not recorded', html)
        self.assertIn(f'{r["injury_weeks"]} (season total)', html)

    def test_injured_now(self):
        lv = self.w.live
        if not lv.injured_now:
            self.skipTest('nobody injured in this week of the test world')
        g = lv.injured_now[0]
        self.assertIn('<span class="tag">injured now</span>', O.render(self.w, f'/golfer/{g}', {})[1])


    # ---- coaches and caddies --------------------------------------------------------------------------------
    def test_a_coach_profile(self):
        a = self.w.a
        coach = min(pid for pid, p in a.people.items() if (p.get('coach') or {}).get('speciality')
                    and a.staff_clients(pid, 'coach'))
        info = a.people[coach]['coach']
        html = O.render(self.w, f'/golfer/{coach}', parse_qs('tab=coaching'))[1]
        self.assertIn(f'<dt>Speciality</dt><dd>{info["speciality"].replace("_", " ")}</dd>', html)
        self.assertIn(f'<dt>Takes on</dt><dd>up to {info["clients"]} clients</dd>', html)
        self.assertIn('not shown (hidden in the game', html)
        self.assertFalse({'teaching', 'scouting'} & set(info))             # (never archived either)
        st = a.staff_clients(coach, 'coach')[0]['stint']
        part = html.split('<h2>All partnerships')[1]                       # (not the current-clients table)
        row = re.search(rf'<a href="/golfer/{st.golfer}">[^<]*</a></td>.*?</tr>', part, re.S).group(0)
        self.assertIn(O._began(st), row)
        self.assertIn(f'{st.work:,.0f}', row)
        if st.end:
            self.assertIn(O._ended(st), row)
        team = O.render(self.w, f'/golfer/{st.golfer}', parse_qs('tab=team'))[1]
        self.assertIn(f'/golfer/{coach}"', team)                          # the golfer's side names them too

    def test_staff_seasons_count_a_partnership_only_while_it_ran(self):
        from golfsim.history import Stint
        lo, hi = self.w.a.years[0], self.w.a.years[-1]
        st = lambda i, g, start, end: Stint(i, 'coach', 999999, g, start, 'fee', 'golfer', end=end)
        self.assertEqual(list(st(0, 1, (lo, 5), (lo + 1, 1)).years(lo, hi)), [lo])          # ended in week 1
        self.assertEqual(list(st(0, 1, (lo, 5), (lo + 1, 2)).years(lo, hi)), [lo, lo + 1])  # ended in week 2
        self.assertEqual(list(st(0, 1, (lo - 3, 5), None).years(lo, hi)), list(range(lo, hi + 1)))  # bounded
        self.assertEqual(list(st(0, 1, (hi + 1, 1), None).years(lo, hi)), [])                # after the archive
        stints = [{'stint': st(0, 5, (lo, 1), (lo + 1, 1)), 'by_year': {lo: [3, 1]}},       # ends at week 1
                  {'stint': st(1, 6, (lo + 1, 30), (lo + 1, 40)), 'by_year': {lo + 1: [2, 0]}},
                  {'stint': st(2, 5, (lo + 2, 10), None), 'by_year': {lo + 2: [4, 0]}},     # a reunion
                  {'stint': st(3, 7, (hi + 1, 1), None), 'by_year': {}}]                       # beyond the archive
        html = O._staff_seasons(self.w, 999999, 'coach', stints)
        got = {int(m[0]): (int(m[1]), int(m[2]), int(m[3])) for m in
               re.findall(r'<tr><td class=n>(\d+)</td><td class=n>(\d+)</td><td class=n>(\d+)</td><td class=n>(\d+)</td>', html)}
        self.assertEqual(got, {lo: (1, 3, 1), lo + 1: (1, 2, 0), lo + 2: (1, 4, 0)})        # clients, starts, wins
        coach = min(pid for pid, p in self.w.a.people.items() if (p.get('coach') or {}) and self.w.a.staff_clients(pid, 'coach'))
        cl = self.w.a.staff_clients(coach, 'coach')
        html = O._staff_seasons(self.w, coach, 'coach', cl)
        rows = {int(m[0]): int(m[1]) for m in re.findall(r'<tr><td class=n>(\d+)</td><td class=n>(\d+)</td>', html)}
        for y in range(lo, hi + 1):                                       # clients = partnerships in force that season
            want = len({c['stint'].golfer for c in cl if y in c['stint'].years(lo, hi)})
            self.assertEqual(rows.get(y, 0), want, y)
        self.assertTrue(set(rows) <= set(range(lo, hi + 1)))

    def test_partnerships_show_the_recorded_fit(self):
        a = self.w.a
        coach = min(pid for pid, p in a.people.items() if (p.get('coach') or {}) and a.staff_clients(pid, 'coach'))
        st = a.staff_clients(coach, 'coach')[0]['stint']
        pair = a.rel.pairs[('coach', coach, st.golfer)]                   # the value the engine draws and uses
        html = O.render(self.w, f'/golfer/{coach}', parse_qs('tab=coaching'))[1].split('<h2>All partnerships')[1]
        row = re.search(rf'<a href="/golfer/{st.golfer}">[^<]*</a></td>.*?</tr>', html, re.S).group(0)
        self.assertIn(f'<td class=n>{pair.fit:+.2f}</td>', row)
        rap = a.rel.rapport('coach', coach, st.golfer, a.years[-1])
        self.assertIn(f'<td class=n>{100 * rap:.0f}%</td>', row)
        team = O.render(self.w, f'/golfer/{st.golfer}', parse_qs('tab=team'))[1]
        self.assertIn(f'<td class=n>{pair.fit:+.2f}</td>', team)              # the same value from the golfer's side

    def test_a_caddie_profile(self):
        a = self.w.a
        cad = min(pid for pid, p in a.people.items() if (p.get('caddie') or {}).get('skills'))
        sk = a.people[cad]['caddie']['skills']
        self.assertEqual(len(sk), 6)
        html = O.render(self.w, f'/golfer/{cad}', parse_qs('tab=caddying'))[1]
        for k, v in sk.items():
            self.assertIn(f'{k.replace("_", " ")} {v:.1f}', html)
        missing = O._staff_card({'reputation': 50, 'seasons': 3}, 'caddie')
        self.assertIn('not recorded (recorded from rules 2026-11-01)', missing)


if __name__ == '__main__':
    unittest.main()
