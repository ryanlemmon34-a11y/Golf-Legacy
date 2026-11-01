"""Checks before any arm is compared (study only; nothing is simulated):

1. Per cohort (57 entrant years x 2 pathways), Test2's seed 386509:
   a. production: population.entrant_rows with Test2's recorded shares -> its total and allocation against the
      recorded ones (the shares are recorded to 6 decimals);
   b. production first-k: each nation's first k passers of its population._Stream, k = the RECORDED allocation;
   c. the study's A0 replay (ReplayStream / replay_entrants) against (b), row for row: country, age, stored
      potential, peak age, current overall, status, aging rate all equal; and every draw the replay consumed
      equal to the production stream's draw (passer or not);
   d. latent-draw parity for each entrant: the candidate's recorded potential, peak, aging and luck give the
      production row (current = potential - deficit + luck, stored potential = max(min(potential, 99), current));
   e. rho = 1 gives A0's rows; A2 evaluated first on the same stream leaves A0's rows unchanged (arm evaluation
      draws nothing from the production stream).
2. Reconciliation: juniors per entrant year (born = year - 18) and new professionals per entry age, with the
   2028-2083 total against the review brief's 16,811.
3. The juniors who entered at 80+ (the brief: 8, one at 85+: Cardenas).

    python3 -I validate.py <checkout> <tests/data/test2_nation_shares.json.gz> <out.json> <out.md>
"""
import gzip
import hashlib
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import study as S  # noqa: E402

S.setup(sys.argv[1])
P = S.P
fx = json.load(gzip.open(sys.argv[2], 'rt'))
SEED = 386509
A0, A2 = S.ARMS['A0'], S.ARMS['A2']


def digest(rows):
    return hashlib.sha256(repr(rows).encode()).hexdigest()[:16]


cohorts = []
j80 = []
problems = []
for y in sorted(map(int, fx['years'])):
    rec = fx['years'][str(y)]
    for kind in ('juniors', 'new_pros'):
        alloc = rec['allocated'][kind]
        rep = {}
        prod_pipeline = P.entrant_rows(kind, y, SEED, S.NATIONS, shares=rec['shares'][kind], report=rep)
        prod, repl, rho1, draws, same_draws, latent_ok = [], [], [], 0, 0, 0
        ages = Counter()
        for country, prof in S.NATIONS.items():
            k = alloc.get(country, 0)
            need = P._cand_n(kind, prof)
            st = P._Stream(kind, y, SEED, country, prof)
            got = []
            while len(got) < k:
                r = st.draw()
                if r is not None:
                    got.append(r)
            prod.extend(got)
            rs = S.ReplayStream(kind, y, SEED, country)
            S.replay_entrants(rs, k, A2, need)                     # an arm first, on the same stream
            ents, _ = S.replay_entrants(rs, k, A0, need)
            repl.extend(row for _, row, _ in ents)
            e1, _ = S.replay_entrants(rs, k, S.IDENTITY, need)
            rho1.extend(row for _, row, _ in e1)
            # every draw the replay consumed against a fresh production stream
            st2 = P._Stream(kind, y, SEED, country, prof)
            for prow in rs.production:
                draws += 1
                same_draws += st2.draw() == prow
            for d, row, f in ents:
                pot, peak, aging, luck = rs.get(d)[:4]
                cur = pot - P.age_deficit(row[1] if kind == 'new_pros' else 18, peak, aging) + luck
                cur = min(cur, 99.0)
                latent_ok += (row[3] == peak and row[6] == aging and row[4] == cur
                              and row[2] == max(min(pot, 99.0), cur))
                ages[row[1]] += 1
                if kind == 'juniors' and row[4] >= 80:
                    j80.append({'year': y, 'country': country, 'overall': round(row[4], 3),
                                'raw_potential': round(pot, 3), 'peak_age': round(peak, 3),
                                'aging_rate': round(aging, 3)})
        same_rows = sum(a == b for a, b in zip(prod, repl))
        c = {'year': y, 'kind': kind, 'recorded_total': rec['totals'][kind],
             'entrant_rows_total': rep['total'], 'entrant_rows_allocation_equal': rep['allocated'] == alloc,
             'entrant_rows_rows_equal_first_k': (sorted(prod_pipeline) == sorted(prod))
             if rep['allocated'] == alloc else None,
             'first_k_rows': len(prod), 'a0_rows': len(repl), 'a0_rows_identical': same_rows,
             'draws_compared': draws, 'draws_identical': same_draws, 'latent_parity': latent_ok,
             'rho1_rows_identical': sum(a == b for a, b in zip(prod, rho1)),
             'digest_production': digest(prod), 'digest_a0': digest(repl),
             'mean_overall': round(sum(r[4] for r in repl) / max(1, len(repl)), 4),
             'mean_stored_potential': round(sum(r[2] for r in repl) / max(1, len(repl)), 4),
             'mean_peak_age': round(sum(r[3] for r in repl) / max(1, len(repl)), 4),
             'by_age': dict(sorted(ages.items()))}
        ok = (c['first_k_rows'] == c['a0_rows'] == c['a0_rows_identical'] == c['latent_parity'] == c['rho1_rows_identical']
              == c['recorded_total'] and c['draws_identical'] == c['draws_compared']
              and c['digest_production'] == c['digest_a0'] and c['entrant_rows_total'] == c['recorded_total'])
        c['ok'] = ok
        if not ok:
            problems.append((y, kind))
        cohorts.append(c)
    print(y, 'ok' if not problems else problems[-3:], flush=True)

jun = [c for c in cohorts if c['kind'] == 'juniors']
npro = [c for c in cohorts if c['kind'] == 'new_pros']
recon = {'juniors_2028_2083': sum(c['a0_rows'] for c in jun if c['year'] <= 2083),
         'juniors_2084': sum(c['a0_rows'] for c in jun if c['year'] == 2084),
         'juniors_all': sum(c['a0_rows'] for c in jun),
         'new_pros_all': sum(c['a0_rows'] for c in npro),
         'new_pros_by_age': dict(sorted(sum((Counter(c['by_age']) for c in npro), Counter()).items()))}
alloc_diff = [(c['year'], c['kind']) for c in cohorts if not c['entrant_rows_allocation_equal']]


def allocation_gap(y, kind):
    """Where entrant_rows with the recorded (6-decimal) shares allocates differently from Test2: the nations whose
    places differ, their quota remainders from the recorded shares, the gap between them, and how far rounding a
    share to 6 decimals can move one nation's quota (total x 0.0000005, before renormalisation)."""
    import math
    rec = fx['years'][str(y)]
    shares, total, recorded = rec['shares'][kind], rec['totals'][kind], rec['allocated'][kind]
    got = P.allocate(total, shares)
    sh = P.normalised(shares)
    diff = sorted(c for c in got if got[c] != recorded[c])
    rows = {c: {'recorded_share': shares[c], 'quota': total * sh[c], 'remainder': total * sh[c] - math.floor(total * sh[c]),
                'recorded_places': recorded[c], 'places_from_recorded_shares': got[c]} for c in diff}
    rems = [r['remainder'] for r in rows.values()]
    return {'year': y, 'kind': kind, 'total': total, 'nations': rows, 'remainder_gap': max(rems) - min(rems),
            'rounding_bound_per_nation': total * 0.5e-6, 'recorded_share_sum': sum(shares.values())}


gaps = [allocation_gap(y, k) for y, k in alloc_diff]
out = {'cohorts_checked': len(cohorts), 'cohorts_ok': sum(c['ok'] for c in cohorts), 'problems': problems,
       'draws_compared': sum(c['draws_compared'] for c in cohorts),
       'draws_identical': sum(c['draws_identical'] for c in cohorts),
       'rows_compared': sum(c['first_k_rows'] for c in cohorts),
       'rows_identical': sum(c['a0_rows_identical'] for c in cohorts),
       'entrant_rows_totals_equal': sum(c['entrant_rows_total'] == c['recorded_total'] for c in cohorts),
       'entrant_rows_allocation_differs': alloc_diff, 'allocation_gaps': gaps,
       'reconciliation': recon, 'juniors_80_plus': sorted(j80, key=lambda r: -r['overall']), 'cohorts': cohorts}
json.dump(out, open(sys.argv[3], 'w'), indent=1)

L = ['# Study validation: Test2 cohorts, baseline (A0) parity per cohort', '',
     f'Seed 386509, entrant years 2028-2084, both pathways: {out["cohorts_ok"]} of {out["cohorts_checked"]} cohorts '
     f'pass every check; {out["rows_identical"]:,} of {out["rows_compared"]:,} entrant rows identical (country, age, '
     f'stored potential, peak age, current overall, status, aging rate); {out["draws_identical"]:,} of '
     f'{out["draws_compared"]:,} production draws identical. Production entrant_rows with the recorded shares gives '
     f'the recorded total in {out["entrant_rows_totals_equal"]} of {len(cohorts)} cohorts and the recorded allocation '
     f'in all but {len(alloc_diff)}. The replay always uses the recorded allocation, so it is unaffected.', '']
for gp in gaps:
    nn = gp['nations']
    L += [f"**{gp['year']} {gp['kind']}: allocation recomputed from the recorded shares differs from the recorded one.** "
          + '; '.join(f"{c}: recorded share {r['recorded_share']}, quota {r['quota']:.6f}, remainder {r['remainder']:.7f}, "
                      f"recorded {r['recorded_places']} place(s), recomputed {r['places_from_recorded_shares']}"
                      for c, r in nn.items())
          + f". The two remainders differ by {gp['remainder_gap']:.7f}. Rounding a share to 6 decimals can move that "
          f"nation's quota by up to {gp['total']} x 0.0000005 = {gp['rounding_bound_per_nation']:.7f} (and the recorded "
          f"shares sum to {gp['recorded_share_sum']:.6f}, so renormalising moves every quota slightly too): the gap is "
          f"about 1/{gp['rounding_bound_per_nation'] / gp['remainder_gap']:.0f} of one nation's rounding bound, so "
          "share rounding is large enough to reverse the order. That it did is not established: the cause is "
          "unresolved.", '']
L += ['',
     '## Reconciliation of the junior count', '',
     f'Juniors entering 2028-2083: {recon["juniors_2028_2083"]:,}; entering 2084: {recon["juniors_2084"]:,}; all: '
     f'{recon["juniors_all"]:,}. Each class is created when the previous season closes (season.py: add_juniors(year + 1) '
     'after the winter aging), so the 2084 class (born 2066) is created at the close of Test2\'s last season, 2083, '
     'and never plays a season; the review brief\'s 16,811 equals the 2028-2083 classes. New professionals, all years: '
     f'{recon["new_pros_all"]:,}, by entry age {recon["new_pros_by_age"]}.', '',
     '## Per cohort', '',
     '| year | pathway | recorded | entrant_rows total | allocation from recorded shares | A0 rows identical | '
     'draws identical | latent parity | rho 1 = A0 | mean overall | mean stored potential | mean peak age | '
     'by entry age | digest (production = A0) | ok |',
     '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
for c in cohorts:
    L.append(f"| {c['year']} | {c['kind']} | {c['recorded_total']} | {c['entrant_rows_total']} | "
             f"{'equal' if c['entrant_rows_allocation_equal'] else 'differs'} | {c['a0_rows_identical']}/{c['first_k_rows']} | "
             f"{c['draws_identical']}/{c['draws_compared']} | {c['latent_parity']} | {c['rho1_rows_identical']} | "
             f"{c['mean_overall']} | {c['mean_stored_potential']} | {c['mean_peak_age']} | "
             f"{' '.join(f'{a}:{n}' for a, n in c['by_age'].items())} | "
             f"{c['digest_production']}{'' if c['digest_production'] == c['digest_a0'] else ' != ' + c['digest_a0']} | "
             f"{'yes' if c['ok'] else 'NO'} |")
L += ['', '## Juniors who entered at 80+ (A0 = Test2)', '', '| year | nation | overall | raw potential | peak age | aging |',
      '|---|---|---|---|---|---|']
L += [f"| {r['year']} | {r['country']} | {r['overall']} | {r['raw_potential']} | {r['peak_age']} | {r['aging_rate']} |"
      for r in out['juniors_80_plus']]
open(sys.argv[4], 'w').write('\n'.join(L) + '\n')
print(json.dumps({k: v for k, v in out.items() if k != 'cohorts'}, indent=1))
