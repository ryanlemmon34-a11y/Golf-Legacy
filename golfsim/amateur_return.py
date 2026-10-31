"""Return from work to full-time amateur golf (rules 2026-11-06): the way back for a working amateur when their
finances and results support it, never guaranteed.

Approved by the owner on 31 October 2026 (decision D5); the thresholds are HAL's delegated decision D5a (no hard
age cut-off; sustainable funding, relevant results and a meaningful period in work; a probability that declines
smoothly with age). Every number below is a PROVISIONAL calibration, to be validated by measuring how many
working amateurs return and how many of those are cash-blocked again (docs/AMATEUR_WORK_PATHWAY_PROPOSAL.md).

Who: a part-time (working) amateur outside college, decided each winter with the other career decisions, after
the chance of turning professional (a golfer who turns professional does not also return). Three conditions,
then a chance:

    in work      at least MIN_SEASONS full seasons worked since they took the job (a job taken mid-season starts
                 counting from the next season); a working amateur already in work when the world's records
                 begin counts as having worked long enough
    funding      not in debt, and their own savings plus family money cover a full-time amateur season of golf
                 with the staff they are already committed to: FULL_TIME_EVENTS events at their own average trip
                 cost last season (or a regional amateur trip when they played too few to tell), plus their
                 caddie's weekly fee for those events if they employ one, plus their coach's agreed yearly fee if
                 they pay one (a share deal costs nothing up front). Each cost is counted once. Amateur support
                 never counts (it is restricted to golf, lapses each season and is not promised for the next);
                 salary does not either (they give the job up)
    results      something to go back for in the season just ended: amateur ranking inside the top 300, a win or
                 a top-3 finish, or a rise of 100 places or more in the amateur ranking

    chance       sig(BASE + RESULTS x signal + FUNDS x min(2, savings / season cost) + WILL x (will - 0.5)
                     - AGE_SLOPE x max(0, age - AGE_FROM)) x (1 - the chance they would take a job again next
                     winter as a full-time amateur, careers.p_amateur_job at next season's age with their savings
                     after paying for that season), at most CAP

The last factor keeps the two decisions consistent instead of flipping a golfer back and forth: the existing
job decision makes full-time adult amateurs ever likelier to take work through their mid-twenties, so a return
where that is near certain would be undone a year later. It is what makes the chance fall with age (smoothly,
no age excluded), together with the small direct age term.

No financial advantage comes from switching: a full-time amateur has no salary and (living at home, as the
model has it) no living costs, and the funding test asks for a whole season's golf in hand without debt, so
the switch is never a way out of debt. Once full-time again, amateur support and the work pathway apply as to
any full-time amateur: a golfer who is blocked again can take work again. The draw uses its own random stream
per golfer and season, so it never shifts anyone else's career decisions.
"""
from __future__ import annotations

import math
import random

from . import finance as FIN

MIN_SEASONS = 1                 # full seasons in work before a return is considered
FULL_TIME_EVENTS = 16           # a full-time amateur's season (Season.target_events)
MIN_TRIPS_SEEN = 3              # trips last season needed to use the golfer's own average cost
FALLBACK_TRIP = FIN.EVENT_COST[6] * FIN.TRAVEL['region']   # a regional amateur event's trip
RANK_GATE, RISE_GATE = 300, 100
BASE, RESULTS, FUNDS, WILL = -3.0, 2.0, 0.6, 1.5
AGE_FROM, AGE_SLOPE = 23, 0.12  # the chance falls smoothly from 23 (no age is excluded)
CAP = 0.6
KIND = 'amateur returned to full-time golf'


def _sig(x):
    return 1 / (1 + math.exp(-x))


def started_work(season, g, year, week):
    """Record when a golfer started working as an amateur ((year, week); week 53 = the winter after `year`)."""
    season.amateur_work_from[g.id] = (year + 1, 1) if week >= 53 else (year, week)


def seasons_in_work(season, gid, year):
    """Full seasons worked by the end of `year` (None: already working when the world's records began)."""
    start = season.amateur_work_from.get(gid)
    if start is None:
        return None
    y0, w0 = start
    return max(0, year - y0 + (1 if w0 <= 1 else 0))


def season_cost(season, g, year, row):
    """A full-time amateur season of golf: FULL_TIME_EVENTS trips at the golfer's own average travel and entry
    cost last season (the ledger's events line: travel and fees only), plus the committed staff -- their caddie's
    weekly fee for each of those events and their coach's agreed yearly fee. Each counted once."""
    led = season.ledgers.get(year, {}).get(g.id)
    events = row.get('events', 0)
    trip = led.events / events if led is not None and events >= MIN_TRIPS_SEEN else FALLBACK_TRIP
    cost = FULL_TIME_EVENTS * max(trip, FALLBACK_TRIP)
    st = season.staff
    k = st.caddie(g.id)
    if k is not None:
        cost += FULL_TIME_EVENTS * k.weekly_fee
    if st.coach(g.id) is not None:
        cost += st.agreed_fee(g.id)
    return cost


def results_signal(row, standing):
    """(signal, reasons) from the season just ended; signal 0 = nothing to go back for."""
    rank, start = row.get('am_end'), row.get('am_start')
    wins, top3 = row.get('wins', 0), row.get('top3', 0)
    rose = bool(rank and start and start - rank >= RISE_GATE)
    why = []
    if rank and rank <= RANK_GATE:
        why.append(f'amateur ranking {rank}')
    if wins:
        why.append(f'{wins} win{"s" if wins > 1 else ""}')
    if top3 and top3 > wins:
        why.append(f'{top3} top-3 finishes')
    if rose:
        why.append(f'rose from {start} to {rank} in the amateur ranking')
    if not why:
        return 0.0, why
    return standing + 0.5 * min(2, wins) + 0.25 * min(4, top3) + (0.3 if rose else 0.0), why


def chance(season, g, row, year, standing):
    """(probability, facts) of returning to full-time amateur golf this winter; probability 0 when a condition
    is not met (facts then say which)."""
    age = g.age(year)
    worked = seasons_in_work(season, g.id, year)
    cost = season_cost(season, g, year, row)
    funds = max(0.0, g.cash) + g.backing
    signal, why = results_signal(row, standing)
    facts = {'age': age, 'seasons_in_work': worked, 'cash': round(g.cash), 'family': round(g.backing),
             'season_cost': round(cost), 'results': why}
    if worked is not None and worked < MIN_SEASONS:
        return 0.0, dict(facts, blocked='not yet a full season in work')
    if g.cash < 0 or funds < cost:
        return 0.0, dict(facts, blocked='savings do not cover a full-time amateur season')
    if signal <= 0:
        return 0.0, dict(facts, blocked='no results to go back for')
    will = (g.personality['work_ethic'] + g.personality['big_stage']) / 200
    x = (BASE + RESULTS * signal + FUNDS * min(2.0, funds / cost) + WILL * (will - 0.5)
         - AGE_SLOPE * max(0, age - AGE_FROM))
    stay = keep_up(season, g, row, year, cost)
    return min(CAP, _sig(x) * stay), dict(facts, keep_up=round(stay, 3))


def keep_up(season, g, row, year, cost):
    """1 - the chance they would take a job again next winter, judged as they would stand then: a year older and
    with the season's golf paid for out of their savings (family money first only if savings fall short)."""
    from .careers import p_amateur_job
    cash, backing = g.cash, g.backing
    spend = min(cost, max(0.0, cash))
    try:
        g.cash, g.backing = cash - spend, max(0.0, backing - (cost - spend))
        return 1.0 - p_amateur_job(season, g, row, year + 1)
    finally:
        g.cash, g.backing = cash, backing


def draw(season, gid, year):
    return random.Random(f'{season.seed}:amateur-return:{year}:{gid}').random()
