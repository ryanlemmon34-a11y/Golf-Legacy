"""Resume a long_world run from a verified checkpoint on a DIFFERENT engine build, with the boundary recorded.

Used once (results/runaway_2049): the realism branch's seed-2027 world stopped in 2049 on engine d619dd6 (the
runaway defect); its checkpoint after 2048 is continued on the build that carries the reviewed fix. The result is a
MIXED-VERSION run: seasons up to and including the boundary were played on the first engine, later seasons on this
checkout's engine. It is never presented as a single-version run.

Usage: python resume_mixed.py SRC_DIR OUT_DIR --seed 2027 --boundary 2048 --years 30 --workers 2
Run from the checkout whose engine plays the later seasons (tools/long_world.py and golfsim are taken from it).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pickle
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
import long_world as LW                                                 # noqa: E402
from golfsim import savegame as SG                                     # noqa: E402


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('out')
    ap.add_argument('--seed', type=int, required=True)
    ap.add_argument('--boundary', type=int, required=True, help='last season played on the first engine')
    ap.add_argument('--years', type=int, required=True)
    ap.add_argument('--workers', type=int, default=2)
    a = ap.parse_args()
    src, out = Path(a.src), Path(a.out)
    save, state = src / f'seed_{a.seed}.save', src / f'seed_{a.seed}.state.pkl'
    # 1. verify the checkpoint: the save and the run state both stop exactly at the boundary
    with __import__('gzip').open(save, 'rb') as f:
        meta = pickle.load(f)
    with open(state, 'rb') as f:
        data = pickle.load(f)[0]
    last = max(int(y) for y in data['rows'])
    assert meta['note'] == f'seed {a.seed} after {a.boundary}', meta['note']
    assert last == a.boundary and data['years'] == a.boundary - data['first'] + 1, (last, data['years'])
    src_manifest = json.loads((src / 'manifest.json').read_text())
    head = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    prov = {
        'kind': 'mixed-version continuation (not a single-version run)',
        'seed': a.seed,
        'first_part': {'seasons': [data['first'], a.boundary], 'commit': meta['commit'], 'engine': meta['engine'],
                       'run_manifest_commit': src_manifest.get('commit')},
        'second_part': {'seasons': [a.boundary + 1, data['first'] + a.years - 1], 'commit': head,
                        'engine': SG.engine_id()},
        'checkpoint': {'save': str(save), 'save_sha256': sha(save), 'state': str(state), 'state_sha256': sha(state),
                       'save_note': meta['note'], 'state_last_season': last, 'state_seasons': data['years']},
        'started': time.strftime('%Y-%m-%d %H:%M:%S'),
    }
    assert prov['first_part']['engine'] != prov['second_part']['engine'], 'not a different engine: use --resume'
    # 2. copy the checkpoint (the source directory is left untouched)
    out.mkdir(parents=True, exist_ok=False)
    for name in (save.name, state.name, f'seed_{a.seed}.json.gz', f'seed_{a.seed}.debug.json.gz', 'manifest.json'):
        if (src / name).exists():
            shutil.copy2(src / name, out / name)
    shutil.copytree(src / f'archive_{a.seed}', out / f'archive_{a.seed}')
    man = dict(src_manifest)
    man['commit'] = f"{meta['commit'][:7]} (seasons to {a.boundary}) + {head[:7]} (seasons from {a.boundary + 1})"
    man['mixed_version'] = prov
    (out / 'manifest.json').write_text(json.dumps(man, indent=1, default=str))
    (out / 'PROVENANCE.json').write_text(json.dumps(prov, indent=1))
    print(json.dumps(prov, indent=1), flush=True)
    # 3. continue: the save is read across engines explicitly (and only here), then the run goes on as usual
    real = SG.load_simulation
    SG.load_simulation = lambda p, allow_other_engine=False: real(p, allow_other_engine=True)
    LW.run_world(a.seed, a.years, a.workers, out, resume=True, save_every=1)
    prov['finished'] = time.strftime('%Y-%m-%d %H:%M:%S')
    (out / 'PROVENANCE.json').write_text(json.dumps(prov, indent=1))


if __name__ == '__main__':
    main()
