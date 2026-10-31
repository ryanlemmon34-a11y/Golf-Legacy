"""Seasonal weather (roadmap G3, rules 2026-11-09): climate by place and time of year, wind direction against each
hole, mitigation by existing skills, no cancelled rounds, no country penalty, reproducible draws.

Run from the project folder:  python -m unittest tests.test_weather -v
"""
from __future__ import annotations

import random
import statistics as S
import sys
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from golfsim import season as SEA                                      # noqa: E402
from golfsim import weather as WX                                      # noqa: E402
from golfsim import engine as E                                         # noqa: E402
from golfsim.course import ashford_ridge, windy_links                  # noqa: E402
from golfsim.course_gen import generate_site                           # noqa: E402
from golfsim.engine import Conditions, Player, RoundStats, HoleState, play_hole, play_round  # noqa: E402
from golfsim.golfer import uniform_golfer                              # noqa: E402
from golfsim.rules import RULES, RULES_VERSION, VERSIONS               # noqa: E402

MID = ashford_ridge()
WINTER_N, SUMMER_N = 3, 29          # weeks in January and July


def at(city, country, style='Parkland', wind=9.0, course=MID):
    return replace(course, city=city, country=country, style=style, typical_wind=wind, name=f'{city} test')


def site(city, style='Parkland'):
    return generate_site('', city, 'standard', random.Random(7), set(), style)['layouts']['Championship']


def golfer(rating=75, **attrs):
    g = uniform_golfer(rating)
    return replace(g, attrs={**g.attrs, **attrs})


def mean_score(g, course, cond, n, seed):
    return sum(play_round(g, course, random.Random(seed * 100_003 + i), cond).score for i in range(n)) / n


class ClimateTests(unittest.TestCase):
    def test_hemispheres_have_opposite_seasons(self):
        for (n_city, n_ctry), (s_city, s_ctry) in ((('Southport', 'England'), ('Melbourne', 'Australia')),
                                                   (('Barcelona', 'Spain'), ('Perth', 'Australia')),
                                                   (('Bandon, Oregon', 'USA'), ('Christchurch', 'New Zealand'))):
            north, south = at(n_city, n_ctry), at(s_city, s_ctry)
            nw, nj = WX.seasonal(north, WINTER_N), WX.seasonal(north, SUMMER_N)
            sw, sj = WX.seasonal(south, SUMMER_N), WX.seasonal(south, WINTER_N)    # southern winter = July
            self.assertGreater(nw[0], nj[0], n_city)          # windier in its winter
            self.assertGreater(nw[1], nj[1], n_city)          # and wetter
            self.assertGreater(sw[0], sj[0], s_city)
            self.assertGreater(sw[1], sj[1], s_city)

    def test_southern_courses_read_the_table_six_months_on(self):
        for city, ctry in (('Melbourne', 'Australia'), ('Johannesburg', 'South Africa'), ('Cairns', 'Australia'),
                           ('Buenos Aires', 'Argentina')):
            c = at(city, ctry)
            cl = WX.climate_of(c)
            self.assertTrue(cl.south)
            for week in range(1, 53):
                local = (WX.month_of(week) + 6) % 12
                self.assertEqual(WX.seasonal(c, week)[1], WX.CLIMATE[cl.group][1][local])
        north = WX.climate_of(at('Southport', 'England'))
        self.assertFalse(north.south)

    def test_tropical_wet_season_is_local_summer(self):
        self.assertGreater(WX.seasonal(at('Bangkok', 'Thailand'), 32)[1], WX.seasonal(at('Bangkok', 'Thailand'), 3)[1])
        self.assertGreater(WX.seasonal(at('Cairns', 'Australia'), 3)[1], WX.seasonal(at('Cairns', 'Australia'), 32)[1])

    def test_mediterranean_summers_dry_deserts_dry(self):
        self.assertLess(WX.seasonal(at('Marbella', 'Spain'), SUMMER_N)[1], 0.05)
        self.assertLess(max(WX.seasonal(at('Dubai', 'United Arab Emirates'), w)[1] for w in range(1, 53)), 0.06)

    def test_nearby_courses_are_coherent(self):
        for a, b, ctry in (('St Andrews', 'Carnoustie', 'Scotland'), ('Southport', 'Hoylake', 'England'),
                           ('Sunningdale', 'Virginia Water', 'England'), ('Phoenix, Arizona', 'Scottsdale, Arizona', 'USA')):
            for w in range(1, 53):
                self.assertEqual(WX.seasonal(at(a, ctry), w), WX.seasonal(at(b, ctry), w), (a, b, w))

    def test_weeks_change_smoothly(self):
        for city, ctry in (('St Andrews', 'Scotland'), ('Perth', 'Australia'), ('Bangkok', 'Thailand')):
            c = at(city, ctry)
            for w in range(1, 52):
                (w0, p0), (w1, p1) = WX.seasonal(c, w), WX.seasonal(c, w + 1)
                self.assertLess(abs(w1 - w0) / w0, 0.2)
                self.assertLess(abs(p1 - p0), 0.09)

    def test_coastal_windier_than_inland_at_the_same_place_and_week(self):
        coast, inland = site('Southport'), site('Manchester')        # both oceanic England, same style
        self.assertEqual(coast.style, inland.style)
        for w in range(1, 53):
            self.assertGreater(WX.seasonal(coast, w)[0], WX.seasonal(inland, w)[0], w)
            self.assertEqual(WX.seasonal(coast, w)[1], WX.seasonal(inland, w)[1])
        # and the coast swings more through the year
        swing = lambda c: WX.seasonal(c, WINTER_N)[0] / WX.seasonal(c, SUMMER_N)[0]
        self.assertGreater(swing(coast), swing(inland))

    def test_links_wind_and_drainage_by_style(self):
        links, park = site('Carnoustie', 'Links'), site('Carnoustie', 'Parkland')
        self.assertGreater(WX.seasonal(links, 20)[0], WX.seasonal(park, 20)[0])
        self.assertLess(WX.soak(links), WX.soak(park))

    def test_draws_follow_the_climate(self):
        c = at('Melbourne', 'Australia', wind=12.0)
        for week in (WINTER_N, SUMMER_N):
            draws = [WX.draw_conditions(c, week, 4, 0.5, s) for s in range(1500)]
            winds = [d[r].wind_mph for d in draws for r in d]
            wet = sum(d[r].rain for d in draws for r in d) / len(winds)
            mean, p = WX.seasonal(c, week)
            self.assertAlmostEqual(S.fmean(winds), mean, delta=0.08 * mean + 0.3)
            self.assertAlmostEqual(wet, p, delta=0.03)
            self.assertTrue(all(w >= 0 for w in winds))

    def test_draws_are_deterministic_and_archived_exactly(self):
        c = at('Carnoustie', 'Scotland', 'Links', 16.0)
        a = WX.draw_conditions(c, 28, 4, 0.61234, 991)
        self.assertEqual(a, WX.draw_conditions(c, 28, 4, 0.61234, 991))
        self.assertNotEqual(a, WX.draw_conditions(c, 28, 4, 0.61234, 992))
        self.assertEqual(WX.draw_conditions(c, 28, 2, 0.61234, 991), {1: a[1], 2: a[2]})   # per (seed, round)
        for cond in a.values():
            row = WX.archived(cond)
            self.assertEqual(row, [cond.wind_mph, int(cond.rain), cond.pin_difficulty, cond.wind_from, cond.gust])
            back = Conditions(wind_mph=row[0], rain=bool(row[1]), pin_difficulty=row[2], wind_from=row[3],
                              gust=row[4])
            self.assertEqual(back, cond)                                  # archived weather does not drift

    def test_bearings_are_stable_and_links_run_out_and_back(self):
        links = windy_links()
        b = WX.hole_bearings(links)
        self.assertEqual(b, WX.hole_bearings(replace(links, layout='Club')))
        out = S.fmean([abs(((b[n] - b[n + 9]) + 180) % 360 - 180) for n in range(1, 10)])
        self.assertGreater(out, 120)                                       # holes 1-9 and 10-18 roughly opposite


class WindDirectionTests(unittest.TestCase):
    HOLE = 4                                                               # Ashford Ridge 4: long par 4

    def drives(self, wind_from, n=400, seed=3, cond_wind=20.0, holeno=None, g=None):
        holeno = holeno or self.HOLE
        hole = MID.holes[holeno - 1]
        cond = Conditions(wind_mph=cond_wind, wind_from=wind_from)
        g = g or golfer()
        st, rng = RoundStats(), random.Random(seed)
        for _ in range(n):
            pl = Player(g, MID, cond, None, rng)
            play_hole(pl, hole, holeno - 1, rng, st, 0.0, HoleState(), (0.0, 0.0))
        return S.fmean(st.drives), st.fairways / st.fairway_att

    def test_head_tail_and_cross_on_one_hole(self):
        b = WX.hole_bearings(MID)[self.HOLE]
        head, tail, cross = self.drives(b), self.drives(b + 180), self.drives(b + 90)
        self.assertLess(head[0], cross[0] - 5)                             # into the wind: shorter
        self.assertGreater(tail[0], cross[0] + 5)                          # downwind: longer
        # crosswind: wider lateral spread, fewer fairways than downwind (open, exposed hole 12)
        b12, g = WX.hole_bearings(MID)[12], golfer(ball_flight=50)
        self.assertLess(self.drives(b12 + 90, 2000, holeno=12, g=g)[1] + 0.02,
                        self.drives(b12 + 180, 2000, holeno=12, g=g)[1])
        terms = lambda frm: Player(golfer(), MID, Conditions(wind_mph=20.0, wind_from=frm), None,
                                   random.Random(1)).hw[self.HOLE]
        h, t, c = terms(b), terms(b + 180), terms(b + 90)
        self.assertGreater(c[0], h[0])                                     # spread: cross > head > tail
        self.assertGreater(h[0], t[0])
        self.assertGreater(t[3], 0.0)                                      # a tailwind takes the spin off
        self.assertEqual(h[3], 0.0)
        self.assertGreater(h[4], c[4])                                     # head: more long/short error
        self.assertGreater(c[5], h[5])                                     # cross: more left/right error
        self.assertGreater(h[1], 0.0)                                      # headwind distance loss...
        self.assertLess(h[2], h[1])                                        # ...only partly won back by control

    def test_opposing_holes_under_one_wind(self):
        b = WX.hole_bearings(MID)
        n1 = self.HOLE
        n2 = max((n for n in b if n != n1 and MID.holes[n - 1].par >= 4),
                 key=lambda n: abs(((b[n] - b[n1]) + 180) % 360 - 180))   # the hole most nearly opposite
        cond = Conditions(wind_mph=20.0, wind_from=b[n1])
        hw = Player(golfer(), MID, cond, None, random.Random(1)).hw
        dfac = lambda t: 1 - t[1] + t[2] * 0.75
        self.assertLess(dfac(hw[n1]), 1.0)                                 # hole n1 into the wind
        self.assertGreater(dfac(hw[n2]), 1.0)                              # the opposite hole downwind
        flip = Player(golfer(), MID, Conditions(wind_mph=20.0, wind_from=b[n1] + 180), None, random.Random(1)).hw
        self.assertGreater(dfac(flip[n1]), 1.0)
        self.assertLess(dfac(flip[n2]), 1.0)

    def test_direction_averages_to_the_speed_only_spread(self):
        import math
        dirs = [((math.cos(a), abs(math.sin(a)))) for a in [i * math.pi / 180 for i in range(360)]]
        avg = S.fmean(c + 0.85 * max(al, 0) + 0.30 * max(-al, 0) for al, c in dirs)
        self.assertAlmostEqual(avg, 1.0, delta=0.01)


def holes_played(cond, n, holeno=4, g=None, seed=3):
    """n plays of one hole (each by a different golfer id, so each has its own gusts): RoundStats."""
    g = g or golfer()
    st, rng = RoundStats(), random.Random(seed)
    for i in range(n):
        pl = Player(replace(g, id=i + 1), MID, cond, None, rng)
        play_hole(pl, MID.holes[holeno - 1], holeno - 1, rng, st, 0.0, HoleState(), (0.0, 0.0))
    return st


class GustTests(unittest.TestCase):
    def test_gustiness_follows_coast_and_month_within_bounds(self):
        coast, inland = site('Southport'), site('Manchester')
        draws = lambda c, wk: [x.gust for s in range(400) for x in WX.draw_conditions(c, wk, 4, 0.5, s).values()]
        for wk in (WINTER_N, SUMMER_N):
            self.assertGreater(S.fmean(draws(coast, wk)), S.fmean(draws(inland, wk)) + 0.04)
            self.assertTrue(all(WX.GUST_RANGE[0] <= x <= WX.GUST_RANGE[1] for x in draws(coast, wk)))
        self.assertGreater(S.fmean(draws(inland, WINTER_N)), S.fmean(draws(inland, SUMMER_N)))   # windier month

    def test_gusts_reproduce_from_the_archived_row(self):
        c = at('Carnoustie', 'Scotland', 'Links', 16.0)
        played = WX.draw_conditions(c, 30, 4, 0.55, 77)
        g = replace(golfer(), id=42)
        for r, cond in played.items():
            row = WX.archived(cond)
            replay = Conditions(wind_mph=row[0], rain=bool(row[1]), pin_difficulty=row[2], wind_from=row[3],
                                gust=row[4])
            self.assertGreater(replay.gust, 0)
            a = play_round(g, c, random.Random(r), cond, round_no=r)
            b = play_round(g, c, random.Random(r), replay, round_no=r)   # a resumed or replayed round
            self.assertEqual((a.holes, a.drives), (b.holes, b.drives))

    def test_gusts_have_their_own_stream(self):
        cond = Conditions(wind_mph=20.0, wind_from=90, gust=0.3)
        rng = random.Random(1)
        state = rng.getstate()
        pl = Player(golfer(), MID, cond, None, rng)
        self.assertGreater(pl.gust, 0)
        rng2 = random.Random(1)
        Player(golfer(), MID, Conditions(wind_mph=20.0, wind_from=90), None, rng2)
        self.assertEqual(rng.getstate(), rng2.getstate())                  # building a gusty player draws nothing extra
        self.assertNotEqual(state, rng.getstate())
        seq = lambda gid: [Player(replace(golfer(), id=gid), MID, cond, None, random.Random(0)).gust_draw()
                           for _ in range(1)]
        self.assertEqual(seq(5), seq(5))                                   # deterministic per golfer and round
        self.assertNotEqual(seq(5), seq(6))

    def test_gustier_rounds_vary_more_shot_to_shot(self):
        exposed = replace(MID, name='Exposed test', holes=tuple(replace(h, wind_exposure=1.0) for h in MID.holes))
        b = WX.hole_bearings(exposed)[4]
        g = golfer(ball_flight=40, striking_consistency=99, focus=99)      # few mishits: the wind shows

        def drives(gust):
            st, rng = RoundStats(), random.Random(3)
            for i in range(3000):
                pl = Player(replace(g, id=i + 1), exposed, Conditions(wind_mph=30.0, wind_from=b, gust=gust), None, rng)
                play_hole(pl, exposed.holes[3], 3, rng, st, 0.0, HoleState(), (0.0, 0.0))
            return st.drives
        steady, gusty = drives(0.05), drives(0.45)
        self.assertGreater(S.pstdev(gusty), 1.25 * S.pstdev(steady))       # (measured: 29.9 vs 20.2 yards)
        self.assertAlmostEqual(S.fmean(gusty), S.fmean(steady), delta=3.0)  # same mean wind, same mean drive
        # the shot terms themselves: each shot's distance factor and spread vary around the steady values
        pl = Player(replace(g, id=1), exposed, Conditions(wind_mph=30.0, wind_from=b, gust=0.45), None, random.Random(1))
        dfac = E.wind_distance(pl, exposed.holes[3])
        gs = [pl.gust_draw() for _ in range(4000)]
        self.assertAlmostEqual(S.fmean(dfac - (1 - dfac) * x for x in gs), dfac, delta=0.003)
        self.assertGreater(S.pstdev(dfac - (1 - dfac) * x for x in gs), 0.03)
        self.assertTrue(all(-0.9 <= x <= 0.9 for x in gs))                 # bounded: never a reversed wind

    def test_mean_wind_damage_preserved_at_equal_mean_speed(self):
        b = WX.hole_bearings(MID)[1]
        g = golfer()
        diff = S.fmean(mean_score(g, MID, Conditions(wind_mph=20.0, wind_from=b, gust=0.45), 400, seed)
                       - mean_score(g, MID, Conditions(wind_mph=20.0, wind_from=b, gust=0.0), 400, seed)
                       for seed in (5, 6))
        self.assertLess(abs(diff), 0.15)

    def test_gusts_felt_less_with_control_never_zero(self):
        cond = Conditions(wind_mph=20.0, wind_from=0, gust=0.4)
        felt = lambda g, cad=None: Player(g, MID, cond, cad, random.Random(1)).gust
        from golfsim.golfer import neutral_caddie
        weak, strong = felt(golfer(ball_flight=40, management=40)), felt(golfer(ball_flight=95, management=95))
        self.assertLess(strong, weak)
        self.assertGreater(strong, 0.2)
        self.assertLess(felt(golfer(), neutral_caddie(95)), felt(golfer(), neutral_caddie(30)))

    def test_no_gusts_in_calm_air_or_the_classic_model(self):
        for cond in (Conditions(wind_mph=0.0, wind_from=90, gust=0.4), Conditions(wind_mph=20.0, gust=0.4)):
            self.assertEqual(Player(golfer(), MID, cond, None, random.Random(1)).gust, 0.0)
        for i in range(4):                                                 # calm: the gust value changes nothing
            a = play_round(golfer(), MID, random.Random(i), Conditions(wind_mph=0.0, wind_from=90, gust=0.4))
            b = play_round(golfer(), MID, random.Random(i), Conditions(wind_mph=0.0))
            self.assertEqual((a.holes, a.drives), (b.holes, b.drives))
            a = play_round(golfer(), MID, random.Random(i), Conditions(wind_mph=20.0, gust=0.4))   # classic: ignored
            b = play_round(golfer(), MID, random.Random(i), Conditions(wind_mph=20.0))
            self.assertEqual((a.holes, a.drives), (b.holes, b.drives))


class MitigationTests(unittest.TestCase):
    def test_skill_reduces_wind_loss_without_immunity(self):
        b = WX.hole_bearings(MID)[1]
        windy, calm = Conditions(wind_mph=25.0, wind_from=b), Conditions(wind_mph=0.0, wind_from=b)
        weak = golfer(ball_flight=55, management=55)
        strong = golfer(ball_flight=95, management=95)
        n = 300
        loss_weak = mean_score(weak, MID, windy, n, 5) - mean_score(weak, MID, calm, n, 5)
        loss_strong = mean_score(strong, MID, windy, n, 5) - mean_score(strong, MID, calm, n, 5)
        self.assertLess(loss_strong, loss_weak)
        self.assertGreater(loss_strong, 0.3)                               # still loses strokes: no immunity

    def test_wind_terms_bounded_away_from_zero(self):
        best = Player(golfer(100), MID, Conditions(wind_mph=30.0, wind_from=0), None, random.Random(1))
        self.assertGreater(best.wind_skill, 0.8)
        for dirf, *_ in best.hw.values():
            self.assertGreaterEqual(dirf, 0.3)                             # a tailwind still costs some control

    def test_wet_mitigation_by_existing_skills(self):
        wet, dry = Conditions(wind_mph=0, rain=True, wind_from=0), Conditions(wind_mph=0, wind_from=0)
        p = lambda g, c: Player(g, MID, c, None, random.Random(1))
        lo, hi = golfer(50), golfer(50, bunker=95, focus=95, striking_consistency=95)
        for attr in ('sand_fail', 'mental', 'mishit'):
            d_lo = getattr(p(lo, wet), attr) - getattr(p(lo, dry), attr)
            d_hi = getattr(p(hi, wet), attr) - getattr(p(hi, dry), attr)
            self.assertGreater(d_hi, 0, attr)                              # strong players still affected
            self.assertLess(d_hi, d_lo, attr)                              # but less

    def test_aggression_with_control_differs_from_aggression_without(self):
        b = WX.hole_bearings(MID)[1]
        windy = Conditions(wind_mph=25.0, wind_from=b)
        bold = lambda bfc: replace(golfer(ball_flight=bfc), personality={**golfer().personality, 'aggression': 90})
        self.assertLess(mean_score(bold(95), MID, windy, 200, 9), mean_score(bold(45), MID, windy, 200, 9))


class ControlTests(unittest.TestCase):
    def test_calm_dry_unchanged_by_the_seasonal_model(self):
        for g in (golfer(), golfer(40, management=20), golfer(90, ball_flight=99)):
            g = replace(g, familiarity={MID.familiarity_key: 30})
            for i in range(6):
                a = play_round(g, MID, random.Random(i), Conditions(wind_mph=0.0))
                b = play_round(g, MID, random.Random(i), Conditions(wind_mph=0.0, wind_from=137))
                self.assertEqual((a.holes, a.drives), (b.holes, b.drives))

    def test_no_country_penalty(self):
        cond = Conditions(wind_mph=18.0, rain=True, wind_from=220)
        g = golfer()
        for country in ('Scotland', 'Australia', 'Thailand'):
            h = replace(g, country=country, hometown='')
            a = play_round(g, MID, random.Random(4), cond)
            b = play_round(h, MID, random.Random(4), cond)
            self.assertEqual((a.holes, a.drives), (b.holes, b.drives))

    def test_no_round_is_ever_cancelled(self):
        course = at('Bergen', 'Norway', 'Parkland', 14.0)                  # wet, windy: the worst there is
        golfers = [replace(golfer(60 + i), id=i + 1) for i in range(6)]
        for seed in range(3):
            task = {'event_id': '2030:TEST', 'site': 0, 'course': course, 'golfers': golfers,
                    'caddies': [None] * len(golfers), 'match_play': False, 'rounds': 4, 'cut_top': 0,
                    'prestige': 50.0, 'seed': seed, 'week': 2, 'weather': WX.MODEL}
            out = SEA.play_site(task)
            self.assertEqual(len(out['conditions']), 4)
            self.assertTrue(all(len(c) == 5 for c in out['conditions']))
            self.assertEqual(len(out['rounds']), 4 * len(golfers))         # every round played by everyone

    def test_match_play_weather_every_day_and_no_match_cancelled(self):
        course = at('Bergen', 'Norway', 'Parkland', 14.0)
        golfers = [replace(golfer(60 + i), id=i + 1) for i in range(8)]
        task = {'event_id': '2030:TEST_AM', 'site': 0, 'course': course, 'golfers': golfers,
                'caddies': [None] * len(golfers), 'match_play': True, 'rounds': 0, 'cut_top': 0,
                'prestige': 40.0, 'seed': 11, 'week': 3, 'weather': WX.MODEL}
        out = SEA.play_site(task)
        self.assertEqual(len(out['conditions']), 2 + 3)                    # two stroke rounds, three knockout days
        self.assertEqual(len(out['matches']), 7)                           # every match played
        self.assertEqual(out['conditions'], SEA.play_site(task)['conditions'])

    def test_classic_worlds_keep_classic_records(self):
        golfers = [replace(golfer(70), id=1), replace(golfer(72), id=2)]
        task = {'event_id': '2030:TEST', 'site': 0, 'course': MID, 'golfers': golfers, 'caddies': [None, None],
                'match_play': False, 'rounds': 2, 'cut_top': 0, 'prestige': 50.0, 'seed': 1}
        out = SEA.play_site(task)
        self.assertTrue(all(len(c) == 3 for c in out['conditions']))


class RecordTests(unittest.TestCase):
    def test_observer_shows_each_rounds_conditions(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
        import observer_history as OH
        full = {'conditions': [[[10.0, 0, 0.5, 270], [22.5, 1, 0.5, 90]]], 'scores': [{'1': [70, 71]}]}
        text = OH.conditions_lines(full, 0)
        self.assertIn('R1: wind 10.0 mph from the W, dry', text)
        self.assertIn('R2: wind 22.5 mph from the E, wet', text)
        self.assertNotIn('R2', OH.conditions_lines(full, 0, through=1))   # a replay shows nothing ahead
        mp = {'match_play': True, 'conditions': [[[8.0, 0, 0.4, 0]] * 3], 'scores': [{'1': [70, 72]}]}
        self.assertIn('knockout day 1: wind 8.0 mph from the N', OH.conditions_lines(mp, 0))
        self.assertEqual(OH.conditions_lines({'conditions': [None]}, 0), '')                # not recorded: nothing


    def test_describe(self):
        self.assertEqual(WX.describe([12.5, 1, 0.5]), 'wind 12.5 mph, wet, pin difficulty 0.5')
        self.assertEqual(WX.describe([12.5, 0, 0.5, 225]), 'wind 12.5 mph from the SW, dry, pin difficulty 0.5')
        self.assertEqual(WX.describe([12.5, 0, 0.5, 225, 0.32]),
                         'wind 12.5 mph from the SW, gusts ±32%, dry, pin difficulty 0.5')
        self.assertEqual(WX.describe(None), 'not recorded')

    def test_rule_recorded(self):
        self.assertGreaterEqual(RULES_VERSION, '2026-11-09')                 # later versions may follow
        self.assertEqual(VERSIONS[-1][0], RULES_VERSION)
        self.assertEqual(RULES['weather'][2], '2026-11-09')
        self.assertIn('2026-11-09', [v for v, _ in VERSIONS])
        self.assertIn('No round is ever cancelled, shortened or delayed by weather', RULES['weather'][1])
        self.assertIn('never cancelled, shortened or delayed', dict(VERSIONS)['2026-11-09'])


if __name__ == '__main__':
    unittest.main()
