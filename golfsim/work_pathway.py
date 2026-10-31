"""Work pathway: persistently cash-blocked adult amateurs take a job and keep playing (rules 2026-11-03).

An initial calibration of the proposal approved on 31 October 2026 (docs/AMATEUR_WORK_PATHWAY_PROPOSAL.md). It is
an employment-and-golf pathway, not sponsorship, retirement or a promise of success: nobody is given money, no
cost is waived, and the golfer stays an amateur with the part-time salary, living costs and schedule that every
working amateur already has.

Who: a full-time amateur outside college, aged 21 or over, outside the amateur ranking's top 300 (or unranked),
holding no amateur support this season and with no family money left.

The evidence, counted week by week from the weekly access ledger (Season.record_access), for every full-time
non-college amateur (so the groups the pathway leaves out can be measured too):

    counts     'could not afford any event': at least one event they were eligible for that week, and not one
               of them affordable from their spendable funds (support included). Only this week adds one.
    pauses     'injured', 'no suitable event scheduled', 'not eligible for the events scheduled': an injury or a
               gap in the calendar says nothing about money either way, so the count neither grows nor resets.
               Ordinary gaps (an off week, the winter between seasons) therefore never erase the evidence.
    resets     every other week: they played, or could have paid for an event and entered, declined, trained or
               rested (an affordable week, so no longer blocked), or were shut out of a full field (they could
               pay for it).

The decision is made at each monthly plan (every 4 weeks, before the month is planned): a candidate whose count
has reached WEEKS takes a job from that block on, so the month they plan is already a working one. The date, the
weeks counted and the facts behind it are recorded (Season.work_pathway) and written in their career history.
The count carries across the year end and ends when they stop being a full-time non-college amateur.

The way back is unchanged: a working amateur's route to full-time golf is the existing winter decision to turn
professional (careers.p_turn_pro); this pathway adds no return to full-time amateur golf (none existed before).
"""
from __future__ import annotations

from collections import Counter, defaultdict

MIN_AGE = 21
OUTSIDE_TOP = 300
WEEKS = 8                       # counted weeks (pauses not counted, nothing in between resets them)

COUNTS = 'could not afford any event'
PAUSES = ('injured', 'no suitable event scheduled', 'not eligible for the events scheduled')
REASON = 'could not afford to play: took work'


def tracked(g):
    """A full-time amateur outside college: the group whose blocked weeks are counted."""
    return g.status == 'amateur' and g.lifestyle == 'full_time' and not g.tour.startswith('CO_')


def why_not(season, g, year):
    """The reasons a tracked golfer is outside the pathway (empty: a candidate)."""
    out = []
    if g.age(year) < MIN_AGE:
        out.append(f'under {MIN_AGE}')
    rank = season.am_pos.get(g.id)
    if rank is not None and rank <= OUTSIDE_TOP:
        out.append(f'amateur ranking {rank}')
    if g.id in season.am_support:
        out.append('holds amateur support')
    if g.backing > 0:
        out.append('family money left')
    return out


def count(season, g, year, week, why):
    """After the week (Season.record_access): add, pause or reset the golfer's blocked-week count."""
    run = season.cash_blocked
    if not tracked(g):
        run.pop(g.id, None)
        return
    if why == COUNTS:
        run[g.id] += 1
        best = season.cash_blocked_max[year]
        best[g.id] = max(best[g.id], run[g.id])
    elif why not in PAUSES:
        run.pop(g.id, None)


def decide(season, year, week):
    """At a monthly plan: every candidate whose count has reached WEEKS takes a job from this block on."""
    if not season.work_pathway_on:
        return
    for gid, n in sorted(season.cash_blocked.items()):
        if n < WEEKS:
            continue
        g = season.g.get(gid)
        if g is None or not tracked(g) or why_not(season, g, year):
            continue
        g.lifestyle = 'part_time'
        season.cash_blocked.pop(gid, None)
        rec = {'gid': gid, 'year': year, 'week': week, 'age': g.age(year), 'weeks_blocked': n,
               'am_rank': season.am_pos.get(gid), 'cash': round(g.cash), 'reason': REASON}
        season.work_pathway[year].append(rec)
        season.log(gid, year, week, f'Could not afford to play for {n} weeks with no family money left: took a job '
                                    f'at {g.age(year)} and kept playing as an amateur')


def init(season):
    season.cash_blocked = Counter()                 # gid -> blocked weeks counted (see the module note)
    season.cash_blocked_max = defaultdict(Counter)  # year -> gid -> the highest count reached that season
    season.work_pathway = defaultdict(list)         # year -> [transitions with their facts]
