"""Run the starting-ability study (experiment only). Writes one pickle per task into <workdir> (disposable, kept in
RAM) for report.py; nothing here changes the game or any save.

    python3 -I run.py <checkout> <tests/data/test2_nation_shares.json.gz> <workdir> [procs]

Tasks:
  replay   Test2's seed 386509, each nation's recorded allocation, every arm and pathway; every entrant projected
           (standard schedule) and the juniors again under the light schedule (sensitivity)
  paired   seeds 2027, 11, 23, 83, 386509: the same candidates under every arm (existing-rule selection); entrants
           with stored potential >= 70 projected (standard schedule)
"""
import gzip
import json
import os
import pickle
import sys
import time
from collections import Counter, defaultdict
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import study as S  # noqa: E402

CHECKOUT, FIXTURE, WORK = sys.argv[1], sys.argv[2], sys.argv[3]
PROCS = int(sys.argv[4]) if len(sys.argv) > 4 else 4
TEST2_SEED = 386509
PAIRED_SEEDS = (2027, 11, 23, 83, 386509)
ARM_NAMES = ('A0', 'A1', 'A2', 'A3', 'A3r5')
YEARS = list(range(2028, 2085))
PROJECT_MIN_POT = 70.0


def tempo_band(t):
    return 'early' if t < 25 else 'late' if t >= 29 else 'mid'


def add_generated(agg, kind, f, kept):
    """Generated candidates (the existing rule's draws) and what selection did with them."""
    agg['n'] += 1
    agg['stage:' + f['stage']] += 1
    agg['peak_sum'] += f['peak']
    if kept:
        agg['kept'] += 1
        agg['kept_peak_sum'] += f['peak']
        agg['kept_tempo_sum'] += f['tempo']
    tb = tempo_band(f['tempo'])
    agg['tempo:' + tb] += 1
    agg['kept_tempo:' + tb] += kept
    for lo in (75, 80, 90):
        if f['pot'] >= lo:
            agg[f'pot{lo}'] += 1
            agg[f'pot{lo}_kept'] += kept
            agg[f'pot{lo}_tempo:{tb}'] += 1
            agg[f'pot{lo}_kept_tempo:{tb}'] += kept
            if kept:
                agg[f'pot{lo}_kept_peak_sum'] += f['peak']
            else:
                agg[f'pot{lo}_missed_peak_sum'] += f['peak']
    c = f['cur18'] if kind == 'juniors' else f.get('cur', f['cur18'])
    for lo in (70, 75, 80, 85, 90):
        if c >= lo:
            agg[f'cur{lo}'] += 1
            agg[f'cur{lo}_kept'] += kept


def record(kind, key, year, country, row, f, project, schedule):
    country, age, pot_s, peak, cur, status, aging = row
    rec = {'kind': kind, 'key': key, 'year': year, 'country': country, 'age': age, 'cur': cur, 'pot_s': pot_s,
           'pot': f['pot'], 'peak': peak, 'tempo': f['tempo'], 'aging': aging}
    if project:
        g = S.build(row, S.study_id(key), key)
        rec['ov0'] = g.overall
        rec['work_ethic'] = g.personality['work_ethic']
        tr = S.project(g, age, key, schedule)
        rec['traj'] = [round(tr[a], 2) for a in range(age, 41)]
    return rec


def replay_task(arm_name, kind, schedule):
    S.setup(CHECKOUT)
    fx = json.load(gzip.open(FIXTURE, 'rt'))
    arm = S.ARMS[arm_name]
    agg = Counter()
    ents = []
    for y in YEARS:
        alloc = fx['years'][str(y)]['allocated'][kind]
        for country in S.NATIONS:
            k = alloc.get(country, 0)
            rows, facts = S.replay_cohort(kind, y, TEST2_SEED, country, k, arm)
            for f in facts:
                if f['in_existing_rule']:
                    add_generated(agg, kind, f, f['stage'] == 'kept')
            for row, f in rows:
                key = f'{TEST2_SEED}:{kind}:{y}:{country}:{f["d"]}'
                ents.append(record(kind, key, y, country, row, f, True, schedule))
    return {'layer': 'replay', 'seed': TEST2_SEED, 'arm': arm_name, 'kind': kind, 'schedule': schedule,
            'generated': dict(agg), 'entrants': ents}


def paired_task(seed, kind):
    S.setup(CHECKOUT)
    arms = [S.ARMS[a] for a in ARM_NAMES]
    agg = {a.name: Counter() for a in arms}
    ents = {a.name: [] for a in arms}
    churn = Counter()
    for y in YEARS:
        for country in S.NATIONS:
            for d, cand in enumerate(S.paired_candidates(kind, y, seed, country)):
                key = f'{seed}:paired:{kind}:{y}:{country}:{d}'
                kept = {}
                for arm in arms:
                    stage, row, f = S.paired_outcome(kind, cand, country, arm)
                    f['stage'] = stage
                    kept[arm.name] = row is not None
                    add_generated(agg[arm.name], kind, f, kept[arm.name])
                    if row is not None:
                        ents[arm.name].append(record(kind, key, y, country, row, f, row[2] >= PROJECT_MIN_POT,
                                                     'standard'))
                for a in ARM_NAMES[1:]:
                    churn[f'{a}:kept_both'] += kept['A0'] and kept[a]
                    churn[f'{a}:only_A0'] += kept['A0'] and not kept[a]
                    churn[f'{a}:only_arm'] += kept[a] and not kept['A0']
    return {'layer': 'paired', 'seed': seed, 'kind': kind, 'generated': {k: dict(v) for k, v in agg.items()},
            'entrants': ents, 'churn': dict(churn)}


def run(task):
    t0 = time.time()
    name = '_'.join(map(str, task))
    path = os.path.join(WORK, name + '.pkl')
    if os.path.exists(path):
        return name, 0.0
    res = replay_task(*task[1:]) if task[0] == 'replay' else paired_task(*task[1:])
    with open(path + '.tmp', 'wb') as fh:
        pickle.dump(res, fh, protocol=4)
    os.replace(path + '.tmp', path)
    return name, time.time() - t0


if __name__ == '__main__':
    os.makedirs(WORK, exist_ok=True)
    tasks = [('replay', a, k, 'standard') for a in ARM_NAMES for k in ('juniors', 'new_pros')]
    tasks += [('paired', s, k) for s in PAIRED_SEEDS for k in ('juniors', 'new_pros')]
    tasks += [('replay', a, 'juniors', 'light') for a in ARM_NAMES]
    t0 = time.time()
    with Pool(PROCS) as pool:
        for name, dt in pool.imap_unordered(run, tasks):
            print(f'{time.time() - t0:7.1f}s  {name}  ({dt:.1f}s)', flush=True)
    print('done', round(time.time() - t0, 1), flush=True)
