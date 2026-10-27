"""Legends of Golf Masters simulation at Georgia National vs real-world Masters patterns.

    python tools/major_test.py [--events 1000]

Plays many editions with a fixed, Masters-shaped field (stars, top-50 players, tour winners,
aging past champions, amateurs) and compares the results with approximate real Masters history.
Writes reports/MAJOR_TEST_REPORT.md.
"""
from __future__ import annotations

import argparse
import random
import statistics as S
import sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from golfsim.course import georgia_national           # noqa: E402
from golfsim.engine import play_round                  # noqa: E402
from golfsim.golfer import ARCHETYPES, archetype_golfer  # noqa: E402
from golfsim.tournament import play_event              # noqa: E402

# Field built like a real Masters field: from a generated world of 600 professionals
# (Premier Tour average 75, real-tour-like spread), take the world top 55, 14 tour winners from
# further down the rankings, aging past champions and elite amateur champions.
WORLD_PROS, WORLD_MEAN, WORLD_SD = 600, 74.0, 4.6
FIELD_GROUPS = ('World top 10', 'World 11-30', 'World 31-55', 'Tour winner (56-160)',
                'Aging past champion', 'Amateur')

# Approximate real Masters patterns, roughly 1995-2024 (reference ranges, not exact records).
REAL = {
    'winning_to_par': 'about -11 on average; usually -7 to -15, extremes +1 (2007) and -20 (2020)',
    'field_round_avg': 'about 72.5-74 per round depending on weather',
    'cut_line': 'usually +2 to +4 (top 50 and ties)',
    'playoff_rate': 'roughly 1 edition in 6-8',
    'margin': 'about 2 strokes on average',
    'favourite': 'world No.1 won 5 of 30 (17%); betting markets usually price a typical No.1 at ~8-12%',
    'top10': 'about 15 of 30 (50%)',
    'longshot': '2 of 30 (7%); betting markets usually imply 20-30% for this group',
    'distinct_per_30': 'about 20-23 different champions per 30 editions',
}


def build_field(seed=2027):
    rng = random.Random(seed)
    world = sorted((min(95.0, rng.gauss(WORLD_MEAN, WORLD_SD)) for _ in range(WORLD_PROS)), reverse=True)
    picks = [('World top 10', o) for o in world[:10]] + [('World 11-30', o) for o in world[10:30]]
    picks += [('World 31-55', o) for o in world[30:55]]
    picks += [('Tour winner (56-160)', o) for o in rng.sample(world[55:160], 14)]
    picks += [('Aging past champion', rng.gauss(71, 2.5)) for _ in range(8)]
    picks += [('Amateur', rng.gauss(65, 3)) for _ in range(6)]
    names = list(ARCHETYPES)
    field = []
    for i, (label, ov) in enumerate(picks):
        g = archetype_golfer(names[i % len(names)], round(ov, 1), name=f'G{i:02d}')
        g.personality['big_stage'] = rng.uniform(10, 50) if label == 'Amateur' else rng.uniform(15, 85)
        fam = {'Aging past champion': (60, 120), 'Amateur': (0, 3)}.get(label, (0, 40))
        g.familiarity['Georgia National Golf Club'] = rng.randint(*fam)
        field.append((label, g))
    return field


def run_batch(args):
    n, seed = args
    course = georgia_national()
    labelled = build_field()
    field = [g for _, g in labelled]
    label_of = {g.name: lab for lab, g in labelled}
    rng = random.Random(seed)
    rows = []
    for _ in range(n):
        board, playoff = play_event(field, course, rng, cut_top=50, prestige=1.0)
        totals = [t for _, t, _ in board]
        rounds = [s for _, _, r in board for s in r]
        winner = board[0][0]
        made = {g.name for g, _, _ in board}
        rows.append(dict(
            winner=winner.name, winner_overall=winner.overall, winner_label=label_of[winner.name],
            winning_to_par=totals[0] - 4 * course.par, margin=(totals[1] - totals[0]) if not playoff else 0,
            playoff=playoff > 0, cut_size=len(board),
            cut_to_par=max(sum(r[:2]) for _, _, r in board) - 2 * course.par,
            weekend_avg=S.mean(rounds), amateurs_cut=sum(label_of[n] == 'Amateur' for n in made)))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--events', type=int, default=1000)
    a = ap.parse_args()
    per = a.events // 4
    with ProcessPoolExecutor() as ex:
        rows = [r for batch in ex.map(run_batch, [(per, 500 + b) for b in range(4)]) for r in batch]
    n = len(rows)
    labelled = build_field()
    field = [g for _, g in labelled]
    by_rank = sorted(field, key=lambda g: -g.overall)
    rank_of = {g.name: i + 1 for i, g in enumerate(by_rank)}

    # Thursday/Friday scoring average of the full field (one quick separate sample).
    course = georgia_national()
    rng = random.Random(9)
    first_rounds = [play_round(g, course, rng).score for _ in range(30) for g in field]

    wins = Counter(r['winner'] for r in rows)
    win_ranks = [rank_of[r['winner']] for r in rows]
    blocks = [len({r['winner'] for r in rows[i:i + 30]}) for i in range(0, n - 29, 30)]
    lab_wins = Counter(r['winner_label'] for r in rows)
    to_par = [r['winning_to_par'] for r in rows]
    out = ['# Legends of Golf Masters at Georgia National — event realism test', '',
           f'{n:,} simulated editions, fixed {len(field)}-player field, 72 holes, cut top 50 and ties. '
           'Compared with real Masters history 1995-2024 (approximate, by world ranking at the time) and typical betting-market odds.', '',
           '| Measure | Simulated | Real Masters (approx.) |', '|---|---|---|',
           f'| Winning score to par | avg {S.mean(to_par):+.1f}, middle 80% {sorted(to_par)[n // 10]:+d} to '
           f'{sorted(to_par)[9 * n // 10]:+d}, range {min(to_par):+d} to {max(to_par):+d} | {REAL["winning_to_par"]} |',
           f'| Field scoring average (rounds 1-2) | {S.mean(first_rounds):.2f} | {REAL["field_round_avg"]} |',
           f'| 36-hole cut line | avg {S.mean(r["cut_to_par"] for r in rows):+.1f} | {REAL["cut_line"]} |',
           f'| Playoffs | {100 * sum(r["playoff"] for r in rows) / n:.0f}% | {REAL["playoff_rate"]} |',
           f'| Winning margin (no playoff) | {S.mean(r["margin"] for r in rows if not r["playoff"]):.1f} | {REAL["margin"]} |',
           f'| Best player in field wins | {100 * sum(x == 1 for x in win_ranks) / n:.1f}% | {REAL["favourite"]} |',
           f'| Top-10 rated player wins | {100 * sum(x <= 10 for x in win_ranks) / n:.0f}% | {REAL["top10"]} |',
           f'| Winner rated outside top 30 | {100 * sum(x > 30 for x in win_ranks) / n:.0f}% | {REAL["longshot"]} |',
           f'| Different champions per 30 editions | avg {S.mean(blocks):.1f} | {REAL["distinct_per_30"]} |',
           f'| Amateurs making the cut (of 6) | avg {S.mean(r["amateurs_cut"] for r in rows):.1f} | usually 1-2 |',
           '', '## Wins by field group', '',
           '| Group | Players | Overall range | Wins | Win % per player-start |', '|---|---|---|---|---|']
    for label in FIELD_GROUPS:
        members = [g for lab, g in labelled if lab == label]
        count = len(members)
        lo, hi = min(g.overall for g in members), max(g.overall for g in members)
        out.append(f'| {label} | {count} | {lo:.0f}-{hi:.0f} | {lab_wins[label]} ({100 * lab_wins[label] / n:.1f}%) '
                   f'| {100 * lab_wins[label] / (n * count):.2f}% |')
    out += ['', '## Lowest-rated champions', '']
    low = sorted(rows, key=lambda r: r['winner_overall'])[:5]
    for r in low:
        how = 'in a playoff' if r['playoff'] else f"by {r['margin']}"
        out.append(f"- Overall {r['winner_overall']:.1f} ({r['winner_label']}), won at {r['winning_to_par']:+d} {how}")
    text = '\n'.join(out) + '\n'
    (ROOT / 'reports').mkdir(exist_ok=True)
    (ROOT / 'reports' / 'MAJOR_TEST_REPORT.md').write_text(text, encoding='utf8')
    print(text)


if __name__ == '__main__':
    main()
