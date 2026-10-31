"""Season engine, prestige and tour cards.

Run from the project folder:  python -m unittest discover -s tests -v
"""
from __future__ import annotations

import random
import statistics
import sys
import unittest
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from golfsim import prestige as PR                                    # noqa: E402
from golfsim.calendar import TOUR_BY_KEY                              # noqa: E402
from golfsim.cards import apply_cards                                 # noqa: E402
from golfsim.population import MEMBERS_PER_FIELD, generate_world      # noqa: E402
from golfsim.season import AMATEUR_OPEN_EXPANSION, PREMIER_TOURS, Season  # noqa: E402

WEEKS = 19


def _run(weeks, seed=2027):
    # the classic calendar: these checks sample its first 19 weeks (under the reference calendar the Kenya
    # Open in week 10 draws more of the top 30, while opportunity events stay star-light over the season)
    s = Season(generate_world(seed=seed), seed=seed, workers=2, calendar='v1')
    eds = s.cal.editions(2027)
    for w in range(1, weeks + 1):
        s.run_week(2027, w, [e for e in eds if e.week == w])
    s.close()
    return s


SEASON = _run(WEEKS)


class PrestigeTests(unittest.TestCase):
    def test_scales(self):
        self.assertAlmostEqual(PR.world_points(100, 1), 100.0)
        self.assertGreater(PR.world_points(90, 1), PR.world_points(75, 1) > PR.world_points(55, 1))
        self.assertEqual(PR.world_points(90, None), 0)
        shares = PR.payout_shares(70)
        self.assertAlmostEqual(sum(shares), 1.0)
        self.assertTrue(all(a >= b for a, b in zip(shares, shares[1:])))
        self.assertGreater(PR.player_prestige(2000, 200), PR.player_prestige(200, 0) > PR.player_prestige(10, 0))
        self.assertGreater(PR.endorsements(85), 10_000_000)
        self.assertLess(PR.endorsements(20), 50_000)
        self.assertGreater(PR.fame_points(100, 1), 5 * PR.fame_points(55, 1))

    def test_event_prestige_ladder(self):
        p = SEASON.event_prestige
        by = SEASON.cal.by_id
        cat = defaultdict(list)
        for sid, v in p.items():
            s = by[sid]
            cat['major' if s.kind == 'major' else s.category if s.tier == 1 else f'tier{s.tier}'].append(v)
        mean = {k: sum(v) / len(v) for k, v in cat.items()}
        self.assertGreater(mean['major'], mean['flagship'])
        self.assertGreater(mean['flagship'], mean['standard'])
        self.assertGreater(mean['standard'], mean['opportunity'] + 5)
        self.assertGreater(mean['opportunity'], mean['tier2'])
        self.assertGreater(mean['tier2'], mean['tier3'] > mean['tier4'])

    def test_weeks_are_fixed_every_year(self):
        a = {e.series.series_id: e.week for e in SEASON.cal.editions(2027)}
        for y in (2028, 2035):
            self.assertEqual(a, {e.series.series_id: e.week for e in SEASON.cal.editions(y)})


    def test_event_prestige_is_a_rolling_average(self):
        """Five calendar years, recency-weighted (rules 2026-11-05; tests/test_world_prestige.py for the rest)."""
        from golfsim.calendar import WorldCalendar
        ser = WorldCalendar().by_id['PT_GULF_COAST_CLASSIC']
        by = PR.seeded_years(PR.factors(ser, 70, 80), 2027)
        before = PR.combine(PR.window_factors(by, 2026))
        by[2027] = [PR.factors(ser, 100, 80)]                 # one great field: a quarter of the weight
        after = PR.combine(PR.window_factors(by, 2027))
        self.assertAlmostEqual(after - before, PR.WEIGHTS['field'] * 30 * PR.YEAR_WEIGHTS[0] / sum(PR.YEAR_WEIGHTS))
        for y in range(2028, 2027 + PR.EVENT_YEARS):
            by[y] = [PR.factors(ser, 100, 80)]
        self.assertAlmostEqual(PR.combine(PR.window_factors(by, 2026 + PR.EVENT_YEARS)) - before,
                               PR.WEIGHTS['field'] * 30)

    def test_player_fame_is_last_52_weeks(self):
        s = SEASON
        gid = s.world.ranked(s.world.pros())[0].id
        s.fame_log[gid].append((s.abs_week(2027, WEEKS) - 60, 999.0))   # an old result
        s.update_fame(2027, WEEKS)
        self.assertLess(s.fame[gid], 999.0)


class FatigueTests(unittest.TestCase):
    def test_fatigue_injury_risk_and_recovery(self):
        s = SEASON
        g = next(x for x in s.world.golfers if x.status == 'pro' and 40 < x.attrs['injury_resistance'] < 60)
        s.fatigue[g.id] = 0.0
        fresh = s.injury_chance(g, 4, 2027)
        s.fatigue[g.id] = 0.8
        tired = s.injury_chance(g, 4, 2027)
        self.assertGreater(tired, 3 * fresh)
        fragile = dict(g.attrs, injury_resistance=20)
        sturdy = dict(g.attrs, injury_resistance=90)
        from dataclasses import replace
        self.assertGreater(s.injury_chance(replace(g, attrs=fragile), 4, 2027),
                           2 * s.injury_chance(replace(g, attrs=sturdy), 4, 2027))
        old = replace(g, born=2027 - 45)
        young = replace(g, born=2027 - 25)
        self.assertGreater(s.injury_chance(old, 4, 2027), s.injury_chance(young, 4, 2027))
        self.assertGreater(s.load(replace(g, attrs=dict(g.attrs, stamina=20)), 4, False, 2027),
                           s.load(replace(g, attrs=dict(g.attrs, stamina=90)), 4, False, 2027))
        s.fatigue[g.id] = 0.0

    def test_tired_golfers_score_worse(self):
        from golfsim.course import ashford_ridge
        from golfsim.engine import play_round
        from golfsim.golfer import uniform_golfer
        def avg(f):
            gg = uniform_golfer(75)
            gg.fatigue = f
            rng = random.Random(4)
            return sum(play_round(gg, ashford_ridge(), rng).score for _ in range(1500)) / 1500
        self.assertGreater(avg(0.8), avg(0.0) + 0.6)

    def test_injured_players_sit_out(self):
        s = SEASON
        for yy, rows in s.injuries.items():
            for week, gid, kind, weeks, _ in rows:
                later = [w for w in s.played[yy][gid] if week < w <= week + weeks]
                self.assertEqual(later, [], (gid, week, weeks))


class SeasonTests(unittest.TestCase):
    def test_fields_respect_capacity_days_and_amateur_limits(self):
        s = SEASON
        week_days = defaultdict(lambda: defaultdict(set))
        for r in s.results.values():
            ser = s.cal.by_id[r.series_id]
            ids = [gid for site in r.finish for gid, _, _ in site]
            self.assertEqual(len(ids), len(set(ids)), r.event_id)
            # open amateur events take up to AMATEUR_OPEN_EXPANSION times their field when more want to play
            room = AMATEUR_OPEN_EXPANSION if ser.tier == 6 and not s.is_special(ser) else 1
            self.assertLessEqual(len(ids), int(ser.field * room) * ser.sites, r.event_id)
            if ser.tier in (1, 2) and ser.kind != 'major':
                self.assertLessEqual(sum(s.g[g].status == 'amateur' for g in ids), 8, r.event_id)
            for gid in ids:
                clash = week_days[r.week][gid] & ser.day_set
                self.assertFalse(clash, (r.event_id, gid))
                week_days[r.week][gid] |= ser.day_set

    def test_every_event_played_and_recorded(self):
        s = SEASON
        played = {r.event_id for r in s.results.values()}
        unheld = set(s.unheld[2027])
        self.assertFalse(played & unheld)
        for ed in s.cal.editions(2027):
            if ed.week <= WEEKS and ed.series.kind != 'qualifying':
                self.assertIn(ed.event_id, played | unheld)
                # only local and open events can go without entries (a club-pro Monday in a small country);
                # the tours, college and the championships are always played
                if ed.event_id in unheld:
                    self.assertIn(ed.series.tier, (4, 6, 8), ed.event_id)
        self.assertLess(len(unheld), 0.1 * len(played))
        self.assertGreater(s.holes_played[2027], 800_000)
        self.assertTrue(s.records.layouts)
        self.assertTrue(s.ctx.ranking(2027, WEEKS))

    def test_tour_masters_field_from_the_rules(self):
        r = SEASON.results['2027:TOUR_MASTERS']
        self.assertTrue(80 <= len(r.finish[0]) <= 100)
        top = SEASON.world.ranked(SEASON.world.pros())[:20]
        self.assertGreaterEqual(len({g.id for g in top} & {gid for gid, _, _ in r.finish[0]}), 18)

    def test_every_major_entrant_has_a_recorded_route(self):
        routes = SEASON.entry_routes[(2027, 'TOUR_MASTERS')]
        r = SEASON.results['2027:TOUR_MASTERS']
        self.assertEqual({gid for gid, _, _ in r.finish[0]}, set(routes))
        self.assertTrue(all(v for v in routes.values()))

    def test_club_pro_sectionals_are_played_and_decide_the_championship(self):
        sect = SEASON.results['2027:CLUB_PRO_SECTIONALS']
        self.assertGreater(len(sect.finish), 1)                              # several sites
        finishers = {gid for site in sect.finish for gid, pos, _ in site if pos is not None}
        champ = SEASON.results['2027:CLUB_PRO_CHAMPIONSHIP']
        entrants = {gid for gid, _, _ in champ.finish[0]}
        self.assertTrue(entrants and entrants <= finishers)
        self.assertTrue(all(SEASON.g[gid].status == 'club_pro' for gid in finishers))

    def test_stars_skip_opportunity_events(self):
        s = SEASON
        top30 = {g.id for g in s.world.ranked(s.world.pros())[:30]}
        def stars(category):
            rs = [r for r in s.results.values() if s.cal.by_id[r.series_id].category == category]
            return statistics.median(len(top30 & {gid for gid, _, _ in r.finish[0]}) for r in rs)
        # medians: the week-2 season opener is an opportunity event that stars play because nothing
        # else is on that week, which made a mean hinge on one event
        self.assertGreater(stars('flagship'), 20)
        self.assertLess(stars('opportunity'), stars('flagship') / 3)

    def test_prize_money_paid_in_full(self):
        s = SEASON
        r = s.results['2027:PT_PREMIER_PLAYERS_CHAMPIONSHIP']
        purse = s.cal.by_id[r.series_id].purse
        paid = sum(s.earnings[2027][gid] for gid, pos, _ in r.finish[0] if pos is not None)
        # (other events also paid these players; the winner's share alone is 18%)
        self.assertGreaterEqual(paid, purse * 0.99)
        self.assertEqual(r.winner(), r.finish[0][0][0])

    def test_deterministic(self):
        a = _run(3)
        b = _run(3)
        self.assertEqual({k: v.finish for k, v in a.results.items()}, {k: v.finish for k, v in b.results.items()})


class CardTests(unittest.TestCase):
    def test_promotion_and_relegation_keep_tours_full(self):
        s = Season(generate_world(), seed=1, workers=1)
        rng = random.Random(3)
        for g in s.world.golfers:
            if g.status == 'pro':
                keys = [g.tour] + (['PREMIER'] if g.tour in PREMIER_TOURS else [])
                for k in keys:
                    s.money[(k, 2027)][g.id] = rng.random() * 1e6 * (1 + g.overall / 10)
        prem = [g for g in s.world.golfers if g.tour in PREMIER_TOURS]
        worst = min(prem, key=lambda g: s.money[('PREMIER', 2027)][g.id])
        ch = [g for g in s.world.golfers if g.tour == 'CH_AMERICAS']
        best_ch = max(ch, key=lambda g: s.money[('CH_AMERICAS', 2027)][g.id])
        apply_cards(s, 2027)
        self.assertNotIn(worst.tour, PREMIER_TOURS)
        self.assertEqual(best_ch.tour, 'PT_AMERICAS')
        sizes = Counter(g.tour for g in s.world.golfers if g.status == 'pro')
        # (no winners or Q-School graduates in this synthetic season, so a little under 300)
        self.assertTrue(250 <= sum(sizes[t] for t in PREMIER_TOURS) <= 330)
        for key, t in TOUR_BY_KEY.items():
            if t.tier == 2:
                self.assertLessEqual(abs(sizes[key] - round(t.field * MEMBERS_PER_FIELD)), 25, key)
        self.assertTrue(s.card_log[2027])


if __name__ == '__main__':
    unittest.main()
