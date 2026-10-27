"""Coaches and caddies: the people around the players.

Coaches
    Every coach has a **speciality** (physical, long game, short game, putting or mental — the training
    categories), a **teaching** skill, a **scouting** skill and a **reputation** (what golfers can see:
    it grows with their students' success). Some coaches specialise in **young players** (22 and under).
    A golfer has at most one coach at a time. A coach makes training count for more (most in their
    speciality, and for young players if that is their gift) and helps the golfer read their own game
    (what to work on). Without a coach a golfer teaches themselves.

    Golfers get a coach in one of two ways:
      * they hire one they can afford (a yearly fee that grows with the coach's reputation) — so many
        college players and amateurs have none;
      * a coach approaches them. Coaches scout young, raw players near them; they estimate potential
        through the noise of their own scouting skill and approach those they believe in, coaching for
        free in return for a share of future prize money.

Caddies
    A caddie has the six caddie skills the shot engine uses (strategy and yardage help course management,
    mental support helps composure and recovering from bad holes, green reading helps putts,
    communication decides how much of it reaches the player) and builds **familiarity with every course
    they work**, like a player does. Professionals on the bigger tours hire a caddie they can afford —
    the best players attract the best caddies — and pay a weekly fee plus a share of winnings. Everyone
    else carries their own bag (or brings a friend): weaker help than any professional caddie.

Where they come from
    Former golfers. When a golfer gives up the chase or retires they may become a coach (a teaching mind:
    course management, green reading, coachability, work ethic) or a caddie (management, composure,
    green reading), younger more often for caddies. Golfers who have made a fortune rarely do — they do
    not need the money. The starting world's coaches and caddies, and any outside hires needed when
    demand outgrows the profession, are generated with a short background (club caddies, teaching
    professionals) and labelled as such.

Every coach and caddie has a history (hired, let go, retired), and their golfers' histories record them.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from .calendar import TOUR_BY_KEY
from .development import CATEGORIES, perceived_gap
from .geography import COUNTRIES
from .golfer import CADDIE_SKILLS, Caddie
from .names import make_name

SPECIALITIES = tuple(CATEGORIES)                  # physical, long_game, short_game, putting, mental
SELF_TEACHING = 0.3                               # coaching quality of a golfer with no coach
YOUTH_AGE = 22
SCOUT_AGE = 23                                    # coaches scout players this age and younger
SCOUT_SHARE = 0.05                                # of prize money, for a coach who approached the player
CADDIE_TIERS = 2                                  # tour tiers whose members hire professional caddies
SELF_CADDIE = 40.0                                # skills of carrying your own bag / a friend on the bag
COACH_RETIRE_AGE, CADDIE_RETIRE_AGE = 68.0, 60.0


def _clip(x, lo=5.0, hi=99.0):
    return max(lo, min(hi, x))


def _sig(x):
    return 1 / (1 + math.exp(-x))


# ---- the people -------------------------------------------------------------------------------------
@dataclass
class Coach:
    id: int
    name: str
    country: str
    born: int
    speciality: str                    # a training category
    youth: bool                        # specialises in developing young players
    teaching: float                    # 0-100: how much their coaching helps (hidden)
    scouting: float                    # 0-100: how well they judge a young player's potential (hidden)
    reputation: float                  # 0-100: what golfers see; grows with their students' success
    background: str = ''
    former_golfer: int = 0             # golfer id if they were a golfer in this world
    status: str = 'active'             # 'active' / 'retired'
    earnings: float = 0.0
    history: list = field(default_factory=list)      # [(year, text)]

    @property
    def capacity(self):
        return 3 + int(self.teaching / 12)

    @property
    def fee(self):
        """Yearly fee for a paying student."""
        return round(3000 * math.exp(self.reputation / 30), -2)

    def age(self, year):
        return year - self.born


@dataclass
class TourCaddie(Caddie):
    id: int = 0
    country: str = ''
    born: int = 0
    reputation: float = 50.0           # what players see; grows with their employers' success
    background: str = ''
    former_golfer: int = 0
    status: str = 'active'
    earnings: float = 0.0
    seasons: int = 0                   # seasons worked on a tour
    history: list = field(default_factory=list)

    @property
    def weekly_fee(self):
        return round(800 + 25 * self.reputation, -1)

    def age(self, year):
        return year - self.born


def self_caddie():
    """Carrying their own bag, or a friend: no professional reads or course book."""
    c = Caddie('Own bag', {k: SELF_CADDIE for k in CADDIE_SKILLS})
    c.skills['communication'] = 50.0
    return c


SELF_CADDIE_OBJ = self_caddie()


# ---- aptitudes of former golfers --------------------------------------------------------------------
def coach_aptitude(g):
    a, p = g.attrs, g.personality
    return (0.30 * a['management'] + 0.20 * a['green_reading'] + 0.25 * p['coachability'] + 0.25 * p['work_ethic']) / 100


def caddie_aptitude(g):
    a = g.attrs
    return (0.40 * a['management'] + 0.30 * a['composure'] + 0.30 * a['green_reading']) / 100


def need_for_money(g):
    """1 for a golfer with little saved; close to 0 for someone who made a fortune from the game."""
    return math.exp(-max(0.0, g.cash) / 1_500_000)


def p_become_coach(g, age):
    return 0.10 * need_for_money(g) * _sig(12 * (coach_aptitude(g) - 0.55)) * _sig((62 - age) / 3)


def p_become_caddie(g, age):
    return 0.12 * need_for_money(g) * _sig(12 * (caddie_aptitude(g) - 0.55)) * _sig((55 - age) / 3)


def strongest_category(g):
    over = g.overall
    return max(SPECIALITIES, key=lambda c: (sum(g.attrs[k] for k in CATEGORIES[c]) / len(CATEGORIES[c]) - over, c))


# ---- the staff of the world -------------------------------------------------------------------------
class Staff:
    """All coaches and caddies, and who works with whom."""

    def __init__(self):
        self.coaches = {}              # id -> Coach
        self.caddies = {}              # id -> TourCaddie
        self.coach_of = {}             # golfer id -> coach id
        self.deal = {}                 # golfer id -> 'fee' or 'share'
        self.caddie_of = {}            # golfer id -> caddie id
        self.taken = set()             # names in use
        self._next = 1

    def _id(self):
        self._next += 1
        return self._next - 1

    # -- creating people --------------------------------------------------------------------------
    def new_coach(self, rng, country, year, age, teaching, scouting, speciality, youth, reputation, background,
                  former=0, name=None):
        c = Coach(self._id(), name or make_name(country, rng, self.taken), country, year - age, speciality, youth,
                  round(_clip(teaching), 1), round(_clip(scouting), 1), round(_clip(reputation, 1.0), 1),
                  background, former)
        self.taken.add(c.name)
        self.coaches[c.id] = c
        return c

    def new_caddie(self, rng, country, year, age, skills, reputation, background, former=0, name=None):
        k = TourCaddie(name or make_name(country, rng, self.taken), {s: round(_clip(v), 1) for s, v in skills.items()},
                       id=self._id(), country=country, born=year - age, reputation=round(_clip(reputation, 1.0), 1),
                       background=background, former_golfer=former)
        self.taken.add(k.name)
        self.caddies[k.id] = k
        return k

    def generated_coach(self, rng, country, year, background='a teaching professional'):
        age = int(rng.uniform(30, 66))
        teaching = rng.gauss(50, 14)
        return self.new_coach(rng, country, year, age, teaching, rng.gauss(50, 15),
                              rng.choices(SPECIALITIES, (0.15, 0.25, 0.2, 0.2, 0.2))[0], rng.random() < 0.3,
                              teaching + rng.gauss(0, 10) + 0.3 * (age - 40), background)

    def generated_caddie(self, rng, country, year, background='a club caddie'):
        age = int(rng.uniform(24, 58))
        base = rng.gauss(50, 9) + 0.25 * (age - 35)
        skills = {s: base + rng.gauss(0, 8) for s in CADDIE_SKILLS}
        return self.new_caddie(rng, country, year, age, skills, sum(skills.values()) / 6 + rng.gauss(0, 8), background)

    def from_golfer(self, g, year, role, rng, level):
        """A former golfer becomes a coach or a caddie; their game shapes their skills."""
        a, p = g.attrs, g.personality
        age = g.age(year)
        where = f'former {level} golfer'
        if role == 'coach':
            teaching = (100 * coach_aptitude(g) + 0.15 * (g.overall - 55) + rng.gauss(0, 8))
            scouting = 0.4 * a['management'] + 0.3 * p['adaptability'] + 15 + rng.gauss(0, 10)
            c = self.new_coach(rng, g.country, year, age, teaching, scouting, strongest_category(g),
                               rng.random() < 0.15 + 0.3 * p['coachability'] / 100,
                               20 + 0.35 * (g.overall - 40) + rng.gauss(0, 6), where, g.id, g.name)
            c.history.append((year, f'Became a coach ({c.speciality.replace("_", " ")} specialist'
                                    f'{", young players" if c.youth else ""}) after a career as a {level} golfer'))
            return c
        skills = {'strategy': a['management'], 'green_reading': a['green_reading'],
                  'yardage': (a['focus'] + a['management']) / 2, 'course_knowledge': 0.5 * a['management'] + 25,
                  'mental_support': (a['composure'] + a['resilience']) / 2, 'communication': p['adaptability']}
        skills = {s: v + rng.gauss(0, 6) for s, v in skills.items()}
        k = self.new_caddie(rng, g.country, year, age, skills, sum(skills.values()) / 6 - 5, where, g.id, g.name)
        k.history.append((year, f'Became a caddie after a career as a {level} golfer'))
        return k

    # -- effects --------------------------------------------------------------------------------------
    def coach(self, gid):
        cid = self.coach_of.get(gid)
        return self.coaches.get(cid) if cid else None

    def caddie(self, gid):
        kid = self.caddie_of.get(gid)
        return self.caddies.get(kid) if kid else None

    def coaching(self, g, category, age):
        """Coaching quality (0-1) for this golfer training this category this week."""
        c = self.coach(g.id)
        if c is None:
            return SELF_TEACHING
        q = c.teaching / 100
        if category == c.speciality:
            q += 0.15
        if c.youth and age <= YOUTH_AGE:
            q += 0.15
        return min(1.0, q)

    def insight(self, g):
        """How well the golfer's coach reads their game (0 without a coach)."""
        c = self.coach(g.id)
        return c.teaching / 100 if c else 0.0

    def bag(self, g):
        """The caddie on this golfer's bag this week (their own bag if they have no caddie)."""
        return self.caddie(g.id) or SELF_CADDIE_OBJ


def initial_staff(world, seed):
    """The starting world's coaches and caddies (generated: the world has no recorded past)."""
    rng = random.Random(f'{seed}:staff')
    st = Staff()
    st.taken = {g.name for g in world.golfers}
    year = world.year
    pool = {c: p.pool for c, p in world.nations.items()}
    total = sum(pool.values())
    for country, w in sorted(pool.items()):
        for _ in range(max(1, round(320 * w / total))):
            st.generated_coach(rng, country, year)
    bags = {}
    for g in world.golfers:
        t = TOUR_BY_KEY.get(g.tour)
        if g.status == 'pro' and t and t.tier <= CADDIE_TIERS:
            bags[g.country] = bags.get(g.country, 0) + 1
    for country, n in sorted(bags.items()):
        for _ in range(round(n * 1.15) + 1):
            st.generated_caddie(rng, country, year)
    return st


def region(country):
    return COUNTRIES[country].region


# ---- the yearly market -------------------------------------------------------------------------------
def coach_budget(season, g, year):
    """What a golfer can put towards coaching this year."""
    led = season.ledgers.get(year - 1, {}).get(g.id)
    earned = (led.prize + led.sponsors + led.salary + led.work) if led else 0.0
    return 0.10 * max(0.0, season.spendable(g, year)) + 0.08 * earned


def caddie_budget(season, g, year):
    """What a golfer can put towards a caddie: a share of their funds and of the prize money their own
    record says they will win on their tour this season."""
    from .careers import _tour_economics
    purse, _ = _tour_economics(season, g.tour)
    expected = season.prize_share.get(g.id, 0.004) * purse * season.target_events(g)
    return 0.25 * (max(0.0, season.spendable(g, year)) + expected)


def wants_caddie(g):
    t = TOUR_BY_KEY.get(g.tour)
    return g.status == 'pro' and g.lifestyle == 'full_time' and t is not None and t.tier <= CADDIE_TIERS


def start_of_season(season, year):
    """Coaches scout, golfers hire and drop coaches, and caddies are hired for the season."""
    st = season.staff
    rng = random.Random(f'{season.seed}:staff-market:{year}')
    log = season.log
    active = [g for g in sorted(season.world.golfers, key=lambda x: x.id) if g.lifestyle != 'retired']
    students = {}
    for gid, cid in st.coach_of.items():
        students[cid] = students.get(cid, 0) + 1

    def leave_coach(g, why):
        cid = st.coach_of.pop(g.id)
        st.deal.pop(g.id, None)
        students[cid] -= 1
        c = st.coaches[cid]
        c.history.append((year, f'Stopped coaching {g.name} ({why})'))
        log(g.id, year, 1, f'Left coach {c.name} ({why})')

    def take_coach(g, c, deal, why):
        st.coach_of[g.id] = c.id
        st.deal[g.id] = deal
        students[c.id] = students.get(c.id, 0) + 1
        c.history.append((year, f'Began coaching {g.name} ({why})'))
        log(g.id, year, 1, f'{"Approached by" if deal == "share" else "Hired"} coach {c.name} '
                           f'({c.speciality.replace("_", " ")} specialist{", young players" if c.youth else ""}; {why})')

    # golfers who can no longer pay their coach, or retired, leave them
    for g in season.world.golfers:
        if g.id in st.coach_of:
            if g.lifestyle == 'retired' or st.coaches[st.coach_of[g.id]].status != 'active':
                leave_coach(g, 'coach retired' if g.lifestyle != 'retired' else 'retired from golf')
            elif st.deal.get(g.id) == 'fee' and st.coaches[st.coach_of[g.id]].fee > 1.5 * coach_budget(season, g, year):
                leave_coach(g, 'could no longer afford the fee')
    coaches = [c for c in st.coaches.values() if c.status == 'active']
    by_region = {}
    for c in coaches:
        by_region.setdefault(region(c.country), []).append(c)
    # 1. scouting: coaches approach young, raw players they believe in
    young = [g for g in active if g.age(year) <= SCOUT_AGE and g.status in ('amateur', 'pro')]
    near = {}
    for g in young:
        near.setdefault(g.country, []).append(g)
    for c in sorted(coaches, key=lambda c: (-c.reputation, c.id)):
        free = c.capacity - students.get(c.id, 0)
        if free <= 0:
            continue
        pool = list(near.get(c.country, ()))
        if c.reputation >= 60:                        # well-known coaches look further afield
            pool += [g for cc, gs in near.items() if cc != c.country and region(cc) == region(c.country) for g in gs]
        if not pool:
            continue
        crng = random.Random(f'{season.seed}:scout:{year}:{c.id}')
        look = crng.sample(pool, min(60, len(pool)))
        sd = 3 + 12 * (1 - c.scouting / 100)
        bar = 50 + 0.35 * c.reputation                # top coaches only approach the best prospects
        picks = []
        for g in sorted(look, key=lambda x: x.id):
            est = g.potential + crng.gauss(0, sd)     # what this coach believes the player can become
            raw = est - g.overall
            if est >= bar and raw >= 6:
                picks.append((est + 0.3 * raw, g.id, g))
        for _, _, g in sorted(picks, reverse=True)[:min(2, free)]:
            cur = st.coach(g.id)
            if cur is not None and cur.reputation >= c.reputation - 5:
                continue
            if crng.random() < 0.85:
                if cur is not None:
                    leave_coach(g, f'joined {c.name}')
                take_coach(g, c, 'share', 'saw their potential')
    # 2. golfers looking for a coach they can pay
    def priority(g):
        return (-season.player_prestige(g.id), g.id)
    for g in sorted((g for g in active if g.id not in st.coach_of and g.status in ('pro', 'amateur')), key=priority):
        t = TOUR_BY_KEY.get(g.tour)
        p_want = 0.35 + 0.5 * g.personality['coachability'] / 100 + (0.3 if t and t.tier <= 2 else 0.0)
        if rng.random() > p_want:
            continue
        budget = coach_budget(season, g, year)
        if budget < 2500:
            continue
        # the part of their game they believe has most room (their own imperfect view)
        weak = max(SPECIALITIES, key=lambda cat: (sum(perceived_gap(g, k) for k in CATEGORIES[cat])
                                                  if g.ceilings else 0, cat))
        options = by_region.get(region(g.country), []) + [c for c in coaches if c.reputation >= 70
                                                          and region(c.country) != region(g.country)]
        best = None
        for c in options:
            if c.fee > budget or students.get(c.id, 0) >= c.capacity:
                continue
            v = c.reputation + (12 if c.speciality == weak else 0) + (10 if c.youth and g.age(year) <= YOUTH_AGE else 0) \
                + (5 if c.country == g.country else 0) + rng.gauss(0, 4)
            if best is None or v > best[0]:
                best = (v, c)
        if best:
            take_coach(g, best[1], 'fee', f'${best[1].fee:,.0f} a year')
    # 3. caddies
    cads = [k for k in st.caddies.values() if k.status == 'active']
    employed = {kid for kid in st.caddie_of.values()}
    for g in season.world.golfers:
        kid = st.caddie_of.get(g.id)
        if kid is None:
            continue
        k = st.caddies[kid]
        if g.lifestyle == 'retired' or k.status != 'active' or not wants_caddie(g) \
                or k.weekly_fee * season.target_events(g) > 1.5 * caddie_budget(season, g, year):
            st.caddie_of.pop(g.id)
            employed.discard(kid)
            k.history.append((year, f'Left the bag of {g.name}'))
            log(g.id, year, 1, f'Parted with caddie {k.name}')
    free_cads = sorted((k for k in cads if k.id not in employed), key=lambda k: (-k.reputation - rng.gauss(0, 8), k.id))
    for g in sorted((g for g in active if wants_caddie(g) and g.id not in st.caddie_of), key=priority):
        budget = caddie_budget(season, g, year)
        events = max(1, season.target_events(g))
        for i, k in enumerate(free_cads):
            if k.weekly_fee * events <= budget:
                st.caddie_of[g.id] = k.id
                free_cads.pop(i)
                k.history.append((year, f'Began caddying for {g.name}'))
                log(g.id, year, 1, f'Hired caddie {k.name}')
                break


def end_of_season(season, year, snap):
    """Reputations follow results; disappointing seasons cost jobs; coaches and caddies age, retire, and
    the profession recruits from outside when it runs short."""
    st = season.staff
    rng = random.Random(f'{season.seed}:staff-year:{year}')
    from .careers import progress_signal
    pupils = {}
    for gid, cid in st.coach_of.items():
        pupils.setdefault(cid, []).append(gid)
    for c in st.coaches.values():
        if c.status != 'active' or (c.history and c.history[0][0] == year and c.former_golfer):
            continue                                  # (a coach who joined this winter starts next season)
        fame = sum(season.player_prestige(gid) for gid in pupils.get(c.id, ()))
        progress = sum(progress_signal(snap.get(gid, {})) for gid in pupils.get(c.id, ()))
        target = 100 * (1 - math.exp(-fame / 150)) + 4 * progress
        c.reputation = round(_clip(0.8 * c.reputation + 0.2 * target, 1.0), 1)
        if rng.random() < _sig((c.age(year) - COACH_RETIRE_AGE) / 3) or (not pupils.get(c.id) and rng.random() < 0.15):
            c.status = 'retired'
            c.history.append((year, f'Retired from coaching at {c.age(year)}'))
    for gid, kid in list(st.caddie_of.items()):
        k = st.caddies[kid]
        row = snap.get(gid, {})
        k.seasons += 1
        k.reputation = round(_clip(0.8 * k.reputation + 0.2 * min(100.0, 20 * math.log10(1 + row.get('prize', 0) / 1000)), 1.0), 1)
        for s in ('strategy', 'green_reading', 'yardage', 'course_knowledge'):
            if k.age(year) < 50:
                k.skills[s] = round(min(95.0, k.skills[s] + 0.3), 1)      # experience on the bag
        if progress_signal(row) < -0.3 and rng.random() < 0.3:          # a bad year: a new caddie
            st.caddie_of.pop(gid)
            k.history.append((year, f'Let go by {season.g[gid].name} after a difficult season'))
            season.log(gid, year, 53, f'Let caddie {k.name} go after a difficult season')
    for gid in list(st.coach_of):
        if progress_signal(snap.get(gid, {})) < -0.3 and rng.random() < 0.2:
            c = st.coaches[st.coach_of.pop(gid)]
            st.deal.pop(gid, None)
            c.history.append((year, f'Let go by {season.g[gid].name} after a difficult season'))
            season.log(gid, year, 53, f'Parted with coach {c.name} after a difficult season')
    employed = set(st.caddie_of.values())
    for k in st.caddies.values():
        if k.status != 'active' or (k.history and k.history[0][0] == year and k.former_golfer):
            continue
        idle = k.id not in employed
        if rng.random() < _sig((k.age(year) - CADDIE_RETIRE_AGE) / 3) or (idle and rng.random() < 0.25):
            k.status = 'retired'
            k.history.append((year, f'Stopped caddying at {k.age(year)}'))
    # outside recruits when demand outgrows the profession (labelled as such)
    demand = {}
    for g in season.world.golfers:
        if wants_caddie(g) and g.lifestyle != 'retired':
            demand[g.country] = demand.get(g.country, 0) + 1
    supply = {}
    for k in st.caddies.values():
        if k.status == 'active':
            supply[k.country] = supply.get(k.country, 0) + 1
    for country, n in sorted(demand.items()):
        for _ in range(max(0, round(1.1 * n) - supply.get(country, 0))):
            st.generated_caddie(rng, country, year + 1, 'a club caddie (outside recruit)')
    capacity = sum(c.capacity for c in st.coaches.values() if c.status == 'active')
    if capacity < 1.2 * len(st.coach_of):
        pool = {c: p.pool for c, p in season.world.nations.items()}
        for country in rng.choices(sorted(pool), [pool[c] for c in sorted(pool)], k=10):
            st.generated_coach(rng, country, year + 1, 'a teaching professional (outside recruit)')


def former_golfer_role(season, g, year, rng, level):
    """When a golfer stops chasing or retires: become a coach, a caddie, or neither."""
    age = g.age(year)
    pc, pk = p_become_coach(g, age), p_become_caddie(g, age)
    r = rng.random()
    if r < pc:
        role = 'coach'
    elif r < pc + pk:
        role = 'caddie'
    else:
        return None
    person = season.staff.from_golfer(g, year, role, rng, level)
    season.log(g.id, year, 53, f'Became a {role}' + (f' ({person.speciality.replace("_", " ")} specialist)'
                                                       if role == 'coach' else ''))
    return role
