"""Careers: the decisions golfers make between seasons, and the history they leave behind.

Every decision is a probability built from things the golfer can actually see about themselves —
the completed season's results (snapshotted before tour cards change), their money, their health,
their next season's opportunity, and their own willingness — combined smoothly. There are no age
cut-offs, debt cliffs or tour-level immunities; each factor shifts the odds, and the log records why.

    money       runway: how many years their funds (savings, backers, limited credit) would cover
                the gap between what golf costs them and what their own record says it earns
    progress    promotion to a better tour, a rising world ranking, wins and top-10s. Progress buys
                time only in proportion to how well the next year is funded: it creates no money.
    opportunity the card they hold for next season (a Premier card is worth more than a mini tour)
    health      weeks lost to injury this season and lasting damage from serious injuries
    willingness work ethic and appetite for the big stage
    age         a gradual shift in life priorities, never a cliff

Competition rules are separate from choices: college eligibility ends at 22 (so a graduating golfer
must decide what's next), Q-School and tour cards decide where a professional may play.

Decisions: give up the chase (and take a job: part-time professional, regained amateur status or club
professional — or join the profession as a coach or caddie, see staff.py), retire from competitive golf,
make a comeback, turn professional. New juniors arrive
every year. Every decision is written to the golfer's career history.
"""
from __future__ import annotations

import math
import random

from .calendar import TOUR_BY_KEY
from .cards import home_challenger, home_lower, home_mini
from .development import EXPERIENCE_ROUNDS, init_ceilings
from . import finance as FIN
from . import prestige as PR
from . import staff as ST
from .finance import initial_backing, initial_cash
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


LIFE_AGE = 26.0            # around here the pull of an ordinary life grows fastest (smoothly)


def life_stage(age):
    """How much an ordinary life (a steady income, family) pulls against chasing golf, by age: small
    for a 22-year-old, growing through the mid-twenties, still creeping up in the thirties. A smooth
    curve, not a cut-off: it shifts the odds, money and results decide them."""
    return 2.0 * (_sig((age - LIFE_AGE) / 2.0) - 0.5) + 0.04 * max(0.0, age - 32)


def _tour_economics(season, tour):
    """Typical purse and travel cost of a tour's events (for a golfer's own budget estimate)."""
    cache = season.__dict__.setdefault('_tour_econ', {})
    if tour not in cache:
        ss = [x for x in season.cal.series if x.tour == tour]
        t = TOUR_BY_KEY.get(tour)
        purse = sum(x.purse for x in ss) / len(ss) if ss else 0.0
        cost = FIN.EVENT_COST.get(t.tier if t else 4, 600) * FIN.TRAVEL['region']
        if t and t.tier == 4 and ss:
            cost += 1.1 * purse / max(1, ss[0].field)
        cache[tour] = (purse, cost)
    return cache[tour]


def season_shortfall(season, g, tour, events, last_prize=None, without_backers=False):
    """What a season chasing golf on `tour` would cost a golfer beyond what it brings in, judged from
    their own record: expected prize money (the share of purses they have been winning, weighed equally
    with what they actually won in the season just played, so a season spent unable to afford events
    counts) net of the caddie's and a scouting coach's shares (and the backers', unless
    `without_backers`), their sponsor contract, against trips and committed weekly costs. 0 or less: the
    season pays for itself."""
    purse, cost = _tour_economics(season, tour)
    income = season.prize_share.get(g.id, FIN.PRIOR_PRIZE_SHARE) * purse * events
    if last_prize is not None:
        income = 0.5 * income + 0.5 * last_prize
    kept = season.prize_kept(g) + (FIN.BACKER_SHARE if without_backers and g.backer else 0.0)
    income = income * kept + PR.endorsements(season.player_prestige(g.id))
    k = season.staff.caddie(g.id)
    costs = events * (cost + (k.weekly_fee if k else 0.0)) + 52 * season.committed_weekly(g)
    return costs - income


def runway_years(season, g, year, tour, events, last_prize=None, own_money=False):
    """Years a golfer's funds would last chasing golf on `tour` (season_shortfall); 10 = self-funding or
    funds for ten seasons. `own_money`: count only savings, family money and backers' money (next
    season's deal included), not what a lender would advance -- a line of credit pays for a few weeks,
    not for another season."""
    shortfall = season_shortfall(season, g, tour, events, last_prize)
    if shortfall <= 0:
        return 10.0
    funds = (max(0.0, g.cash + g.backing + max(g.backer_funds, g.backer)) if own_money
             else max(0.0, season.funds(g, year + 1)))
    return min(10.0, funds / shortfall)


SELF_FUNDED_SEASONS = 3          # own savings covering this many seasons of losses: no need of backers


def own_way(season, g, year, row):
    """Whether a backed golfer could pay their own way without backers, and why: their own expected
    winnings and sponsors cover a season (backers' share not taken), or their own savings (cash alone:
    not family money, not the backers' money being withdrawn, not credit) cover SELF_FUNDED_SEASONS
    seasons of losses. None if not."""
    shortfall = season_shortfall(season, g, g.tour, season.target_events(g), row.get('prize', 0.0),
                                 without_backers=True)
    if shortfall <= 0:
        return 'their winnings and sponsors now cover a season'
    if g.cash >= SELF_FUNDED_SEASONS * shortfall:
        return f'their own savings now cover {g.cash / shortfall:.0f} seasons'
    return None


def end_backing(season, g, year, why):
    """A backing deal ends: backers stop putting up money, the undrawn part of theirs goes back to them,
    and their share of winnings ends with it (family money stays the golfer's)."""
    g.backer, g.backer_funds, g.backer_stale = 0.0, 0.0, 0
    if why:
        season.log(g.id, year, 53, why)


def progress_signal(row):
    """Observable progress from the completed season: promotion, ranking movement, results."""
    p = 0.6 if row.get('promoted') else 0.0
    p -= 0.4 if row.get('demoted') else 0.0
    start, end = row.get('wr_start'), row.get('wr_end')
    if start and end:
        p += max(-0.6, min(0.6, 0.35 * math.log(start / end)))
    elif end and not start:
        p += 0.3                                   # newly ranked
    p += 0.35 * min(2, row.get('wins', 0)) + 0.06 * min(5, row.get('top10', 0))
    return max(-1.0, min(2.0, p))


OPPORTUNITY = {1: 1.0, 2: 0.7, 3: 0.4, 4: 0.15}
LEVEL_NAME = {1: 'Premier Tour', 2: 'Challenger Tour', 3: 'regional tour', 4: 'mini-tour', 5: 'college',
              6: 'amateur', 9: 'club'}


def level_name(row):
    return LEVEL_NAME.get(row.get('tier', 9), 'club') if row.get('status') != 'amateur' else 'amateur'


def lasting_damage(season, gid, year, years=3):
    return sum(1 for y, _, t in season.history.get(gid, ()) if y > year - years and 'lasting damage' in t)


def desire_to_continue(season, g, row, year):
    """How much a golfer *wants* another season, from reasons they can see (logit units): progress
    they have made, the card they have earned for next season, a significant event they have already
    secured a place in, their health, their own willingness, and the pull of an ordinary life.
    This is a reason to accept another losing season; it creates no money — what they can actually
    afford to enter is still decided week by week from their funds."""
    tier = TOUR_BY_KEY[g.tour].tier if g.tour in TOUR_BY_KEY else 4
    will = (g.personality['work_ethic'] + g.personality['big_stage']) / 200
    return (1.2 * progress_signal(row) + 1.5 * OPPORTUNITY.get(tier, 0.15) + 0.8 * min(1, len(row.get('secured', ())))
            + 1.5 * (will - 0.5) - life_stage(g.age(year))
            - 0.05 * row.get('injury_weeks', 0) - 0.6 * lasting_damage(season, g.id, year))


def p_stop_chasing(season, g, row, year):
    """Chance a full-time professional gives up the chase this winter (every tier): money pressure
    (1 / (1 + runway)) against their desire to continue. Under half a season of money of their own
    (savings and backers), wanting to continue is not enough: the season cannot be paid for, so the
    pressure rises steeply (smoothly) as the runway runs out."""
    runway = runway_years(season, g, year, g.tour, season.target_events(g), row.get('prize', 0.0), own_money=True)
    pressure = 1 / (1 + runway)                    # 1 = broke and losing money, ~0 = self-funding
    desire = desire_to_continue(season, g, row, year)
    x = -4.5 + 4.0 * pressure + 2.2 * max(0.0, 1 - 2 * runway) - desire
    return _sig(x), {'runway': runway, 'progress': progress_signal(row), 'desire': desire,
                     'secured': list(row.get('secured', ()))}


def review_backers(season, g, row, year, rng):
    """Each winter, a full-time professional's backers decide on next season from what they can see:
    progress (promotion, a rising ranking, wins, top-10s) renews the deal; two seasons in a row
    without it, or the golfer passing BACKER_AGE, ends it; so does the golfer paying their own way.
    A young professional without backers can attract them with a breakthrough season."""
    age = g.age(year) + 1
    progress = progress_signal(row)
    if g.backer:
        why = own_way(season, g, year, row)
        if why:
            end_backing(season, g, year, f'Paying their own way now ({why}); their backers stepped aside')
            return 'backers no longer needed'
        g.backer_stale = 0 if progress > 0.1 else g.backer_stale + 1
        if g.backer_stale >= 2 or age > FIN.BACKER_AGE:
            end_backing(season, g, year, 'Their backers withdrew (no progress to show for two seasons)'
                        if age <= FIN.BACKER_AGE else 'Their backers withdrew')
            return 'backers withdrew'
        return None
    paying = season_shortfall(season, g, g.tour, season.target_events(g), row.get('prize', 0.0)) <= 0
    if not paying and age <= FIN.BACKER_AGE and (row.get('wins', 0) or row.get('promoted') or progress >= 0.6) and rng.random() < 0.5:
        g.backer = FIN.backer_deal(age, max(0.6, amateur_standing(row.get('wr_end'))), 0.0, rng.random())
        g.backer_stale = 0
        season.log(g.id, year, 53, f'Found backers after their season (${g.backer:,.0f} a season for a share of winnings)')
        return 'found backers'
    return None


def p_retire(season, g, row, year):
    """Chance of retiring from competitive golf altogether."""
    age = g.age(year)
    inj = 0.06 * row.get('injury_weeks', 0) + 0.8 * lasting_damage(season, g.id, year)
    if g.status == 'club_pro':
        # the club job goes on; competing winds down from their fifties (about 5% a year at 45, 15% at 55)
        x = -4.0 + 0.15 * (age - 40) + inj
    elif g.lifestyle == 'part_time':
        # work and family crowd competition out, least for those still playing often and well: most
        # golfers who took a job after the tour, and adult amateurs, compete for a few years (about one
        # in five stops each year), the good and keen ones for much longer
        engaged = min(1.0, row.get('events', 0) / 6) + 0.3 * min(2, row.get('top10', 0))
        rank = row.get('am_end') if g.status == 'amateur' else row.get('wr_end')
        x = -0.4 + 0.06 * (age - 35) - 0.8 * engaged - 1.5 * amateur_standing(rank) + inj
    else:
        tier = TOUR_BY_KEY[g.tour].tier if g.tour in TOUR_BY_KEY else 4
        standing = 1 - row.get('money_rank_pct', 1.0) if row.get('status') == 'pro' else 0.5
        x = -6.5 + 0.22 * (age - 30) + 1.2 * (1 - standing) - 1.0 * OPPORTUNITY.get(tier, 0.15) + inj
    return _sig(x)


def amateur_standing(rank):
    """1 for the No.1 (amateur or world ranking), about 0.3 at No.300, 0 if unranked."""
    if not rank:
        return 0.0
    return max(0.0, 1 - math.log10(rank) / math.log10(3000))


def p_turn_pro(season, g, row, year, graduating):
    age = g.age(year)
    standing = amateur_standing(row.get('am_end'))
    means = min(2.0, (max(0.0, g.cash) + g.backing) / 40000)
    will = (g.personality['work_ethic'] + g.personality['big_stage']) / 200
    if graduating:
        x = -0.6 + 3.0 * standing + 0.6 * means + 1.0 * (will - 0.5) + 0.3 * min(2, row.get('wins', 0))
    else:
        x = (-5.0 + 4.5 * standing + 0.6 * means + 1.0 * (will - 0.5) + 0.4 * min(2, row.get('wins', 0))
             - 0.15 * abs(age - 21))
    return _sig(x)


def p_amateur_job(season, g, row, year):
    """An adult amateur outside college, living on savings and family help, taking a job and playing
    alongside it (as college graduates who stay amateur do). Smooth in age, pushed by debt and a short
    runway, held back by money to keep going; their hope of turning professional is p_turn_pro's."""
    age = g.age(year)
    runway = runway_years(season, g, year, g.tour, max(8, row.get('events', 0)))
    x = -1.2 + 0.8 * (age - 22) - 0.4 * min(runway, 5.0) + (1.0 if g.cash < 0 else 0.0)
    return _sig(x)


def p_comeback(season, g, row, year):
    """A part-timer quitting their job to make another full-time run at it."""
    age = g.age(year)
    signal = (1.0 * min(3, row.get('wins', 0)) + 0.4 * min(4, row.get('top3', 0))
              + 0.6 * max(0.0, progress_signal(row)))
    funded = min(1.0, (max(0.0, g.cash) + g.backing) / (FIN.LIVING + 15 * 900))   # a year on tour paid for?
    will = (g.personality['work_ethic'] + g.personality['big_stage']) / 200
    # results give the desire, money the means: separate terms (desire alone does not pay for a season)
    x = (-7.0 + 1.1 * signal + 0.9 * funded - 0.10 * (age - 30) - 0.05 * row.get('injury_weeks', 0)
         + 1.5 * (will - 0.5))
    return _sig(x)


def decide(season, year, snap):
    """End-of-season career decisions. `snap` is the completed season's evidence (season_snapshot),
    taken before tour cards changed membership; promotion is in it as a separate fact."""
    rng = random.Random(f'{season.seed}:careers:{year}')
    log = season.log
    counts = {}

    trans = season.transitions.setdefault(year, [])

    def note(kind, g, **why):
        """Count the decision and record it with its reasons (for reports and checks)."""
        counts[kind] = counts.get(kind, 0) + 1
        trans.append({'gid': g.id, 'kind': kind, 'age': g.age(year), **why})

    for g in sorted(season.world.golfers, key=lambda x: x.id):     # order never matters
        if g.lifestyle == 'retired':
            continue
        row = snap.get(g.id, {})
        age = g.age(year)
        college = g.tour.startswith('CO_')
        # ---- retirement ---------------------------------------------------------------------
        p_ret = p_retire(season, g, row, year) if not college else 0.0
        if not college and rng.random() < p_ret:
            role = ST.former_golfer_role(season, g, year, rng, level_name(row)) if g.status != 'amateur' or age >= 23 \
                else None
            if role is None:
                log(g.id, year, 53, f'Retired from competitive golf at {age}')
            g.lifestyle, g.tour = 'retired', ''
            note(f'became {role}' if role else 'retired', g, p=round(p_ret, 4), via='retirement',
                 injury_weeks=row.get('injury_weeks', 0), events=row.get('events', 0))
            continue
        # ---- amateurs: graduation (an eligibility rule) and turning professional ---------------
        if g.status == 'amateur':
            graduating = college and age >= 22                     # college eligibility ends
            if graduating or not college:
                p_pro = p_turn_pro(season, g, row, year, graduating)
                if rng.random() < p_pro:
                    turn_pro(season, g, year, row.get('am_end') or 99999,
                             'after college' if graduating else
                             'late, after years as an amateur' if g.lifestyle == 'part_time' and age >= 27
                             else 'from the amateur ranks')
                    note('turned pro' if not (g.lifestyle == 'part_time' and age >= 27) else 'comeback', g,
                         p=round(p_pro, 4), am_rank=row.get('am_end'), graduating=graduating)
                elif graduating:
                    g.tour, g.lifestyle = amateur_series(g), 'part_time'
                    log(g.id, year, 53, 'College eligibility ended; kept playing as an amateur alongside a job')
                    note('college to amateur', g, p=round(1 - p_pro, 4), am_rank=row.get('am_end'))
                elif g.lifestyle == 'full_time' and age >= 19:
                    p_job = p_amateur_job(season, g, row, year)
                    if rng.random() < p_job:
                        g.lifestyle = 'part_time'
                        log(g.id, year, 53, f'Took a job at {age} and kept playing as an amateur')
                        note('amateur took a job', g, p=round(p_job, 4), am_rank=row.get('am_end'),
                             cash=round(g.cash))
            continue
        if g.status != 'pro':
            continue
        # ---- part-timers: a comeback? --------------------------------------------------------
        if g.lifestyle == 'part_time':
            p_cb = p_comeback(season, g, row, year)
            if rng.random() < p_cb:
                g.lifestyle = 'full_time'
                g.tour = home_mini(g)
                log(g.id, year, 53, f'Quit their job to make another run at it, aged {age}')
                note('comeback', g, p=round(p_cb, 4), wins=row.get('wins', 0), top3=row.get('top3', 0))
            continue
        # ---- full-time professionals (every tier): backers decide first, then keep chasing or stop --
        change = review_backers(season, g, row, year, rng)
        if change:
            note(change, g, backer=round(g.backer), progress=round(progress_signal(row), 2))
        p, why = p_stop_chasing(season, g, row, year)
        if rng.random() < p:
            why = dict(p=round(p, 4), runway=round(why['runway'], 2), progress=round(why['progress'], 2),
                       desire=round(why['desire'], 2), secured=why['secured'], tier=row.get('tier'),
                       net=round(row.get('net', 0.0)), events=row.get('events', 0))
            role = ST.former_golfer_role(season, g, year, rng, level_name(row))
            if role is not None:                                    # off to coach or caddie
                g.lifestyle, g.tour = 'retired', ''
                note(f'became {role}', g, via='stopped chasing', **why)
                continue
            mind = (g.attrs['management'] + g.attrs['composure']) / 200
            earned = season.career_prize.get(g.id, 0.0)
            r = rng.random()
            reason = f'runway {why["runway"]:.1f} yrs, progress {why["progress"]:+.1f}, desire {why["desire"]:+.1f}'
            p_club = 0.25 * mind * min(1.0, max(0.0, age - 22) / 8)
            p_am = 0.45 * math.exp(-earned / 250000)        # reinstatement suits those who never earned much
            if r < p_club:
                g.status, g.lifestyle, g.tour = 'club_pro', 'part_time', ''
                log(g.id, year, 53, f'Stopped chasing the tour at {age} and became a club professional ({reason})')
                note('became club pro', g, **why)
            elif r < p_club + p_am:
                g.status, g.lifestyle, g.tour = 'amateur', 'part_time', amateur_series(g)
                log(g.id, year, 53, f'Stopped chasing the tour at {age}, took a job and regained amateur status ({reason})')
                note('back to amateur', g, **why)
            else:
                g.lifestyle, g.tour = 'part_time', home_mini(g)
                log(g.id, year, 53, f'Stopped chasing the tour at {age}; took a job and plays a few local events ({reason})')
                note('part-time pro', g, **why)
    for g in season.world.golfers:                   # backers fund only a full-time chase
        if (g.backer or g.backer_funds) and not (g.status == 'pro' and g.lifestyle == 'full_time'):
            end_backing(season, g, year, 'Their backing deal ended when they stopped chasing the tour'
                        if g.lifestyle != 'retired' else None)
    return counts


def turn_pro(season, g, year, am_rank, how):
    g.status, g.lifestyle, g.turned_pro = 'pro', 'full_time', year + 1
    rng = random.Random(f'{season.seed}:backers:{year}:{g.id}')
    g.backer = FIN.backer_deal(g.age(year) + 1, amateur_standing(am_rank if am_rank < 99999 else None),
                               rng.random(), rng.random())
    g.backer_stale = 0
    if am_rank <= 15:
        g.tour = home_challenger(g)
    elif am_rank <= 60:
        g.tour = home_lower(g)
    else:
        g.tour = home_mini(g)
    season.log(g.id, year, 53, f'Turned professional {how} (amateur ranking {am_rank if am_rank < 99999 else "unranked"}), '
               f'starting on the {TOUR_BY_KEY[g.tour].name}'
               + (f', with backers putting up ${g.backer:,.0f} a season for a share of winnings' if g.backer
                  else ', paying their own way'))


def add_new_professionals(season, year):
    """This year's new professionals from outside the tracked amateur game (population.new_professionals):
    they start on their home mini tour, with savings and perhaps backers like any new professional."""
    from .population import new_professionals
    start = season.world.next_id
    taken = {g.name for g in season.world.golfers} | season.staff.taken
    arrivals = new_professionals(year, season.seed, season.world.nations, start, taken)
    season.world.next_id = start + len(arrivals)
    rng = random.Random(f'{season.seed}:new-pros:{year}')
    for g in arrivals:
        age = g.age(year)
        init_ceilings(g, age, rng)
        g.cash = initial_cash(g, age, rng.random())
        g.status, g.lifestyle, g.tour = 'pro', 'full_time', home_mini(g)
        g.backer = FIN.backer_deal(age, 0.2, rng.random(), rng.random())     # no ranking to show backers
        season.world.golfers.append(g)
        season.g[g.id] = g
        season.prior_rounds[g.id] = (year, EXPERIENCE_ROUNDS)    # seasons of competition behind them (fading)
        season.log(g.id, year, 1, f'Turned professional at {age}, starting on the {TOUR_BY_KEY[g.tour].name}'
                   + (f', with backers putting up ${g.backer:,.0f} a season' if g.backer else ', paying their own way'))
    season.world.by_id = season.g
    return len(arrivals)


def add_juniors(season, year):
    """A new class of 18-year-olds joins the world."""
    from .population import junior_class
    start = season.world.next_id                     # ids come from the world's single person registry
    taken = {g.name for g in season.world.golfers} | season.staff.taken
    juniors = junior_class(year, season.seed, season.world.nations, start, taken)
    season.world.next_id = start + len(juniors)
    rng = random.Random(f'{season.seed}:juniors:{year}')
    for g in juniors:
        init_ceilings(g, 18, rng)
        g.cash = initial_cash(g, 18, rng.random())
        g.backing = initial_backing(18, rng.random(), rng.random())
        season.world.golfers.append(g)
        season.g[g.id] = g
        season.prior_rounds[g.id] = (year, EXPERIENCE_ROUNDS)    # a junior season of competition behind them (fading)
        where = TOUR_BY_KEY[g.tour].name if g.tour in TOUR_BY_KEY else 'amateur golf'
        season.log(g.id, year, 1, f'Arrived on the scene at 18 ({where})')
    season.world.by_id = season.g
    return len(juniors)
