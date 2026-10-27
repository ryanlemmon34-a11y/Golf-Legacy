"""Season engine, prestige and tour cards.

Run from the project folder:  python -m unittest discover -s tests -v
"""
from __future__ import annotations

import random
import sys
import unittest
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from golfsim import prestige as PR                                    # noqa: E402
from golfsim.calendar import TOUR_BY_KEY                              # noqa: E402
from golfsim.cards import apply_cards                                 # noqa: E402
from golfsim.population import MEMBERS_PER_FIELD, generate_world      # noqa: E402
from golfsim.season import PREMIER_TOURS, Season                      # noqa: E402

WEEKS = 19


def _run(weeks, seed=2027):
    s = Season(generate_world(seed=seed), seed=seed, workers=2)
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


class SeasonTests(unittest.TestCase):
    def test_fields_respect_capacity_days_and_amateur_limits(self):
        s = SEASON
        week_days = defaultdict(lambda: defaultdict(set))
        for r in s.results.values():
            ser = s.cal.by_id[r.series_id]
            ids = [gid for site in r.finish for gid, _, _ in site]
            self.assertEqual(len(ids), len(set(ids)), r.event_id)
            self.assertLessEqual(len(ids), ser.field * ser.sites, r.event_id)
            if ser.tier in (1, 2) and ser.kind != 'major':
                self.assertLessEqual(sum(s.g[g].status == 'amateur' for g in ids), 8, r.event_id)
            for gid in ids:
                clash = week_days[r.week][gid] & ser.day_set
                self.assertFalse(clash, (r.event_id, gid))
                week_days[r.week][gid] |= ser.day_set

    def test_every_event_played_and_recorded(self):
        s = SEASON
        played = {r.event_id for r in s.results.values()}
        for ed in s.cal.editions(2027):
            if ed.week <= WEEKS and ed.series.kind != 'qualifying':
                self.assertIn(ed.event_id, played)
        self.assertGreater(s.holes_played[2027], 800_000)
        self.assertTrue(s.records.layouts)
        self.assertTrue(s.ctx.ranking(2027, WEEKS))

    def test_tour_masters_field_from_the_rules(self):
        r = SEASON.results['2027:TOUR_MASTERS']
        self.assertTrue(80 <= len(r.finish[0]) <= 100)
        top = SEASON.world.ranked(SEASON.world.pros())[:20]
        self.assertGreaterEqual(len({g.id for g in top} & {gid for gid, _, _ in r.finish[0]}), 18)

    def test_stars_skip_opportunity_events(self):
        s = SEASON
        top30 = {g.id for g in s.world.ranked(s.world.pros())[:30]}
        def stars(category):
            rs = [r for r in s.results.values() if s.cal.by_id[r.series_id].category == category]
            return sum(len(top30 & {gid for gid, _, _ in r.finish[0]}) for r in rs) / max(1, len(rs))
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
