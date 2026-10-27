"""Build the world course library: rate every layout, write data files and the report.

    python tools/build_course_library.py [--rounds 100] [--demo-years 10]

Writes:
    data/layout_ratings.json       simulated scoring for every layout (read by the library)
    data/course_library.json       every course, its layouts and hole-by-hole card
    reports/COURSE_LIBRARY_REPORT.md
"""
from __future__ import annotations

import argparse
import json
import random
import statistics as S
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from golfsim.calendar import MAJOR_VENUES, TIERS                                   # noqa: E402
from golfsim.course_library import (RATINGS_FILE, default_library, event_level,     # noqa: E402
                                    fingerprint, rate_layout)
from golfsim.golfer import ARCHETYPES, archetype_golfer                             # noqa: E402
from golfsim.records import RecordBook                                              # noqa: E402
from golfsim.tournament import play_event, play_stroke_and_match                    # noqa: E402

CLASS_LABEL = {'elite': 'Elite', 'championship': 'Championship', 'standard': 'Standard', 'municipal': 'Municipal'}
LAYOUT_ORDER = ('Championship', 'Club', 'Forward', 'Regular')
# Demo field strength by tier (mean overall, sd): stand-ins until real populations exist.
TIER_FIELD = {0: (80, 5), 1: (76, 4.5), 2: (67, 4.5), 3: (61, 5), 4: (54, 6), 5: (42, 7), 6: (33, 8), 7: (52, 9)}
FIRST = ('James', 'Liam', 'Lucas', 'Mateo', 'Noah', 'Oliver', 'Ethan', 'Hugo', 'Kenji', 'Min-jun', 'Rory', 'Shane',
         'Tomás', 'Viktor', 'Wei', 'Arjun', 'Callum', 'Diego', 'Erik', 'Felix', 'Hiro', 'Jack', 'Kai', 'Louis', 'Nico',
         'Owen', 'Pablo', 'Rafael', 'Sam', 'Theo', 'Will', 'Yuto', 'Zach', 'Adam', 'Ben', 'Connor', 'Dylan', 'Finn')
LAST = ('Archer', 'Barnes', 'Castillo', 'Dalton', 'Eriksen', 'Fowler', 'Garza', 'Hale', 'Ito', 'Jensen', 'Kim',
        'Lindqvist', 'McAllister', 'Navarro', "O'Brien", 'Park', 'Quinn', 'Reyes', 'Sato', 'Thorne', 'Uribe', 'Vance',
        'Walsh', 'Xu', 'Young', 'Zimmer', 'Brennan', 'Coetzee', 'Duval', 'Esposito', 'Fischer', 'Grant', 'Holm')


def _rate(args):
    lid, rounds = args
    return lid, rate_layout(default_library().course(lid), rounds)


def rate_all(lib, rounds):
    jobs = [(c.layout_id, rounds) for _, _, c in lib.layouts()]
    with ProcessPoolExecutor() as ex:
        return dict(ex.map(_rate, jobs, chunksize=8))


def fmt_par(x):
    return 'E' if abs(x) < 0.05 else f'{x:+.1f}'


def scorecard(course, ratings):
    r = ratings[course.layout_id]
    lines = [f'**{course.name}** — {course.layout} layout: par {course.par}, {course.yards:,} yards. '
             f'Tour average {r["tour"]:.1f} ({fmt_par(r["difficulty"])}), amateur event winner {r["amateur_winner"]:.1f}, '
             f'amateur {r["amateur"]:.1f}.', '',
             '| Hole | Par | Yards | Fairway | Rough | Left / right | Green (radius, stimp, slope) | Notes |',
             '|---|---|---|---|---|---|---|---|']
    for h in course.holes:
        lines.append(f'| {h.number} | {h.par} | {h.yards} | {h.fairway_width:.0f} yd | {h.rough_severity:.2f} | '
                     f'{h.left} / {h.right} | {h.green_radius:.1f} yd, {h.green_speed:.1f}, {h.green_slope:.2f} | {h.note} |')
    return lines


def demo_records(lib, years):
    """Play every event at the busiest multi-layout course for `years` seasons; keep its records."""
    usage = Counter()
    for y in range(lib.first_year, lib.first_year + years):
        for eid, vs in lib.venues(y).items():
            for v in vs:
                if len(lib.sites[v.course_id]['layouts']) >= 2:
                    usage[v.course_id] += 1
    cid = max(usage, key=lambda c: (len({lv for y in range(lib.first_year, lib.first_year + years)
                                         for eid, vs in lib.venues(y).items() for v in vs if v.course_id == c
                                         for lv in [v.layout]}), usage[c]))
    book = RecordBook()
    rng = random.Random(7)
    played = []
    arche = list(ARCHETYPES)
    for y in range(lib.first_year, lib.first_year + years):
        for eid, vs in lib.venues(y).items():
            for v in vs:
                if v.course_id != cid:
                    continue
                s = lib.calendar.by_id[eid.split(':', 1)[1]]
                course = lib.course(v)
                mean, sd = TIER_FIELD[s.tier]
                n = s.field // max(1, s.sites) if s.sites > 1 else s.field
                field = [archetype_golfer(rng.choice(arche), max(5, min(98, rng.gauss(mean, sd))),
                                          f'{rng.choice(FIRST)} {rng.choice(LAST)}') for _ in range(n)]
                rec = book.round_recorder(course, eid, y, s.week, s.tier)
                if s.match_play:
                    play_stroke_and_match(field, course, rng, on_round=rec)
                else:
                    board, _ = play_event(field, course, rng, cut_top=s.cut_top or len(field),
                                          rounds_n=s.rounds, cut_after=2 if s.cut_top else None, on_round=rec)
                    book.add_event(course, board, s.holes, eid, y, s.week, s.tier)
                played.append((y, s.week, s.name, TIERS[s.tier], v.layout))
    return cid, book, played


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--rounds', type=int, default=100)
    ap.add_argument('--demo-years', type=int, default=10)
    a = ap.parse_args()
    t0 = time.perf_counter()
    lib = default_library()
    errors = lib.validate(10)
    ratings = rate_all(lib, a.rounds)
    (ROOT / 'data').mkdir(exist_ok=True)
    (ROOT / RATINGS_FILE).write_text(json.dumps(ratings, indent=0, sort_keys=True), encoding='utf8')
    export = []
    for cid, site in lib.sites.items():
        base = next(iter(site['layouts'].values()))          # Championship (or Regular) tees
        lays = {}
        for key, c in site['layouts'].items():
            # other layouts differ only in yardage and set-up: store just what changes per hole
            lays[key] = dict(layout_id=c.layout_id, par=c.par, yards=c.yards, rating=ratings[c.layout_id],
                             hole_yards=[h.yards for h in c.holes], green_speed=[h.green_speed for h in c.holes],
                             rough_severity=[h.rough_severity for h in c.holes],
                             green_firmness=[h.green_firmness for h in c.holes])
        export.append({k: v for k, v in site.items() if k not in ('layouts', 'hand_built')}
                      | {'holes': [asdict(h) for h in base.holes], 'layouts': lays})
    (ROOT / 'data' / 'course_library.json').write_text(json.dumps(export, ensure_ascii=False, separators=(',', ':')),
                                                       encoding='utf8')
    t_rate = time.perf_counter() - t0

    sites = list(lib.sites.values())
    out = ['# Golf Legacy — World Course Library', '',
           f'**{len(sites)} fictional courses** in {len({s["city"] for s in sites})} real cities across '
           f'{len({s["country"] for s in sites})} countries, with **{sum(len(s["layouts"]) for s in sites)} layouts**. '
           f'Every layout rated by simulation ({a.rounds} rounds per level, {t_rate:.0f} s to build and rate). '
           f'Venue checks over 10 seasons: **{"all passed" if not errors else f"{len(errors)} problems"}**.', '',
           'Courses are generated from the calendar: ten seasons are replayed and every event (and every site of a '
           'multi-site qualifier) needs a free course of the right standard in its host city that week. That sets the '
           'minimum; the rest of the 380 are extra clubs where golf is busiest.', '']

    # ---- classes and layouts ---------------------------------------------------------------------
    out += ['## Classes and layouts', '',
            '| Class | Courses | Layouts | Who plays there |', '|---|---|---|---|']
    who = {'elite': 'Majors and the Premier Tour only. One layout.',
           'championship': 'Premier Tour, Challenger tours, national opens (Championship); regional, mini and college events (Club).',
           'standard': 'Challenger, regional, mini, college, national amateurs (Championship); mini and amateur events (Club); 18-36 hole amateur events (Forward).',
           'municipal': 'Regional amateur and small events (Regular); junior golf (Forward).'}
    for cls in CLASS_LABEL:
        ss = [s for s in sites if s['cls'] == cls]
        combos = Counter(' + '.join(s['layouts']) for s in ss)
        out.append(f'| {CLASS_LABEL[cls]} | {len(ss)} | {"; ".join(f"{k} ({n})" for k, n in combos.most_common())} | {who[cls]} |')
    std = [s for s in sites if s['cls'] == 'standard']
    out.append(f'\nEasier layouts for lower tours: every Championship and Standard course has a Club layout, and '
               f'{sum("Forward" in s["layouts"] for s in std)} of the {len(std)} Standard courses also have Forward tees. '
               'The Club layout plays about 7% shorter with greens a foot slower and lighter rough; Forward plays about '
               '14% shorter. Same holes, same hazards.')

    # ---- how layouts play --------------------------------------------------------------------------
    out += ['', '## How each layout plays', '',
            'Average score to par for uniform golfers at each level (calm weather). Ranges show the easiest and hardest '
            'course of each kind.', '',
            '| Class | Layout | Layouts | Yards (avg) | Tour pro (75) | Amateur winner (40) | Amateur (25) | High schooler (10) |',
            '|---|---|---|---|---|---|---|---|']
    groups = defaultdict(list)
    for site, key, c in lib.layouts():
        groups[(site['cls'], key)].append(ratings[c.layout_id])
    for cls in CLASS_LABEL:
        for key in LAYOUT_ORDER:
            rs = groups.get((cls, key))
            if not rs:
                continue
            def col(level):
                v = [r[level] - r['par'] for r in rs]
                return f'{fmt_par(S.mean(v))} ({fmt_par(min(v))} to {fmt_par(max(v))})'
            out.append(f'| {CLASS_LABEL[cls]} | {key} | {len(rs)} | {S.mean(r["yards"] for r in rs):,.0f} | {col("tour")} | '
                       f'{col("amateur_winner")} | {col("amateur")} | {col("high_school")} |')

    # ---- styles and geography ---------------------------------------------------------------------
    out += ['', '## Styles', '', '| Style | Courses | Elite | Championship | Standard | Municipal |', '|---|---|---|---|---|---|']
    for style, n in Counter(s['style'] for s in sites).most_common():
        c = Counter(s['cls'] for s in sites if s['style'] == style)
        out.append(f'| {style} | {n} | {c["elite"]} | {c["championship"]} | {c["standard"]} | {c["municipal"]} |')
    out += ['', '## Where the courses are', '', '| Country | Courses | Cities | Elite | Championship | Standard | Municipal |',
            '|---|---|---|---|---|---|---|']
    for country, n in Counter(s['country'] for s in sites).most_common():
        ss = [s for s in sites if s['country'] == country]
        c = Counter(s['cls'] for s in ss)
        out.append(f'| {country} | {n} | {len({s["city"] for s in ss})} | {c["elite"]} | {c["championship"]} | '
                   f'{c["standard"]} | {c["municipal"]} |')

    # ---- the elite courses -------------------------------------------------------------------------
    major_city = {c: sid for sid, (_, cities, _) in MAJOR_VENUES.items() for c in cities}
    out += ['', '## The elite courses (majors and Premier Tour only)', '',
            '| Course | City | Style | Architect | Opened | Par | Yards | Tour avg | Major rota |', '|---|---|---|---|---|---|---|---|---|']
    elite = sorted((s for s in sites if s['cls'] == 'elite'), key=lambda s: -ratings[s['layouts']['Championship'].layout_id]['difficulty'])
    for s in elite:
        c = s['layouts']['Championship']
        r = ratings[c.layout_id]
        rota = major_city.get(s['city'], '')
        rota = {'TOUR_MASTERS': 'Tour Masters (every year)', 'PREMIER_TOUR_CHAMPIONSHIP': 'Premier Tour Championship',
                'USA_OPEN': 'USA Open', 'BRITANNIA_OPEN': 'Britannia Open'}.get(rota, '')
        out.append(f'| {s["name"]} | {s["city"]} | {s["style"]} | {s["architect"]} | {s["opened"]} | {c.par} | {c.yards:,} | '
                   f'{r["tour"]:.1f} ({fmt_par(r["difficulty"])}) | {rota} |')

    # ---- hardest and easiest -----------------------------------------------------------------------
    all_l = sorted(((ratings[c.layout_id], site, key) for site, key, c in lib.layouts()), key=lambda x: -x[0]['difficulty'])
    out += ['', '## Hardest and easiest layouts for tour pros', '', '| | Course | Layout | City | Par | Yards | Tour avg | Amateur (25) |',
            '|---|---|---|---|---|---|---|---|']
    for tag, rows in (('Hardest', all_l[:10]), ('Easiest', all_l[-10:])):
        for r, site, key in rows:
            out.append(f'| {tag} | {site["name"]} | {key} | {site["city"]} | {r["par"]} | {r["yards"]:,} | '
                       f'{r["tour"]:.1f} ({fmt_par(r["difficulty"])}) | {r["amateur"]:.1f} |')

    # ---- venue use ---------------------------------------------------------------------------------
    use = Counter()
    moved = Counter()
    for y in range(lib.first_year, lib.first_year + 10):
        for ed in lib.calendar.editions(y):
            for v in lib.venues(y)[ed.event_id]:
                use[(TIERS[ed.series.tier], CLASS_LABEL[lib.sites[v.course_id]['cls']], v.layout)] += 1
                if ed.series.sites == 1 and v.city != ed.city:
                    moved[TIERS[ed.series.tier]] += 1
    out += ['', '## Which layouts each level plays (10 seasons of venues)', '',
            '| Level | Course class | Layout | Event-sites |', '|---|---|---|---|']
    for (lvl, cls, lay), n in sorted(use.items(), key=lambda x: (list(TIERS.values()).index(x[0][0]), -x[1])):
        out.append(f'| {lvl} | {cls} | {lay} | {n:,} |')
    out.append('\nA series goes back to the same course whenever it is in the same city, so events build a history at '
               'their home venue. When a city\'s suitable courses are all booked that week, the event moves to another '
               f'city in its host pool ({sum(moved.values())} of {sum(use.values()):,} event-sites over 10 seasons).')

    # ---- sample scorecards ------------------------------------------------------------------------
    gn = lib.sites['georgia-national-golf-club']['layouts']['Championship']
    out += ['', '## Sample scorecards', ''] + scorecard(gn, ratings)
    three = next(s for s in sites if s['cls'] == 'standard' and 'Forward' in s['layouts'])
    out += ['', f'**{three["name"]}** ({three["city"]}, {three["style"]}, {three["architect"]} {three["opened"]}): one course, three layouts.', '',
            '| Layout | Par | Yards | Avg stimp | Avg rough | Tour avg | Amateur winner | Amateur | High schooler |',
            '|---|---|---|---|---|---|---|---|---|']
    for key, c in three['layouts'].items():
        r = ratings[c.layout_id]
        out.append(f'| {key} | {c.par} | {c.yards:,} | {S.mean(h.green_speed for h in c.holes):.1f} | '
                   f'{S.mean(h.rough_severity for h in c.holes):.2f} | {r["tour"]:.1f} | {r["amateur_winner"]:.1f} | '
                   f'{r["amateur"]:.1f} | {r["high_school"]:.1f} |')
    out += [''] + scorecard(three['layouts']['Championship'], ratings)

    # ---- records demo ------------------------------------------------------------------------------
    t1 = time.perf_counter()
    cid, book, played = demo_records(lib, a.demo_years)
    site = lib.sites[cid]
    out += ['', f'## Course records are kept per layout — {a.demo_years}-season demonstration', '',
            f'Every event the calendar sends to **{site["name"]}** ({site["city"]}) over {a.demo_years} seasons, played shot '
            f'by shot with stand-in fields of the right strength for each level ({len(played)} events, '
            f'{time.perf_counter() - t1:.0f} s). Each layout keeps its own records.', '',
            '| Year | Week | Event | Level | Layout |', '|---|---|---|---|---|']
    for row in played:
        out.append('| ' + ' | '.join(map(str, row)) + ' |')
    for key, c in site['layouts'].items():
        rec = book.layouts.get(c.layout_id)
        if not rec:
            continue
        out += ['', f'**{key} layout** (par {c.par}, {c.yards:,} yards) — {rec.rounds:,} competitive rounds, scoring average '
                f'{rec.scoring_average:.2f}.', '',
                f'- Course record: {rec.course_record.line()}',
                f'- Highest round: {rec.highest_round.line()}']
        for holes, m in sorted(rec.lowest_totals.items()):
            out.append(f'- Lowest {holes}-hole total: {m.score} ({"E" if m.to_par == 0 else f"{m.to_par:+d}"}) — {m.golfer}, {m.event_id}')
        for tier, m in sorted(rec.tier_records.items()):
            out.append(f'- {TIERS[tier]} record: {m.line()}')
        out.append(f'- Holes-in-one: {len(rec.aces)}' + (f' (e.g. hole {rec.aces[0][0]}, {rec.aces[0][1]}, {rec.aces[0][2]})' if rec.aces else ''))
        out.append('- Record history: ' + '; '.join(f'{m.score} {kind} by {m.golfer} ({m.event_id})' for kind, m in rec.history[:12])
                   + (' …' if len(rec.history) > 12 else ''))

    if errors:
        out += ['', '## Problems', ''] + [f'- {e}' for e in errors]
    text = '\n'.join(out) + '\n'
    (ROOT / 'reports').mkdir(exist_ok=True)
    (ROOT / 'reports' / 'COURSE_LIBRARY_REPORT.md').write_text(text, encoding='utf8')
    print(text[:5000])
    print(f'... {time.perf_counter() - t0:.0f} s total')


if __name__ == '__main__':
    main()
