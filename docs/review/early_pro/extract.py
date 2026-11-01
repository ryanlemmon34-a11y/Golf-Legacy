"""One read-only pass over the archived season files: compact facts for the early turn-pro analysis (analyse.py).
Usage: python3 -I extract.py test2_orig/archive facts.json.gz   (decodes each season file once; standard library only)

Kept per season: every college (CO_*) golfer's careers row fields the model and the money reconstruction need, their
decision-evidence week plans' funds column ('m') and amateur-support contract, every graduating turn_pro evaluation
of a college golfer, every major / Premier (tier 1) winner, every careers `exemption` field, and the college golfers'
winter transitions. Every archived turn_pro evaluation is also checked against the model as written in careers.py
(p from the terms, am_rank vs careers am_end, wins, age, standing): counts are kept under `check`."""
import gc
import gzip
import json
import math
import sys

arch, out_path = sys.argv[1], sys.argv[2]
man = json.load(open(f'{arch}/MANIFEST.json'))
people = json.load(gzip.open(f"{arch}/{man['files']['people']}"))
born = {int(k): v.get('born') for k, v in people.items() if 'golfer' in v}
created = {int(k): v.get('created') for k, v in people.items() if 'golfer' in v}
del people
gc.collect()

KEEP = ('tour', 'tier', 'status', 'lifestyle', 'events', 'wins', 'am_start', 'am_end', 'wr_end', 'net', 'net_at_decision',
        'income', 'costs', 'support', 'backer_support', 'moving', 'am_support', 'am_support_band', 'college', 'exemption',
        'next_tour', 'injury_weeks')


def sig(x):
    return 1 / (1 + math.exp(-x))


def standing(rank):
    if not rank:
        return 0.0
    return max(0.0, 1 - math.log10(rank) / math.log10(3000))


res = {'years': {}, 'born': {}, 'created': {}}
college_ids = set()
for y in man['years']:
    c = json.load(gzip.open(f"{arch}/{man['files']['years'][str(y)]}"))
    car = c['careers']
    de = c.get('decision_evidence') or {}
    defs = de.get('definitions', {}).get('careers', {}).get('models', {})
    sched = de.get('schedule', {})
    dcar = de.get('careers', {})
    yr = {'col': {}, 'sched': {}, 'amsup': {}, 'grad_ev': {}, 'ev_college_other': {}, 'exempt_field': {},
          'winners': [], 'trans': {}, 'check': {}, 'de_format': de.get('format')}
    for gid, r in car.items():
        if r.get('exemption'):
            yr['exempt_field'][gid] = r['exemption']
        if (r.get('tour') or '').startswith('CO_'):
            college_ids.add(int(gid))
            yr['col'][gid] = {k: r.get(k) for k in KEEP}
            if gid in sched:
                yr['sched'][gid] = {'w': sched[gid]['w'], 'm': sched[gid]['m']}
            a = c.get('amateur_support', {}).get(gid)
            if a is not None:
                yr['amsup'][gid] = {k: a.get(k) for k in ('band', 'cap', 'drawn', 'from', 'upgrades', 'ended')}
    # turn_pro evidence: graduates in full; every turn_pro row checked against the model and the careers row
    tspec = defs.get('turn_pro', {})
    terms, inputs = tspec.get('terms', []), tspec.get('inputs', [])
    chk = {'n': 0, 'p_mismatch': 0, 'rank_mismatch': 0, 'wins_mismatch': 0, 'age_mismatch': 0,
           'standing_mismatch': 0, 'college_nongrad': 0, 'max_dp': 0.0}
    for gid, rows in dcar.items():
        for row in rows:
            if row[0] != 'turn_pro':
                if gid in yr['col']:
                    yr['ev_college_other'].setdefault(gid, []).append(row[0])
                continue
            t = dict(zip(terms, row[4:4 + len(terms)]))
            i = dict(zip(inputs, row[4 + len(terms):]))
            chk['n'] += 1
            r = car.get(gid, {})
            x = sum(v for v in t.values() if v is not None)
            dp = abs(sig(x) - row[1])
            chk['max_dp'] = max(chk['max_dp'], dp)
            if dp > 0.01:
                chk['p_mismatch'] += 1
            if i.get('am_rank') != r.get('am_end'):
                chk['rank_mismatch'] += 1
            grad = bool(i.get('graduating'))
            if abs(t['wins'] - (0.3 if grad else 0.4) * min(2, r.get('wins') or 0)) > 0.006:
                chk['wins_mismatch'] += 1
            if i.get('age') != y - (born.get(int(gid)) or 0):
                chk['age_mismatch'] += 1
            if abs(t['standing'] - (3.0 if grad else 4.5) * standing(r.get('am_end'))) > 0.006:
                chk['standing_mismatch'] += 1
            if gid in yr['col']:
                if grad:
                    yr['grad_ev'][gid] = row
                else:
                    chk['college_nongrad'] += 1
    yr['check'] = chk
    for e in c['events']:
        if e.get('kind') == 'major' or e.get('tier') == 1:
            fin = e.get('finish') or []
            rows = sorted((x for site in fin for x in site), key=lambda x: (x[1] is None, x[1] or 0))
            w = next((x[0] for x in rows if x[1] == 1), None)
            yr['winners'].append([e['series'], e.get('kind'), e.get('tier'), w, e.get('name')])
    for t in c.get('transitions', []):
        if str(t.get('gid')) in yr['col']:
            yr['trans'].setdefault(t['kind'], []).append([t['gid'], t.get('age'), t.get('p'), t.get('am_rank'),
                                                          t.get('graduating')])
    res['years'][str(y)] = yr
    print(y, len(yr['col']), len(yr['grad_ev']), chk, flush=True)
    del c, car, de, sched, dcar
    gc.collect()
res['born'] = {str(g): born.get(g) for g in sorted(college_ids)}
res['created'] = {str(g): created.get(g) for g in sorted(college_ids)}
with (gzip.open(out_path, 'wt') if out_path.endswith('.gz') else open(out_path, 'w')) as f:
    json.dump(res, f, separators=(',', ':'))
