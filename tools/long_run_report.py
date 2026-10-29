"""The long-run diagnostic report: one world run through the persistent session (long_world --session).

    python tools/long_run_report.py --out reports/long_run_2027 --seed 2027

Reads the run's data (seed_<s>.json.gz, seed_<s>.debug.json.gz, manifest.json) and its session archive
(world_<s>/archive) and writes LONG_RUN.md:

    1  run          engine commit, configuration, seed, hardware, seasons
    2  money        reconciliation, debt (against each golfer's own credit), backing changes (seeded
                    incumbents apart from careers that began in the world), funding-related missed starts
                    by career stage and tour
    3  access       every golfer-week by outcome and stage: financial barriers kept apart from full fields,
                    eligibility, injury and voluntary time off
    4  residence    moves per season by kind, moves not made for money, travel costs, college moves,
                    return-home stories
    5  potential    high-potential golfers who left full-time golf before developing (debug data: hidden
                    potential is used here only to find them, never by the simulation's decisions)
    6  generations  whether golfers who arrived in season two or later became great; interesting careers
    7  scale        active population, archive and checkpoint size and the season skip (simulate, save,
                    publish, observer) around seasons 1, 10, 25 and 50
"""
from __future__ import annotations

import argparse
import json
import statistics as S
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
import long_world as LW                                               # noqa: E402

FINANCIAL = ('could not afford any event', 'declined an invitation or place for cost')
INJURY = ('injured',)
VOLUNTARY = ('chose to train', 'chose to rest', 'chose to work', 'declined the events on offer')
ACCESS = ('shut out: every acceptable field full', 'not selected for the college lineup',
          'no suitable event scheduled', 'not eligible for the events scheduled')
PLAYED = ('played: first choice', 'played: alternative', 'played: selected field')
STAGES = ('college', 'amateur', 'new pro', 'established pro', 'part-time pro', 'club pro')


def pct(a, b):
    return f'{100 * a / b:.1f}%' if b else '—'


def money(x):
    return f'${x:,.0f}'


def section_run(d, man, perf_years):
    years = sorted(d['rows'])
    return ['# Long run: one world, every shot, seed ' + str(d['seed']), '',
            f'- {LW.analysis_note(man)}',
            f'- Engine commit `{man.get("commit")}`{" (working tree had changes)" if man.get("dirty") else ""}, '
            f'engine id `{man.get("engine")}`, Python {man.get("python")}.',
            f'- Hardware: {man.get("machine", "not recorded")}.',
            f'- Seasons {years[0]}–{years[-1]} ({len(years)}), full population, every shot simulated; started '
            f'{man.get("started")}. Run through the persistent session and the observer (a season skip each '
            f'year, committed, published and reloaded).',
            f'- Configuration: `{json.dumps(man.get("config", {}), sort_keys=True)}`', '']


def section_money(d, man=None):
    man = man or {}
    out = ['## 2. Money', '']
    ck = d['checks']
    bad = [y for y, c in ck.items() if c['reconcile_errors'] or c.get('support_errors')
           or abs(c['caddie_paid'] - c['caddie_received']) > 0.01 or abs(c['coach_paid'] - c['coach_received']) > 0.01]
    out += [f'- **Reconciliation:** {len(ck)} seasons checked; seasons where cash, family money, backers\' money or '
            f'staff payments did not reconcile: {len(bad)}{" " + str(bad) if bad else ""}.',
            '- **Flagged, not reconstructed:** in runs made before 4754eed (this one: engine '
            f'{str(man.get("commit", "?"))[:7]}) a season\'s *annual net* is the figure taken before the winter, '
            'so a winter move\'s $6,000 is not in it, and before 75c135f a support-funded winter move was drawn in the '
            '*next* year\'s ledger. Cash still reconciled every year; the per-year split of those few moves cannot be '
            'rebuilt exactly from the saved data, so annual nets are reported as recorded.', '']
    from golfsim import finance as FIN
    out += ['**Debt at the end of each season** (full-time professionals; beyond credit = below minus their own '
            'credit limit, which grows with last season\'s earnings):', '',
            '| Season | Full-time pros | In debt | Beyond own credit | Of those injured | Median debt |', '|---|---|---|---|---|---|']
    years = sorted(d['rows'])
    for y in years:
        rows, prev = d['rows'][y], d['rows'].get(y - 1, {})
        ft = [(g, r) for g, r in rows.items() if r['status'] == 'pro' and r['lifestyle'] == 'full_time']
        debt = [(g, r) for g, r in ft if r['cash'] < 0]
        beyond = []
        for g, r in debt:
            p = prev.get(g)
            earned = (p['prize'] + p['sponsors'] + p['salary'] + p['work']) if p else 0.0
            if r['cash'] < -FIN.credit_limit(earned) - 1:
                beyond.append(r)
        if y in (years[0], years[-1]) or y % 5 == 0:
            out.append(f'| {y} | {len(ft):,} | {len(debt):,} | {len(beyond):,} | {sum(1 for r in beyond if r["injury_weeks"])} | '
                       f'{money(-S.median([r["cash"] for _, r in debt])) if debt else "—"} |')
    out += ['', '**Backing changes per season** (seeded = professional when the world began; new = a career that began '
            'in the world):', '', '| Season | Found backers | Withdrew (seeded / new) | No longer needed (seeded / new) |',
            '|---|---|---|---|']
    initial = {int(g) for g, v in d['golfers'].items() if v['initial']}
    for y in years:
        tr = d['transitions'].get(y, [])
        c = lambda kind, seeded=None: sum(1 for t in tr if t['kind'] == kind and (seeded is None or (t['gid'] in initial) == seeded))
        if y in (years[0], years[1] if len(years) > 1 else years[0], years[-1]) or y % 5 == 0:
            out.append(f'| {y} | {c("found backers")} | {c("backers withdrew", True)} / {c("backers withdrew", False)} | '
                       f'{c("backers no longer needed", True)} / {c("backers no longer needed", False)} |')
    out += ['', '**Funding-related missed starts by career stage** (golfer-weeks with no affordable event, and '
            'invitations or qualified places declined for cost), whole run:', '',
            '| Stage | Golfer-weeks | No affordable event | Declined for cost |', '|---|---|---|---|']
    by_stage, tours = Counter(), Counter()
    for y, e in d['extras'].items():
        for k, n in e['access'].items():
            st, tour, outcome = k.split('|', 2)
            if outcome != 'declined an invitation or place for cost':
                by_stage[(st, 'weeks')] += n
            by_stage[(st, outcome)] += n
            if outcome in FINANCIAL:
                tours[(tour, outcome)] += n
    for st in STAGES:
        w = by_stage[(st, 'weeks')]
        if w:
            out.append(f'| {st} | {w:,} | {by_stage[(st, FINANCIAL[0])]:,} ({pct(by_stage[(st, FINANCIAL[0])], w)}) | '
                       f'{by_stage[(st, FINANCIAL[1])]:,} |')
    worst = sorted(((n, t) for (t, o), n in tours.items() if o == FINANCIAL[0]), reverse=True)[:10]
    out += ['', 'Tours with the most weeks lost to money: ' + '; '.join(f'{t} {n:,}' for n, t in worst) + '.', '']
    return out


def mini_affordability(d, archive, years=None):
    """Why full-time mini-tour professionals could not afford events (4+ weeks in a season), golfer by
    golfer: every cause that applies is counted (they overlap), from recorded facts only."""
    from golfsim.calendar import TOUR_BY_KEY
    out = []
    if archive is None:
        return out
    first = d['first']
    years = years or [y for y in sorted(d['rows']) if y > first]
    causes, n_all, n_short = Counter(), 0, 0
    for y in years:
        chunk = archive.year(y)['careers']
        prev = d['rows'].get(y - 1, {})
        withdrew = {t['gid'] for t in d['transitions'].get(y - 1, []) if t['kind'] == 'backers withdrew'}
        for gid, r in d['rows'][y].items():
            if not (r['status'] == 'pro' and r['lifestyle'] == 'full_time' and r['tier'] == 4):
                continue
            n_all += 1
            weeks = (chunk.get(gid, {}).get('access') or {}).get('could not afford any event', 0)
            if weeks < 4:
                continue
            n_short += 1
            p = prev.get(gid)
            if p is None or p['status'] != 'pro':
                causes['new professional this season'] += 1
            else:
                start = p['cash']
                if start < 0:
                    causes['began the season in debt'] += 1
                elif start < 5000:
                    causes['began the season with under $5,000'] += 1
                if p['prize'] < p['event_costs'] + p['caddie_cost'] + p['coaching']:
                    causes['last season golf cost more than it won'] += 1
                if p['injury_weeks'] >= 4:
                    causes['injured 4+ weeks last season'] += 1
            if gid in withdrew:
                causes['backers withdrew last winter'] += 1
            if not r['backer_support'] and not (p or {}).get('backer_support'):
                causes['no backers\' money this season or last'] += 1
            if r['injury_weeks'] >= 4:
                causes['injured 4+ weeks this season'] += 1
            tour = chunk.get(gid, {}).get('tour') or ''
            countries = {c for c, _ in TOUR_BY_KEY[tour].countries} if tour in TOUR_BY_KEY else set()
            if r.get('home') and countries and r['home'] not in countries:
                causes['lives outside their tour\'s countries'] += 1
            if r['work_wk'] >= 8:
                causes['took 8+ weeks of paid work'] += 1
    out += [f'Full-time mini-tour professional seasons ({years[0]}–{years[-1]}): {n_all:,}; with 4+ weeks unable to afford '
            f'any event: {n_short:,} ({pct(n_short, n_all)}). Causes that applied (a season can have several):', '']
    out += [f'- {k}: {n:,} ({pct(n, n_short)})' for k, n in causes.most_common()]
    return out + ['']


def section_access(d):
    out = ['## 3. Competition access, apart from money, injury and choice', '',
           'Every golfer-week of the whole run, by career stage: played; blocked by access (full fields, college '
           'lineup, no event, not eligible); blocked by money; injured; chose not to play.', '',
           '| Stage | Weeks | Played | Access | Money | Injured | Chose not to |', '|---|---|---|---|---|---|---|']
    tot = defaultdict(Counter)
    for e in d['extras'].values():
        for k, n in e['access'].items():
            st, _, outcome = k.split('|', 2)
            if outcome == 'declined an invitation or place for cost':
                continue
            tot[st]['weeks'] += n
            grp = ('played' if outcome in PLAYED else 'access' if outcome in ACCESS else 'money' if outcome in FINANCIAL
                   else 'injured' if outcome in INJURY else 'choice')
            tot[st][grp] += n
    for st in STAGES:
        c = tot[st]
        if c['weeks']:
            out.append(f'| {st} | {c["weeks"]:,} | {pct(c["played"], c["weeks"])} | {pct(c["access"], c["weeks"])} | '
                       f'{pct(c["money"], c["weeks"])} | {pct(c["injured"], c["weeks"])} | {pct(c["choice"], c["weeks"])} |')
    return out + ['']


def kind_of(reason):
    if reason.startswith('college transfer'):
        return 'college transfer'
    if reason.startswith('college'):
        return 'college arrival'
    if reason.startswith('returned home'):
        return 'returned home' + (' (after college)' if 'after college' in reason else '')
    if reason.startswith('closer to'):
        return 'closer to their events' + (' (after college)' if 'after college' in reason else '')
    if reason.startswith('to be near'):
        return 'caddie followed their player'
    if reason.startswith('to where most'):
        return 'coach followed their players'
    return 'other'


def returned_after_abroad(moves):
    """A career move abroad and, later in time, a return home (moves in date order)."""
    away = next((i for i, m in enumerate(moves) if m['reason'].startswith('closer to')), None)
    return away is not None and any(m['reason'].startswith('returned home') for m in moves[away + 1:])


def section_residence(d, archive):
    out = ['## 4. Where people live', '']
    years = sorted(d['extras'])
    kinds = sorted({kind_of(m['reason']) for e in d['extras'].values() for m in e['moves']})
    out += ['| Season | ' + ' | '.join(kinds) + ' | Not made (money) |', '|---|' + '---|' * (len(kinds) + 1)]
    for y in years:
        c = Counter(kind_of(m['reason']) for m in d['extras'][y]['moves'])
        if y in (years[0], years[-1]) or y % 5 == 0:
            out.append(f'| {y} | ' + ' | '.join(str(c[k]) for k in kinds) + f' | {d["extras"][y]["move_blocked"]} |')
    total = Counter(kind_of(m['reason']) for e in d['extras'].values() for m in e['moves'])
    out += ['', 'Whole run: ' + '; '.join(f'{k} {n:,}' for k, n in total.most_common()) + '.', '']
    # travel: event costs per event for full-time professionals living abroad vs at home
    abroad, home = [], []
    for y, rows in d['rows'].items():
        for gid, r in rows.items():
            if r['status'] == 'pro' and r['lifestyle'] == 'full_time' and r['events'] and r.get('home'):
                (home if r['home'] == d['golfers'][str(gid) if str(gid) in d['golfers'] else gid]['country']
                 else abroad).append(r['event_costs'] / r['events'])
    if home:
        out.append(f'- Travel and entry costs per event, full-time professionals: living in their own country median '
                   f'{money(S.median(home))} ({len(home):,} seasons); living abroad median '
                   f'{money(S.median(abroad)) if abroad else "—"} ({len(abroad):,} seasons).')
    # return-home stories from the archive's move histories
    stories = []
    if archive is not None:
        for pid, p in archive.people.items():
            ms = sorted(p.get('moves') or [], key=lambda m: (m['year'], m.get('week', 0)))
            if returned_after_abroad(ms):
                stories.append((pid, p, ms))
    out.append(f'- Golfers who moved abroad for their career and later returned home: {len(stories):,}.')
    for pid, p, ms in sorted(stories, key=lambda x: x[0])[:5]:
        out.append(f'  - **{p["name"]} ({p["nationality"]})**, born {p["born"]}: ' + '; '.join(
            f'{m["year"]}: {where(m["from"])} → {where(m["to"])} ({m["reason"]})' for m in ms))
    return out + ['']


def where(x):
    return f'{x["region"]}, {x["country"]}' if x and x.get('region') else (x['country'] if x else 'unknown')


EXITS = ('part-time pro', 'back to amateur', 'retired', 'became caddie', 'became coach', 'became club pro',
         'amateur took a job', 'college to amateur')


def episodes(rows_by_year, gid):
    """A golfer's full-time golf episodes (professional or amateur, college included): [(first, last)]."""
    out = []
    for y in sorted(rows_by_year):
        r = rows_by_year[y].get(gid)
        if r and r['lifestyle'] == 'full_time' and r['status'] in ('pro', 'amateur'):
            if out and out[-1][1] == y - 1:
                out[-1][1] = y
            else:
                out.append([y, y])
    return out


def section_potential(d, dbg):
    """High-potential golfers and how their full-time episodes ended, episode by episode."""
    out = ['## 5. High-potential golfers: how their full-time golf ended', '',
           '**Definition.** High potential = the top 5% of hidden potential (debug data: the simulation never uses it '
           'for decisions; it only finds these golfers here). An episode is a run of consecutive full-time seasons '
           '(professional or amateur, college included). An episode **ended before developing** if it ended (the '
           'golfer was no longer full-time the next season) before they were 27 and with their best overall so far at '
           'least 6 points below their potential. Its reason is the career decision recorded at the end of *that* '
           'episode\'s last season. A golfer who later returned to full-time golf is a **comeback**, not a loss. '
           'These counts describe this one world; they are not the total of lost talent, and the recorded reasons '
           '(with the money and desire the decision weighed) are not proof that money alone caused a departure.', '']
    years = sorted(d['rows'])
    last = years[-1]
    rows = d['rows']
    pot, best_by_year = {}, defaultdict(dict)
    for y in years:
        for gid, v in dbg.get(y, {}).items():
            if v[1] is not None:
                pot.setdefault(gid, v[1])
            best_by_year[gid][y] = v[0]
    pots = sorted(pot.values())
    cut = pots[int(0.95 * len(pots))] if pots else 99
    high = [gid for gid, p in pot.items() if p >= cut]
    why = {}
    for y, ts in d['transitions'].items():
        for t in ts:
            if t['kind'] in EXITS:
                why[(t['gid'], y)] = t
    cat = Counter()
    cases = []
    for gid in high:
        g = d['golfers'].get(str(gid)) or d['golfers'].get(gid)
        eps = episodes(rows, gid)
        if not eps:
            cat['never full-time in the archive'] += 1
            continue
        for k, (a, b) in enumerate(eps):
            if b == last:
                cat['still full-time at the end of the run (an unfolding episode)'] += 1
                continue
            age = b - g['born']
            best = max(v for y, v in best_by_year[gid].items() if y <= b)
            reason = why.get((gid, b))
            comeback = k < len(eps) - 1
            if age >= 27 or pot[gid] - best < 6:
                cat['episode ended after developing or at 27+ (a completed episode)'] += 1
            elif comeback:
                cat['ended young and undeveloped, then came back (comeback episode)'] += 1
            else:
                cat['ended young and undeveloped, not back by the end of the run'] += 1
                cases.append((pot[gid], gid, g, age, b, best, sum(rows[y][gid]['events'] for y in range(a, b + 1)), reason))
    out.append(f'Top 5% of potential (≥ {cut:.1f}): {len(high):,} golfers. Each of their full-time episodes '
               '(a golfer can have several), and those never full-time:')
    out += [''] + [f'- {k}: {n:,}' for k, n in cat.most_common()] + ['']
    reasons = Counter((c[7] or {}).get('kind', 'no departure decision recorded') for c in cases)
    out.append('Episodes that ended young and undeveloped and did not come back, by the recorded decision: '
               + ('; '.join(f'{k} {n}' for k, n in reasons.most_common()) or 'none') + '.')
    out += ['', '| Golfer | Potential | Best overall then | Episode | Age at end | Starts in it | Decision (recorded) |',
            '|---|---|---|---|---|---|---|']
    for p_, gid, g, age, b, best, starts, t in sorted(cases, key=lambda c: (-c[0], c[1]))[:15]:
        detail = ', '.join(f'{k} {v}' for k, v in (t or {}).items() if k in ('p', 'runway', 'progress', 'desire'))
        out.append(f'| {g["name"]} ({g["country"]}) | {p_:.0f} | {best:.1f} | ends {b} | {age} | {starts} | '
                   f'{(t or {}).get("kind", "none recorded")}{f" ({detail})" if detail else ""} |')
    return out + ['']


def arrival(d, gid):
    """How a golfer entered the world: starting-world professional / amateur (college included), or later
    as an 18-year-old junior or as a new professional from outside the amateur game."""
    g = d['golfers'].get(str(gid)) or d['golfers'].get(gid)
    if g['initial']:
        r = d['rows'][d['first']].get(gid) or d['rows'][d['first']].get(str(gid))
        return 'starting world: professional' if r and r['status'] in ('pro', 'club_pro') else 'starting world: amateur'
    first = next((t for _, t in g['history'] if t.startswith(('Arrived on the scene', 'Turned professional'))), '')
    return 'later: new professional' if first.startswith('Turned professional') and 'Arrived' not in first \
        else 'later: junior (18)'


def weekly_best(archive):
    """Each person's best weekly world ranking (top 100 kept per week) over the archive: one pass, a few
    seasons decoded at a time."""
    best = {}
    for y in archive.years:
        for w in range(1, 53):
            for i, pid in enumerate(archive.ranking(y, w)[:10]):
                best[pid] = min(best.get(pid, 99), i + 1)
    return best


def section_generations(d, dbg, archive=None, best=None):
    out = ['## 6. Generations', '']
    majors = Counter(d['majors'].values())
    wins = Counter()
    for y, rows in d['rows'].items():
        for gid, r in rows.items():
            wins[gid] += sum(r['wins_by_tier'].values())
    if best is None and archive is not None:
        best = weekly_best(archive)
    label = 'weekly world ranking' if best is not None else 'world ranking at a season\'s end (weekly not available)'
    if best is None:
        best = {}
        for y, rows in d['rows'].items():
            for gid, r in rows.items():
                if r['wr'] is not None and r['wr'] <= 10:
                    best[gid] = min(best.get(gid, 99), r['wr'])
    groups = defaultdict(set)
    for gid in d['golfers']:
        groups[arrival(d, int(gid))].add(int(gid))
    out += [f'Reaching No. 1 and the top ten is by **{label}**. Cohorts: the starting world\'s professionals and its '
            'amateurs (college included) are separate; later arrivals are 18-year-old juniors or new professionals '
            'from outside the tracked amateur game. Starting-world careers began before the archive (their early '
            'results are unknown).', '',
            '| Cohort | Golfers | Reached No. 1 | Reached top 10 | Major champions | Majors won |', '|---|---|---|---|---|---|']
    for k in ('starting world: professional', 'starting world: amateur', 'later: junior (18)', 'later: new professional'):
        ids = groups.get(k, set())
        out.append(f'| {k} | {len(ids):,} | {sum(1 for x in ids if best.get(x) == 1)} | '
                   f'{sum(1 for x in ids if best.get(x, 99) <= 10)} | {sum(1 for x in majors if x in ids)} | '
                   f'{sum(n for x, n in majors.items() if x in ids)} |')
    out += ['', '**Most major titles:**', '']
    g = d['golfers']
    for gid, n in majors.most_common(8):
        r = g.get(str(gid)) or g.get(gid)
        out.append(f'- {r["name"]} ({r["country"]}), born {r["born"]}, {arrival(d, gid)} (arrived {r.get("created")}): '
                   f'{n} majors, {wins[gid]} wins at every level (amateur and college included), best {label} {best.get(gid, "outside the top 10")}')
    return out + ['']


def section_scale(d):
    out = ['## 7. Population, archive and the season skip', '',
           'The owner\'s target: a season skip within 120 s including save, publication and a usable observer. '
           'A 50-season run does not prove season 100.', '',
           '| Season | Active | People | Archive MB | Checkpoint MB | Skip s | Simulate | Save | Publish | Observer | First Records |',
           '|---|---|---|---|---|---|---|---|---|---|---|']
    perf = d.get('perf', {})
    years = sorted(perf)
    marks = {years[0], years[-1]} | {y for y in years if (y - years[0] + 1) in (1, 10, 25, 50)} | \
            {y for y in years if (y - years[0] + 1) % 5 == 0}
    for y in years:
        p = perf[y]
        if y in marks:
            out.append(f'| {y} (#{y - years[0] + 1}) | {p["active"]:,} | {p["people"]:,} | {p["archive_mb"]} | {p["checkpoint_mb"]} | '
                       f'{p["skip"]} | {p["simulate"]} | {p["save"]} | {p["publish"]} | {p["reload"] + p["overview"]:.1f} | {p["records"]} |')
    over = [y for y in years if perf[y]['skip'] > 120]
    out += ['', f'Seasons over 120 s: {len(over)} of {len(years)}' + (f' (first: {over[0]})' if over else '') + '.', '']
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--seed', type=int, default=2027)
    a = ap.parse_args()
    out = Path(a.out)
    d = LW.load(out, a.seed)
    dbg = LW.load_debug(out, a.seed)
    man = LW.load_manifest(out)
    arch = None
    arch_dir = out / f'world_{a.seed}' / 'archive'
    if (arch_dir / 'MANIFEST.json').exists() or (arch_dir / 'world.json').exists():
        from golfsim.archive import Archive
        arch = Archive(out / f'world_{a.seed}' / 'archive')
    tl = LW.analyse(d, min(12, d['years']))
    best = weekly_best(arch) if arch is not None else None
    lines = (section_run(d, man, d.get('perf', {})) + section_money(d, man) + section_access(d) + section_residence(d, arch)
             + ['## 3b. Mini-tour seasons cut short by money, by cause', ''] + mini_affordability(d, arch)
             + section_potential(d, dbg) + section_generations(d, dbg, arch, best)
             + ['**Interesting careers** (picked by rules on recorded results):', ''] + LW.interesting(d, tl, best_week=best) + ['']
             + section_scale(d))
    (out / 'LONG_RUN.md').write_text('\n'.join(lines) + '\n')
    print('wrote', out / 'LONG_RUN.md')


if __name__ == '__main__':
    main()
