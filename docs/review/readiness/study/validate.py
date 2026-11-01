"""Checks before any arm is compared (study only):

1. the study's draw functions under A0 are the production draws: every row of population._Stream equals the
   replay's, draw for draw, for every nation, both pathways and several years (and rho = 1 equals A0);
2. A0 replays Test2's 57 cohorts: each nation's first k passers (k as recorded), totals as recorded, and the
   Test2 facts from the review brief (16,811 juniors; 8 entered at 80+; one at 85+ -- Cardenas, overall 96.09,
   raw potential 100.881, peak age 20.892, aging rate 0.718).

    python3 -I validate.py <checkout> <tests/data/test2_nation_shares.json.gz> <out.json>
"""
import gzip
import json
import sys

sys.path.insert(0, sys.argv[0].rsplit('/', 1)[0] if '/' in sys.argv[0] else '.')
import study as S  # noqa: E402

S.setup(sys.argv[1])
P = S.P
fx = json.load(gzip.open(sys.argv[2], 'rt'))
SEED = 386509
out = {}

# 1. draw for draw
n_rows = mism = 0
for kind in ('juniors', 'new_pros'):
    for year in (2028, 2050, 2084):
        for country, prof in S.NATIONS.items():
            st = P._Stream(kind, year, SEED, country, prof)
            n = P._cand_n(kind, prof)
            prod = [st.draw() for _ in range(n)]
            for arm in (S.ARMS['A0'], S.IDENTITY):
                import random
                tag = 'juniors' if kind == 'juniors' else 'new-pros'
                crng = random.Random(f'{SEED}:{tag}:{year}:{country}')
                rr = random.Random(f'{SEED}:readiness:{tag}:{year}:{country}')
                for want in prod:
                    if kind == 'juniors':
                        got, _ = S.junior_draw(crng, rr, country, P._mu(prof), arm)
                    else:
                        got, _ = S.new_pro_draw(crng, rr, country, P._mu(prof), prof, arm)
                    n_rows += 1
                    mism += got != want
out['draw_identity'] = {'draws_compared': n_rows, 'mismatches': mism}
print('draw identity', out['draw_identity'], flush=True)

# 2. Test2's cohorts under A0
A0 = S.ARMS['A0']
tot = {'juniors': 0, 'new_pros': 0}
bad_totals = []
j80 = []
for y in sorted(fx['years'], key=int):
    rec = fx['years'][y]
    for kind in ('juniors', 'new_pros'):
        alloc = rec['allocated'][kind]
        if sum(alloc.values()) != rec['totals'][kind]:
            bad_totals.append((y, kind))
        for country, k in alloc.items():
            if not k:
                continue
            rows, _ = S.replay_cohort(kind, int(y), SEED, country, k, A0)
            if len(rows) != k:
                bad_totals.append((y, kind, country))
            tot[kind] += len(rows)
            if kind == 'juniors':
                for row, f in rows:
                    if row[4] >= 80:
                        j80.append({'year': int(y), 'country': country, 'overall': round(row[4], 3),
                                    'raw_potential': round(f['pot'], 3), 'peak_age': round(f['peak'], 3),
                                    'aging_rate': round(f['aging'], 3)})
out['test2_replay'] = {'juniors': tot['juniors'], 'new_pros': tot['new_pros'], 'allocation_mismatches': bad_totals,
                       'juniors_80_plus': sorted(j80, key=lambda r: -r['overall'])}
print(json.dumps(out['test2_replay'], indent=1))
json.dump(out, open(sys.argv[3], 'w'), indent=1)
