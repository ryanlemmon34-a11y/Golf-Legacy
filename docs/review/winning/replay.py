"""Replay the save's own history with the save's own engine and check it event by event against the archive.

Usage: python replay.py CHECKOUT SAVE_DIR WORK_DIR --weeks N [--capture CAPDIR] [--workers W]

CHECKOUT must be a clean checkout whose engine id equals the save's (c0d1ea5 for the Test2 save: engine
1949ff63...). A new session is created in WORK_DIR from the save's seed and start year exactly as the observer
creates a world (generate_world(year, seed), calendar v2, amateur support on), then advanced one week at a time.
After every week each event played is compared with the archived edition: every site's complete finish list
(golfer, position, total) and every round's recorded conditions. The first mismatch stops the replay.

--capture: for every primary edition (one site, stroke play, estimated) the exact task the engine played
(golfers as the worker received them, caddies, course, seed, rounds, cut, prestige, week) is pickled to CAPDIR
(these files are written and read only by this study's own processes), plus a compact npz of every starter's
pre-event attributes, personality, fatigue and course familiarity. With --capture the engine runs with one
worker so the capture hook sees every task.
"""
from __future__ import annotations

import argparse
import gzip
import json
import pickle
import sys
import time
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('checkout')
    ap.add_argument('save')
    ap.add_argument('work')
    ap.add_argument('--weeks', type=int, default=1)
    ap.add_argument('--capture')
    ap.add_argument('--workers', type=int, default=3)
    a = ap.parse_args()
    sys.path.insert(0, a.checkout)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import common as C
    from golfsim import season as SEA
    from golfsim.population import generate_world
    from golfsim.savegame import engine_id
    from golfsim.session import Session
    meta = C.save_meta(a.save)
    eng = engine_id()
    assert eng == meta['engine'], f'engine {eng} is not the save engine {meta["engine"]}'
    seed = int(meta['world_id'].split('-')[0])
    world_json = json.loads((Path(a.save) / 'archive' / f'world.g{meta["generation"]:06d}.json').read_text())
    start = world_json['first_year']
    years = C.year_files(a.save)
    cap = Path(a.capture) if a.capture else None
    captured = []
    if cap:
        cap.mkdir(parents=True, exist_ok=True)
        orig = SEA.play_site

        def hooked(task):
            out = orig(task)
            if len(task['golfers']) and not task['match_play'] and task.get('estimate'):
                captured.append(task['event_id'])
                with open(cap / (task['event_id'].replace(':', '_') + f'_s{task["site"]}.pkl'), 'wb') as f:
                    pickle.dump(task, f, protocol=pickle.HIGHEST_PROTOCOL)
            return out
        SEA.play_site = hooked
        a.workers = 1
    t0 = time.time()
    work = Path(a.work)
    s = Session.create(work / 'w', seed=seed, workers=a.workers, world=generate_world(year=start, seed=seed),
                       calendar='v2')
    print(f'world generated and committed in {time.time() - t0:.0f}s', flush=True)
    arch = {}
    checked = mism = 0
    done = set()
    for i in range(a.weeks):
        t1 = time.time()
        y = s.cursor['year']
        if y not in arch:
            arch = {y: {e['id']: e for e in C.load_year(years[y])['events']}}
        s.advance(1)
        played = [r for r in s.season.results.values() if r.year == y and r.event_id not in done]
        done.update(r.event_id for r in played)
        wk = max((r.week for r in played), default=0)
        for r in played:
            e = arch[y].get(r.event_id)
            got = [[list(x) for x in site] for site in r.finish]
            want = e['finish'] if e else None
            cond_ok = (not e) or [[list(map(float, c)) for c in site] for site in r.conditions] == \
                [[list(map(float, c)) for c in site] for site in e.get('conditions', [])]
            checked += 1
            if want != got or not cond_ok:
                mism += 1
                print('MISMATCH', r.event_id, 'finish' if want != got else 'conditions', flush=True)
        print(f'week {wk} of {y}: {len(played)} events checked, {mism} mismatches so far, '
              f'{time.time() - t1:.1f}s', flush=True)
        if mism:
            break
    s.close()
    print(json.dumps({'checked': checked, 'mismatches': mism, 'captured': len(captured), 'engine': eng,
                      'seconds': round(time.time() - t0)}), flush=True)


if __name__ == '__main__':
    main()
