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


class ScoutingCadence(unittest.TestCase):
    """Looks at control start, each period start, the first week after a coach change and the season's end; written
    by the career's gate only (never by a read); growth room as the judge's qualitative, uncertain opinion."""

    def gate(self, se, w):
        CA.gate(se, {'year': 2028, 'week': w, 'phase': 'week'})

    def test_period_and_coach_change_looks_from_the_gate_only(self):
        from test_careertest2_fixes import free_coach
        with Copy() as s:
            g = started(s)
            se, c = s.season, s.season.career
            rows = c.observations[g.id]
            self.assertEqual([(r['week'], r['reason']) for r in rows], [(1, 'start')])
            before = F.digest(s)
            real = g.ceilings
            g.ceilings = NoPeeking(real)
            try:
                for w in range(1, 10):
                    self.gate(se, w)
                    self.gate(se, w)                                   # asked twice: one look
                    for _ in range(3):                                 # reads write nothing
                        scouting.view(se, c, g.id)
                        CA.view(se, s.cursor)
            finally:
                g.ceilings = real
            self.assertEqual([(r['week'], r['reason']) for r in rows], [(1, 'start'), (5, 'period'), (9, 'period')])
            self.assertEqual(F.digest(s), before)                     # no world state or random stream touched
            st = se.staff
            new = free_coach(st)
            st.assign_coach(se, g, new, 'fee', (2028, 10), 'golfer', 'test set-up')
            self.gate(se, 10)
            self.gate(se, 11)
            self.assertEqual([(r['week'], r['reason'], r['coach']) for r in rows][-1], (10, 'coach_change', new.id))
            self.assertEqual(len(rows), 4)
            v = scouting.view(se, c, g.id)
            self.assertEqual(v['source'], 'coach')
            self.assertEqual([h['reason'] for h in v['categories'][0]['history']],
                             ['start', 'period', 'period', 'coach_change'])

    def test_growth_room_basis_and_evidence(self):
        with Copy() as s:
            g = started(s)
            se, c = s.season, s.season.career
            v = scouting.view(se, c, g.id)
            for x in v['categories']:                                  # one look: no trend, wider, said so
                gr = x['growth_room']
                self.assertIn(gr['label'], ('little', 'some', 'considerable'))
                self.assertNotIn('observed_trend', gr['basis'])
                self.assertIn('age_curve', gr['basis'])
                self.assertIn(gr['uncertainty'], ('moderate', 'wide'))
                self.assertIn('no observed trend yet', gr['explanation'])
                self.assertEqual(x['evidence'], {'observations': 1, 'looks_in_read': 1, 'span_weeks': 0,
                                                 'trend_available': False, 'trend_weeks': None})
                for h in HIDDEN:
                    self.assertNotIn(h, gr['explanation'].lower())
            for w in (5, 9, 13, 17, 21, 25, 29, 33):                   # (test: looks over 32 weeks)
                scouting.observe(se, c, g.id, 2028, w, 'period')
            v = scouting.view(se, c, g.id)
            o = c.observations[g.id][-1]
            for x in v['categories']:
                e = o['estimates'][x['category']]
                self.assertTrue(x['evidence']['trend_available'])
                self.assertEqual(x['evidence']['trend_weeks'], 32)
                self.assertEqual(x['evidence']['looks_in_read'], 3)
                self.assertIn('observed_trend', x['growth_room']['basis'])
                self.assertEqual(x['growth_room']['label'],
                                 next(n for n, bar in scouting.ROOM if e['gain'] <= bar))
                self.assertEqual(x['confidence'], 'medium')

    def test_growth_room_is_the_judges_projection_not_grade_minus_level(self):
        """The room follows the judge's projected gain (age curve, observed trend, their persistent error); a read
        recorded before this was kept says 'unknown' instead of guessing."""
        with Copy() as s:
            g = started(s)
            se, c = s.season, s.season.career
            e = c.observations[g.id][0]['estimates']
            for cat, x in e.items():
                gr = scouting.growth_room(x, 'self')
                self.assertEqual(gr['label'], next(n for n, bar in scouting.ROOM if x['gain'] <= bar))
            old = {k: {kk: vv for kk, vv in x.items() if kk not in ('gain', 'spread', 'looks', 'trend_weeks')}
                   for k, x in e.items()}                              # a read recorded by an earlier build
            self.assertEqual(scouting.growth_room(old['putting'], 'self')['label'], 'unknown')

    def test_same_rules_whoever_controls(self):
        """The read of a golfer depends on the looks and the judge, not on who controls them: the same looks of an AI
        golfer, kept on another career record, give the same read."""
        with Copy() as s:
            g = started(s)
            se, c = s.season, s.season.career
            other = next(x for x in se.active_golfers() if x.id != g.id and x.lifestyle != 'retired')
            c2 = CA.Career(other.id, 2028, 1, {'rule': 'test'})
            for car in (c, c2):
                for w in (1, 5, 33):
                    scouting.observe(se, car, other.id, 2028, w, 'period')
            self.assertEqual(scouting.view(se, c, other.id), scouting.view(se, c2, other.id))


if __name__ == '__main__':
    unittest.main()
