"""Relationships between golfers and the people around them, as dated records.

Every coaching, caddying or school-team arrangement is a **stint**: one record with both participants
(person ids, never names), the kind of relationship, the arrangement, when it started and ended, who
ended it and why, and how much they actually worked together. A golfer's profile and a coach's profile
read the same stint. Ending a stint (or anyone retiring) never deletes it; a pair that separates and
later reunites gets a second stint.

Each golfer–staff **pair** also keeps its working relationship across stints:

    work    time actually spent working together (coaching weeks in which the golfer trained or played,
            or rounds on the bag), with time apart wearing it down
    fit     how well these two particular people suit each other (fixed per pair, modest)

`effectiveness()` turns them into how well the staff member's ability reaches the golfer: it rises with
work, with diminishing returns (it never exceeds 1), it fades with years apart, and it only *scales*
the staff member's own skill — so a familiar average coach never outperforms a clearly better coach
for ever. Nothing about a relationship changes a golfer's attributes directly.

Current assignments (who coaches whom now) are an index maintained only by opening and closing stints.
"""
from __future__ import annotations

import math
import random
from dataclasses import asdict, dataclass, field

KINDS = ('coach', 'caddie', 'school')
WORK_SCALE = {'coach': 30.0, 'caddie': 60.0}     # weeks of coaching / rounds on the bag to reach ~63%
APART_DECAY_YEARS = 3.0                         # time apart wears a working relationship down
BASE_EFFECT, RAPPORT_EFFECT, FIT_EFFECT = 0.75, 0.25, 0.05


@dataclass
class Stint:
    id: int
    kind: str                    # 'coach', 'caddie' or 'school'
    staff: int                   # person id of the coach or caddie (0 for a school programme)
    golfer: int                  # person id of the golfer
    start: tuple                 # (year, week)
    arrangement: str             # 'fee', 'share', 'tour bag', 'school team: CO_US_D1' ...
    started_by: str              # 'golfer', 'coach' (an approach), 'school'
    reason_start: str = ''
    end: tuple | None = None
    reason_end: str = ''
    ended_by: str = ''           # 'golfer', 'staff', 'retirement', 'school', ...
    work: float = 0.0            # coaching weeks / rounds actually worked together during this stint
    seasons: list = field(default_factory=list)   # [(year, observed progress, weight of evidence)]

    def active_in(self, year, week=26):
        return self.start <= (year, week) and (self.end is None or (year, week) < self.end)


@dataclass
class Pair:
    work: float = 0.0            # accumulated working time (worn down by time apart)
    last_year: int = 0           # the last year they worked together
    fit: float = 0.0


class Relations:
    """Every stint in the world, indexed by golfer and by staff member."""

    def __init__(self, seed=0):
        self.seed = seed
        self.stints = []                         # index = stint id
        self.open = {}                           # (kind, golfer) -> stint id
        self.by_golfer = {}                      # golfer -> [stint ids]
        self.by_staff = {}                       # staff person -> [stint ids]
        self.pairs = {}                          # (kind, staff, golfer) -> Pair

    # -- recording ------------------------------------------------------------------------------
    def begin(self, kind, staff, golfer, when, arrangement, started_by, reason=''):
        assert kind in KINDS
        if (kind, golfer) in self.open:
            raise ValueError(f'golfer {golfer} already has an open {kind} stint')
        s = Stint(len(self.stints), kind, staff, golfer, tuple(when), arrangement, started_by, reason)
        self.stints.append(s)
        self.open[(kind, golfer)] = s.id
        self.by_golfer.setdefault(golfer, []).append(s.id)
        if staff:
            self.by_staff.setdefault(staff, []).append(s.id)
            self.pair(kind, staff, golfer)
        return s

    def finish(self, kind, golfer, when, reason, ended_by):
        sid = self.open.pop((kind, golfer), None)
        if sid is None:
            return None
        s = self.stints[sid]
        s.end, s.reason_end, s.ended_by = tuple(when), reason, ended_by
        return s

    def current(self, kind, golfer):
        sid = self.open.get((kind, golfer))
        return self.stints[sid] if sid is not None else None

    # -- working relationship ----------------------------------------------------------------------
    def pair(self, kind, staff, golfer):
        key = (kind, staff, golfer)
        p = self.pairs.get(key)
        if p is None:
            fit = max(-2.0, min(2.0, random.Random(f'{self.seed}:fit:{kind}:{staff}:{golfer}').gauss(0, 1)))
            p = self.pairs[key] = Pair(fit=round(fit, 3))
        return p

    def add_work(self, kind, golfer, amount, year):
        """Time actually worked together (a coaching week used, or rounds on the bag)."""
        s = self.current(kind, golfer)
        if s is None or not s.staff or amount <= 0:
            return
        s.work += amount
        p = self.pair(kind, s.staff, golfer)
        if p.last_year and year > p.last_year + 1:   # coming back together after time apart
            p.work *= math.exp(-(year - p.last_year - 1) / APART_DECAY_YEARS)
        p.work += amount
        p.last_year = year

    def rapport(self, kind, staff, golfer, year):
        """0 (strangers) .. 1 (long, recent working relationship), with diminishing returns."""
        p = self.pairs.get((kind, staff, golfer))
        if p is None or p.work <= 0:
            return 0.0
        apart = max(0, year - p.last_year - 1)
        work = p.work * math.exp(-apart / APART_DECAY_YEARS)
        return 1 - math.exp(-work / WORK_SCALE[kind])

    def effectiveness(self, kind, staff, golfer, year):
        """How much of a staff member's ability reaches this golfer (about 0.65-1.05)."""
        p = self.pairs.get((kind, staff, golfer))
        fit = p.fit if p else 0.0
        return (BASE_EFFECT + RAPPORT_EFFECT * self.rapport(kind, staff, golfer, year)) * (1 + FIT_EFFECT * fit)

    # -- reading ---------------------------------------------------------------------------------
    def of_golfer(self, golfer, kind=None):
        return [self.stints[i] for i in self.by_golfer.get(golfer, ()) if kind is None or self.stints[i].kind == kind]

    def of_staff(self, staff, kind=None):
        return [self.stints[i] for i in self.by_staff.get(staff, ()) if kind is None or self.stints[i].kind == kind]

    def at(self, kind, golfer, year, week):
        """The stint in force for this golfer at a given week (or None)."""
        for s in reversed(self.of_golfer(golfer, kind)):
            if s.active_in(year, week):
                return s
        return None

    def export(self):
        return {'stints': [asdict(s) for s in self.stints],
                'pairs': [[k, st, g, p.work, p.last_year, p.fit] for (k, st, g), p in self.pairs.items()]}

    @classmethod
    def load(cls, data, seed=0):
        r = cls(seed)
        for d in data['stints']:
            d = dict(d, start=tuple(d['start']), end=tuple(d['end']) if d['end'] else None)
            s = Stint(**d)
            r.stints.append(s)
            r.by_golfer.setdefault(s.golfer, []).append(s.id)
            if s.staff:
                r.by_staff.setdefault(s.staff, []).append(s.id)
            if s.end is None:
                r.open[(s.kind, s.golfer)] = s.id
        for k, st, g, work, last, fit in data['pairs']:
            r.pairs[(k, st, g)] = Pair(work, last, fit)
        return r
