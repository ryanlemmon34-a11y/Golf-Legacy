"""World calendar and major-qualification rules.

Run from the project folder:  python -m unittest discover -s tests -v
"""
from __future__ import annotations

import sys
import unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from golfsim import qualification as Q                                  # noqa: E402
from golfsim.calendar import DAYS, MAJOR_WEEKS, MAJORS, WorldCalendar   # noqa: E402

CAL = WorldCalendar()


class CalendarTests(unittest.TestCase):
    def test_majors_fixed_and_exclusive_at_the_top(self):
        """A major owns its week at the top level only: no Premier Tour event, but lower tours, college,
        amateur and club-professional golf go on."""
        self.assertEqual({w: sid for w, (sid, _) in MAJORS.items()},
                         {18: 'TOUR_MASTERS', 24: 'PREMIER_TOUR_CHAMPIONSHIP', 25: 'USA_OPEN', 30: 'BRITANNIA_OPEN'})
        for seed in range(12):
            cal = WorldCalendar(seed)
            for year in (2027, 2031):
                for w in MAJOR_WEEKS:
                    week = [e for e in cal.editions(year) if e.week == w]
                    self.assertEqual([e.series.series_id for e in week if e.series.kind == 'major'], [MAJORS[w][0]])
                    self.assertFalse([e for e in week if e.series.tier == 1], f'seed {seed} week {w}')
                    self.assertGreaterEqual(len({e.series.tier for e in week} & {2, 3, 4, 5, 6, 8}), 2, f'seed {seed} week {w}')

    def test_calendar_validates_for_many_worlds(self):
        for seed in range(25):
            self.assertEqual(WorldCalendar(seed).validate(2027 + seed % 7), [], f'seed {seed}')

    def test_premier_structure(self):
        prem = [s for s in CAL.series if s.tier == 1]
        self.assertEqual(len(prem), 36)
        cls = Counter('standard' if s.category == 'national_open' else s.category for s in prem)
        self.assertEqual(cls, Counter(flagship=8, standard=20, opportunity=8))
        for w in (19, 26, 31):          # weeks straight after majors
            self.assertTrue(any(s.week == w and s.category == 'opportunity' for s in prem))
        for tour in ('PT_AMERICAS', 'PT_EUROPE', 'PT_ASIA_PACIFIC'):
            weeks = [s.week for s in prem if s.tour == tour]
            self.assertEqual(len(weeks), len(set(weeks)), f'{tour} double-booked')

    def test_every_level_and_length_exists(self):
        tiers = Counter(s.tier for s in CAL.series)
        self.assertTrue(all(tiers[t] for t in range(8)))
        amateur_lengths = {s.holes for s in CAL.series if s.kind == 'amateur'}
        self.assertTrue({18, 36, 54, 72} <= amateur_lengths)
        self.assertTrue(any(s.match_play for s in CAL.series))

    def test_series_are_stable_across_years(self):
        a = {e.series.series_id: (e.week, e.series.holes) for e in CAL.editions(2027)}
        b = {e.series.series_id: (e.week, e.series.holes) for e in CAL.editions(2041)}
        self.assertEqual(a, b)
        masters = {e.city for y in range(2027, 2040) for e in CAL.editions(y) if e.series.series_id == 'TOUR_MASTERS'}
        self.assertEqual(masters, {'Athens, Georgia'})
        brit = {e.city for y in range(2027, 2040) for e in CAL.editions(y) if e.series.series_id == 'BRITANNIA_OPEN'}
        self.assertGreater(len(brit), 4)

    def test_qualifying_stages_run_before_their_targets(self):
        w = {s.series_id: s.week for s in CAL.series}
        for local in ('USA_OPEN_LOCAL_W19', 'USA_OPEN_LOCAL_W20', 'USA_OPEN_LOCAL_W21'):
            self.assertLess(w[local], w['USA_OPEN_FINAL_INTL'])
        self.assertLess(w['USA_OPEN_FINAL'], w['USA_OPEN'])
        self.assertLess(w['BRITANNIA_REGIONAL_W27'], w['BRITANNIA_FINAL'])
        self.assertLess(w['BRITANNIA_FINAL'], w['BRITANNIA_OPEN'])
        self.assertLess(w['CLUB_PRO_CHAMPIONSHIP'], w['PREMIER_TOUR_CHAMPIONSHIP'])
        self.assertLess(w['BRITANNIA_AMATEUR'], w['USA_OPEN'])
        for route in Q.RULES['BRITANNIA_OPEN']:
            if route.code.startswith('BQ_'):
                sid = route.code[3:]
                self.assertIn(sid, w)

    def test_rules_only_reference_real_series(self):
        for sid in Q.REFERENCED_SERIES:
            self.assertIn(sid, CAL.by_id, sid)

    def test_monday_qualifier_and_weekend_event_can_share_a_week(self):
        self.assertFalse(DAYS['Mon'] & DAYS['Thu-Sun'])
        self.assertTrue(DAYS['Mon-Sun'] & DAYS['Thu-Sun'])


def make_ctx(n=400):
    ctx = Q.QualificationContext.from_calendar(CAL)
    for i in range(1, n + 1):
        ctx.people[i] = Q.Person(i, f'G{i}', 'pro', 30, 'USA' if i % 3 else 'England')
    ctx.world_rankings[(2026, 52)] = list(range(1, n + 1))
    ctx.world_rankings[(2027, 16)] = list(range(1, n + 1))
    ctx.world_rankings[(2027, 21)] = list(range(1, n + 1))
    ctx.world_rankings[(2027, 23)] = list(range(1, n + 1))
    ctx.world_rankings[(2027, 26)] = list(range(1, n + 1))
    return ctx


class QualificationTests(unittest.TestCase):
    def test_masters_is_invitation_only_with_real_categories(self):
        ctx = make_ctx()
        ctx.people[900] = Q.Person(900, 'Old Champ', 'pro', 58)
        ctx.add_result('TOUR_MASTERS', 1995, [(900, 1)])                 # lifetime exemption
        ctx.people[901] = Q.Person(901, 'Amateur Champ', 'amateur', 21)
        ctx.add_result('USA_AMATEUR', 2026, [(901, 1), (902, 2)])
        ctx.people[902] = Q.Person(902, 'Runner-up who turned pro', 'pro', 22)
        ctx.people[903] = Q.Person(903, 'Players winner', 'pro', 33)
        ctx.add_result('PT_PREMIER_PLAYERS_CHAMPIONSHIP', 2027, [(903, 1)])
        ctx.people[904] = Q.Person(904, 'Opportunity-event winner', 'pro', 33)
        ctx.add_result('PT_GULF_COAST_CLASSIC', 2026, [(904, 1)])          # opposite-field style: no invite
        ctx.people[905] = Q.Person(905, 'Future USA Open champion', 'pro', 27)
        ctx.add_result('USA_OPEN', 2027, [(905, 1)])                       # played AFTER the Masters
        f = Q.build_field('TOUR_MASTERS', 2027, ctx)
        ids = set(f.ids())
        self.assertIn(900, ids)
        self.assertIn(901, ids)
        self.assertNotIn(902, ids)            # amateur exemption lost on turning pro
        self.assertIn(903, ids)
        self.assertNotIn(904, ids)
        self.assertNotIn(905, ids)            # no hindsight
        self.assertTrue(set(range(1, 51)) <= ids)
        invites = [e.golfer_id for e in f.entries if e.primary == 'M15']
        self.assertEqual(len(invites), 4)                                   # special international invitations
        self.assertTrue(all(ctx.people[g].country != 'USA' and g > 50 for g in invites))
        self.assertNotIn(52, ids)                                           # a US player ranked 52 is not invited
        self.assertLess(len(f.entries), 100)  # never filled up to a quota
        self.assertEqual(next(e for e in f.entries if e.golfer_id == 900).primary, 'M1')

    def test_entry_sources_record_every_category(self):
        ctx = make_ctx()
        ctx.add_result('USA_OPEN', 2026, [(1, 1)])
        f = Q.build_field('TOUR_MASTERS', 2027, ctx)
        e = next(e for e in f.entries if e.golfer_id == 1)
        self.assertEqual(e.primary, 'M2')
        self.assertIn('M13', e.sources)
        self.assertIn('M14', e.sources)

    def test_premier_championship_club_pros_and_fill(self):
        ctx = make_ctx()
        clubs = list(range(1000, 1030))
        for g in clubs:
            ctx.people[g] = Q.Person(g, f'Club pro {g}', 'club_pro', 40)
        ctx.add_result('CLUB_PRO_CHAMPIONSHIP', 2027, [(g, i + 1) for i, g in enumerate(clubs)])
        ctx.standings[('PT_AMERICAS', 2026)] = list(range(1, 300))
        f = Q.build_field('PREMIER_TOUR_CHAMPIONSHIP', 2027, ctx)
        self.assertEqual(len(f.entries), 156)
        self.assertEqual(f.route_counts.get('P5'), 20)
        self.assertTrue(set(clubs[:20]) <= set(f.ids()))
        self.assertFalse(set(clubs[20:]) & set(f.ids()))

    def test_usa_open_qualifying_spots_pass_down_past_exempt_players(self):
        ctx = make_ctx()
        # Site 0 of the international final qualifier: world No.1 (already exempt) finishes first.
        site = [(1, 1)] + [(500 + i, i + 2) for i in range(20)]
        for i in range(20):
            ctx.people[500 + i] = Q.Person(500 + i, f'Q{i}', 'pro', 25)
        ctx.add_result('USA_OPEN_FINAL_INTL', 2027, site, site=0)
        f = Q.build_field('USA_OPEN', 2027, ctx)
        qualifiers = [e.golfer_id for e in f.entries if e.primary == 'UQ']
        self.assertEqual(qualifiers, [500, 501, 502, 503, 504, 505])        # 6 spots at that site
        self.assertEqual(next(e for e in f.entries if e.golfer_id == 1).primary, 'U9')
        self.assertEqual(len(f.entries), 156)                                # alternates fill the field
        self.assertIn(506, f.ids())                                          # first alternate from the site

    def test_britannia_age_limit_and_qualifying_series(self):
        ctx = make_ctx()
        ctx.people[910] = Q.Person(910, 'Champion aged 61', 'pro', 61)
        ctx.add_result('BRITANNIA_OPEN', 2001, [(910, 1)])
        ctx.people[911] = Q.Person(911, 'Champion aged 45', 'pro', 45)
        ctx.add_result('BRITANNIA_OPEN', 2010, [(911, 1)])
        # Scotland Open (week 29): the top 3 not already exempt qualify.
        for i in range(10):
            ctx.people[700 + i] = Q.Person(700 + i, f'S{i}', 'pro', 28)
        ctx.add_result('PT_SCOTLAND_OPEN', 2027, [(2, 1)] + [(700 + i, i + 2) for i in range(10)])
        ctx.people[920] = Q.Person(920, 'Top amateur', 'amateur', 20)
        ctx.amateur_rankings[(2027, 26)] = [920]
        f = Q.build_field('BRITANNIA_OPEN', 2027, ctx)
        ids = f.ids()
        self.assertNotIn(910, ids)
        self.assertIn(911, ids)
        self.assertIn(920, ids)
        self.assertEqual([e.golfer_id for e in f.entries if e.primary == 'BQ_PT_SCOTLAND_OPEN'], [700, 701, 702])
        self.assertEqual(len(ids), 156)

    def test_exempt_club_pro_does_not_use_a_qualifying_place(self):
        ctx = make_ctx()
        ctx.people[5] = Q.Person(5, 'Club pro in the world top 100', 'club_pro', 38)
        clubs = list(range(1000, 1030))
        for g in clubs:
            ctx.people[g] = Q.Person(g, f'Club pro {g}', 'club_pro', 40)
        ctx.add_result('CLUB_PRO_CHAMPIONSHIP', 2027, [(5, 1)] + [(g, i + 2) for i, g in enumerate(clubs)])
        ctx.standings[('PT_AMERICAS', 2026)] = list(range(1, 300))
        f = Q.build_field('PREMIER_TOUR_CHAMPIONSHIP', 2027, ctx)
        self.assertNotEqual(next(e for e in f.entries if e.golfer_id == 5).primary, 'P5')
        self.assertEqual([e.golfer_id for e in f.entries if e.primary == 'P5'], clubs[:20])
        self.assertNotIn(clubs[20], f.ids())

    def test_promoted_alternates_leave_the_alternate_list(self):
        ctx = make_ctx()
        site = [(500 + i, i + 1) for i in range(30)]
        for i in range(30):
            ctx.people[500 + i] = Q.Person(500 + i, f'Q{i}', 'pro', 25)
        ctx.add_result('USA_OPEN_FINAL_INTL', 2027, site, site=0)
        f = Q.build_field('USA_OPEN', 2027, ctx)
        self.assertIn(506, f.ids())                       # first alternate promoted into the field
        self.assertFalse(set(f.alternates) & set(f.ids()))
        self.assertEqual(len(f.alternates), len(set(f.alternates)))
        self.assertEqual(len(f.entries), 156)


if __name__ == '__main__':
    unittest.main()
