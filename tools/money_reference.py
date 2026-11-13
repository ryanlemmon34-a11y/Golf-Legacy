"""Rebuild finance.MONEY_REFERENCE: the Overall at each standing (mid-rank percentile) of the professional pool of a
typical starting world, the median over REF_SEEDS starting worlds under the existing generation rule (dev-1, the
rule the money formulas were calibrated on). Prints the table to paste into golfsim/finance.py; with --check, exits
non-zero if the table in finance.py differs from a fresh build.

    python tools/money_reference.py [--check]
"""
from __future__ import annotations

import bisect
import statistics as S
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from golfsim import finance as FIN                       # noqa: E402
from golfsim import population as P                      # noqa: E402
from golfsim import realism as RZ                        # noqa: E402

REF_SEEDS = range(1, 21)
# standings stored: every 2% to 90%, every 0.5% to 99%, then the top ranks of a pool of the median size
GRID_LOW = [i / 50 for i in range(0, 46)] + [0.90 + i / 200 for i in range(1, 19)]


def value_at(sorted_vals, q):
    """The Overall at standing q in one pool (linear between mid-rank positions)."""
    n = len(sorted_vals)
    pos = q * n - 0.5
    if pos <= 0:
        return sorted_vals[0]
    if pos >= n - 1:
        return sorted_vals[-1]
    i = int(pos)
    return sorted_vals[i] + (sorted_vals[i + 1] - sorted_vals[i]) * (pos - i)


def build():
    pools = []
    for seed in REF_SEEDS:
        w = P.generate_world(seed=seed, dev_rules=RZ.LEGACY)
        pools.append(sorted(g.overall for g in w.golfers if FIN.in_money_pool(g)))
    n = int(S.median(len(p) for p in pools))
    grid = GRID_LOW + [(n - r - 0.5) / n for r in range(29, -1, -1)]          # the top 30 ranks
    grid = sorted(set(round(q, 6) for q in grid if q < 1.0)) + [1.0]
    return n, [(q, round(S.median(value_at(p, q) for p in pools), 2)) for q in grid]


def main():
    n, table = build()
    if '--check' in sys.argv:
        ok = list(FIN.MONEY_REFERENCE) == [tuple(r) for r in table]
        print('MONEY_REFERENCE', 'matches' if ok else 'DIFFERS', f'(reference pool size {n})')
        sys.exit(0 if ok else 1)
    print(f'# reference pool size (median professionals): {n}')
    print('MONEY_REFERENCE = (')
    for i in range(0, len(table), 4):
        print('    ' + ' '.join(f'({q!r}, {v!r}),' for q, v in table[i:i + 4]))
    print(')')


if __name__ == '__main__':
    main()
