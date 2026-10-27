"""Quick calibration ladder: uniform golfers at each rating vs the target scores.

    python tools/calibrate.py [--rounds 2000] [--course mid|easy|hard]
"""
from __future__ import annotations

import argparse
import random
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from golfsim.course import ashford_ridge, cedar_creek_municipal, easy_course, georgia_national, hard_course  # noqa: E402
from golfsim.engine import play_round                                 # noqa: E402
from golfsim.golfer import uniform_golfer                             # noqa: E402
from golfsim.ratings import TARGET_SCORE, interp                      # noqa: E402
from golfsim.stats import summarize                                   # noqa: E402

COURSES = {'mid': ashford_ridge, 'easy': easy_course, 'hard': hard_course, 'georgia': georgia_national, 'cedar': cedar_creek_municipal}
LADDER = (5, 10, 25, 40, 50, 60, 65, 71, 75, 80, 85, 90, 95)


def run(args):
    rating, rounds, course_key, seed = args
    course = COURSES[course_key]()
    g = uniform_golfer(rating)
    rng = random.Random(seed * 1000 + rating)
    return rating, summarize([play_round(g, course, rng) for _ in range(rounds)])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--rounds', type=int, default=2000)
    ap.add_argument('--course', default='mid', choices=COURSES)
    ap.add_argument('--seed', type=int, default=1)
    a = ap.parse_args()
    with ProcessPoolExecutor() as ex:
        results = dict(ex.map(run, [(r, a.rounds, a.course, a.seed) for r in LADDER]))
    print(f'{"rt":>3} {"avg":>6} {"tgt":>5} {"diff":>5} {"sd":>4} | {"drv":>5} {"fw":>4} {"gir":>4} {"scr":>4} '
          f'{"sand":>4} {"putt":>4} {"3p":>4} | {"p3":>4} {"p4":>4} {"p5":>4} | {"brd":>4} {"bog":>4} {"dbl+":>4} {"pen":>4} '
          f'| {"ott":>5} {"app":>5} {"arg":>5} {"putt":>5}')
    for r in LADDER:
        s = results[r]
        tgt = interp(TARGET_SCORE, r)
        print(f'{r:3d} {s["scoring_avg"]:6.2f} {tgt:5.1f} {s["scoring_avg"] - tgt:+5.1f} {s["score_sd"]:4.2f} | '
              f'{s["driving_distance"]:5.1f} {s["fairways_pct"]:4.0%} {s["gir_pct"]:4.0%} {s["scrambling_pct"]:4.0%} '
              f'{s["sand_save_pct"]:4.0%} {s["putts_per_round"]:4.1f} {s["three_putts_per_round"]:4.2f} | '
              f'{s["par3_avg"]:4.2f} {s["par4_avg"]:4.2f} {s["par5_avg"]:4.2f} | {s["birdies"] + s["eagles"]:4.2f} '
              f'{s["bogeys"]:4.2f} {s["doubles_plus"]:4.2f} {s["penalties"]:4.2f} | {s["sg_ott"]:+5.2f} {s["sg_app"]:+5.2f} '
              f'{s["sg_arg"]:+5.2f} {s["sg_putt"]:+5.2f}')


if __name__ == '__main__':
    main()
