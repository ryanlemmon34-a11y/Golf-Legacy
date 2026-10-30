"""History views (2090 world audit and roadmap, 30 October 2026): recorded round scores reproduce totals and cuts,
recorded payouts reconcile with the money paid and drive per-tour prize money, round views are labelled replays,
entry routes read in words with a link to versioned rules, a season page shows that season's facts (never today's
ratings), coach and caddie histories are separate, residence shows the initial placement apart from moves,
tournament and course summaries count their editions, records show dates and who is still pursuing them, the
recap links its evidence, and the Career Grand Slam is completed by four distinct majors.

Run from the project folder:  python -m unittest tests.test_observer_history -v
"""
from __future__ import annotations

import re
import shutil
import sys
import tempfile
import unittest
from collections import Counter, defaultdict
from pathlib import Path
from unittest import mock
from urllib.parse import parse_qs, quote, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
from golfsim import rules as R                                        # noqa: E402
from golfsim.archive import Archive                                   # noqa: E402
from golfsim.population import generate_world                         # noqa: E402
from golfsim.session import Session                                   # noqa: E402
import observer as O                                                  # noqa: E402
import observer_data as OD                                            # noqa: E402
import observer_history as OH                                         # noqa: E402
import observer_stats as ST                                           # noqa: E402

SCALE = 0.02


class HistoryViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.base = cls.tmp / 'base'                                    # 2027 archived; 2028 to week 21 (Masters played)
        s = Session.create(cls.base, seed=13, workers=1, world=generate_world(seed=13, scale=SCALE))
        s.advance(52 + 20)
        s.close()
        cls.w = O.World(cls.base, workers=1)
        cls.w.reload()
        cls.year = Archive(cls.base / 'archive')
        cls.season = cls.year.year(2027)

    @classmethod
    def tearDownClass(cls):
        cls.year.close()
        cls.w.close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def page(self, path):
        u = urlparse(path)
        return O.render(self.w, u.path, parse_qs(u.query))[1]

    def built(self):
        db, building = self.w.statistics()
        if db is None:
            self.w._builder.wait(120)
            db, building = self.w.statistics()
        self.assertIsNotNone(db, building)
        return db

    # -- recorded facts ----------------------------------------------------------------------------------------
    def test_round_scores_reproduce_totals_and_cuts(self):
        n = 0
        for e in self.season['events']:
            self.assertIn('scores', e)
            for k, site in enumerate(e['finish']):
                scores = e['scores'][k]
                for g, pos, total in site:
                    rs = scores.get(str(g), [])
                    if total is not None:
                        n += 1
                        self.assertEqual(sum(rs), total, (e['id'], g))
                        self.assertEqual(len(rs), e['rounds'], (e['id'], g))
                    if pos is None and e['cut_top'] and not e['match_play'] and e['rounds'] > 2:
                        self.assertEqual(len(rs), 2, (e['id'], g))           # missed cut: the two rounds before it
                if e['conditions'][k] is not None and not e['match_play']:
                    self.assertEqual(len(e['conditions'][k]), e['rounds'])
        self.assertGreater(n, 500)
        majors = [e for e in self.season['events'] if e['kind'] == 'major']
        self.assertEqual(len(majors), 4)
        for e in majors:
            for g, card in e['holes'][0].items():
                self.assertEqual([sum(h) for h in card], e['scores'][0][g])
            self.assertEqual(len(e['pars'][0]), 18)

    def test_recorded_payouts_reconcile_and_drive_tour_prize_money(self):
        paid = defaultdict(float)
        by_tour = defaultdict(float)
        for e in self.season['events']:
            for site in e['prizes']:
                for g, x in site.items():
                    paid[int(g)] += x
                    by_tour[(int(g), e['tour'])] += x
            self.assertLessEqual(sum(sum(s.values()) for s in e['prizes']), (e['purse'] or 0) + 1)
        for g, row in self.season['careers'].items():
            self.assertAlmostEqual(row['prize'], round(paid.get(g, 0.0)), delta=1, msg=g)
        # the index carries each start's prize, the stats store's per-tour money is the recorded payouts
        idx = self.w.a.index
        got = defaultdict(float)
        for g, x in idx.db.execute('SELECT person, prize FROM starts WHERE year = 2027'):
            self.assertIsNotNone(x)
            got[g] += x
        self.assertEqual({g: round(x, 2) for g, x in got.items() if x}, {g: round(x, 2) for g, x in paid.items() if x})
        db = self.built()
        for (g, tour), x in list(by_tour.items())[:300]:
            row = db.execute('SELECT prize FROM agg WHERE person = ? AND year = 2027 AND tour = ?', (g, tour)).fetchone()
            self.assertIsNotNone(row, (g, tour))
            self.assertAlmostEqual(row[0], x, delta=0.01)

    # -- rounds and replay -----------------------------------------------------------------------------------------
    def test_rounds_view_is_a_labelled_replay_with_cut_and_scorecards(self):
        eid = '2027:TOUR_MASTERS'
        e = next(x for x in self.season['events'] if x['id'] == eid)
        body = self.page(f'/event/{eid}?view=rounds&round=1')
        self.assertIn('Replay', body)
        self.assertIn('nothing is simulated', body)
        r1 = sorted(v[0] for v in e['scores'][0].values())
        leader = min(e['scores'][0], key=lambda g: (e['scores'][0][g][0], int(g)))
        self.assertIn(f'/golfer/{leader}"', body.split('<tbody>')[1].split('</tr>')[0])
        final = self.page(f'/event/{eid}?view=rounds')
        missed = [g for g, p, _ in e['finish'][0] if p is None]
        if missed:
            self.assertIn('missed cut', final)
        winner = next(g for g, p, _ in e['finish'][0] if p == 1)
        card = self.page(f'/event/{eid}?view=rounds&player={winner}')
        self.assertIn('Scorecard', card)
        self.assertIn('<td>Par</td>', card)
        self.assertEqual(r1[0], min(v[0] for v in e['scores'][0].values()))

    def test_editions_without_rounds_say_so(self):
        e = self.w.edition('2027:TOUR_MASTERS')
        with mock.patch.object(OH, 'full_edition', return_value={'id': e['id'], 'finish': []}):
            self.assertIn('were not recorded', OH.rounds_view(self.w, {}, e))

    def test_live_major_has_rounds_and_prizes(self):
        live = self.w.live.editions['2028:TOUR_MASTERS']
        self.assertTrue(live['scores'] and live['prizes'] and live['holes'] and live['pars'])
        body = self.page('/event/2028:TOUR_MASTERS')
        self.assertIn('$', body)
        self.assertIn('Rounds &amp; replay', body)
        self.assertIn('2026-10-30', body)                              # the rules the season is played under

    # -- entry routes and rules -------------------------------------------------------------------------------------
    def test_routes_read_in_words_with_rule_links_and_codes(self):
        body = self.page('/event/2027:TOUR_MASTERS')
        self.assertIn('href="/rules#major-qualification"', body)
        self.assertRegex(body, r'class="tag" title="the code recorded with the start">M\d+<')
        rules = self.page('/rules')
        for rid in R.RULES:
            self.assertIn(f'id="{rid}"', rules)
        self.assertIn('2027', rules.split(R.RULES_VERSION)[1].split('</tr>')[0])    # 2027 played under it
        self.assertIn('the current season', rules)

    # -- a season as it was -------------------------------------------------------------------------------------------
    def test_season_view_uses_that_seasons_facts_not_todays(self):
        snaps = {}
        pid = next(g for g, r in self.season['careers'].items() if r['events'] >= 5 and g in self.w.live.people
                   and self.w.live.people[g].get('ratings'))
        snaps = OD.rating_snapshots(self.w, pid)
        body = self.page(f'/golfer/{pid}?tab=season&year=2027')
        row = self.season['careers'][pid]
        self.assertIn('Start of 2027', body)
        self.assertIn('End of season', body)
        end = snaps[2028]
        self.assertIn(f'<td class=n>{end[0]:.1f}</td>', body)          # the recorded end-of-2027 overall
        self.assertIn('unavailable', body)                             # no start-of-2027 snapshot (first season)
        self.assertIn(f'{row["wr_start"] or "—"} → {row["wr_end"] or "—"}', body)
        live = self.page(f'/golfer/{pid}?tab=season&year=2028')
        self.assertIn('partial season', live)

    def test_season_rows_link_to_seasons_and_total_a_career(self):
        pid = next(g for g, r in self.season['careers'].items() if r['events'] >= 5 and g in self.w.live.people)
        body = self.page(f'/golfer/{pid}?tab=playing')
        self.assertIn(f'/golfer/{pid}?tab=season&amp;year=2027', body.replace('&year', '&amp;year'))
        self.assertIn('Missed cuts', body)
        career = body.split('<strong>Career</strong>')[1].split('</tr>')[0]
        starts = len([r for r in OD.results(self.w, pid) if not OD.is_qualifying(r)])
        self.assertIn(f'>{starts}</a>', career)

    # -- status and team ----------------------------------------------------------------------------------------------
    def test_status_shows_membership_rights_and_changes(self):
        lv = self.w.live
        member = next(g for g, r in lv.rights.items() if g in lv.people)
        body = self.page(f'/golfer/{member}')
        self.assertIn('Premier playing rights', body)
        self.assertIn(lv.rights[member][1], body.replace('&#x27;', "'"))
        # a change of tour between two seasons shows the card reason recorded with the season before it
        pid = next(g for g in self.season['careers'] if g in self.w.a.people)
        rows = [(2026, {'tour': 'CH_ASIA', 'status': 'pro', 'lifestyle': 'full_time',
                        'card_reason': 'Premier card earned: won the 2026 USA Open', 'next_tour': 'PT_ASIA_PACIFIC'}),
                (2027, {'tour': 'PT_ASIA_PACIFIC', 'status': 'pro', 'lifestyle': 'full_time'})]
        with mock.patch.object(OD, 'career_rows', return_value=rows), \
                mock.patch.object(self.w.live, 'people', {}):
            html = OH.status_changes(self.w, pid)
        self.assertIn('How their status changed', html)
        self.assertIn('Premier card earned: won the 2026 USA Open', html)
        self.assertIn('after 2026', html)

    def test_coaches_and_caddies_are_separate_with_shared_starts(self):
        pid = next(g for g, c in self.w.live.caddie_of.items() if g in self.w.live.coach_of)
        body = self.page(f'/golfer/{pid}?tab=team')
        self.assertIn('<h2>Coaches</h2>', body)
        self.assertIn('<h2>Caddies</h2>', body)
        rows = OD.results(self.w, pid)
        for s in self.w.a.golfer_staff(pid):
            if s.kind in ('coach', 'caddie'):
                n = sum(1 for r in rows if r[s.kind] == s.staff and (r['year'], r['week']) >= s.start
                        and (s.end is None or (r['year'], r['week']) < s.end))
                self.assertIn(f'<td class=n>{n}</td>', body)

    def test_residence_shows_initial_placement_apart_from_moves(self):
        lv = self.w.live
        pid = next(g for g, f in lv.first.items() if f[3].startswith('at college') and g in lv.people)
        body = self.page(f'/golfer/{pid}')
        self.assertIn('Where they have lived', body)
        self.assertIn('initial placement, not a move', body)
        self.assertIn('at college', body)

    # -- tournaments, courses, records, recap ------------------------------------------------------------------------
    def test_series_and_course_summaries_count_their_editions(self):
        body = self.page('/series/TOUR_MASTERS')
        self.assertIn('in brief', body)
        self.assertIn('2 editions won', body)                          # 2027 archived, 2028 played this season
        idx = self.w.a.index
        cid = idx.db.execute('SELECT course FROM sites GROUP BY course ORDER BY COUNT(*) DESC LIMIT 1').fetchone()[0]
        total = idx.db.execute('SELECT COUNT(*) FROM starts st JOIN sites si ON st.eid = si.eid AND st.site = si.site '
                               'WHERE si.course = ?', (cid,)).fetchone()[0]
        live = sum(len(e['finish'][k]) for e in self.w.live.editions.values() for k, (c, _, _) in enumerate(e['sites'])
                   if c == cid)
        self.assertIn(f'{total + live:,} starts played here', self.page(f'/course/{cid}'))

    def test_records_show_when_and_who_is_pursuing(self):
        body = self.page('/records/most-wins')
        self.assertIn('<th title="Sort by this column">Now</th>', body)
        self.assertIn('competing: can add to it', body)
        body = self.page('/records/weeks-at-number-one')
        no1 = next(g for g, p in self.w.live.wr.items() if p == 1)
        if f'/golfer/{no1}"' in body:
            row = body.split(f'/golfer/{no1}"')[1].split('</tr>')[0]
            self.assertIn('world No. 1 now', row)

    def test_recap_links_majors_money_and_changes(self):
        body = self.page('/season/2027')
        self.assertIn('<h2>Majors</h2>', body)
        self.assertIn('Prize money leaders', body)
        self.assertIn('Career changes that winter', body)
        for e in (e for e in self.season['events'] if e['kind'] == 'major'):
            self.assertIn(f'/event/{quote(e["id"])}', body)

    def test_grand_slam_needs_four_distinct_majors(self):
        wins = [(2027, 18, '2027:TOUR_MASTERS', 'TOUR_MASTERS', 7), (2028, 18, '2028:TOUR_MASTERS', 'TOUR_MASTERS', 7),
                (2028, 21, '2028:PREMIER_TOUR_CHAMPIONSHIP', 'PREMIER_TOUR_CHAMPIONSHIP', 7),
                (2028, 24, '2028:USA_OPEN', 'USA_OPEN', 7), (2029, 28, '2029:BRITANNIA_OPEN', 'BRITANNIA_OPEN', 7),
                (2029, 18, '2029:TOUR_MASTERS', 'TOUR_MASTERS', 8)]
        gs = OH.grand_slams(self.w, wins)
        self.assertEqual(gs[7]['complete'], (2029, '2029:BRITANNIA_OPEN'))
        self.assertEqual(gs[7]['firsts']['TOUR_MASTERS'], (2027, '2027:TOUR_MASTERS'))
        self.assertIsNone(gs[8]['complete'])
        self.assertIsNone(OH.grand_slams(self.w, wins[:4])[7]['complete'])   # three distinct majors, one twice
        self.assertIn('Winners of all four majors', self.page('/grand-slam'))

    # -- tables and money -----------------------------------------------------------------------------------------------
    def test_tables_sort_and_money_formats(self):
        html = O.table(['A', 'B'], [['1', '2']], numeric=(1,))
        self.assertIn('<table class="sortable"><thead>', html)
        self.assertIn('<tbody><tr>', html)
        self.assertEqual(O.money(1234567.4), '$1,234,567')
        self.assertEqual(O.money(-1234), '-$1,234')
        self.assertIn('unknown', O.money(None))
        self.assertIn('table.sortable th', O.CSS)
        self.assertIn(OH.SORT_JS, O.page(self.w, 'x', 'y'))

    def test_staff_directories_sort_by_reputation(self):
        body = self.page('/coaches?sort=reputation')
        reps = [float(x) for x in re.findall(r'<td class=n>(\d+\.\d)</td>', body)]
        self.assertTrue(reps)
        self.assertEqual(reps, sorted(reps, reverse=True))


if __name__ == '__main__':
    unittest.main()
