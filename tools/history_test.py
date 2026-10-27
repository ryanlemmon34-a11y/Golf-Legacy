"""World history test: the world evolving for decades, every shot simulated, with development on.

    python tools/history_test.py [--years 20] [--seed 2027]

Golfers train, play, rest, improve, age, get injured, earn and spend money, turn professional, give up
the chase, come back, and retire; new juniors arrive every year. Writes reports/WORLD_HISTORY_REPORT.md
and a pickle of the final world (scratch use).
"""
from __future__ import annotations

import argparse
import statistics as S
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from golfsim import prestige as PR                                   # noqa: E402
from golfsim.calendar import TOUR_BY_KEY                             # noqa: E402
from golfsim.nations import REAL_TOP200                              # noqa: E402
from golfsim.population import generate_world, level_of              # noqa: E402
from golfsim.season import PREMIER_TOURS, Season                     # noqa: E402

LEVELS = ('Premier Tour', 'Challenger', 'Regional', 'Mini tour', 'College', 'Amateur', 'Club professional')
MAJORS = ('TOUR_MASTERS', 'PREMIER_TOUR_CHAMPIONSHIP', 'USA_OPEN', 'BRITANNIA_OPEN')


def snapshot(s, year):
    w = s.world
    active = [g for g in w.golfers if g.lifestyle != 'retired']
    pros = sorted((g for g in active if g.status == 'pro'), key=lambda g: -g.overall)
    lv = defaultdict(list)
    for g in active:
        lv[level_of(g)].append(g.overall)
    top200 = Counter(g.country for g in pros[:200])
    return {'active': len(active), 'full_pros': sum(1 for g in active if g.status == 'pro' and g.lifestyle == 'full_time'),
            'part_time': sum(1 for g in active if g.lifestyle == 'part_time'),
            'retired': sum(1 for g in w.golfers if g.lifestyle == 'retired'),
            'levels': {k: (len(v), S.mean(v)) for k, v in lv.items()},
            'no1': (pros[0].name, pros[0].country, pros[0].overall, pros[0].age(year)),
            'top10': [g.overall for g in pros[:10]], 'n85': sum(1 for g in pros if g.overall >= 85),
            'n90': sum(1 for g in pros if g.overall >= 90), 'top200': top200,
            'ages_premier': S.mean(g.age(year) for g in active if g.tour in PREMIER_TOURS)}


def career_line(s, gid):
    g = s.g[gid]
    return [f'  - {y}' + (f' wk {wk}' if wk <= 52 else '') + f': {text}' for y, wk, text in s.history[gid]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--years', type=int, default=20)
    ap.add_argument('--seed', type=int, default=2027)
    a = ap.parse_args()
    t0 = time.perf_counter()
    world = generate_world(seed=a.seed)
    start_ids = {g.id for g in world.golfers}
    s = Season(world, seed=a.seed, development=True)
    years = list(range(s.first_year, s.first_year + a.years))
    snaps = {s.first_year - 1: snapshot(s, s.first_year)}
    overall_at = defaultdict(dict)                     # gid -> year -> overall (start of year)
    premier_at = {}                                    # year -> Premier Tour members at the start of the year
    for y in years:
        premier_at[y] = {x.id for x in world.golfers if x.tour in PREMIER_TOURS}
        for g in world.golfers:
            if g.lifestyle != 'retired':
                overall_at[g.id][y] = g.overall
        t1 = time.perf_counter()
        s.run_year(y, progress=lambda yy, wk: print(f'\r{yy} week {wk:2d}', end='', flush=True))
        snaps[y] = snapshot(s, y + 1)
        print(f'  {time.perf_counter() - t1:.0f} s  active {snaps[y]["active"]}  No.1 {snaps[y]["no1"][2]:.1f}')
    s.close()
    g = s.g
    elapsed = time.perf_counter() - t0
    out = ['# Golf Legacy — World History Test', '',
           f'**{a.years} years** of the whole world ({years[0]}–{years[-1]}) with development on: '
           f'{sum(s.holes_played.values()):,} holes, every shot simulated, in {elapsed / 60:.0f} minutes. '
           f'{len(world.golfers):,} golfers have lived in this world ({len(world.golfers) - len(start_ids):,} arrived as juniors). '
           'Golfers plan each month (play, train or rest), improve toward their potential, age, get injured, earn '
           'and spend money, turn professional, give up the chase, come back and retire.', '']

    # ---- 1. the world's size ---------------------------------------------------------------------
    out += ['## 1. A stable, living world', '',
            '| Year | Active golfers | Full-time pros | Part-timers | Retired (total) | New juniors | Turned pro | Gave up the chase | Comebacks | Retired that year |',
            '|---|---|---|---|---|---|---|---|---|---|']
    for y in years:
        c = s.career_counts.get(y, {})
        quit_ = c.get('part-time pro', 0) + c.get('back to amateur', 0) + c.get('became club pro', 0)
        sn = snaps[y]
        out.append(f'| {y} | {sn["active"]:,} | {sn["full_pros"]:,} | {sn["part_time"]:,} | {sn["retired"]:,} | '
                   f'{s.juniors_added.get(y + 1, 0)} | {c.get("turned pro", 0)} | {quit_} | {c.get("comeback", 0)} | {c.get("retired", 0)} |')

    # ---- 2. levels over time ------------------------------------------------------------------------
    out += ['', '## 2. Levels over time (average overall)', '', '| Year | ' + ' | '.join(LEVELS) + ' |', '|---|' + '---|' * len(LEVELS)]
    for y in [years[0] - 1] + years[::2] + ([years[-1]] if years[-1] not in years[::2] else []):
        lv = snaps[y]['levels']
        out.append(f'| {y + 1 if y >= years[0] else years[0]} start | ' + ' | '.join(
            f'{lv[L][1]:.1f} ({lv[L][0]})' if L in lv else '—' for L in LEVELS) + ' |')

    # ---- 3. eras -----------------------------------------------------------------------------------
    out += ['', '## 3. Eras: the best players in the world', '',
            '| Start of | World No.1 (by ability) | Overall | Age | Top-10 average | Players 85+ | Players 90+ |', '|---|---|---|---|---|---|---|']
    for y in [years[0] - 1] + years:
        sn = snaps[y]
        n, c, o, ag = sn['no1']
        out.append(f'| {y + 1} | {n} ({c}) | {o:.1f} | {ag} | {S.mean(sn["top10"]):.1f} | {sn["n85"]} | {sn["n90"]} |')

    # ---- 4. majors ---------------------------------------------------------------------------------
    out += ['', '## 4. Major champions', '', '| Year | Tour Masters | Premier Tour Championship | USA Open | Britannia Open |', '|---|---|---|---|---|']
    major_wins = Counter()
    for y in years:
        cells = []
        for m in MAJORS:
            r = s.results.get(f'{y}:{m}')
            w = r.winner() if r else None
            if w:
                major_wins[w] += 1
                cells.append(f'{g[w].name} ({g[w].country[:3]}, {g[w].age(y)}) {next((tp for yy, gw, tp in s.champions[m] if yy == y), 0):+d}')
            else:
                cells.append('—')
        out.append(f'| {y} | ' + ' | '.join(cells) + ' |')
    out.append('\n**Most majors:** ' + ', '.join(f'{g[gid].name} ({g[gid].country}) {n}' for gid, n in major_wins.most_common(8)) + '.')

    # ---- 5. development ------------------------------------------------------------------------------
    out += ['', '## 5. Development: how golfers change with age', '',
            'Average change in overall per year, by age, across every golfer active in two consecutive seasons.', '',
            '| Age | Golfers | Average change per year | Best year |', '|---|---|---|---|']
    changes = defaultdict(list)
    for gid, yrs in overall_at.items():
        for y in years[:-1]:
            if y in yrs and y + 1 in yrs:
                changes[g[gid].age(y)].append(yrs[y + 1] - yrs[y])
    for lo, hi in ((18, 19), (20, 21), (22, 23), (24, 25), (26, 28), (29, 32), (33, 36), (37, 40), (41, 45), (46, 55)):
        xs = [d for age in range(lo, hi + 1) for d in changes.get(age, [])]
        if xs:
            out.append(f'| {lo}–{hi} | {len(xs):,} | {S.mean(xs):+.2f} | {max(xs):+.1f} |')
    # rising stars: juniors who arrived during the test
    juniors = [gid for gid in g if gid not in start_ids]
    risers = sorted(juniors, key=lambda gid: -g[gid].overall)[:8]
    out += ['', '**The best of the new generation** (arrived as 18-year-olds during the test):', '',
            '| Golfer | Arrived | Overall at 18 | Overall now | Potential | Work ethic | Now |', '|---|---|---|---|---|---|---|']
    for gid in risers:
        x = g[gid]
        first = min(overall_at[gid]) if overall_at[gid] else years[-1] + 1
        out.append(f'| {x.name} ({x.country}) | {first} | {overall_at[gid].get(first, x.overall):.1f} | {x.overall:.1f} | '
                   f'{x.potential:.1f} | {x.personality["work_ethic"]:.0f} | {level_of(x) if x.lifestyle != "retired" else "retired"} |')

    # ---- 6. careers --------------------------------------------------------------------------------
    quitters = [(gid, y, t) for gid, h in s.history.items() for y, wk, t in h if t.startswith('Stopped chasing')]
    by_age = Counter()
    for gid, y, t in quitters:
        by_age[min(40, (g[gid].age(y) // 2) * 2)] += 1
    out += ['', '## 6. Careers: giving up, comebacks, late bloomers', '',
            f'{len(quitters):,} professionals gave up the chase over {a.years} years. By age:', '',
            '| Age | Gave up |', '|---|---|'] + [f'| {k}–{k + 1}{"+" if k == 40 else ""} | {n} |' for k, n in sorted(by_age.items())]
    comebacks = [gid for gid, h in s.history.items() if any('another run' in t or 'late, after' in t for _, _, t in h)]
    out += ['', f'**Comebacks:** {len(comebacks)} part-timers quit their jobs to try again. What became of them:', '']
    for gid in comebacks[:6]:
        x = g[gid]
        out.append(f'- **{x.name}** ({x.country}), born {x.born}, now {level_of(x) if x.lifestyle != "retired" else "retired"}, overall {x.overall:.0f}:')
        out += career_line(s, gid)[-8:]
    late = []
    ever = set()
    for y in years:
        for gid in premier_at.get(y, ()):
            if gid not in ever and y > years[0] and g[gid].age(y) >= 30:
                late.append((gid, y))
            ever.add(gid)
    out += ['', f'**Late bloomers:** {len(late)} players reached the Premier Tour for the first time at 30 or older'
            + (' — e.g. ' + '; '.join(f'{g[gid].name} ({g[gid].country}) at {g[gid].age(y)}' for gid, y in late[:6]) if late else '') + '.']
    # a full career story
    star = max(juniors or list(g), key=lambda gid: (major_wins[gid], g[gid].overall))
    out += ['', f'**A career, in full — {g[star].name} ({g[star].country}):**', ''] + career_line(s, star)[:40]

    # ---- 7. money -----------------------------------------------------------------------------------
    y = years[-1]
    led = s.ledgers[y]
    out += ['', f'## 7. Money ({y})', '',
            '| Level | Golfers | Median prize money | Median sponsors | Median costs | Median net | Median savings |', '|---|---|---|---|---|---|---|']
    for L in LEVELS:
        xs = [x for x in world.golfers if level_of(x) == L and x.lifestyle != 'retired' and x.id in led]
        if not xs:
            continue
        m = lambda f: S.median(f(x) for x in xs)
        out.append(f'| {L} | {len(xs):,} | ${m(lambda x: led[x.id].prize):,.0f} | ${m(lambda x: led[x.id].sponsors):,.0f} | '
                   f'${m(lambda x: led[x.id].costs):,.0f} | ${m(lambda x: led[x.id].net):,.0f} | ${m(lambda x: x.cash):,.0f} |')
    rich = sorted(world.golfers, key=lambda x: -x.cash)[:5]
    out.append('\nRichest golfers: ' + ', '.join(f'{x.name} ${x.cash / 1e6:.0f}M' for x in rich) + '.')

    # ---- 8. injuries ------------------------------------------------------------------------------
    inj = [r for yy in years for r in s.injuries[yy]]
    lasting = sum(1 for h in s.history.values() for _, _, t in h if 'lasting damage' in t)
    out += ['', '## 8. Injuries', '', f'{len(inj):,} injuries in {a.years} years; {lasting} with lasting damage (10+ weeks out).']

    # ---- 9. nations ---------------------------------------------------------------------------------
    first, last = snaps[years[0] - 1]['top200'], snaps[years[-1]]['top200']
    out += ['', '## 9. Nations in the world top 200 (by ability)', '',
            'Nation profiles are fixed in this test (the nation-improvement model is next), so shares should stay '
            'close to the start.', '', '| Country | Start | End | Real world |', '|---|---|---|---|']
    for c in sorted(set(first) | set(last), key=lambda c: -(first[c] + last[c]))[:16]:
        out.append(f'| {c} | {first[c]} | {last[c]} | {REAL_TOP200.get(c, 0)} |')

    # ---- 10. events ---------------------------------------------------------------------------------
    cat = defaultdict(lambda: defaultdict(list))
    for sid, hist in s.prestige_history.items():
        ser = s.cal.by_id[sid]
        if ser.tier <= 1:
            for yy, p, f in hist:
                cat[ser.category if ser.kind != 'major' else 'major'][yy].append(p)
    out += ['', '## 10. Event prestige over the years', '', '| Year | Majors | Flagship | Standard | National opens | Opportunity |', '|---|---|---|---|---|---|']
    for yy in years[::4] + [years[-1]]:
        out.append(f'| {yy} | ' + ' | '.join(f'{S.mean(cat[c][yy]):.1f}' if cat[c][yy] else '—'
                                             for c in ('major', 'flagship', 'standard', 'national_open', 'opportunity')) + ' |')

    text = '\n'.join(out) + '\n'
    (ROOT / 'reports').mkdir(exist_ok=True)
    (ROOT / 'reports' / 'WORLD_HISTORY_REPORT.md').write_text(text, encoding='utf8')
    print(text[:5000])


if __name__ == '__main__':
    main()
