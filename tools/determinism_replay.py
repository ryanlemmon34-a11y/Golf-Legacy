"""Replay one season of a long run from the copy kept before it and compare every digest with the original's.

    python tools/determinism_replay.py --out <long-run folder> --seed 2027 [--workers 2]

tools/long_world.py --keep-after N copies the world after N seasons (world_<seed>_after<N>) and records the
digests of season N + 1 as the run played it (tools/equivalence_check.parts). This plays season N + 1 again from
the copy, the same way (an observer season skip), and reports each part as identical or different. The copy is
advanced in place (it was made for this).
"""
from __future__ import annotations

import argparse
import json
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--seed', type=int, required=True)
    ap.add_argument('--workers', type=int, default=None)
    a = ap.parse_args()
    import equivalence_check as EQ
    import observer
    out = Path(a.out)
    with open(out / f'seed_{a.seed}.state.pkl', 'rb') as f:
        data = pickle.load(f)[0]
    want = data['determinism']
    copy = next(out.glob(f'world_{a.seed}_after*'))
    w = observer.World(copy, workers=a.workers) if a.workers else observer.World(copy)
    c = w.session.cursor
    y = c['year']
    if y != want['season']:
        raise SystemExit(f'the copy is at {y}, the recorded digests are of {want["season"]}')
    w.submit({'weeks': ['season'], 'year': [str(y)], 'week': [str(c['week'])], 'phase': [c['phase']],
              'op': [f'long-{a.seed}-{y}']})
    got = EQ.parts(w.session, copy)
    w.session.close()
    same = {k: got.get(k) == v for k, v in want['parts'].items()}
    report = {'seed': a.seed, 'season': y, 'identical': all(same.values()), 'parts': same}
    (out / f'determinism_{a.seed}.json').write_text(json.dumps(report, indent=1))
    print(json.dumps(report, indent=1))
    sys.exit(0 if report['identical'] else 1)


if __name__ == '__main__':
    main()
