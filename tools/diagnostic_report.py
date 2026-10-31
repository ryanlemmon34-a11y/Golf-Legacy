"""The diagnostic runs' report: full careers (run A), the amateur-support comparison (B against C), a third world
(D), the work pathway and the groups it leaves out, retirement coverage and performance, from what
tools/long_world.py --session kept (seed_<seed>.json.gz, debug, and the world's archived season files).

    python tools/diagnostic_report.py --run A=<dir>:360013 --run B=<dir>:2027 --run C=<dir>:2027 \
        --run D=<dir>:3031 --out docs/DIAGNOSTIC_RUNS.md

Every number is counted from the recorded seasons; nothing is estimated. Runs that stopped early are reported
with the seasons they completed.
"""
from __future__ import annotations

import argparse
import gzip
import json
import statistics as S
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
import long_world as LW                                                   # noqa: E402

EXITS = LW.EXITS
TECH = (1, 2, 3)                      # development categories that make up the technical game


def med(xs):
    return S.median(xs) if xs else None


def q(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(p * len(xs)))] if xs else None


def rating_at_age(ov, born, age):
    """The season-end Overall of the season the golfer was exactly `age` ({year: overall}); None if not recorded."""
    return next((ov[y] for y in sorted(ov) if y - born == age), None)


def f(x, d=1):
    return '—' if x is None else f'{x:.{d}f}'


def table(head, rows):
    out = ['| ' + ' | '.join(head) + ' |', '|' + '---|' * len(head)]
    out += ['| ' + ' | '.join(str(c) for c in r) + ' |' for r in rows]
    return out


class Run:
    def __init__(self, name, folder, seed):
        self.name, self.dir, self.seed = name, Path(folder), seed
        self.d = LW.load(self.dir, seed)
        self.dbg = LW.load_debug(self.dir, seed)
        self.man = json.loads((self.dir / 'manifest.json').read_text())
        self.years = sorted(self.d['rows'])
        self.first = self.d['first']
        self._seasons = {}

    def season(self, y):
        """The archived season file (development diagnostics), read once."""
        if y not in self._seasons:
            from golfsim.archive import _read, read_manifest
            a = self.dir / f'world_{self.seed}' / 'archive'
            man = read_manifest(a) or {}
            f = man.get('files', {}).get('years', {}).get(str(y)) or man.get('files', {}).get('years', {}).get(y)
            self._seasons[y] = _read(a / f) if f else {}
        return self._seasons[y]

    def amateurs(self, y):
        return {int(g): v for g, v in self.d['extras'].get(y, {}).get('amateurs', {}).items()}

    def exits(self):
        """{gid: (year, age, kind)} of every exit from competitive golf."""
        out = {}
        for y, ts in self.d['transitions'].items():
            for t in ts:
                if t['kind'] in EXITS or t['kind'].startswith('became '):
                    out.setdefault(t['gid'], (y, t['age'], t['kind']))
        return out


# ---- sections -----------------------------------------------------------------------------------------
def overview(runs):
    out = ['## The runs', '']
    rows = []
    for r in runs:
        m = r.man
        stop = r.d.get('stopped')
        rows.append([r.name, r.seed, f'`{str(m.get("commit"))[:10]}`', 'on' if r.d.get('amateur_support', True) else 'off',
                     f'{len(r.years)} ({r.years[0]}-{r.years[-1]})' if r.years else '0',
                     f'{r.d.get("minutes", 0):.0f} min', stop or 'completed'])
    out += table(['Run', 'Seed', 'Commit', 'Amateur support', 'Seasons', 'Run time', 'Ended'], rows)
    m = runs[0].man.get('machine') or {}
    out += ['', f'Machine: {json.dumps(m)}', '']
    return out


def performance(runs):
    out = ['## Performance on this machine', '',
           'Each season is the observer\'s season skip (simulate, save the checkpoint, publish the history, reload). '
           'Two worker processes per run; two runs side by side on 4 CPUs while other work shared the machine, so '
           'these are this machine\'s timings, not the 120-second acceptance measurement (that uses the owner\'s '
           'machine and workload).', '']
    rows = []
    for r in runs:
        p = r.d['perf']
        if not p:
            continue
        ys = sorted(p)
        sk = [p[y]['skip'] for y in ys]
        rows.append([r.name, f(sk[0], 0), f(med(sk), 0), f(max(sk), 0), f(sk[-1], 0),
                     f(med([p[y]['simulate'] for y in ys]), 0), f(med([p[y]['save'] + p[y]['publish'] for y in ys]), 1),
                     f(p[ys[-1]]['archive_mb'], 0), f(p[ys[-1]]['checkpoint_mb'], 0)])
    out += table(['Run', 'First season s', 'Median s', 'Slowest s', 'Last s', 'Median simulate s', 'Median save+publish s',
                  'Archive MB at end', 'Checkpoint MB'], rows)
    return out + ['']


def population(runs):
    out = ['## Population', '']
    rows = []
    for r in runs:
        c = r.d['checks']
        ys = sorted(c)
        if not ys:
            continue
        rows.append([r.name, c[ys[0]]['active_before'], c[ys[-1]]['active_after'],
                     sum(c[y]['juniors'] for y in ys), sum(c[y]['exits'] for y in ys),
                     sum(1 for y in ys if c[y]['population_ok']), len(ys), len(r.d.get('flags', {}))])
    out += table(['Run', 'Active at start', 'Active at end', 'Arrivals', 'Exits', 'Seasons reconciling', 'Seasons',
                  'Seasons flagged (>20 % from start)'], rows)
    for r in runs:
        for y, t in sorted(r.d.get('flags', {}).items()):
            out.append(f'- {r.name} {y}: {t}')
    return out + ['']


def retirement(r):
    """Run A: who has retired by the end, cohort by cohort (when each golfer entered the world)."""
    out = [f'## Retirement coverage (run {r.name}, {len(r.years)} seasons)', '',
           'Cohorts by the season a golfer entered (the seeded world, then procedural arrivals). Retired = left '
           'competitive golf (retired, or became a coach or caddie).', '']
    g = r.d['golfers']
    ex = r.exits()
    last = r.years[-1]
    groups = [('seeded world', lambda c: c is None or c <= r.first)]
    for lo, hi in ((1, 5), (6, 10), (11, 20), (21, 30), (31, 45)):
        groups.append((f'arrived in seasons {lo + 1}-{hi + 1}', lambda c, lo=lo, hi=hi: c is not None and
                       r.first + lo <= c <= r.first + hi))
    rows = []
    for label, test in groups:
        ids = [gid for gid, v in g.items() if test(v.get('created')) and (label == 'seeded world') == bool(v.get('initial'))]
        if not ids:
            continue
        gone = [gid for gid in ids if gid in ex]
        ages = [ex[gid][1] for gid in gone]
        still = [last - g[gid]['born'] for gid in ids if gid not in ex]
        rows.append([label, len(ids), len(gone), f'{len(gone) / len(ids):.0%}', f(med(ages), 0),
                     f'{q(ages, .1)}-{q(ages, .9)}' if ages else '—', len(still), f(med(still), 0),
                     max(still) if still else '—'])
    out += table(['Cohort', 'Golfers', 'Retired by the end', 'Share', 'Median retirement age', '10th-90th pct age',
                  'Still active', 'Their median age', 'Oldest active'], rows)
    return out + ['']


def careers(r):
    """Run A: peak Overall, peak age, time near the peak, for procedural golfers whose careers ended."""
    ex = r.exits()
    g = r.d['golfers']
    by = defaultdict(dict)                                    # gid -> year -> overall (the season's end)
    for y, rows in r.dbg.items():
        for gid, v in rows.items():
            by[gid][y] = v[0]
    done = [gid for gid, v in g.items() if not v.get('initial') and gid in ex and len(by.get(gid, {})) >= 5]
    peaks = []
    for gid in done:
        ov = by[gid]
        py = max(ov, key=lambda y: ov[y])
        near = sum(1 for y in ov if ov[y] >= ov[py] - 2)
        peaks.append((gid, ov[py], py - g[gid]['born'], near, len(ov)))
    out = [f'## Peaks of completed procedural careers (run {r.name})', '',
           f'{len(peaks)} golfers who arrived after the world began and have left competitive golf (five or more '
           'seasons recorded).', '']
    if peaks:
        rows = []
        for lo, hi in ((0, 50), (50, 60), (60, 70), (70, 80), (80, 101)):
            sel = [p for p in peaks if lo <= p[1] < hi]
            if sel:
                rows.append([f'{lo}-{hi - 1 if hi < 101 else 100}', len(sel), f(med([p[2] for p in sel]), 0),
                             f(med([p[3] for p in sel]), 0), f(med([p[4] for p in sel]), 0)])
        out += table(['Peak Overall', 'Golfers', 'Median peak age', 'Median seasons within 2 of peak',
                      'Median seasons recorded'], rows)
    # the strongest careers of the run (any golfer arriving after the start)
    best = sorted(((max(ov.values()), gid) for gid, ov in by.items() if not g.get(gid, {}).get('initial')),
                  reverse=True)[:10]
    out += ['', 'The ten highest peaks among golfers who arrived during the run:', '']
    rows = []
    for peak, gid in best:
        v, ov = g[gid], by[gid]
        at19 = rating_at_age(ov, v['born'], 19)
        y0 = min(ov)
        py = max(ov, key=lambda y: ov[y])
        pot = next((r.dbg[y][gid][1] for y in sorted(ov) if gid in r.dbg.get(y, {})), None)
        wins = sum(r.d['rows'][y][gid]['wins'] for y in ov if gid in r.d['rows'].get(y, {}))
        majors = sum(r.d['rows'][y][gid]['majors'] for y in ov if gid in r.d['rows'].get(y, {}))
        rows.append([v['name'], v['country'], v['created'], f(at19), f'{f(ov[y0])} at {y0 - v["born"]}', f(pot),
                     f(peak), py - v['born'], wins, majors,
                     f'retired at {ex[gid][1]}' if gid in ex else 'active'])
    out += table(['Golfer', 'Nation', 'Arrived', 'Overall at 19', 'First recorded (Overall at age)', 'Potential',
                  'Peak', 'Peak age', 'Wins', 'Majors', 'Now'], rows)
    out += ['', '"Overall at 19" is the season-end rating of the season they were exactly 19; "—" when no such '
            'season was recorded (they arrived older, or it is not played yet).']
    return out + ['']


def development(r):
    """Run A: what moved Overall, by age and by source; decline by part of the game after 30. Golfers of the seeded
    world (created with the world, already mid-career) and procedural arrivals are reported apart, as careers() does,
    so the seeded population's starting ages and levels do not mix into the arrivals' development curves."""
    g = r.d['golfers']
    out = [f'## Development by age and source (run {r.name})', '',
           'Mean change in Overall per golfer-season, by the source the development evidence records (all levels; the '
           'development evidence of each archived season). The seeded world and procedural arrivals are shown apart.',
           '']
    for label, want in (('Procedural arrivals (joined during the run)', False), ('Seeded world (present at the start)', True)):
        by_age = defaultdict(lambda: [0.0] * 5)
        n_age = Counter()
        decline = defaultdict(lambda: [0.0, 0.0, 0.0])          # age band -> physical, technical, mental (aging)
        n_dec = Counter()
        for y in r.years:
            dev = r.season(y).get('diagnostics', {}).get('development', {})
            for gid, v in dev.items():
                gv = g.get(int(gid))
                if gv is None or bool(gv.get('initial')) != want:
                    continue
                age = y - gv['born']
                band = min(age // 3 * 3, 51)
                for i in range(5):
                    by_age[band][i] += v[25 + i]
                n_age[band] += 1
                if age >= 30:
                    b = min(age // 5 * 5, 55)
                    decline[b][0] += v[4 * 5 + 0]
                    decline[b][1] += sum(v[4 * 5 + c] for c in TECH)
                    decline[b][2] += v[4 * 5 + 4]
                    n_dec[b] += 1
        out += [f'**{label}**', '']
        rows = [[f'{a}-{a + 2}' if a < 51 else '51+', n_age[a]] + [f(by_age[a][i] / n_age[a], 3) for i in range(5)]
                + [f(sum(by_age[a]) / n_age[a], 3)] for a in sorted(by_age)]
        out += table(['Age', 'Golfer-seasons', 'Maturing', 'Training', 'Tournaments', 'Injury', 'Aging', 'Total'], rows)
        out += ['', 'Aging after 30 by part of the game (mean change per golfer-season, attribute points summed over '
                'the category\'s attributes):', '']
        rows = [[f'{b}-{b + 4}' if b < 55 else '55+', n_dec[b]] + [f(decline[b][i] / n_dec[b], 3) for i in range(3)]
                for b in sorted(decline)]
        out += table(['Age', 'Golfer-seasons', 'Physical', 'Technical (long, short, putting)', 'Mental'], rows) + ['']
    return out


AGE_BANDS = ((0, 20, 'under 21'), (21, 22, '21-22'), (23, 25, '23-25'), (26, 29, '26-29'), (30, 200, '30+'))
STANDING = ((1, 50, 'amateur top 50'), (51, 150, '51-150'), (151, 300, '151-300'), (301, 10 ** 6, 'ranked beyond 300'))


def age_band(age):
    return next(label for lo, hi, label in AGE_BANDS if lo <= age <= hi)


def standing_band(rank):
    if rank is None:
        return 'unranked'
    return next(label for lo, hi, label in STANDING if lo <= rank <= hi)


def breakdowns(b, c):
    """F1.h: the support comparison and zero-start seasons by age and by amateur standing at the season's end, both
    arms, from each season's recorded amateur rows (read only)."""
    out = [f'### By age and by amateur standing (runs {b.name} and {c.name})', '',
           'Every amateur season of every recorded season, grouped by age and by the amateur ranking at the season\'s '
           'end; support columns are run ' + b.name + '\'s (run ' + c.name + ' has none by design).', '']
    for title, key in (('Age', lambda v: age_band(v[0])), ('Amateur standing', lambda v: standing_band(v[3]))):
        agg = {run.name: defaultdict(list) for run in (b, c)}
        sup = defaultdict(lambda: [0, 0, 0])                    # group -> supported seasons, drawn, cap exhausted
        cap = {'A': 25000, 'B': 12000, 'C': 5000}
        for run in (b, c):
            for y in run.years:
                for v in run.amateurs(y).values():
                    k = key(v)
                    agg[run.name][k].append(v[4])
                    if run is b and v[6]:
                        sup[k][0] += 1
                        sup[k][1] += v[7]
                        sup[k][2] += v[7] >= 0.98 * cap[v[6]]
        order = [label for *_, label in (AGE_BANDS if title == 'Age' else STANDING)] + (['unranked'] if title != 'Age' else [])
        rows = []
        for k in order:
            xb, xc = agg[b.name].get(k, []), agg[c.name].get(k, [])
            if not xb and not xc:
                continue
            s_ = sup[k]
            rows.append([k, len(xb), f(S.mean(xb) if xb else None), f'{sum(1 for e in xb if e == 0) / len(xb):.1%}' if xb else '—',
                         f'{s_[0] / len(xb):.0%}' if xb else '—', f'${s_[1] / s_[0]:,.0f}' if s_[0] else '—',
                         f'{s_[2] / s_[0]:.0%}' if s_[0] else '—',
                         len(xc), f(S.mean(xc) if xc else None), f'{sum(1 for e in xc if e == 0) / len(xc):.1%}' if xc else '—'])
        out += [f'**{title}**', '']
        out += table([title, f'{b.name} amateur-seasons', f'{b.name} events', f'{b.name} no start', f'{b.name} supported',
                      f'{b.name} mean drawn', f'{b.name} cap used up', f'{c.name} amateur-seasons', f'{c.name} events',
                      f'{c.name} no start'], rows) + ['']
    return out


def support(b, c):
    """B (with support) against C (the same world and rules without it)."""
    out = [f'## Amateur support: run {b.name} (with) against run {c.name} (without)', '',
           'The same seed, build and rules; support is the only intended difference. Outcomes diverge as the '
           'seasons go on (different fields, rankings and money), so these are aggregate comparisons.', '']
    rows = []
    for y in b.years:
        am = b.amateurs(y)
        sup = [v for v in am.values() if v[6]]
        bands = Counter(v[6] for v in sup)
        drawn = sum(v[7] for v in sup)
        cap = {'A': 25000, 'B': 12000, 'C': 5000}
        ex = sum(1 for v in sup if v[7] >= 0.98 * cap[v[6]])
        rows.append([y, len(sup), f'{bands["A"]} / {bands["B"]} / {bands["C"]}', f'${drawn / 1e6:.2f} m',
                     f'{ex} ({ex / len(sup):.0%})' if sup else '—', f'${drawn / len(sup):,.0f}' if sup else '—'])
    out += ['Recipients and spending (run B; counted, no ceiling on contracts):', '']
    out += table(['Season', 'Recipients', 'A / B / C', 'Drawn', 'Used 98 %+ of their cap', 'Mean drawn'], rows)

    def stage_of(v):
        return 'college' if v[2] else f'{v[1].replace("_", "-")} non-college'

    def by_stage(run, y, test=lambda v: True):
        acc = defaultdict(list)
        for v in run.amateurs(y).values():
            if test(v):
                acc[stage_of(v)].append(v[4])
        return acc
    out += ['', 'Events per amateur and seasons without a start (season by season, both arms):', '']
    rows = []
    for y in sorted(set(b.years) & set(c.years)):
        sb, sc = by_stage(b, y), by_stage(c, y)
        for st in sorted(set(sb) | set(sc)):
            xb, xc = sb.get(st, []), sc.get(st, [])
            rows.append([y, st, len(xb), f(S.mean(xb) if xb else None), sum(1 for e in xb if e == 0),
                         len(xc), f(S.mean(xc) if xc else None), sum(1 for e in xc if e == 0)])
    out += table(['Season', 'Amateurs', f'{b.name}: n', f'{b.name}: events', f'{b.name}: no start',
                  f'{c.name}: n', f'{c.name}: events', f'{c.name}: no start'], rows)
    # professional conversion: turned pro each season
    out += ['', 'Amateurs turning professional each season:', '']
    rows = []
    for y in sorted(set(b.years) & set(c.years)):
        tb = sum(1 for t in b.d['transitions'].get(y, ()) if t['kind'] in ('turned pro', 'comeback') and t.get('am_rank', 0) is not None)
        tc = sum(1 for t in c.d['transitions'].get(y, ()) if t['kind'] in ('turned pro', 'comeback') and t.get('am_rank', 0) is not None)
        rows.append([y, tb, tc])
    out += table(['Season', b.name, c.name], rows)
    # the cohort ranked 1-150 when the world began
    y0 = b.years[0]
    top = {gid for gid, v in b.amateurs(y0).items() if v[3] is not None and v[3] <= 150}
    top_c = {gid for gid, v in c.amateurs(y0).items() if v[3] is not None and v[3] <= 150}
    out += ['', f'The amateurs ranked 1-150 at the end of {y0} ({len(top)} in {b.name}, {len(top_c)} in {c.name}), '
            'season by season after:', '']
    rows = []
    for y in sorted(set(b.years) & set(c.years)):
        def tally(run, ids):
            rows_y = run.d['rows'].get(y, {})
            pro = sum(1 for gid in ids if rows_y.get(gid, {}).get('status') == 'pro')
            am = [rows_y[gid]['events'] for gid in ids if rows_y.get(gid, {}).get('status') == 'amateur']
            gone = sum(1 for gid in ids if gid not in rows_y)
            return pro, len(am), f(S.mean(am) if am else None), sum(1 for e in am if e == 0), gone
        rows.append([y, *tally(b, top), *tally(c, top_c)])
    out += table(['Season', f'{b.name} pro', f'{b.name} amateur', f'{b.name} events', f'{b.name} no start',
                  f'{b.name} gone', f'{c.name} pro', f'{c.name} amateur', f'{c.name} events', f'{c.name} no start',
                  f'{c.name} gone'], rows)
    # by region (all seasons together)
    out += ['', 'By region (all seasons): events per amateur and the share of amateur seasons without a start:', '']
    agg = {run.name: defaultdict(list) for run in (b, c)}
    for run in (b, c):
        for y in run.years:
            for v in run.amateurs(y).values():
                agg[run.name][v[10]].append(v[4])
    rows = []
    for reg in sorted(set(agg[b.name]) | set(agg[c.name])):
        xb, xc = agg[b.name].get(reg, []), agg[c.name].get(reg, [])
        rows.append([reg, len(xb), f(S.mean(xb) if xb else None), f'{sum(1 for e in xb if e == 0) / len(xb):.1%}' if xb else '—',
                     len(xc), f(S.mean(xc) if xc else None), f'{sum(1 for e in xc if e == 0) / len(xc):.1%}' if xc else '—'])
    out += table(['Region', f'{b.name} amateur-seasons', f'{b.name} events', f'{b.name} no start',
                  f'{c.name} amateur-seasons', f'{c.name} events', f'{c.name} no start'], rows)
    return out + [''] + breakdowns(b, c)


def pathway(runs):
    out = ['## The work pathway and the amateurs it leaves out', '',
           'Full-time non-college amateur seasons, by why the pathway does or does not apply (as each season ended). '
           '"Blocked 8+" = a count of 8 or more genuinely cash-blocked weeks during the season (injury and calendar '
           'gaps pause the count, an affordable week resets it).', '']
    rows = []
    for r in runs:
        groups = defaultdict(lambda: [0, 0, 0, 0])            # seasons, zero starts, blocked 8+, both
        took = []
        for y in r.years:
            for gid, v in r.amateurs(y).items():
                if v[9] is not None:
                    took.append((y, gid, v))
                if v[1] != 'full_time' or v[2]:
                    continue
                age, rank, band, family = v[0], v[3], v[6], v[8]
                key = ('under 21' if age < 21 else 'ranked in the top 300' if rank is not None and rank <= 300
                       else 'holds support' if band else 'family money left' if family else 'eligible (21+, outside '
                       'the top 300, no support, no family money)')
                gr = groups[key]
                gr[0] += 1
                gr[1] += v[4] == 0
                gr[2] += v[5] >= 8
                gr[3] += v[4] == 0 and v[5] >= 8
        for key in sorted(groups):
            s_, z, bl, both = groups[key]
            rows.append([r.name, key, s_, z, bl, both])
        rows.append([r.name, '**took work by the pathway**', len(took), '', '', ''])
    out += table(['Run', 'Group', 'Seasons', 'No start all season', 'Blocked 8+', 'Both'], rows)
    return out + ['']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', action='append', required=True, help='NAME=<folder>:<seed>')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    runs = []
    for spec in a.run:
        name, rest = spec.split('=', 1)
        folder, seed = rest.rsplit(':', 1)
        runs.append(Run(name, folder, int(seed)))
    by = {r.name: r for r in runs}
    out = ['# Diagnostic runs', ''] + overview(runs) + performance(runs) + population(runs)
    if 'A' in by:
        out += retirement(by['A']) + careers(by['A']) + development(by['A'])
    if 'B' in by and 'C' in by:
        out += support(by['B'], by['C'])
    out += pathway(runs)
    Path(a.out).write_text('\n'.join(out) + '\n')
    print('wrote', a.out)


if __name__ == '__main__':
    main()
