"""Careers: the decisions golfers make between seasons, and the history they leave behind.

Turning professional
    College golfers graduate at 22. The best (by amateur ranking) turn pro; the very best start on
    their region's Challenger tour, the rest on a mini or regional tour. Young amateurs outside college
    turn pro when they are ranked highly. The others keep playing as amateurs and get a job.
Giving up the chase
    A full-time professional below the Challenger tours weighs money against hope. Young players keep
    chasing the dream whatever it costs; from about 25-27, losing money year after year (and running out
    of savings) makes them stop. Hard workers hold on longer; a player who is climbing holds on.
    Those who stop take a job and either keep playing a few local events as part-time professionals,
    become club professionals, or (after a year) regain their amateur status.
Comebacks (rare)
    A part-timer aged 25-40 who wins or contends in their local events — often because their mental
    game has matured with age — may quit their job and make another run at it.
Retirement
    Full-time professionals start retiring in their mid-forties (earlier if they have lost their card),
    club professionals in their early sixties, amateurs and part-timers in their late fifties and sixties.
New golfers
    Every year a new class of 18-year-olds arrives from every nation (its pool, development and pathway
    decide how many and how good) and goes to college or amateur golf.

Every decision is written to the golfer's career history.
"""
from __future__ import annotations

import math
import random

from .calendar import TOUR_BY_KEY
from .cards import home_challenger, home_lower, home_mini
from .development import init_ceilings
from .finance import initial_cash
from .geography import COUNTRIES

AMATEUR_SERIES = {c: k for k, t in TOUR_BY_KEY.items() if t.tier == 6 for c, _ in t.countries}
AMATEUR_BY_REGION = {'North America': 'AM_NORTH_AMERICA', 'Latin America': 'AM_LATAM', 'Europe': 'AM_EUROPE',
                     'Africa': 'AM_AFRICA', 'Middle East': 'AM_ASIA', 'Asia': 'AM_ASIA', 'Oceania': 'AM_OCEANIA'}


def amateur_series(g):
    return AMATEUR_SERIES.get(g.country, AMATEUR_BY_REGION[COUNTRIES[g.country].region])


def _sig(x):
    return 1 / (1 + math.exp(-x))


def tier_of(g):
    t = TOUR_BY_KEY.get(g.tour)
    return t.tier if t else 9


def decide(season, year):
    """End-of-season career decisions for every golfer. Returns counts by decision."""
    rng = random.Random(f'{season.seed}:careers:{year}')
    log = season.log
    counts = {}

    def note(kind):
        counts[kind] = counts.get(kind, 0) + 1

    results = season.season_results(year)
    for g in list(season.world.golfers):
        if g.lifestyle == 'retired':
            continue
        age = g.age(year)
        led = season.ledgers[year].get(g.id)
        net = led.net if led else 0.0
        res = results.get(g.id, {})
        # ---- retirement ---------------------------------------------------------------------
        if g.status == 'club_pro':
            p_ret = _sig((age - 63) / 2.5)
        elif g.lifestyle == 'part_time' or g.status == 'amateur' and not g.tour.startswith('CO_'):
            p_ret = _sig((age - 60) / 3.5)
        else:
            lost = tier_of(g) >= 3
            p_ret = _sig((age - (44 if lost else 48)) / 2.5)
        if g.lifestyle == 'part_time' and g.status in ('amateur', 'pro') and age >= 26:
            p_ret = max(p_ret, 0.05)            # life gets in the way: many part-timers drift away
        if rng.random() < p_ret:
            log(g.id, year, 53, f'Retired from competitive golf at {age}')
            g.lifestyle, g.tour = 'retired', ''
            note('retired')
            continue
        # ---- college graduation and turning professional --------------------------------------
        if g.status == 'amateur':
            am = season.am_pos.get(g.id, 99999)
            if g.tour.startswith('CO_') and age >= 22:
                p_pro = (0.9 if am <= 100 else 0.75 if am <= 300 else 0.55 if g.overall >= 45
                         else 0.3 if g.overall >= 38 else 0.08)          # most decent graduates try
                if rng.random() < p_pro:
                    turn_pro(season, g, year, am, 'after college')
                    note('turned pro')
                else:
                    g.tour, g.lifestyle = amateur_series(g), 'part_time'
                    log(g.id, year, 53, 'Finished college and kept playing as an amateur alongside a job')
                    note('college to amateur')
                continue
            if not g.tour.startswith('CO_') and age <= 26 and (am <= 150 or g.overall >= 45) and rng.random() < 0.35:
                turn_pro(season, g, year, am, 'from the amateur ranks')
                note('turned pro')
                continue
            if g.lifestyle == 'part_time' and 25 <= age <= 40 and res.get('wins', 0) >= 2 and am <= 30 \
                    and rng.random() < 0.15 * g.personality['work_ethic'] / 50:
                turn_pro(season, g, year, am, 'late, after dominating amateur golf')
                note('comeback')
            continue
        if g.status != 'pro':
            continue
        # ---- part-timers: the rare comeback ----------------------------------------------------
        if g.lifestyle == 'part_time':
            if 25 <= age <= 40 and g.cash > 20000:
                form = 0.06 * res.get('wins', 0) + 0.02 * res.get('top3', 0)
                p = min(0.25, form) * (0.5 + g.personality['work_ethic'] / 100)
                if rng.random() < p:
                    g.lifestyle = 'full_time'
                    g.tour = home_mini(g)
                    log(g.id, year, 53, f'Quit their job to make another run at it, aged {age}')
                    note('comeback')
            continue
        # ---- full-time professionals: keep chasing, or stop? -------------------------------------
        tier = tier_of(g)
        if tier <= 2:
            continue
        stress = max(0.0, -net) / 30000 + max(0.0, -g.cash) / 40000
        age_p = max(0.0, min(2.0, (age - 24) / 3))
        climbing = res.get('moved_up', False) or res.get('money_rank_pct', 1.0) <= 0.15
        p_quit = (0.01 + 0.10 * min(3.0, stress) * age_p + 0.02 * max(0, age - 29))
        p_quit *= 1.4 - 0.8 * g.personality['work_ethic'] / 100
        if tier == 3 and g.cash > 0:
            p_quit *= 0.5                       # a regional tour card is a living for many, while it pays
        if climbing:
            p_quit *= 0.4
        if g.cash < -50000 and age > 23:
            p_quit = max(p_quit, 0.5)           # deep in debt: the dream can't be paid for any more
        if rng.random() < min(0.85, p_quit):
            mind = (g.attrs['management'] + g.attrs['composure']) / 2
            r = rng.random()
            if age >= 25 and mind >= 55 and r < 0.15:
                g.status, g.lifestyle, g.tour = 'club_pro', 'part_time', ''
                log(g.id, year, 53, f'Stopped chasing the tour at {age} and became a club professional')
                note('became club pro')
            elif r < 0.5:
                g.status, g.lifestyle, g.tour = 'amateur', 'part_time', amateur_series(g)
                log(g.id, year, 53, f'Stopped chasing the tour at {age}, took a job and regained amateur status')
                note('back to amateur')
            else:
                g.lifestyle, g.tour = 'part_time', home_mini(g)
                log(g.id, year, 53, f'Stopped chasing the tour at {age}; took a job and plays a few local events')
                note('part-time pro')
    return counts


def turn_pro(season, g, year, am_rank, how):
    g.status, g.lifestyle, g.turned_pro = 'pro', 'full_time', year + 1
    if am_rank <= 15:
        g.tour = home_challenger(g)
    elif am_rank <= 60:
        g.tour = home_lower(g)
    else:
        g.tour = home_mini(g)
    season.log(g.id, year, 53, f'Turned professional {how} (amateur ranking {am_rank if am_rank < 99999 else "unranked"}), '
               f'starting on the {TOUR_BY_KEY[g.tour].name}')


def add_juniors(season, year):
    """A new class of 18-year-olds joins the world."""
    from .population import junior_class
    start = max(season.g) + 1
    taken = {g.name for g in season.world.golfers}
    juniors = junior_class(year, season.seed, season.world.nations, start, taken)
    rng = random.Random(f'{season.seed}:juniors:{year}')
    for g in juniors:
        init_ceilings(g, 18, rng)
        g.cash = initial_cash(g, 18, rng.random())
        season.world.golfers.append(g)
        season.g[g.id] = g
        where = TOUR_BY_KEY[g.tour].name if g.tour in TOUR_BY_KEY else 'amateur golf'
        season.log(g.id, year, 1, f'Arrived on the scene at 18 ({where})')
    season.world.by_id = season.g
    return len(juniors)
