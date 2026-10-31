"""Read-only extraction of one comparison arm's committed seasons (no World/Session/Archive object is opened).

Reads, for one run folder: manifest.json, seed_<s>.state.pkl (rewritten atomically after every committed season) or
seed_<s>.json.gz (checkpointed every 5 seasons) -- whichever lists more seasons --, world_<s>/archive/MANIFEST.json and
the season / people / relations files that manifest names. Every file is opened for reading only. A season is used
only when it is both merged in the run state and published in the archive manifest at read time.

Each season file (~65 MB of JSON) is decoded once and reduced to a compact summary cached under
armsan/cache/<folder key>/<season file stem>.pkl; the season file's name carries its generation and is never
rewritten, so a cached summary stays valid and a rerun decodes only seasons added since.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os
import pickle
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.dont_write_bytecode = True          # never write __pycache__ into the pinned build checkout

HERE = Path(__file__).resolve().parent
CACHE = HERE / 'cache'
EXTRACT_VERSION = 3                       # bump when the summary's contents change


def use_build(build):
    """Make the pinned build's golfsim importable (read only)."""
    b = str(Path(build).resolve())
    if b not in sys.path:
        sys.path.insert(0, b)


# ---- the build's own definitions -----------------------------------------------------------------------------------
def build_defs():
    from golfsim import season as SN
    from golfsim.calendar import TOUR_BY_KEY
    from golfsim.geography import COUNTRIES
    return {'OPEN_AMATEUR_REGIONS': {k: tuple(v) for k, v in SN.OPEN_AMATEUR_REGIONS.items()},
            'EXPANSION': SN.AMATEUR_OPEN_EXPANSION,
            'ELIG': {k: t.eligibility for k, t in TOUR_BY_KEY.items()},
            'REGION': {c: v.region for c, v in COUNTRIES.items()}}


def ordinary_open(e, defs):
    """golfsim/season.py ordinary_open_amateur, from an archived edition: tier 6, category 'regular', amateur
    eligibility (the series' eligibility is its tour's: calendar.py) and a tour in OPEN_AMATEUR_REGIONS."""
    t = e['tour']
    return (e['tier'] == 6 and e['category'] == 'regular' and defs['ELIG'].get(t) == 'amateur'
            and t in defs['OPEN_AMATEUR_REGIONS'])


# ---- safe reads ------------------------------------------------------------------------------------------------------
def read_json(p):
    with open(p, 'rb') as f:
        raw = f.read()
    if str(p).endswith('.gz'):
        raw = gzip.decompress(raw)
    return json.loads(raw)


def archive_manifest(arch):
    for attempt in range(10):
        try:
            m = json.loads((Path(arch) / 'MANIFEST.json').read_text())
            m['files']['years'] = {int(y): f for y, f in m['files']['years'].items()}
            return m
        except (OSError, ValueError):
            time.sleep(0.2 * (attempt + 1))
    raise SystemExit(f'cannot read {arch}/MANIFEST.json')


def read_table(arch, name):
    """A cumulative table (people / relations) as the current manifest names it (re-read if collected meanwhile)."""
    for attempt in range(10):
        m = archive_manifest(arch)
        try:
            return read_json(Path(arch) / m['files'][name]), m['files'][name]
        except FileNotFoundError:
            time.sleep(0.2 * (attempt + 1))
    raise SystemExit(f'cannot read {name} of {arch}')


def run_state(folder):
    """(data, debug) of the run as merged so far: the state pickle (every season) or the seed json (every 5),
    whichever holds more seasons. Rows are kept as the harness wrote them (lists in long_world.ROW order)."""
    folder = Path(folder)
    man = json.loads((folder / 'manifest.json').read_text())
    cands = []
    for p in sorted(folder.glob('seed_*.state.pkl')):
        with open(p, 'rb') as f:
            data, debug, _created, _initial = pickle.load(f)
        cands.append((data['years'], 'state.pkl', data, debug))
    for p in sorted(folder.glob('seed_*.json.gz')):
        if p.name.endswith('.debug.json.gz'):
            continue
        d = read_json(p)
        dbg_p = p.with_name(p.name.replace('.json.gz', '.debug.json.gz'))
        dbg = read_json(dbg_p) if dbg_p.exists() else {'rows': {}}
        cands.append((d['years'], 'seed json', d, dbg))
    if not cands:
        return man, None, None, None
    cands.sort(key=lambda c: c[0])
    years, src, data, debug = cands[-1]
    norm = lambda dd: {int(y): v for y, v in dd.items()}
    data['rows'] = {int(y): {int(g): v for g, v in yr.items()} for y, yr in data['rows'].items()}
    data['extras'] = norm(data.get('extras', {}))
    data['transitions'] = norm(data.get('transitions', {}))
    data['checks'] = norm(data.get('checks', {}))
    debug_rows = norm(debug.get('rows', {}))
    return man, data, debug_rows, src


# ---- one season ----------------------------------------------------------------------------------------------------
def extract_season(path, year, defs, homeclub_country, lib_sites):
    """The compact summary of one season file (see the module note)."""
    from golfsim import weather as WX
    from golfsim import decision_evidence as DE
    d = read_json(path)
    out = {'version': EXTRACT_VERSION, 'year': year, 'file': Path(path).name}
    exp = defs['EXPANSION']
    oo, open_starts, t5_starts, all_starts = {}, defaultdict(Counter), Counter(), Counter()
    weather = []
    home_floor = Counter()            # gid -> starts at a home club found by country (the floor can apply there)
    for e in d['events']:
        starters = []
        for site in e.get('finish') or []:
            starters.extend(r[0] for r in site)
        for g in starters:
            all_starts[g] += 1
        if ordinary_open(e, defs):
            oo[e['id']] = {'tour': e['tour'], 'week': e['week'], 'cap': int(e['field_size'] * exp),
                           'entrants': len(e.get('routes') or {}), 'starters': len(set(starters))}
            for g in starters:
                open_starts[g][e['tour']] += 1
        elif e['tier'] == 5:
            for g in starters:
                t5_starts[g] += 1
        for si, (site, rounds) in enumerate(zip(e.get('sites') or [], e.get('conditions') or [])):
            cid, _layout, city = site[0], site[1], site[2]
            s = lib_sites.get(cid) or {}
            country = s.get('country') or (WX.CITY_BY_NAME[city].country if city in WX.CITY_BY_NAME else '')
            cl = WX._climate(s.get('city') or city or '', country, s.get('style') or '')
            cm = WX.month_of(e['week'])
            lm = WX.local_month(cm, cl.south)
            for r in rounds or []:
                if r is None:
                    continue
                weather.append((cl.group, cm, lm, cl.coastal, cl.south, r[0], r[1],
                                r[4] if len(r) >= 5 else None, e['tier']))
        if homeclub_country:
            for si, site in enumerate(e.get('sites') or []):
                ids = (e.get('finish') or [[]])[si] if si < len(e.get('finish') or []) else []
                for row in ids:
                    hc = homeclub_country.get(row[0])
                    if hc and _club_at(hc, year, e['week']) == ('country', site[0]):
                        home_floor[row[0]] += 1
    out['oo'] = oo
    out['open_starts'] = {g: dict(c) for g, c in open_starts.items()}
    out['t5_starts'] = dict(t5_starts)
    out['all_starts'] = dict(all_starts)
    out['weather'] = weather
    out['home_floor_starts'] = dict(home_floor)
    out['familiar_base'] = {int(g): n for g, n in d.get('familiar_base', {}).items()}
    car = {}
    for gs, c in d['careers'].items():
        gid = int(gs)
        res = c.get('residence')
        rec = {'status': c['status'], 'lifestyle': c['lifestyle'], 'tour': c['tour'], 'events': c['events'],
               'overall': (c.get('ratings') or [None])[0], 'res': res[0] if res else None,
               'am_end': c.get('am_end')}
        if c['status'] == 'amateur':
            sh = alt = sh_any = 0
            for wk, why, wanted, played in c.get('denied') or ():
                if wanted in oo:
                    if why.startswith('shut out'):
                        sh += 1
                    elif why == 'played: alternative':
                        alt += 1
                if why.startswith(('shut out', 'not selected')):
                    sh_any += 1
            rec.update({'oo_shut': sh, 'oo_alt': alt, 'shut_any': sh_any, 'access': c.get('access') or {}})
        car[gid] = rec
    out['careers'] = car
    out['transitions'] = d.get('transitions', [])
    out['work_pathway'] = d.get('work_pathway', [])
    out['cash_blocked_max'] = {int(g): n for g, n in d.get('cash_blocked_max', {}).items()}
    # decision evidence: the monthly plans of amateurs outside college (the work pathway's tracked group) and the
    # career evaluations of every amateur -- through decision_evidence.read
    blk = d.get('decision_evidence')
    out['evidence_format'] = blk.get('format') if blk else None
    plans, careers_ev = {}, {}
    if blk:
        for gid, rec in car.items():
            if rec['status'] != 'amateur':
                continue
            ev = DE.read(d, gid)
            if not rec['tour'].startswith('CO_'):
                plans[gid] = [(r['week'], r['availability'], r['plan'], r['injured_weeks']) for r in ev['schedule']]
            if ev['careers']:
                careers_ev[gid] = [(c['model'], c['p'], c['outcome']) for c in ev['careers']]
    out['plans'] = plans
    out['career_ev'] = careers_ev
    dg = (d.get('diagnostics') or {})
    lay = (dg.get('layout') or {}).get('overall_by_source', [25, 30])
    out['dev'] = {int(g): round(sum(v[lay[0]:lay[1]]), 3) for g, v in (dg.get('development') or {}).items()
                  if car.get(int(g), {}).get('status') == 'amateur'}
    pr = d.get('prestige') or {}
    nat = pr.get('nations') or {}
    out['prestige'] = {'format': pr.get('format'), 'multiplier': nat.get('multiplier', {}), 'shares': nat.get('shares', {}),
                       'baseline_shares': nat.get('baseline_shares', {}), 'prestige': nat.get('prestige', {}),
                       'entrant_year': nat.get('entrant_year'), 'allocated': nat.get('allocated', {}),
                       'totals': nat.get('totals', {}),
                       'venue_moves_decided': pr.get('venue_moves_decided', []),
                       'venue_moves_total': len(pr.get('venue_moves', []))}
    del d
    return out


def _club_at(rows, year, week):
    """(basis, course) of a golfer's home club at (year, week) from their dated home-club rows."""
    cur = None
    for y, w, cid, basis in rows:
        if (y, w) <= (year, week):
            cur = (basis, cid)
    return cur


def folder_key(folder):
    return hashlib.sha1(str(Path(folder).resolve()).encode()).hexdigest()[:12] + '_' + Path(folder).name


def prune(summary, keep):
    """Only the parts a report reads (careers lose the access counts, which no table uses)."""
    if keep is None:
        return summary
    out = {k: v for k, v in summary.items() if k in keep or k in ('version', 'year', 'file', 'evidence_format')}
    if 'careers' in out:
        out['careers'] = {g: {k: v for k, v in c.items() if k != 'access'} for g, c in out['careers'].items()}
    return out


def load_arm(folder, build, log=print, keep=None):
    """Everything the report reads of one arm: run state, committed seasons and their summaries."""
    use_build(build)
    folder = Path(folder)
    man, data, debug, src = run_state(folder)
    if data is None:
        return {'folder': str(folder), 'man': man, 'seasons': [], 'note': 'no run state yet'}
    seed = data['seed']
    arch = folder / f'world_{seed}' / 'archive'
    am = archive_manifest(arch)
    merged = sorted(data['rows'])
    published = sorted(am['files']['years'])
    seasons = [y for y in merged if y in published]
    defs = build_defs()
    people, people_file = read_table(arch, 'people')
    relations, rel_file = read_table(arch, 'relations')
    hc_country = {}
    for gs, p in people.items():
        rows = ((p.get('golfer') or {}).get('home_club') or [])
        if any(r[3] == 'country' for r in rows):
            hc_country[int(gs)] = [(r[0], r[1], r[2], r[3]) for r in rows]
    from golfsim.course_library import default_library
    lib_sites = default_library().sites
    cdir = CACHE / folder_key(folder)
    cdir.mkdir(parents=True, exist_ok=True)
    summ = {}
    for y in seasons:
        f = am['files']['years'][y]
        cp = cdir / (Path(f).name.replace('.json.gz', '') + f'.v{EXTRACT_VERSION}.pkl')
        if cp.exists():
            with open(cp, 'rb') as fh:
                summ[y] = prune(pickle.load(fh), keep)
            continue
        t = time.perf_counter()
        s = extract_season(arch / f, y, defs, hc_country, lib_sites)
        with open(str(cp) + '.tmp', 'wb') as fh:
            pickle.dump(s, fh, protocol=pickle.HIGHEST_PROTOCOL)
        os.replace(str(cp) + '.tmp', cp)
        summ[y] = prune(s, keep)
        del s
        log(f'  {folder.name} {y}: extracted in {time.perf_counter() - t:.1f} s')
    rel_small = {'stints': [(s['kind'], s['staff'], s['golfer'], tuple(s['start']), s['arrangement'], s['started_by'],
                             s.get('reason_start', ''), s.get('reason_accept', '')) for s in relations.get('stints', [])],
                 'refusals': [tuple(r) for r in relations.get('refusals', [])]}
    del relations
    people_small = {int(g): {'name': p.get('name'), 'born': p.get('born'), 'country': p.get('country'),
                             'created': p.get('created'),
                             'hc_from': ((p.get('golfer') or {}).get('home_club_familiarity') or {}).get('from'),
                             'hc_basis': (((p.get('golfer') or {}).get('home_club') or [[None] * 4])[-1][3]),
                             'status': (p.get('golfer') or {}).get('status'),
                             'lifestyle': (p.get('golfer') or {}).get('lifestyle'),
                             'tour': (p.get('golfer') or {}).get('tour'),
                             'staff': bool(p.get('caddie') or p.get('coach')),
                             'died': (p.get('died') or {}).get('year') if isinstance(p.get('died'), dict) else p.get('died')}
                    for g, p in people.items()}
    return {'folder': str(folder), 'name': folder.name, 'man': man, 'seed': seed, 'state_source': src,
            'merged': merged, 'published': published, 'seasons': seasons, 'data': data, 'debug': debug,
            'summ': summ, 'people': people_small, 'people_file': people_file, 'relations': rel_small,
            'relations_file': rel_file, 'defs': defs, 'arm': data.get('arm') or man.get('arm'),
            'pathway_min_age': data.get('work_pathway_min_age'), 'archive_generation': am.get('generation')}
