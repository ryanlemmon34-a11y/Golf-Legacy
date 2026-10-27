"""High-school championship at Cedar Creek Municipal (the easiest course in the world).

    python tools/high_school_test.py [--events 600]

1. A 96-player high-school field (mostly varsity players around rating 10, some good amateurs, a few
   blue-chip recruits) plays 36 holes, no cut, many times over.
2. Hole-to-hole and week-to-week variance of individual juniors.
3. For contrast, the Masters professional field plays the same course.
Writes reports/HIGH_SCHOOL_TEST_REPORT.md.
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
sys.path.insert(0, str(ROOT / 'tools'))
from golfsim.course import ashford_ridge, cedar_creek_municipal     # noqa: E402
from golfsim.engine import WeekForm, play_round                       # noqa: E402
from golfsim.golfer import ARCHETYPES, Golfer, archetype_golfer       # noqa: E402
from golfsim.ratings import ATTRIBUTE_KEYS                            # noqa: E402
from golfsim.tournament import play_event                             # noqa: E402
from major_test import build_field as masters_field                   # noqa: E402

HS_GROUPS = (('Varsity', 9, 5, 70), ('Good amateur', 22, 5, 20), ('Blue-chip recruit', 40, 5, 6))


def build_hs_field(seed=11):
    """Juniors have uneven, still-developing skill profiles: each attribute gets extra noise."""
    rng = random.Random(seed)
    names = list(ARCHETYPES)
    field, i = [], 0
    for label, centre, spread, count in HS_GROUPS:
        for _ in range(count):
            ov = max(0.0, rng.gauss(centre, spread))
            base = archetype_golfer(names[i % len(names)], round(ov, 1))
            attrs = {k: max(1.0, min(99.0, v + rng.gauss(0, 6))) for k, v in base.attrs.items()}
            g = Golfer(f'HS{i:02d}', attrs, {**base.personality, 'big_stage': rng.uniform(5, 60)},
                       archetype=base.archetype)
            g.familiarity['Cedar Creek Municipal Golf Course'] = rng.randint(0, 20)
            field.append((label, g))
            i += 1
    return field


def run_hs(args):
    n, seed = args
    course = cedar_creek_municipal()
    labelled = build_hs_field()
    field = [g for _, g in labelled]
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        board, playoff = play_event(field, course, rng, prestige=0.5, rounds_n=2, cut_after=None)
        totals = [t for _, t, _ in board]
        out.append(dict(winner=board[0][0].name, win=totals[0] - 2 * course.par, tenth=totals[9] - 2 * course.par,
                        rounds=[s for _, _, r in board for s in r], playoff=playoff > 0,
                        totals={g.name: t for g, t, _ in board}))
    return out


def run_pros(args):
    n, seed = args
    course = cedar_creek_municipal()
    field = [g for _, g in masters_field()]
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        board, _ = play_event(field, course, rng, cut_top=50)
        out.append(dict(win=board[0][1] - 4 * course.par, rounds=[s for _, _, r in board for s in r]))
    return out


def hole_profile(args):
    rating, course_key, n = args
    course = {'easy': cedar_creek_municipal, 'mid': ashford_ridge}[course_key]()
    g = archetype_golfer('All-Rounder', rating)
    rng = random.Random(rating)
    holes, rounds = [], []
    for _ in range(n):
        st = play_round(g, course, rng, week_form=WeekForm.draw(rng, g))
        rounds.append(st.score)
        holes += [s - h.par for s, h in zip(st.holes, course.holes)]
    return args, dict(avg=S.mean(rounds), round_sd=S.pstdev(rounds), hole_sd=S.pstdev(holes),
                      best=min(rounds), worst=max(rounds),
                      birdie_plus=sum(x < 0 for x in holes) / len(holes), double_plus=sum(x >= 2 for x in holes) / len(holes))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--events', type=int, default=600)
    a = ap.parse_args()
    per = a.events // 4
    with ProcessPoolExecutor() as ex:
        hs = [r for b in ex.map(run_hs, [(per, 70 + i) for i in range(4)]) for r in b]
        pros = [r for b in ex.map(run_pros, [(max(25, per // 6), 90 + i) for i in range(4)]) for r in b]
        prof = dict(ex.map(hole_profile, [(r, ck, 3000) for r in (10, 25, 40, 75, 90) for ck in ('easy', 'mid')]))
    labelled = build_hs_field()
    label_of = {g.name: lab for lab, g in labelled}
    by_rank = sorted((g for _, g in labelled), key=lambda g: -g.overall)
    rank_of = {g.name: i + 1 for i, g in enumerate(by_rank)}
    n = len(hs)
    par = 72
    wins = [r['win'] for r in hs]
    tenth = [r['tenth'] for r in hs]
    rounds = [s for r in hs for s in r['rounds']]
    win_rank = [rank_of[r['winner']] for r in hs]
    lab_wins = Counter(label_of[r['winner']] for r in hs)

    # Week-to-week: the same junior's 36-hole total across every event.
    typical = min(by_rank, key=lambda g: abs(g.overall - 10))
    star = by_rank[0]
    def weekly(g):
        t = [r['totals'][g.name] - 2 * par for r in hs]
        return S.mean(t), S.pstdev(t), min(t), max(t)

    pro_wins = [r['win'] for r in pros]
    pro_rounds = [s for r in pros for s in r['rounds']]
    lines = ['# High-school championship at Cedar Creek Municipal', '',
             f'Cedar Creek Municipal (Muncie, Indiana): par 72, 6,180 yards — wide, open, slow flat greens, '
             f'one pond. {n} simulated 36-hole high-school championships, 96 players, no cut.', '',
             '## The tournament', '',
             '| Measure | Result |', '|---|---|',
             f'| Winning 36-hole score | avg {S.mean(wins):+.1f}, middle 80% {sorted(wins)[n // 10]:+d} to '
             f'{sorted(wins)[9 * n // 10]:+d}, best {min(wins):+d}, worst {max(wins):+d} |',
             f'| 10th place | avg {S.mean(tenth):+.1f} |',
             f'| Field scoring average per round | {S.mean(rounds):.1f} |',
             f'| Rounds under par | {100 * sum(s < par for s in rounds) / len(rounds):.1f}% |',
             f'| Rounds of 100 or more | {100 * sum(s >= 100 for s in rounds) / len(rounds):.1f}% |',
             f'| Lowest round seen | {min(rounds)} ({min(rounds) - par:+d}) |',
             f'| Playoffs | {100 * sum(r["playoff"] for r in hs) / n:.0f}% |',
             f'| Top-rated junior wins | {100 * sum(x == 1 for x in win_rank) / n:.0f}% |',
             f'| Winner from outside the top 5 | {100 * sum(x > 5 for x in win_rank) / n:.0f}% |',
             '', '| Group | Players | Overall range | Share of wins |', '|---|---|---|---|']
    for label, _, _, count in HS_GROUPS:
        members = [g for lab, g in labelled if lab == label]
        lines.append(f'| {label} | {count} | {min(g.overall for g in members):.0f}-{max(g.overall for g in members):.0f} '
                     f'| {100 * lab_wins[label] / n:.1f}% |')
    lines += ['', '## Week-to-week swings (the same junior, every event)', '',
              '| Junior | Overall | Avg 36-hole score | Spread (SD) | Best week | Worst week |', '|---|---|---|---|---|---|']
    for label, g in (('Typical varsity player', typical), ('Top recruit', star)):
        m, sd, lo, hi = weekly(g)
        lines.append(f'| {label} | {g.overall:.0f} | {m:+.1f} | {sd:.1f} | {lo:+d} | {hi:+d} |')
    lines += ['', '## Hole-to-hole and round-to-round variance', '',
              'All-rounder golfers, 3,000 rounds each with fresh daily and weekly form.', '',
              '| Rating | Course | Avg | Round SD | Best / worst round | Hole SD | Birdie+ holes | Double+ holes |',
              '|---|---|---|---|---|---|---|---|']
    for r in (10, 25, 40, 75, 90):
        for ck, name in (('easy', 'Cedar Creek'), ('mid', 'Ashford Ridge')):
            p = prof[(r, ck, 3000)]
            lines.append(f'| {r} | {name} | {p["avg"]:.1f} | {p["round_sd"]:.2f} | {p["best"]} / {p["worst"]} | '
                         f'{p["hole_sd"]:.2f} | {100 * p["birdie_plus"]:.1f}% | {100 * p["double_plus"]:.1f}% |')
    lines += ['', '## For contrast: the Masters field plays Cedar Creek', '',
              f'{len(pros)} simulated 72-hole events with the same professional field used at Georgia National.', '',
              f'- Winning score: avg {S.mean(pro_wins):+.1f} (best {min(pro_wins):+d}).',
              f'- Field scoring average: {S.mean(pro_rounds):.1f} per round.',
              f'- Rounds of 62 or better: {100 * sum(s <= 62 for s in pro_rounds) / len(pro_rounds):.1f}%; '
              f'rounds of 59 or better: {sum(s <= 59 for s in pro_rounds)} of {len(pro_rounds):,}; '
              f'lowest round: {min(pro_rounds)} ({min(pro_rounds) - par:+d}).']
    text = '\n'.join(lines) + '\n'
    (ROOT / 'reports').mkdir(exist_ok=True)
    (ROOT / 'reports' / 'HIGH_SCHOOL_TEST_REPORT.md').write_text(text, encoding='utf8')
    print(text)


if __name__ == '__main__':
    main()
