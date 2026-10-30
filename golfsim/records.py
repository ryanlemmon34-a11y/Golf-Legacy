"""Course records, kept per layout.

A course's Championship tees and its Club tees are different tests, so every record belongs to a
layout (`Course.layout_id`, e.g. 'stonebridge-hollow-golf-club:Championship'). Only competitive rounds
count: a round in a calendar event, from any tour or amateur event that plays that layout.

For each layout the book keeps:
    course record     lowest 18-hole score (first to shoot it holds it; equalling it is noted)
    record history    every round that set or equalled the record, in order
    tier records      lowest round at each level of golf (Premier, Challenger, college, ...)
    lowest totals     lowest 36 / 54 / 72-hole tournament totals: completed stroke-play events of that
                      length on this layout, every round played (a missed cut is not a completed longer
                      event; match play never makes a stroke-play total; playoff holes are not in a
                      total; a one-round event is a round, kept by the course record); equalling a
                      total does not take it (the first to post it holds it)
    highest round     the worst competitive round ever posted there
    hole bests        lowest score ever made on each hole, and every hole-in-one and albatross
    scoring           rounds played and scoring average

Every mark carries the golfer's person id and the event id, so a record links to the golfer and the
edition, not just a display name.

Match-play holes and playoff holes count for the hole records and the memorable moments (an ace in a
championship final is kept), but never as an 18-hole round: a match that ends 5&4 is not a round.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields


@dataclass(frozen=True)
class Mark:
    score: int
    to_par: int
    golfer: str
    event_id: str
    year: int
    week: int
    round_no: int = 0
    tier: int = -1
    golfer_id: int = 0           # person id: records link to the golfer and the event, not just a name

    def line(self):
        tp = 'E' if self.to_par == 0 else f'{self.to_par:+d}'
        rd = f', round {self.round_no}' if self.round_no else ''
        return f'{self.score} ({tp}) — {self.golfer}, {self.event_id}{rd}'


@dataclass
class LayoutRecords:
    layout_id: str
    par: int
    course_record: Mark | None = None
    history: list = field(default_factory=list)          # Marks that set or equalled the record
    tier_records: dict = field(default_factory=dict)      # tier -> Mark
    lowest_totals: dict = field(default_factory=dict)     # holes -> Mark
    highest_round: Mark | None = None
    hole_best: list = field(default_factory=lambda: [None] * 18)   # (score, golfer, event_id, golfer_id)
    aces: list = field(default_factory=list)              # (hole number, golfer, event_id, year, stage, golfer_id)
    albatrosses: list = field(default_factory=list)       # (hole number, golfer, event_id, year, stage, golfer_id)
    holes_played: int = 0                                 # every competitive hole, rounds or not
    rounds: int = 0
    strokes: int = 0

    @property
    def scoring_average(self):
        return self.strokes / self.rounds if self.rounds else None

    def add_round(self, mark, hole_scores=(), hole_pars=()):
        self.rounds += 1
        self.strokes += mark.score
        cr = self.course_record
        if cr is None or mark.score < cr.score:
            self.course_record = mark
            self.history.append(('set', mark))
        elif mark.score == cr.score:
            self.history.append(('equalled', mark))
        t = self.tier_records.get(mark.tier)
        if t is None or mark.score < t.score:
            self.tier_records[mark.tier] = mark
        if self.highest_round is None or mark.score > self.highest_round.score:
            self.highest_round = mark
        # each hole, exactly as add_hole does it (inlined: about 6 million holes a season)
        best = self.hole_best
        golfer, event_id, gid = mark.golfer, mark.event_id, mark.golfer_id
        for i, s in enumerate(hole_scores):
            b = best[i]
            if b is None or s < b[0]:
                best[i] = (s, golfer, event_id, gid)
            if s == 1 or (hole_pars and hole_pars[i] and s == hole_pars[i] - 3):
                stage = f'round {mark.round_no}' if mark.round_no else ''
                (self.aces if s == 1 else self.albatrosses).append((i + 1, golfer, event_id, mark.year, stage, gid))
        self.holes_played += len(hole_scores)

    def add_hole(self, idx, score, par, golfer, event_id, year, stage='', golfer_id=0):
        """One competitive hole: a round's hole, a match-play hole or a playoff hole."""
        self.holes_played += 1
        b = self.hole_best[idx]
        if b is None or score < b[0]:
            self.hole_best[idx] = (score, golfer, event_id, golfer_id)
        if score == 1:
            self.aces.append((idx + 1, golfer, event_id, year, stage, golfer_id))
        elif par and score == par - 3:
            self.albatrosses.append((idx + 1, golfer, event_id, year, stage, golfer_id))

    def add_total(self, holes, mark):
        cur = self.lowest_totals.get(holes)
        if cur is None or mark.score < cur.score:
            self.lowest_totals[holes] = mark


class RecordBook:
    """Records for every layout in the world. Feed it with `round_recorder` and `add_event`."""

    def __init__(self):
        self.layouts = {}
        self.totals_since = None          # the first season whose tournament totals were recorded

    def note_totals(self, year):
        """Tournament totals are recorded from this season on (a world whose earlier seasons were played
        before totals were recorded keeps the season it began: its totals are "since" that season)."""
        if getattr(self, 'totals_since', None) is None:
            self.totals_since = year

    def get(self, course):
        lid = course.layout_id
        if lid not in self.layouts:
            self.layouts[lid] = LayoutRecords(lid, course.par)
        return self.layouts[lid]

    def round_recorder(self, course, event_id, year, week, tier=-1):
        """A callback for `play_event(..., on_round=...)` that records every round at this layout."""
        rec = self.get(course)
        pars = [h.par for h in course.holes]

        def on_round(golfer, round_no, stats):
            rec.add_round(Mark(stats.score, stats.score - course.par, golfer.name, event_id, year, week, round_no,
                               tier, getattr(golfer, 'id', 0)), stats.holes, pars)
        return on_round

    def hole_recorder(self, course, event_id, year):
        """A callback for `on_hole=` (match play, playoffs): records single holes, never rounds."""
        rec = self.get(course)
        pars = [h.par for h in course.holes]

        def on_hole(golfer, idx, strokes, stage=''):
            rec.add_hole(idx, strokes, pars[idx], golfer.name, event_id, year, stage, getattr(golfer, 'id', 0))
        return on_hole

    def add_event(self, course, leaderboard, holes, event_id, year, week, tier=-1):
        """Lowest tournament totals from a finished `play_event` leaderboard (players who finished)."""
        rec = self.get(course)
        for golfer, total, rounds in leaderboard:
            if len(rounds) * 18 == holes:
                rec.add_total(holes, Mark(total, total - course.par * len(rounds), golfer.name, event_id, year,
                                          week, 0, tier, getattr(golfer, 'id', 0)))

    def to_dict(self):
        """Every layout's records as plain data: what dataclasses.asdict gives (the same keys in the same
        order, Marks as dicts, lists and tuples copied), built directly (asdict walks millions of values
        a season on a mature world)."""
        names = _layout_fields()
        since = getattr(self, 'totals_since', None)
        out = {}
        for lid, r in self.layouts.items():
            d = {n: _plain(getattr(r, n)) for n in names}
            d['totals_since'] = since
            out[lid] = d
        return out


_FIELDS = {}


def _layout_fields():
    if 'layout' not in _FIELDS:
        _FIELDS['layout'] = tuple(f.name for f in fields(LayoutRecords))
        _FIELDS['mark'] = tuple(f.name for f in fields(Mark))
    return _FIELDS['layout']


def _plain(v):
    """dataclasses.asdict's conversion for the record book's values (Marks hold only plain values)."""
    if isinstance(v, Mark):
        return {k: getattr(v, k) for k in _FIELDS['mark']}
    if isinstance(v, list):
        return [_plain(x) for x in v]
    if isinstance(v, tuple):
        return tuple(_plain(x) for x in v)
    if isinstance(v, dict):
        return {k: _plain(x) for k, x in v.items()}
    return v
