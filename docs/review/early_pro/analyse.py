"""Early turn-pro evaluation for college amateurs under 22: gates A, B and B' scored with the existing
non-graduating model, from the archived (fixed) inputs. No world is replayed.

Usage (any folder):  python3 -I analyse.py facts.json.gz results.json per_winter.csv
facts.json.gz is written by extract.py from the archive in test2_orig/ (python3 -I extract.py test2_orig/archive
facts.json.gz). Standard library only.

Two kinds of total are reported, and they are not the same thing:
  expected decision-events  the sum of p over every golfer-winter the gate evaluates. A golfer who left early would
                            not be evaluated again, so repeated golfer-winters overcount real departures.
  expected unique exits     survival-weighted per golfer: over the winters a gate evaluates them, in order,
                            exit at winter t = p_t * prod_{s<t}(1 - p_s); P(leave early at all) = 1 - prod(1 - p_t).
Both keep every input as archived: an early exit would also change the golfer's later amateur ranking and other
golfers' rankings and fields, so the survival-weighted figure is still a fixed-input approximation."""
import csv
import gzip
import json
import math
import re
import statistics as S
import sys
from collections import defaultdict

facts_path, out_path, csv_path = sys.argv[1], sys.argv[2], sys.argv[3]
F = json.load(gzip.open(facts_path) if facts_path.endswith('.gz') else open(facts_path))
Y = F['years']
born = {int(k): v for k, v in F['born'].items()}
years = sorted(int(y) for y in Y)
WINTERS = [y for y in years if 2027 <= y <= 2082]
BANDS = {'A': 25000.0, 'B': 12000.0, 'C': 5000.0}
GATES = {'A': 'A', 'B': 'B', 'B2': "B'"}          # internal key -> label
OUT_KEY = {'A': 'A', 'B': 'B', 'B2': 'B_prime'}


def sig(x):
    return 1 / (1 + math.exp(-x))


def standing(rank):                                 # careers.amateur_standing
    if not rank:
        return 0.0
    return max(0.0, 1 - math.log10(rank) / math.log10(3000))


# ---- exemptions held next season, from the editions (cards.winner_exemptions(season, Y + 1)) ----------------
winners = {y: Y[str(y)]['winners'] for y in years}


def exempt_next(Y0):
    """{gid: why}: a major won in Y0-4..Y0, a Premier (tier 1) event won in Y0-1..Y0 (a later major's reason
    replaces an earlier one; a Premier event's never replaces a major's)."""
    out = {}
    for y in sorted(winners):
        if y > Y0 or y < Y0 + 1 - 5:
            continue
        for sid, kind, tier, w, name in winners[y]:
            if w is None:
                continue
            if kind == 'major':
                out[w] = f'won the {y} {name}'
            elif tier == 1 and y >= Y0 + 1 - 2 and w not in out:
                out[w] = f'won the {y} {name}'
    return out


EX = {y: exempt_next(y) for y in WINTERS}

# cross-check: the next season's careers `exemption` (season.earned: held in Y+1, in-season wins of Y+1 included;
# compared only where its reason names a season <= Y)
xc = {'agree': 0, 'archive_field_only': 0, 'editions_only': 0, 'editions_only_cases': []}
for y in WINTERS:
    fld = Y[str(y + 1)]['exempt_field'] if str(y + 1) in Y else {}
    for gid in Y[str(y)]['col']:
        a = EX[y].get(int(gid))
        raw = b = fld.get(gid)
        if b is not None:
            m = re.search(r'won the (\d{4})', b)
            if m and int(m.group(1)) > y:
                b = None
        if a and b:
            xc['agree'] += 1
        elif b:
            xc['archive_field_only'] += 1
        elif a:
            xc['editions_only'] += 1
            xc['editions_only_cases'].append([y, int(gid), a, raw])

# ---- per golfer: seasons, ledger flows, anchors ---------------------------------------------------------------
seasons = defaultdict(dict)
for y in years:
    for gid, r in Y[str(y)]['col'].items():
        seasons[int(gid)][y] = r


def flow(r):
    """Change in W = cash + family money from 1 January to the winter decision. Every cash change goes through
    Season.earn/spend (the ledger); family `support` and backers' `backer_support` are transfers into cash, so they
    are taken out; amateur support is in kind and nets to zero inside `net`."""
    return (r['net_at_decision'] or 0) - (r['support'] or 0) - (r['backer_support'] or 0)


def winter_flow(r):
    """Winter expenses after the decision (a move): settled net minus the net the decision saw."""
    return (r['net'] or 0) - (r['net_at_decision'] or 0)


grad = {}          # gid -> (year, means, will, p) from the archived graduating turn_pro evaluation (age 22)
for y in years:
    for gid, row in Y[str(y)]['grad_ev'].items():   # row: model, p, u, outcome, base, standing, means, will, wins, age, ...
        grad[int(gid)] = (y, row[4 + 2] / 0.6, row[4 + 3] + 0.5, row[1])
WILLS = sorted(w for _, _, w, _ in grad.values())

# exact W at each winter, backward from an unclipped graduation means term; bounds from a clipped one
W_exact, bounds = {}, {}
for gid, (yg, means, will, p) in grad.items():
    ss = seasons[gid]
    if yg not in ss:
        continue
    term = round(means * 0.6, 2)
    if 0 < term < 1.2:
        W = means * 40000
        W_exact[(gid, yg)] = W
        y = yg
        while (y - 1) in ss:
            W = W - flow(ss[y]) - winter_flow(ss[y - 1])
            y -= 1
            W_exact[(gid, y)] = W
    else:                                            # term 0: W <= 0 at 22; term 1.2: W >= $80k (+-$400 rounding)
        lo, hi = (80000 - 400, math.inf) if term >= 1.2 else (-math.inf, 400)
        y = yg
        bounds[(gid, y)] = (lo, hi)
        while (y - 1) in ss:
            d = flow(ss[y]) + winter_flow(ss[y - 1])
            lo, hi = lo - d, hi - d
            y -= 1
            bounds[(gid, y)] = (lo, hi)


def as_left_wk1(gid, y):
    """Amateur-support budget open at the week-1 plan (amateur_support.left), from the season's contract."""
    a = Y[str(y)]['amsup'].get(str(gid))
    if not a or a.get('from') != [y, 1]:
        return 0.0
    ups = a.get('upgrades') or []
    if not ups:
        return BANDS[a['band']]
    return BANDS['C'] if ups[0][2] == 'B' else (BANDS['B'] + BANDS['C']) / 2   # band before the first upgrade


def credit(gid, y):                                  # finance.credit_limit on last season's earned income
    prev = seasons[gid].get(y - 1)
    if prev is None or prev.get('income') is None:
        return 8000.0
    earned = (prev['income'] or 0) - (prev['support'] or 0) - (prev['backer_support'] or 0) - (prev['am_support'] or 0)
    return min(60000.0, 8000 + 0.25 * max(0.0, earned))


def W_forward_raw(gid, y):
    """W at the decision from the planner's week-1 funds (decision evidence schedule 'm': Season.spendable in $1000s,
    two figures = W + credit line - 4 weeks' committed costs - reserved + amateur support left), plus the ledger flow."""
    s = Y[str(y)]['sched'].get(str(gid))
    if not s or s['w'] != 1 or not s['m'] or s['m'][0] is None:
        return None
    return 1000 * s['m'][0] - credit(gid, y) - as_left_wk1(gid, y) + flow(seasons[gid][y])


def q(v, f):
    v = sorted(v)
    if not v:
        return None
    k = (len(v) - 1) * f
    lo, hi = math.floor(k), math.ceil(k)
    return v[lo] + (v[hi] - v[lo]) * (k - lo)


resid = [W_forward_raw(g, y) - W for (g, y), W in W_exact.items() if W_forward_raw(g, y) is not None]
resid_med = S.median(resid)


def W_at(gid, y):
    """(W, source) at the winter decision of season y."""
    if (gid, y) in W_exact:
        return W_exact[(gid, y)], 'exact'
    f = W_forward_raw(gid, y)
    lo, hi = bounds.get((gid, y), (-math.inf, math.inf))
    if f is not None:
        f -= resid_med
        return min(max(f, lo), hi), ('forward+bound' if (gid, y) in bounds else 'forward')
    if (gid, y) in bounds:
        return (lo if lo > -math.inf else hi), 'bound only'
    return None, 'none'


def means_of(W):
    return min(2.0, max(0.0, W) / 40000)


def p_of(r, shift=0.0, will_fixed=None):
    """p_turn_pro(graduating=False) for one golfer-winter; `shift` moves a non-exact W (sensitivity)."""
    W = r['W'] if r['W'] is not None else 0.0
    if r['msrc'] != 'exact':
        W += shift
    x0 = (-5.0 + 4.5 * standing(r['rank']) + 0.6 * means_of(W) + 0.4 * min(2, r['wins'])
          - 0.15 * abs(r['age'] - 21))
    if r['will'] is not None:
        return sig(x0 + r['will'] - 0.5)
    if will_fixed is not None:
        return sig(x0 + will_fixed - 0.5)
    return sum(sig(x0 + w - 0.5) for w in WILLS) / len(WILLS)     # integrated over the graduates' willingness


# ---- every college amateur under 22 at each winter ----------------------------------------------------------------
rows = []
for y in WINTERS:
    for gid_s, r in Y[str(y)]['col'].items():
        gid = int(gid_s)
        age = y - born[gid]
        if r['status'] != 'amateur' or r['lifestyle'] == 'retired' or age >= 22:
            continue
        W, src = W_at(gid, y)
        rank = r['am_end']
        ex = EX[y].get(gid)
        row = {'y': y, 'gid': gid, 'age': age, 'rank': rank, 'wins': r['wins'] or 0, 'W': W, 'msrc': src,
               'will': grad[gid][2] if gid in grad else None, 'ex': ex, 'tour': r['tour'],
               'A': True, 'B': bool(ex) or (rank is not None and rank <= 15),
               'B2': bool(ex) or (rank is not None and rank <= 60)}
        row['wsrc'] = 'graduation evidence' if row['will'] is not None else 'graduates average'
        row['means'] = means_of(W) if W is not None else None
        row['p'] = p_of(row)
        rows.append(row)


def band(rank):
    if rank is None:
        return 'unranked'
    return '1-15' if rank <= 15 else '16-60' if rank <= 60 else '61-300' if rank <= 300 else '301+'


# what each golfer actually did at 22
fate = {}
for y in years:
    for kind, lst in Y[str(y)]['trans'].items():
        for gid, age, p, rank, g in lst:
            if kind == 'turned pro' and g:
                fate[gid] = 'turned pro at 22'
            elif kind == 'college to amateur':
                fate[gid] = 'stayed amateur at 22'
FATES = ('turned pro at 22', 'stayed amateur at 22', 'still in college when the archive ends')


def survival(sel):
    """Per golfer, in winter order: S_t = prod_{s<t}(1 - p_s); exit_t = p_t * S_t."""
    by_g = defaultdict(list)
    for r in sel:
        by_g[r['gid']].append(r)
    for v in by_g.values():
        v.sort(key=lambda r: r['y'])
        s = 1.0
        for r in v:
            r['_S'], r['_exit'] = s, r['p'] * s
            s *= 1 - r['p']
    return by_g


def mmm(v, years_=None):
    d = {'mean': S.mean(v), 'min': min(v), 'max': max(v)}
    if years_:
        d['min_winter'], d['max_winter'] = years_[v.index(min(v))], years_[v.index(max(v))]
    return d


out = {'definitions': {
    'expected_decision_events': 'sum of p over every golfer-winter the gate evaluates (a golfer evaluated in several '
                                'winters counts in each: overcounts departures, since an early exit ends later evaluations)',
    'expected_unique_exits': 'survival-weighted per golfer: exit at winter t = p_t * prod_{s<t}(1 - p_s); total = '
                             'sum over golfers of 1 - prod(1 - p_t)',
    'evaluated_survival_weighted': 'sum over golfer-winters of prod_{s<t}(1 - p_s): golfer-winters still in college to be '
                                   'evaluated after earlier expected exits',
    'caveat': 'fixed inputs: every input is as archived; a real early exit would also change the golfer\'s later amateur '
              'ranking and other golfers\' rankings and fields, and every later season'},
       'model_check': {y: Y[str(y)]['check'] for y in map(str, years)},
       'exemption_cross_check': xc}
mc = out['model_check'].values()
out['model_check_summary'] = {'turn_pro_evaluations_checked': sum(c['n'] for c in mc),
                              'max_abs_dp': max(c['max_dp'] for c in mc),
                              **{k: sum(c[k] for c in mc) for k in ('p_mismatch', 'rank_mismatch', 'wins_mismatch',
                                                                     'age_mismatch', 'standing_mismatch')}}
src = defaultdict(int)
for r in rows:
    src[r['msrc']] += 1
out['reconstruction'] = {
    'golfer_winters': len(rows), 'golfers': len({r['gid'] for r in rows}),
    'money_sources': dict(src), 'money_exact_share': src['exact'] / len(rows),
    'forward_proxy_error_vs_exact': {'n': len(resid), 'median_error': resid_med,
                                     'median_abs_error_after_bias': q([abs(r - resid_med) for r in resid], .5),
                                     'p90_abs_error_after_bias': q([abs(r - resid_med) for r in resid], .9)},
    'graduation_means_terms': {'unclipped': sum(1 for g in grad.values() if 0 < round(g[1] * 0.6, 2) < 1.2),
                               'zero': sum(1 for g in grad.values() if round(g[1] * 0.6, 2) <= 0),
                               'capped': sum(1 for g in grad.values() if round(g[1] * 0.6, 2) >= 1.2)},
    'willingness_sources': {k: sum(1 for r in rows if r['wsrc'] == k) for k in ('graduation evidence', 'graduates average')},
    'graduates_willingness': {'n': len(WILLS), 'mean': S.mean(WILLS), 'p10': q(WILLS, .1), 'p90': q(WILLS, .9)}}

csv_rows = []
for gate, label in GATES.items():
    sel = [r for r in rows if r[gate]]
    by_g = survival(sel)
    ps = [r['p'] for r in sel]
    per_n = [sum(1 for r in sel if r['y'] == y) for y in WINTERS]
    per_e = [sum(r['p'] for r in sel if r['y'] == y) for y in WINTERS]
    per_u = [sum(r['_exit'] for r in sel if r['y'] == y) for y in WINTERS]
    per_s = [sum(r['_S'] for r in sel if r['y'] == y) for y in WINTERS]
    unique = sum(1 - math.prod(1 - r['p'] for r in v) for v in by_g.values())
    by_fate = defaultdict(float)
    for gid, v in by_g.items():
        by_fate[fate.get(gid, FATES[2])] += 1 - math.prod(1 - r['p'] for r in v)
    sens = {'base': sum(ps)}
    for name, kw in (('nonexact_W_minus_5000', {'shift': -5000}), ('nonexact_W_plus_5000', {'shift': 5000}),
                     ('graduates_average_will_as_0.5', {'will_fixed': 0.5})):
        alt = [dict(r, p=p_of(r, **kw)) for r in sel]
        sens[name] = {'decision_events': sum(r['p'] for r in alt),
                      'unique_exits': sum(1 - math.prod(1 - r['p'] for r in v)
                                          for v in survival(alt).values())}
    sens['base'] = {'decision_events': sum(ps), 'unique_exits': unique}
    out[OUT_KEY[gate]] = {
        'label': label,
        'evaluated_per_winter': mmm(per_n), 'golfer_winters_evaluated': len(sel), 'golfers': len(by_g),
        'golfer_winters_evaluated_survival_weighted': sum(per_s),
        'evaluated_survival_weighted_per_winter': mmm(per_s),
        'expected_decision_events_total': sum(per_e),
        'expected_decision_events_per_winter': mmm(per_e, WINTERS),
        'expected_unique_exits_total': unique,
        'expected_unique_exits_per_winter': mmm(per_u, WINTERS),
        'unique_exits_by_age_at_exit': {a: sum(r['_exit'] for r in sel if r['age'] == a) for a in (18, 19, 20, 21)},
        'unique_exits_by_rank_band_at_exit': {b: sum(r['_exit'] for r in sel if band(r['rank']) == b)
                                              for b in ('1-15', '16-60', '61-300', '301+', 'unranked')},
        'unique_exits_by_what_they_did_at_22': {f: by_fate.get(f, 0.0) for f in FATES},
        'decision_events_by_age': {a: {'evaluated': sum(1 for r in sel if r['age'] == a),
                                       'expected_decision_events': sum(r['p'] for r in sel if r['age'] == a)}
                                   for a in (18, 19, 20, 21)},
        'decision_events_by_rank_band': {b: {'evaluated': sum(1 for r in sel if band(r['rank']) == b),
                                             'expected_decision_events': sum(r['p'] for r in sel if band(r['rank']) == b)}
                                         for b in ('1-15', '16-60', '61-300', '301+', 'unranked')},
        'p_among_evaluated': {'median': q(ps, .5), 'p90': q(ps, .9), 'max': max(ps), 'mean': S.mean(ps),
                              'n_p_ge_0.5': sum(1 for p in ps if p >= 0.5), 'n_p_ge_0.2': sum(1 for p in ps if p >= 0.2)},
        'via_exemption': {'golfer_winters': sum(1 for r in sel if r['ex']),
                          'golfers': len({r['gid'] for r in sel if r['ex']}),
                          'with_rank_above_15': sum(1 for r in sel if r['ex'] and (r['rank'] is None or r['rank'] > 15)),
                          'expected_decision_events': sum(r['p'] for r in sel if r['ex'])},
        'share_of_decision_events_from_rank_le_15_or_exempt': sum(r['p'] for r in sel if r['B']) / sum(ps),
        'sensitivity': sens}
    for y, n, s_, e, u in zip(WINTERS, per_n, per_s, per_e, per_u):
        csv_rows.append([y, label, n, round(s_, 3), round(e, 4), round(u, 4)])

real, grads = [], []
for y in WINTERS:
    t = Y[str(y)]['trans']
    tp = [x for x in t.get('turned pro', []) if x[4]]
    real.append(len(tp))
    grads.append(len(tp) + len(t.get('college to amateur', [])))
out['realised_at_graduation'] = {'turned_pro_at_22': {**mmm(real), 'total': sum(real)},
                                 'all_graduates': {**mmm(grads), 'total': sum(grads)},
                                 'per_winter': {y: {'turned_pro': a, 'graduates': b} for y, a, b in zip(WINTERS, real, grads)}}

# Cardenas (id 19411)
cid = 19411
card = {'gid': cid, 'born': born[cid], 'willingness': grad[cid][2], 'winters': []}
for y in range(2041, 2046):
    r = seasons[cid].get(y)
    W, srcW = W_at(cid, y)
    rr = next((x for x in rows if x['gid'] == cid and x['y'] == y), None)
    card['winters'].append({'winter': y, 'age': y - born[cid], 'tour': r['tour'], 'am_end': r['am_end'], 'wins': r['wins'],
                            'W': W, 'W_source': srcW, 'means': means_of(W), 'ledger_flow': flow(r),
                            'week1_funds_k': (Y[str(y)]['sched'].get(str(cid)) or {}).get('m', [None])[0],
                            'exemption_next_season': EX.get(y, {}).get(cid),
                            'p_early': rr['p'] if rr else None, 'in_A': bool(rr), 'in_B': rr['B'] if rr else None,
                            'in_B_prime': rr['B2'] if rr else None,
                            'archived_graduation_evaluation': Y[str(y)]['grad_ev'].get(str(cid))})
for gate in GATES:
    v = [r for r in rows if r['gid'] == cid and r[gate]]
    surv = 1.0
    exits = {}
    for r in sorted(v, key=lambda r: r['y']):
        exits[r['y']] = r['p'] * surv
        surv *= 1 - r['p']
    card[f'p_leave_before_22_{OUT_KEY[gate]}'] = 1 - surv
    card[f'exit_by_winter_{OUT_KEY[gate]}'] = exits
out['cardenas'] = card
out['top_golfer_winters'] = sorted(({k: r[k] for k in ('y', 'gid', 'age', 'rank', 'wins', 'means', 'msrc', 'will', 'p', 'ex')}
                                    for r in rows), key=lambda r: -r['p'])[:25]

json.dump(out, open(out_path, 'w'), indent=1, default=str)
with open(csv_path, 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['winter', 'gate', 'evaluated', 'evaluated_survival_weighted', 'expected_decision_events',
                'expected_unique_exits_survival_weighted'])
    w.writerows(csv_rows)
summary = {k: {kk: out[k][kk] for kk in ('evaluated_per_winter', 'golfer_winters_evaluated',
                                          'golfer_winters_evaluated_survival_weighted', 'expected_decision_events_total',
                                          'expected_decision_events_per_winter', 'expected_unique_exits_total',
                                          'expected_unique_exits_per_winter', 'unique_exits_by_age_at_exit',
                                          'unique_exits_by_what_they_did_at_22', 'sensitivity')}
           for k in OUT_KEY.values()}
print(json.dumps({'summary': summary, 'reconstruction': out['reconstruction'], 'model_check': out['model_check_summary'],
                  'exemptions': {k: v for k, v in xc.items()}, 'realised': {k: v for k, v in out['realised_at_graduation'].items()
                                                                              if k != 'per_winter'},
                  'cardenas': card}, indent=1, default=str))
