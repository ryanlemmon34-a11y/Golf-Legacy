"""Same-seed familiarity comparison on the exact candidate: one fresh full-population season with the regional
baseline (home-club floor included) switched OFF (Season.familiar_base_on = False), decision evidence off, through
the persistent session as the observer plays it. Compared with the final smoke's world_off (same seed, evidence off,
baseline ON): season time and every outcome part's digest.

    python fam_off.py <checkout> <out dir> <seed> <smoke.json of the same build and seed>
"""
import json
import sys
import time
from pathlib import Path

CHECKOUT, OUT, SEED, SMOKE = Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3]), Path(sys.argv[4])
sys.path[:0] = [str(CHECKOUT), str(CHECKOUT / 'tools')]
from golfsim.population import generate_world          # noqa: E402
from golfsim.session import Session                    # noqa: E402
import equivalence_check as EQ                          # noqa: E402


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    d = OUT / 'world_famoff'
    t0 = time.perf_counter()
    s = Session.create(d, seed=SEED, workers=2, world=generate_world(seed=SEED, scale=1.0))
    s.season.record_decisions = False
    s.season.familiar_base_on = False
    y = s.cursor['year']
    t = time.perf_counter()
    s.advance(52)
    secs = time.perf_counter() - t
    parts = {k: EQ.digest(v) for k, v in EQ.parts(s, d).items()}
    s.close()
    ref = json.loads(SMOKE.read_text())['off'][0]
    diff = sorted(k for k in parts if k != 'decision_evidence' and parts.get(k) != ref['parts'].get(k))
    res = {'seed': SEED, 'year': y, 'season_s_famoff': round(secs, 1), 'season_s_famon_smoke_off': ref['season_s'],
           'created_s': round(t - t0, 1), 'parts_differing': diff, 'parts': parts}
    (OUT / 'fam_off.json').write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != 'parts'}), flush=True)


if __name__ == '__main__':
    main()
