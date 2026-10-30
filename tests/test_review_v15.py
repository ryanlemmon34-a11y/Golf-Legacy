"""HAL's review of 07cecee: four findings, each with its regression.

A. A golfer who already holds a Britannia Open place through a qualifying-series event played earlier does not
   enter regional or final qualifying (no entry, no cost, no starting place used); a golfer with only a
   *projected* ranking place still can.
B. (Hide results leaking winners: the setting has since been removed -- every page shows the complete history;
   tests/test_complete_history.py.)
C. A playoff's tie is shown against the par of all the regulation rounds (283 on a par-72 course over four
   rounds is -5, not +211).
D. "Watch from round 1" restarts at round one (tests/test_complete_history.py: replay without the removed setting).

Run from the project folder:  python -m unittest tests.test_review_v15 -v
"""
from __future__ import annotations

import copy
import pickle
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
from golfsim import qualification as Q                                    # noqa: E402
from golfsim.calendar import TOUR_BY_KEY, WorldCalendar                   # noqa: E402
import observer_history as OH                                             # noqa: E402


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


if __name__ == '__main__':
    unittest.main()
