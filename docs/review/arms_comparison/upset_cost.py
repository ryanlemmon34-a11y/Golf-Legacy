#!/usr/bin/env python3
"""Upset snapshot cost, read-only: bytes of each edition's archived `upset` record, and the CPU of recomputing the
stored estimates offline from their `inputs` snapshot (golfsim.upsets.reproduce).

    nice -n 19 ionice -c3 python3 -B upset_cost.py --arms a18new=DIR seed2=DIR --cpu a18new:2027,2036 --out upset_cost.json

Bytes: every season the archive MANIFEST names. JSON bytes are the archive's own encoding (json.dumps with
separators (',', ':'), golfsim/archive._write); gzip bytes compress the season's upset records alone (level 6, the
archive's level) -- an approximation of their contribution inside the whole-file compression.
CPU: process CPU time (time.process_time) of reproduce() per edition; only that call is timed. It is an offline
recomputation from stored inputs: it excludes the fact capture at field-set time and any engine-side bookkeeping,
so it is not the in-engine overhead.
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
import time
import zlib
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
V18 = HERE.parent


def jb(x):
    return json.dumps(x, separators=(',', ':')).encode()


def gz(b):
    return len(gzip.compress(b, compresslevel=6, mtime=0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--build', default=str(V18 / 'arms' / 'build_c0d1ea5'))
    ap.add_argument('--arms', nargs='*', default=[f'a18new={V18 / "arms" / "a18new"}', f'seed2={V18 / "arms" / "seed2"}'])
    ap.add_argument('--cpu', default='a18new:2027,2036', help='arm:year,year seasons to recompute (empty: none)')
    ap.add_argument('--out', default=str(HERE / 'upset_cost.json'))
    a = ap.parse_args()
    sys.path.insert(0, str(Path(a.build).resolve()))
    from golfsim import upsets as U
    cpu_arm, cpu_years = (a.cpu.split(':') + [''])[:2] if a.cpu else ('', '')
    cpu_years = {int(y) for y in cpu_years.split(',') if y}
    out = {'model': U.VERSION, 'arms': {}, 'cpu': []}
    for kv in a.arms:
        name, folder = kv.split('=', 1)
        folder = Path(folder)
        man = json.loads((folder / 'manifest.json').read_text())
        seed = next(iter(man.get('seeds') or {}), None)
        arch = next(folder.glob('world_*/archive'))
        m = json.loads((arch / 'MANIFEST.json').read_text())
        rows = []
        for y, f in sorted((int(y), f) for y, f in m['files']['years'].items()):
            p = arch / f
            gz_size = p.stat().st_size
            raw = gzip.decompress(p.read_bytes())
            d = json.loads(raw)
            ups = [e['upset'] for e in d['events'] if e.get('upset') is not None]
            inputs = [u['inputs'] for u in ups if u.get('inputs')]
            ub, ib = jb(ups), jb(inputs)
            r = {'year': y, 'file': f, 'editions': len(d['events']), 'with_upset': len(ups),
                 'estimated': sum(1 for u in ups if u.get('estimated')), 'file_raw': len(raw), 'file_gz': gz_size,
                 'upset_json': sum(len(jb(u)) for u in ups), 'inputs_json': sum(len(jb(i)) for i in inputs),
                 'upset_gz_alone': gz(ub), 'inputs_gz_alone': gz(ib)}
            rows.append(r)
            if name == cpu_arm and y in cpu_years:
                n = same = 0
                worst = 0.0
                cpu = []
                for e in d['events']:
                    u = e.get('upset')
                    if not u or not u.get('estimated') or not u.get('inputs'):
                        continue
                    t0 = time.process_time()
                    p_ = U.reproduce(u)
                    cpu.append(time.process_time() - t0)
                    n += 1
                    stored = {g: v for g, v in u.get('top', [])}
                    if u.get('winner') is not None and 'p' in u:
                        stored[u['winner']] = u['p']
                    if u.get('favourite') is not None:
                        stored[u['favourite']] = u['favourite_p']
                    ok = all(p_.get(int(g)) == v or p_.get(g) == v for g, v in stored.items())
                    same += ok
                    for g, v in stored.items():
                        worst = max(worst, abs((p_.get(int(g)) or p_.get(g) or 0) - v))
                cpu.sort()
                out['cpu'].append({'arm': name, 'year': y, 'editions': n, 'equal': same, 'max_abs_diff': worst,
                                   'cpu_total_s': round(sum(cpu), 3), 'cpu_per_edition_ms': round(1000 * sum(cpu) / n, 3) if n else None,
                                   'cpu_median_ms': round(1000 * cpu[n // 2], 3) if n else None,
                                   'cpu_max_ms': round(1000 * cpu[-1], 3) if n else None,
                                   'compared': 'top 5, favourite and winner chances as stored (6 significant figures)'})
                print(f'{name} {y}: reproduced {n}, equal {same}, CPU {sum(cpu):.2f} s', flush=True)
            del d, raw
            print(f'{name} {y}: {r["with_upset"]} upset records, {r["upset_json"] / 1e6:.2f} MB json', flush=True)
        out['arms'][name] = {'seed': seed, 'seasons': rows}
    Path(a.out).write_text(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
