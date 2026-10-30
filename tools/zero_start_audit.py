"""Who played no event all season, and why: a read-only audit of an archive (roadmap v14: investigate the
full-time amateur zero-start rate by region, affordable eligible options and admission before proposing any
change; never force starts or add money).

    python tools/zero_start_audit.py WORLD_OR_ARCHIVE_DIR [--years 2040-2052] [--out report.md] [--save]

For every person-season it reads the archived season row (status, lifestyle, tour, events) and the weekly
evidence (golfsim.access: played, injured, barriers -- not admitted, no suitable event, not eligible,
unaffordable -- and choices -- declined, trained, rested or worked, counted only when an affordable event
they could enter existed). Full-time amateurs are also broken down by home region and circuit together, with
every week's cause. --save (a world folder) adds the affordability evidence the archive does not keep: the world's
committed save is read (never written) and each full-time amateur's spendable funds at that moment are set against
the cheapest trip to an event of their own circuit that season, by the engine's own cost and funds rules
(Season.trip_cost, Season.spendable). Nothing is simulated or changed.
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from golfsim import access as ACC                                        # noqa: E402
from golfsim.archive import Archive                                      # noqa: E402
from golfsim.geography import COUNTRIES                                  # noqa: E402


def cohort(row):
    st, life, tier = row.get('status'), row.get('lifestyle'), row.get('tier')
    if life == 'retired':
        return None
    if (row.get('tour') or '').startswith('CO_'):
        return 'college'
    if st == 'amateur':
        return f'{"full-time" if life == "full_time" else "part-time"} amateur'
    if st == 'club_pro':
        return 'club professional'
    level = {1: 'Premier', 2: 'Challenger', 3: 'Regional', 4: 'Mini'}.get(tier, 'other')
    return f'{"full-time" if life == "full_time" else "part-time"} {level}'


def region(row, people, pid):
    res = row.get('residence')                      # [country, region] where they lived that season
    country = (res[0] if res else None) or (people.get(pid) or {}).get('country')
    return COUNTRIES[country].region if country in COUNTRIES else 'unknown'


def audit(archive_dir, years=None):
    with Archive(archive_dir) as a:
        ys = [y for y in a.years if years is None or y in years]
        totals = Counter()
        zeros = Counter()
        kinds = defaultdict(Counter)
        causes = defaultdict(Counter)            # cohort -> group -> weeks (zero-start seasons only)
        weeks = Counter()
        by_region = defaultdict(lambda: [0, 0])  # (cohort, region) -> [seasons, zero]
        by_tour = defaultdict(lambda: [0, 0])
        examples = defaultdict(list)
        with_choice = Counter()                  # zero-start seasons with at least one choice week
        cells = defaultdict(lambda: {'seasons': 0, 'zero': 0, 'weeks': Counter(), 'all_weeks': Counter()})
        for y in ys:
            careers = a.year(y)['careers']
            for pid, row in careers.items():
                c = cohort(row)
                if c is None:
                    continue
                totals[c] += 1
                reg = region(row, a.people, pid)
                by_region[(c, reg)][0] += 1
                by_tour[(c, row.get('tour'))][0] += 1
                if c == 'full-time amateur':             # region and circuit together, every week's cause
                    cell = cells[(reg, row.get('tour'))]
                    cell['seasons'] += 1
                    lg_ = ACC.ledger(row.get('access'))
                    cell['all_weeks']['recorded'] += lg_['weeks']
                    cell['all_weeks']['played'] += lg_['played']
                    cell['all_weeks']['injured'] += lg_['injured']
                    for g_, n_ in lg_['groups'].items():
                        cell['all_weeks'][g_] += n_
                    if not row.get('events'):
                        cell['zero'] += 1
                        cell['weeks']['recorded'] += lg_['weeks']
                        cell['weeks']['injured'] += lg_['injured']
                        for g_, n_ in lg_['groups'].items():
                            cell['weeks'][g_] += n_
                if row.get('events'):
                    continue
                zeros[c] += 1
                by_region[(c, reg)][1] += 1
                by_tour[(c, row.get('tour'))][1] += 1
                kind, text = ACC.zero_start_summary(row.get('access'), row.get('injury_weeks') or 0, row.get('lifestyle'))
                kinds[c][kind] += 1
                lg = ACC.ledger(row.get('access'))
                weeks[c] += lg['weeks']
                for g, n in lg['groups'].items():
                    causes[c][g] += n
                causes[c]['injured'] += lg['injured']
                with_choice[c] += lg['choice'] > 0
                if len(examples[c]) < 6 and kind in ('mixed', 'barriers'):
                    examples[c].append((y, pid, a.name(pid), row.get('tour'), text))
        return {'years': ys, 'totals': totals, 'zeros': zeros, 'kinds': kinds, 'causes': causes, 'weeks': weeks,
                'by_region': by_region, 'by_tour': by_tour, 'examples': examples, 'with_choice': with_choice,
                'cells': cells}


def report(r):
    out = [f'# Zero-start seasons: who and why\n',
           f'Seasons {r["years"][0]}-{r["years"][-1]} ({len(r["years"])}), read-only. A zero-start season is a season row '
           'with no event. Causes are weeks (golfsim.access), so shares are of the weeks those golfers recorded.\n',
           '| Cohort | Seasons | No starts | Share | Kept out only by barriers | Barriers and choices | '
           'Choices only | Mostly injured |', '|---|---|---|---|---|---|---|---|']
    for c in sorted(r['totals'], key=lambda c: -r['totals'][c]):
        n, z = r['totals'][c], r['zeros'][c]
        k = r['kinds'][c]
        out.append(f'| {c} | {n:,} | {z:,} | {100 * z / n:.2f}% | {k["barriers"]} | {k["mixed"]} | {k["choices"]} | '
                   f'{k["injured"]} |')
    out.append('\n## Weeks of the zero-start seasons, by cause\n')
    out.append('| Cohort | Weeks | ' + ' | '.join(['injured'] + list(ACC.BARRIERS) + list(ACC.CHOICES)) + ' |')
    out.append('|---|---|' + '---|' * (1 + len(ACC.BARRIERS) + len(ACC.CHOICES)))
    for c in sorted(r['zeros'], key=lambda c: -r['zeros'][c]):
        n = r['weeks'][c] or 1
        cells = [f'{100 * r["causes"][c][g] / n:.0f}%' for g in ['injured'] + list(ACC.BARRIERS) + list(ACC.CHOICES)]
        out.append(f'| {c} | {r["weeks"][c]:,} | ' + ' | '.join(cells) + ' |')
    out.append('\n## Full-time amateurs by region (where they live)\n')
    out.append('| Region | Seasons | No starts | Share |')
    out.append('|---|---|---|---|')
    for (c, reg), (n, z) in sorted(r['by_region'].items(), key=lambda kv: -kv[1][1]):
        if c == 'full-time amateur':
            out.append(f'| {reg} | {n:,} | {z:,} | {100 * z / n:.1f}% |')
    out.append('\n## Full-time amateurs by circuit\n')
    out.append('| Circuit | Seasons | No starts | Share |')
    out.append('|---|---|---|---|')
    for (c, tour), (n, z) in sorted(r['by_tour'].items(), key=lambda kv: -kv[1][1])[:40]:
        if c == 'full-time amateur' and z:
            out.append(f'| {tour} | {n:,} | {z:,} | {100 * z / n:.1f}% |')
    causes_ = ['injured'] + list(ACC.BARRIERS) + list(ACC.CHOICES)
    out.append('\n## Full-time amateurs by region and circuit: the weeks of their zero-start seasons\n')
    out.append('Each cause as a share of the weeks those zero-start seasons recorded (a golfer is counted under the '
               'region they lived in that season and the circuit of their season row).\n')
    out.append('| Region | Circuit | Seasons | No starts | Share | Weeks | ' + ' | '.join(causes_) + ' |')
    out.append('|---|---|---|---|---|---|' + '---|' * len(causes_))
    for (reg, tour), c_ in sorted(r['cells'].items(), key=lambda kv: (-kv[1]['zero'], kv[0][0], str(kv[0][1]))):
        if not c_['zero']:
            continue
        n = c_['weeks']['recorded'] or 1
        out.append(f'| {reg} | {tour} | {c_["seasons"]:,} | {c_["zero"]:,} | {100 * c_["zero"] / c_["seasons"]:.1f}% | '
                   f'{c_["weeks"]["recorded"]:,} | ' + ' | '.join(f'{100 * c_["weeks"][g] / n:.0f}%' for g in causes_) + ' |')
    out.append('\n## Full-time amateurs by region and circuit: every season\'s weeks (those who played too)\n')
    out.append('| Region | Circuit | Seasons | Weeks | played | ' + ' | '.join(causes_) + ' |')
    out.append('|---|---|---|---|---|' + '---|' * len(causes_))
    for (reg, tour), c_ in sorted(r['cells'].items(), key=lambda kv: (-kv[1]['seasons'], kv[0][0], str(kv[0][1])))[:40]:
        n = c_['all_weeks']['recorded'] or 1
        out.append(f'| {reg} | {tour} | {c_["seasons"]:,} | {c_["all_weeks"]["recorded"]:,} | '
                   f'{100 * c_["all_weeks"]["played"] / n:.0f}% | '
                   + ' | '.join(f'{100 * c_["all_weeks"][g] / n:.0f}%' for g in causes_) + ' |')
    out.append('\n## Examples (barriers involved)\n')
    for c, ex in r['examples'].items():
        for y, pid, name, tour, text in ex:
            out.append(f'- {y} {name} (#{pid}, {c}, {tour}): {text}')
    out.append('\nReading it: "Choices only" means an affordable event they could enter existed every week they did not '
               'play; anything with barrier weeks is not voluntary. A barrier is a fact of that week (no event nearby, '
               'not eligible, could not afford it, field full), not proof that the rules or the money are wrong: '
               'compare cohorts and regions before proposing a change.')
    return '\n'.join(out) + '\n'


def affordability(world_dir):
    """From a world's committed save (read only): full-time amateurs (college golfers aside) by home region and
    circuit -- how many, their spendable funds at that moment, the cheapest trip to an event of their own circuit
    that season, and how many cannot afford even that one. The engine's own rules: Season.spendable (funds less
    four weeks of committed costs) and Season.trip_cost (travel and fees, or nothing when a school or club pays)."""
    import statistics
    from golfsim import session as SES
    gen, s, state = SES._load_committed(Path(world_dir), True)
    year = state.get('cursor', {}).get('year') if isinstance(state, dict) else None
    year = year or getattr(s, 'year', None) or max(s.ledgers)
    eds = defaultdict(list)
    for ed in s.cal.editions(year):
        eds[ed.series.tour].append(ed)
    rows = defaultdict(lambda: {'n': 0, 'spend': [], 'cheap': [], 'short': 0, 'none': 0, 'family': []})
    split = defaultdict(lambda: {'n': 0, 'spend': [], 'short': 0, 'no_family': 0, 'debt': 0, 'living': [],
                                 'events': [], 'work': [], 'support': []})
    last = {}
    arch = Path(world_dir) / 'archive'
    if arch.is_dir():                                   # their last archived season: played or not
        with Archive(arch) as a:
            if year - 1 in a.years:
                last = {pid: bool(r.get('events')) for pid, r in a.year(year - 1)['careers'].items()}
    for g in s.world.golfers:
        if g.status != 'amateur' or g.lifestyle != 'full_time' or (g.tour or '').startswith('CO_'):
            continue
        reg = s.home_region(g)
        r = rows[(reg, g.tour)]
        r['n'] += 1
        spend = s.spendable(g, year)
        r['spend'].append(spend)
        r['family'].append(g.backing)
        costs = [s.trip_cost(g, ed.series, ed.city) for ed in eds.get(g.tour, ())]
        if not costs:
            r['none'] += 1
            continue
        cheap = min(costs)
        r['cheap'].append(cheap)
        r['short'] += cheap > 0 and cheap > spend
        if g.id in last:
            k = (reg, 'played' if last[g.id] else 'no starts')
            sp_ = split[k]
            sp_['n'] += 1
            sp_['spend'].append(spend)
            sp_['short'] += cheap > 0 and cheap > spend
            sp_['no_family'] += g.backing <= 0
            sp_['debt'] += g.cash < 0
            led = s.ledgers.get(year - 1, {}).get(g.id)        # what last season cost them, and what came in
            if led is not None:
                for k_ in ('living', 'events', 'work', 'support'):
                    sp_[k_].append(getattr(led, k_))
    med = lambda xs: statistics.median(xs) if xs else None
    out = {'year': year, 'generation': gen, 'rows': {}, 'split': {}}
    for k, r in split.items():
        out['split'][k] = {'n': r['n'], 'spend': med(r['spend']), 'short': r['short'], 'no_family': r['no_family'],
                           'debt': r['debt'], **{k_: med(r[k_]) for k_ in ('living', 'events', 'work', 'support')}}
    for k, r in rows.items():
        out['rows'][k] = {'n': r['n'], 'spend': med(r['spend']), 'cheap': med(r['cheap']), 'short': r['short'],
                          'none': r['none'], 'family': med(r['family'])}
    return out


def affordability_report(a):
    out = [f'\n## Affordability at the start of {a["year"]} (the committed save, generation {a["generation"]}, read only)\n',
           'Full-time amateurs (college golfers aside) by home region and circuit: spendable funds (the engine\'s '
           'own rule: cash, family support left, backers and credit, less four weeks of committed costs) against the '
           'cheapest trip to an event of their own circuit that season (travel and fees).\n',
           '| Region | Circuit | Golfers | Median spendable | Median cheapest own-circuit trip | Cannot afford even that | '
           'Median family support left | No event of their circuit |', '|---|---|---|---|---|---|---|---|']
    f = lambda x: '—' if x is None else f'${x:,.0f}'
    for (reg, tour), r in sorted(a['rows'].items(), key=lambda kv: (kv[0][0], str(kv[0][1]))):
        share = f'{r["short"]} ({100 * r["short"] / r["n"]:.0f}%)' if r['n'] else '0'
        out.append(f'| {reg} | {tour} | {r["n"]} | {f(r["spend"])} | {f(r["cheap"])} | {share} | {f(r["family"])} | '
                   f'{r["none"]} |')
    if a['split']:
        out += ['', f'The same golfers by whether their {a["year"] - 1} season (the last archived) had a start:', '',
                '| Region | Last season | Golfers | Median spendable | Cannot afford their cheapest trip | No family support '
                'left | In debt | Median living costs | Median event costs | Median work income | Median family '
                'support drawn |', '|---|---|---|---|---|---|---|---|---|---|---|']
        pct = lambda n, d: f'{n} ({100 * n / d:.0f}%)' if d else '0'
        for (reg, kind), r in sorted(a['split'].items()):
            out.append(f'| {reg} | {kind} | {r["n"]} | {f(r["spend"])} | {pct(r["short"], r["n"])} | '
                       f'{pct(r["no_family"], r["n"])} | {pct(r["debt"], r["n"])} | {f(r["living"])} | {f(r["events"])} | '
                       f'{f(r["work"])} | {f(r["support"])} |')
    return '\n'.join(out) + '\n'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('world')
    ap.add_argument('--years')
    ap.add_argument('--out')
    ap.add_argument('--save', action='store_true', help='also read the committed save (read only) for affordability')
    a = ap.parse_args()
    d = Path(a.world)
    world = d
    d = d / 'archive' if (d / 'archive').is_dir() else d
    years = None
    if a.years:
        lo, hi = (int(x) for x in a.years.split('-'))
        years = set(range(lo, hi + 1))
    text = report(audit(d, years))
    if a.save:
        text += affordability_report(affordability(world))
    if a.out:
        Path(a.out).write_text(text)
    print(text)


if __name__ == '__main__':
    main()
