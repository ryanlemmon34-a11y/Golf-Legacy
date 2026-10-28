"""Finance through the real season: forecasts, cards, backing and careers, as the engine runs them.

Run from the project folder:  python -m unittest discover -s tests -v
"""
from __future__ import annotations

import copy
import sys
import unittest
from unittest import mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from golfsim import careers as C                                      # noqa: E402
from golfsim import finance as FIN                                    # noqa: E402
from golfsim.calendar import TOUR_BY_KEY                              # noqa: E402
from golfsim.population import generate_world                         # noqa: E402
from golfsim.season import Season                                     # noqa: E402


class PromotionTests(unittest.TestCase):
    """A season played for real, then the real end of season: cards, backers, careers."""

    @classmethod
    def setUpClass(cls):
        cls.s = s = Season(generate_world(seed=11, scale=0.2), seed=11, development=True, workers=4)
        cls.pots0 = {g.id: (g.cash, g.backing, g.backer_funds) for g in s.world.golfers}
        s.start_year(2027)
        for w in range(1, 53):
            s.advance_week(2027, w)
        cls.end = {g.id: (g.cash, g.backing, g.backer_funds) for g in s.world.golfers}
        cls.before = {g.id: (g.backer, g.cash, g.tour) for g in s.world.golfers}
        cls.status = {g.id: g.status for g in s.world.golfers}
        s.finish_year(2027)
        cls.promoted = {gid: (frm, to, why) for gid, frm, to, why in s.card_log[2027]
                        if TOUR_BY_KEY[frm].tier > TOUR_BY_KEY[to].tier}
        cls.decisions = {t['gid']: t for t in s.transitions[2027]}

    @classmethod
    def tearDownClass(cls):
        cls.s.close()

    def test_a_new_card_does_not_prove_financial_independence(self):
        s = self.s
        backed = [gid for gid in self.promoted if self.before[gid][0]]
        poor = [gid for gid in backed if self.before[gid][1] < 50000]
        self.assertGreater(len(poor), 5)                                     # cash-poor golfers who earned promotion
        independent = [gid for gid in backed if self.decisions.get(gid, {}).get('kind') == 'backers no longer needed']
        for gid in independent:
            g = s.g[gid]
            why = next(t for y, w, t in reversed(s.history[gid]) if 'Paying their own way' in t)
            # cash for the start of the season, then savings for several seasons or proven earnings
            g2 = copy.deepcopy(g)
            g2.backer = 0.0                                                    # judged without the backers
            income, costs = s.season_forecast(g, g.tour, s.target_events(g), without_backers=True, cautious=True)
            self.assertGreaterEqual(g.cash, FIN.UPFRONT_SHARE * costs, (gid, why))
            if 'savings' in why:
                self.assertGreaterEqual(g.cash, C.SELF_FUNDED_SEASONS * (costs - income) - 1e-6, (gid, why))
            elif 'sponsor contract' in why:                                    # a contract, not a forecast
                self.assertGreaterEqual(s.sponsor_income(g), costs, (gid, why))
            else:                                                              # proven at the new level
                self.assertGreaterEqual(s.events_at_level(gid, TOUR_BY_KEY[g.tour].tier), FIN.PROVEN_EVENTS, (gid, why))
                self.assertGreaterEqual(income, costs, (gid, why))
        # a level they have barely played (if any such golfer was promoted in this world) is not an income yet
        unproven = [gid for gid in backed
                    if s.events_at_level(gid, TOUR_BY_KEY[self.promoted[gid][1]].tier) < FIN.PROVEN_EVENTS]
        for gid in unproven:
            why = self.decisions.get(gid, {}).get('kind')
            if why == 'backers no longer needed':
                why = next(t for y, w, t in reversed(s.history[gid]) if 'Paying their own way' in t)
                self.assertTrue('savings' in why or 'sponsor contract' in why, why)   # money they have, not hope
        kept = [gid for gid in poor if s.g[gid].backer and s.g[gid].tour == self.promoted[gid][1]]
        self.assertTrue(kept)                                                # patient backers stay with them
        for gid in poor:
            lines = [t for y, w, t in s.history[gid] if y == 2027 and w == 53]
            self.assertTrue(any('→' in t for t in lines), gid)              # the card change is in their history

    def test_promotion_raises_willingness_without_inventing_income(self):
        s = self.s
        gid = next(gid for gid in self.promoted if s.g[gid].lifestyle == 'full_time' and s.g[gid].status == 'pro')
        g = s.g[gid]
        frm = self.promoted[gid][0]
        before = copy.deepcopy(g)
        before.tour = frm
        new_tier, old_tier = TOUR_BY_KEY[g.tour].tier, TOUR_BY_KEY[frm].tier
        # what they can count on at the new level before playing it is less than their record suggests there
        self.assertLess(s.prize_forecast(g, new_tier, cautious=True), s.prize_forecast(g, new_tier))
        self.assertLessEqual(s.prize_forecast(g, new_tier), s.prize_forecast(g, old_tier))   # stronger fields
        row = s.snapshots[2027][gid]
        self.assertGreater(C.desire_to_continue(s, g, dict(row, promoted=True), 2027),
                           C.desire_to_continue(s, before, dict(row, promoted=False), 2027))


    def test_payers_are_labelled_and_support_money_is_conserved(self):
        """Every event paid for by someone else is counted for the payer who really paid it, and the
        money golfers draw on stays in its own pot: cash reconciles with the ledger, family money falls
        only by what was drawn from it, and backers' money moves only by what they put up, what was drawn
        and what went back to them when a deal ended."""
        s = self.s
        for gid, n in s.school_trips[2027].items():                         # the tour they had in the season
            self.assertTrue(n == 0 or self.before[gid][2].startswith('CO_'), gid)
        self.assertTrue(s.club_trips[2027])
        for gid in s.club_trips[2027]:
            self.assertEqual(self.status[gid], 'club_pro', gid)
        self.assertFalse(set(s.club_trips[2027]) & {gid for gid, n in s.school_trips[2027].items() if n})
        led = s.ledgers[2027]
        drawn = backed = returned = 0
        for gid, (_, backing0, funds0) in self.pots0.items():
            g, l = s.g[gid], led.get(gid)
            support, backer_support = (l.support, l.backer_support) if l else (0.0, 0.0)
            cash0 = s.cash_start[2027][gid]
            self.assertAlmostEqual(self.end[gid][0], cash0 + (l.net if l else 0.0), delta=0.01)
            self.assertAlmostEqual(self.end[gid][1], backing0 - support, delta=0.01)      # family money
            put_up = s.backer_flows[2027][(gid, 'put_up')]
            self.assertAlmostEqual(self.end[gid][2], funds0 + put_up - backer_support, delta=0.01)
            back = s.backer_flows[2027][(gid, 'returned')]
            self.assertAlmostEqual(g.backer_funds, self.end[gid][2] - back, delta=0.01)  # deals that ended
            drawn += backer_support > 0
            backed += put_up > 0
            returned += back > 0
        self.assertTrue(drawn and backed and returned)


class EntryBudgetTests(unittest.TestCase):
    """One budget per golfer per week: entries reserve their cost as they are accepted, each site of a
    qualifier is priced for the golfer at that site, and a caddie's weekly fee is paid once a week."""

    @classmethod
    def setUpClass(cls):
        cls.s = s = Season(generate_world(seed=11, scale=0.2), seed=11, development=True, workers=1)
        s.start_year(2027)
        for w in range(1, 19):
            s.advance_week(2027, w)

    def _week(self, s, week):
        return next(e for e in s.cal.editions(2027) if e.week == week and e.series.series_id.startswith(
            'USA_OPEN_LOCAL' if week < 22 else 'USA_OPEN_FINAL'))

    @staticmethod
    def _set_spendable(s, g, amount):
        g.backing = g.backer_funds = 0.0
        g.cash += amount - s.spendable(g, 2027)

    def _cheapest_regular(self, s, g, week):
        venues = s.lib.venues(2027)
        costs = [s.trip_cost(g, e.series, venues[e.event_id][0].city) for e in s.cal.editions(2027)
                 if e.week == week and not s.is_special(e.series) and s.eligible(g, e.series, week)]
        return min(costs) if costs else None

    def test_a_qualifier_and_a_weekend_event_share_one_budget(self):
        local = self._week(self.s, 19)
        free = copy.deepcopy(self.s)
        free.advance_week(2027, 19)
        both = lambda s: {gid for gid, wks in s.played[2027].items() if wks.count(19) >= 2}
        self.assertTrue(both(free))                                      # golfers do play both when they can
        s = copy.deepcopy(self.s)
        city = s.lib.venues(2027)[local.event_id][0].city
        tight = {}
        for g in s.active_golfers():
            if g.status != 'pro' or g.lifestyle != 'full_time' or s.staff.caddie(g.id) is not None:
                continue
            q, r = s.trip_cost(g, local.series, city), self._cheapest_regular(s, g, 19)
            if r is not None and q > 0:
                self._set_spendable(s, g, max(q, r) + 1)                 # either one, not both
                tight[g.id] = (q, r)
        s.advance_week(2027, 19)
        played_local = {gid for rows in s.ctx.results[(local.series.series_id, 2027)].values() for gid, _ in rows}
        self.assertTrue(played_local & set(tight))                       # each was affordable on its own
        self.assertFalse(both(s) & set(tight))                           # but not the two together

    def test_qualifiers_are_priced_at_their_own_site_and_a_caddie_is_paid_once_a_week(self):
        s = copy.deepcopy(self.s)
        for w in (19, 20, 21):
            s.advance_week(2027, w)
        intl = self._week(s, 22)
        assert intl.series.series_id == 'USA_OPEN_FINAL_INTL'
        england, japan = (v.city for v in s.lib.venues(2027)[intl.event_id])
        tight = []
        for g in s.active_golfers():
            if g.country != 'Japan' or g.status != 'pro' or g.lifestyle == 'retired':
                continue
            at_home, abroad = s.trip_cost(g, intl.series, japan), s.trip_cost(g, intl.series, england)
            self.assertLess(at_home, abroad)
            self._set_spendable(s, g, at_home + 1)                       # Japan, not England
            tight.append(g.id)
        self.assertTrue(tight)
        before = {g.id: (s.ledger(2027, g.id).caddie, s.staff.caddie(g.id).weeks_worked)
                  for g in s.active_golfers() if s.staff.caddie(g.id) is not None}
        s.advance_week(2027, 22)
        sites = s.ctx.results[('USA_OPEN_FINAL_INTL', 2027)]
        self.assertTrue({gid for gid, _ in sites.get(1, ())} & set(tight))   # they qualify at the Japan site
        for gid in tight:
            self.assertNotIn(gid, {g for g, _ in sites.get(0, ())})
            self.assertNotIn('USA_OPEN_FINAL_INTL', s.declined[2027].get(gid, ()))
        two = 0
        for w in (22, 23):
            if w == 23:
                before = {gid: (s.ledger(2027, gid).caddie, s.staff.caddie(gid).weeks_worked)
                          for gid in before if s.staff.caddie(gid) is not None}
                s.advance_week(2027, 23)
            for gid, (paid, worked) in before.items():
                k = s.staff.caddie(gid)
                if k is None:
                    continue
                n = s.played[2027][gid].count(w)
                self.assertAlmostEqual(s.ledger(2027, gid).caddie - paid, k.weekly_fee if n else 0.0, delta=0.01)
                self.assertEqual(k.weeks_worked - worked, 1 if n else 0)
                two += n >= 2
        self.assertTrue(two)                                             # some played twice in a week


class InjuryDebtTests(unittest.TestCase):
    """The debt rule (finance.py, 'Debt'): the line of credit limits what a golfer chooses to spend;
    living costs go on whatever their funds. An injured professional who needs money does light paid
    work while recovering; one with money rests. Debt is neither erased nor covered by anyone new,
    blocks spending until repaid, and weighs on the season's-end decision smoothly, with no threshold."""

    @classmethod
    def setUpClass(cls):
        cls.s = s = Season(generate_world(seed=13, scale=0.2), seed=13, development=True, workers=4)
        s.start_year(2027)
        pros = [g for g in s.active_golfers() if g.status == 'pro' and g.lifestyle == 'full_time'
                and not g.backer and s.staff.coach(g.id) is None and s.staff.caddie(g.id) is None]
        cls.poor, cls.rich = pros[0], pros[1]
        for g, cash in ((cls.poor, 1000.0), (cls.rich, 400000.0)):
            g.cash, g.backing, g.backer_funds = cash, 0.0, 0.0
            s.cash_start[2027][g.id] = g.cash
            s.injured[g.id] = (s.abs_week(2027, 1) + 31, 'back', 30)    # out for weeks 1-30
        for w in range(1, 31):
            s.advance_week(2027, w)
        cls.at30 = {g.id: (copy.deepcopy(s.ledger(2027, g.id)), g.cash) for g in (cls.poor, cls.rich)}
        for w in range(31, 53):
            s.advance_week(2027, w)

    @classmethod
    def tearDownClass(cls):
        cls.s.close()

    def test_an_injured_professional_who_needs_money_works_while_recovering(self):
        s, g = self.s, self.poor
        led, cash = self.at30[g.id]
        self.assertFalse([w for w in s.played[2027].get(g.id, ()) if w <= 30])   # no golf while hurt ...
        self.assertGreater(led.work, 0.0)                                         # ... but paid work
        self.assertAlmostEqual(led.work % FIN.WORK_WAGE, 0.0, delta=0.01)
        self.assertAlmostEqual(led.living, 30 * FIN.LIVING / 52, delta=0.01)     # living costs go on
        self.assertEqual(led.support + led.backer_support, 0.0)                   # nobody new pays them
        self.assertGreater(cash, -FIN.credit_limit(0.0))                          # injury did not sink them
        self.assertEqual(s.injured.get(g.id), None)                               # and they healed on time

    def test_an_injured_professional_with_money_rests(self):
        led, _ = self.at30[self.rich.id]
        self.assertEqual(led.work, 0.0)

    def test_debt_is_kept_and_weighed_smoothly(self):
        s, g = self.s, self.poor
        led = s.ledger(2027, g.id)
        self.assertAlmostEqual(g.cash, 1000.0 + led.net, delta=0.01)             # kept, never erased
        row = s.season_snapshot(2027)[g.id]
        cash = g.cash
        ps = []
        for debt in (0, 10000, 20000, 30000, 40000):
            g.cash = -debt
            ps.append(C.p_stop_chasing(s, g, row, 2027)[0])
        g.cash = cash
        self.assertEqual(ps, sorted(ps))                                          # more debt, more pressure
        self.assertLess(max(ps), 1.0)
        self.assertLess(max(b - a for a, b in zip(ps, ps[1:])), 0.25)             # never a cliff


class BackersWhenNeededTests(unittest.TestCase):
    """Backers come when a golfer needs them: the starting world gives no deal to a professional whose
    own savings already cover three seasons of losses, and an unbacked professional whose own money
    runs low can find backers (not within two winters of a deal ending)."""

    @classmethod
    def setUpClass(cls):
        cls.s = s = Season(generate_world(seed=14, scale=0.2), seed=14, development=True, workers=1)
        s.start_year(2027)
        cls.snap = s.season_snapshot(2027)

    def test_the_starting_world_backs_only_those_who_need_it(self):
        tour_pros = [g for g in self.s.world.golfers if g.status == 'pro' and g.lifestyle == 'full_time'
                     and g.tour in TOUR_BY_KEY and TOUR_BY_KEY[g.tour].tier >= 2]
        rich = [g for g in tour_pros if g.cash >= FIN.SELF_FUNDED_SEASONS * FIN.seeded_losses(g, TOUR_BY_KEY[g.tour].tier)]
        poor = [g for g in tour_pros if g not in rich]
        self.assertTrue(rich and poor)
        self.assertFalse([g.id for g in rich if g.backer])                 # savings pay for their chase
        self.assertGreater(sum(1 for g in poor if g.backer) / len(poor), 0.2)   # many who need it are

    def _unbacked(self):
        s = self.s
        return next(g for g in s.active_golfers() if g.status == 'pro' and g.lifestyle == 'full_time'
                    and not g.backer and g.age(2027) <= 26 and g.id in self.snap
                    and TOUR_BY_KEY[g.tour].tier == 4)                       # a mini-tour professional

    def test_an_unbacked_professional_who_runs_low_can_find_backers(self):
        s = self.s
        g = copy.deepcopy(self._unbacked())
        g.cash, g.backing = 0.0, 0.0
        row = dict(self.snap[g.id], wins=0, promoted=False)
        s.backer_ended.pop(g.id, None)
        self.assertLess(C.runway_years(s, g, 2027, g.tour, s.target_events(g), row, own_money=True), C.NEED_RUNWAY)
        lucky = mock.Mock(random=mock.Mock(return_value=0.0))
        self.assertEqual(C.review_backers(s, g, row, 2027, lucky), 'found backers')
        self.assertGreater(g.backer, 0)
        rich = copy.deepcopy(self._unbacked())
        rich.cash = 5_000_000.0                                              # does not need them
        self.assertIsNone(C.review_backers(s, rich, row, 2027, lucky))
        again = copy.deepcopy(self._unbacked())
        again.cash, again.backing = 0.0, 0.0
        s.backer_ended[again.id] = 2026                                      # a deal ended last winter
        try:
            self.assertIsNone(C.review_backers(s, again, row, 2027, lucky))
        finally:
            s.backer_ended.pop(again.id, None)


class AmateurForecastTests(unittest.TestCase):
    def test_an_amateurs_forecast_income_is_what_an_amateur_can_receive(self):
        """Sponsor contracts and prize money are for professionals: an amateur's forecast must not count
        them, however famous the amateur."""
        s = Season(generate_world(seed=12, scale=0.2), seed=12, development=True, workers=1)
        am = max((g for g in s.world.golfers if g.status == 'amateur' and g.lifestyle != 'retired'),
                 key=lambda g: s.player_prestige(g.id))
        plain = copy.deepcopy(am)
        s.legacy[plain.id], fame = 0.0, s.fame.get(am.id, 0.0)
        shortfall_famous = C.season_shortfall(s, am, am.tour, 8)
        s.fame[am.id] = 0.0
        shortfall_plain = C.season_shortfall(s, am, am.tour, 8)
        s.fame[am.id] = fame
        self.assertGreater(s.player_prestige(am.id), 0)
        self.assertEqual(shortfall_famous, shortfall_plain)                  # prestige buys an amateur nothing
        s.start_finances(2027)
        self.assertNotIn(am.id, s.contracts)                                 # and nothing is paid
        self.assertEqual(s.expected_prize(am, next(x for x in s.cal.series if x.purse)), 0.0)


if __name__ == '__main__':
    unittest.main()
