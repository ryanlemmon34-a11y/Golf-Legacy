"""Money: what golf costs, what it pays, and how long a golfer can afford to chase it.

Income
    prize money         from the season engine (amateurs take none)
    sponsors            yearly, from player prestige (`prestige.endorsements`)
    salary              part-timers and reinstated amateurs have a job; club professionals are paid
                        by their club; college golfers are on scholarship
Costs
    each event          travel and accommodation by level (more overseas), entry fees on the mini
                        tours and at Q-School, and a caddie (a weekly fee plus a share of winnings)
    living              a full-time touring professional lives on their winnings; everyone with a job
                        pays ordinary living costs from their salary (college golfers and teenagers
                        living at home pay none)

A golfer's cash carries over from year to year and can go negative (debt). Money is one of the big
reasons golfers give up the chase (see `careers.py`).
"""
from __future__ import annotations

import math

from .geography import CITY_BY_NAME, COUNTRIES

EVENT_COST = {0: 5000, 1: 3500, 2: 1800, 3: 1200, 4: 600, 5: 0, 6: 350, 7: 1000}   # by tier, home country
TRAVEL = {'home': 1.0, 'region': 1.3, 'abroad': 1.8}
QSCHOOL_FEE = 4500
CADDIE_SHARE = 0.08              # of prize money, tiers 0-2 (lower tours use friends or a pull cart)
LIVING = 32000                   # a full-time touring professional's yearly living costs
LIVING_WORKING = 40000           # an adult with a job: normal life costs more than living on the road
SALARY = {'part_time': 52000, 'club_pro': 65000}


def expected_prize(overall):
    """Typical yearly prize money for a full-time professional of this ability (seeding only)."""
    return 2000 * math.exp((overall - 40) / 5.6)


def initial_cash(g, age, u):
    """Savings at the start of the world."""
    if g.status == 'amateur':
        return 5000 + 20000 * u
    if g.status == 'club_pro':
        return 20000 + 40000 * u
    years = max(0.0, min(8.0, age - 21))
    return 15000 + 0.25 * expected_prize(g.overall) * years * (0.4 + 1.2 * u)


def event_cost(g, series, city):
    """What one event costs a golfer: travel by distance, entry fees, caddie fee."""
    if g.tour.startswith('CO_') and series.tier == 5:
        return 0.0                                    # the college pays
    country = CITY_BY_NAME[city].country
    where = 'home' if country == g.country else 'region' if COUNTRIES[country].region == COUNTRIES[g.country].region \
        else 'abroad'
    cost = EVENT_COST[series.tier] * TRAVEL[where]
    if series.tier == 4 and series.field:
        cost += 1.1 * series.purse / series.field     # mini tours are paid for by entry fees
    if series.category == 'q_school':
        cost += QSCHOOL_FEE
    return cost


class Ledger:
    """One golfer's money for one year."""
    __slots__ = ('prize', 'sponsors', 'salary', 'events', 'caddie', 'living')

    def __init__(self):
        self.prize = self.sponsors = self.salary = self.events = self.caddie = self.living = 0.0

    @property
    def income(self):
        return self.prize + self.sponsors + self.salary

    @property
    def costs(self):
        return self.events + self.caddie + self.living

    @property
    def net(self):
        return self.income - self.costs
