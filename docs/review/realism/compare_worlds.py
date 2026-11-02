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


def analyse(data, debug, only=None):
    """Season-end facts of one run, restricted to the seasons in `only` (both arms are compared on the identical
    covered seasons)."""
    years = sorted(int(y) for y in data['rows'] if only is None or int(y) in only)
    gol = data['golfers']
    born = {int(k): v['born'] for k, v in gol.items()}
    created = {int(k): v['created'] for k, v in gol.items()}
    initial = {int(k): v['initial'] for k, v in gol.items()}
    ov = defaultdict(dict)                                  # gid -> year -> overall
    rows = defaultdict(dict)
    for y in years:
        for gid, r in data['rows'][str(y)].items():  # (rows: golfers in the season snapshot; retirees are not in it)
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
    # wins by age from the season snapshots (golfers in them); majors by age from the majors' winner ledger
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
                maj_age['snapshot ' + band] += r[I_MAJORS]
    for key, gid in data['majors'].items():
        y = int(key.split(':')[0])
        if y in years:
            a = y - born[int(gid)]
            maj_age['<25' if a < 25 else '25-29' if a < 30 else '30-34' if a < 35 else '35-39' if a < 40 else '40-44'
                    if a < 45 else '45-49' if a < 50 else '50+'] += 1
    res['maj_snapshot_total'] = sum(v for k, v in maj_age.items() if k.startswith('snapshot '))
    res['maj_ledger_total'] = sum(1 for k in data['majors'] if int(k.split(':')[0]) in years)
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
    # retirements by age from the recorded career transitions (the winter's decisions), among golfers whose highest
    # observed season-end Overall was 65+: retired from play, and retired into a coaching or caddie job, apart.
    # Deaths are not in this export (unavailable here).
    ret = Counter()
    for y in years:
        for t in data['transitions'].get(str(y), []):
            g = t['gid']
            if not (ov.get(g) and max(ov[g].values()) >= 65):
                continue
            band = min(65, t['age'] // 5 * 5)
            if t.get('kind') == 'retired':
                ret[(band, 'play')] += 1
            elif t.get('via') == 'retirement' and t.get('kind') in ('became coach', 'became caddie'):
                ret[(band, 'staff')] += 1
    res['ret'] = ret
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
    raw = {'main (dev-1)': load(a.main_dir, a.seed), 'branch (dev-2)': load(a.branch_dir, a.seed)}
    common = set.intersection(*({int(y) for y in d['rows']} for d, _ in raw.values()))
    arms = {k: analyse(d, g, common) for k, (d, g) in raw.items()}
    out = []
    p = out.append
    ys = sorted(common)
    p(f'Seed {a.seed}, full scale. Both arms compared on the identical covered seasons {ys[0]}-{ys[-1]} ({len(ys)}). '
      'Ratings are season-end values (after the season and its winter); a golfer\'s "maximum" is the highest observed '
      'season-end rating, not a complete-career peak; careers still running at the end are censored.\n')
    p('### Golfers at 80+ / 85+ / 90+ Overall at season end (golfers in that season\'s snapshot)\n')
    pick = [y for y in ys if (y - ys[0]) % 5 == 4 or y == ys[-1]]
    p(table([[y] + ['/'.join(map(str, arms[k]['elite'][y])) for k in arms] for y in pick], ['season'] + list(arms)))
    p('\n### Juniors arriving from the second season: first observed season-end Overall and highest observed season-end '
      'Overall (not their entry rating: the first record is after their first season and winter)\n')
    p(table([[k, *[f'{x:.2f}' if isinstance(x, float) else x for x in r['entry']],
              *[r['entr_max'][t] for t in (75, 80, 85, 90)]] for k, r in arms.items()],
            ['arm', 'juniors', 'mean first observed', 'first observed 75+', '80+', '85+', 'largest first observed',
             'highest observed 75+', '80+', '85+', '90+']))
    p('\n### Top of the world by Overall (season-end averages)\n')
    rows = []
    for k, r in arms.items():
        for label, sel in (('all', ys), ('last 10', ys[-10:])):
            t = [r['top'][y] for y in sel]
            rows.append([k, label] + [f'{S.mean(x[i] for x in t):.2f}' for i in range(5)])
    p(table(rows, ['arm', 'seasons', 'top-20 mean age', 'top-50 mean age', 'top-50 aged 40+', '45+', 'best Overall']))
    p('\n### Wins by age (season snapshots) and majors by age (the majors\' winner ledger)\n')
    bands = ['<25', '25-29', '30-34', '35-39', '40-44', '45-49', '50+']
    for key, name in (('wins_age', 'all wins (snapshots)'), ('prem_age', 'Premier wins (snapshots)'),
                      ('maj_age', 'majors (winner ledger)')):
        p(f'\n{name}:\n')
        p(table([[k] + [r[key][b] for b in bands] + [f"{100 * sum(r[key][b] for b in bands[4:]) / max(1, sum(r[key][b] for b in bands)):.1f}%"]
                 for k, r in arms.items()], ['arm'] + bands + ['share 40+']))
    for k, r in arms.items():
        p(f"- {k}: majors in the ledger {r['maj_ledger_total']}, counted in season snapshots {r['maj_snapshot_total']}"
          + (' (reconciled)' if r['maj_ledger_total'] == r['maj_snapshot_total'] else ' (the ledger is used)'))
    p('\n### Careers observed from 28 or younger to 38 or older (highest observed 70+): age at the highest observed '
      'rating, and the rating at 40 and 45 relative to it; last observed age at 85+ (censored at the run\'s end)\n')
    rr = []
    for k, r in arms.items():
        pk = r['peak']
        d40 = [x[2] - x[1] for x in pk if x[2] is not None]
        d45 = [x[3] - x[1] for x in pk if x[3] is not None]
        rr.append([k, len(pk), f'{S.median(x[0] for x in pk):.0f} ({q([x[0] for x in pk], .1)}-{q([x[0] for x in pk], .9)})'
                   if pk else '-',
                   f'{S.median(d40):+.1f}' if d40 else '-', f'{S.median(d45):+.1f}' if d45 else '-',
                   f"{S.median(r['last85']):.0f} ({q(r['last85'], .9)})" if r['last85'] else '-', len(r['last85'])])
    p(table(rr, ['arm', 'n', 'age at highest observed: median (p10-p90)', 'at 40 vs highest', 'at 45 vs highest',
                 'last observed age at 85+: median (p90)', 'golfers observed at 85+']))
    p('\n### Year-on-year season-end Overall change of golfers in consecutive snapshots (highest observed 65+), by age\n')
    bks = sorted(set(arms['main (dev-1)']['dec']) | set(arms['branch (dev-2)']['dec']))
    p(table([[f'{b}-{b + 4}' if b < 55 else '55+'] + [f"{arms[k]['dec'].get(b, (0, 0))[1]:+.2f} (n {arms[k]['dec'].get(b, (0, 0))[0]})" for k in arms]
             for b in bks], ['age'] + list(arms)))
    p('\n### Injuries by age: weeks injured per golfer-season with starts, and the share of those golfer-seasons with any '
      'injury (not a per-start injury rate: injury episodes per start are not in this export)\n')
    bks = sorted(set(arms['main (dev-1)']['inj']) | set(arms['branch (dev-2)']['inj']))
    p(table([[f'{b}-{b + 4}' if b < 55 else '55+'] + [f"{arms[k]['inj'].get(b, (0, 0, 0))[1]:.2f} / {100 * arms[k]['inj'].get(b, (0, 0, 0))[2]:.1f}%" for k in arms]
             for b in bks], ['age'] + list(arms)))
    p('\n### Retirements by age (recorded career transitions; golfers whose highest observed rating was 65+): from play, '
      'and into a coaching or caddie job. Deaths are not in this export.\n')
    bks = sorted({b for r in arms.values() for b, _ in r['ret']})
    p(table([[f'{b}-{b + 4}' if b < 65 else '65+'] + [f"{arms[k]['ret'][(b, 'play')]} / {arms[k]['ret'][(b, 'staff')]}" for k in arms]
             for b in bks], ['age'] + [f'{k}: play / staff' for k in arms]))
    p('\n### Item 4 diagnostic (partial): world top-100 by Overall not on the Premier Tour; Premier MEMBERS\' Overall gaps\n')
    p('Diagnostic only: being off the Premier Tour (amateur, college, another tour, eligibility, scheduling) does not '
      'establish blocked access, and member gaps are not tournament-field gaps.\n')
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
                   'Premier members: best minus 10th', 'best minus 20th']))
    p('\n### Dominance: seasons ending at world No. 1, and majors per winner (winner ledger)\n')
    for k, r in arms.items():
        mw = Counter(g for key, g in r['majors'].items() if int(key.split(':')[0]) in common)
        top3 = mw.most_common(3)
        p(f"- {k}: season-end No. 1 held by {len(r['no1'])} golfers (most {max(r['no1'].values()) if r['no1'] else 0} "
          f"seasons); {sum(mw.values())} majors, {len(mw)} winners, most by one golfer: "
          + ', '.join(f'{c} (born {r["born"].get(int(g), "?")})' for g, c in top3))
    for k, log in (('main (dev-1)', a.log_main), ('branch (dev-2)', a.log_branch)):
        t = season_times(log)
        if t:
            p(f'- season time, {k} (cloud, 2 workers, two runs sharing 4 CPUs; relative only): median {S.median(t):.0f} s, '
              f'max {max(t)} s over {len(t)} seasons')
    print('\n'.join(out))


if __name__ == '__main__':
    main()
