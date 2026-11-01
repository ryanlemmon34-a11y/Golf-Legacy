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

Fail closed: the run exits 1, and the stamp says passed = false, unless every one of these holds (each is listed with
its result in the output): F1 exactly the 114 cohorts 2028-2084 x both pathways were checked; F2 every cohort passes
checks a-e; F3 juniors 2028-2083 = 16,811 and 2084 = 257; F4 juniors at 80+ = 8 and at 85+ = 1, the top one Cardenas
(2041, Argentina, 96.09, raw potential 100.881, peak 20.892, aging 0.718); F5 the cohorts where entrant_rows' allocation
from the recorded (6-decimal) shares differs from the recorded allocation are exactly the documented one, 2061 juniors
(that discrepancy is reported separately and does not affect the replay, which uses the recorded allocation; any new
or missing discrepancy fails); F6 not a negative-test run. The stamp (provenance.py) binds the result to study.py,
validate.py, the fixture and the golfsim sources; run.py and report.py refuse a missing, failed or stale stamp.

    python3 -I validate.py <checkout> <tests/data/test2_nation_shares.json.gz> <out.json> <out.md>
           [--stamp PATH] [--years FIRST-LAST] [--negative-baseline ARM]

--years and --negative-baseline exist for the negative tests (selftest.sh): a subset of years fails F1; a baseline
other than A0 (e.g. A1) must fail the parity checks; neither can ever produce a passing stamp.
"""
import argparse
import gzip
import hashlib
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import provenance as PV  # noqa: E402
import study as S  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('checkout')
ap.add_argument('fixture')
ap.add_argument('out_json')
ap.add_argument('out_md')
ap.add_argument('--stamp', default=PV.STAMP)
ap.add_argument('--years', default=None)
ap.add_argument('--negative-baseline', default=None)
args = ap.parse_args()

S.setup(args.checkout)
P = S.P
fx = json.load(gzip.open(args.fixture, 'rt'))
SEED = 386509
EXPECT = {'years': (2028, 2084), 'cohorts': 114, 'juniors_2028_2083': 16811, 'juniors_2084': 257, 'juniors_80_plus': 8,
          'juniors_85_plus': 1, 'top_junior': {'year': 2041, 'country': 'Argentina', 'overall': 96.09,
                                               'raw_potential': 100.881, 'peak_age': 20.892, 'aging_rate': 0.718},
          'known_allocation_discrepancies': [[2061, 'juniors']]}
A2 = S.ARMS['A2']
A0 = S.ARMS[args.negative_baseline] if args.negative_baseline else S.ARMS['A0']   # the baseline under test
YEARS = sorted(map(int, fx['years']))
if args.years:
    lo, hi = map(int, args.years.split('-'))
    YEARS = [y for y in YEARS if lo <= y <= hi]


def digest(rows):
    return hashlib.sha256(repr(rows).encode()).hexdigest()[:16]


cohorts = []
j80 = []
problems = []
for y in YEARS:
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

# ---- failure conditions (fail closed) ------------------------------------------------------------------------------
checks = []


def check(name, ok, detail):
    checks.append({'check': name, 'ok': bool(ok), 'detail': detail})


want_cohorts = {(y, k) for y in range(EXPECT['years'][0], EXPECT['years'][1] + 1) for k in ('juniors', 'new_pros')}
got_cohorts = {(c['year'], c['kind']) for c in cohorts}
check('F1 cohort boundary', got_cohorts == want_cohorts and len(cohorts) == EXPECT['cohorts'],
      f'{len(cohorts)} cohorts checked, {len(want_cohorts)} expected (2028-2084 x juniors, new professionals); '
      f'missing {sorted(want_cohorts - got_cohorts)[:4]}{"..." if len(want_cohorts - got_cohorts) > 4 else ""}')
check('F2 every cohort passes a-e', not problems and all(c['ok'] for c in cohorts),
      f'{sum(c["ok"] for c in cohorts)} of {len(cohorts)} pass; failing: {problems[:6]}')
check('F3 junior reconciliation', recon['juniors_2028_2083'] == EXPECT['juniors_2028_2083']
      and recon['juniors_2084'] == EXPECT['juniors_2084'],
      f'2028-2083 {recon["juniors_2028_2083"]} (expected {EXPECT["juniors_2028_2083"]}), 2084 {recon["juniors_2084"]} '
      f'(expected {EXPECT["juniors_2084"]})')
top = sorted(j80, key=lambda r: -r['overall'])
check('F4 tail counts and top junior', len(j80) == EXPECT['juniors_80_plus']
      and sum(r['overall'] >= 85 for r in j80) == EXPECT['juniors_85_plus'] and bool(top)
      and top[0] == EXPECT['top_junior'],
      f'80+: {len(j80)} (expected 8); 85+: {sum(r["overall"] >= 85 for r in j80)} (expected 1); top: '
      f'{top[0] if top else None}')
check('F5 allocation discrepancies are exactly the documented one', sorted(map(list, alloc_diff))
      == EXPECT['known_allocation_discrepancies'],
      f'found {sorted(map(list, alloc_diff))}, documented {EXPECT["known_allocation_discrepancies"]} (recorded shares '
      'are rounded to 6 decimals; the replay uses the recorded allocation)')
check('F6 not a negative-test run', not args.negative_baseline and not args.years,
      f'negative baseline {args.negative_baseline}, years {args.years}')
failures = [c['check'] + ': ' + c['detail'] for c in checks if not c['ok']]
out['checks'] = checks
out['passed'] = not failures
json.dump(out, open(args.out_json, 'w'), indent=1)
stamp = {'passed': not failures, 'failures': failures, 'bound': PV.bindings(args.checkout, args.fixture),
         'checks': [(c['check'], c['ok']) for c in checks], 'cohorts_ok': out['cohorts_ok'],
         'cohorts_checked': out['cohorts_checked']}
os.makedirs(os.path.dirname(os.path.abspath(args.stamp)), exist_ok=True)
json.dump(stamp, open(args.stamp, 'w'), indent=1)

L = ['# Study validation: Test2 cohorts, baseline (A0) parity per cohort', '',
     f"**Result: {'PASSED' if not failures else 'FAILED'}.** Stamp bound to study.py {stamp['bound']['study.py'][:12]}, "
     f"validate.py {stamp['bound']['validate.py'][:12]}, fixture {stamp['bound']['fixture'][:12]}, golfsim "
     f"{stamp['bound']['golfsim_digest'][:12]}.", '',
     '| failure condition | result | detail |', '|---|---|---|']
L += [f"| {c['check']} | {'ok' if c['ok'] else 'FAILED'} | {c['detail']} |" for c in checks]
L += ['',
     f'Seed 386509, entrant years {YEARS[0]}-{YEARS[-1]}, both pathways: {out["cohorts_ok"]} of {out["cohorts_checked"]} cohorts '
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
open(args.out_md, 'w').write('\n'.join(L) + '\n')
print(json.dumps({k: v for k, v in out.items() if k not in ('cohorts', 'juniors_80_plus', 'allocation_gaps')}, indent=1))
if failures:
    print('VALIDATION FAILED:', *failures, sep='\n  ', file=sys.stderr)
    sys.exit(1)
print('validation passed')
