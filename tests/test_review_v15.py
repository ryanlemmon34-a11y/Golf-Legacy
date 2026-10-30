"""HAL's review of 07cecee: four findings, each with its regression.

A. A golfer who already holds a Britannia Open place through a qualifying-series event played earlier does not
   enter regional or final qualifying (no entry, no cost, no starting place used); a golfer with only a
   *projected* ranking place still can.
B. Hide results also covers season recaps (majors and their champions, leading winners, moments), the Career
   Grand Slam (profile line and page), records set by a single hidden result, golf records, ranking points,
   a golfer's season page and status lines that name a hidden win.
C. A playoff's tie is shown against the par of all the regulation rounds (283 on a par-72 course over four
   rounds is -5, not +211).
D. "Watch from round 1" restarts at round one; Resume returns to the round last watched.

Run from the project folder:  python -m unittest tests.test_review_v15 -v
"""
from __future__ import annotations

import copy
import pickle
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
from golfsim import qualification as Q                                    # noqa: E402
from golfsim.calendar import TOUR_BY_KEY, WorldCalendar                   # noqa: E402
import observer_history as OH                                             # noqa: E402
import observer_spoilers as SP                                            # noqa: E402


def ctx_for(people):
    ctx = Q.QualificationContext.from_calendar(WorldCalendar(2027, 'v2'))
    for gid, status in people.items():
        ctx.people[gid] = Q.Person(gid, f'G{gid}', status=status)
    return ctx


class A_SeriesPlacesCount(unittest.TestCase):
    def test_a_completed_series_place_is_earned_and_passes_down(self):
        ctx = ctx_for({i: 'pro' for i in range(1, 200)})
        ctx.world_rankings[(2030, 21)] = list(range(100, 200))            # 1-6 are outside the top 50
        ctx.add_result('PT_HEARTLAND_INVITATIONAL', 2030, [(120, 1), (3, 2), (4, 3), (5, 4), (6, 5)], week=23)
        exempt, pending = Q.earned_exemptions('BRITANNIA_OPEN', 2030, ctx.as_of(2030, 26))
        self.assertEqual(exempt[120], ['B5'])                              # the winner is in the top 50 already
        for gid in (3, 4, 5):                                              # three places, passed down past 150
            self.assertEqual(exempt[gid], ['BQ_PT_HEARTLAND_INVITATIONAL'], gid)
        self.assertNotIn(6, exempt)                                        # three places only
        self.assertNotIn('BQ_PT_SCOTLAND_OPEN', {c for v in exempt.values() for c in v})   # not played yet
        # the same places the field will give (exemptions first, then the series in the rules' order)
        for wk in range(1, 30):
            ctx.world_rankings.setdefault((2030, wk), list(range(100, 200)))
        field = {e.golfer_id: e.primary for e in Q.build_field('BRITANNIA_OPEN', 2030, ctx).entries}
        for gid in (3, 4, 5):
            self.assertEqual(field[gid], 'BQ_PT_HEARTLAND_INVITATIONAL')

    def test_a_projected_ranking_place_is_never_earned(self):
        ctx = ctx_for({i: 'pro' for i in range(1, 200)})
        ctx.world_rankings[(2030, 21)] = list(range(100, 200))            # the published Britannia cut-off
        ctx.world_rankings[(2030, 25)] = [7] + list(range(100, 199))      # 7 is projected No. 1 now
        exempt, _ = Q.earned_exemptions('BRITANNIA_OPEN', 2030, ctx.as_of(2030, 26))
        self.assertNotIn(7, exempt)                                        # still free to qualify
        exempt, pending = Q.earned_exemptions('USA_OPEN', 2030, ctx.as_of(2030, 17))
        self.assertIn('U9', pending)
        self.assertNotIn(7, exempt)


class A_SeasonStages(unittest.TestCase):
    """A small reference-calendar season to week 25, then the Britannia stages twice: as played, and with two
    golfers given the Heartland Invitational's places (week 23): a Challenger golfer outside the top 50 with no
    other exemption (on the direct-to-final list), and a golfer who did enter final qualifying as played."""

    @classmethod
    def setUpClass(cls):
        from golfsim.population import generate_world
        from golfsim.season import Season
        s = Season(generate_world(seed=101, scale=0.15), seed=101, development=True, workers=2, calendar='v2')
        s.start_year(2027)                                                  # (the smallest scale with Challenger tours)
        for wk in range(1, 18):
            s.advance_week(2027, wk)
        cls.usa = copy.deepcopy(s.stage_log[(2027, 'USA_OPEN')])           # (as it stood at local qualifying)
        cls.usa_wr = list(s.ctx.world_rankings[(2027, 16)])
        for wk in range(18, 26):
            s.advance_week(2027, wk)
        cls.blob = pickle.dumps(s)
        a = pickle.loads(cls.blob)
        for wk in (26, 27, 28):
            a.advance_week(2027, wk)
        cls.entered = {sid: {g for rows in a.ctx.results.get((sid, 2027), {}).values() for g, _ in rows}
                       for sid in STAGES}
        st = a.stage_log[(2027, 'BRITANNIA_OPEN')]
        top50 = set(a.ctx.world_rankings[(2027, 21)][:50])
        cls.challenger = sorted(g for g in st['direct'] if g not in top50 and
                                getattr(TOUR_BY_KEY.get(a.g[g].tour), 'tier', 9) == 2)
        cls.finalist = sorted(g for g in cls.entered['BRITANNIA_FINAL'] if g in st['direct'] and g not in top50)
        a.close()
        s.close()

    def test_a_series_qualifiers_skip_qualifying(self):
        self.assertTrue(self.challenger and self.finalist)
        c, f = self.challenger[0], self.finalist[0]
        b = pickle.loads(self.blob)
        (site, rows), = b.ctx.results[('PT_HEARTLAND_INVITATIONAL', 2027)].items()
        b.ctx.results[('PT_HEARTLAND_INVITATIONAL', 2027)] = {site: [(c, 1), (f, 2)] + [(g, p) for g, p in rows
                                                                                       if g not in (c, f)]}
        for wk in (26, 27, 28):
            b.advance_week(2027, wk)
        st = b.stage_log[(2027, 'BRITANNIA_OPEN')]
        for gid in (c, f):
            self.assertIn(gid, st['exempt'])                               # their place counts as earned
            self.assertNotIn(gid, st['pool'])
            self.assertNotIn(gid, st['direct'])
            for sid in STAGES:                                             # no entry: no fee or travel booked
                entered = {g for rows in b.ctx.results.get((sid, 2027), {}).values() for g, _ in rows}
                self.assertNotIn(gid, entered, (gid, sid))                # (costs are booked per finisher)
        self.assertIn(f, self.entered['BRITANNIA_FINAL'])                  # as played, f used a final place
        final = {g for rows in b.ctx.results[('BRITANNIA_FINAL', 2027)].values() for g, _ in rows}
        fs = b.cal.by_id['BRITANNIA_FINAL']
        cap = fs.field * fs.sites
        if len(self.entered['BRITANNIA_FINAL']) >= cap:                    # a full final: f's place went to another
            self.assertEqual(len(final), cap)
        b.advance_week(2027, 29)
        b.advance_week(2027, 30)
        entry = {e.golfer_id: e for e in b.stage_log[(2027, 'BRITANNIA_OPEN', 'field')].entries}
        for gid in (c, f):                                                 # and the place is in the field
            self.assertEqual(entry[gid].primary, 'BQ_PT_HEARTLAND_INVITATIONAL')
        b.close()

    def test_a_projected_ranking_still_qualifies_in_a_season(self):
        """USA local qualifying (week 17) comes before the week-20 ranking cut-off: the ranking places are
        pending, and golfers inside the projected top 60 who hold nothing else keep their attempt."""
        self.assertIn('U9', self.usa['pending'])
        projected = set(self.usa_wr[:60]) - self.usa['exempt']
        self.assertTrue(projected)
        self.assertTrue(projected <= set(self.usa['direct']) | set(self.usa['pool']))   # nobody's attempt removed


STAGES = ('BRITANNIA_REGIONAL_1', 'BRITANNIA_REGIONAL_2', 'BRITANNIA_FINAL')


class C_PlayoffPar(unittest.TestCase):
    def w(self):
        return SimpleNamespace(person_link=lambda g: f'<a href="/golfer/{g}">G{g}</a>', name=lambda g: f'G{g}')

    def test_four_rounds(self):
        full = {'finish': [[(1, 1, 283), (2, 2, 283), (3, 2, 283), (4, 4, 285)]], 'playoff': 2, 'rounds': 4,
                'scores': [{'1': [70, 71, 71, 71], '2': [71, 71, 71, 70], '3': [72, 70, 70, 71]}],
                'playoffs': [{'players': [1, 2, 3], 'winner': 1, 'holes': [[1, 18, {'1': 4, '2': 4, '3': 5}],
                                                                           [2, 17, {'1': 3, '2': 4}]]}]}
        html = OH.playoff_lines(self.w(), full, 0, 72)
        self.assertIn('tied at 283 (-5)', html)
        self.assertNotIn('+211', html)

    def test_two_rounds(self):
        full = {'finish': [[(1, 1, 138), (2, 2, 138)]], 'playoff': 1, 'rounds': 2,
                'scores': [{'1': [69, 69], '2': [70, 68]}],
                'playoffs': [{'players': [1, 2], 'winner': 1, 'holes': [[1, 18, {'1': 3, '2': 4}]]}]}
        self.assertIn('tied at 138 (-2)', OH.playoff_lines(self.w(), full, 0, 70))

    def test_an_older_archive_without_holes_or_rounds(self):
        full = {'finish': [[(11, 1, 283), (12, 2, 283), (13, 4, 285)]], 'playoff': 2, 'rounds': 4}
        html = OH.playoff_lines(self.w(), full, 0, 72)
        self.assertIn('tied at 283 (-5)', html)                            # rounds from the edition
        self.assertIn('not recorded', html)
        self.assertNotIn('(', OH.playoff_lines(self.w(), {**full, 'rounds': None}, 0, 72).split('tied at 283')[1][:2])


def stub_world(majors, hide_from=None, revealed=None):
    """A world holding only this season's majors (live editions), with Hide results as given."""
    eds = {}
    for eid, week, winner in majors:
        sid = eid.split(':', 1)[1]
        eds[eid] = {'id': eid, 'series': sid, 'week': week, 'finish': [[(winner, 1, 280), (99, 2, 281)]]}
    w = SimpleNamespace(a=None, live=SimpleNamespace(editions=eds, cursor={'year': 2030, 'week': 40}), read_only=True,
                        series_name=lambda s: s.replace('_', ' ').title(), person=lambda g: {'born': 2000},
                        person_link=lambda g: f'<a href="/golfer/{g}">G{g}</a>', name=lambda g: f'G{g}')
    w._spoilers = {'hide': hide_from is not None, 'from': hide_from, 'revealed': dict(revealed or {})}
    return w


class B_GrandSlam(unittest.TestCase):
    MAJORS = [('2030:TOUR_MASTERS', 15, 7), ('2030:PREMIER_TOUR_CHAMPIONSHIP', 20, 7), ('2030:USA_OPEN', 25, 7),
              ('2030:BRITANNIA_OPEN', 30, 7)]

    def test_a_hidden_fourth_major_does_not_complete_the_slam(self):
        shown = stub_world(self.MAJORS)
        self.assertIn('Career Grand Slam', OH.grand_slam_line(shown, 7))
        hidden = stub_world(self.MAJORS, hide_from=[2030, 26])            # the Britannia Open (week 30) hidden
        line = OH.grand_slam_line(hidden, 7)
        self.assertNotIn('Career Grand Slam', line)
        self.assertNotIn('BRITANNIA_OPEN', line)
        self.assertIn('3 of the four', line)
        page = OH.grand_slam_page(hidden, {})[1]
        self.assertIn('Nobody has won all four majors yet', page)
        self.assertNotIn('2030%3ABRITANNIA_OPEN', page)
        revealed = stub_world(self.MAJORS, hide_from=[2030, 26], revealed={'2030:BRITANNIA_OPEN': 'final'})
        self.assertIn('Career Grand Slam', OH.grand_slam_line(revealed, 7))   # revealed: shown again
        self.assertEqual([r[2] for r in OH.major_wins(hidden)], [e for e, _, _ in self.MAJORS[:3]])
        self.assertEqual(len(OH.major_wins(hidden, include_hidden=True)), 4)


class B_D_WorldPages(unittest.TestCase):
    """A small world with one archived season and Hide results on for every result."""

    @classmethod
    def setUpClass(cls):
        from golfsim.population import generate_world
        from golfsim.session import Session
        import observer as O
        cls.O = O
        cls.tmp = Path(tempfile.mkdtemp())
        s = Session.create(cls.tmp / 'w', seed=103, workers=1, world=generate_world(seed=103, scale=0.03))
        s.advance(52 + 6)
        s.close()
        cls.w = O.World(cls.tmp / 'w', workers=1)
        cls.w.reload()
        if cls.w.statistics()[0] is None:
            cls.w._builder.wait(300)

    @classmethod
    def tearDownClass(cls):
        cls.w.close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def setUp(self):
        SP.set_hide(self.w, False)

    def page(self, path):
        u = urlparse(path)
        return self.O.render(self.w, u.path, parse_qs(u.query))[1]

    def test_recaps_and_season_pages_hide_major_champions(self):
        majors = [m for m in OH.major_wins(self.w) if m[0] == 2027]
        self.assertTrue(majors)
        champs = {m[4] for m in majors}
        shown = self.page('/season/2027')
        self.assertTrue(any(f'/golfer/{g}"' in shown.split('<h2>Majors</h2>')[1].split('</table>')[0] for g in champs))
        SP.set_hide(self.w, True, 'all')
        hidden = self.page('/season/2027')
        self.assertNotIn('<h2>Majors</h2>', hidden)
        self.assertIn('headline results', hidden)
        self.assertNotIn('Career Grand Slams completed', hidden)
        for m in majors:                                                   # every major's edition: not linked as won
            self.assertNotIn(f'at the <a href="/event/{m[2].replace(":", "%3A")}"', hidden)
        champ = majors[0][4]
        prof = self.page(f'/golfer/{champ}')
        self.assertNotIn(f'/event/{majors[0][2].replace(":", "%3A")}"', prof.split('<h2>Moments</h2>')[-1]
                         if '<h2>Moments</h2>' in prof else '')
        season = self.page(f'/golfer/{champ}?tab=season&year=2027')
        self.assertIn('left out below', season)
        self.assertNotIn(f'won the 2027 {self.w.series_name(majors[0][3])}', season)
        rec = self.page('/records/youngest-major-champions')
        self.assertNotIn(f'/event/{majors[0][2].replace(":", "%3A")}"', rec)
        margins = self.page('/golf-records/largest-margin?rounds=4&field=2')
        for m in majors:
            self.assertNotIn(f'/event/{m[2].replace(":", "%3A")}"', margins)

    def test_restart_and_resume_are_separate(self):
        SP.set_hide(self.w, True, 'season')
        e = next(e for e in sorted(self.w.live.editions.values(), key=lambda e: e['id'])
                 if (e.get('rounds') or 0) >= 3 and not e.get('match_play') and len(e['sites']) == 1)
        eid = e['id']
        self.page(f'/event/{eid}?view=rounds&round=3')
        self.assertEqual(SP.watched(self.w, eid), 3)
        top = self.page(f'/event/{eid}')
        self.assertIn('<strong>after round 3</strong>', top)               # opening the event resumes
        resume = re.search(r'href="([^"]*)">Resume at round 3', top).group(1)
        restart = re.search(r'href="([^"]*)">Watch from round 1', top).group(1)
        self.assertIn('round=3', resume)
        self.assertIn('round=1', restart)
        again = self.page(restart.replace('&amp;', '&'))
        self.assertIn('<strong>after round 1</strong>', again)             # restarting opens round one
        self.assertEqual(SP.watched(self.w, eid), 3)                        # and Resume still returns to round 3
        self.assertIn('<strong>after round 3</strong>', self.page(f'/event/{eid}'))
        self.assertTrue(SP.hidden(self.w, eid))                             # nothing revealed by either


if __name__ == '__main__':
    unittest.main()
