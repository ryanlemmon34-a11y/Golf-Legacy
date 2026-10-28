"""Competition access: major weeks, Premier playing rights, alternatives, local golf, circuit flagships.

Run from the project folder:  python -m unittest discover -s tests -v
"""
from __future__ import annotations

import random
import sys
import unittest
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from golfsim.calendar import (CIRCUIT_FLAGSHIP_ELSEWHERE, CIRCUIT_FLAGSHIPS, MAJOR_WEEKS, TOUR_BY_KEY,   # noqa: E402
                              local_allocation)
from golfsim.geography import COUNTRIES                                  # noqa: E402
from golfsim.population import generate_world                            # noqa: E402
from golfsim.season import ACCESS, FULL_STATUS, PREMIER_TOURS, PREMIER_VISITOR_SHARE, Season   # noqa: E402


def fresh(seed=2027):
    s = Season(generate_world(seed=seed), seed=seed, development=True, workers=2)
    s.refresh_people(2027)
    s.start_finances(2027)
    return s


def run_weeks(weeks, seed=2027):
    """A season started at week 17 (a planning week) through the Tour Masters week."""
    s = fresh(seed)
    eds = s.cal.editions(2027)
    for w in weeks:
        s.run_week(2027, w, [e for e in eds if e.week == w])
    s.close()
    return s


SEASON = run_weeks((17, 18))


class MajorWeekTests(unittest.TestCase):
    def test_lower_levels_play_in_a_major_week_and_no_one_plays_twice(self):
        s = SEASON
        week18 = [r for r in s.results.values() if r.week == 18]
        tiers = Counter(s.cal.by_id[r.series_id].tier for r in week18)
        self.assertEqual(tiers[0], 1)                                    # the Tour Masters
        self.assertEqual(tiers[1], 0)                                    # no Premier Tour event
        self.assertTrue(tiers[2] + tiers[3] + tiers[4] > 0 and tiers[6] > 0, tiers)
        masters = {gid for site in s.results['2027:TOUR_MASTERS'].finish for gid, _, _ in site}
        days = defaultdict(set)
        for r in week18:
            ser = s.cal.by_id[r.series_id]
            for site in r.finish:
                for gid, _, _ in site:
                    self.assertFalse(days[gid] & ser.day_set, (gid, r.event_id))
                    days[gid] |= ser.day_set
                    if r.series_id != 'TOUR_MASTERS':
                        self.assertNotIn(gid, masters)
        # Premier members who are not in the Masters can play elsewhere that week
        others = [gid for r in week18 if r.series_id != 'TOUR_MASTERS' for site in r.finish for gid, _, _ in site
                  if s.g[gid].tour in PREMIER_TOURS]
        self.assertTrue(others)


class PremierRightsTests(unittest.TestCase):
    def test_full_status_sized_to_the_smallest_ordinary_field(self):
        s = SEASON
        rights = Counter(r for r, _ in s.rights[2027].values())
        self.assertEqual(rights['full'] + rights['exempt'], FULL_STATUS)   # first season: seeded by ranking
        smallest = min(x.field for x in s.cal.series if x.tier == 1 and x.category in ('standard', 'opportunity'))
        self.assertLessEqual(FULL_STATUS, smallest)
        self.assertTrue(all(why for _, why in s.rights[2027].values()))

    def test_rights_from_last_season(self):
        s = fresh()
        pros = [g for g in s.world.golfers if g.tour in PREMIER_TOURS]
        m = s.money[('PREMIER', 2027)]
        for i, g in enumerate(pros):
            m[g.id] = 1e6 - i                                            # a money list in this order
        winner, grad = pros[250], pros[260]
        s.ctx.add_result('PT_TEXAS_OPEN', 2027, [(winner.id, 1)])
        s.card_reasons[2028] = {grad.id: 'top 25 on Challenger Tour Americas'}
        s.premier_rights(2028)
        r = s.rights[2028]
        self.assertEqual(r[pros[0].id][0], 'full')
        self.assertEqual(r[pros[FULL_STATUS - 1].id][0], 'full')
        self.assertEqual(r[pros[FULL_STATUS].id][0], 'conditional')
        self.assertEqual(r[winner.id], ('exempt', 'won the 2027 Texas Open'))
        self.assertEqual(r[grad.id][0], 'graduate')

    def test_priority_full_before_conditional_and_bounded_visitor_places(self):
        s = fresh()
        prem = next(x for x in s.cal.series if x.tier == 1 and x.category == 'standard' and x.tour == 'PT_AMERICAS')
        full = next(s.g[g] for g, (r, _) in s.rights[2027].items() if r == 'full' and s.g[g].tour == 'PT_EUROPE')
        cond = next(s.g[g] for g, (r, _) in s.rights[2027].items() if r == 'conditional' and s.g[g].tour == 'PT_AMERICAS')
        self.assertLess(s.priority(full, prem), s.priority(cond, prem))  # rights first, then home circuit
        ch = next(x for x in s.cal.series if x.tour == 'CH_AMERICAS' and x.category == 'regular')
        visitors = [g for g in s.world.golfers if g.tour in PREMIER_TOURS][:40]
        residents = [g for g in s.world.golfers if g.tour == 'CH_AMERICAS'][:ch.field]
        limits = s._limits(ch)
        self.assertEqual(limits[1], int(PREMIER_VISITOR_SHARE * ch.field))
        rows, c = [], [0, 0]
        import bisect
        for g in residents + visitors:
            bisect.insort(rows, (s.priority(g, ch), g.id))
            s._count(c, g.id, ch, 1)
            while len(rows) > ch.field or s._over(c, limits):
                s._bump(rows, ch, ch.field, c, limits)
        kept = Counter('visitor' if s.g[gid].tour in PREMIER_TOURS else 'resident' for _, gid in rows)
        self.assertEqual(kept['visitor'], limits[1])                      # a bounded share, not wholesale
        self.assertEqual(kept['resident'], ch.field - limits[1])

    def test_shut_out_premier_members_play_alternatives(self):
        s = SEASON
        alt = [x for gid, log in s.access_log[2027].items() if s.g[gid].tour in PREMIER_TOURS
               for x in log if x[1] == 'played: alternative']
        self.assertTrue(alt)
        routes = [r for rs in s.event_routes[2027].values() for r in rs.values()]
        self.assertIn('PREMIER MEMBER (visitor places)', routes)


class LocalGolfTests(unittest.TestCase):
    def test_every_golfing_country_has_local_amateur_and_club_pro_events(self):
        cal = SEASON.cal
        for kind, tours in (('amateur', [k for k, t in TOUR_BY_KEY.items() if t.tier == 6]),
                            ('club_pro', [k for k, t in TOUR_BY_KEY.items() if t.tier == 8])):
            for k in tours:
                got = Counter(x.host_country for x in cal.series if x.tour == k and x.category == 'regular')
                regions = {COUNTRIES[c].region for c, _ in TOUR_BY_KEY[k].countries}
                want = local_allocation(tuple(regions), kind)
                for c, n in want.items():
                    self.assertGreaterEqual(got[c], min(n, 2), (k, c))
        sweden = [x for x in cal.series if x.tour == 'CP_EUROPE' and x.host_country == 'Sweden']
        self.assertGreaterEqual(len(sweden), 6)

    def test_club_professionals_outside_north_america_are_eligible(self):
        s = SEASON
        cp = next(g for g in s.world.golfers if g.status == 'club_pro' and g.country == 'England')
        ev = next(x for x in s.cal.series if x.tour == 'CP_EUROPE' and x.host_country == 'England')
        self.assertTrue(s.eligible(cp, ev, ev.week))
        pro = next(g for g in s.world.golfers if g.status == 'pro' and g.country == 'England')
        self.assertFalse(s.eligible(pro, ev, ev.week))
        self.assertEqual(ev.days in ('Mon', 'Mon-Tue'), True)          # club pros work weekends

    def test_newcomers_and_college_golfers_have_open_doors(self):
        s = fresh()
        am_ev = next(x for x in s.cal.series if x.tour == 'AM_NORTH_AMERICA' and x.category == 'regular')
        d1 = next(g for g in s.world.golfers if g.tour == 'CO_US_D1' and g.country != 'USA')
        self.assertTrue(s.eligible(d1, am_ev, 10))                       # at college in the USA, in season too
        newcomer = next(g for g in s.world.golfers if g.status == 'amateur' and g.tour == 'AM_NORTH_AMERICA')
        s.am_pos.pop(newcomer.id, None)
        self.assertTrue(s.eligible(newcomer, am_ev, am_ev.week))
        veteran = next(g for g in s.world.golfers if g.status == 'amateur' and g.tour == 'AM_NORTH_AMERICA'
                       and g.id != newcomer.id)
        s.am_pos[veteran.id] = 1
        s.played[2027][veteran.id] = list(range(1, 9))                    # eight starts already
        self.assertLess(s.priority(newcomer, am_ev), s.priority(veteran, am_ev))   # the lineup rotates


class FlagshipTests(unittest.TestCase):
    def test_every_circuit_has_a_flagship(self):
        cal = SEASON.cal
        for k, t in TOUR_BY_KEY.items():
            if t.tier in CIRCUIT_FLAGSHIPS and k not in CIRCUIT_FLAGSHIP_ELSEWHERE:
                fl = [x for x in cal.series if x.tour == k and x.category == 'circuit_championship']
                self.assertEqual(len(fl), 1, k)
                self.assertGreaterEqual(fl[0].week, max(w for x in cal.series if x.tour == k
                                                        and x.category == 'regular' for w in (x.week,)) - 8, k)
        self.assertIn(CIRCUIT_FLAGSHIP_ELSEWHERE['CP_NORTH_AMERICA'], cal.by_id)

    def test_circuit_championship_field_routes_ties_and_alternates(self):
        s = fresh()
        ed = next(e for e in s.cal.editions(2027) if e.series.series_id == 'CH_EUROPE_CHAMPIONSHIP')
        members = [g for g in s.world.golfers if g.tour == 'CH_EUROPE']
        m = s.money[('CH_EUROPE', 2027)]
        for i, g in enumerate(members):
            m[g.id] = 100000 - 1000 * (i // 2)                            # pairs tied on money
        champ = members[150]
        s.champions['CH_EUROPE_CHAMPIONSHIP'] = [(2025, members[0].id, -8), (2026, champ.id, -10)]   # most recent first
        broke = members[3]
        broke.cash, broke.backing = -1e6, 0.0
        sites = s.special_field(ed, 2027, ed.week, random.Random(1), defaultdict(set))
        ids = sites[0]
        self.assertEqual(len(ids), ed.series.field)
        self.assertEqual(len(ids), len(set(ids)))                         # a champion high on the list once
        self.assertEqual(ids[:2], [champ.id, members[0].id])
        self.assertNotIn(broke.id, ids)                                   # declined: the next on the list in
        self.assertIn('CH_EUROPE_CHAMPIONSHIP', s.declined[2027][broke.id])
        routes = s.entry_routes[(2027, 'CH_EUROPE_CHAMPIONSHIP')]
        self.assertEqual(routes[champ.id], 'PAST CHAMPION')
        # ties on money go to the better world ranking
        a, b = members[4], members[5]
        first, second = sorted((a, b), key=lambda g: s.wr_pos.get(g.id, 10 ** 6))
        self.assertLess(ids.index(first.id), ids.index(second.id))

    def test_usa_amateur_open_qualifying_needs_no_ranking(self):
        s = fresh()
        eds = {e.series.series_id: e for e in s.cal.editions(2027)}
        q = eds['USA_AMATEUR_QUALIFYING']
        newcomer = next(g for g in s.world.golfers if g.status == 'amateur' and g.country == 'USA'
                        and g.lifestyle == 'full_time' and not g.tour.startswith('CO_'))
        s.am_pos.pop(newcomer.id, None)
        for g in s.world.golfers:                                        # an active season so far
            if g.status == 'amateur':
                s.played[2027][g.id] = [1, 2, 3]
        exempt = s.usa_amateur_exempt(2027)
        self.assertEqual(len(exempt), len(set(exempt)))
        sites = s.special_field(q, 2027, q.week, random.Random(1), defaultdict(set))
        entrants = {gid for site in sites for gid in site}
        self.assertTrue(newcomer.id in entrants or len(entrants) == q.series.field * q.series.sites)
        self.assertFalse(entrants & set(exempt))
        # qualifiers fill the field after the exempt players
        rows = sorted(entrants, key=lambda gid: s.entry_ticket(s.g[gid], q.series))
        for k, site in enumerate(sites):
            s.ctx.add_result('USA_AMATEUR_QUALIFYING', 2027, [(gid, i + 1) for i, gid in enumerate(site)], site=k)
        field = s.special_field(eds['USA_AMATEUR'], 2027, eds['USA_AMATEUR'].week, random.Random(1), defaultdict(set))[0]
        self.assertEqual(len(field), eds['USA_AMATEUR'].series.field)
        routes = s.entry_routes[(2027, 'USA_AMATEUR')]
        self.assertTrue(any(v.startswith('QUALIFYING SITE') for v in routes.values()))
        self.assertTrue(any(v.startswith('AMATEUR RANKING') for v in routes.values()))
        self.assertTrue(rows)


class AccessRecordTests(unittest.TestCase):
    def test_every_week_classified_and_kept_in_history(self):
        s = SEASON
        for gid, c in s.week_access[2027].items():
            self.assertEqual(sum(c.values()), 2, gid)                    # both weeks run
            self.assertTrue(set(c) <= set(ACCESS))
        routes = s.event_routes[2027]
        self.assertTrue(routes)
        some = next(iter(routes.values()))
        self.assertTrue(all(isinstance(v, str) and v for v in some.values()))


class HistoryContractTests(unittest.TestCase):
    def test_archive_keeps_classification_routes_rankings_and_access(self):
        import tempfile
        from golfsim.archive import Archive, write_archive
        s = SEASON
        s.snapshots[2027] = s.season_snapshot(2027)
        with tempfile.TemporaryDirectory() as d:
            arc = Archive(write_archive(s, d, years=[2027]))
            ev = next(e for e in arc.year(2027)['events'] if e['id'] == '2027:TOUR_MASTERS')
            self.assertEqual((ev['tour'], ev['tier'], ev['category']), ('MAJORS', 0, 'major'))
            top = arc.ranking(2027, 18)
            self.assertEqual(top[:100], s.ctx.world_rankings[(2027, 18)][:100])
            self.assertEqual(arc.weeks_at_number_one()[top[0]] >= 1, True)
            gid = next(g for g, _ in ev['team'].items())
            starts = [r for r in arc.results(gid) if r['event'] == '2027:TOUR_MASTERS']
            self.assertTrue(starts[0]['route'])                          # how they got into the Masters
            acc = arc.access(gid, 2027)
            self.assertEqual(sum(acc['weeks'].values()), 2)

    def test_weekly_detail_is_pruned_but_finals_and_results_stay(self):
        s = fresh()
        s.ctx.world_rankings[(2020, 5)] = [1]
        s.ctx.standings[('CH_EUROPE', 2020, 5)] = [1]
        s.ctx.standings[('CH_EUROPE', 2020)] = [1]
        s.ctx.add_result('PT_TEXAS_OPEN', 2020, [(1, 1)])
        s.week_access[2020][1]['chose to train'] = 1
        s.prune_history(2027)
        self.assertNotIn((2020, 5), s.ctx.world_rankings)
        self.assertNotIn(('CH_EUROPE', 2020, 5), s.ctx.standings)
        self.assertIn(('CH_EUROPE', 2020), s.ctx.standings)
        self.assertIn(('PT_TEXAS_OPEN', 2020), s.ctx.results)
        self.assertNotIn(2020, s.week_access)
        self.assertIn((2026, 52), s.ctx.world_rankings)                    # last season's weeks stay


if __name__ == '__main__':
    unittest.main()
