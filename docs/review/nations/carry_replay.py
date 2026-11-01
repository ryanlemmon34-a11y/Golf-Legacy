"""Fixed-input replay of the cohort rounding on the Test2 world: the recorded shares and totals of 57 entrant seasons
held fixed, allocated year by year (before) and with each nation's fraction carried forward (rules 2026-11-13).

    python3 -I carry_replay.py <checkout> <tests/data/test2_nation_shares.json.gz>
"""
import gzip, json, sys
sys.path.insert(0, sys.argv[1])
from golfsim import population as P
d = json.load(gzip.open(sys.argv[2], 'rt'))
ys = sorted(d['years'], key=int)
tot_old, tot_new, cq = {}, {}, {}
worst_old = worst_new = (0.0, None)
for kind in ('juniors', 'new_pros'):
    carry, q, co, cn = {}, {}, {}, {}
    for y in ys:
        r = d['years'][y]
        t, sh = r['totals'][kind], P.normalised(r['shares'][kind])
        a_old = P.allocate(t, sh)
        a_new, carry = P.allocate_with_carry(t, sh, carry)
        for c in sh:
            q[c] = q.get(c, 0) + t * sh[c]
            co[c] = co.get(c, 0) + a_old[c]
            cn[c] = cn.get(c, 0) + a_new[c]
            worst_old = max(worst_old, (abs(q[c] - co[c]), (kind, c, y)))
            worst_new = max(worst_new, (abs(q[c] - cn[c]), (kind, c, y)))
    for c in q:
        tot_old[c] = tot_old.get(c, 0) + co[c]
        tot_new[c] = tot_new.get(c, 0) + cn[c]
        cq[c] = cq.get(c, 0) + q[c]
zero = sorted(c for c in cq if tot_old[c] == 0)
print(f'nations {len(cq)}; never given a newcomer: before {len(zero)} (entitled {sum(cq[c] for c in zero):.2f}), '
      f'after {sum(1 for c in cq if tot_new[c] == 0)}')
print(f'worst |cumulative quota - places|: before {worst_old[0]:.2f} {worst_old[1]}; after {worst_new[0]:.6f} {worst_new[1]}')
print('| nation | entitled (57 seasons, both pathways) | before | after |')
print('|---|---|---|---|')
for c in sorted(cq, key=lambda c: -abs(tot_new[c] - tot_old[c])):
    if tot_new[c] != tot_old[c]:
        print(f'| {c} | {cq[c]:.2f} | {tot_old[c]} | {tot_new[c]} |')
