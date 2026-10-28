"""Finance through the real season: forecasts, cards, backing and careers, as the engine runs them.

Run from the project folder:  python -m unittest discover -s tests -v
"""
from __future__ import annotations

import copy
import sys
import unittest
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
        s.start_year(2027)
        for w in range(1, 53):
            s.advance_week(2027, w)
        cls.before = {g.id: (g.backer, g.cash, g.tour) for g in s.world.golfers}
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
        unproven = [gid for gid in backed if s.g[gid].tour in TOUR_BY_KEY
                    and s.events_at_level(gid, TOUR_BY_KEY[s.g[gid].tour].tier) < FIN.PROVEN_EVENTS]
        self.assertTrue(unproven)
        for gid in unproven:                                                   # a new level is not an income yet
            why = self.decisions.get(gid, {}).get('kind')
            if why == 'backers no longer needed':
                why = next(t for y, w, t in reversed(s.history[gid]) if 'Paying their own way' in t)
                self.assertTrue('savings' in why or 'sponsor contract' in why, why)   # money they have, not hope
        unproven_poor = [gid for gid in unproven if gid in poor]
        self.assertTrue(unproven_poor)
        self.assertTrue(any(s.g[gid].backer for gid in unproven_poor))        # their backers stay with them
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
