"""Course records, kept per layout.

A course's Championship tees and its Club tees are different tests, so every record belongs to a
layout (`Course.layout_id`, e.g. 'stonebridge-hollow-golf-club:Championship'). Only competitive rounds
count: a round in a calendar event, from any tour or amateur event that plays that layout.

For each layout the book keeps:
    course record     lowest 18-hole score (first to shoot it holds it; equalling it is noted)
    record history    every round that set or equalled the record, in order
    tier records      lowest round at each level of golf (Premier, Challenger, college, ...)
    lowest totals     lowest 36 / 54 / 72-hole tournament totals
    highest round     the worst competitive round ever posted there
    hole bests        lowest score ever made on each hole, and every hole-in-one
    scoring           rounds played and scoring average
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field


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
    hole_best: list = field(default_factory=lambda: [None] * 18)   # (score, golfer, event_id)
    aces: list = field(default_factory=list)              # (hole number, golfer, event_id, year)
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
        for i, s in enumerate(hole_scores):
            b = self.hole_best[i]
            if b is None or s < b[0]:
                self.hole_best[i] = (s, mark.golfer, mark.event_id)
            if s == 1:
                self.aces.append((i + 1, mark.golfer, mark.event_id, mark.year))

    def add_total(self, holes, mark):
        cur = self.lowest_totals.get(holes)
        if cur is None or mark.score < cur.score:
            self.lowest_totals[holes] = mark


class RecordBook:
    """Records for every layout in the world. Feed it with `round_recorder` and `add_event`."""

    def __init__(self):
        self.layouts = {}

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
                               tier), stats.holes, pars)
        return on_round

    def add_event(self, course, leaderboard, holes, event_id, year, week, tier=-1):
        """Lowest tournament totals from a finished `play_event` leaderboard (players who finished)."""
        rec = self.get(course)
        for golfer, total, rounds in leaderboard:
            if len(rounds) * 18 == holes:
                rec.add_total(holes, Mark(total, total - course.par * len(rounds), golfer.name, event_id, year,
                                          week, 0, tier))

    def to_dict(self):
        out = {}
        for lid, r in self.layouts.items():
            d = asdict(r)
            d['history'] = [(k, asdict(m)) for k, m in r.history]
            out[lid] = d
        return out
