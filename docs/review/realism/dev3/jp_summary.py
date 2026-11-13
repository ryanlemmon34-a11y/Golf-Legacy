import json, statistics as st, sys
d = json.load(open(sys.argv[1]))
cl = d['classes']
print('classes', len(cl), 'identical golfers/paths in all:', all(c[3] for c in cl), 'juniors', sum(c[2] for c in cl),
      'juniors whose attributes changed', sum(c[4] for c in cl))
def stats(recs, r):
    out = {}
    pk = [max(x[r]['traj']) for x in recs]
    out['entry'] = st.median(x[r]['entry'] for x in recs)
    out['headroom'] = st.median(x[r]['pot'] - x[r]['entry'] for x in recs)
    out['peak'] = st.median(pk)
    out['age_peak'] = st.median(18 + x[r]['traj'].index(max(x[r]['traj'])) for x in recs)
    out['yrs90'] = st.mean(sum(v >= 90 for v in x[r]['traj']) for x in recs)
    out['at40'] = st.median(x[r]['traj'][22] for x in recs)
    out['at45'] = st.median(x[r]['traj'][27] for x in recs)
    out['ceil99'] = st.mean(x[r]['ceil99'] for x in recs)
    return {k: round(v, 2) for k, v in out.items()}
E = d['elite']
for lo, hi in ((84, 87), (87, 89), (89, 92), (92, 100)):
    recs = [x for x in E if lo <= x['dev-2']['pot'] < hi]
    if recs:
        print(f'dev-2 potential {lo}-{hi}: n={len(recs)}')
        for r in ('dev-2', 'dev-3'):
            print('  ', r, stats(recs, r))
print('\ntop 8 by dev-2 potential (projection, fixed schedule):')
for x in sorted(E, key=lambda x: -x['dev-2']['pot'])[:8]:
    a, b = x['dev-2'], x['dev-3']
    print(f"  seed {x['seed']} {x['year']} pot {a['pot']}->{b['pot']} entry {a['entry']}->{b['entry']} "
          f"at19 {a['traj'][1]}->{b['traj'][1]} peak {max(a['traj'])}->{max(b['traj'])} "
          f"at40 {a['traj'][22]}->{b['traj'][22]} at45 {a['traj'][27]}->{b['traj'][27]} ceil99 {a['ceil99']}->{b['ceil99']} attr99@50 {a['attr99_50']}->{b['attr99_50']}")
# first-season entry tops per class
tops2 = sorted((c[5][0] for c in cl), reverse=True)[:5]; tops3 = sorted((c[6][0] for c in cl), reverse=True)[:5]
print('\nbest entry ratings over all classes dev-2', tops2, 'dev-3', tops3)
