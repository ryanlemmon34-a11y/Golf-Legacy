"""A compact 72-hole stroke-play event for balance testing.

This is a test harness, not the final tournament engine: pressure is set from
each golfer's position at the START of a round (cut-line battle on Friday,
contention on Sunday) instead of from a live tee-sheet leaderboard. The full
world simulation will reuse the chronological tee-time model from v0.13.
"""
from __future__ import annotations

from .engine import Conditions, WeekForm, play_round, play_hole, Player, RoundStats, HoleState


def _pressure_fn(level_front, level_back):
    def fn(i, _to_par):
        return level_back if i >= 9 else level_front
    return fn


def play_event(field, course, rng, cut_top=65, prestige=1.0, cond_by_round=None, caddies=None,
               rounds_n=4, cut_after=2):
    """field: list of Golfer. Returns ordered leaderboard [(golfer, total, rounds)].

    rounds_n: 1-4 rounds; cut_after: round after which the cut is made (None = no cut).
    """
    caddies = caddies or {}
    forms = {id(g): WeekForm.draw(rng, g) for g in field}
    totals = {id(g): 0 for g in field}
    rounds = {id(g): [] for g in field}
    alive = list(field)
    for rd in range(1, rounds_n + 1):
        cond = (cond_by_round or {}).get(rd) or Conditions()
        board = sorted(totals[id(g)] for g in alive)
        leader = board[0] if board else 0
        cut_est = board[min(cut_top, len(board)) - 1] if board else 0
        for g in alive:
            t = totals[id(g)]
            pf = None
            final = rd == rounds_n
            if rd == 2 and cut_after == 2 and rounds_n > 2:
                # After 18 holes the projected cut is fuzzy; golfers near it feel it late on.
                if abs(t - cut_est) <= 2:
                    pf = _pressure_fn(0.15, 0.45 * prestige)
            elif rd == 3 and not final and t - leader <= 3:
                pf = _pressure_fn(0.25 * prestige, 0.35 * prestige)
            elif final and rd > 1:
                gap = t - leader
                if gap <= 3:
                    pf = _pressure_fn(0.5 * prestige, 0.95 * prestige)
                elif gap <= 6:
                    pf = _pressure_fn(0.2 * prestige, 0.4 * prestige)
            st = play_round(g, course, rng, cond, caddies.get(id(g)), rd, forms[id(g)], pf)
            totals[id(g)] += st.score
            rounds[id(g)].append(st.score)
        if cut_after and rd == cut_after and rd < rounds_n:
            ordered = sorted(alive, key=lambda g: totals[id(g)])
            line = totals[id(ordered[min(cut_top, len(ordered)) - 1])]
            alive = [g for g in ordered if totals[id(g)] <= line]
    board = sorted(alive, key=lambda g: totals[id(g)])
    best = totals[id(board[0])]
    tied = [g for g in board if totals[id(g)] == best]
    playoff_holes = 0
    while len(tied) > 1:
        hole = course.holes[17 if playoff_holes % 2 == 0 else 16]
        scores = {}
        for g in tied:
            pl = Player(g, course, Conditions(), caddies.get(id(g)), rng, rounds_n, forms[id(g)])
            scores[id(g)] = play_hole(pl, hole, 17, rng, RoundStats(), 1.0 * prestige, HoleState())
        low = min(scores.values())
        tied = [g for g in tied if scores[id(g)] == low]
        playoff_holes += 1
    winner = tied[0]
    board.remove(winner)
    board.insert(0, winner)
    return [(g, totals[id(g)], rounds[id(g)]) for g in board], playoff_holes
