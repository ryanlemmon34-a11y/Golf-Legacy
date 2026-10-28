"""Drive a world through the weekly session from the command line (until the observer app exists).

    python tools/world.py worlds/demo create --seed 2027      # a new world, committed before its first week
    python tools/world.py worlds/demo status                  # where it is: the cursor and last commit
    python tools/world.py worlds/demo advance                 # one week
    python tools/world.py worlds/demo advance --weeks 52      # a season (committed once, at the end)
    python tools/world.py worlds/demo board most-majors       # a records list from the world's history

Every advance goes through golfsim.session (the weekly step, committed atomically when the advance ends);
Ctrl-C finishes the week being played, commits, and stops.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from golfsim.session import Session                                  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('dir')
    ap.add_argument('command', choices=('create', 'status', 'advance', 'board'))
    ap.add_argument('name', nargs='?')
    ap.add_argument('--seed', type=int, default=2027)
    ap.add_argument('--weeks', type=int, default=1)
    ap.add_argument('--workers', type=int, default=None)
    a = ap.parse_args()
    if a.command == 'create':
        s = Session.create(a.dir, seed=a.seed, workers=a.workers)
        print(f'created world {s.state["world_id"]} at {s.cursor}')
        s.close()
        return
    if a.command == 'board':
        from golfsim.archive import Archive
        from golfsim.history_stats import HistoryStats, board
        title, rows = board(HistoryStats(Archive(Path(a.dir) / 'archive')), a.name, n=20)
        print(title)
        for i, r in enumerate(rows, 1):
            print(f'{i:3d}. {r["name"]:34s} {r["value"]:>10} {"active" if r["active"] else ""}')
        return
    s = Session.open(a.dir, workers=a.workers)
    if a.command == 'status':
        print(f'world {s.state["world_id"]}: next {s.cursor}, generation {s.generation}, '
              f'{s.state["weeks_played"]} weeks played, archive through {s.state["archive_through"]}')
    else:
        t0 = time.perf_counter()
        def progress(r):
            c = r['changes']
            line = f'{r["completed"][0]} week {r["completed"][1]:2d}: {c["events"]} events'
            if c.get('new_number_one'):
                line += f', new world No. 1: {s.season.g[c["number_one"]].name}'
            if 'season_end' in c:
                line += f'; season over: {c["season_end"]["juniors"]} new juniors'
            print(line + f'  ({time.perf_counter() - t0:.0f} s)', flush=True)
        import signal
        stop = []
        signal.signal(signal.SIGINT, lambda *_: stop.append(1))     # Ctrl-C: finish this week, then stop
        s.advance(a.weeks, progress=progress, cancel=lambda: bool(stop))
        print(f'committed: next {s.cursor} (generation {s.generation})')
    s.close()


if __name__ == '__main__':
    main()
