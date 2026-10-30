"""Golf statistics, world ranking points and the records built on them (roadmap, 29 October 2026 pretest review):

- the engine counts the defined statistics from every simulated shot (first tee shots only, GIR with penalties,
  putts on the green, putts per GIR) and keeping them changes nothing in the simulation;
- each edition's counters reach the archive, survive two season boundaries, reload and a repeated advance
  without being counted twice, and season / career / tour figures are sums of counts over sums of
  opportunities (1/2 + 8/10 = 9/12, never the mean of 50% and 80%);
- the world ranking a profile works out from each start's recorded points is exactly the engine's, at the
  live week and at archived weeks (seeded points included);
- winning margins (regulation; a playoff is zero, tied runners-up all listed) and match-play results;
- seasons played before the counts were kept say "not recorded".

Run from the project folder:  python -m unittest tests.test_golf_stats -v
"""
from __future__ import annotations

import json
import random
import shutil
import sys
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
from golfsim import golfstats as GS                                     # noqa: E402
from golfsim import prestige as PR                                      # noqa: E402
from golfsim.archive import Archive                                     # noqa: E402
from golfsim.course_library import default_library                      # noqa: E402
from golfsim.engine import play_round                                   # noqa: E402
from golfsim.population import generate_world                           # noqa: E402
from golfsim.session import Session                                     # noqa: E402
import observer as O                                                    # noqa: E402
import observer_golf as OG                                              # noqa: E402
import observer_stats as ST                                             # noqa: E402

SCALE = 0.02


def arch_page(w, pid):
    return O.render(w, f'/golfer/{pid}', {})[1]


class CountingTests(unittest.TestCase):
    """The engine's counters, checked against their definitions on many simulated rounds."""

    def test_counters_follow_the_definitions(self):
        lib = default_library()
        course = lib.course(next(v for vs in lib.venues(2027).values() for v in vs))
        golfers = generate_world(seed=4, scale=0.01).golfers[:12]
        rng = random.Random(8)
        long_holes = sum(1 for h in course.holes if h.par >= 4)
        tot = GS.empty()
        penalties = 0
        for g in golfers:
            for _ in range(10):
                st = play_round(g, course, rng)
                c, long = GS.round_counters(st)
                d = GS.as_dict(c)
                self.assertEqual(d['fairway_att'], long_holes)          # one measured tee shot per par 4 / 5
                self.assertLessEqual(d['drives'], d['fairway_att'])     # drivers only, never a re-tee
                self.assertLessEqual(d['fairways'], d['fairway_att'])
                self.assertEqual(d['gir'] + d['scr_att'], 18)           # each hole: a GIR or a scrambling chance
                self.assertLessEqual(d['gir_putts'], d['putts'])      # (a holed approach is a GIR with no putt)
                self.assertEqual(d['strokes'], sum(st.holes))
                self.assertEqual(d['p3_strokes'] + d['p4_strokes'] + d['p5_strokes'], d['strokes'])
                self.assertEqual(sum(d[k] for k in ('eagles', 'birdies', 'pars', 'bogeys', 'doubles', 'worse')), 18)
                if long:
                    self.assertAlmostEqual(long[0] / 10, max(st.drives), places=0)
                    self.assertIn(long[1], [h.number for h in course.holes if h.par >= 4])
                penalties += d['penalties']
                GS.add(tot, c)
        self.assertGreater(penalties, 0)                                # trouble happened, and was counted once
        self.assertEqual(tot[GS.IDX['rounds']], 120)

    def test_a_ball_holed_from_off_the_green_in_regulation_is_a_gir(self):
        """Aces and holed approaches within par - 2 strokes (penalties included) are greens in regulation with no
        putts; a chip-in after a missed green is a scramble."""
        from golfsim.engine import RoundStats, tally_hole
        def one(par, strokes, putts, gir=False):
            st = RoundStats()
            tally_hole(st, par, strokes, putts, gir, None)
            return st.gir, st.gir_putts, st.scramble_att, st.scramble_made
        self.assertEqual(one(3, 1, 0), (1, 0, 0, 0))                     # ace
        self.assertEqual(one(4, 2, 0), (1, 0, 0, 0))                     # holed approach for eagle
        self.assertEqual(one(5, 2, 0), (1, 0, 0, 0))                     # albatross
        self.assertEqual(one(5, 3, 0), (1, 0, 0, 0))                     # a penalty stroke and two shots, holed
        self.assertEqual(one(4, 3, 0), (0, 0, 1, 1))                     # chip-in birdie after missing the green
        self.assertEqual(one(4, 4, 0), (0, 0, 1, 1))                     # a penalty, then holed from off for par
        self.assertEqual(one(4, 5, 0), (0, 0, 1, 0))
        self.assertEqual(one(4, 4, 2, gir=True), (1, 2, 0, 0))           # on in two, two putts
        self.assertEqual(one(3, 2, 1, gir=True), (1, 1, 0, 0))
        # and as simulated, shot by shot: every hole finished without a putt follows the same rule
        from golfsim.engine import Conditions, Player, play_hole
        lib = default_library()
        course = lib.course(next(v for vs in lib.venues(2027).values() for v in vs))
        g = max(generate_world(seed=4, scale=0.01).golfers, key=lambda g: g.overall)
        seen = {'gir without a putt': 0, 'holed after missing': 0}
        for par in (3, 4):
            h = next(h for h in course.holes if h.par == par)
            for seed in range(1, 1500):
                rng = random.Random(seed)
                st = RoundStats()
                n = play_hole(Player(g, course, Conditions(), None, rng), h, course.holes.index(h), rng, st, pin=(0.0, 0.0))
                if st.putts == 0:
                    if n <= par - 2:
                        self.assertEqual((st.gir, st.scramble_att), (1, 0), (par, seed))
                        seen['gir without a putt'] += 1
                    else:
                        self.assertEqual((st.gir, st.scramble_att), (0, 1), (par, seed))
                        seen['holed after missing'] += 1
        self.assertTrue(all(seen.values()), seen)                        # both happened (an ace at seed 332)

    def test_aggregates_are_sums_of_counts_not_means_of_rates(self):
        a = dict.fromkeys(GS.FIELDS, 0) | {'fairways': 1, 'fairway_att': 2}
        b = dict.fromkeys(GS.FIELDS, 0) | {'fairways': 8, 'fairway_att': 10}
        both = {k: a[k] + b[k] for k in GS.FIELDS}
        self.assertEqual(GS.metric('fairways', both), 75.0)                 # 9/12, not (50 + 80) / 2
        self.assertIsNone(GS.metric('gir', a))                              # no holes: N/A, not 0%
        self.assertEqual(GS.fmt('gir', None), 'N/A')

    def test_qualified_driving_averages_are_filtered_before_they_are_limited(self):
        """150 longer averages from too few drives must not push a qualified performance off the record list."""
        def counters(tenths, drives):
            c = GS.empty() + [0, 0, 0]
            c[GS.IDX['drive_tenths']], c[GS.IDX['drives']] = tenths, drives
            return c
        base = {'tier': 4, 'tour': 'MN_TEST', 'series': 'S', 'category': 'regular', 'kind': 'pro', 'rounds': 2,
                'match_play': False, 'playoff': 0}
        events = [dict(base, id=f'2030:E{i}', week=i % 50 + 1, finish=[[(100 + i, 1, 140)]],
                       golf=[{str(100 + i): counters(9 * (3300 + i), 9)}]) for i in range(150)]
        events.append(dict(base, id='2030:Q', week=7, finish=[[(1, 1, 140)]], golf=[{'1': counters(25 * 3100, 25)}]))
        _, avgs, _, _ = ST.season_records(events, 2030)
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        store = ST.StatsStore(tmp / 's.sqlite')
        store.put(2030, 'x', {}, {}, {}, {}, (), ((), avgs, (), ()))
        q = ('SELECT person, drives FROM event_drives WHERE tier = ? ORDER BY CAST(tenths AS REAL) / drives DESC, '
             'person LIMIT 100')
        self.assertEqual(store.db.execute(q, (20,)).fetchall(), [(1, 25)])   # the qualified leader is kept
        self.assertEqual(len(store.db.execute(q, (8,)).fetchall()), 100)      # (8 drives: the 100 short samples)
        self.assertNotIn((1, 25), store.db.execute(q, (8,)).fetchall())
        store.db.execute("UPDATE meta SET value = '2' WHERE key = 'schema'")    # an older store is rebuilt
        store.db.commit()
        store.close()
        again = ST.StatsStore(tmp / 's.sqlite')
        self.assertEqual(again.db.execute('SELECT COUNT(*) FROM event_drives').fetchone()[0], 0)
        self.assertEqual(again.sources(), {})
        again.close()

    def test_winning_margins_and_match_results(self):
        base = {'tier': 1, 'tour': 'PT_AMERICAS', 'series': 'S', 'week': 5, 'category': 'regular', 'kind': 'pro',
                'rounds': 4, 'match_play': False}
        events = [
            dict(base, id='2030:A', finish=[[(1, 1, 270), (2, 2, 275), (3, 2, 275), (4, 4, 280)]], playoff=0),
            dict(base, id='2030:B', finish=[[(5, 1, 272), (6, 2, 272), (7, 3, 279)]], playoff=2),
            dict(base, id='2030:C', finish=[[(8, 1, 200)], [(9, 1, 199), (10, 2, 210)]], playoff=0),   # two sites
            dict(base, id='2030:Q', tier=7, kind='qualifying', finish=[[(11, 1, 140), (12, 2, 160)]], playoff=0),
            dict(base, id='2030:M', match_play=True, finish=[[(13, 1, None), (14, 2, None)]], playoff=0,
                 matches=[[['round of 64', 13, 15, '7&6', 18], ['final', 13, 14, '37 holes', 36],
                           ['semi-final', 14, 16, '2 up', 18]]]),
        ]
        longs, avgs, margins, matches = ST.season_records(events, 2030)
        by = {m[2]: m for m in margins}
        self.assertEqual(set(by), {'2030:A', '2030:B'})                     # multi-site, qualifying, match play out
        a = by['2030:A']
        self.assertEqual((a[7], a[8], a[9], a[10]), (1, 270, 275, 5))
        self.assertEqual(json.loads(a[11]), [2, 3])                         # every tied runner-up
        b = by['2030:B']
        self.assertEqual((b[10], b[12]), (0, 2))                            # playoff: regulation margin zero
        got = {(m[5], m[8]): (m[10], m[11]) for m in matches}
        self.assertEqual(got[('round of 64', '7&6')], (7, 6))
        self.assertEqual(got[('final', '37 holes')], (1, 0))
        self.assertEqual(got[('semi-final', '2 up')], (2, 0))


class GolfHistoryTests(unittest.TestCase):
    """A small world played across two season boundaries, reloaded and advanced again."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.dir = cls.tmp / 'w'
        s = Session.create(cls.dir, seed=17, workers=1, world=generate_world(seed=17, scale=SCALE))
        s.advance(52 * 2 + 2)                       # 2027 and 2028 archived; 2029 weeks 1-2 played
        s.close()
        s = Session.open(cls.dir, workers=1)        # reload, then one week twice under one request key
        s.advance_one_week(op_key='same-request')
        s.advance_one_week(op_key='same-request')
        cls.cursor = dict(s.cursor)
        cls.live_results = {eid: r for eid, r in s.season.results.items() if r.year == s.cursor['year']}
        cls.pstats_years = sorted(s.season.pstats)
        s.close()
        cls.w = O.World(cls.dir, workers=1)
        cls.w.reload()
        cls.a = Archive(cls.dir / 'archive')

    @classmethod
    def tearDownClass(cls):
        cls.a.close()
        cls.w.close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def page(self, path):
        u = urlparse(path)
        return O.render(self.w, u.path, parse_qs(u.query))[1]

    def built(self):
        db, building = self.w.statistics()
        if db is None:
            self.w._builder.wait(300)
            db, building = self.w.statistics()
        self.assertIsNotNone(db, building)
        return db

    def test_a_repeated_request_plays_one_week(self):
        self.assertEqual((self.cursor['year'], self.cursor['week']), (2029, 4))

    def test_counters_survive_season_boundaries_and_reconcile_with_scores(self):
        self.assertEqual(self.a.years, [2027, 2028])
        for y in (2027, 2028):                                              # the archive keeps every edition
            d = self.a.year(y)
            self.assertEqual(d['definitions'], {'golf_stats': GS.VERSION, 'ranking': 'world-ranking-1'})
            n = 0
            for e in d['events']:
                for k, site in enumerate(e['finish']):
                    for g, pos, total in site:
                        rs = e['scores'][k].get(str(g), [])
                        c = e['golf'][k].get(str(g))
                        if not rs:
                            self.assertIsNone(c)
                            continue
                        n += 1
                        c = GS.as_dict(c[:GS.N])
                        self.assertEqual((c['rounds'], c['strokes'], c['holes']), (len(rs), sum(rs), 18 * len(rs)))
            self.assertGreater(n, 500)

    def test_store_sums_every_start_once_and_merges_the_live_season(self):
        db = self.built()
        expect = defaultdict(lambda: GS.empty())
        starts = defaultdict(int)
        for y in self.a.years:
            for e in self.a.year(y)['events']:
                if e['kind'] == 'qualifying':
                    continue
                for k, site in enumerate(e['golf']):
                    for g, c in site.items():
                        GS.add(expect[int(g)], c[:GS.N])
                        starts[int(g)] += 1
        got = ST.query(db, None, None)
        for g, c in list(expect.items())[:400]:
            self.assertEqual([got[g][f] for f in GS.FIELDS], c, g)
            self.assertEqual(got[g]['golf_starts'], starts[g])
        live = self.w.live_statistics()
        merged = ST.query(db, None, None, live)
        live_rounds = defaultdict(int)
        for r in self.live_results.values():
            if self.w.live.editions[r.event_id]['kind'] == 'qualifying':     # (not starts: left out)
                continue
            for site in r.golf:
                for g, c in site.items():
                    live_rounds[g] += c[GS.IDX['rounds']]
        for g in list(live_rounds)[:200]:
            self.assertEqual(merged[g]['rounds'], got[g]['rounds'] + live_rounds[g], g)

    def test_profile_and_stats_pages_show_the_figures_with_their_sample(self):
        db = self.built()
        pid = max(ST.query(db, None, None).items(), key=lambda kv: kv[1]['rounds'])[0]
        body = self.page(f'/golfer/{pid}')
        self.assertIn('Golf statistics', body)
        self.assertIn('<strong>Career</strong>', body)
        self.assertIn('starts</td>', body)                                   # coverage column
        stats = self.page('/stats?show=golf&min=0&sort=rounds')
        self.assertIn('Driving dist.', stats)
        self.assertIn(f'/golfer/{pid}"', stats)
        for name in OG.GOLF_RECORDS:
            self.assertIn('<table', self.page(f'/golf-records/{name}?min=1&field=2&rounds=4'), name)
        eid = next(e['id'] for e in self.a.year(2028)['events'] if e['kind'] == 'major')
        self.assertIn('Longest drive', self.page(f'/event/{eid}?view=stats'))

    def test_ranking_points_reproduce_the_engine_exactly(self):
        lv = self.w.live
        at = OG.last_played(self.w)
        self.assertEqual(at, (2029, 3))
        checked = 0
        for g, avg in lv.wr_avg.items():
            r = OG.ranking_at(self.w, g, at)
            self.assertEqual(r['average'], avg, g)                           # exact: same sums, same order
            checked += 1
        self.assertGreater(checked, 50)
        for y, wk in ((2027, 10), (2028, 30), (2028, 52)):                  # seeded points, two seasons, a boundary
            snap = self.a.year(y)['ranking_points'][str(wk)]
            for g, avg, n in snap:
                r = OG.ranking_at(self.w, g, (y, wk))
                self.assertEqual((r['average'], r['events']), (avg, n), (y, wk, g))
        top = min(lv.wr, key=lv.wr.get)
        body = self.page(f'/golfer/{top}')
        self.assertIn('World ranking points', body)
        self.assertIn('Weight now', body)
        self.assertIn('No. 1 ·', body)
        self.assertIn(f'/golfer/{top}"', self.page('/rankings?kind=points'))

    def test_the_qualification_toggle_works_both_ways(self):
        import re
        def toggle(body, label):
            m = re.search(r'href="([^"]*)">' + label + '</a>', body)
            self.assertIsNotNone(m, label)
            return m.group(1).replace('&amp;', '&')
        self.built()
        default = self.page('/stats?show=golf&year=2028&sort=gir')
        everyone = toggle(default, 'include everyone')
        self.assertIn('min=0', everyone)
        self.assertIn('year=2028', everyone)
        self.assertIn('sort=gir', everyone)
        body = self.page(everyone)
        self.assertIn('at least 0 recorded rounds', body)
        back = toggle(body, 'qualified only')
        self.assertNotIn('min=', back)                                      # the minimum is dropped, not kept at 0
        self.assertIn('year=2028', back)
        again = self.page(back)
        self.assertIn(f'at least {OG.QUALIFY["season_rounds"]} recorded rounds', again)
        self.assertIn('include everyone', again)
        self.assertIn('name="min" value="0"', body)                          # filters keep the choice

    def test_ranking_labels_agree_live_and_archive_only(self):
        """The position comes from the ranking recorded for the week shown, with or without a live world."""
        lv = self.w.live
        at = OG.last_played(self.w)
        top = lv.rank_top[at[1]]
        for i, (g, _, _) in enumerate(top[:50], 1):                         # live: the table and the snapshot agree
            self.assertEqual(lv.wr[g], i)
            self.assertEqual(OG.position_at(self.w, g, at), f'No. {i}')
        arch = O.World(self.dir / 'archive')                                # archive only: no live world
        self.addCleanup(arch.close)
        self.assertIsNone(arch.live)
        self.assertEqual(OG.last_played(arch), (2028, 52))
        d = self.a.year(2028)
        snap = d['ranking_points']['52']
        order = d['rankings']['world']['52']                                # the engine's own order, top 100
        for i, (g, avg, _) in enumerate(snap[:50], 1):
            self.assertEqual(OG.position_at(arch, g, (2028, 52), avg), f'No. {i}')
            self.assertEqual(order[i - 1], g)
            self.assertEqual(OG.position_at(self.w, g, (2028, 52), avg), f'No. {i}')   # the live world, same week
            self.assertIn(f'No. {i} ·', arch_page(arch, g))
        none = [g for g in self.a.people if OG.ranking_at(arch, g, (2028, 52))['average'] == 0
                and (self.a.people[g].get('golfer') or {}).get('status') == 'pro']
        from unittest import mock
        short = {'ranking_points': {'52': snap[:2]}}                         # a golfer with points below the record
        with mock.patch.object(OG, '_season_file', return_value=short):
            self.assertEqual(OG.position_at(arch, snap[5][0], (2028, 52), snap[5][1]), 'outside the recorded top 2')
        self.assertTrue(none)
        self.assertEqual(OG.position_at(arch, none[0], (2028, 52), 0.0), 'unranked (no points in the last 104 weeks)')
        self.assertEqual(OG.position_at(arch, none[0], (2026, 52), 0.0), 'position not recorded')

    def test_old_seasons_read_not_recorded(self):
        e = self.w.edition(next(iter(self.live_results)))
        import observer_history as OH
        from unittest import mock
        with mock.patch.object(OH, 'full_edition', return_value={'id': e['id'], 'finish': []}):
            self.assertIn('were not recorded', OG.edition_stats(self.w, e))


if __name__ == '__main__':
    unittest.main()
