"""Run the starting-ability study (experiment only; nothing here changes the game or any save).

    python3 -I run.py <checkout> <tests/data/test2_nation_shares.json.gz> <workroot> [procs]

Results go to <workroot>/<manifest hash>/, one pickle per task, each carrying the manifest hash. The manifest
covers the study's source files (study.py, run.py), the configuration below, the input fixture's SHA-256 and the
checkout's git HEAD and golfsim source digest; any change gives a new directory, and a pickle whose manifest hash
differs from the current one stops the run (fail closed), so revised scripts never mix with stale results.

Tasks:
  replay   FIXED RECORDED ALLOCATION: Test2's seed 386509, candidates = production's own draws (study.ReplayStream),
           each nation's entrants = the first k passers, k = Test2's recorded allocation; every arm and pathway;
           every entrant projected (standard schedule), juniors again under the light schedule. Also, per arm, the
           outcome of the existing rule's own candidates (RECALCULATED pass counts) and the candidate churn
           against A0.
  paired   RECALCULATED SELECTION: seeds 2027, 11, 23, 83, 386509; the same study candidates under every arm, the
           existing rule's filter over its fixed candidate count (no allocation); entrants with stored potential
           >= 70 projected (standard schedule).
"""
import gzip
import hashlib
import json
import os
import pickle
import subprocess
import sys
import time
from collections import Counter
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import study as S  # noqa: E402

CHECKOUT, FIXTURE, ROOT = sys.argv[1], sys.argv[2], sys.argv[3]
PROCS = int(sys.argv[4]) if len(sys.argv) > 4 else 4
CONFIG = {'test2_seed': 386509, 'paired_seeds': [2027, 11, 23, 83, 386509], 'arms': ['A0', 'A1', 'A2', 'A3', 'A3r5'],
          'years': [2028, 2084], 'project_min_pot_paired': 70.0, 'to_age': 40}
YEARS = list(range(CONFIG['years'][0], CONFIG['years'][1] + 1))


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def manifest():
    golf = hashlib.sha256()
    gdir = os.path.join(CHECKOUT, 'golfsim')
    for name in sorted(os.listdir(gdir)):
        if name.endswith('.py'):
            golf.update(name.encode() + b'\0' + open(os.path.join(gdir, name), 'rb').read())
    head = subprocess.run(['git', '-C', CHECKOUT, 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    m = {'config': CONFIG, 'study.py': sha256_file(os.path.join(HERE, 'study.py')),
         'run.py': sha256_file(os.path.join(HERE, 'run.py')), 'fixture': sha256_file(FIXTURE),
         'checkout_head': head, 'golfsim_digest': golf.hexdigest()}
    m['hash'] = hashlib.sha256(json.dumps(m, sort_keys=True).encode()).hexdigest()[:16]
    return m


MANIFEST = manifest()
WORK = os.path.join(ROOT, MANIFEST['hash'])


def tempo_band(t):
    return 'early' if t < 25 else 'late' if t >= 29 else 'mid'


def add_generated(agg, kind, f, kept):
    """Generated candidates (the existing rule's own draws) and what selection did with them."""
    agg['n'] += 1
    agg['stage:' + f['stage']] += 1
    agg['peak_sum'] += f['peak']
    tb = tempo_band(f['tempo'])
    agg['tempo:' + tb] += 1
    if kept:
        agg['kept'] += 1
        agg['kept_peak_sum'] += f['peak']
        agg['kept_tempo_sum'] += f['tempo']
        agg['kept_tempo:' + tb] += 1
    for lo in (75, 80, 90):
        if f['pot'] >= lo:
            agg[f'pot{lo}'] += 1
            agg[f'pot{lo}_tempo:{tb}'] += 1
            if kept:
                agg[f'pot{lo}_kept'] += 1
                agg[f'pot{lo}_kept_tempo:{tb}'] += 1
                agg[f'pot{lo}_kept_peak_sum'] += f['peak']
            else:
                agg[f'pot{lo}_missed_peak_sum'] += f['peak']
    c = f['cur18'] if kind == 'juniors' else f.get('cur', f['cur18'])
    for lo in (70, 75, 80, 85, 90):
        if c >= lo:
            agg[f'cur{lo}'] += 1
            agg[f'cur{lo}_kept'] += kept


def record(kind, key, year, row, f, project, schedule):
    country, age, pot_s, peak, cur, status, aging = row
    rec = {'kind': kind, 'key': key, 'year': year, 'country': country, 'age': age, 'cur': cur, 'pot_s': pot_s,
           'pot': f['pot'], 'peak': peak, 'tempo': f['tempo'], 'aging': aging}
    if project:
        g = S.build(row, S.study_id(key), key)
        rec['ov0'] = g.overall
        rec['work_ethic'] = g.personality['work_ethic']
        tr = S.project(g, age, key, schedule, CONFIG['to_age'])
        rec['traj'] = [round(tr[a], 2) for a in range(age, CONFIG['to_age'] + 1)]
    return rec


def replay_task(arm_name, kind, schedule):
    S.setup(CHECKOUT)
    fx = json.load(gzip.open(FIXTURE, 'rt'))
    arm, a0 = S.ARMS[arm_name], S.ARMS['A0']
    agg, churn, ents = Counter(), Counter(), []
    for y in YEARS:
        alloc = fx['years'][str(y)]['allocated'][kind]
        for country, prof in S.NATIONS.items():
            k, need = alloc.get(country, 0), S.P._cand_n(kind, prof)
            rs = S.ReplayStream(kind, y, CONFIG['test2_seed'], country)
            e_arm, o_arm = S.replay_entrants(rs, k, arm, need)
            e_0, o_0 = S.replay_entrants(rs, k, a0, need)
            for (d, stage, f), (_, stage0, _) in zip(o_arm, o_0):
                f['stage'] = stage
                add_generated(agg, kind, f, stage == 'kept')
                churn['pass_both'] += stage == 'kept' and stage0 == 'kept'
                churn['pass_only_A0'] += stage0 == 'kept' and stage != 'kept'
                churn['pass_only_arm'] += stage == 'kept' and stage0 != 'kept'
            da, d0 = {d for d, _, _ in e_arm}, {d for d, _, _ in e_0}
            churn['enter_both'] += len(da & d0)
            churn['enter_only_A0'] += len(d0 - da)
            churn['enter_only_arm'] += len(da - d0)
            for d, row, f in e_arm:
                ents.append(record(kind, f'{rs.keybase}:{d}', y, row, f, True, schedule))
    return {'layer': 'replay', 'seed': CONFIG['test2_seed'], 'arm': arm_name, 'kind': kind, 'schedule': schedule,
            'generated': dict(agg), 'churn': dict(churn), 'entrants': ents}


def paired_task(seed, kind):
    S.setup(CHECKOUT)
    arms = [S.ARMS[a] for a in CONFIG['arms']]
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
                        ents[arm.name].append(record(kind, key, y, row, f,
                                                     row[2] >= CONFIG['project_min_pot_paired'], 'standard'))
                for a in CONFIG['arms'][1:]:
                    churn[f'{a}:pass_both'] += kept['A0'] and kept[a]
                    churn[f'{a}:pass_only_A0'] += kept['A0'] and not kept[a]
                    churn[f'{a}:pass_only_arm'] += kept[a] and not kept['A0']
    return {'layer': 'paired', 'seed': seed, 'kind': kind, 'generated': {k: dict(v) for k, v in agg.items()},
            'entrants': ents, 'churn': dict(churn)}


def run(task):
    t0 = time.time()
    name = '_'.join(map(str, task))
    path = os.path.join(WORK, name + '.pkl')
    if os.path.exists(path):
        with open(path, 'rb') as fh:
            old = pickle.load(fh)
        if old.get('manifest') != MANIFEST['hash']:
            raise RuntimeError(f'{path}: manifest {old.get("manifest")} is not {MANIFEST["hash"]}; refusing to reuse')
        return name, 0.0
    res = replay_task(*task[1:]) if task[0] == 'replay' else paired_task(*task[1:])
    res['manifest'] = MANIFEST['hash']
    with open(path + '.tmp', 'wb') as fh:
        pickle.dump(res, fh, protocol=4)
    os.replace(path + '.tmp', path)
    return name, time.time() - t0


TASKS = ([('replay', a, k, 'standard') for a in CONFIG['arms'] for k in ('juniors', 'new_pros')]
         + [('paired', s, k) for s in CONFIG['paired_seeds'] for k in ('juniors', 'new_pros')]
         + [('replay', a, 'juniors', 'light') for a in CONFIG['arms']])

if __name__ == '__main__':
    os.makedirs(WORK, exist_ok=True)
    mpath = os.path.join(WORK, 'manifest.json')
    if os.path.exists(mpath) and json.load(open(mpath))['hash'] != MANIFEST['hash']:
        raise SystemExit(f'{mpath} belongs to another manifest')
    json.dump(MANIFEST, open(mpath, 'w'), indent=1)
    print('manifest', json.dumps(MANIFEST), flush=True)
    t0 = time.time()
    with Pool(PROCS) as pool:
        for name, dt in pool.imap_unordered(run, TASKS):
            print(f'{time.time() - t0:7.1f}s  {name}  ({dt:.1f}s)', flush=True)
    print('done', WORK, round(time.time() - t0, 1), flush=True)
