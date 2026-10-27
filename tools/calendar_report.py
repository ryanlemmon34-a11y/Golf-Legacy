"""World calendar report: writes reports/CALENDAR_REPORT.md.

    python tools/calendar_report.py [--year 2027]
"""
from __future__ import annotations

import argparse
import random
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from golfsim import qualification as Q                                    # noqa: E402
from golfsim.calendar import MAJOR_WEEKS, TIERS, TOUR_BY_KEY, WorldCalendar   # noqa: E402
from golfsim.course import ashford_ridge                                  # noqa: E402
from golfsim.engine import play_round                                     # noqa: E402
from golfsim.geography import COUNTRIES                                   # noqa: E402
from golfsim.golfer import uniform_golfer                                 # noqa: E402

TIER_SHORT = {0: 'Maj', 1: 'Prem', 2: 'Chal', 3: 'Reg', 4: 'Mini', 5: 'Coll', 6: 'Am', 7: 'Qual'}
# Planned mid-scale population (requirements R06): golfers available to fill each level.
POPULATION = {'Premier': 500, 'Challenger': 900, 'Regional': 1400, 'Mini': 1200, 'College': 900, 'Amateur': 1100}


def holes_played(s):
    """Expected competitive holes for one edition (all sites), counting cuts and match play."""
    n = s.field * s.sites
    if s.match_play:
        return n * 36 + 63 * 18 * 1.15
    if s.cut_top:
        return n * 36 + min(n, s.cut_top * 1.1) * (s.holes - 36)
    return n * s.holes


def us_per_hole(rating, rounds=400):
    g, c, rng = uniform_golfer(rating), ashford_ridge(), random.Random(rating)
    t = time.perf_counter()
    for _ in range(rounds):
        play_round(g, c, rng)
    return (time.perf_counter() - t) / (rounds * 18) * 1e6


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--year', type=int, default=2027)
    a = ap.parse_args()
    cal = WorldCalendar()
    eds = cal.editions(a.year)
    errors = cal.validate(a.year)
    out = ['# Golf Legacy — World Calendar', '',
           f'{len(cal.series)} permanent event series; {a.year} editions shown. Calendar checks: '
           f'**{"all passed" if not errors else f"{len(errors)} problems"}**.', '',
           '**The four majors own their weeks: no other competitive golf anywhere in the world in weeks 18, 24, 25 and 30.**', '',
           '| Week | Major |', '|---|---|']
    for e in eds:
        if e.series.kind == 'major':
            out.append(f'| {e.week} | **{e.series.name}** — {e.city} ({e.series.field}-player field) |')

    # ---- summary by level -------------------------------------------------------------------------
    out += ['', '## Events by level', '',
            '| Level | Event series | Lengths (18 / 36 / 54 / 72 holes) | Field places per season | Planned golfers | Starts per golfer |',
            '|---|---|---|---|---|---|']
    for tier, label in TIERS.items():
        ss = [s for s in cal.series if s.tier == tier]
        lengths = Counter(s.holes for s in ss)
        places = sum(s.field * s.sites for s in ss)
        pop = POPULATION.get(label)
        per = f'{places / pop:.1f}' if pop else '—'
        out.append(f'| {label} | {len(ss)} | {" / ".join(str(lengths.get(h, 0)) for h in (18, 36, 54, 72))} | '
                   f'{places:,} | {pop or "—"} | {per} |')
    out.append('\n"Starts per golfer" = field places ÷ planned golfers at that level. Golfers also play up and down '
               'levels (amateurs in qualifiers, pros in national opens), so this is a capacity check, not a schedule.')

    # ---- tours ------------------------------------------------------------------------------------
    out += ['', '## Tours', '', '| Tour | Level | Real-life analogue | Events | Season (weeks) | Field | Formats |',
            '|---|---|---|---|---|---|---|']
    analogue = {'PT_AMERICAS': 'PGA Tour', 'PT_EUROPE': 'DP World Tour', 'PT_ASIA_PACIFIC': 'DP World / Asian swing',
                'CH_AMERICAS': 'Korn Ferry Tour', 'CH_EUROPE': 'Challenge Tour', 'CH_ASIA': 'Asian Tour',
                'CH_LATAM_CANADA': 'PGA Tour Americas', 'CH_JAPAN': 'Japan Golf Tour', 'RG_SOUTHERN_AFRICA': 'Sunshine Tour',
                'RG_AUSTRALASIA': 'PGA Tour of Australasia', 'RG_KOREA': 'KPGA Tour', 'RG_INDIA': 'PGTI',
                'RG_CHINA': 'China Tour', 'RG_MENA': 'MENA Tour', 'CO_US_D1': 'NCAA Division I',
                'CO_US_SMALL': 'NCAA D2/D3, NAIA', 'CO_INTL': 'University golf worldwide'}
    for key, tour in TOUR_BY_KEY.items():
        ss = [s for s in cal.series if s.tour == key]
        weeks = sorted({s.week for s in ss})
        fmts = Counter(s.holes for s in ss)
        out.append(f'| {tour.name} | {TIERS[tour.tier]} | {analogue.get(key, "regional mini tour" if tour.tier == 4 else "state/county/national amateur golf" if tour.tier == 6 else "")} '
                   f'| {len(ss)} | {weeks[0]}–{weeks[-1]} | {tour.field} | {", ".join(f"{n}×{h}" for h, n in sorted(fmts.items()))} |')

    # ---- week by week ------------------------------------------------------------------------------
    out += ['', '## Week by week', '', '| Week | ' + ' | '.join(TIER_SHORT[t] for t in TIERS) + ' | Total | Highlights |',
            '|---|' + '---|' * (len(TIERS) + 2)]
    for w in range(1, 53):
        week = [e for e in eds if e.week == w]
        c = Counter(e.series.tier for e in week)
        hi = [e.series.name for e in week if e.series.kind == 'major' or e.series.category in
              ('flagship', 'elite_amateur', 'national_open') and e.series.tier <= 2 or e.series.category == 'qualifier'
              or e.series.category == 'college_postseason' and 'National' in e.series.name]
        name = f'**{week[0].series.name}**' if w in MAJOR_WEEKS else '; '.join(hi[:4]) + (' …' if len(hi) > 4 else '')
        out.append(f'| {w} | ' + ' | '.join(str(c.get(t, '')) for t in TIERS) + f' | {len(week)} | {name} |')

    # ---- where golf is played ----------------------------------------------------------------------
    by_country = defaultdict(list)
    simultaneous = defaultdict(int)
    for year in range(a.year, a.year + 10):
        per_city_week = Counter((e.city, e.week) for e in cal.editions(year))
        for (city, _), n in per_city_week.items():
            simultaneous[city] = max(simultaneous[city], n)
    cities_used = defaultdict(set)
    for s in cal.series:
        by_country[s.host_country].append(s)
        for c in s.cities:
            cities_used[c].add(s.series_id)
    out += ['', '## Where the golf is played', '',
            'Every event series has a host country and a pool of real host cities (rotating events move each year). '
            'This is the input for the course library: every city below needs fictional courses.', '',
            '| Country | Region | Event series | Host cities | Min. courses needed* |', '|---|---|---|---|---|']
    total_min = 0
    rows = []
    for country, ss in by_country.items():
        cities = {c for s in ss for c in s.cities}
        need = sum(simultaneous[c] or 1 for c in cities)
        total_min += need
        rows.append((len(ss), country, COUNTRIES[country].region, len(cities), need))
    for n, country, region, nc, need in sorted(rows, reverse=True):
        out.append(f'| {country} | {region} | {n} | {nc} | {need} |')
    out.append(f'\n\\*Minimum = the most events any city hosts in the same week (over 10 seasons of rotation), summed over cities: '
               f'**{total_min} courses** just to stage the calendar. A living world needs several times that — '
               'home clubs, practice venues and variety — which is the target for the course library.')

    # ---- every-shot workload -------------------------------------------------------------------------
    pro, am = us_per_hole(75), us_per_hole(15)
    out += ['', '## Every-shot workload per season', '',
            '| Level | Competitive holes per season | Est. time, one core | Est. time, 4 cores |', '|---|---|---|---|']
    total_h = total_t = 0
    for tier, label in TIERS.items():
        h = sum(holes_played(s) for s in cal.series if s.tier == tier)
        cost = am if tier in (4, 5, 6, 7) else pro
        t = h * cost / 1e6
        total_h += h
        total_t += t
        out.append(f'| {label} | {h:,.0f} | {t:.0f} s | {t / 4:.0f} s |')
    out.append(f'| **All** | **{total_h:,.0f}** | **{total_t / 60:.1f} min** | **{total_t / 240:.1f} min** |')
    out.append(f'\nMeasured engine speed on this machine: {pro:.0f} µs per hole for a tour pro, {am:.0f} µs for a weaker '
               'amateur (more shots per hole). The 4-core column assumes the week\'s independent events run in parallel '
               '(planned). Golf only — season logic, rankings and saving history add to this.')

    # ---- qualification ------------------------------------------------------------------------------
    out += ['', '## How players get into the majors', '']
    for major in Q.MAJOR_SERIES:
        s = cal.by_id[major]
        out += [f'### {s.name} — week {s.week} ({Q.FIELD_SIZE[major] or "invitation only, about 90"} players)', '',
                '| # | Route | Real-life analogue | Type |', '|---|---|---|---|']
        for i, r in enumerate(Q.RULES[major], 1):
            kind = {'exempt': 'Exempt', 'qualifying': 'Qualifying places', 'fill': 'Fills remaining places'}[r.kind]
            extra = ' (amateurs only)' if r.amateur_only else ' (club professionals)' if r.status == 'club_pro' else ''
            out.append(f'| {i} | {r.label}{extra} | {r.analogue} | {kind} |')
        out.append('')
    out += ['Qualifying stages feeding the final qualifiers:', '']
    for final, info in Q.STAGES.items():
        out.append(f'- **{cal.by_id[final].name}** (week {cal.by_id[final].week}): fed by '
                   + ', '.join(f'{cal.by_id[f].name}' for f in info['feeders'])
                   + f' — {info["per_site"]} advance per site. Exempt from the earlier stage: {info["exempt_from_earlier"]}.')
    if errors:
        out += ['', '## Calendar problems', ''] + [f'- {e}' for e in errors]
    text = '\n'.join(out) + '\n'
    (ROOT / 'reports').mkdir(exist_ok=True)
    (ROOT / 'reports' / 'CALENDAR_REPORT.md').write_text(text, encoding='utf8')
    print(text[:6000])


if __name__ == '__main__':
    main()
