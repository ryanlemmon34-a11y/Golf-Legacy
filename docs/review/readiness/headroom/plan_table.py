"""Reproduces PLAN.md's headroom tables from study.readiness_knee (no randomness).

    python3 -I plan_table.py <checkout>
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import study as S  # noqa: E402

ARMS = ('A0', 'B1', 'B2')


def headroom(arm, p, age=18):
    return S.deficit(age, S.tempo(S.ARMS[arm], p, 0.0), p, 1.0)


def phi(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def share_at_most(arm, h):
    """P(headroom at 18 <= h) for p ~ N(27, 2): headroom falls as p falls, so find the largest such p."""
    lo, hi = 0.0, 40.0
    for _ in range(100):
        mid = (lo + hi) / 2
        if headroom(arm, mid) <= h:
            lo = mid
        else:
            hi = mid
    return phi((lo - 27.0) / 2.0)


def table():
    rows = [(z, 27 + 2 * z, [headroom(a, 27 + 2 * z) for a in ARMS]) for z in (0, -1, -1.5, -2, -2.5, -3, -3.5, -4, -5)]
    shares = [(h, [share_at_most(a, h) for a in ARMS]) for h in (3, 4, 5, 6)]
    return rows, shares


if __name__ == '__main__':
    S.setup(sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(os.path.join(os.path.dirname(__file__), *['..'] * 4)))
    rows, shares = table()
    print('| z | p | ' + ' | '.join(ARMS) + ' |')
    for z, p, hs in rows:
        print(f'| {z} | {p:g} | ' + ' | '.join(f'{h:.2f}' for h in hs) + ' |')
    for h, ss in shares:
        print(f'| at most {h} | ' + ' | '.join(f'{100 * s:.4f}%' for s in ss) + ' |')
    for a in ('B1', 'B2'):
        print(a, 'touches', f'{100 * phi((S.ARMS[a].knee[0] - 27) / 2):.1f}%')
