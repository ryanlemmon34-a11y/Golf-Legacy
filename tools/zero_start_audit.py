"""Who played no event all season, and why: a read-only audit of an archive (roadmap v14: investigate the
full-time amateur zero-start rate by region, affordable eligible options and admission before proposing any
change; never force starts or add money).

    python tools/zero_start_audit.py WORLD_OR_ARCHIVE_DIR [--years 2040-2052] [--out report.md]

For every person-season it reads the archived season row (status, lifestyle, tour, events) and the weekly
evidence (golfsim.access: played, injured, barriers -- not admitted, no suitable event, not eligible,
unaffordable -- and choices -- declined, trained, rested or worked, counted only when an affordable event
they could enter existed). Nothing is simulated or changed.
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
                'by_region': by_region, 'by_tour': by_tour, 'examples': examples, 'with_choice': with_choice}


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
    out.append('\n## Examples (barriers involved)\n')
    for c, ex in r['examples'].items():
        for y, pid, name, tour, text in ex:
            out.append(f'- {y} {name} (#{pid}, {c}, {tour}): {text}')
    out.append('\nReading it: "Choices only" means an affordable event they could enter existed every week they did not '
               'play; anything with barrier weeks is not voluntary. A barrier is a fact of that week (no event nearby, '
               'not eligible, could not afford it, field full), not proof that the rules or the money are wrong: '
               'compare cohorts and regions before proposing a change.')
    return '\n'.join(out) + '\n'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('world')
    ap.add_argument('--years')
    ap.add_argument('--out')
    a = ap.parse_args()
    d = Path(a.world)
    d = d / 'archive' if (d / 'archive').is_dir() else d
    years = None
    if a.years:
        lo, hi = (int(x) for x in a.years.split('-'))
        years = set(range(lo, hi + 1))
    text = report(audit(d, years))
    if a.out:
        Path(a.out).write_text(text)
    print(text)


if __name__ == '__main__':
    main()
