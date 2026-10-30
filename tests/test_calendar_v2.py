"""The reference calendar (v2) and its qualification rules (roadmap v14, "Calendar and qualification rework"),
and the classic calendar (v1) kept exactly as it was for the worlds that use it.

Pure calendar fixtures first (anchors and counts, feeder order, venues and climate, Q-School), then hand-built
qualification fixtures (cut-off snapshots, year routing, duplicate routes, amateur status, ties, travel), then
one small deterministic world played for a season under v2 (and reopened).

Run from the project folder:  python -m unittest tests.test_calendar_v2 -v
"""
from __future__ import annotations

import dataclasses
import hashlib
import shutil
import sys
import tempfile
import unittest
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from golfsim import qualification as Q                                    # noqa: E402
from golfsim import schedule as SCH                                       # noqa: E402
from golfsim.calendar import TOUR_BY_KEY, WorldCalendar                   # noqa: E402
from golfsim.geography import CITY_BY_NAME, season_weeks                  # noqa: E402

# The classic calendar's series, as the engine built them before calendar versions existed (sha1 of every
# series' fields): v1 must never change
V1_SERIES_SHA1 = '2984f53a80d5c50ffe540a26d491aa1a19c8a4bc'
MAJORS = ('TOUR_MASTERS', 'PREMIER_TOUR_CHAMPIONSHIP', 'USA_OPEN', 'BRITANNIA_OPEN')


class ReferenceCalendar(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cal = WorldCalendar(2027, 'v2')
        cls.old = WorldCalendar(2027, 'v1')
        cls.by = cls.cal.by_id

    def test_the_classic_calendar_is_unchanged(self):
        h = hashlib.sha1(repr([dataclasses.astuple(s) for s in self.old.series]).encode()).hexdigest()
        self.assertEqual(h, V1_SERIES_SHA1)
        self.assertEqual(self.old.validate(), [])
        self.assertEqual({sid: self.old.by_id[sid].week for sid in MAJORS},
                         {'TOUR_MASTERS': 18, 'PREMIER_TOUR_CHAMPIONSHIP': 24, 'USA_OPEN': 25, 'BRITANNIA_OPEN': 30})

    def test_anchors_and_counts(self):
        self.assertEqual(self.cal.validate(), [])
        self.assertEqual([self.by[m].week for m in MAJORS], [15, 20, 25, 30])
        weeks = [self.by[m].week for m in MAJORS]
        self.assertEqual({b - a for a, b in zip(weeks, weeks[1:])}, {5})
        prem = [s for s in self.cal.series if s.tier == 1]
        self.assertEqual(len(prem), 36)
        cls = Counter('standard' if s.category == 'national_open' else s.category for s in prem)
        self.assertEqual(cls, Counter(flagship=8, standard=20, opportunity=8))
        self.assertFalse([s.series_id for s in prem if s.week in (15, 20, 25, 30)])
        for w in (16, 21, 26, 31):                                          # opportunity the week after each major
            self.assertTrue(any(s.week == w and s.category == 'opportunity' for s in prem), w)
        self.assertEqual({s.name: s.week for s in prem if s.name in ('Gulf Coast Classic', 'Nordic Masters',
                                                                      'Great Lakes Open', 'Netherlands Open')},
                         {'Gulf Coast Classic': 16, 'Nordic Masters': 21, 'Great Lakes Open': 26, 'Netherlands Open': 31})
        for name, week in SCH.V2.premier_weeks.items():                    # every Premier event at its reference week
            self.assertEqual(next(s.week for s in prem if s.name == name), week, name)
        flag = Counter(s.week for s in prem if s.category == 'flagship')
        self.assertEqual(max(flag.values()), 1)                            # no flagship collision

    def test_feeders_finish_before_their_cutoffs_and_fields(self):
        w = lambda sid: self.by[sid].week
        self.assertLess(w('CLUB_PRO_SECTIONALS'), w('CLUB_PRO_CHAMPIONSHIP'))
        self.assertEqual((w('CLUB_PRO_SECTIONALS'), w('CLUB_PRO_CHAMPIONSHIP')), (12, 18))
        self.assertLess(w('CLUB_PRO_CHAMPIONSHIP'), w('PREMIER_TOUR_CHAMPIONSHIP'))
        self.assertEqual([w(x[0]) for x in SCH.V2.usa_local], [17, 19, 21])
        self.assertEqual((w('USA_OPEN_FINAL_INTL'), w('USA_OPEN_FINAL')), (22, 24))
        self.assertEqual([w(x[0]) for x in SCH.V2.britannia_regional], [26, 27])
        self.assertEqual(w('BRITANNIA_FINAL'), 28)
        self.assertEqual(self.by['BRITANNIA_FINAL'].days, 'Tue')
        self.assertEqual(w('PT_SCOTLAND_OPEN'), 29)
        c = SCH.V2.cutoffs
        self.assertEqual((c['masters_ranking'], c['masters_wins_through']), (13, 14))
        self.assertEqual((c['pga_points'], c['pga_wins_through']), (18, 19))
        self.assertEqual((c['usa_ranking_1'], c['usa_ranking_2']), (20, 24))
        self.assertEqual((c['britannia_ranking'], c['britannia_fill'], c['amateur_award']), (21, 29, 33))
        for major, cut in (('TOUR_MASTERS', c['masters_wins_through']), ('PREMIER_TOUR_CHAMPIONSHIP', c['pga_wins_through']),
                           ('USA_OPEN', c['usa_ranking_2']), ('BRITANNIA_OPEN', c['britannia_fill'])):
            self.assertLess(cut, w(major))                                  # the last input is before the field
        for sid, off, *_ in [(x[0], x[3]) for x in Q.BRITANNIA_SERIES]:  # qualifying series: before the Open
            if off == 0:
                self.assertLess(w(sid), w('BRITANNIA_OPEN'), sid)
        self.assertLess(w('USA_AMATEUR_QUALIFYING'), w('USA_AMATEUR'))
        self.assertEqual((w('BRITANNIA_AMATEUR'), w('COLLEGE_REGIONAL_1'), w('COLLEGE_NATIONAL_CHAMPIONSHIP')), (26, 21, 22))

    def test_venues_climate_and_lower_tours(self):
        for year in (2027, 2031, 2044):
            for e in self.cal.editions(year):
                self.assertIn(e.week, season_weeks(CITY_BY_NAME[e.city]), e.event_id)
        texas = self.by['PT_TEXAS_OPEN']
        self.assertTrue(texas.cities and all(c.endswith(', Texas') for c in texas.cities))
        self.assertTrue(set(self.by['PT_GULF_COAST_CLASSIC'].cities) <= set(SCH.V2.city_pools['Gulf Coast Classic']))
        for w in (15, 20, 25, 30):                                          # the rest of the world plays on
            tiers = {s.tier for s in self.cal.series if s.week == w}
            self.assertTrue({2, 4, 6} <= tiers, (w, tiers))
        self.assertEqual(len(self.cal.series), len(self.old.series))      # the whole universe, every event
        self.assertEqual(Counter(s.tour for s in self.cal.series), Counter(s.tour for s in self.old.series))

    def test_q_school_weeks_and_standings(self):
        self.assertEqual(self.by['ASIA_QSCHOOL_FINAL'].week, 51)
        self.assertIn('ASIA_QSCHOOL_FINAL', SCH.V2.qschool_next_season)
        self.assertEqual({sid: self.by[sid].week for sid in ('PT_QSCHOOL_PRE', 'PT_QSCHOOL_FIRST', 'PT_QSCHOOL_SECOND',
                                                             'PT_QSCHOOL_FINAL', 'EU_QSCHOOL_FIRST', 'EU_QSCHOOL_SECOND',
                                                             'EU_QSCHOOL_FINAL', 'JP_QSCHOOL_FINAL')},
                         {'PT_QSCHOOL_PRE': 40, 'PT_QSCHOOL_FIRST': 42, 'PT_QSCHOOL_SECOND': 46, 'PT_QSCHOOL_FINAL': 50,
                          'EU_QSCHOOL_FIRST': 37, 'EU_QSCHOOL_SECOND': 44, 'EU_QSCHOOL_FINAL': 48, 'JP_QSCHOOL_FINAL': 48})
        champ = {s.tour: s.week for s in self.cal.series if s.category == 'circuit_championship'}
        self.assertLess(champ['CH_ASIA'], 51)                               # each championship before its school
        self.assertLess(champ['CH_JAPAN'], 48)
        self.assertTrue(all(w <= 48 for t, w in champ.items() if TOUR_BY_KEY[t].tier in (2, 3, 4)))

    def test_stable_identities(self):
        self.assertEqual(SCH.canonical('USA_OPEN_LOCAL_W19'), 'USA_OPEN_LOCAL_1')
        old_ids = {SCH.canonical(s.series_id) for s in self.old.series}
        self.assertEqual(old_ids, {s.series_id for s in self.cal.series})


def ctx_for(version, people):
    cal = WorldCalendar(2027, version)
    ctx = Q.QualificationContext.from_calendar(cal)
    for gid, status in people.items():
        ctx.people[gid] = Q.Person(gid, f'G{gid}', status=status)
    return ctx


class QualificationTruth(unittest.TestCase):
    def test_future_snapshots_fail_and_published_ones_are_exact(self):
        ctx = ctx_for('v2', {i: 'pro' for i in range(1, 80)})
        ctx.world_rankings[(2030, 12)] = list(range(1, 80))
        ctx.world_rankings[(2030, 13)] = list(range(79, 0, -1))
        early = ctx.as_of(2030, 13)                                         # week 13 not over yet
        with self.assertRaises(Q.FutureSnapshot):
            early.snapshot(2030, 13)
        m14 = next(r for r in Q.rules_for('v2')['TOUR_MASTERS'] if r.code == 'M14')
        with self.assertRaises(Q.FutureSnapshot):
            m14.select(early, 2030)
        self.assertEqual(m14.select(ctx.as_of(2030, 14), 2030), list(range(79, 29, -1)))   # exactly week 13's
        self.assertEqual(ctx.as_of(2030, 14).snapshot(2027, 13), [])        # never recorded: nobody
        old = ctx_for('v1', {1: 'pro'})                                     # v1 still reads the latest list
        old.world_rankings[(2030, 12)] = [1]
        self.assertEqual(Q.ranking_top(50, 16)(old.as_of(2030, 18), 2030), [1])

    def test_a_projected_ranking_never_removes_a_local_attempt(self):
        ctx = ctx_for('v2', {i: 'pro' for i in range(1, 100)})
        ctx.world_rankings[(2030, 16)] = list(range(1, 100))               # projected top 60 already
        exempt, pending = Q.earned_exemptions('USA_OPEN', 2030, ctx.as_of(2030, 17))
        self.assertIn('U9', pending)
        self.assertIn('U10', pending)
        self.assertFalse(exempt)                                            # nobody exempt yet: everyone may try
        ctx.world_rankings[(2030, 20)] = list(range(1, 100))
        exempt, pending = Q.earned_exemptions('USA_OPEN', 2030, ctx.as_of(2030, 22))
        self.assertEqual(sorted(exempt), list(range(1, 61)))               # published after week 20: earned
        self.assertEqual(pending, ['U10'])

    def test_britannia_amateur_feeds_the_editions_its_date_allows(self):
        ctx = ctx_for('v2', {7: 'amateur', 8: 'amateur', 9: 'pro'})
        ctx.add_result('BRITANNIA_AMATEUR', 2030, [(7, 1), (8, 2)], week=26)
        for wk in (52,):
            ctx.world_rankings[(2029, wk)] = []
        for major, year, want in (('USA_OPEN', 2030, False), ('BRITANNIA_OPEN', 2030, True),
                                  ('USA_OPEN', 2031, True), ('TOUR_MASTERS', 2031, True)):
            for wk in range(1, 30):
                ctx.world_rankings.setdefault((year, wk), [])
                ctx.standings.setdefault(('PT_AMERICAS', year, wk), [])
            ids = Q.build_field(major, year, ctx).ids()
            self.assertEqual(7 in ids, want, (major, year))
        classic = ctx_for('v1', {7: 'amateur'})                             # (v1: same-season USA Open, week 23)
        classic.add_result('BRITANNIA_AMATEUR', 2030, [(7, 1)], week=23)
        self.assertIn(7, Q.build_field('USA_OPEN', 2030, classic).ids())

    def test_champion_and_runner_up_are_separate_and_status_is_checked(self):
        ctx = ctx_for('v2', {1: 'amateur', 2: 'amateur'})
        ctx.add_result('USA_AMATEUR', 2030, [(1, 1), (2, 2)], week=33)
        f = Q.build_field('TOUR_MASTERS', 2031, ctx)
        by = {e.golfer_id: e for e in f.entries}
        self.assertEqual((by[1].primary, by[2].primary), ('M4', 'M4R'))
        ctx.people[2].status = 'pro'                                         # turned professional before it
        self.assertNotIn(2, Q.build_field('TOUR_MASTERS', 2031, ctx).ids())
        self.assertIn(1, Q.build_field('TOUR_MASTERS', 2031, ctx).ids())

    def test_duplicate_routes_take_one_place(self):
        ctx = ctx_for('v2', {1: 'amateur'})
        ctx.add_result('USA_AMATEUR', 2030, [(1, 1)], week=33)
        ctx.add_result('USA_MID_AMATEUR', 2030, [(1, 1)], week=38)
        ctx.add_result('ASIA_PACIFIC_AMATEUR', 2030, [(1, 1)], week=43)
        f = Q.build_field('TOUR_MASTERS', 2031, ctx)
        self.assertEqual(f.ids().count(1), 1)
        e = f.entries[f.ids().index(1)]
        self.assertEqual(e.sources, ['M4', 'M6', 'M8'])                    # every route recorded, one place

    def test_the_annual_amateur_award_and_the_first_season(self):
        ctx = ctx_for('v2', {5: 'amateur'})
        self.assertEqual(Q.amateur_award()(ctx, 2028), [])                 # no award before the world: nobody
        ctx.awards[('amateur_award', 2030)] = 5
        self.assertEqual(Q.amateur_award()(ctx.as_of(2031, 1), 2031), [5])
        self.assertEqual(Q.amateur_award()(ctx.as_of(2030, 33), 2031), [])  # named only after week 33
        self.assertEqual(Q.amateur_award()(ctx.as_of(2030, 34), 2031), [5])
        ua = {r.code: r for r in Q.rules_for('v2')['USA_OPEN']}['UA']
        self.assertTrue(ua.amateur_only)
        self.assertNotIn('UA', {r.code for r in Q.rules_for('v2')['TOUR_MASTERS']})   # not a Masters route
        places = Q.secured_places(ctx, 2030)
        self.assertEqual(sorted(m for m, _, cond in places[5]), ['BRITANNIA_OPEN', 'USA_OPEN'])
        self.assertTrue(all(cond == 'if still an amateur' for _, _, cond in places[5]))

    def test_the_last_club_professional_place(self):
        ctx = ctx_for('v2', {i: 'club_pro' for i in range(100, 130)})
        finish = [(100 + i, i + 1 if i < 18 else 19) for i in range(25)]   # 19th place tied five ways
        ctx.add_result('CLUB_PRO_CHAMPIONSHIP', 2030, finish, week=18)
        for wk in range(1, 20):
            ctx.world_rankings[(2030, wk)] = []
            ctx.standings[('PT_AMERICAS', 2030, wk)] = []
        f = Q.build_field('PREMIER_TOUR_CHAMPIONSHIP', 2030, ctx)
        p5 = [e.golfer_id for e in f.entries if e.primary == 'P5']
        self.assertEqual(p5, [100 + i for i in range(20)])                 # exactly 20, in the recorded order

    def test_masters_winner_window_follows_the_actual_prior_edition(self):
        ctx = ctx_for('v2', {1: 'pro', 2: 'pro', 3: 'pro'})
        ctx.add_result('TOUR_MASTERS', 2030, [(9, 1)], week=15)
        ctx.add_result('PT_TEXAS_OPEN', 2030, [(1, 1)], week=14)           # before last year's Masters
        ctx.add_result('PT_GULF_COAST_CLASSIC', 2030, [(2, 1)], week=16)    # after it: counts
        ctx.add_result('PT_TEXAS_OPEN', 2031, [(3, 1)], week=14)            # last eligible week
        sel = Q.winners_since_major(Q._is_premier, 'TOUR_MASTERS', 14)
        self.assertEqual(sel(ctx.as_of(2031, 15), 2031), [2, 3])

    def test_rights_evidence_names_the_source(self):
        ctx = ctx_for('v2', {1: 'amateur'})
        ctx.add_result('USA_AMATEUR', 2030, [(1, 1)], week=33)
        m4 = {r.code: r for r in Q.rules_for('v2')['TOUR_MASTERS']}['M4']
        self.assertEqual(Q.evidence(m4, 1, 2031, ctx), [('2030:USA_AMATEUR (position 1)', (2030, 33))])


class Travel(unittest.TestCase):
    """Day-level availability (v2): overlapping days never; a trip needs time between events in one week."""

    def season(self):
        from golfsim.season import Season
        s = Season.__new__(Season)
        s.cal = WorldCalendar(2027, 'v2')
        s._week_where = defaultdict(list)
        return s

    def test_monday_to_thursday_needs_time_to_travel(self):
        s = self.season()
        s._week_where[1].append(({0}, 'England'))                           # a Monday qualifier in England
        self.assertTrue(s.can_travel(1, {3, 4, 5, 6}, ('USA',)))            # Thursday start in the USA: two days
        s._week_where[2].append(({1}, 'England'))                           # a Tuesday final in England
        self.assertFalse(s.can_travel(2, {3, 4, 5, 6}, ('USA',)))           # one day: not enough across the ocean
        self.assertTrue(s.can_travel(2, {3, 4, 5, 6}, ('Scotland',)))       # nearby: one day is enough
        s._week_where[3].append(({0}, 'USA'))                               # local qualifier Monday
        self.assertFalse(s.can_travel(3, {0, 1, 2}, ('USA',)))              # college regional Mon-Wed: overlap
        self.assertTrue(s.can_travel(3, {3, 4, 5, 6}, ('USA',)))            # same country: no gap needed


class ReferenceSeason(unittest.TestCase):
    """A small deterministic world: one season and a week under v2, reopened."""

    @classmethod
    def setUpClass(cls):
        from golfsim.population import generate_world
        from golfsim.session import Session
        cls.tmp = Path(tempfile.mkdtemp())
        s = Session.create(cls.tmp / 'w', seed=79, workers=1, world=generate_world(seed=79, scale=0.03))
        s.advance(53)
        cls.version = s.season.calendar_version
        se = s.season
        cls.results = {eid: (r.week, [list(site) for site in r.finish]) for eid, r in se.results.items()}
        cls.stage = {k: v for k, v in se.stage_log.items() if isinstance(k, tuple) and len(k) == 2
                     and k[1] in ('USA_OPEN', 'BRITANNIA_OPEN')}
        cls.days = {eid: se.cal.by_id[eid.split(':', 1)[1]].day_set for eid in cls.results}
        cls.country = {}
        for eid in cls.results:
            vs = se.lib.venues(int(eid.split(':')[0]))[eid]
            cls.country[eid] = [CITY_BY_NAME[v.city].country for v in vs]
        cls.awards = dict(se.ctx.awards)
        cls.rights = {y: {m: dict(b) for m, b in book.items()} for y, book in se.major_rights.items()}
        s.close()
        cls.s2 = Session.open(cls.tmp / 'w', workers=1)

    @classmethod
    def tearDownClass(cls):
        cls.s2.close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_new_worlds_play_the_reference_calendar(self):
        self.assertEqual(self.version, 'v2')
        for sid, week in zip(MAJORS, (15, 20, 25, 30)):
            self.assertEqual(self.results[f'2027:{sid}'][0], week)
        self.assertEqual(self.s2.season.calendar_version, 'v2')              # kept on reopening
        self.assertEqual(self.s2.season.cal.by_id['TOUR_MASTERS'].week, 15)

    def test_one_attempt_and_exemptions_rechecked(self):
        for (year, major), st in self.stage.items():
            waves = [x[0] for x in (SCH.V2.usa_local if major == 'USA_OPEN' else SCH.V2.britannia_regional)]
            played = Counter(gid for sid in waves for site in self.results.get(f'{year}:{sid}', (0, []))[1]
                             for gid, _, _ in site)
            self.assertTrue(all(n == 1 for n in played.values()), major)   # nobody tried twice
            for gid, n in played.items():
                self.assertEqual(st['choice'][gid], next(sid for sid in waves if any(
                    g == gid for site in self.results.get(f'{year}:{sid}', (0, []))[1] for g, _, _ in site)))
            final = 'USA_OPEN_FINAL' if major == 'USA_OPEN' else 'BRITANNIA_FINAL'
            entered = {g for site in self.results.get(f'{year}:{final}', (0, []))[1] for g, _, _ in site}
            self.assertFalse(entered & set(st['exempt']))                   # the exempt never use a place
            intl = {g for site in self.results.get(f'{year}:USA_OPEN_FINAL_INTL', (0, []))[1] for g, _, _ in site}
            self.assertFalse(intl & set(played))                             # local qualifiers never sent abroad

    def test_no_overlapping_starts_or_impossible_trips(self):
        by_week = defaultdict(list)
        for eid, (week, sites) in self.results.items():
            for k, site in enumerate(sites):
                for gid, _, _ in site:
                    by_week[(eid.split(':')[0], week, gid)].append(
                        (self.days[eid], self.country[eid][min(k, len(self.country[eid]) - 1)]))
        from golfsim.season import Season
        from golfsim.geography import COUNTRIES
        for (year, week, gid), starts in by_week.items():
            for i, (d1, c1) in enumerate(starts):
                for d2, c2 in starts[i + 1:]:
                    self.assertFalse(d1 & d2, (week, gid))
                    gap = (min(d2) - max(d1) - 1) if min(d2) > max(d1) else (min(d1) - max(d2) - 1)
                    need = 0 if c1 == c2 else 1 if COUNTRIES[c1].region == COUNTRIES[c2].region else 2
                    self.assertGreaterEqual(gap, need, (week, gid, c1, c2))

    def test_award_and_rights_ledger(self):
        self.assertIn(('amateur_award', 2027), self.awards)
        gid = self.awards[('amateur_award', 2027)]
        if gid is not None:
            for major in ('USA_OPEN', 'BRITANNIA_OPEN'):
                r = self.rights[2028][major][gid]
                self.assertEqual(r['state'], 'conditional') if set(r['routes']) <= {'UA', 'B13'} else None
                self.assertTrue(any(c in r['routes'] for c in ('UA', 'B13')))
        for major in MAJORS:
            book = self.rights[2027][major]
            entered = {g for site in self.results[f'2027:{major}'][1] for g, _, _ in site}
            self.assertEqual({g for g, r in book.items() if r['result'] == 'entered'}, entered, major)
            self.assertTrue(all(r['result'] for r in book.values()), major)    # every place resolved
            for r in book.values():
                self.assertEqual(r['target'], f'2027:{major}')

    def test_the_season_file_records_its_calendar_and_cutoffs(self):
        from golfsim.archive import Archive
        with Archive(self.tmp / 'w' / 'archive') as a:
            d = a.year(2027)
            self.assertEqual(a.world.get('calendar'), 'v2')
        self.assertEqual(d['calendar']['version'], 'v2')
        weeks = {k: v['week'] for k, v in d['cutoffs'].items()}
        for k, w in (('masters_ranking', 13), ('pga_ranking', 18), ('usa_ranking_1', 20), ('usa_ranking_2', 24),
                     ('britannia_ranking', 21), ('britannia_fill', 29), ('year_end', 52)):
            self.assertEqual(weeks.get(k), w, k)
        self.assertTrue(d['major_rights'])
        self.assertTrue(d['next_major_rights'])
        if 2027 not in [int(e.split(':')[0]) for e in d.get('unheld', []) if 'ASIA_QSCHOOL' in e]:
            asia = next((e for e in d['events'] if e['id'] == '2027:ASIA_QSCHOOL_FINAL'), None)
            if asia is not None:
                self.assertEqual(asia['week'], 51)


class ClassicWorldsStayClassic(unittest.TestCase):
    def test_a_classic_world_keeps_its_calendar(self):
        from golfsim.population import generate_world
        from golfsim.session import Session
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        s = Session.create(tmp / 'w', seed=83, workers=1, world=generate_world(seed=83, scale=0.02), calendar='v1')
        s.advance(3)
        s.close()
        s = Session.open(tmp / 'w', workers=1)
        self.addCleanup(s.close)
        self.assertEqual(s.season.calendar_version, 'v1')
        self.assertEqual(s.season.cal.by_id['TOUR_MASTERS'].week, 18)
        self.assertEqual(s.season.ctx.version, 'v1')
        self.assertIs(Q.rules_for(s.season.ctx.version), Q.RULES)


if __name__ == '__main__':
    unittest.main()
