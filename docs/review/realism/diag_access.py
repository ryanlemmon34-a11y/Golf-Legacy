"""Item 4 diagnostic (read only; PLAN.md): access of high-Overall golfers to the Premier Tour and the Overall gaps at
the top of Premier fields, per seed, from tools/long_world.py outputs. Nothing here changes or boosts anyone.
Usage: python diag_access.py LABEL:DIR:SEED [...] > OUT.md
"""
from __future__ import annotations

import statistics as S
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compare_worlds import analyse, load, table  # noqa: E402


def main(specs):
    rows, gaps = [], []
    for spec in specs:
        label, d, seed = spec.rsplit(':', 2)
        r = analyse(*load(d, int(seed)))
        ys = r['years']
        acc = [r['access'][y] for y in ys]
        why = Counter()
        for x in acc:
            why.update(x[1])
        top = [r['top'][y] for y in ys]
        rows.append([label, seed, len(ys), f'{S.mean(x[0] for x in acc):.1f}',
                     ', '.join(f'{w} {c / len(acc):.1f}' for w, c in why.most_common(4)),
                     f'{S.mean(x[2] for x in acc if x[2] is not None):.2f}',
                     f'{S.mean(x[3] for x in acc if x[3] is not None):.2f}',
                     f'{S.mean(t[4] for t in top):.1f}', f'{S.mean(t[0] for t in top):.1f}'])
        late = ys[len(ys) // 2:]
        gaps.append([label, seed, f'{late[0]}-{late[-1]}',
                     f'{S.mean(r["access"][y][2] for y in late if r["access"][y][2] is not None):.2f}',
                     f'{S.mean(r["access"][y][3] for y in late if r["access"][y][3] is not None):.2f}',
                     f'{max(r["access"][y][3] for y in late if r["access"][y][3] is not None):.2f}',
                     f"{S.mean(r['access'][y][0] for y in late):.1f}"])
    print('### World top-100 by Overall who are not on the Premier Tour, and Premier Tour MEMBERS\' Overall gaps '
          '(season-end; all seasons)\n')
    print('Diagnostic only (item 4 partial): being off the Premier Tour (amateur, college, another tour, eligibility, '
          'scheduling) does not establish blocked access; member gaps are not tournament-field or major-field gaps; a '
          'later era of a run does not establish that the starting population is gone.\n')
    print(table(rows, ['run', 'seed', 'seasons', 'top-100 not on Premier (mean)', 'where (mean per season)',
                       'Premier members: best minus 10th', 'best minus 20th', 'best Overall', 'top-20 mean age']))
    print('\n### Second half of each run (later seasons; not a claim that the starting population has gone)\n')
    print(table(gaps, ['run', 'seed', 'seasons', 'members: best minus 10th', 'best minus 20th', 'largest best-minus-20th',
                       'top-100 not on Premier']))


if __name__ == '__main__':
    main(sys.argv[1:])
