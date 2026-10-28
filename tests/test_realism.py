"""Realism checks: money before spending, smooth career odds, season-transition evidence, honest
qualification, development without hidden knowledge, and exact payout accounting.

Most tests are counterfactual: the same golfer in the same situation with one thing changed (money,
age, results, population order), so they test the mechanism rather than a tuned outcome.

Run from the project folder:  python -m unittest discover -s tests -v
"""
from __future__ import annotations

import copy
import random
import statistics as S
import sys
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from golfsim import careers as C                                      # noqa: E402
from golfsim import development as D                                  # noqa: E402
from golfsim import finance as FIN                                    # noqa: E402
from golfsim import prestige as PR                                    # noqa: E402
from golfsim import qualification as Q                                # noqa: E402
from golfsim.calendar import TOUR_BY_KEY                              # noqa: E402
from golfsim.population import generate_world                         # noqa: E402
from golfsim.season import PREMIER_TOURS, Season                      # noqa: E402

SEASON = Season(generate_world(seed=11), seed=11, development=True, workers=1)


def set_record(s, g, share):
    """A proven earnings record (20 events) at the golfer's own level."""
    s.prize_record[g.id] = {tier(g) if g.tour in TOUR_BY_KEY else 4: [share, 20]}


def tier(g):
    return TOUR_BY_KEY[g.tour].tier if g.tour in TOUR_BY_KEY else 9


def full_timers(s, t, n=60):
    return [g for g in s.world.golfers if g.status == 'pro' and g.lifestyle == 'full_time' and tier(g) == t][:n]


def at_age(g, age, year=2027):
    g = copy.deepcopy(g)
    g.born = year - age
    return g


# ---- 1. money before spending ------------------------------------------------------------------------
class FundingTests(unittest.TestCase):
    def test_credit_is_limited_and_based_on_earnings(self):
        self.assertEqual(FIN.credit_limit(0), FIN.CREDIT_BASE)
        self.assertEqual(FIN.credit_limit(10 ** 9), FIN.CREDIT_CAP)            # no unlimited borrowing
        s = SEASON
        g = full_timers(s, 4)[0]
        base = s.funds(g, 2027)
        s.ledger(2026, g.id).support = 10 ** 6                                # family money is not income
        self.assertEqual(s.funds(g, 2027), base)
        s.ledgers[2026].pop(g.id)

    def test_trips_need_funds_counterfactual(self):
        """The same mini-tour players plan no tournaments when they cannot pay, and do when they can."""
        s = SEASON
        group = full_timers(s, 4, 80)
        saved = {g.id: (g.cash, g.backing) for g in group}
        for g in group:
            g.backing = 0.0
            g.cash = -FIN.credit_limit(0) - 5000                           # nothing left to draw on
        s.plan_block(2027, 1)
        broke = {g.id: [a for a, _ in s.plans[g.id].values()] for g in group}
        for g in group:
            g.cash = 10 ** 6
        s.plan_block(2027, 1)
        rich = {g.id: [a for a, _ in s.plans[g.id].values()] for g in group}
        for g in group:
            g.cash, g.backing = saved[g.id]
        self.assertTrue(all('play' not in acts for acts in broke.values()))
        self.assertTrue(all('work' in acts for acts in broke.values()))       # they work instead
        self.assertGreater(sum('play' in acts for acts in rich.values()), len(group) // 2)

    def test_no_debt_trap_just_short_of_a_trip(self):
        """A card holder whose funds sit just below the price of any trip works to get back on the
        road, even if their past prize record looks good (regression: they used to train and wait)."""
        s = SEASON
        week0 = next(w for w in range(1, 49, 4)
                     if any(e.week in range(w, w + 4) and e.series.tour.startswith('RG_') for e in s.cal.editions(2027)))
        group = [g for g in full_timers(s, 3, 300)
                 if any(e.week in range(week0, week0 + 4) and e.series.tour == g.tour for e in s.cal.editions(2027))][:40]
        saved = {g.id: (g.cash, g.backing) for g in group}
        for g in group:
            g.backing = 0.0
            set_record(s, g, 0.05)                                           # a good record
            g.cash = 0.0
            g.cash = 300.0 - s.spendable(g, 2027)                            # $300 to spend: no trip costs that little
        s.plan_block(2027, week0)
        for g in group:
            g.cash, g.backing = saved[g.id]
            del s.prize_record[g.id]
        self.assertTrue(all('work' in [a for a, _ in s.plans[g.id].values()] for g in group))

    def test_a_season_without_events_counts_against_the_record(self):
        s = SEASON
        g = copy.deepcopy(full_timers(s, 3)[0])
        g.cash, g.backing = 5000.0, 0.0
        set_record(s, g, 0.0)
        _, costs = s.season_forecast(g, g.tour, 20)
        ss = [x for x in s.cal.series if x.tour == g.tour and x.purse]
        purse = sum(x.purse for x in ss) / len(ss)
        share = 1.2 * costs / (20 * purse * s.prize_kept(g))                 # a record that pays its way
        set_record(s, g, share)
        played = C.runway_years(s, g, 2027, g.tour, 20, {'prize_by_tier': {tier(g): (share * 20 * purse, 20)},
                                                            'tier': tier(g)})
        idle = C.runway_years(s, g, 2027, g.tour, 20, {'prize_by_tier': {}, 'tier': tier(g)})
        del s.prize_record[g.id]
        self.assertLess(idle, played)

    def test_a_cheaper_event_is_still_an_option(self):
        """If the event a golfer would prefer is out of reach, an affordable eligible event that week
        is still considered (the week is not written off)."""
        s = SEASON
        g = full_timers(s, 4)[0]
        venues = s.lib.venues(2027)
        eds = [e for e in s.cal.editions(2027) if e.series.tier == 4][:2]
        city = {e.event_id: venues[e.event_id][0].city for e in eds}
        costs = {e.event_id: s.trip_cost(g, e.series, city[e.event_id]) for e in eds}
        dear, cheap = sorted(eds, key=lambda e: -costs[e.event_id])
        opts = [(10.0, dear.event_id, dear), (5.0, cheap.event_id, cheap)]  # the dear one preferred
        if costs[dear.event_id] == costs[cheap.event_id]:
            self.skipTest('no price difference between these events')
        money = (costs[dear.event_id] + costs[cheap.event_id]) / 2
        self.assertIs(s.best_affordable(g, opts, city, money)[0][1], cheap)
        self.assertIs(s.best_affordable(g, opts, city, costs[dear.event_id])[0][1], dear)
        self.assertIsNone(s.best_affordable(g, opts, city, costs[cheap.event_id] - 1))

    def test_open_entry_does_not_favour_low_ids(self):
        """Unranked members of a full mini tour get in by a fair draw, not by how golfers are numbered
        (regression: new professionals, who have the highest ids, were always shut out)."""
        s = SEASON
        series = next(x for x in s.cal.series if x.tier == 4)
        members = sorted((g for g in s.world.golfers if g.tour == series.tour and g.status == 'pro'), key=lambda g: g.id)
        order = sorted(members, key=lambda g: s.priority(g, series))
        rank = {g.id: i for i, g in enumerate(order)}
        n = len(members)
        first_half_ids = [g.id for g in members[: n // 2]]
        share = sum(1 for gid in first_half_ids if rank[gid] < n // 2) / max(1, len(first_half_ids))
        self.assertTrue(0.3 < share < 0.7, share)                            # about half, by chance
        ranked_out = s.priority(members[0], series)[1]
        self.assertEqual(ranked_out, 0)                                      # mini tours ignore ranking

    def test_same_world_whatever_the_number_of_workers(self):
        def run(workers):
            s = Season(generate_world(seed=17), seed=17, development=True, workers=workers)
            s.refresh_people(2027)
            s.start_finances(2027)
            eds = s.cal.editions(2027)
            for w in (1, 2, 3):
                s.run_week(2027, w, [e for e in eds if e.week == w])
            s.close()
            return ({k: r.finish for k, r in s.results.items()},
                    {g.id: (round(g.cash, 6), round(g.overall, 9)) for g in s.world.golfers},
                    dict(s.staff.coach_of), dict(s.staff.caddie_of))
        self.assertEqual(run(1), run(2))

    def test_a_challenger_card_is_no_financial_immunity(self):
        s = SEASON
        g = min(full_timers(s, 2, 400), key=lambda x: (s.player_prestige(x.id), x.id))   # no sponsor to lean on
        row = {'status': 'pro', 'tier': 2, 'events': 20}
        set_record(s, g, 0.0)                                                # their results earn nothing
        rich, broke = copy.deepcopy(g), copy.deepcopy(g)
        rich.cash, broke.cash, broke.backing = 10 ** 7, -10 ** 6, 0.0
        p_rich, _ = C.p_stop_chasing(s, rich, row, 2027)
        p_broke, why = C.p_stop_chasing(s, broke, row, 2027)
        self.assertEqual(why['runway'], 0.0)
        self.assertGreater(p_broke, 0.3)
        self.assertLess(p_rich, 0.1)
        mini = copy.deepcopy(broke)
        mini.tour = full_timers(s, 4)[0].tour
        self.assertGreater(C.p_stop_chasing(s, mini, row, 2027)[0], p_broke)  # a better card still helps
        del s.prize_record[g.id]


# ---- 2. smooth, individual career odds ---------------------------------------------------------------
class CareerOddsTests(unittest.TestCase):
    def setUp(self):
        self.s = SEASON
        self.g = copy.deepcopy(full_timers(self.s, 4)[3])
        self.g.backing, self.g.cash, self.g.backer = 0.0, 30000.0, 0.0
        self.row = {'status': 'pro', 'tier': 4, 'events': 15, 'top10': 1}

    def test_no_age_cliffs(self):
        ps = [C.p_stop_chasing(self.s, at_age(self.g, a), self.row, 2027)[0] for a in range(18, 61)]
        for a, (p0, p1) in enumerate(zip(ps, ps[1:]), 18):
            self.assertGreaterEqual(p1, p0 - 1e-12, a)                       # never less likely with age
            self.assertLess(p1 / p0, 1.6, a)                                 # and never a jump
        self.assertGreater(ps[28 - 18], 2 * ps[22 - 18])                     # the mid-twenties shift the odds

    def test_no_debt_cliff(self):
        ps = []
        for cash in range(20000, -120001, -2000):
            g = copy.deepcopy(self.g)
            g.cash = cash
            ps.append(C.p_stop_chasing(self.s, at_age(g, 25), self.row, 2027)[0])
        for p0, p1 in zip(ps, ps[1:]):
            self.assertGreaterEqual(p1, p0 - 1e-12)
            self.assertLess(p1 - p0, 0.06)

    def test_contrasting_career_arcs(self):
        """The same 27-year-old in four situations. Finances matter, but a golfer who is improving, has
        earned a better card or secured a big event may accept another losing season; nothing about
        that desire creates money."""
        s = self.s
        stagnant = dict(self.row)
        improving = dict(self.row, promoted=True, wins=2, top10=5, wr_start=900, wr_end=300)
        secured = dict(self.row, secured=['world top 50 (Tour Masters invitation)'])
        challenger = full_timers(s, 2)[0].tour
        def golfer(cash, tour=None):
            g = at_age(self.g, 27)
            g.cash = cash
            if tour:
                g.tour = tour                                                # the card earned for next season
            return g
        p = lambda g, row: C.p_stop_chasing(s, g, row, 2027)[0]
        broke, funded = -10 ** 6, 10 ** 6
        b = golfer(broke)
        before = s.funds(b, 2027)
        p_improving = p(golfer(broke, challenger), improving)
        self.assertEqual(s.funds(b, 2027), before)                           # desire creates no money
        self.assertLess(p_improving, 0.6 * p(b, stagnant))                   # willing to accept a losing season
        self.assertGreater(p_improving, p(golfer(funded, challenger), improving))   # money still matters
        self.assertGreater(p_improving, 0.01)                                # and nothing is guaranteed
        self.assertLess(p(golfer(broke), secured), p(b, stagnant))           # a secured major counts
        self.assertLess(p(golfer(funded), stagnant), p(b, stagnant))
        hurt = dict(stagnant, injury_weeks=30)
        self.assertGreater(p(b, hurt), p(b, stagnant))                       # health counts

    def test_part_timers_stop_for_their_own_reasons_not_to_fit_the_world(self):
        """Participation, opportunity, progress, health and willingness decide; not being able to find
        events is not the same as choosing not to play."""
        from collections import Counter
        s = self.s
        part = at_age(copy.deepcopy(self.g), 30)
        part.lifestyle = 'part_time'
        weeks = lambda **c: Counter({k.replace('_', ' ').replace('none', 'no suitable event scheduled'): v
                                     for k, v in c.items()})
        def p(row, access, g=part):
            s.week_access[2027][g.id] = access
            try:
                return C.p_retire(s, g, row, 2027)
            finally:
                s.week_access[2027].pop(g.id, None)
        played = {'status': 'pro', 'tier': 4, 'events': 8}
        idle = {'status': 'pro', 'tier': 4, 'events': 0}
        options = weeks(**{'chose to work': 40, 'chose to rest': 12})          # events there, chose not to
        none = weeks(**{'no suitable event scheduled': 45, 'chose to work': 7})  # nothing they could enter
        regular = p(played, weeks(**{'played: first choice': 8, 'chose to work': 44}))
        self.assertLess(regular, 0.08)                                      # keen part-timers keep playing
        self.assertGreater(p(idle, options), p(idle, none))                 # drifting away vs shut out
        self.assertGreater(p(idle, none), regular)
        keen = copy.deepcopy(part)
        keen.personality.update(work_ethic=90, big_stage=90)
        self.assertLess(p(idle, options, keen), p(idle, options))           # willingness counts
        better = dict(played, wr_start=3000, wr_end=1500, top10=2)
        self.assertLess(p(better, weeks(**{'played: first choice': 8})), regular)    # and progress
        self.assertGreater(p(dict(played, injury_weeks=20), weeks(**{'injured': 20})), regular)   # and health

    def test_retirement_and_comebacks_have_no_age_or_cash_switches(self):
        s = self.s
        part = copy.deepcopy(self.g)
        part.lifestyle = 'part_time'
        row = {'status': 'pro', 'tier': 4, 'events': 3, 'wins': 1, 'top3': 2}
        rets = [C.p_retire(s, at_age(part, a), row, 2027) for a in range(20, 75)]
        self.assertGreater(rets[0], 0)                                       # no floor at 26
        self.assertTrue(all(r1 >= r0 and r1 / r0 < 1.2 for r0, r1 in zip(rets, rets[1:])))
        cbs = [C.p_comeback(s, at_age(part, a), row, 2027) for a in range(25, 56)]
        self.assertGreater(cbs[-1], 0)                                       # no cut-off at 40
        self.assertTrue(all(c1 <= c0 and c1 / c0 > 0.8 for c0, c1 in zip(cbs, cbs[1:])))
        lo, hi = copy.deepcopy(part), copy.deepcopy(part)
        lo.cash, hi.cash = 19000, 21000                                      # no $20,000 threshold
        self.assertAlmostEqual(C.p_comeback(s, lo, row, 2027), C.p_comeback(s, hi, row, 2027), delta=0.01)

    def test_college_eligibility_is_a_rule_not_a_choice(self):
        s = Season(generate_world(seed=12), seed=12, development=True, workers=1)
        col = [g for g in s.world.golfers if g.tour == 'CO_US_D1']
        old, young = col[:40], col[40:80]
        for g in old:
            g.born = 2027 - 22
        for g in young:
            g.born = 2027 - 20
        C.decide(s, 2027, s.season_snapshot(2027))
        self.assertTrue(all(not g.tour.startswith('CO_') for g in old))
        self.assertTrue(all(g.tour == 'CO_US_D1' or g.status == 'pro' for g in young))

    def test_decisions_do_not_depend_on_population_order(self):
        def run(reverse):
            s = Season(generate_world(seed=13), seed=13, development=True, workers=1)
            if reverse:
                s.world.golfers.reverse()
            for g in s.world.golfers:
                if g.status == 'pro' and tier(g) == 4:
                    g.cash -= 40000
            snap = s.season_snapshot(2027)
            C.decide(s, 2027, snap)
            return snap, {g.id: (g.status, g.lifestyle, g.tour) for g in s.world.golfers}
        snap_a, a = run(False)
        snap_b, b = run(True)
        self.assertEqual(snap_a, snap_b)
        self.assertEqual(a, b)


# ---- 3. season-transition evidence --------------------------------------------------------------------
class BackerTests(unittest.TestCase):
    def setUp(self):
        self.s = SEASON
        self.g = copy.deepcopy(full_timers(self.s, 4)[5])
        self.g.backing, self.g.cash, self.g.backer, self.g.backer_stale = 0.0, 0.0, 0.0, 0
        self.flat = {'status': 'pro', 'tier': 4, 'events': 20, 'top10': 0, 'wr_start': 2000, 'wr_end': 2100}
        self.good = dict(self.flat, wr_end=1200, top10=3)

    def test_most_new_professionals_find_backers_and_a_record_helps(self):
        r = random.Random(1)
        share = lambda st: S.mean(FIN.backer_deal(22, st, r.random(), r.random()) > 0 for _ in range(4000))
        self.assertAlmostEqual(share(0.4), 0.76, delta=0.04)
        self.assertGreater(share(0.9), share(0.1))
        deals = [FIN.backer_deal(22, 0.5, 0.0, r.random()) for _ in range(500)]
        self.assertTrue(all(FIN.BACKER_MIN <= d <= FIN.BACKER_MAX for d in deals))

    def test_backers_take_their_share_of_winnings(self):
        g = self.g
        kept = self.s.prize_kept(g)
        g.backer = 30000.0
        self.assertAlmostEqual(self.s.prize_kept(g), kept - FIN.BACKER_SHARE)
        led = FIN.Ledger()
        led.prize, led.backer_share = 1000.0, FIN.BACKER_SHARE * 1000.0
        self.assertAlmostEqual(led.net, 750.0)                               # in the ledger: cash reconciles

    def test_backers_renew_on_progress_and_lose_patience_without_it(self):
        g = at_age(self.g, 24)
        g.backer = 30000.0
        good = C.p_backers_continue(self.s, g, self.good, 2027)
        flat1 = C.p_backers_continue(self.s, g, self.flat, 2027)
        g.backer_stale = 2
        flat3 = C.p_backers_continue(self.s, g, self.flat, 2027)
        self.assertGreater(good, 0.85)                                      # progress: almost always renewed
        self.assertTrue(good > flat1 > flat3 > 0.02, (good, flat1, flat3))
        h = copy.deepcopy(g)
        while C.review_backers(self.s, h, self.flat, 2027, random.Random(h.backer_stale)) is None and h.backer_stale < 12:
            pass
        self.assertEqual((h.backer, h.backer_funds), (0.0, 0.0))            # withdrawn in the end, recorded
        self.assertIn('backers withdrew', self.s.history[h.id][-1][2].lower())

    def test_independence_is_judged_without_the_support_being_withdrawn(self):
        """A losing golfer with a large family pot and credit is not 'paying their own way'; a golfer
        whose own expected winnings cover a season's costs is."""
        rng = random.Random(4)
        g = at_age(self.g, 24)
        g.backer, g.backing = 30000.0, 10 ** 6                               # rich family, no winnings
        set_record(self.s, g, 0.0)
        self.assertNotEqual(C.review_backers(self.s, g, self.good, 2027, rng), 'backers no longer needed')
        self.assertEqual(g.backer, 30000.0)
        h = at_age(self.g, 24)
        h.backer, h.cash = 30000.0, 20000.0                                  # can pay for the season's start
        set_record(self.s, h, 0.15)                                          # winning enough to pay the way
        try:
            self.assertEqual(C.review_backers(self.s, h, self.good, 2027, rng), 'backers no longer needed')
            self.assertIn('winnings', self.s.history[h.id][-1][2])          # and the reason given is true
        finally:
            self.s.prize_record.pop(h.id, None)
            self.s.prize_record.pop(g.id, None)

    def test_backers_money_goes_back_when_the_deal_ends(self):
        """Backers' money and family money are kept apart: when a deal ends the undrawn backers' money
        goes back with it (and so does their share of winnings); family money stays the golfer's."""
        s, g = self.s, at_age(self.g, 24)
        g.backer, g.backing, g.cash = 30000.0, 5000.0, 0.0
        s.start_backing(g)                                                   # 1 January: this season's money
        self.assertEqual((g.backer_funds, g.backing), (30000.0, 5000.0))
        with_deal = s.funds(g, 2027)
        C.end_backing(s, g, 2027, 'Their backers withdrew')
        self.assertEqual((g.backer, g.backer_funds, g.backing), (0.0, 0.0, 5000.0))
        self.assertAlmostEqual(with_deal - s.funds(g, 2027), 30000.0)
        self.assertAlmostEqual(s.prize_kept(g), 1.0 - (FIN.CADDIE_SHARE if s.staff.caddie(g.id) is not None else 0.0)
                               - (C.ST.SCOUT_SHARE if s.staff.deal.get(g.id) == 'share' else 0.0))

    def test_no_age_cliff_and_no_universal_two_season_rule(self):
        """Backers decide with bounded odds: progress, secured opportunities, how far the season's losses
        outrun the deal, their own patience, flat seasons and age all count; none ends every deal."""
        def keeps(g, row, n=300):
            kept = 0
            for i in range(n):
                h = copy.deepcopy(g)
                if C.review_backers(self.s, h, row, 2027, random.Random(i)) is None and h.backer:
                    kept += 1
            return kept / n
        g = at_age(self.g, 34)
        g.backer = 30000.0
        self.assertGreater(keeps(g, self.good), 0.6)                        # a 34-year-old making progress
        g = at_age(self.g, 25)
        g.backer, g.backer_stale = 30000.0, 1                               # a second flat season
        flat2 = keeps(g, self.flat)
        self.assertTrue(0.1 < flat2 < 0.9, flat2)                           # likely to end, not certain
        g.backer_patience = 0.95
        self.assertGreater(keeps(g, self.flat), flat2)                      # patient backers wait longer
        p = [C.p_backers_continue(self.s, at_age(g, a), self.good, 2027) for a in range(24, 46)]
        self.assertTrue(all(p1 <= p0 and p1 / p0 > 0.8 for p0, p1 in zip(p, p[1:])))   # smooth in age
        self.assertGreater(p[-1], 0.02)
        secured = dict(self.flat, secured=['USA_OPEN'])
        self.assertGreater(C.p_backers_continue(self.s, g, secured, 2027), C.p_backers_continue(self.s, g, self.flat, 2027))

    def test_finding_backers_declines_smoothly_with_age(self):
        r = random.Random(2)
        share = lambda age: S.mean(FIN.backer_deal(age, 0.4, r.random(), r.random()) > 0 for _ in range(3000))
        shares = [share(a) for a in (22, 26, 30, 32, 34, 38)]
        self.assertTrue(all(b < a for a, b in zip(shares, shares[1:])), shares)
        self.assertGreater(shares[3], 0.4 * shares[2])                     # no step at 33
        self.assertGreater(shares[-1], 0.0)

    def test_credit_does_not_fund_another_season_but_backers_do(self):
        g = at_age(self.g, 25)
        g.cash = -5000.0
        p_broke = C.p_stop_chasing(self.s, g, self.flat, 2027)[0]
        led = self.s.ledger(2027, g.id)                                      # a big year: a big credit line
        saved = led.work
        led.work = 200000.0
        p_credit = C.p_stop_chasing(self.s, g, self.flat, 2027)[0]
        led.work = saved
        self.assertAlmostEqual(p_broke, p_credit)
        g.backer = 40000.0
        self.assertLess(C.p_stop_chasing(self.s, g, self.flat, 2027)[0], p_broke)


class TransitionTests(unittest.TestCase):
    def test_ties_share_a_rank_whatever_the_population_order(self):
        s = Season(generate_world(seed=14), seed=14, workers=1)
        members = [g for g in s.world.golfers if g.tour == 'CH_EUROPE' and g.lifestyle == 'full_time']
        for i, g in enumerate(members):
            s.money[('CH_EUROPE', 2027)][g.id] = 50000.0 if i < 4 else 100.0 * (len(members) - i)
        snap = s.season_snapshot(2027)
        tied = [snap[g.id]['money_rank'] for g in members[:4]]
        self.assertEqual(tied, [2.5] * 4)                                    # ranks 1-4 shared
        s.world.golfers.reverse()
        self.assertEqual(s.season_snapshot(2027), snap)
        m = s.money[('CH_EUROPE', 2027)]
        order = sorted((g.id for g in members[:4]), key=lambda gid: s.standing_key(m, gid))
        self.assertEqual(order, sorted(order, key=lambda gid: (s.wr_pos.get(gid, 10 ** 6), gid)))

    def test_evidence_is_taken_before_cards_change(self):
        s = Season(generate_world(seed=15), seed=15, workers=1)
        members = [g for g in s.world.golfers if g.tour == 'CH_AMERICAS' and g.lifestyle == 'full_time']
        for i, g in enumerate(members):
            s.money[('CH_AMERICAS', 2027)][g.id] = 10000.0 * (len(members) - i)
        s.end_of_season(2027)
        snap = s.snapshots[2027]
        top = members[:25]
        for i, g in enumerate(top):
            row = snap[g.id]
            self.assertEqual(row['tour'], 'CH_AMERICAS')                     # the tour they played on
            self.assertEqual(row['money_rank'], i + 1)                       # ranked among its members
            self.assertIn(row['next_tour'], PREMIER_TOURS)
            self.assertTrue(row['promoted'])
        for gid, row in snap.items():
            new = TOUR_BY_KEY[row['next_tour']].tier if row['next_tour'] in TOUR_BY_KEY else 9
            self.assertEqual(row['promoted'], new < row['tier'])


# ---- 4. honest qualification --------------------------------------------------------------------------
VALID_ROUTES = {r.code for rules in Q.RULES.values() for r in rules} | {'ALT', 'INIT'}


class QualificationTests(unittest.TestCase):
    def test_every_major_entrant_has_a_route(self):
        s = SEASON
        for sid in Q.MAJOR_SERIES:
            ids = s.major_field(sid, 2027, Q.MAJOR_WEEK[sid])
            routes = s.entry_routes[(2027, sid)]
            self.assertEqual(len(ids), len(set(ids)))
            self.assertEqual(set(ids), set(routes))
            self.assertTrue(set(routes.values()) <= VALID_ROUTES)
            if sid != 'TOUR_MASTERS':
                self.assertNotIn('INIT', routes.values())

    def test_inaugural_invitations_are_first_season_only(self):
        s = SEASON
        first = s.major_field('TOUR_MASTERS', 2027, 18)
        first_routes = s.entry_routes[(2027, 'TOUR_MASTERS')]
        self.assertIn('INIT', first_routes.values())
        s.first_year = 2026                                                  # pretend history exists
        try:
            later = s.major_field('TOUR_MASTERS', 2027, 18)
        finally:
            s.first_year = 2027
        routes = s.entry_routes[(2027, 'TOUR_MASTERS')]
        self.assertNotIn('INIT', routes.values())                           # no fill-to-90 fallback
        self.assertLess(len(later), len(first))
        self.assertEqual(set(later), {gid for gid in first if first_routes[gid] != 'INIT'})

    def test_withdrawals_are_replaced_by_recorded_alternates_only(self):
        s = SEASON
        ids = s.major_field('USA_OPEN', 2027, Q.MAJOR_WEEK['USA_OPEN'])
        out = ids[0]
        s.injured[out] = (10 ** 6, 'test', 1)
        try:
            again = s.major_field('USA_OPEN', 2027, Q.MAJOR_WEEK['USA_OPEN'])
        finally:
            del s.injured[out]
        self.assertNotIn(out, again)
        new = set(again) - set(ids)
        self.assertTrue(all(s.entry_routes[(2027, 'USA_OPEN')][gid] == 'ALT' for gid in new))

    def test_premier_tour_championship_withdrawals_are_replaced_in_order(self):
        s = SEASON
        sid = 'PREMIER_TOUR_CHAMPIONSHIP'
        f = Q.build_field(sid, 2027, s.ctx)
        self.assertEqual(len(f.entries), 156)
        self.assertGreaterEqual(len(f.alternates), 10)                       # ordered reserves kept
        out = [e.golfer_id for e in f.entries[:3]] + [e.golfer_id for e in f.entries if e.primary == 'PF'][:3]
        out += f.alternates[:1]                                              # a reserve who is hurt too
        for gid in out:
            s.injured[gid] = (10 ** 6, 'test', 1)
        try:
            ids = s.major_field(sid, 2027, Q.MAJOR_WEEK[sid])
        finally:
            for gid in out:
                del s.injured[gid]
        self.assertEqual(len(ids), 156)                                      # the field is full again
        routes = s.entry_routes[(2027, sid)]
        alts = [gid for gid in ids if routes[gid] == 'ALT']
        self.assertEqual(alts, f.alternates[1:7])                            # the next six, in order
        self.assertTrue(not set(out) & set(ids))

    def test_club_pro_championship_comes_from_sectional_results(self):
        s = SEASON
        ed = next(e for e in s.cal.editions(2027) if e.series.series_id == 'CLUB_PRO_CHAMPIONSHIP')
        clubs = sorted(g.id for g in s.world.golfers if g.status == 'club_pro')
        sites = [clubs[i::4] for i in range(4)]

        def field(order):
            for k, ids in enumerate(sites):
                s.ctx.add_result('CLUB_PRO_SECTIONALS', 2027, [(gid, i + 1) for i, gid in enumerate(order(ids))], site=k)
            return s.club_pro_championship(ed, 2027, lambda g: True)[0]
        a = field(lambda ids: ids)
        b = field(lambda ids: ids[::-1])
        s.ctx.results.pop(('CLUB_PRO_SECTIONALS', 2027))
        self.assertLessEqual(len(a), ed.series.field)
        for ids in sites:                                                    # each site's best finishers advance
            chosen = [gid for gid in ids if gid in set(a)]
            self.assertEqual(chosen, ids[:len(chosen)])
            self.assertGreater(len(chosen), 0)
        self.assertLess(len(set(a) & set(b)), len(a) // 2)                   # results decide, not ratings
        self.assertTrue(all(r.startswith('SECTIONAL') for r in s.entry_routes[(2027, 'CLUB_PRO_CHAMPIONSHIP')].values()))


# ---- 5. development ----------------------------------------------------------------------------------
class SecuredPlacesTests(unittest.TestCase):
    """Next season's major places come from the majors' own rules applied to what is known at the end
    of the season: earned invitations and continuing exemptions count, ranking cut-offs still to come
    and qualifying do not, and an amateur title's place keeps its condition."""

    def test_secured_places_follow_the_qualification_rules(self):
        s = SEASON
        ctx = s.ctx
        pros = [g for g in s.world.golfers if g.status == 'pro' and g.lifestyle == 'full_time'
                and s.wr_pos.get(g.id, 9999) > 300 and g.tour not in PREMIER_TOURS]
        top10, recent, expired, other = pros[:4]
        ranked_55 = next(gid for gid in ctx.ranking(2027, 52)[50:60] if s.g[gid].status == 'pro')
        amateur = next(g for g in s.world.golfers if g.status == 'amateur' and g.lifestyle == 'full_time')
        added = {('USA_OPEN', 2027): {0: [(other.id, 1), (top10.id, 5)] + [(g.id, 30 + i) for i, g in enumerate(pros[4:10])]},
                 ('BRITANNIA_OPEN', 2023): {0: [(recent.id, 1)]},           # 5 years back from 2028: still exempt
                 ('USA_OPEN', 2017): {0: [(expired.id, 1)]},                # 10 years back: lapsed
                 ('USA_AMATEUR', 2027): {0: [(amateur.id, 1)]}}
        saved = {k: ctx.results.get(k) for k in added}
        ctx.results.update(added)
        try:
            snap = s.season_snapshot(2027)
        finally:
            for k, v in saved.items():
                if v is None:
                    ctx.results.pop(k, None)
                else:
                    ctx.results[k] = v
        self.assertIn('USA Open 2028: Top 10 and ties, last USA Open', snap[top10.id]['secured'])
        self.assertEqual(snap[top10.id]['wins'], 0)                          # earned without winning
        self.assertTrue(any(t.startswith('Tour Masters 2028: Major champions, last 5 years') for t in snap[recent.id]['secured']))
        self.assertTrue(any(t.startswith('Britannia Open 2028: Past Britannia Open champions') for t in snap[recent.id]['secured']))
        self.assertFalse(any('USA Open' in t for t in snap[expired.id]['secured']))
        self.assertFalse(snap[expired.id]['secured'])
        self.assertFalse(any('USA Open 2028' in t for t in snap[ranked_55]['secured']))   # top 60 cut-off still to come
        self.assertFalse(snap[amateur.id]['secured'])                       # nothing a professional could keep...
        self.assertIn('Tour Masters 2028: USA Amateur champion and runner-up (if still an amateur)',
                      snap[amateur.id]['secured_if'])                        # ...but the place, with its condition


class DevelopmentRealismTests(unittest.TestCase):
    def _golfer(self, age):
        g = copy.deepcopy(next(x for x in SEASON.world.golfers if x.age(2027) == age))
        g.potential = g.overall + 12
        D.init_ceilings(g, age, random.Random(3))
        return g

    def test_teenagers_mature_while_resting(self):
        g = self._golfer(19)
        before = dict(g.attrs)
        for _ in range(8):
            D.develop_week(g, 'rest', 19)
        self.assertTrue(all(g.attrs[k] > before[k] for k in D.CATEGORIES['physical'] if g.ceilings[k] > before[k]))
        self.assertTrue(all(g.attrs[k] == before[k] for k in D.CATEGORIES['putting']))
        adult = self._golfer(28)
        before = dict(adult.attrs)
        D.develop_week(adult, 'rest', 28)
        self.assertEqual(adult.attrs, before)

    def test_golfers_do_not_know_their_ceilings(self):
        gs = [self._golfer(20) for _ in range(1)] + [copy.deepcopy(g) for g in SEASON.world.golfers[:400] if g.ceilings]
        err = lambda g: S.mean(abs(D.perceived_gap(g, k) - (g.ceilings[k] - g.attrs[k])) for k in g.attrs)
        good = [g for g in gs if D.judgement(g) > 0.6]
        poor = [g for g in gs if D.judgement(g) < 0.4]
        self.assertGreater(S.mean(err(g) for g in gs), 0.5)                  # nobody reads it exactly
        self.assertGreater(S.mean(err(g) for g in poor), S.mean(err(g) for g in good))

    def test_diminishing_returns(self):
        raw, near = self._golfer(20), self._golfer(20)
        near.ceilings = {k: min(99.0, v + 1.0) for k, v in near.attrs.items()}
        self.assertGreater(D.develop_week(raw, 'train', 20, 'putting'), 3 * D.develop_week(near, 'train', 20, 'putting'))


# ---- 6. payout accounting ----------------------------------------------------------------------------
class PayoutTests(unittest.TestCase):
    def setUp(self):
        self.s = Season(generate_world(seed=16), seed=16, workers=1)
        self.pros = [g.id for g in self.s.world.golfers if g.status == 'pro'][:200]
        self.ams = [g.id for g in self.s.world.golfers if g.status == 'amateur'][:50]
        self.series = next(x for x in self.s.cal.series if x.tier == 3 and x.purse and x.cut_top)

    def pay(self, finish, **kw):
        s = replace(self.series, **kw)
        before = self.s.unpaid[2027]
        won = self.s.pay_out(s, finish, 2027)
        return won, self.s.unpaid[2027] - before, s.purse

    def test_purse_is_accounted_for_exactly(self):
        for n, cut in ((8, 0), (40, 30), (156, 65), (156, 0)):
            finish = [(gid, i + 1 if (not cut or i < cut) else None, 0) for i, gid in enumerate(self.pros[:n])]
            won, unpaid, purse = self.pay(finish, cut_top=cut)
            self.assertAlmostEqual(sum(won.values()) + unpaid, purse, places=6)
            self.assertGreaterEqual(unpaid, -1e-6)

    def test_amateurs_take_nothing_and_professionals_move_up(self):
        finish = [(self.ams[0], 1, 0)] + [(gid, i + 2, 0) for i, gid in enumerate(self.pros[:69])]
        won, _, purse = self.pay(finish, cut_top=70)
        self.assertNotIn(self.ams[0], won)
        self.assertAlmostEqual(won[self.pros[0]], PR.payout_shares(70)[0] * purse)

    def test_a_small_paid_list_does_not_inflate_shares(self):
        # a 65-place cut that only 20 professionals made (the rest of the places went to amateurs)
        finish = [(gid, i + 1, 0) for i, gid in enumerate(self.pros[:20])]
        finish += [(gid, 21 + i, 0) for i, gid in enumerate(self.ams[:45])]
        finish += [(gid, None, None) for gid in self.pros[20:111]]
        won, unpaid, purse = self.pay(finish, cut_top=65)
        self.assertAlmostEqual(won[self.pros[0]], PR.payout_shares(65)[0] * purse)
        self.assertGreater(unpaid, 0)

    def test_undersized_cut_field_keeps_the_paid_place_schedule(self):
        """Fewer starters than the cut: the intended schedule stands and unfilled places go unpaid,
        with ties sharing their places' money and amateurs taking none."""
        cut = 65
        places = min(cut, self.series.field)
        sh = PR.payout_shares(places)
        finish = [(self.pros[0], 1, 0), (self.ams[0], 2, 0), (self.pros[1], 3, 0), (self.pros[2], 3, 0)]
        finish += [(gid, i + 5, 0) for i, gid in enumerate(self.pros[3:30])]
        won, unpaid, purse = self.pay(finish, cut_top=cut)
        self.assertAlmostEqual(won[self.pros[0]], sh[0] * purse)
        self.assertNotIn(self.ams[0], won)
        self.assertAlmostEqual(won[self.pros[1]], won[self.pros[2]])
        self.assertAlmostEqual(won[self.pros[1]], (sh[1] + sh[2]) / 2 * purse)   # pros move up past the amateur
        self.assertAlmostEqual(unpaid, purse * sum(sh[30:]))                 # 30 pros paid, the rest unpaid
        self.assertAlmostEqual(sum(won.values()) + unpaid, purse, places=6)

    def test_ties_share_the_places_money(self):
        finish = [(self.pros[0], 1, 0), (self.pros[1], 2, 0), (self.pros[2], 2, 0)] + \
                 [(gid, i + 4, 0) for i, gid in enumerate(self.pros[3:60])]
        won, _, purse = self.pay(finish, cut_top=0)
        sh = PR.payout_shares(60)
        self.assertAlmostEqual(won[self.pros[1]], won[self.pros[2]])
        self.assertAlmostEqual(won[self.pros[1]], (sh[1] + sh[2]) / 2 * purse)


if __name__ == '__main__':
    unittest.main()
