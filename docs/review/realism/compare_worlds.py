"""Full-scale world comparison for realism pass 1 (PLAN.md, acceptance 3) and the item-4 access diagnostic.

Reads tools/long_world.py outputs (seed_<s>.json.gz, seed_<s>.debug.json.gz) of two runs with the same seed: main
18a8e23 (dev-1) and this branch (dev-2). Realized careers: access, money, injuries, coaching and retirement all apply.
Usage: python compare_worlds.py MAIN_DIR BRANCH_DIR SEED [--log-main F --log-branch F] > OUT.md
"""
from __future__ import annotations

import argparse
import gzip
import json
import re
import statistics as S
from collections import Counter, defaultdict
from pathlib import Path

I_STATUS, I_LIFE, I_TIER, I_EVENTS, I_WINS, I_WBT, I_MAJORS, I_TOP10, I_WR, I_INJ = 0, 1, 2, 4, 5, 6, 7, 8, 13, 15


def load(d, seed):
    d = Path(d)
    with gzip.open(d / f'seed_{seed}.json.gz', 'rt') as f:
        data = json.load(f)
    with gzip.open(d / f'seed_{seed}.debug.json.gz', 'rt') as f:
        debug = json.load(f)
    return data, debug


def q(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, max(0, int(round(p * (len(xs) - 1)))))] if xs else float('nan')


def season_times(log):
    if not log or not Path(log).exists():
        return []
    t = [int(m.group(1)) for m in re.finditer(r'done \(\d+/\d+\).*?, (\d+) s', Path(log).read_text())]
    return [b - a for a, b in zip([0] + t, t)]


def table(rows, head):
    out = ['| ' + ' | '.join(head) + ' |', '|' + '---|' * len(head)]
    out += ['| ' + ' | '.join(str(c) for c in r) + ' |' for r in rows]
    return '\n'.join(out)


def analyse(data, debug):
    years = sorted(int(y) for y in data['rows'])
    gol = data['golfers']
    born = {int(k): v['born'] for k, v in gol.items()}
    created = {int(k): v['created'] for k, v in gol.items()}
    initial = {int(k): v['initial'] for k, v in gol.items()}
    ov = defaultdict(dict)                                  # gid -> year -> overall
    rows = defaultdict(dict)
    for y in years:
        for gid, r in data['rows'][str(y)].items():
            rows[int(gid)][y] = r
        for gid, r in debug['rows'][str(y)].items():
            ov[int(gid)][y] = r[0]
    res = {'years': years}
    # elite supply over time
    res['elite'] = {y: tuple(sum(1 for g in ov if ov[g].get(y, 0) >= t) for t in (80, 85, 90)) for y in years}
    # top-20 / top-50 by Overall: ages
    top = {}
    for y in years:
        act = sorted((ov[g][y], g) for g in ov if y in ov[g] and rows[g][y][I_LIFE] != 'retired')[::-1]
        ages20 = [y - born[g] for _, g in act[:20]]
        ages50 = [y - born[g] for _, g in act[:50]]
        top[y] = (S.mean(ages20), S.mean(ages50), sum(a >= 40 for a in ages50), sum(a >= 45 for a in ages50),
                  act[0][0], act[0][0] - act[9][0], act[0][0] - act[19][0])
    res['top'] = top
    # wins and majors by age
    wins_age, maj_age, prem_age = Counter(), Counter(), Counter()
    for g, ys in rows.items():
        for y, r in ys.items():
            a = y - born[g]
            band = '<25' if a < 25 else '25-29' if a < 30 else '30-34' if a < 35 else '35-39' if a < 40 else '40-44' if a < 45 else '45-49' if a < 50 else '50+'
            if r[I_WINS]:
                wins_age[band] += r[I_WINS]
            wbt = r[I_WBT] or {}
            p = wbt.get('1', 0) if isinstance(wbt, dict) else 0
            if p:
                prem_age[band] += p
            if r[I_MAJORS]:
                maj_age[band] += r[I_MAJORS]
    res['wins_age'], res['maj_age'], res['prem_age'] = wins_age, maj_age, prem_age
    # careers of entrants (juniors from the second season): entry overall, max, age at max, last 85+ / 80+
    entr = [g for g in ov if not initial[g] and created[g] and born[g] == created[g] - 18]
    entry = [ov[g][min(ov[g])] for g in entr]
    res['entry'] = (len(entr), S.mean(entry) if entry else 0, sum(e >= 75 for e in entry), sum(e >= 80 for e in entry),
                    sum(e >= 85 for e in entry), max(entry) if entry else 0)
    res['entr_max'] = Counter()
    for g in entr:
        m = max(ov[g].values())
        for t in (75, 80, 85, 90):
            if m >= t:
                res['entr_max'][t] += 1
    # everyone observed from <= 28 to >= 38: age at max and decline
    peak_rows, last85 = [], []
    for g, ys in ov.items():
        ages = {y - born[g]: v for y, v in ys.items()}
        if min(ages) <= 28 and max(ages) >= 38 and max(ages.values()) >= 70:
            am = max(ages, key=lambda a: ages[a])
            peak_rows.append((am, max(ages.values()), ages.get(40), ages.get(45)))
        if max(ys.values()) >= 85:
            last85.append(max(y - born[g] for y, v in ys.items() if v >= 85))
    res['peak'] = peak_rows
    res['last85'] = last85
    # decline among survivors by age band (year-on-year change of active golfers with max >= 65)
    dec = defaultdict(list)
    for g, ys in ov.items():
        if max(ys.values()) < 65:
            continue
        for y in ys:
            if y + 1 in ys and rows[g][y + 1][I_LIFE] != 'retired':
                a = y - born[g]
                dec[min(55, a // 5 * 5)].append(ys[y + 1] - ys[y])
    res['dec'] = {k: (len(v), S.mean(v)) for k, v in sorted(dec.items())}
    # injuries by age (weeks per golfer-season among those who played)
    inj = defaultdict(list)
    for g, ys in rows.items():
        for y, r in ys.items():
            if r[I_EVENTS]:
                inj[min(55, (y - born[g]) // 5 * 5)].append(r[I_INJ])
    res['inj'] = {k: (len(v), S.mean(v), sum(x > 0 for x in v) / len(v)) for k, v in sorted(inj.items())}
    # retirements by age
    ret = Counter()
    for g, ys in rows.items():
        yy = sorted(ys)
        for a, b in zip(yy, yy[1:]):
            if ys[b][I_LIFE] == 'retired' and ys[a][I_LIFE] != 'retired':
                ret[min(65, (b - born[g]) // 5 * 5)] += 1
    res['ret'] = dict(sorted(ret.items()))
    # item 4: access of high-Overall golfers and field gaps
    acc = {}
    for y in years:
        act = sorted((ov[g][y], g) for g in ov if y in ov[g] and rows[g][y][I_LIFE] != 'retired')[::-1][:100]
        off = Counter()
        for v, g in act:
            r = rows[g][y]
            if r[I_TIER] != 1:
                off['amateur' if r[I_STATUS] == 'amateur' else 'club pro' if r[I_STATUS] == 'club_pro'
                    else f'pro tier {r[I_TIER]}'] += 1
        prem = sorted((ov[g][y] for g in ov if y in ov[g] and rows[g][y][I_TIER] == 1), reverse=True)
        acc[y] = (sum(off.values()), dict(off), prem[0] - prem[9] if len(prem) > 9 else None,
                  prem[0] - prem[19] if len(prem) > 19 else None)
    res['access'] = acc
    nums = [data['number_one'].get(str(y)) for y in years]
    res['no1'] = Counter(n for n in nums if n)
    res['majors'] = data['majors']
    res['born'] = born
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('main_dir'); ap.add_argument('branch_dir'); ap.add_argument('seed', type=int)
    ap.add_argument('--log-main'); ap.add_argument('--log-branch')
    a = ap.parse_args()
    arms = {'main (dev-1)': analyse(*load(a.main_dir, a.seed)), 'branch (dev-2)': analyse(*load(a.branch_dir, a.seed))}
    out = []
    p = out.append
    ys = sorted(set(arms['main (dev-1)']['years']) & set(arms['branch (dev-2)']['years']))
    p(f'Seed {a.seed}, full scale, seasons {ys[0]}-{ys[-1]} ({len(ys)}) in both runs.\n')
    p('### Elite supply (golfers at 80+ / 85+ / 90+ Overall at season end)\n')
    pick = [y for y in ys if (y - ys[0]) % 5 == 4 or y == ys[-1]]
    p(table([[y] + [ '/'.join(map(str, arms[k]['elite'][y])) for k in arms] for y in pick], ['season'] + list(arms)))
    p('\n### Juniors entering from the second season: entry and realized maximum\n')
    p(table([[k, *[f'{x:.2f}' if isinstance(x, float) else x for x in r['entry']],
              *[r['entr_max'][t] for t in (75, 80, 85, 90)]] for k, r in arms.items()],
            ['arm', 'juniors', 'mean entry', 'entered 75+', '80+', '85+', 'max entry', 'reached 75+', '80+', '85+', '90+']))
    p('\n### Top of the world by Overall (season-end averages over all seasons and over the last ten)\n')
    rows = []
    for k, r in arms.items():
        for label, sel in (('all', ys), ('last 10', ys[-10:])):
            t = [r['top'][y] for y in sel]
            rows.append([k, label] + [f'{S.mean(x[i] for x in t):.2f}' for i in range(7)])
    p(table(rows, ['arm', 'seasons', 'top-20 mean age', 'top-50 mean age', 'top-50 aged 40+', '45+', 'best Overall',
                   'gap best-10th', 'gap best-20th']))
    p('\n### Wins, Premier wins and majors by age\n')
    bands = ['<25', '25-29', '30-34', '35-39', '40-44', '45-49', '50+']
    for key, name in (('wins_age', 'all wins'), ('prem_age', 'Premier wins'), ('maj_age', 'majors')):
        p(f'\n{name}:\n')
        p(table([[k] + [r[key][b] for b in bands] + [f"{100 * sum(r[key][b] for b in bands[4:]) / max(1, sum(r[key].values())):.1f}%"]
                 for k, r in arms.items()], ['arm'] + bands + ['share 40+']))
    p('\n### Careers observed from 28 or younger to 38 or older (maximum 70+): age at maximum, Overall at 40 and 45 '
      'relative to the maximum\n')
    rr = []
    for k, r in arms.items():
        pk = r['peak']
        d40 = [x[2] - x[1] for x in pk if x[2] is not None]
        d45 = [x[3] - x[1] for x in pk if x[3] is not None]
        rr.append([k, len(pk), f'{S.median(x[0] for x in pk):.0f} ({q([x[0] for x in pk], .1)}-{q([x[0] for x in pk], .9)})',
                   f'{S.median(d40):+.1f}' if d40 else '-', f'{S.median(d45):+.1f}' if d45 else '-',
                   f"{S.median(r['last85']):.0f} ({q(r['last85'], .9)})" if r['last85'] else '-', len(r['last85'])])
    p(table(rr, ['arm', 'n', 'age at max: median (p10-p90)', 'at 40 vs max', 'at 45 vs max',
                 'last season at 85+: median age (p90)', 'golfers ever 85+']))
    p('\n### Year-on-year Overall change of active golfers (maximum 65+) by age band\n')
    bks = sorted(set(arms['main (dev-1)']['dec']) | set(arms['branch (dev-2)']['dec']))
    p(table([[f'{b}-{b + 4}' if b < 55 else '55+'] + [f"{arms[k]['dec'].get(b, (0, 0))[1]:+.2f} (n {arms[k]['dec'].get(b, (0, 0))[0]})" for k in arms]
             for b in bks], ['age'] + list(arms)))
    p('\n### Injuries by age (golfer-seasons with starts: mean weeks injured, share injured)\n')
    bks = sorted(set(arms['main (dev-1)']['inj']) | set(arms['branch (dev-2)']['inj']))
    p(table([[f'{b}-{b + 4}' if b < 55 else '55+'] + [f"{arms[k]['inj'].get(b, (0, 0, 0))[1]:.2f} / {100 * arms[k]['inj'].get(b, (0, 0, 0))[2]:.1f}%" for k in arms]
             for b in bks], ['age'] + list(arms)))
    p('\n### Retirements by age at retirement\n')
    bks = sorted(set(arms['main (dev-1)']['ret']) | set(arms['branch (dev-2)']['ret']))
    p(table([[f'{b}-{b + 4}' if b < 65 else '65+'] + [arms[k]['ret'].get(b, 0) for k in arms] for b in bks], ['age'] + list(arms)))
    p('\n### Item 4 diagnostic: world top-100 by Overall not on the Premier Tour; Premier members\' Overall gaps\n')
    rows = []
    for k, r in arms.items():
        for label, sel in (('all', ys), ('last 10', ys[-10:])):
            acc = [r['access'][y] for y in sel]
            why = Counter()
            for x in acc:
                why.update(x[1])
            rows.append([k, label, f'{S.mean(x[0] for x in acc):.1f}',
                         ', '.join(f'{w} {c / len(acc):.1f}' for w, c in why.most_common()),
                         f'{S.mean(x[2] for x in acc if x[2] is not None):.2f}',
                         f'{S.mean(x[3] for x in acc if x[3] is not None):.2f}'])
    p(table(rows, ['arm', 'seasons', 'top-100 not on Premier (mean)', 'where they are (mean per season)',
                   'Premier best minus 10th', 'best minus 20th']))
    p('\n### Dominance: seasons ending at world No. 1, and majors per winner\n')
    for k, r in arms.items():
        mw = Counter(r['majors'].values())
        top3 = mw.most_common(3)
        p(f"- {k}: season-end No. 1 held by {len(r['no1'])} golfers (most {max(r['no1'].values()) if r['no1'] else 0} "
          f"seasons); {len(r['majors'])} majors, {len(mw)} winners, most by one golfer: "
          + ', '.join(f'{c} (born {r["born"].get(int(g), "?")})' for g, c in top3))
    for k, log in (('main (dev-1)', a.log_main), ('branch (dev-2)', a.log_branch)):
        t = season_times(log)
        if t:
            p(f'- season time, {k} (cloud, 2 workers, two runs sharing 4 CPUs): median {S.median(t):.0f} s, '
              f'max {max(t)} s over {len(t)} seasons')
    print('\n'.join(out))


if __name__ == '__main__':
    main()
