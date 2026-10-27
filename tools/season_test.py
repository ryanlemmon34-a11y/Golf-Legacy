"""Long-term world test: several full seasons, every shot of every event, attributes held fixed.

    python tools/season_test.py [--years 5] [--seed 2027]

Checks that the world's machinery works over time: AI scheduling by prestige, fields, the majors'
qualifying rules, tour cards, rankings, money and prestige, and that the attributes show up in the
season statistics the way they should. Writes reports/SEASON_TEST_REPORT.md.
"""
from __future__ import annotations

import argparse
import math
import statistics as S
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from golfsim import prestige as PR                                   # noqa: E402
from golfsim.calendar import TIERS, TOUR_BY_KEY                      # noqa: E402
from golfsim.population import generate_world, level_of              # noqa: E402
from golfsim.season import PREMIER_TOURS, Season                     # noqa: E402

LEVELS = ('Premier Tour', 'Challenger', 'Regional', 'Mini tour', 'College', 'Amateur')


def corr(xs, ys):
    mx, my = S.mean(xs), S.mean(ys)
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    sy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy) if sx and sy else 0.0


def spearman(xs, ys):
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0] * len(v)
        for k, i in enumerate(order):
            r[i] = k
        return r
    return corr(ranks(xs), ranks(ys))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--years', type=int, default=5)
    ap.add_argument('--seed', type=int, default=2027)
    a = ap.parse_args()
    t0 = time.perf_counter()
    world = generate_world(seed=a.seed)
    s = Season(world, seed=a.seed)
    years = list(range(s.first_year, s.first_year + a.years))
    timing = {}
    level_by_year = {}
    for y in years:
        t1 = time.perf_counter()
        level_by_year[y] = {g.id: level_of(g) for g in world.golfers}       # membership during the season
        s.run_year(y, progress=lambda yy, w: print(f'\r{yy} week {w:2d}', end='', flush=True))
        timing[y] = time.perf_counter() - t1
        print(f'  {timing[y]:.0f} s, {s.holes_played[y]:,} holes')
    s.close()
    g = s.g
    name = lambda gid: f'{g[gid].name} ({g[gid].country}, {g[gid].overall:.0f})'
    out = ['# Golf Legacy — Multi-Season World Test', '',
           f'{a.years} full seasons ({years[0]}–{years[-1]}) of the whole world: {len(world.golfers):,} golfers, '
           f'{len(s.results):,} events, **{sum(s.holes_played.values()):,} holes, every shot simulated**, in '
           f'{(time.perf_counter() - t0) / 60:.1f} minutes ({S.mean(timing.values()):.0f} s per season on '
           f'{s.workers} cores). Attributes are held fixed, so every change below comes from the season system '
           '(entries, results, cards, rankings, prestige), not from players improving or aging.', '']

    # ---- 1. does the world sort players by ability? -------------------------------------------
    out += ['## 1. Does the world sort players by ability?', '',
            'Average overall rating at each level at the start of each season (the starting world was sorted by a '
            'noisy reputation; after that, only results move players), and how well the world ranking follows true '
            'ability (Spearman correlation, top 500 pros by overall).', '',
            '| Season | ' + ' | '.join(LEVELS) + ' | Ranking vs ability | Top-50 players on the Premier Tour |',
            '|---|' + '---|' * (len(LEVELS) + 2)]
    rank_snap = {}
    for y in years:
        lv = level_by_year[y]
        cols = []
        for L in LEVELS:
            xs = [g[i].overall for i, l in lv.items() if l == L]
            cols.append(f'{S.mean(xs):.1f} ({len(xs)})' if xs else '—')
        ids = s.ctx.ranking(y, 52)
        pos = {gid: i for i, gid in enumerate(ids)}
        pros = sorted((x for x in world.golfers if x.status == 'pro'), key=lambda x: -x.overall)[:500]
        rs = spearman([-x.overall for x in pros], [pos.get(x.id, 5000) for x in pros])
        top50 = sum(1 for x in pros[:50] if lv[x.id] == 'Premier Tour')
        rank_snap[y] = pos
        out.append(f'| {y} | ' + ' | '.join(cols) + f' | {rs:.2f} | {top50} of 50 |')
    moves = Counter()
    for y in years:
        for gid, frm, to, why in s.card_log[y]:
            moves[(y, TOUR_BY_KEY[frm].tier if frm in TOUR_BY_KEY else 9, TOUR_BY_KEY[to].tier)] += 1
    out += ['', '**Tour cards each off-season** (players moving between levels):', '',
            '| After season | Premier → Challenger | Challenger → Premier | Challenger → lower | Lower → Challenger | Regional ↔ Mini |',
            '|---|---|---|---|---|---|']
    for y in years:
        out.append(f'| {y} | {moves[(y, 1, 2)]} | {moves[(y, 2, 1)]} | {moves[(y, 2, 3)] + moves[(y, 2, 4)]} | '
                   f'{moves[(y, 3, 2)] + moves[(y, 4, 2)]} | {moves[(y, 3, 4)] + moves[(y, 4, 3)]} |')
    ups = [(gid, frm, to, why) for gid, frm, to, why in s.card_log[years[-1]] if to in PREMIER_TOURS and frm not in PREMIER_TOURS]
    out.append('\nExamples of players earning Premier Tour cards after the last season: ' + '; '.join(
        f'{name(gid)} — {why}' for gid, _, _, why in ups[:6]) + '.')

    # ---- 2. who wins --------------------------------------------------------------------------
    out += ['', '## 2. Who wins', '', '| Level | Events | Different winners | Winners\' average overall | '
            'Field average | Wins by the level\'s 10 best players | Lowest-rated winner |', '|---|---|---|---|---|---|---|']
    wins_by_tier = defaultdict(list)
    field_ov = defaultdict(list)
    for r in s.results.values():
        ser = s.cal.by_id[r.series_id]
        if ser.kind == 'qualifying' or not r.finish or not r.finish[0]:
            continue
        w = r.winner()
        if w is None:
            continue
        wins_by_tier[ser.tier].append((r, w))
        field_ov[ser.tier].append(S.mean(g[x].overall for x, _, _ in r.finish[0]))
    for tier in sorted(wins_by_tier):
        rows = wins_by_tier[tier]
        winners = [w for _, w in rows]
        best = sorted({gid for r, _ in rows for gid, _, _ in r.finish[0]}, key=lambda i: -g[i].overall)[:10]
        low_r, low_w = min(rows, key=lambda rw: g[rw[1]].overall)
        out.append(f'| {TIERS[tier]} | {len(rows)} | {len(set(winners))} | {S.mean(g[w].overall for w in winners):.1f} | '
                   f'{S.mean(field_ov[tier]):.1f} | {sum(w in best for w in winners) / len(winners):.0%} | '
                   f'{g[low_w].overall:.0f} ({s.cal.by_id[low_r.series_id].name} {low_r.year}) |')
    out += ['', '**Most wins in a season (Premier Tour and majors):**', '']
    for y in years:
        c = Counter(w for r, w in wins_by_tier[0] + wins_by_tier[1] if r.year == y)
        top = c.most_common(3)
        out.append(f'- {y}: ' + ', '.join(f'{name(gid)} {n}' for gid, n in top))

    # ---- 3. majors ----------------------------------------------------------------------------
    out += ['', '## 3. The majors', '', '| Year | Major | Champion | Overall | World rank before | Score | Field | Amateurs | Club pros | Via qualifying |',
            '|---|---|---|---|---|---|---|---|---|---|']
    for y in years:
        for sid in ('TOUR_MASTERS', 'PREMIER_TOUR_CHAMPIONSHIP', 'USA_OPEN', 'BRITANNIA_OPEN'):
            r = s.results[f'{y}:{sid}']
            w = r.winner()
            topar = next(tp for yy, gw, tp in s.champions[sid] if yy == y)
            ids = [x for x, _, _ in r.finish[0]]
            prev = s.ctx.ranking(y, s.cal.by_id[sid].week - 1)
            wr = prev.index(w) + 1 if w in prev else '—'
            f = s.stage_log.get((y, sid, 'field'))
            qual = sum(n for code, n in (f.route_counts.items() if f else []) if code.endswith(('Q', 'F')) or code.startswith(('BQ', 'P5')))
            out.append(f'| {y} | {s.cal.by_id[sid].name} | {g[w].name} ({g[w].country}) | {g[w].overall:.0f} | {wr} | '
                       f'{topar:+d} | {len(ids)} | {sum(g[x].status == "amateur" for x in ids)} | '
                       f'{sum(g[x].status == "club_pro" for x in ids)} | {qual} |')

    # ---- 4. prestige drives the schedule ------------------------------------------------------
    top20 = {x.id for x in sorted((x for x in world.golfers if x.status == 'pro'), key=lambda x: -x.overall)[:20]}
    cat_rows = defaultdict(lambda: defaultdict(list))
    for r in s.results.values():
        ser = s.cal.by_id[r.series_id]
        if ser.tier == 1:
            ids = {x for site in r.finish for x, _, _ in site}
            cat_rows[ser.category][r.year].append((r.prestige, r.field_strength, len(ids & top20)))
    out += ['', '## 4. Event prestige and where the stars play', '',
            'Event prestige is a rolling average of the last 4 editions of each factor (tour, field, purse, course). '
            'Average per event: prestige going into the event, field strength (0–100, from the world ranking of the '
            'best 30 entrants) and how many of the world\'s 20 best players entered.', '',
            '| Season | ' + ' | '.join(f'{c.title()} prestige / field / top-20' for c in ('flagship', 'standard', 'national_open', 'opportunity')) + ' |',
            '|---|---|---|---|---|']
    for y in years:
        cells = []
        for c in ('flagship', 'standard', 'national_open', 'opportunity'):
            rows = cat_rows[c][y]
            cells.append(f'{S.mean(p for p, _, _ in rows):.1f} / {S.mean(f for _, f, _ in rows):.0f} / {S.mean(t for _, _, t in rows):.1f}' if rows else '—')
        out.append(f'| {y} | ' + ' | '.join(cells) + ' |')
    out += ['', '**Prestige of every Premier Tour event over the test** (same week every year):', '',
            '| Week | Event | Category | ' + ' | '.join(str(y) for y in years) + ' | Next year |', '|---|---|---|' + '---|' * (len(years) + 1)]
    for ser in sorted((x for x in s.cal.series if x.tier <= 1), key=lambda x: x.week):
        hist = {yy: p for yy, p, _ in s.prestige_history[ser.series_id]}
        out.append(f'| {ser.week} | {ser.name} | {ser.category} | ' + ' | '.join(f'{hist.get(y, 0):.0f}' for y in years)
                   + f' | {s.event_prestige[ser.series_id]:.0f} |')
    lvl = defaultdict(list)
    for ser in s.cal.series:
        lvl[TIERS[ser.tier]].append(s.event_prestige[ser.series_id])
    out.append('\nAverage prestige by level now: ' + ', '.join(f'{k} {S.mean(v):.0f}' for k, v in lvl.items()) + '.')

    # ---- 4b. schedules, fatigue and injuries --------------------------------------------------------
    y = years[-1]
    out += ['', f'## 5. Schedules, fatigue and injuries', '',
            f'Events played in {y} by level (median / 90th percentile), and the world\'s 20 best players.', '',
            '| Level | Golfers | Events (median) | Events (90th pct) |', '|---|---|---|---|']
    for L in LEVELS:
        xs = sorted(len(s.played[y][i]) for i, l in level_by_year[y].items() if l == L and s.played[y][i])
        if xs:
            out.append(f'| {L} | {len(xs)} | {S.median(xs):.0f} | {xs[int(len(xs) * .9)]} |')
    best20 = sorted((x for x in world.golfers if x.status == 'pro'), key=lambda x: -x.overall)[:20]
    ev = [len(s.played[y][x.id]) for x in best20]
    out.append(f'\nThe 20 best players averaged **{S.mean(ev):.1f} events** in {y} (range {min(ev)}–{max(ev)}; '
               'real-life top players play about 18–24 including majors). Stamina sets each golfer\'s plan '
               '(Premier players about 15–23 events, stars about 4 fewer; lower tours 19–27), tiredness makes them skip weeks, and good course '
               'managers rest more wisely.')
    inj = [row for yy in years for row in s.injuries[yy]]
    pros_n = sum(1 for x in world.golfers if x.status == 'pro')
    out += ['', f'**Injuries:** {len(inj)} over {a.years} seasons ({len(inj) / a.years:.0f} a year; about '
            f'{sum(1 for r in inj if g[r[1]].status == "pro") / a.years / pros_n:.0%} of professionals a year). Median time out '
            f'{S.median(r[3] for r in inj):.0f} weeks; longest {max(r[3] for r in inj)} weeks.' if inj else 'No injuries.', '',
            'Injury risk by group, per 1,000 events played by professionals (so golfers who play more are compared '
            'fairly with those who play less):', '',
            '| Group | Professionals | Events played | Injuries per 1,000 events |', '|---|---|---|---|']
    def rate(pred):
        grp = [x for x in world.golfers if x.status == 'pro' and pred(x)]
        ids = {x.id for x in grp}
        events = sum(len(s.played[yy][i]) for yy in years for i in ids)
        n = sum(1 for _, gid, *_ in inj if gid in ids)
        return len(grp), events, 1000 * n / max(1, events)
    for label, pred in (('Age under 30', lambda x: x.age(y) < 30), ('Age 30-39', lambda x: 30 <= x.age(y) < 40),
                        ('Age 40+', lambda x: x.age(y) >= 40),
                        ('Injury resistance under 40', lambda x: x.attrs['injury_resistance'] < 40),
                        ('Injury resistance 40-60', lambda x: 40 <= x.attrs['injury_resistance'] <= 60),
                        ('Injury resistance over 60', lambda x: x.attrs['injury_resistance'] > 60),
                        ('Stamina under 40', lambda x: x.attrs['stamina'] < 40),
                        ('Stamina over 70', lambda x: x.attrs['stamina'] > 70)):
        n, e, r = rate(pred)
        out.append(f'| {label} | {n} | {e:,} | {r:.1f} |')
    stars = [r for r in inj if r[1] in {x.id for x in best20}]
    if stars:
        out.append('\nInjuries to the world\'s 20 best: ' + '; '.join(
            f'{g[gid].name} — {kind}, {wk} weeks ({yy_w})' for yy_w, gid, kind, wk, _ in stars[:8]) + '.')
    from golfsim.course import ashford_ridge
    from golfsim.engine import play_round
    from golfsim.golfer import uniform_golfer
    import random as _r
    out += ['', '**What tiredness costs** (tour-average golfer, strokes per round at Ashford Ridge versus fresh):', '',
            '| Stamina | Fatigue 0.3 | Fatigue 0.6 | Fatigue 0.9 |', '|---|---|---|---|']
    for stam in (30, 60, 90):
        base = None
        cells = []
        for f in (0.0, 0.3, 0.6, 0.9):
            gg = uniform_golfer(75)
            gg.attrs['stamina'] = stam
            gg.fatigue = f
            rr = _r.Random(1)
            m = S.mean(play_round(gg, ashford_ridge(), rr).score for _ in range(2000))
            if base is None:
                base = m
            else:
                cells.append(f'+{m - base:.2f}')
        out.append(f'| {stam} | ' + ' | '.join(cells) + ' |')

    # ---- 5. players: prestige, money, sponsors --------------------------------------------------
    y = years[-1]
    out += ['', f'## 6. Player prestige, money and sponsors ({y})', '',
            '| # | Player | Overall | World rank | Wins (all seasons) | Majors | Prize money (season) | Prestige | Sponsor income |',
            '|---|---|---|---|---|---|---|---|---|']
    wins_all = Counter(w for rows in wins_by_tier.values() for _, w in rows)
    majors = Counter(w for r, w in wins_by_tier[0])
    best = sorted(world.golfers, key=lambda x: -s.player_prestige(x.id))[:15]
    for i, x in enumerate(best, 1):
        p = s.player_prestige(x.id)
        out.append(f'| {i} | {x.name} ({x.country}) | {x.overall:.0f} | {rank_snap[y].get(x.id, 9999) + 1} | {wins_all[x.id]} | '
                   f'{majors[x.id]} | ${s.earnings[y][x.id]:,.0f} | {p:.0f} | ${PR.endorsements(p):,.0f} |')
    by_level = defaultdict(list)
    for x in world.golfers:
        by_level[level_of(x)].append(s.player_prestige(x.id))
    out.append('\nAverage player prestige by level: ' + ', '.join(f'{k} {S.mean(v):.0f}' for k, v in by_level.items()) + '.')

    # ---- 6. attributes in the statistics --------------------------------------------------------
    out += ['', '## 7. Do the attributes show up in the statistics?', '',
            f'Professionals with 30+ rounds in {y}. Correlation between an attribute and the season statistic it '
            'should drive (−1 to 1; strokes-gained per round and scoring relative to the field in the same round, so '
            'different courses are comparable).', '',
            '| Attribute | Statistic | Correlation | Expect |', '|---|---|---|---|']
    ps = s.pstats[y]
    pool = [x for x in world.golfers if x.status == 'pro' and ps[x.id]['rounds'] >= 30]
    def stat(x, k):
        d = ps[x.id]
        return {'distance': d['drive_yards'] / max(1, d['drives']), 'fairways': d['fairways'] / max(1, d['fairway_att']),
                'gir': d['gir'] / (18 * d['rounds']), 'putts': d['putts'] / d['rounds'],
                'sg_ott': d['sg_ott'] / d['rounds'], 'sg_app': d['sg_app'] / d['rounds'], 'sg_arg': d['sg_arg'] / d['rounds'],
                'sg_putt': d['sg_putt'] / d['rounds'], 'vs_field': d['vs_field'] / d['rounds']}[k]
    checks = (('power', 'distance', 'Driving distance', 'strong +'),
              ('driving_accuracy', 'fairways', 'Fairways hit %', 'strong +'),
              ('mid_irons', 'sg_app', 'Strokes gained: approach', '+'),
              ('chipping', 'sg_arg', 'Strokes gained: around the green', '+'),
              ('short_putting', 'sg_putt', 'Strokes gained: putting', '+'),
              ('green_reading', 'sg_putt', 'Strokes gained: putting', '+'),
              ('power', 'sg_ott', 'Strokes gained: off the tee', '+'),
              (None, 'vs_field', 'Scoring vs field, Premier Tour players (lower is better)', 'strong −'))
    prem_pool = [x for x in pool if level_by_year[y][x.id] == 'Premier Tour']
    for attr, k, label, expect in checks:
        sample = prem_pool if k == 'vs_field' else pool       # same fields, so scores are comparable
        xs = [x.overall if attr is None else x.attrs[attr] for x in sample]
        ys = [stat(x, k) for x in sample]
        out.append(f'| {"Overall" if attr is None else attr.replace("_", " ").title()} | {label} | {corr(xs, ys):+.2f} | {expect} |')
    out.append(f'\n({len(pool)} professionals.)')
    leaders = []
    for k, label, rev in (('distance', 'Driving distance', True), ('fairways', 'Fairway accuracy', True),
                          ('sg_putt', 'Strokes gained putting', True), ('vs_field', 'Scoring vs field', False)):
        prem = [x for x in pool if level_by_year[y][x.id] == 'Premier Tour']
        if not prem:
            continue
        top = sorted(prem, key=lambda x: stat(x, k), reverse=rev)[0]
        fmt = {'distance': '{:.0f} yds', 'fairways': '{:.0%}', 'sg_putt': '{:+.2f}', 'vs_field': '{:+.2f}'}[k]
        leaders.append(f'{label}: {top.name} {fmt.format(stat(top, k))} ({top.archetype}; power {top.attrs["power"]:.0f}, '
                       f'accuracy {top.attrs["driving_accuracy"]:.0f}, short putting {top.attrs["short_putting"]:.0f}, overall {top.overall:.0f})')
    out += ['', f'**Premier Tour statistics leaders {y}:**', ''] + [f'- {x}' for x in leaders]

    # ---- 7. course records ---------------------------------------------------------------------
    recs = sorted((r for r in s.records.layouts.values() if r.course_record), key=lambda r: r.course_record.to_par)[:8]
    out += ['', '## 8. Lowest rounds and course records', '', '| Round | Course (layout) | Golfer | Event |', '|---|---|---|---|']
    for r in recs:
        cid, lay = r.layout_id.split(':')
        m = r.course_record
        out.append(f'| {m.score} ({m.to_par:+d}) | {s.lib.sites[cid]["name"]} ({lay}) | {m.golfer} | {m.event_id} round {m.round_no} |')
    aces = sum(len(r.aces) for r in s.records.layouts.values())
    albs = sum(len(r.albatrosses) for r in s.records.layouts.values())
    out.append(f'\nHoles-in-one: {aces:,}; albatrosses: {albs:,} across {a.years} seasons.')

    text = '\n'.join(out) + '\n'
    (ROOT / 'reports').mkdir(exist_ok=True)
    (ROOT / 'reports' / 'SEASON_TEST_REPORT.md').write_text(text, encoding='utf8')
    print(text[:6000])


if __name__ == '__main__':
    main()
