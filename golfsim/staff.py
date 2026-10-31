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
    last year's improvement) through their own scouting error — never hidden potential — which firms up
    with the seasons they have watched a player, and back the ones they believe can reach about
    Challenger standard, for a share of future prize money.

Recruitment is two-way (rules 2026-11-04)
    Development coaches (youth specialists) look for promising growth; the others for established
    success (Prestige, rankings, a known fit, earned major places). A golfer may turn a coach's approach
    down, a coach may turn a golfer down as their book fills, and a caddie may turn a bag down (earnings,
    compatibility, stability). Coaches of established players court established golfers of any age for a fee,
    and caddies without a bag offer to carry one; the golfer answers within their means. A partnership's
    loyalty (rapport, fit, results together) stands against a better-known offer, and ends only once another
    is accepted. Every approach records who made it, why, and why it was accepted or refused.

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
    age (and leave the profession after long spells without work), which closes their stints. A coach or
    caddie can die in the winter after a season (mortality.py): their stints end then, with the reason.

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

# ---- recruitment (rules 2026-11-04): PROPOSED starting values -----------------------------------------------
# Every constant below is a proposal awaiting the owner's approval, measured on small worlds against the build
# before it (docs/RECRUITMENT_PACKAGE.md). None of the decisions they tune reads a golfer's hidden potential or
# ceilings: only what can be watched (level seen with error, growth for the age, last year's improvement),
# public standing (Prestige, rankings, earned major places, last season's prize money) and the recorded pair.
SCOUT_LOOK = 60                     # young players a coach looks at each winter
WATCH_FOLLOW = 20                   # of them, at most this many followed from earlier winters ...
WATCH_FOLLOW_MARGIN = 4.0           # ... those whose projected level came within this of the coach's bar
WATCH_FIRMING = 0.5                 # a scout's error x 1 / sqrt(1 + 0.5 (seasons watched - 1)): 1, .82, .71, .63
WATCH_MAX = 6                       # seasons watched beyond this firm up no further (error x 0.53)
WATCH_FORGET = 2                    # a followed player not looked at for this many winters is forgotten (others: 1)
DEV_GROWTH, DEV_RISE = 0.6, 0.5     # development coach's ranking: projected level + 0.6 room to grow + 0.5 rise
ELITE_GROWTH = 0.1                  # elite coach's ranking: projected level + 0.1 room to grow ...
ELITE_ACHIEVED, ELITE_FIT, ELITE_MAJORS = 1.0, 1.0, 1.0   # ... + achievement + known fit + earned major places
COACH_TAKES_BASE, COACH_TAKES_INTEREST, COACH_TAKES_FULL = 5.5, 1.2, 5.0   # a coach taking on a paying client
GOLFER_SAYS_YES = 1.8               # a golfer without a coach accepting a share deal (about 86% before the terms)
GOLFER_REP, GOLFER_FIT = 0.3, 0.5   # ... per 10 points of the coach's reputation over 50; per point of known fit
GOLFER_COLLEGE = 0.8                # ... less likely while their college team coaches them
GOLFER_EARNING = 1.0                # ... less likely the more prize money they won last season (to $100k)
SWITCH_BASE, SWITCH_GAIN, SWITCH_CAP = -0.5, 1.2, 2.5      # leaving a coach for an approach: per 10 points better
LOYALTY_RAPPORT, LOYALTY_FIT, LOYALTY_RESULTS = 4.0, 1.0, 1.5   # loyalty: rapport (0-1), fit (-2..2), results
CADDIE_SAYS_YES = 2.5               # a caddie accepting a bag (about 92% before the terms)
CADDIE_PAY, CADDIE_FIT, CADDIE_STABLE = 0.6, 1.0, 0.5      # per 10 points of earnings gap; known fit; a Premier bag
CADDIE_WAITING = 0.5                # each bag turned down this winter makes a caddie this much readier to say yes
# staff who make the first move beyond youth scouting (bounded: candidates looked at and offers made per winter)
ESTABLISHED_REP = 55.0              # coaches of established players this well known court established golfers ...
ESTABLISHED_BAR = 4.0               # ... who show at least this achievement (Prestige 40, or 25 and a top-100 rank)
ESTABLISHED_LOOK, ESTABLISHED_OFFERS = 30, 1   # ... looking at the 30 most accomplished near them, offering 1 a winter
GOLFER_FEE_YES = 0.5                # a golfer without a coach accepting a paid coach's approach (62% before terms)
GOLFER_COACHABLE = 1.0              # ... per 50 points of coachability over 50 (some want no individual coach)
CADDIE_LOOK, CADDIE_OFFERS = 30, 1  # a free caddie looks at the 30 best-placed bags in their region, offers 1
CADDIE_APPROACH_MIN = 0.85          # ... and only to a golfer they would accept at least this readily
GOLFER_CADDIE_YES, GOLFER_CADDIE_REP = 1.5, 0.5   # a golfer without a caddie accepting an approach; per 10 points
                                    # of the caddie's reputation against the golfer's own results level


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
        self.watched = {}              # (coach, golfer) -> (seasons watched, last winter watched, still following)

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
    def assign_coach(self, season, g, c, arrangement, when, started_by, reason, accept=''):
        # a paying client's fee is agreed when they start and holds for the stint (a coach whose
        # reputation rises charges new clients more, not existing ones)
        self.rel.begin('coach', c.id, g.id, when, arrangement, started_by, reason,
                       terms=c.fee if arrangement == 'fee' else 0.0, accept=accept)
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

    def assign_caddie(self, season, g, k, when, reason='hired for the season', accept='', started_by='golfer'):
        if k.id in self._bags():
            raise ValueError(f'caddie {k.id} already has a bag')
        self.rel.begin('caddie', k.id, g.id, when, 'tour bag', started_by, reason, accept=accept)
        self.caddie_of[g.id] = k.id
        if season:
            season.log(g.id, when[0], when[1], f'{"Approached by" if started_by == "caddie" else "Hired"} caddie {k.name}')

    def end_caddie(self, season, gid, when, reason, ended_by):
        kid = self.caddie_of.pop(gid, None)
        if kid is None:
            return None
        s = self.rel.finish('caddie', gid, when, reason, ended_by)
        if season:
            season.log(gid, when[0], when[1], f'Caddie {self.caddies[kid].name} off the bag ({reason})')
        return s

    def refuse(self, season, kind, person, g, when, asked_by, refused_by, reason_asked, reason):
        """An approach turned down, recorded with both people and both reasons (history.Relations.refuse)."""
        self.rel.refuse(kind, person.id, g.id, when, asked_by, refused_by, reason_asked, reason)
        if season:
            role = 'coach' if kind == 'coach' else 'caddie'
            season.log(g.id, when[0], when[1], f'Turned down an approach from {role} {person.name} ({reason})'
                       if refused_by == 'golfer' else f'{role.title()} {person.name} declined to work with them ({reason})')

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


def firming(seasons):
    """How much of a scout's error remains once they have watched a player for this many seasons (this one
    included): watching longer firms an assessment up, with diminishing returns."""
    return 1 / math.sqrt(1 + WATCH_FIRMING * (min(max(1, seasons), WATCH_MAX) - 1))


def scouting_estimate(season, g, year, rng, sd, coach_id=0, seasons=1):
    """A coach's judgement of where a young player is heading, from what can be watched: their
    current level (seen with some error), the growth typical for their age, and how much they really
    improved over the last year (a fast improver looks like more to come) — through the coach's own
    scouting error, which shrinks with the seasons this coach has watched this player (`firming`).
    Never the player's hidden potential, so coaches back players who do not make it and miss some who do."""
    from .population import age_deficit
    age = g.age(year)
    seen = g.overall + rng.gauss(0, 2.0)
    last = season.overall_start.get(year - 1, {}).get(g.id)
    recent = (g.overall - last) if last is not None else 0.0
    typical = age_deficit(age, 27.0) - age_deficit(age + 1, 27.0)     # a typical year's growth at this age
    # the coach's view of this player persists (a scout does not re-roll their opinion every winter);
    # it moves only as the player's observed level and improvement move, and firms up as they watch longer
    view = random.Random(f'{season.seed}:view:{coach_id}:{g.id}').gauss(0, sd)
    error = view + rng.gauss(0, 0.3 * sd)
    return seen + age_deficit(age, 27.0) + 1.5 * (recent - typical) + firming(seasons) * error


# ---- recruitment: two-way, each side for its own reasons (rules 2026-11-04) ---------------------------------
# Every input below is something the people involved can see: a level watched with error, growth for the age,
# last year's improvement, Prestige, rankings, earned major places, last season's prize money, reputation, and
# the recorded pair (fit, rapport, results together). Hidden potential and ceilings are never read.
def motivation(c):
    """What a coach looks for: youth specialists develop promising growth; the others build on established
    success."""
    return 'development' if c.youth else 'established'


def recent_rise(season, g, year):
    """Last year's real improvement against the growth typical for the age (0 when it was not seen)."""
    from .population import age_deficit
    last = season.overall_start.get(year - 1, {}).get(g.id)
    if last is None:
        return 0.0
    age = g.age(year)
    return max(-5.0, min(5.0, (g.overall - last) - (age_deficit(age, 27.0) - age_deficit(age + 1, 27.0))))


def earned_majors(season, year):
    """golfer -> the majors this season they hold an earned place in (the published qualification ledger)."""
    out = {}
    for book in season.major_rights.get(year, {}).values():
        for gid, r in book.items():
            if r.get('state') == 'earned':
                out[gid] = out.get(gid, 0) + 1
    return out


def achievement(season, g):
    """Established achievement as anyone can see it, on a 0-13 scale: Prestige / 10 plus up to 3 for a world
    ranking inside 200 or an amateur ranking inside 300."""
    wr, am = season.wr_pos.get(g.id), season.am_pos.get(g.id)
    rank = max(3 * (1 - wr / 200) if wr else 0.0, 3 * (1 - am / 300) if am else 0.0, 0.0)
    return season.player_prestige(g.id) / 10 + rank


def coach_rates(season, st, c, g, year, est, raw, majors=0):
    """How a scouting coach ranks a candidate they believe can reach their bar, and why: a development coach
    by the room to grow they see and last year's rise; a coach of established players by achievement, a known
    fit (only from a pair that already worked together) and earned major places."""
    if motivation(c) == 'development':
        rise = recent_rise(season, g, year)
        why = 'a fast improver over the last year' if DEV_RISE * rise > DEV_GROWTH * raw / 2 else 'saw promising growth'
        return est + DEV_GROWTH * raw + DEV_RISE * rise, why + ' (a development coach)'
    past = st.rel.pairs.get(('coach', c.id, g.id))
    terms = {'established results': ELITE_ACHIEVED * achievement(season, g),
             'a known good fit': ELITE_FIT * past.fit if past else 0.0,
             'a chance at the majors': ELITE_MAJORS * min(3, majors)}
    top = max(terms, key=lambda k: (terms[k], k))
    why = top if terms[top] >= 1.0 else 'saw a player who can reach the professional game'
    return est + ELITE_GROWTH * raw + sum(terms.values()), why + ' (a coach of established players)'


def loyalty(st, kind, staff_id, gid, year):
    """What holds a working partnership together, from the record: rapport (time actually worked together,
    worn by time apart), the pair's fit and the results they have shared (evidence-weighted progress). Returns
    (total, {reason: part})."""
    tr, ev = trend(st.rel.current(kind, gid))
    p = st.rel.pairs.get((kind, staff_id, gid))
    parts = {'a strong working relationship': LOYALTY_RAPPORT * st.rel.rapport(kind, staff_id, gid, year),
             'a good fit': LOYALTY_FIT * (p.fit if p else 0.0),
             'progress together': LOYALTY_RESULTS * max(-1.0, min(2.0, tr)) * min(1.0, ev)}
    return sum(parts.values()), parts


def last_prize(season, g, year):
    """Last season's prize money (the recorded ledger; 0 before the world's first season ends)."""
    led = season.ledgers.get(year - 1, {}).get(g.id)
    return led.prize if led else 0.0


def golfer_answers(season, st, g, c, year, arrangement='share'):
    """A golfer's answer to a coach's approach: (chance of yes, why yes, why no). A share of future prize money
    (youth scouting): without a coach, likelier the better known the coach and with a known good fit; less likely
    while a college team coaches them or when last season's prize money makes a share costly. A fee (a coach of
    established players): only if the coach's fee fits what they can commit to a coach (coach_budget, the hiring
    rule); without a coach, likelier the better known the coach, the more coachable they are and with a known good
    fit. With a coach, either way: the gain in reputation against the partnership's loyalty, so a better-known
    offer alone rarely breaks a good one."""
    cur = st.coach(g.id)
    if arrangement == 'fee' and c.fee > coach_budget(season, g, year):
        return 0.0, '', f'could not afford the fee (${c.fee:,.0f} a year)'
    if cur is None and arrangement == 'fee':
        past = st.rel.pairs.get(('coach', c.id, g.id))
        terms = {'the coach was not well known': GOLFER_REP * (c.reputation - 50) / 10,
                 'had not worked well together before': GOLFER_FIT * past.fit if past else 0.0,
                 'did not want individual coaching': GOLFER_COACHABLE * (g.personality['coachability'] - 50) / 50}
        low = min(terms, key=lambda k: (terms[k], k))
        yes = (('a well-known coach' if c.reputation >= 60 else 'a coach who sought them out')
               + ('; had worked well together before' if past and past.fit > 0.5 else ''))
        no = low if terms[low] < 0 else 'preferred to carry on as they were'
        return _sig(GOLFER_FEE_YES + sum(terms.values())), yes, no
    if cur is None:
        past = st.rel.pairs.get(('coach', c.id, g.id))
        terms = {'the coach was not well known': GOLFER_REP * (c.reputation - 50) / 10,
                 'had not worked well together before': GOLFER_FIT * past.fit if past else 0.0,
                 'happy with their college team\'s coaching': -GOLFER_COLLEGE if g.tour.startswith('CO_') else 0.0,
                 'did not want to give up a share of their winnings':
                     -GOLFER_EARNING * min(1.0, last_prize(season, g, year) / 100_000)}
        low = min(terms, key=lambda k: (terms[k], k))
        yes = ('a share deal costs nothing now' + ('; a well-known coach' if c.reputation >= 60 else '')
               + ('; had worked well together before' if past and past.fit > 0.5 else ''))
        no = low if terms[low] < 0 else 'preferred to carry on as they were'
        return _sig(GOLFER_SAYS_YES + sum(terms.values())), yes, no
    loyal, parts = loyalty(st, 'coach', cur.id, g.id, year)
    gain = SWITCH_GAIN * min(SWITCH_CAP, (c.reputation - cur.reputation) / 10)
    held = [k for k, v in sorted(parts.items(), key=lambda kv: (-kv[1], kv[0])) if v >= 0.5]
    no = f'stayed with {cur.name}: ' + (', '.join(held) if held else 'did not think the move worth it')
    yes = f'a clearly better-known coach than {cur.name}' + ('' if loyal > 1.0 else ', with little yet built together')
    return _sig(SWITCH_BASE + gain - loyal), yes, no


def coach_takes(season, st, c, g, year, load, majors=0):
    """A coach's answer to a golfer asking to be a paying client: (chance of yes, why yes, why no). A coach with
    room rarely says no; as their book fills they keep the places for the players they look for (young players
    with promising growth, or established results and major places), and a known poor fit counts against."""
    past = st.rel.pairs.get(('coach', c.id, g.id))
    if motivation(c) == 'development':
        interest = (1.0 if g.age(year) <= YOUTH_AGE else -1.0) + recent_rise(season, g, year) / 3
        want = 'young players with promising growth'
    else:
        interest = achievement(season, g) / 4 + 0.3 * min(3, majors) - 1.0
        want = 'players with established results'
    if past:
        interest += past.fit
    p = _sig(COACH_TAKES_BASE + COACH_TAKES_INTEREST * interest - COACH_TAKES_FULL * load / max(1, c.capacity))
    no = ('had not worked well together before' if past and past.fit < -1.0
          else f'keeping the room left in their book for {want}')
    yes = f'the kind of player they look for ({want})' if interest > 0 else 'had room for a paying client'
    return p, yes, no


def results_level(season, g, year):
    """A golfer's results on a caddie's reputation scale: last season's prize money (20 log10(1 + prize / $1,000),
    the scale a caddie's reputation follows) or Prestige (20 + 0.85 x Prestige), whichever is higher."""
    return max(20 * math.log10(1 + last_prize(season, g, year) / 1000), 20 + 0.85 * season.player_prestige(g.id))


CADDIE_GOOD = {'wanted a bag with bigger earnings': 'a bag with good earnings',
               'had not got on with them before': 'had worked well together before',
               'wanted the security of a Premier bag': 'a secure Premier bag'}


def caddie_answers(st, k, g, level, turned_down=0):
    """A caddie's answer to a golfer offering the bag: (chance of yes, why yes, why no). Expected earnings (the
    golfer's results against what the caddie's own reputation could earn), compatibility (the pair's fit and
    time together, only if they worked together before) and stability (a Premier card); a caddie who has
    already turned bags down this winter grows readier to say yes."""
    past = st.rel.pairs.get(('caddie', k.id, g.id))
    t = TOUR_BY_KEY.get(g.tour)
    terms = {'wanted a bag with bigger earnings': CADDIE_PAY * max(-4.0, min(2.0, (level - k.reputation) / 10)),
             'had not got on with them before': CADDIE_FIT * (past.fit + min(1.0, past.work / 60)) if past else 0.0,
             'wanted the security of a Premier bag': CADDIE_STABLE * (1.0 if t and t.tier == 1 else -1.0)}
    low = min(terms, key=lambda x: (terms[x], x))
    high = max(terms, key=lambda x: (terms[x], x))
    p = _sig(CADDIE_SAYS_YES + sum(terms.values()) + CADDIE_WAITING * turned_down)
    return p, (CADDIE_GOOD[high] if terms[high] >= 0.3 else 'the work on offer'), (low if terms[low] < 0 else 'kept waiting')


def approach(season, c, g, why, when, rng, students=None, shares=None, arrangement='share'):
    """A coach approaches a player -- a young one for a share of future prize money, or an established one for
    a fee -- and the player answers (golfer_answers): only a yes ends the player's current coaching (recorded as
    leaving for the approach) and opens the new stint with both reasons; a no is recorded with both reasons (on
    the partnership kept, if any). `students` and `shares` (coach -> count) are kept up to date when given. True
    if the player said yes."""
    st = season.staff
    cur = st.coach(g.id)
    p, yes, no = golfer_answers(season, st, g, c, when[0], arrangement)
    if rng.random() >= p:
        st.refuse(season, 'coach', c, g, when, 'coach', 'golfer', why, no)
        return False
    students, shares = ({} if students is None else students), ({} if shares is None else shares)
    if cur is not None:
        students[cur.id] = students.get(cur.id, 0) - 1
        if st.deal.get(g.id) == 'share':
            shares[cur.id] = shares.get(cur.id, 0) - 1
        st.end_coach(season, g.id, when, f'left for an approach from {c.name}', 'golfer')
    st.assign_coach(season, g, c, arrangement, when, 'coach', why, yes)
    students[c.id] = students.get(c.id, 0) + 1
    if arrangement == 'share':
        shares[c.id] = shares.get(c.id, 0) + 1
    return True


def started_now(st, kind, gid, when):
    """Whether this golfer's current partnership of this kind began in this very market (they are not courted
    again the same winter)."""
    s = st.rel.current(kind, gid)
    return s is not None and tuple(s.start) == tuple(when)


def established_approaches(season, year, offered, students, majors=None):
    """Coaches of established players with room in their book (reputation ESTABLISHED_REP or more) court
    established golfers near them -- in their country, or their region when well known (60+), as in scouting --
    by achievement anyone can see (Prestige and a ranking, at least ESTABLISHED_BAR), a known fit and earned major
    places; never potential. Separate from youth scouting: any age, and the offer is a fee. Each coach looks at
    the ESTABLISHED_LOOK most accomplished candidates within reach and makes at most ESTABLISHED_OFFERS offers;
    one offer per pair per winter (`offered`). Returns {coach id: offers made}."""
    st = season.staff
    when = (year, 1)
    majors = earned_majors(season, year) if majors is None else majors
    home = season.home_country
    coaches = sorted((c for c in st.coaches.values() if c.status == 'active' and motivation(c) == 'established'
                      and c.reputation >= ESTABLISHED_REP and students.get(c.id, 0) < c.capacity),
                     key=lambda c: (-c.reputation, c.id))
    if not coaches:
        return {}
    ach = {}
    for g in season.world.golfers:
        if g.lifestyle != 'retired' and g.status in ('pro', 'amateur'):
            a = achievement(season, g)
            if a >= ESTABLISHED_BAR:
                ach[g.id] = a
    by_country = {}
    for gid in sorted(ach, key=lambda x: (-ach[x], x)):            # most accomplished first
        by_country.setdefault(home(season.g[gid]), []).append(season.g[gid])
    made = {}
    for c in coaches:
        here = season.places.country(c.id, c.country)
        reach = [here] + [cc for cc in sorted(by_country) if cc != here and region(cc) == region(here)] \
            if c.reputation >= 60 else [here]                       # (well-known coaches: their whole region)
        pool = sorted((g for cc in reach for g in by_country.get(cc, ())), key=lambda g: (-ach[g.id], g.id))
        look = []
        for g in pool:
            if len(look) >= ESTABLISHED_LOOK:
                break
            cur = st.coach(g.id)
            if (('coach', c.id, g.id) in offered or cur is c or started_now(st, 'coach', g.id, when)
                    or (cur is not None and cur.reputation >= c.reputation - 5)):
                continue                              # (no approach to a player with a coach of their standing)
            look.append(g)
        picks = []
        for g in look:
            score, why = coach_rates(season, st, c, g, year, 0.0, 0.0, majors.get(g.id, 0))
            picks.append((score, g.id, g, why))
        crng = random.Random(f'{season.seed}:court:{year}:{c.id}')
        for _, _, g, why in sorted(picks, key=lambda x: (x[0], x[1]), reverse=True)[:ESTABLISHED_OFFERS]:
            if students.get(c.id, 0) >= c.capacity:
                break
            offered.add(('coach', c.id, g.id))
            made[c.id] = made.get(c.id, 0) + 1
            approach(season, c, g, f'{why}; ${c.fee:,.0f} a year', when, crng, students, arrangement='fee')
    return made


def golfer_takes_caddie(season, st, g, k, year):
    """A golfer's answer to a caddie offering to carry their bag: (chance of yes, why yes, why no). Only if the
    caddie's fees fit what they can commit to a caddie (caddie_budget, the hiring rule). Without a caddie: likelier
    the better known the caddie against the golfer's own results level, and with a known good fit. With a caddie:
    the gain in reputation against the partnership's loyalty (rapport, fit, results together)."""
    events = max(1, season.target_events(g))
    if k.weekly_fee * events > caddie_budget(season, g, year):
        return 0.0, '', f'could not afford their fee (${k.weekly_fee:,.0f} a week)'
    cur = st.caddie(g.id)
    if cur is None:
        past = st.rel.pairs.get(('caddie', k.id, g.id))
        gap = (k.reputation - results_level(season, g, year)) / 10
        terms = {'expected a better-known caddie': GOLFER_CADDIE_REP * max(-4.0, min(2.0, gap)),
                 'had not got on with them before': CADDIE_FIT * (past.fit + min(1.0, past.work / 60)) if past else 0.0}
        low = min(terms, key=lambda x: (terms[x], x))
        yes = 'had worked well together before' if past and past.fit > 0.5 else 'a caddie they could afford'
        return _sig(GOLFER_CADDIE_YES + sum(terms.values())), yes, (low if terms[low] < 0 else 'preferred to look further')
    loyal, parts = loyalty(st, 'caddie', cur.id, g.id, year)
    gain = SWITCH_GAIN * min(SWITCH_CAP, (k.reputation - cur.reputation) / 10)
    held = [x for x, v in sorted(parts.items(), key=lambda kv: (-kv[1], kv[0])) if v >= 0.5]
    no = f'stayed with {cur.name}: ' + (', '.join(held) if held else 'did not think the move worth it')
    yes = f'a clearly better-known caddie than {cur.name}' + ('' if loyal > 1.0 else ', with little yet built together')
    return _sig(SWITCH_BASE + gain - loyal), yes, no


def caddie_offer(season, k, g, why, when, rng):
    """A caddie offers to carry a golfer's bag and the golfer answers (golfer_takes_caddie): only a yes ends the
    golfer's current caddie's stint (recorded as leaving for the approach) and opens the new one, started by the
    caddie, with both reasons; a no is recorded with both reasons (on the partnership kept, if any). True if yes."""
    st = season.staff
    cur = st.caddie(g.id)
    p, yes, no = golfer_takes_caddie(season, st, g, k, when[0])
    if rng.random() >= p:
        st.refuse(season, 'caddie', k, g, when, 'caddie', 'golfer', why, no)
        return False
    if cur is not None:
        st.end_caddie(season, g.id, when, f'left for an approach from {k.name}', 'golfer')
    st.assign_caddie(season, g, k, when, why, yes, started_by='caddie')
    return True


def caddie_approaches(season, year, offered):
    """Caddies without a bag make the first move: each looks at the CADDIE_LOOK golfers wanting a caddie in their
    region with the best results (last season's prize money or Prestige), skipping those whose caddie is as well
    known as they are, and offers to carry the bag of the one they would most readily accept (caddie_answers:
    earnings, a known fit, a Premier card), if at least CADDIE_APPROACH_MIN; at most CADDIE_OFFERS offers each,
    one per pair per winter (`offered`). Returns {caddie id: offers made}."""
    st = season.staff
    when = (year, 1)
    bags = st._bags()
    free = sorted((k for k in st.caddies.values() if k.status == 'active' and k.id not in bags),
                  key=lambda k: (-k.reputation, k.id))
    if not free:
        return {}
    level, by_region = {}, {}
    for g in sorted(season.world.golfers, key=lambda x: x.id):
        if g.lifestyle != 'retired' and wants_caddie(g):
            level[g.id] = results_level(season, g, year)
            by_region.setdefault(region(season.home_country(g)), []).append(g)
    for gs in by_region.values():
        gs.sort(key=lambda g: (-level[g.id], g.id))
    made = {}
    for k in free:
        look = []
        for g in by_region.get(region(season.places.country(k.id, k.country)), ()):
            if len(look) >= CADDIE_LOOK:
                break
            cur = st.caddie(g.id)
            if (('caddie', k.id, g.id) in offered or started_now(st, 'caddie', g.id, when)
                    or (cur is not None and cur.reputation >= k.reputation - 5)):
                continue
            look.append(g)
        picks = []
        for g in look:
            p, why, _ = caddie_answers(st, k, g, level[g.id])
            if p >= CADDIE_APPROACH_MIN:
                picks.append((p, level[g.id], g.id, g, why))
        krng = random.Random(f'{season.seed}:caddie-offer:{year}:{k.id}')
        for _, _, _, g, why in sorted(picks, key=lambda x: x[:3], reverse=True)[:CADDIE_OFFERS]:
            offered.add(('caddie', k.id, g.id))
            made[k.id] = made.get(k.id, 0) + 1
            if caddie_offer(season, k, g, why, when, krng):
                break
    return made


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
    """School teams, coaches scouting young players and courting established ones, golfers hiring coaches,
    caddies offering to carry bags, and golfers hiring caddies for the season. One offer per pair per winter
    (`offered`), whoever makes it."""
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
    offered = set()                                   # (kind, staff, golfer): one offer per pair per winter
    students, shares = {}, {}
    for gid, cid in st.coach_of.items():
        students[cid] = students.get(cid, 0) + 1
        if st.deal.get(gid) == 'share':
            shares[cid] = shares.get(cid, 0) + 1
    coaches = [c for c in st.coaches.values() if c.status == 'active']
    lives = {c.id: season.places.country(c.id, c.country) for c in coaches}   # where they work from
    home = season.home_country
    by_region = {}
    for c in coaches:
        by_region.setdefault(region(lives[c.id]), []).append(c)
    # 1. scouting: coaches approach young, raw players they believe in, and the player may say no
    young = [g for g in active if g.age(year) <= SCOUT_AGE and g.status in ('amateur', 'pro')]
    near = {}
    for g in young:
        near.setdefault(home(g), []).append(g)
    majors = earned_majors(season, year)
    watched = st.watched
    for key in [key for key, w in watched.items() if w[1] < year - (WATCH_FORGET if w[2] else 1)]:
        del watched[key]                              # not looked at for a while: forgotten
    for c in sorted(coaches, key=lambda c: (-c.reputation, c.id)):
        # a coach still has to make a living from paying students: at most a third of their book is
        # players coached for a share of future winnings
        free = min(c.capacity - students.get(c.id, 0), c.capacity // 3 - shares.get(c.id, 0))
        if free <= 0:
            continue
        here = lives[c.id]
        pool = list(near.get(here, ()))
        if c.reputation >= 60:                        # well-known coaches look further afield
            pool += [g for cc, gs in near.items() if cc != here and region(cc) == region(here) for g in gs]
        if not pool:
            continue
        crng = random.Random(f'{season.seed}:scout:{year}:{c.id}')
        # they keep following the promising players they watched in earlier winters, and look at new ones
        followed = [g for g in pool if watched.get((c.id, g.id), (0, 0, False))[2]][:WATCH_FOLLOW]
        keep = {g.id for g in followed}
        rest = [g for g in pool if g.id not in keep]
        look = followed + crng.sample(rest, min(SCOUT_LOOK - len(followed), len(rest)))
        sd = 3 + 12 * (1 - c.scouting / 100)
        # a share of prize money is only worth anything if the player can reach a level where professionals
        # earn (about Challenger standard); better-known coaches hold out for better prospects
        bar = max(SHARE_BAR, 50 + 0.35 * c.reputation)
        picks = []
        for g in sorted(look, key=lambda x: x.id):
            w = watched.get((c.id, g.id))
            seasons = (w[0] + (w[1] < year)) if w else 1
            est = scouting_estimate(season, g, year, crng, sd, c.id, seasons)   # what they believe g can become
            raw = est - g.overall
            watched[(c.id, g.id)] = (seasons, year, est >= bar - WATCH_FOLLOW_MARGIN)
            if est >= bar and raw >= 6:
                score, why = coach_rates(season, st, c, g, year, est, raw, majors.get(g.id, 0))
                picks.append((score, g.id, g, why))
        for _, _, g, why in sorted(picks, key=lambda x: (x[0], x[1]), reverse=True)[:min(2, free)]:
            cur = st.coach(g.id)
            if cur is not None and cur.reputation >= c.reputation - 5:
                continue                              # (no approach to a player with a coach of their standing)
            offered.add(('coach', c.id, g.id))
            approach(season, c, g, why, when, crng, students, shares)
    # 2. coaches of established players court established golfers, for a fee
    established_approaches(season, year, offered, students, majors)
    # 3. golfers looking for a coach they can pay
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
        options = by_region.get(region(home(g)), []) + [c for c in coaches if c.reputation >= 70
                                                         and region(lives[c.id]) != region(home(g))]
        ranked = []
        affordable = False
        for c in options:
            if c.fee > budget:
                continue
            affordable = True
            if students.get(c.id, 0) >= c.capacity or ('coach', c.id, g.id) in offered:
                continue
            past = st.rel.pairs.get(('coach', c.id, g.id))
            v = c.reputation + (12 if c.speciality == weak else 0) + (10 if c.youth and g.age(year) <= YOUTH_AGE else 0) \
                + (5 if lives[c.id] == home(g) else 0) + (4 * past.fit if past else 0) + rng.gauss(0, 4)
            why = ('had worked well together before' if past and past.fit > 0.5
                   else 'a specialist in what they want to improve' if c.speciality == weak
                   else 'a youth specialist' if c.youth and g.age(year) <= YOUTH_AGE else 'the best-known coach they could afford')
            ranked.append((v, c.id, c, why))
        # they ask the coaches they like best in turn; each coach answers for their own reasons
        for _, _, c, why in sorted(ranked, key=lambda x: (x[0], x[1]), reverse=True):
            offered.add(('coach', c.id, g.id))
            p, yes, no = coach_takes(season, st, c, g, year, students.get(c.id, 0), majors.get(g.id, 0))
            if rng.random() < p:
                st.assign_coach(season, g, c, 'fee', when, 'golfer', f'{why}; ${c.fee:,.0f} a year', yes)
                students[c.id] = students.get(c.id, 0) + 1
                break
            st.refuse(season, 'coach', c, g, when, 'golfer', 'coach', why, no)
        else:
            if affordable:                            # could pay, but every coach they could afford was full
                st.unserved[year][home(g)] = st.unserved[year].get(home(g), 0) + 1   # (or said no)
    # 4. caddies (one touring golfer each)
    for g in active:
        k = st.caddie(g.id)
        if k is not None and (not wants_caddie(g)
                              or k.weekly_fee * season.target_events(g) > 1.5 * caddie_budget(season, g, year)):
            st.end_caddie(season, g.id, when, 'no longer on a tour that needs one' if not wants_caddie(g)
                          else 'could no longer afford them', 'golfer')
    caddie_approaches(season, year, offered)          # caddies without a bag make the first move
    bags = st._bags()
    free_cads = sorted((k for k in st.caddies.values() if k.status == 'active' and k.id not in bags),
                       key=lambda k: (-k.reputation - rng.gauss(0, 8), k.id))
    turned_down = {}                                  # caddie -> bags they have said no to this winter
    for g in sorted((g for g in active if wants_caddie(g) and g.id not in st.caddie_of), key=priority):
        budget = caddie_budget(season, g, year)
        events = max(1, season.target_events(g))
        level = results_level(season, g, year)
        # caddies they worked well with come first; then the best-looking ones, as everyone sees them
        known = {s.staff for s in st.rel.of_golfer(g.id, 'caddie')
                 if st.rel.pairs[('caddie', s.staff, g.id)].fit > 0.5}
        for k in [k for k in free_cads if k.id in known] + [k for k in free_cads if k.id not in known]:
            if k.weekly_fee * events > budget or ('caddie', k.id, g.id) in offered:
                continue
            offered.add(('caddie', k.id, g.id))
            why = 'had worked well together before' if k.id in known else 'the best caddie they could afford'
            p, yes, no = caddie_answers(st, k, g, level, turned_down.get(k.id, 0))
            if rng.random() < p:
                st.assign_caddie(season, g, k, when, why, yes)
                free_cads.remove(k)
                break
            turned_down[k.id] = turned_down.get(k.id, 0) + 1
            st.refuse(season, 'caddie', k, g, when, 'golfer', 'caddie', why, no)


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
    # each season's working abilities, kept for historical views (observation only: nothing reads them back)
    for c in st.coaches.values():
        if c.status == 'active':
            r = record.setdefault(('coach', c.id), {'students': 0, 'reputation': c.reputation})
            r['teaching'], r['scouting'] = round(c.teaching, 1), round(c.scouting, 1)
    for k in st.caddies.values():
        if k.status == 'active' and getattr(k, 'skills', None):
            record[('caddie', k.id)]['skills'] = {s: round(v, 1) for s, v in k.skills.items()}
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
    # deaths (mortality.py, rules 2026-11-07): once per winter, after the season's career decisions, these
    # retirements and the departed's relationships, before outside recruits (who then replace the dead)
    from .mortality import winter as mortality_winter
    mortality_winter(season, year)
    # outside recruits for unmet demand (labelled as such)
    demand = {}
    for g in season.world.golfers:
        if wants_caddie(g) and g.lifestyle != 'retired':
            demand[season.home_country(g)] = demand.get(season.home_country(g), 0) + 1
    supply = {}
    for k in st.caddies.values():
        if k.status == 'active':
            supply[season.places.country(k.id, k.country)] = supply.get(season.places.country(k.id, k.country), 0) + 1
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
