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
    moving              a career move to another country (residence.MOVE_COST); college moves are paid
                        by the school and never charged

Money moves when it is earned or spent (weekly), never in a lump at the end of the season, and every
dollar passes through the golfer's ledger, so savings always reconcile exactly:
    cash at the end of a year = cash at the start + ledger income - ledger costs.

Backers
    Most young professionals chasing the game are backed by family, friends or a group of investors
    (about three in four in real life). A backing deal puts up a sum each season (topped up on
    1 January, drawn only when the golfer's own cash runs out, before any family money) for a share
    of their prize money (BACKER_SHARE) while it lasts. Backers' money is kept apart from family money
    (Golfer.backer_funds): when a deal ends, the undrawn part goes back to the backers along with
    their share of winnings; family money stays the golfer's. Deals come when a golfer turns professional (likelier for a better
    amateur record), after a breakthrough season, or when an unbacked professional's own money runs low
    (careers.NEED_RUNWAY: they need backers now; not within two winters of a deal ending); the
    starting world gives none to a professional whose savings already cover SELF_FUNDED_SEASONS seasons
    of losses (seeded_losses). Deals are renewed each winter only on results backers
    can see with bounded odds (progress, secured places, how far the losses outrun the deal, the
    backers' own patience, seasons without progress and age all count, none ends every deal), and
    end when the golfer pays their own way (careers.review_backers).

Funding decisions (before money is spent)
    available funds  cash + remaining family support + backers' money for the season + a limited
                     line of credit
                     (credit grows with a golfer's recent income, up to a cap; nobody can borrow
                     without limit)
    committed        the next few weeks of living costs are set aside before any trip is booked
    expected prize   estimated from the golfer's own results so far, by level of competition (the
                     share of purses they have actually won there, Season.prize_forecast), not from
                     their hidden ability; it is never spent before it is won. A season's money is
                     kept by the level it was won at (Season.level_earnings): money won below a
                     golfer's card is never evidence of what they earn at the card's level. Evidence
                     fades by EVIDENCE_DECAY for each full season away from a level (a comeback is
                     judged mostly on what they do now, not on a large old event count)
    week's budget    every entry accepted in a week books its cost at once (Season.reserve), so a Monday
                     qualifier and that weekend's tournament are paid from one budget, not each from the
                     same funds; a qualifier's site is priced where the golfer is sent to play it
                     (Season.pay_at_sites); a caddie's weekly fee is booked and paid once a week
    payers           a school pays for its golfers' college events and a club for its professional's
                     section golf (event_payer); each is counted for that payer (Season.school_trips,
                     club_trips), never charged to the golfer
    support          family money and backers' money are separate pots and separate ledger lines
                     (support, backer_support); what backers put up and what goes back to them when a
                     deal ends is recorded (Season.backer_flows), so every pot reconciles
A golfer can only enter an event they can pay for. How much a dollar matters scales with their funds,
so a broke mini-tour player weighs a long trip heavily and a millionaire barely notices it. When
funds run short, full-time players take paid work weeks instead of training.

Debt
    The line of credit limits what a golfer *chooses* to spend: entries, travel, a caddie, a coach
    hired. Costs they cannot choose are charged every week whatever their funds: living costs (net of
    any salary) and a contracted coach's fee until the monthly review stops it. An injured touring
    professional who needs money does light paid work while recovering (WORK_WAGE, the same as any work
    week; the injury heals no slower), so an injury no longer has to run up debt; a golfer with no
    income at all can still go deeper into debt than the credit allowance. Such debt is kept, exactly,
    in their cash: it is never erased,
    nobody new pays it (only the family and backers' pots they already had are drawn), it blocks every
    cost they could choose until it is repaid from later income, and it weighs on the end-of-season
    decision through the runway, smoothly (no debt threshold forces any decision; careers change only
    at the end of a season, so a long injury runs its course in the life they had).
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
BACKER_AGE_MID = 31              # age at which backers are half as willing as for a young golfer
BACKER_AGE_SPREAD = 2.0          # how quickly that willingness falls with age (smoothly: no cut-off)


def backer_youth(age):
    """How willing backers are to put money behind a golfer of this age (1 young .. towards 0): an
    uncalibrated assumption shaped like real backing (mostly for golfers in their twenties)."""
    return 1 / (1 + math.exp((age - BACKER_AGE_MID) / BACKER_AGE_SPREAD))
LIVING = 32000                   # a full-time touring professional's yearly living costs
LIVING_WORKING = 40000           # an adult with a job: normal life costs more than living on the road
SALARY = {'part_time': 52000, 'club_pro': 65000}


def expected_prize(overall):
    """Typical yearly prize money for a full-time professional of this ability (seeding only)."""
    return 2000 * math.exp((overall - 40) / 5.6)


def in_money_pool(g):
    """Whether a golfer belongs to the professional pool that seeded money is judged against (MoneyStanding):
    every professional who has not retired, whatever their tour or lifestyle."""
    return g.status == 'pro' and g.lifestyle != 'retired'


SELF_FUNDED_SEASONS = 3          # own savings covering this many seasons of losses: no backers needed
SEED_EVENTS = 24                 # a touring professional's season, for the starting world's estimates


def seeded_losses(g, tier, standing=None, member=None):
    """The starting world's estimate of what a season on tour costs a professional beyond what it
    brings in (living, trips at the level, against their typical winnings): seeding only, like
    initial_cash, so the first winter does not end deals that should never have been made."""
    costs = LIVING + SEED_EVENTS * EVENT_COST[tier] * TRAVEL['region']
    return max(1.0, costs - 0.75 * expected_prize(money_overall(g, standing, member)))


# ---- seeded money by standing (dev-3 worlds, rules 2026-11-17; realism.py section 3c) -----------------------------
# Money a world has to invent before anything has been played (the starting world's savings, the estimate of a
# season's losses that decides seeded backing, and fame, which becomes prestige and sponsor money; and the savings of
# new professionals who arrive later) used to follow the absolute Overall: 2000 x e^((Overall - 40) / 5.6) a year,
# so a 98.6 was worth about $70M a year and a 90.5 about $16M, and anything that moves the top of the rating scale
# moved the money with it. In dev-3 worlds it follows the golfer's standing in the world's professional pool
# (in_money_pool: every professional who has not retired, whatever tour or lifestyle; not an age cohort and not one
# tour, so the best mini-tour player is not paid like the best Premier player): their mid-rank percentile there, read
# as the Overall that holds the same standing in a typical starting world (MONEY_REFERENCE), and the existing formulas
# take it from there. The best professional of a world whose best are 80s and of one whose best are 90s are seeded
# alike; what years on tour, status (amateurs and club professionals keep their flat amounts) and age add is
# unchanged. dev-1 and dev-2 worlds keep the absolute Overall. Rebuild or check the table: tools/money_reference.py
# (median of 20 starting worlds under the existing generation rule, pool size 3443).
MONEY_REFERENCE = (
    (0.0, 28.91), (0.02, 41.36), (0.04, 44.0), (0.06, 45.75),
    (0.08, 47.24), (0.1, 48.32), (0.12, 49.26), (0.14, 50.04),
    (0.16, 50.78), (0.18, 51.49), (0.2, 52.15), (0.22, 52.7),
    (0.24, 53.24), (0.26, 53.82), (0.28, 54.35), (0.3, 54.85),
    (0.32, 55.29), (0.34, 55.85), (0.36, 56.39), (0.38, 56.89),
    (0.4, 57.36), (0.42, 57.87), (0.44, 58.37), (0.46, 58.87),
    (0.48, 59.38), (0.5, 59.85), (0.52, 60.41), (0.54, 60.91),
    (0.56, 61.43), (0.58, 61.93), (0.6, 62.44), (0.62, 62.97),
    (0.64, 63.47), (0.66, 64.02), (0.68, 64.57), (0.7, 65.08),
    (0.72, 65.63), (0.74, 66.28), (0.76, 66.86), (0.78, 67.45),
    (0.8, 68.02), (0.82, 68.64), (0.84, 69.32), (0.86, 69.98),
    (0.88, 70.66), (0.9, 71.44), (0.905, 71.65), (0.91, 71.87),
    (0.915, 72.14), (0.92, 72.39), (0.925, 72.66), (0.93, 72.95),
    (0.935, 73.3), (0.94, 73.64), (0.945, 73.96), (0.95, 74.33),
    (0.955, 74.77), (0.96, 75.12), (0.965, 75.63), (0.97, 76.11),
    (0.975, 76.81), (0.98, 77.68), (0.985, 78.66), (0.99, 80.17),
    (0.991432, 80.7), (0.991722, 80.85), (0.992013, 80.96), (0.992303, 81.06),
    (0.992594, 81.19), (0.992884, 81.35), (0.993175, 81.52), (0.993465, 81.62),
    (0.993755, 81.8), (0.994046, 82.11), (0.994336, 82.25), (0.994627, 82.33),
    (0.994917, 82.43), (0.995208, 82.71), (0.995498, 82.9), (0.995789, 82.99),
    (0.996079, 83.24), (0.996369, 83.44), (0.99666, 83.72), (0.99695, 83.98),
    (0.997241, 84.59), (0.997531, 84.89), (0.997822, 85.35), (0.998112, 85.79),
    (0.998403, 86.02), (0.998693, 86.84), (0.998983, 88.05), (0.999274, 88.69),
    (0.999564, 90.29), (0.999855, 92.51), (1.0, 92.53),
)


class MoneyStanding:
    """A golfer's standing in a money pool (a list of Overall ratings), read on the reference scale.

    standing(x): the mid-rank percentile of rating x among the pool: (golfers below + half of those level with it)
    / pool size, counting x itself once when it is not already a pool member's rating (`member`: x is one of the
    pool's ratings, as for a golfer judged against a pool that includes them). Ties share one standing; a pool of
    one is the middle (0.5); an empty pool (nobody to compare with) is the middle too.
    reference(x): the Overall holding that standing in a typical starting world (MONEY_REFERENCE)."""

    def __init__(self, ratings):
        import bisect
        self._bisect = bisect
        self.vals = sorted(float(r) for r in ratings)

    def standing(self, x, member=True):
        b = self._bisect
        below = b.bisect_left(self.vals, x)
        level = b.bisect_right(self.vals, x) - below
        n = len(self.vals)
        if not member or level == 0:                 # x is not counted in the pool: add it once
            n, level = n + 1, level + 1
        return (below + 0.5 * level) / n if n else 0.5

    def reference(self, x, member=True):
        return reference_overall(self.standing(x, member))


def reference_overall(q):
    """The Overall at standing q (0-1) of a typical starting world's professional pool (MONEY_REFERENCE, linear)."""
    import bisect
    t = MONEY_REFERENCE
    if q <= t[0][0]:
        return t[0][1]
    if q >= t[-1][0]:
        return t[-1][1]
    i = bisect.bisect_right([p for p, _ in t], q)
    (q0, v0), (q1, v1) = t[i - 1], t[i]
    return v0 + (v1 - v0) * (q - q0) / (q1 - q0)


def money_overall(g, standing=None, member=None):
    """The Overall seeded money is judged on: the golfer's own (dev-1, dev-2: `standing` None) or, in dev-3 worlds,
    the reference Overall of their standing in the professional pool (`standing`: a MoneyStanding). `member`: whether
    the golfer is already counted in that pool (default: in_money_pool(g); a newcomer judged against the world they
    join is not)."""
    if standing is None:
        return g.overall
    return standing.reference(g.overall, member=in_money_pool(g) if member is None else member)


def initial_cash(g, age, u, standing=None, member=None):
    """Savings at the start of the world (and a new professional's on arrival). `standing`: dev-3 worlds' money
    pool (MoneyStanding), None for the absolute Overall (dev-1, dev-2); `member`: see money_overall."""
    if g.status == 'amateur':
        return 5000 + 20000 * u
    if g.status == 'club_pro':
        return 20000 + 40000 * u
    years = max(0.0, min(8.0, age - 21))
    return 15000 + 0.25 * expected_prize(money_overall(g, standing, member)) * years * (0.4 + 1.2 * u)


def event_payer(g, series):
    """Who pays for a golfer's trip when it is not the golfer: 'school' (a college's own events),
    'club' (a club professional's section golf), or None."""
    if g.tour.startswith('CO_') and series.tier == 5:
        return 'school'
    if g.status == 'club_pro' and series.eligibility == 'club_pro':
        return 'club'
    return None


def event_cost(g, series, city, home=None):
    """What one event costs a golfer: travel by distance from where they live (`home`: their country of
    residence, Season.home_country; their nationality only for legacy people whose residence is unknown),
    entry fees (0 when a school or club pays, event_payer). A caddie's weekly fee is not part of it
    (Season.trip_cost adds it once a week)."""
    if event_payer(g, series):
        return 0.0
    home = home or g.country
    country = CITY_BY_NAME[city].country
    where = 'home' if country == home else 'region' if COUNTRIES[country].region == COUNTRIES[home].region \
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
PRIOR_EVENTS = 3                 # ... weighed as this many events of evidence
LEVEL_STEP = 0.5                 # share of the purse one level of competition up (twice as much one down)
MAX_PRIZE_SHARE = 0.25           # no forecast expects more than this share of a purse
PROVEN_EVENTS = 8                # events at a level by which earnings there count as fairly proven
UPFRONT_SHARE = 0.25             # of a season's costs that must be paid before winnings come in
EVIDENCE_DECAY = 0.5             # prize evidence at a level fades by half for each full season away from it


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
    """A new professional's backing deal (yearly dollars, 0 = none): about three in four young new
    professionals find backers, more often with a better record (`standing` 0-1, from the amateur or
    world ranking) and less often the older they are (backer_youth, smoothly); the sum varies widely
    and is larger for a better record."""
    if u1 >= min(0.95, 0.6 + 0.4 * standing) * backer_youth(age) / backer_youth(22):
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
    __slots__ = ('prize', 'sponsors', 'salary', 'work', 'support', 'backer_support', 'events', 'caddie',
                 'caddie_share', 'coaching', 'coach_share', 'living', 'backer_share', 'moving', 'am_support')

    def __init__(self):
        self.prize = self.sponsors = self.salary = self.work = self.support = self.backer_support = 0.0
        self.events = self.caddie = self.caddie_share = self.coaching = self.coach_share = self.living = 0.0
        self.backer_share = self.moving = self.am_support = 0.0

    def __setstate__(self, state):                    # ledgers saved before backer shares (or backers'
        self.backer_share = self.backer_support = self.moving = self.am_support = 0.0   # draws, moves, support)
        for k, v in (state[1] if isinstance(state, tuple) else state).items():
            setattr(self, k, v)

    @property
    def income(self):
        return (self.prize + self.sponsors + self.salary + self.work + self.support + self.backer_support
                + self.am_support)                     # (amateur support: in kind, it paid golf costs booked below)

    @property
    def costs(self):
        return (self.events + self.caddie + self.caddie_share + self.coaching + self.coach_share + self.living
                + self.backer_share + self.moving)

    @property
    def net(self):
        return self.income - self.costs
