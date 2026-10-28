"""Money: what golf costs, what it pays, and how long a golfer can afford to chase it.

Income
    prize money         from the season engine (amateurs take none)
    sponsors            yearly, from player prestige (`prestige.endorsements`)
    salary              part-timers and reinstated amateurs have a job; club professionals are paid
                        by their club; college golfers are on scholarship
Costs
    each event          travel and accommodation by level (more overseas), entry fees on the mini
                        tours and at Q-School, and a professional caddie if they employ one (a weekly
                        fee plus a share of winnings); a club professional's club pays for their
                        club-professional events (section events, championships, sectionals)
    coaching            a coach's yearly fee (paid weekly), or a share of prize money to a coach who
                        approached them
    living              a full-time touring professional lives on their winnings; everyone with a job
                        pays ordinary living costs from their salary (college golfers and teenagers
                        living at home pay none)

Money moves when it is earned or spent (weekly), never in a lump at the end of the season, and every
dollar passes through the golfer's ledger, so savings always reconcile exactly:
    cash at the end of a year = cash at the start + ledger income - ledger costs.

Backers
    Most young professionals chasing the game are backed by family, friends or a group of investors
    (about three in four in real life). A backing deal puts up a sum each season (topped up on
    1 January, drawn only when the golfer's own cash runs out) for a share of their prize money
    (BACKER_SHARE) while it lasts. Deals come when a golfer turns professional (likelier for a better
    amateur record) or after a breakthrough season, are renewed each winter only on results backers
    can see, and end after two seasons without progress, past 32, or once the golfer pays their own
    way (careers.review_backers).

Funding decisions (before money is spent)
    available funds  cash + remaining family/backer support + a limited line of credit
                     (credit grows with a golfer's recent income, up to a cap; nobody can borrow
                     without limit)
    committed        the next few weeks of living costs are set aside before any trip is booked
    expected prize   estimated from the golfer's own results so far (the share of purses they have
                     actually won), not from their hidden ability; it is never spent before it is won
A golfer can only enter an event they can pay for. How much a dollar matters scales with their funds,
so a broke mini-tour player weighs a long trip heavily and a millionaire barely notices it. When
funds run short, full-time players take paid work weeks instead of training.
"""
from __future__ import annotations

import math

from .geography import CITY_BY_NAME, COUNTRIES

EVENT_COST = {0: 5000, 1: 3500, 2: 1800, 3: 1200, 4: 600, 5: 0, 6: 350, 7: 1000, 8: 200}   # by tier, home country
TRAVEL = {'home': 1.0, 'region': 1.3, 'abroad': 1.8}
QSCHOOL_FEE = 4500
CADDIE_SHARE = 0.08              # of prize money, to a professional caddie (plus their weekly fee)
BACKER_SHARE = 0.25              # of prize money, to a backed golfer's backers while the deal lasts
BACKER_MIN, BACKER_MAX = 15000, 50000      # what backers put up a season
BACKER_AGE = 32                  # backers do not take on (or keep) golfers older than this
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
    if g.status == 'club_pro' and series.eligibility == 'club_pro':
        return 0.0                                    # the club pays for its professional's section golf
    country = CITY_BY_NAME[city].country
    where = 'home' if country == g.country else 'region' if COUNTRIES[country].region == COUNTRIES[g.country].region \
        else 'abroad'
    cost = EVENT_COST[series.tier] * TRAVEL[where]
    if series.tier == 4 and series.field:
        cost += 1.1 * series.purse / series.field     # mini tours are paid for by entry fees
    if series.category == 'q_school':
        cost += QSCHOOL_FEE
    return cost


WORK_WAGE = 900                  # a week of paid work for a full-time player who needs money
CREDIT_BASE, CREDIT_SHARE, CREDIT_CAP = 8000, 0.25, 60000
RESERVE_WEEKS = 4                # living costs set aside before booking any trip
PRIOR_PRIZE_SHARE = 0.004        # a professional's assumed share of a purse before they have results


def credit_limit(last_income):
    """How far into debt a lender (or family) will let a golfer go: grows with recent income, capped."""
    return min(CREDIT_CAP, CREDIT_BASE + CREDIT_SHARE * max(0.0, last_income))


def initial_backing(age, u1, u2):
    """Family or private backers willing to fund a young golfer's career (a pot used as needed).
    Many have none; a few have generous backing; it is mostly there for the young."""
    if age > 30 or u1 < 0.4:
        return 0.0
    youth = min(1.0, (31 - age) / 10)
    return round(min(150000.0, youth * 20000 * math.exp(2.0 * (u2 - 0.5))), -2)


def backer_deal(age, standing, u1, u2):
    """A new professional's backing deal (yearly dollars, 0 = none): about three in four find backers,
    more often with a better record (`standing` 0-1, from the amateur or world ranking); the sum
    varies widely and is larger for a better record."""
    if age > BACKER_AGE or u1 >= min(0.95, 0.6 + 0.4 * standing):
        return 0.0
    return round(BACKER_MIN + (BACKER_MAX - BACKER_MIN) * (0.65 * u2 + 0.35 * standing), -2)


def weekly_living(g):
    """(salary, living cost) per week for a golfer's lifestyle."""
    if g.lifestyle == 'part_time':
        return SALARY['club_pro' if g.status == 'club_pro' else 'part_time'] / 52, LIVING_WORKING / 52
    if g.status == 'pro' and g.lifestyle == 'full_time':
        return 0.0, LIVING / 52
    return 0.0, 0.0                                  # college golfers and teenagers living at home


def money_unit(available):
    """Dollars per point of 'event value': how much money matters to someone with these funds."""
    return max(100.0, available / 50.0)


class Ledger:
    """One golfer's money for one year."""
    __slots__ = ('prize', 'sponsors', 'salary', 'work', 'support', 'events', 'caddie', 'caddie_share', 'coaching',
                 'coach_share', 'living', 'backer_share')

    def __init__(self):
        self.prize = self.sponsors = self.salary = self.work = self.support = 0.0
        self.events = self.caddie = self.caddie_share = self.coaching = self.coach_share = self.living = 0.0
        self.backer_share = 0.0

    def __setstate__(self, state):                    # ledgers saved before backer shares existed
        self.backer_share = 0.0
        for k, v in (state[1] if isinstance(state, tuple) else state).items():
            setattr(self, k, v)

    @property
    def income(self):
        return self.prize + self.sponsors + self.salary + self.work + self.support

    @property
    def costs(self):
        return (self.events + self.caddie + self.caddie_share + self.coaching + self.coach_share + self.living
                + self.backer_share)

    @property
    def net(self):
        return self.income - self.costs
