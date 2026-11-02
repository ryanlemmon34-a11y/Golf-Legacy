"""Replay the save's own history with the save's own engine; verify it week by week against the archive; capture
each started field's exact pre-event state for the experiments. Fails closed.

Usage: python replay.py CHECKOUT SAVE_DIR WORK_DIR --seasons N --capture CAPDIR --editions CSV [--workers W]
                        [--resume]

CHECKOUT must be a clean checkout whose engine id equals the save's (c0d1ea5 for the Test2 save: engine
1949ff63...). A new session is created in WORK_DIR from the save's seed and start year exactly as the observer
creates a world (generate_world(year, seed), calendar v2, amateur support on) and advanced a season at a time
(one commit per season, as the observer's "advance to the end of the season").

Verification, after each season, for EVERY week 1..52 (the season's results are all still in memory):
  - the set of edition ids played that week equals the set the archive holds for that week, exactly;
  - each edition's complete finish list (every site: golfer, position, total) and every round's recorded
    conditions are equal;
  - every capture record of the season (below) is bound to its edition: its edition is a primary edition
    of that year, the finish the engine returned for the captured task equals the archived finish, the captured
    field equals the starters, and the captured editions are exactly the year's primary editions (none missing,
    none extra, none twice).
The first failure stops the replay with exit code 2. CAPDIR/MANIFEST.json marks each season verified or not
(with the first bad week); experiments may use only captures of verified seasons, and none from or after a
failed week.

Capture: the worker's play_site is wrapped. BEFORE the task is played the wrapper records each starter's exact
pre-event state as the worker received it:
  - ids;
  - the 21 attributes x10 (uint16);
  - the five personality traits x10;
  - season fatigue;
  - effective familiarity rounds on the course;
  - the caddie's six skills.
The wrapper also pickles the complete task of selected editions: majors, Premier in years ending in 7, and tiers
2-4 in weeks 10-13 of 2027 and 2057. After play it records the finish the engine returned, which binds the
captured inputs to their output. All capture files are written and read only by this study's own processes
(never a downloaded file) and stay in RAM scratch.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import pickle
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

SELECTED = set()
CAP = None
ORIG = None


def selected_editions(path):
    out, prim = set(), defaultdict(set)
    with gzip.open(path, 'rt') as f:
        for r in csv.DictReader(f):
            if r['primary'] != '1':
                continue
            y, t, w = int(r['year']), int(r['tier']), int(r['week'])
            prim[y].add(r['eid'])
            if t == 0 or (t == 1 and y % 10 == 7) or (2 <= t <= 4 and y in (2027, 2057) and 10 <= w <= 13):
                out.add(r['eid'])
    return out, prim


def _state(task):
    from golfsim.ratings import ATTRIBUTE_KEYS, PERSONALITY_KEYS
    from golfsim.golfer import CADDIE_SKILLS
    gs = task['golfers']
    fk = task['course'].familiarity_key
    return (task['event_id'], task['site'], fk,
            np.array([g.id for g in gs], np.int32),
            np.array([[round(g.attrs[k] * 10) for k in ATTRIBUTE_KEYS] for g in gs], np.uint16),
            np.array([[round(g.personality[k] * 10) for k in PERSONALITY_KEYS] for g in gs], np.uint16),
            np.array([g.fatigue for g in gs], np.float32),
            np.array([g.familiarity.get(fk, 0.0) for g in gs], np.float32),
            np.array([[round(c.skills[k] * 10) for k in CADDIE_SKILLS] for c in (task.get('caddies') or [])],
                     np.uint16).reshape(-1, len(CADDIE_SKILLS)))


def hooked(task):
    """play_site with the capture taken BEFORE play (module level, so the forked worker pool can pickle it by
    reference), and the engine's own output recorded after, binding inputs to output."""
    if not (len(task['golfers']) and not task['match_play'] and task.get('estimate')):
        return ORIG(task)
    state = _state(task)
    blob = pickle.dumps(task, protocol=pickle.HIGHEST_PROTOCOL) if task['event_id'] in SELECTED else None
    out = ORIG(task)
    year = task['event_id'].split(':')[0]
    fin = [list(x) for x in out['finish']]
    with open(CAP / f'starts_{year}_{os.getpid()}.pkl', 'ab') as f:
        pickle.dump(state + (fin,), f, protocol=pickle.HIGHEST_PROTOCOL)
    if blob is not None:
        with open(CAP / 'tasks' / (task['event_id'].replace(':', '_') + f'_s{task["site"]}.pkl'), 'wb') as f:
            f.write(blob)
    return out


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def read_capture(path):
    with open(path, 'rb') as f:
        while True:
            try:
                yield pickle.load(f)
            except EOFError:
                return


def verify_season(y, results, arch_events, primary_ids, cap):
    """(first bad week or None, problems list, capture summary). bad week 0: results matched, capture did not."""
    want = defaultdict(dict)
    for e in arch_events:
        want[e['week']][e['id']] = e
    got = defaultdict(dict)
    for r in results:
        got[r.week][r.event_id] = r
    problems, bad_week = [], None
    for w in sorted(set(want) | set(got)):
        a, b = set(want[w]), set(got[w])
        if a != b:
            problems.append({'week': w, 'missing': sorted(a - b)[:5], 'extra': sorted(b - a)[:5]})
        for eid in sorted(a & b):
            r, e = got[w][eid], want[w][eid]
            if [[list(x) for x in site] for site in r.finish] != e['finish']:
                problems.append({'week': w, 'edition': eid, 'what': 'finish'})
            elif [[list(map(float, c)) for c in s] for s in r.conditions] != \
                    [[list(map(float, c)) for c in s] for s in e.get('conditions', [])]:
                problems.append({'week': w, 'edition': eid, 'what': 'conditions'})
        if problems:
            bad_week = w
            break
    capsum = {'records': 0}
    if bad_week is None:
        seen = set()
        by_id = {e['id']: e for e in arch_events}
        files = sorted(cap.glob(f'starts_{y}_*.pkl'))
        for p in files:
            for rec in read_capture(p):
                eid, site, fin = rec[0], rec[1], rec[-1]
                capsum['records'] += 1
                if eid in seen:
                    problems.append({'edition': eid, 'what': 'captured twice'})
                seen.add(eid)
                if eid not in primary_ids:
                    problems.append({'edition': eid, 'what': 'captured but not a primary edition'})
                elif by_id[eid]['finish'][site] != fin:
                    problems.append({'edition': eid, 'what': 'captured task output differs from the archive'})
                elif sorted(rec[3].tolist()) != sorted(x[0] for x in by_id[eid]['finish'][site]):
                    problems.append({'edition': eid, 'what': 'captured field differs from the starters'})
        if seen != primary_ids:
            problems.append({'what': 'captured editions differ from the primary editions',
                             'missing': sorted(primary_ids - seen)[:5], 'extra': sorted(seen - primary_ids)[:5]})
        capsum['files'] = {p.name: sha256(p) for p in files}
        tasks = sorted((cap / 'tasks').glob(f'{y}_*.pkl'))
        capsum['tasks'] = {p.name: sha256(p) for p in tasks}
        if problems:
            bad_week = 0
    return bad_week, problems, capsum


def main():
    global CAP, SELECTED, ORIG
    ap = argparse.ArgumentParser()
    ap.add_argument('checkout')
    ap.add_argument('save')
    ap.add_argument('work')
    ap.add_argument('--seasons', type=int, required=True)
    ap.add_argument('--capture', required=True)
    ap.add_argument('--editions', required=True)
    ap.add_argument('--workers', type=int, default=3)
    ap.add_argument('--resume', action='store_true', help='continue the committed session in WORK_DIR')
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
    if eng != meta['engine']:
        print(json.dumps({'event': 'refused', 'reason': f'engine {eng} is not the save engine {meta["engine"]}'}))
        sys.exit(2)
    seed = int(meta['world_id'].split('-')[0])
    start = json.loads(C.archive_file(a.save, 'world').read_text())['first_year']
    years = C.year_files(a.save)
    CAP = Path(a.capture)
    (CAP / 'tasks').mkdir(parents=True, exist_ok=True)
    SELECTED, primary = selected_editions(a.editions)
    man_path = CAP / 'MANIFEST.json'
    man = json.loads(man_path.read_text()) if (a.resume and man_path.exists()) else {
        'format': 'winning-capture/1', 'save': meta, 'engine': eng, 'python': sys.version.split()[0],
        'script_sha256': sha256(__file__), 'editions_sha256': sha256(a.editions), 'years': {}}
    if any(not v['verified'] for v in man['years'].values()):
        print(json.dumps({'event': 'refused', 'reason': 'the manifest records a failed season'}))
        sys.exit(2)
    if a.resume and man['script_sha256'] != sha256(__file__):
        print(json.dumps({'event': 'refused', 'reason': 'replay.py changed since the manifest was started'}))
        sys.exit(2)
    verified = {int(y) for y, v in man['years'].items() if v['verified']}
    for p in list(CAP.glob('starts_*.pkl')) + list((CAP / 'tasks').glob('*.pkl')):
        if int(p.name.split('_')[1 if p.name.startswith('starts_') else 0]) not in verified:
            p.unlink()                          # this study's own partial capture of an unverified season
    ORIG = SEA.play_site
    SEA.play_site = hooked
    t0 = time.time()
    work = Path(a.work)
    if a.resume:                                # a committed session resumes exactly (its saves replay exactly)
        s = Session.open(work / 'w', workers=a.workers)
    else:
        s = Session.create(work / 'w', seed=seed, workers=a.workers, world=generate_world(year=start, seed=seed),
                           calendar='v2')
    if s.cursor != {'year': (max(verified) + 1 if verified else start), 'week': 1, 'phase': 'start'}:
        print(json.dumps({'event': 'refused', 'reason': f'session at {s.cursor} does not follow the manifest'}))
        sys.exit(2)
    print(json.dumps({'event': 'resumed' if a.resume else 'created', 'cursor': s.cursor,
                      'seconds': round(time.time() - t0, 1), 'engine': eng, 'python': sys.version.split()[0],
                      'selected_tasks': len(SELECTED)}), flush=True)
    code = 0
    for _ in range(a.seasons):
        t1 = time.time()
        y = s.cursor['year']
        if y not in years:
            print(json.dumps({'event': 'stop', 'reason': f'{y} is not archived'}), flush=True)
            break
        arch = C.load_year(years[y])['events']
        s.advance(52)
        res = [r for r in s.season.results.values() if r.year == y]
        bad_week, problems, capsum = verify_season(y, res, arch, primary.get(y, set()), CAP)
        man['years'][str(y)] = {'verified': bad_week is None, 'first_bad_week': bad_week,
                                'weeks_verified': (52 if bad_week is None else max(0, (bad_week or 1) - 1)),
                                'editions': len(arch), 'primary': len(primary.get(y, ())),
                                'problems': problems[:10], **capsum}
        tmp = man_path.with_suffix('.tmp')
        tmp.write_text(json.dumps(man, indent=1))
        tmp.replace(man_path)
        print(json.dumps({'event': 'season', 'year': y, 'verified': bad_week is None, 'played': len(res),
                          'archived': len(arch), 'captured': capsum['records'], 'problems': problems[:3],
                          'seconds': round(time.time() - t1, 1)}), flush=True)
        if bad_week is not None:
            code = 2
            break
    s.close()
    print(json.dumps({'event': 'done', 'code': code, 'verified_seasons': sum(v['verified'] for v in
                      man['years'].values()), 'seconds': round(time.time() - t0)}), flush=True)
    sys.exit(code)


if __name__ == '__main__':
    main()
