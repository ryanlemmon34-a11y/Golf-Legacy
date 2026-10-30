"""Player-facing views of the living world: a golfer's ratings over time (fixed-width bars per season, levels or
changes, unknown seasons as gaps, a retired golfer's final playing ratings dated to the season they retired
after, never a later season); injuries as recorded (announced weeks, entries actually missed, when the golfer
could enter again, their first start back, lasting effects; older seasons say "episodes not recorded").

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
            starts = {(x['year'], x['week']) for x in self.w.results(g)}
            for e in r['injuries']:
                self.assertEqual(e['out'], e['announced'] + 1)
                k = e['week'] + e['announced'] + 1
                self.assertEqual(tuple(e['available']), (y + k // 52, k % 52 + 1))
                first = (y, e['week'] + 1)
                blocked = [s for s in starts if first <= s < tuple(e['available'])]
                self.assertEqual(blocked, [], (g, y, e))              # no start while they were out

    def test_the_profile_shows_them(self):
        g, y, r = self.injured_golfers()[0]
        html = O.render(self.w, f'/golfer/{g}', {})[1]
        part = html.split('<h2>Injuries</h2>')[1].split('</p>')[-2] if '<h2>Injuries</h2>' in html else ''
        self.assertIn('<h2>Injuries</h2>', html)
        e = r['injuries'][0]
        self.assertIn(f'{y} week {e["week"]}', html)
        self.assertIn(f'{e["available"][0]} week {e["available"][1]}', html)
        self.assertTrue(part)

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


if __name__ == '__main__':
    unittest.main()
