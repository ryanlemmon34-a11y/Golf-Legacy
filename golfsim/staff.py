"""Coaches and caddies: the people around the players, and their working relationships.

People and identity
    Coaches and caddies are people with world-wide person ids (the same id space as golfers). A golfer
    who becomes a coach or caddie keeps their id: their playing career and their staff career are two
    views of one person. Retirement never deletes anyone.

Relationships (see history.py)
    Every coaching, caddying or school-team arrangement is a dated stint shared by both profiles, with
    who started it, who ended it and why. Current assignments are an index kept only by opening and
    closing stints (`assign_coach`, `end_coach`, `assign_caddie`, `end_caddie`). Every event result
    records the coach and caddie each golfer had that week.

Coaches
    Speciality (physical, long game, short game, putting or mental), hidden teaching and scouting
    skills, a visible reputation that follows their students, and a client capacity (how many players
    they can coach individually: about 6, from 4 to 8, by their availability and how intensively they
    work — separate from how well they teach). A golfer has one coach at a time. Coaching quality
    (teaching, plus their speciality or young players if that is their gift) reaches the golfer through
    their working relationship (history.Relations.effectiveness): new pairings take time to work well,
    a long one works best, time apart wears it down; it only scales the coach's ability.
    Without a personal coach a golfer teaches themselves; young amateurs have some local or school
    instruction, and college golfers their team's coaching. A private coach does not stack with these:
    the better of the two applies.

    Golfers get a coach by hiring one they can afford, or by being approached: coaches scout young, raw
    players near them, judging from what can be watched (current level, typical growth for their age,
    last year's improvement) through their own scouting error — never hidden potential — and back the
    ones they believe can reach about Challenger standard, for a share of future prize money.

Caddies
    The six skills the shot engine uses (strategy, yardage, mental support, green reading, course
    knowledge, communication), familiarity with every course they work, and a working relationship
    with each player (it scales how much of their skill reaches the player). One touring golfer per
    caddie. Premier and Challenger professionals hire the best caddie they can afford; others carry
    their own bag.

Changes
    In the off-season either side may end a relationship, from smooth odds: the golfer's observed
    progress during it (professional and amateur results and rankings, and observed development; a
    season with few events or a long injury counts as weak evidence), their working relationship and
    fit, affordability and better options; a coach who backed a prospect weighs the evidence over an
    observation period, not a birthday. Mid-season changes happen only when someone retires or genuinely
    cannot continue (cannot pay a coach; a caddie with no events to work). Staff retire gradually with
    age (and leave the profession after long spells without work), which closes their stints.

Where they come from
    Former golfers (by aptitude and age; rarely anyone who made a fortune), plus generated starting
    staff and outside recruits for unmet paying demand, labelled as such.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from .calendar import TOUR_BY_KEY
from .development import CATEGORIES, perceived_gap
from .geography import COUNTRIES
from .golfer import CADDIE_SKILLS, Caddie
from .history import Relations
from .names import make_name

SPECIALITIES = tuple(CATEGORIES)                  # physical, long_game, short_game, putting, mental
SELF_TEACHING = 0.3                               # coaching quality of a golfer who teaches themselves
LOCAL_INSTRUCTION = 0.38                          # young amateurs: local club / school instruction
COLLEGE_TEAM = 0.48                               # college golfers: the school team's coaching
YOUTH_AGE = 22
SCOUT_AGE = 23                                    # coaches scout players this age and younger
SCOUT_SHARE = 0.05                                # of prize money, for a coach who approached the player
SHARE_BAR = 66.0                                  # the projected level a scouting coach must believe in
INITIAL_COACHES = 480                             # sized so the first season's paying demand finds room
CLIENTS_MEAN, CLIENTS_MIN, CLIENTS_MAX = 6, 4, 8  # individual clients a coach takes on (tuning assumption)
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
    id: int                            # person id (a former golfer keeps theirs)
    name: str
    country: str
    born: int
    speciality: str                    # a training category
    youth: bool                        # specialises in developing young players
    teaching: float                    # 0-100: how much their coaching helps (hidden)
    scouting: float                    # 0-100: how well they judge a young player's prospects (hidden)
    reputation: float                  # 0-100: what golfers see; grows with their students' success
    background: str = ''
    former_golfer: int = 0             # = id if this person played in this world
    status: str = 'active'             # 'active' / 'retired'
    earnings: float = 0.0
    clients: int = CLIENTS_MEAN        # individual clients they take on (availability, intensity)
    idle_years: int = 0
    history: list = field(default_factory=list)      # [(year, text)]: staff-career events only

    @property
    def capacity(self):
        return self.clients

    @property
    def fee(self):
        """Yearly fee for a paying student."""
        return round(3000 * math.exp(self.reputation / 30), -2)

    def age(self, year):
        return year - self.born


@dataclass
class TourCaddie(Caddie):
    id: int = 0                        # person id
    country: str = ''
    born: int = 0
    reputation: float = 50.0           # what players see; grows with their employers' success
    background: str = ''
    former_golfer: int = 0
    status: str = 'active'
    earnings: float = 0.0
    seasons: int = 0                   # seasons in which they actually worked
    weeks_worked: int = 0              # event weeks worked this season (reset each winter)
    rounds_worked: float = 0.0         # rounds on the bag this season (stroke play, match play, playoffs)
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


class _Counter:
    """Fallback person-id allocator for staff built outside a world (tests, tools)."""

    def __init__(self, start=10_000_000):
        self.next = start

    def __call__(self):
        self.next += 1
        return self.next - 1


# ---- the staff of the world -------------------------------------------------------------------------
class Staff:
    """All coaches and caddies, their relationships, and who works with whom now."""

    def __init__(self, new_id=None, seed=0):
        self.new_id = new_id or _Counter()
        self.coaches = {}              # person id -> Coach
        self.caddies = {}              # person id -> TourCaddie
        self.rel = Relations(seed)     # every stint, and each pair's working relationship
        self.coach_of = {}             # golfer -> coach (index of open coaching stints)
        self.deal = {}                 # golfer -> 'fee' or 'share'
        self.caddie_of = {}            # golfer -> caddie (index of open caddying stints)
        self.taken = set()             # names in use (for generating new names only)
        self.unserved = {}             # year -> country -> golfers who could pay but found no coach with room

    # -- creating people --------------------------------------------------------------------------
    def new_coach(self, rng, country, year, age, teaching, scouting, speciality, youth, reputation, background,
                  former=0, name=None, pid=None):
        clients = int(max(CLIENTS_MIN, min(CLIENTS_MAX, round(rng.gauss(CLIENTS_MEAN, 1.2)))))
        c = Coach(pid or self.new_id(), name or make_name(country, rng, self.taken), country, year - age, speciality,
                  youth, round(_clip(teaching), 1), round(_clip(scouting), 1), round(_clip(reputation, 1.0), 1),
                  background, former, clients=clients)
        self.taken.add(c.name)
        self.coaches[c.id] = c
        return c

    def new_caddie(self, rng, country, year, age, skills, reputation, background, former=0, name=None, pid=None):
        k = TourCaddie(name or make_name(country, rng, self.taken), {s: round(_clip(v), 1) for s, v in skills.items()},
                       id=pid or self.new_id(), country=country, born=year - age,
                       reputation=round(_clip(reputation, 1.0), 1), background=background, former_golfer=former)
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
        """A former golfer becomes a coach or a caddie: the same person (same id), a new career."""
        a, p = g.attrs, g.personality
        age = g.age(year)
        where = f'former {level} golfer'
        if role == 'coach':
            teaching = (100 * coach_aptitude(g) + 0.15 * (g.overall - 55) + rng.gauss(0, 8))
            scouting = 0.4 * a['management'] + 0.3 * p['adaptability'] + 15 + rng.gauss(0, 10)
            c = self.new_coach(rng, g.country, year, age, teaching, scouting, strongest_category(g),
                               rng.random() < 0.15 + 0.3 * p['coachability'] / 100,
                               20 + 0.35 * (g.overall - 40) + rng.gauss(0, 6), where, g.id, g.name, pid=g.id)
            c.history.append((year, f'Became a coach ({c.speciality.replace("_", " ")} specialist'
                                    f'{", young players" if c.youth else ""}) after a career as a {level} golfer'))
            return c
        skills = {'strategy': a['management'], 'green_reading': a['green_reading'],
                  'yardage': (a['focus'] + a['management']) / 2, 'course_knowledge': 0.5 * a['management'] + 25,
                  'mental_support': (a['composure'] + a['resilience']) / 2, 'communication': p['adaptability']}
        skills = {s: v + rng.gauss(0, 6) for s, v in skills.items()}
        k = self.new_caddie(rng, g.country, year, age, skills, sum(skills.values()) / 6 - 5, where, g.id, g.name,
                            pid=g.id)
        k.history.append((year, f'Became a caddie after a career as a {level} golfer'))
        return k

    # -- relationships (the only way assignments change) --------------------------------------------
    def assign_coach(self, season, g, c, arrangement, when, started_by, reason):
        # a paying client's fee is agreed when they start and holds for the stint (a coach whose
        # reputation rises charges new clients more, not existing ones)
        self.rel.begin('coach', c.id, g.id, when, arrangement, started_by, reason,
                       terms=c.fee if arrangement == 'fee' else 0.0)
        self.coach_of[g.id], self.deal[g.id] = c.id, arrangement
        if season:
            season.log(g.id, when[0], when[1], f'{"Approached by" if started_by == "coach" else "Hired"} coach {c.name} '
                       f'({c.speciality.replace("_", " ")} specialist{", young players" if c.youth else ""}; {reason})')

    def end_coach(self, season, gid, when, reason, ended_by):
        cid = self.coach_of.pop(gid, None)
        self.deal.pop(gid, None)
        if cid is None:
            return None
        s = self.rel.finish('coach', gid, when, reason, ended_by)
        if season:
            season.log(gid, when[0], when[1], f'Coaching with {self.coaches[cid].name} ended ({reason})')
        return s

    def assign_caddie(self, season, g, k, when, reason='hired for the season'):
        if k.id in self._bags():
            raise ValueError(f'caddie {k.id} already has a bag')
        self.rel.begin('caddie', k.id, g.id, when, 'tour bag', 'golfer', reason)
        self.caddie_of[g.id] = k.id
        if season:
            season.log(g.id, when[0], when[1], f'Hired caddie {k.name}')

    def end_caddie(self, season, gid, when, reason, ended_by):
        kid = self.caddie_of.pop(gid, None)
        if kid is None:
            return None
        s = self.rel.finish('caddie', gid, when, reason, ended_by)
        if season:
            season.log(gid, when[0], when[1], f'Caddie {self.caddies[kid].name} off the bag ({reason})')
        return s

    def _bags(self):
        return set(self.caddie_of.values())

    # -- effects --------------------------------------------------------------------------------------
    def coach(self, gid):
        cid = self.coach_of.get(gid)
        return self.coaches.get(cid) if cid else None

    def agreed_fee(self, gid):
        """The yearly fee a paying client agreed with their coach (0 if none, or a share deal)."""
        s = self.rel.current('coach', gid)
        return s.terms if s is not None and s.arrangement == 'fee' else 0.0

    def caddie(self, gid):
        kid = self.caddie_of.get(gid)
        return self.caddies.get(kid) if kid else None

    def baseline(self, g, age):
        """Instruction a golfer gets without a personal coach."""
        if g.tour.startswith('CO_'):
            return COLLEGE_TEAM
        if g.status == 'amateur' and age <= YOUTH_AGE:
            return LOCAL_INSTRUCTION
        return SELF_TEACHING

    def coaching(self, g, category, age, year=0):
        """Coaching quality (0-1) for this golfer training this category this week: the coach's quality
        as it reaches this golfer through their working relationship, or their baseline instruction if
        that is better (the two never stack)."""
        base = self.baseline(g, age)
        c = self.coach(g.id)
        if c is None:
            return base
        q = c.teaching / 100 + (0.15 if category == c.speciality else 0) + (0.15 if c.youth and age <= YOUTH_AGE else 0)
        q = min(1.0, q)
        eff = self.rel.effectiveness('coach', c.id, g.id, year)
        return max(base, SELF_TEACHING + max(0.0, q - SELF_TEACHING) * eff)

    def insight(self, g, year=0):
        """How well the golfer's coach reads their game (0 without a coach)."""
        c = self.coach(g.id)
        return c.teaching / 100 * min(1.0, self.rel.effectiveness('coach', c.id, g.id, year)) if c else 0.0

    def bag(self, g, year=0):
        """The caddie on this golfer's bag this week, as they work together: each skill's difference from
        an average caddie is scaled by their working relationship (course familiarity is the caddie's
        own). Their own bag if they have no caddie."""
        k = self.caddie(g.id)
        if k is None:
            return SELF_CADDIE_OBJ
        eff = self.rel.effectiveness('caddie', k.id, g.id, year)
        return Caddie(k.name, {s: 50 + (v - 50) * eff for s, v in k.skills.items()}, k.familiarity)

    def team(self, gid):
        """(coach, caddie) person ids for a golfer right now (0 = none): kept with every event result."""
        return self.coach_of.get(gid, 0), self.caddie_of.get(gid, 0)


def initial_staff(world, seed):
    """The starting world's coaches and caddies (generated: the world has no recorded past)."""
    rng = random.Random(f'{seed}:staff')
    st = Staff(getattr(world, 'new_id', None), seed)
    st.taken = {g.name for g in world.golfers}
    year = world.year
    pool = {c: p.pool for c, p in world.nations.items()}
    total = sum(pool.values())
    for country, w in sorted(pool.items()):
        for _ in range(max(1, round(INITIAL_COACHES * w / total))):
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
COACH_OF_MEANS = 0.10                             # a coach's yearly fee must fit 10% of a golfer's means
CADDIE_OF_MEANS = 0.25


def coach_budget(season, g, year):
    """What a golfer can commit to a coach's yearly fee: a contracted cost paid every week, so it must
    come out of money they have or have earned (Season.means), never out of hoped-for winnings."""
    return COACH_OF_MEANS * season.means(g, year)


def caddie_budget(season, g, year):
    """What a golfer can commit to a caddie's fees over the season. A caddie is paid only in weeks the
    golfer plays, and every trip must still be affordable when it is booked, so the prize money they
    expect to keep (from their own record) may inform this choice — at half weight."""
    income, _ = season.season_forecast(g, g.tour, season.target_events(g))
    expected = income - season.sponsor_income(g)              # the prize money they expect to keep
    return CADDIE_OF_MEANS * (season.means(g, year) + 0.5 * expected)


def wants_caddie(g):
    t = TOUR_BY_KEY.get(g.tour)
    return g.status == 'pro' and g.lifestyle == 'full_time' and t is not None and t.tier <= CADDIE_TIERS


def scouting_estimate(season, g, year, rng, sd, coach_id=0):
    """A coach's judgement of where a young player is heading, from what can be watched: their
    current level (seen with some error), the growth typical for their age, and how much they really
    improved over the last year (a fast improver looks like more to come) — through the coach's own
    scouting error. Never the player's hidden potential, so coaches back players who do not make it
    and miss some who do."""
    from .population import age_deficit
    age = g.age(year)
    seen = g.overall + rng.gauss(0, 2.0)
    last = season.overall_start.get(year - 1, {}).get(g.id)
    recent = (g.overall - last) if last is not None else 0.0
    typical = age_deficit(age, 27.0) - age_deficit(age + 1, 27.0)     # a typical year's growth at this age
    # the coach's view of this player persists (a scout does not re-roll their opinion every winter);
    # it moves only as the player's observed level and improvement move
    view = random.Random(f'{season.seed}:view:{coach_id}:{g.id}').gauss(0, sd)
    return seen + age_deficit(age, 27.0) + 1.5 * (recent - typical) + view + rng.gauss(0, 0.3 * sd)


def sync_school(season, year, week, closing=False):
    """School-team support follows college membership: a stint opens when a golfer is on a college
    team and closes, as an ordinary recorded transition, when they leave it (graduating, turning
    professional, or retiring) — their development is untouched."""
    st = season.staff
    for g in season.world.golfers:
        open_ = st.rel.current('school', g.id)
        on_team = g.tour.startswith('CO_') and g.lifestyle != 'retired'
        if open_ and not on_team:
            why = ('retired from competition' if g.lifestyle == 'retired' else 'turned professional' if g.status == 'pro'
                   else 'college eligibility ended')
            st.rel.finish('school', g.id, (year, week), why, 'school')
        elif on_team and not open_ and not closing:
            st.rel.begin('school', 0, g.id, (year, week), f'school team: {g.tour}', 'school', 'college programme')
        elif on_team and open_ and open_.arrangement != f'school team: {g.tour}':
            st.rel.finish('school', g.id, (year, week), 'moved programme', 'school')
            st.rel.begin('school', 0, g.id, (year, week), f'school team: {g.tour}', 'school', 'college programme')


def start_of_season(season, year):
    """School teams, coaches scouting, golfers hiring coaches, and caddies hired for the season."""
    st = season.staff
    rng = random.Random(f'{season.seed}:staff-market:{year}')
    when = (year, 1)
    active = [g for g in sorted(season.world.golfers, key=lambda x: x.id) if g.lifestyle != 'retired']
    release_departed(season, year, 1)
    sync_school(season, year, 1)
    for g in active:                                  # a contracted fee they can no longer meet
        c = st.coach(g.id)
        if c is not None and st.deal.get(g.id) == 'fee' and st.agreed_fee(g.id) > 1.5 * coach_budget(season, g, year):
            st.end_coach(season, g.id, when, 'could no longer afford the fee', 'golfer')
    students, shares = {}, {}
    for gid, cid in st.coach_of.items():
        students[cid] = students.get(cid, 0) + 1
        if st.deal.get(gid) == 'share':
            shares[cid] = shares.get(cid, 0) + 1
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
        # a coach still has to make a living from paying students: at most a third of their book is
        # players coached for a share of future winnings
        free = min(c.capacity - students.get(c.id, 0), c.capacity // 3 - shares.get(c.id, 0))
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
        # a share of prize money is only worth anything if the player can reach a level where professionals
        # earn (about Challenger standard); better-known coaches hold out for better prospects
        bar = max(SHARE_BAR, 50 + 0.35 * c.reputation)
        picks = []
        for g in sorted(look, key=lambda x: x.id):
            est = scouting_estimate(season, g, year, crng, sd, c.id)   # what this coach believes they can become
            raw = est - g.overall
            if est >= bar and raw >= 6:
                picks.append((est + 0.3 * raw, g.id, g))
        for _, _, g in sorted(picks, reverse=True)[:min(2, free)]:
            cur = st.coach(g.id)
            if cur is not None and cur.reputation >= c.reputation - 5:
                continue
            if crng.random() < 0.85:
                if cur is not None:
                    students[cur.id] -= 1
                    if st.deal.get(g.id) == 'share':
                        shares[cur.id] -= 1
                    st.end_coach(season, g.id, when, f'joined {c.name}', 'golfer')
                st.assign_coach(season, g, c, 'share', when, 'coach', 'saw their potential')
                students[c.id] = students.get(c.id, 0) + 1
                shares[c.id] = shares.get(c.id, 0) + 1
    # 2. golfers looking for a coach they can pay
    st.unserved[year] = {}

    def priority(g):
        return (-season.player_prestige(g.id), g.id)
    for g in sorted((g for g in active if g.id not in st.coach_of and g.status in ('pro', 'amateur')), key=priority):
        t = TOUR_BY_KEY.get(g.tour)
        p_want = 0.35 + 0.5 * g.personality['coachability'] / 100 + (0.3 if t and t.tier <= 2 else 0.0)
        if g.lifestyle == 'part_time':
            p_want *= 0.5                             # a full-time job leaves little time for individual coaching
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
        affordable = False
        for c in options:
            if c.fee > budget:
                continue
            affordable = True
            if students.get(c.id, 0) >= c.capacity:
                continue
            past = st.rel.pairs.get(('coach', c.id, g.id))
            v = c.reputation + (12 if c.speciality == weak else 0) + (10 if c.youth and g.age(year) <= YOUTH_AGE else 0) \
                + (5 if c.country == g.country else 0) + (4 * past.fit if past else 0) + rng.gauss(0, 4)
            if best is None or v > best[0]:
                best = (v, c)
        if best:
            st.assign_coach(season, g, best[1], 'fee', when, 'golfer', f'${best[1].fee:,.0f} a year')
            students[best[1].id] = students.get(best[1].id, 0) + 1
        elif affordable:                              # could pay, but every coach they could afford was full
            st.unserved[year][g.country] = st.unserved[year].get(g.country, 0) + 1
    # 3. caddies (one touring golfer each)
    for g in active:
        k = st.caddie(g.id)
        if k is not None and (not wants_caddie(g)
                              or k.weekly_fee * season.target_events(g) > 1.5 * caddie_budget(season, g, year)):
            st.end_caddie(season, g.id, when, 'no longer on a tour that needs one' if not wants_caddie(g)
                          else 'could no longer afford them', 'golfer')
    bags = st._bags()
    free_cads = sorted((k for k in st.caddies.values() if k.status == 'active' and k.id not in bags),
                       key=lambda k: (-k.reputation - rng.gauss(0, 8), k.id))
    for g in sorted((g for g in active if wants_caddie(g) and g.id not in st.caddie_of), key=priority):
        budget = caddie_budget(season, g, year)
        events = max(1, season.target_events(g))
        for i, k in enumerate(free_cads):
            if k.weekly_fee * events <= budget:
                st.assign_caddie(season, g, k, when)
                free_cads.pop(i)
                break


def observed_progress(season, g, row, year):
    """What a season showed about a golfer's progress, and how much it showed.

    Progress: professional results and ranking movement (careers.progress_signal), amateur ranking
    movement, and observed development (their level against the typical change at their age).
    Evidence: weak when they played few events or lost much of the season to injury."""
    from .careers import progress_signal
    from .population import age_deficit
    p = progress_signal(row)
    a0, a1 = row.get('am_start'), row.get('am_end')
    if a0 and a1:
        p += max(-0.6, min(0.6, 0.35 * math.log(a0 / a1)))
    elif a1 and not a0:
        p += 0.3
    ov0 = season.overall_start.get(year, {}).get(g.id)
    if ov0 is not None:
        age = g.age(year)
        typical = age_deficit(age, 27.0) - age_deficit(age + 1, 27.0)
        p += 0.25 * max(-3.0, min(3.0, (g.overall - ov0) - typical))
    weight = min(1.0, row.get('events', 0) / 6) * (0.3 if row.get('injury_weeks', 0) > 20 else 1.0)
    return max(-1.5, min(2.5, p)), weight


def trend(stint):
    """Evidence-weighted progress over a stint's recent seasons (latest counts most), and its weight."""
    num = den = 0.0
    for i, (_, p, w) in enumerate(reversed(stint.seasons if stint else ())):
        k = 0.6 ** i * w
        num += k * p
        den += k
    return (num / den if den else 0.0), den


# ---- who ends a relationship (smooth odds; each term is something the people involved can see) ----------
def p_golfer_leaves_coach(trend_, evidence, rapport, fit, afford_pressure):
    """A golfer's chance of changing coach this winter: a poor run of observed progress (weighted by
    how much evidence there is), little rapport, a poor fit, or a fee that has outgrown their means."""
    return _sig(-3.6 - 1.2 * trend_ * min(1.0, evidence) - 1.0 * rapport - 0.4 * fit + 1.2 * min(2.0, afford_pressure))


def p_coach_moves_on(deal, trend_, evidence, fit):
    """A coach's chance of ending a relationship. One who backed a prospect for a share of future
    winnings weighs the evidence over an observation period (more evidence of stagnation, more likely;
    a single season, or seasons with little play or long injuries, count for little). A paying client
    is rarely dropped (a poor fit)."""
    if deal == 'share':
        return _sig(-4.5 + 1.0 * min(evidence, 4.0) - 2.5 * trend_) if evidence >= 1.0 else 0.0
    return _sig(-5.0 - 1.5 * fit - 1.0 * trend_)


def p_golfer_changes_caddie(trend_, evidence, rapport, fit):
    return _sig(-3.2 - 1.3 * trend_ * min(1.0, evidence) - 1.0 * rapport - 0.4 * fit)


def p_caddie_moves_on(season_pay, reputation, rapport, fit):
    """A caddie whose bag paid them little this season (against what their reputation could earn) may
    look for another; a strong working relationship keeps them."""
    return _sig(-3.8 + 1.5 * (1 - min(1.0, season_pay / 40000)) * (reputation / 60) - 1.0 * rapport - 0.3 * fit)


def end_of_season(season, year, snap):
    """Reputations follow results; either side may end a relationship; staff gain experience, age and
    retire; the profession recruits from outside for unmet paying demand."""
    st = season.staff
    rng = random.Random(f'{season.seed}:staff-year:{year}')
    when = (year, 53)
    from .careers import progress_signal
    # what this season showed, kept with each open stint
    for (kind, gid), sid in list(st.rel.open.items()):
        if kind in ('coach', 'caddie'):
            s = st.rel.stints[sid]
            p, w = observed_progress(season, season.g[gid], snap.get(gid, {}), year)
            s.seasons.append((year, round(p, 3), round(w, 3)))
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
        c.idle_years = 0 if pupils.get(c.id) else c.idle_years + 1
    record = season.staff_year.setdefault(year, {})   # this season's work, before the counters reset
    for k in st.caddies.values():
        if k.status == 'active':
            record[('caddie', k.id)] = {'rounds': round(k.rounds_worked, 2), 'weeks': k.weeks_worked,
                                        'reputation': k.reputation}
    for gid, cid in st.coach_of.items():
        r = record.setdefault(('coach', cid), {'students': 0, 'reputation': st.coaches[cid].reputation})
        r['students'] += 1
    for k in st.caddies.values():                     # experience comes from rounds actually worked
        if k.status == 'active' and k.rounds_worked > 0:
            k.seasons += 1
            if k.age(year) < 50:
                gain = 0.3 * min(1.0, k.rounds_worked / 60)
                for s in ('strategy', 'green_reading', 'yardage', 'course_knowledge'):
                    if k.skills[s] < 95.0:                # growth stops at 95; higher skills are kept
                        k.skills[s] = round(min(95.0, k.skills[s] + gain), 2)
    receipts = season.staff_receipts.get(year, {})
    for gid, kid in list(st.caddie_of.items()):
        k = st.caddies[kid]
        row = snap.get(gid, {})
        k.reputation = round(_clip(0.8 * k.reputation + 0.2 * min(100.0, 20 * math.log10(1 + row.get('prize', 0) / 1000)), 1.0), 1)
        s = st.rel.current('caddie', gid)
        tr, ev = trend(s)
        rap = st.rel.rapport('caddie', kid, gid, year)
        fit = st.rel.pair('caddie', kid, gid).fit
        # the golfer may want a change after a poor run; the caddie may want a bag that pays better
        p_golfer = p_golfer_changes_caddie(tr, ev, rap, fit)
        p_caddie = p_caddie_moves_on(receipts.get(('caddie', kid), 0.0), k.reputation, rap, fit)
        r = rng.random()
        if r < p_golfer:
            st.end_caddie(season, gid, when, 'the golfer wanted a change after a difficult run' if tr < 0
                          else 'the golfer wanted a change', 'golfer')
        elif r < p_golfer + p_caddie:
            st.end_caddie(season, gid, when, 'the caddie moved on looking for a better-paying bag', 'staff')
        k.weeks_worked, k.rounds_worked = 0, 0.0
    for k in st.caddies.values():
        k.weeks_worked, k.rounds_worked = 0, 0.0
    for gid in list(st.coach_of):
        cid, deal = st.coach_of[gid], st.deal.get(gid)
        s = st.rel.current('coach', gid)
        tr, ev = trend(s)
        rap = st.rel.rapport('coach', cid, gid, year)
        fit = st.rel.pair('coach', cid, gid).fit
        c = st.coaches[cid]
        g = season.g[gid]
        afford = max(0.0, st.agreed_fee(gid) / max(1.0, coach_budget(season, g, year + 1)) - 1) if deal == 'fee' else 0.0
        p_golfer = p_golfer_leaves_coach(tr, ev, rap, fit, afford)
        p_coach = p_coach_moves_on(deal, tr, ev, fit)
        why = 'the promise they saw had not come through' if deal == 'share' else 'the coach felt they were not the right fit'
        r = rng.random()
        if r < p_golfer:
            st.end_coach(season, gid, when, 'the golfer wanted a change after a difficult run' if tr < 0
                         else 'could no longer afford the fee' if afford > 0.3 else 'the golfer wanted a change', 'golfer')
        elif r < p_golfer + p_coach:
            st.end_coach(season, gid, when, why, 'staff')
    for c in st.coaches.values():                     # retirement is a career decision, not a client one
        if c.status != 'active' or (c.history and c.history[0][0] == year and c.former_golfer):
            continue
        if rng.random() < _sig((c.age(year) - COACH_RETIRE_AGE) / 3) or rng.random() < 0.08 * min(3, c.idle_years):
            c.status = 'retired'
            c.history.append((year, f'Retired from coaching at {c.age(year)}'
                                    + (' after a spell without clients' if c.idle_years else '')))
    bags = st._bags()
    for k in st.caddies.values():
        if k.status != 'active' or (k.history and k.history[0][0] == year and k.former_golfer):
            continue
        idle = k.id not in bags
        if rng.random() < _sig((k.age(year) - CADDIE_RETIRE_AGE) / 3) or (idle and rng.random() < 0.25):
            k.status = 'retired'
            k.history.append((year, f'Stopped caddying at {k.age(year)}'))
    release_departed(season, year, 53)
    sync_school(season, year, 53, closing=True)
    # outside recruits for unmet demand (labelled as such)
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
    # new coaches come in where golfers wanted to pay for coaching and found every coach they could
    # afford full (scouting demand alone does not create coaches)
    for country, n in sorted(st.unserved.get(year, {}).items()):
        for _ in range(round(n / 6)):
            st.generated_coach(rng, country, year + 1, 'a teaching professional (outside recruit)')


def release_departed(season, year, week):
    """Golfers who retired from competition (or joined the staff) and staff who retired leave their
    relationships at once, recorded with the reason; nothing is deleted."""
    st = season.staff
    for gid, cid in list(st.coach_of.items()):
        g, c = season.g[gid], st.coaches[cid]
        if g.lifestyle == 'retired':
            st.end_coach(season, gid, (year, week), 'retired from competition', 'retirement')
        elif c.status != 'active':
            st.end_coach(season, gid, (year, week), 'coach retired', 'retirement')
    for gid, kid in list(st.caddie_of.items()):
        g, k = season.g[gid], st.caddies[kid]
        if g.lifestyle == 'retired':
            st.end_caddie(season, gid, (year, week), 'retired from competition', 'retirement')
        elif k.status != 'active':
            st.end_caddie(season, gid, (year, week), 'caddie retired', 'retirement')


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
