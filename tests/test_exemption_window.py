"""The USA Open champions' place (route U1, "USA Open champions, last 10 years"): a champion of year Y is exempt
from the Y+1 through the Y+10 USA Open and not in Y+11 (unless they win again); the evidence a place shows agrees
with the place itself; and the routes that count the current year keep their window. Every other windowed route,
with the editions docs/QUALIFICATION_WINDOWS.md lists for it (today's definitions: the "last N years" routes that
include the current edition count N + 1 editions once it is played -- a decision pending, see that document).

Run from the project folder:  python -m unittest tests.test_exemption_window -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from golfsim import qualification as Q                                    # noqa: E402


class Ctx:
    """The facts winners_of and evidence read: who won which edition."""

    def __init__(self, wins, people=()):
        self.wins = dict(wins)                                            # {(series, year): golfer}
        self.results = {k: True for k in self.wins}
        self.tour_of = {}
        self.people = {p.id: p for p in people}

    def winner(self, sid, year):
        return self.wins.get((sid, year))

    def placed(self, sid, year, n):
        w = self.wins.get((sid, year))
        return [w] if w is not None else []

    def edition_week(self, sid, year):
        return 25


def route(code, version='v2', major='USA_OPEN'):
    return next(r for r in Q.rules_for(version)[major] if r.code == code)


class USAOpenChampions(unittest.TestCase):
    def test_a_champion_holds_the_place_through_the_tenth_anniversary(self):
        for version in ('v1', 'v2'):
            u1 = route('U1', version)
            ctx = Ctx({('USA_OPEN', 2040): 7})
            self.assertNotIn(7, u1.select(ctx, 2040), version)            # (their own year: they are the champion)
            for y in range(2041, 2051):                                   # Y+1 .. Y+10
                self.assertIn(7, u1.select(ctx, y), (version, y))
            self.assertNotIn(7, u1.select(ctx, 2051), version)            # Y+11: expired
            self.assertNotIn(7, u1.select(ctx, 2060), version)

    def test_a_new_win_renews_the_place(self):
        u1 = route('U1')
        ctx = Ctx({('USA_OPEN', 2040): 7, ('USA_OPEN', 2048): 7, ('USA_OPEN', 2049): 9})
        for y in range(2049, 2059):                                       # through 2048 + 10
            self.assertIn(7, u1.select(ctx, y), y)
        self.assertNotIn(7, u1.select(ctx, 2059))
        self.assertEqual(u1.select(ctx, 2050), [9, 7])                    # newest champion first, each once

    def test_the_evidence_names_the_win_behind_the_place(self):
        u1 = route('U1')
        ctx = Ctx({('USA_OPEN', 2040): 7})
        self.assertEqual(Q.evidence(u1, 7, 2050, ctx), [('2040:USA_OPEN (won)', (2040, 25))])   # the tenth year
        self.assertEqual(Q.evidence(u1, 7, 2051, ctx), [])

    def test_routes_that_count_the_current_year_keep_their_window(self):
        u5 = route('U5')                                                  # other majors' champions, last 5 years
        sids = sorted(Q.OTHER_MAJORS['USA_OPEN'])
        ctx = Ctx({(sids[0], 2045): 3, (sids[0], 2040): 4, (sids[0], 2039): 5})
        got = u5.select(ctx, 2045)
        self.assertEqual(got, [3, 4])                                     # this year's (already played) back to 2040
        self.assertNotIn(5, got)


def held(r, x, sid, version='v2', played_this_year=True, years=range(2030, 2060)):
    """The seasons in which a champion (7) of `sid` in year x is selected by route r: the editions they hold. The
    current year's edition is visible only when it was played before this major (played_this_year)."""
    out = []
    for y in years:
        wins = {(sid, x): 7} if x < y or (x == y and played_this_year) else {}
        if 7 in r.select(Ctx(wins), y):
            out.append(y)
    return out


class Windows(unittest.TestCase):
    """docs/QUALIFICATION_WINDOWS.md, route by route (reference calendar: Players week 11; majors 15, 20, 25, 30)."""

    def test_masters_other_majors_five_editions(self):
        m2 = route('M2', major='TOUR_MASTERS')
        for sid in Q.OTHER_MAJORS['TOUR_MASTERS']:                         # none played yet at the Masters
            self.assertEqual(held(m2, 2040, sid, played_this_year=False), list(range(2041, 2046)), sid)

    def test_other_majors_count_the_current_edition_once_played(self):
        cases = (('P2', 'PREMIER_TOUR_CHAMPIONSHIP', {'TOUR_MASTERS'}),
                 ('U5', 'USA_OPEN', {'TOUR_MASTERS', 'PREMIER_TOUR_CHAMPIONSHIP'}),
                 ('B3', 'BRITANNIA_OPEN', {'TOUR_MASTERS', 'PREMIER_TOUR_CHAMPIONSHIP', 'USA_OPEN'}))
        for code, major, before in cases:
            r = route(code, major=major)
            for sid in Q.OTHER_MAJORS[major]:
                if sid in before:                                         # played earlier this season: X .. X+5
                    self.assertEqual(held(r, 2040, sid), list(range(2040, 2046)), (code, sid))
                else:                                                     # later this season: X+1 .. X+5
                    self.assertEqual(held(r, 2040, sid, played_this_year=False), list(range(2041, 2046)), (code, sid))

    def test_players_winners_four_editions(self):
        for code, major in (('M3', 'TOUR_MASTERS'), ('P3', 'PREMIER_TOUR_CHAMPIONSHIP'), ('U6', 'USA_OPEN'),
                            ('B4', 'BRITANNIA_OPEN')):
            r = route(code, major=major)                                   # week 11: always played first
            self.assertEqual(held(r, 2040, 'PT_PREMIER_PLAYERS_CHAMPIONSHIP'), list(range(2040, 2044)), code)

    def test_previous_edition_routes_hold_one_edition(self):
        for code, major, sid in (('M9', 'TOUR_MASTERS', 'TOUR_MASTERS'), ('P4', 'PREMIER_TOUR_CHAMPIONSHIP',
                                 'PREMIER_TOUR_CHAMPIONSHIP'), ('U7', 'USA_OPEN', 'USA_OPEN'),
                                 ('B2', 'BRITANNIA_OPEN', 'BRITANNIA_OPEN')):
            self.assertEqual(held(route(code, major=major), 2040, sid, played_this_year=False), [2041], code)
        m10 = route('M10', major='TOUR_MASTERS')
        for sid in Q.OTHER_MAJORS['TOUR_MASTERS']:
            self.assertEqual(held(m10, 2040, sid, played_this_year=False), [2041], sid)

    def test_past_champions_for_life_and_britannia_to_sixty(self):
        for code, major in (('M1', 'TOUR_MASTERS'), ('P1', 'PREMIER_TOUR_CHAMPIONSHIP'), ('B1', 'BRITANNIA_OPEN')):
            self.assertEqual(held(route(code, major=major), 2040, major, played_this_year=False),
                             list(range(2041, 2060)), code)
        b1 = route('B1', major='BRITANNIA_OPEN')
        for age, ok in ((59, True), (60, True), (61, False)):
            ctx = Ctx({}, [Q.Person(7, 'x', 'pro', age)])
            self.assertEqual(Q._eligible(ctx, 7, b1, 2050), ok, age)

    def test_premier_winner_exemptions(self):
        from types import SimpleNamespace as NS
        from golfsim import cards
        series = {'BRITANNIA_OPEN': NS(kind='major', tier=0, name='Britannia Open'),
                  'PT_X': NS(kind='regular', tier=1, name='X Open')}
        def holds(sid, x):
            out = []
            for y in range(2038, 2050):
                wins = {(sid, x): 7}
                ctx = Ctx({k: v for k, v in wins.items() if k[1] <= y})
                season = NS(ctx=ctx, cal=NS(by_id=series))
                if 7 in cards.winner_exemptions(season, y, through=y):    # this season's wins count from the week
                    out.append(y)
            return out
        self.assertEqual(holds('BRITANNIA_OPEN', 2040), list(range(2040, 2046)))   # rest of X + five seasons
        self.assertEqual(holds('PT_X', 2040), [2040, 2041, 2042])                   # rest of X + two seasons


if __name__ == '__main__':
    unittest.main()
