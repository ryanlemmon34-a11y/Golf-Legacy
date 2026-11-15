"""Trophies from recorded winners (golfsim.awards) and fallible potential grades (golfsim.scouting).

On the career fixture world (seed 11, scale 0.05) after its first season; each test on its own temporary copy.

Run from the project folder:  python -m unittest tests.test_awards_scouting -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))
import career_fixture as F                                             # noqa: E402
from test_careertest2_fixes import Copy, started                       # noqa: E402
from golfsim import awards, scouting                                   # noqa: E402
from golfsim import career as CA                                       # noqa: E402
from golfsim.session import Session                                    # noqa: E402

HIDDEN = ('potential', 'ceiling', 'peak_age', 'aging_rate')


class NoPeeking(dict):
    def __getitem__(self, k):
        raise AssertionError('a hidden ceiling was read')

    def get(self, *a):
        raise AssertionError('a hidden ceiling was read')


class Trophies(unittest.TestCase):
    def test_winners_are_recorded_results_of_trophy_events_only(self):
        with Copy() as s:
            se = s.season
            w = awards.winners(se)
            self.assertTrue(w)
            for (sid, y), gid in w.items():
                ser = se.cal.by_id[sid]
                self.assertIn(awards.trophy_kind(ser), ('major', 'college', 'amateur'))
                sites = se.ctx.results[(sid, y)]
                self.assertEqual(len(sites), 1)
                self.assertEqual([g for g, p in next(iter(sites.values())) if p == 1], [gid])
            kinds = {awards.trophy_kind(se.cal.by_id[sid]) for sid, _ in w}
            self.assertEqual(kinds, {'major', 'college', 'amateur'})
            for sid in ('USA_AMATEUR_QUALIFYING', 'COLLEGE_REGIONAL_1', 'USA_OPEN_FINAL'):
                self.assertIsNone(awards.trophy_kind(se.cal.by_id[sid]))   # qualifiers and regionals: no trophy

    def test_a_golfers_trophies_engraving_and_multiple_wins(self):
        with Copy() as s:
            se = s.season
            (sid, y), gid = next((k, v) for k, v in awards.winners(se).items() if k[0].startswith('NATIONAL_AMATEUR'))
            t = [x for x in awards.trophies(se, gid) if x['series_id'] == sid]
            self.assertEqual(len(t), 1)
            self.assertEqual((t[0]['event_id'], t[0]['year'], t[0]['winner_id'], t[0]['kind'], t[0]['times_won']),
                             (f'{y}:{sid}', y, gid, 'amateur', 1))
            self.assertEqual(t[0]['winner_name'], se.g[gid].name)
            self.assertIsNone(t[0]['during_control'])                   # no career
            # a second recorded win of the same championship the next season (test set-up: a played edition)
            se.ctx.results[(sid, y + 1)] = {0: [(gid, 1), (1, 2)]}
            t = [x for x in awards.trophies(se, gid) if x['series_id'] == sid]
            self.assertEqual([(x['year'], x['times_won']) for x in t], [(y, 1), (y + 1, 2)])
            self.assertEqual([e['year'] for e in awards.engraving(se, sid)], [y, y + 1])
            se.ctx.results[(sid, y + 2)] = {0: [(gid, 1), (2, 1)]}       # two recorded winners: no trophy
            self.assertNotIn((sid, y + 2), awards.winners(se))

    def test_the_career_view_carries_the_controlled_golfers_trophies(self):
        with Copy() as s:
            g = started(s)
            v = CA.view(s.season, s.cursor)
            self.assertEqual(v['trophies'], [])                         # a newcomer: none yet
            sid = 'NATIONAL_AMATEUR_ARGENTINA'
            s.season.ctx.results[(sid, 2028)] = {0: [(g.id, 1)]}      # (test set-up: a recorded win in control)
            t = CA.view(s.season, s.cursor)['trophies']
            self.assertEqual(len(t), 1)
            self.assertTrue(t[0]['during_control'])


class Scouting(unittest.TestCase):
    def test_a_first_look_when_control_starts(self):
        with Copy() as s:
            g = started(s)
            v = CA.view(s.season, s.cursor)['scouting']
            self.assertEqual(v['as_of'], [2028, 1])
            self.assertEqual([c['category'] for c in v['categories']], list(scouting.CATS))
            for c in v['categories']:
                self.assertIn(c['grade'], ('A', 'B', 'C', 'D', 'F'))
                self.assertEqual(c['confidence'], 'low')               # one look
                self.assertEqual(len(c['history']), 1)
                for h in HIDDEN:
                    self.assertNotIn(h, c['explanation'].lower())

    def test_never_reads_ceilings_and_draws_nothing_from_the_world(self):
        with Copy() as s:
            g = started(s)
            se, c = s.season, s.season.career
            before = F.digest(s)
            real = g.ceilings
            g.ceilings = NoPeeking(real)
            try:
                o = scouting.observe(se, c, g.id, 2028, 52)
            finally:
                g.ceilings = real
            self.assertEqual(F.digest(s), before)
            self.assertIs(scouting.observe(se, c, g.id, 2028, 52), o)   # once per (year, week)
            self.assertEqual(len(c.observations[g.id]), 2)

    def test_grades_move_with_observed_progress_and_are_kept(self):
        with Copy() as s:
            g = started(s)
            se, c = s.season, s.season.career
            for k in g.attrs:
                g.attrs[k] = min(99.0, g.attrs[k] + 8.0)               # (test set-up: a strong season observed)
            o = scouting.observe(se, c, g.id, 2029, 52)
            v = scouting.view(se, c, g.id)
            self.assertEqual(v['as_of'], [2029, 52])
            for cat in scouting.CATS:
                e = o['estimates'][cat]
                self.assertGreater(e['recent'], e['typical'])           # faster than typical: shows in the read
                hist = next(x for x in v['categories'] if x['category'] == cat)['history']
                self.assertEqual([h['year'] for h in hist], [2028, 2029])
                self.assertEqual(hist[0]['grade'], c.observations[g.id][0]['estimates'][cat]['grade'])  # kept
            d = s.dir
            s._commit()
            s.close()
            s2 = Session.open(d)
            self.assertEqual(scouting.view(s2.season, s2.season.career, g.id), v)   # the same after a reload
            s2.close()
            s.dir = d

    def test_grade_bands(self):
        self.assertEqual([scouting.grade(x) for x in (80, 73, 70, 60, 50, 30)], ['A', 'A', 'B', 'C', 'D', 'F'])

    def test_a_career_without_observations_says_so(self):
        with Copy() as s:
            g = started(s)
            c = s.season.career
            c.observations = {}                                        # (an older career record)
            v = scouting.view(s.season, c, g.id)
            self.assertIsNone(v['as_of'])
            self.assertTrue(all(x['grade'] is None and x['explanation'] for x in v['categories']))


if __name__ == '__main__':
    unittest.main()
