"""Fresh full-population smoke on an exact candidate checkout: seasons played through the persistent session (as the
observer does), with the decision evidence on; a second fresh world of the same seed with the evidence off for the
first season. Reports per season: time, archived season-file size, the decision_evidence key's size (gzip), save
(checkpoint) size, the evidence bounds, and whether every outcome part matches with the evidence off.

    python full_pop_smoke.py <checkout> <out dir> <seed> <seasons>
"""
import gzip
import json
import os
import sys
import time
from pathlib import Path

CHECKOUT, OUT, SEED, SEASONS = Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
sys.path[:0] = [str(CHECKOUT), str(CHECKOUT / 'tools')]
from golfsim.population import generate_world          # noqa: E402
from golfsim.session import Session                    # noqa: E402
from golfsim.archive import read_manifest, _read       # noqa: E402
import equivalence_check as EQ                          # noqa: E402


def size(p):
    p = Path(p)
    return sum(f.stat().st_size for f in p.rglob('*') if f.is_file()) if p.is_dir() else p.stat().st_size


def season_file(d, y):
    a = d / 'archive'
    man = json.loads((a / 'MANIFEST.json').read_text())    # (read only: the published manifest names each file)
    f = man['files']['years'].get(str(y))
    return (a / f) if f else None


def evidence_stats(data):
    ev = data.get('decision_evidence')
    if not ev:
        return {'recorded': False}
    raw = json.dumps(ev, separators=(',', ':')).encode()
    sched = ev.get('schedule') or {}
    careers = ev.get('careers') or {}
    plans = [len(v.get('n', ())) for v in sched.values()]
    rows = [len(v) for v in careers.values()]
    return {'format': ev.get('format'), 'gzip_bytes': len(gzip.compress(raw, 6)), 'json_bytes': len(raw),
            'golfers_scheduled': len(plans), 'max_plans': max(plans or [0]),
            'over': sum(v.get('over', 0) for v in sched.values()),
            'mortality_deaths': len((ev.get('mortality') or {}).get('died') or {}),
            'career_people': len(rows), 'max_career_rows': max(rows or [0])}


def play(d, record, seasons, log):
    t0 = time.perf_counter()
    s = Session.create(d, seed=SEED, workers=2, world=generate_world(seed=SEED, scale=float(os.environ.get('SMOKE_SCALE', '1.0'))))
    s.season.record_decisions = record
    log(f'created {d.name}: {time.perf_counter() - t0:.0f} s, golfers {len(s.season.world.golfers)}')
    out = []
    for i in range(seasons):
        y = s.cursor['year']
        t = time.perf_counter()
        s.advance(52)
        secs = time.perf_counter() - t
        f = season_file(d, y)
        data = _read(f) if f else {}
        row = {'year': y, 'season_s': round(secs, 1), 'season_file_bytes': f.stat().st_size if f else None,
               'checkpoint_bytes': size(d / f'gen_{s.generation:06d}') if (d / f'gen_{s.generation:06d}').exists() else None,
               'archive_bytes': size(d / 'archive'), 'golfers': len(s.season.world.golfers),
               'evidence': evidence_stats(data)}
        if i == 0:
            row['parts'] = {k: EQ.digest(v) for k, v in EQ.parts(s, d).items()}
        out.append(row)
        log(json.dumps({k: v for k, v in row.items() if k != 'parts'}))
    s.close()
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    logf = open(OUT / 'smoke.log', 'a')

    def log(m):
        line = time.strftime('%H:%M:%S ') + m
        print(line, flush=True)
        logf.write(line + '\n')
        logf.flush()
    log(f'checkout {CHECKOUT} seed {SEED} seasons {SEASONS}; os.nice={os.nice(0)}')
    on = play(OUT / 'world_on', True, SEASONS, log)
    off = play(OUT / 'world_off', False, 1, log)
    a, b = on[0]['parts'], off[0]['parts']
    diff = sorted(k for k in a if k != 'decision_evidence' and a.get(k) != b.get(k))
    res = {'on': on, 'off': off, 'parts_differing_except_evidence': diff,
           'evidence_part_on_vs_off': [a.get('decision_evidence'), b.get('decision_evidence')]}
    (OUT / 'smoke.json').write_text(json.dumps(res, indent=1))
    log('outcome parts differing with the evidence off (should be none): ' + (', '.join(diff) or 'none'))


if __name__ == '__main__':
    main()
