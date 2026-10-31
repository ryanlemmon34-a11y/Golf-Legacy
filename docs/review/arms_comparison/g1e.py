#!/usr/bin/env python3
"""G1.e: one same-seed season with the familiarity baseline on and off -- read-only analysis, writes G1E_FAMILIARITY.md.

    nice -n 19 ionice -c3 python3 -B g1e.py [--on DIR] [--off DIR] [--summary fam_off.json] [--smoke smoke.json]

Reads, for each world, only its archive MANIFEST.json and the files it names (season file, people tables of
generation 0 and of the published generation). No World/Session/Archive object is opened. Whether the regional
baseline applied to a start is reconstructed with the build's own functions (familiarity.baseline / home_floor,
course_library.course_place) from the recorded places, home clubs and familiarity -- exactly for the first week, when
every golfer's familiarity is still the creation value (recorded empty in the generation-0 people table).
"""
from __future__ import annotations

import argparse
import gzip
import json
import statistics as S
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
V18 = HERE.parent


def read(p):
    return json.loads(gzip.decompress(Path(p).read_bytes()) if str(p).endswith('.gz') else Path(p).read_text())


def table(head, rows):
    out = ['| ' + ' | '.join(map(str, head)) + ' |', '|' + '---|' * len(head)]
    return '\n'.join(out + ['| ' + ' | '.join(map(str, r)) + ' |' for r in rows])


def frac(a, b):
    return f'{a}/{b} ({100 * a / b:.1f}%)' if b else f'{a}/0'


def msd(xs):
    if not xs:
        return '—'
    return (f'{S.mean(xs):+.3f} (sd {S.stdev(xs):.3f}, se {S.stdev(xs) / len(xs) ** 0.5:.3f}, n={len(xs)})'
            if len(xs) > 1 else f'{xs[0]:+.3f} (n=1)')


def load(world):
    arch = Path(world) / 'archive'
    m = json.loads((arch / 'MANIFEST.json').read_text())
    y, f = next(iter(sorted(m['files']['years'].items())))
    d = read(arch / f)
    ev = {}
    for e in d['events']:
        sc = [{int(g): v for g, v in s.items()} for s in (e.get('scores') or [])]
        ev[e['id']] = {'week': e['week'], 'tier': e['tier'], 'kind': e['kind'], 'sites': [s[0] for s in e['sites']],
                       'scores': sc, 'field': [sorted(s) for s in sc],
                       'winners': [r[0] for site in (e.get('finish') or []) for r in site if r[1] == 1][:1]}
    out = {'year': int(y), 'events': ev, 'familiar_base': {int(g): n for g, n in d.get('familiar_base', {}).items()},
           'has_familiar_base': 'familiar_base' in d, 'file': f}
    del d
    p0 = read(arch / 'people.g000000.json.gz') if (arch / 'people.g000000.json.gz').exists() else {}
    out['fam0_empty'] = sum(1 for v in p0.values() if v.get('golfer') and v['golfer'].get('familiar') == [])
    out['fam0_n'] = sum(1 for v in p0.values() if v.get('golfer'))
    del p0
    pe = read(arch / m['files']['people'])
    out['people'] = {int(g): {'birth': (v.get('birthplace') or {}),
                              'res': ((v.get('first_residence') or {}).get('place') or {}),
                              'res_when': ((v.get('first_residence') or {}).get('year'), (v.get('first_residence') or {}).get('week')),
                              'moves': [(mv.get('year'), mv.get('week')) for mv in v.get('moves') or []],
                              'clubs': [(r[0], r[1], r[2], r[3]) for r in ((v.get('golfer') or {}).get('home_club') or [])],
                              'hc_from': ((v.get('golfer') or {}).get('home_club_familiarity') or {}).get('from')}
                     for g, v in pe.items() if v.get('golfer')}
    del pe
    return out


def round_means(s):
    n = max((len(v) for v in s.values()), default=0)
    return [S.mean(v[k] for v in s.values() if len(v) > k) for k in range(n)]


def vs_field(v, means, upto=None):
    k = len(v) if upto is None else upto
    return S.mean(v[i] - means[i] for i in range(k)) if k else None


def place(p):
    return (p.get('country'), p.get('region')) if p and p.get('country') else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--build', default=str(V18 / 'arms' / 'build_c0d1ea5'))
    ap.add_argument('--on', default=str(V18 / 'smoke' / 'final_c0d1ea5' / 'world_off'))
    ap.add_argument('--off', default=str(V18 / 'fam' / 'out_c0d1ea5' / 'world_famoff'))
    ap.add_argument('--summary', default=str(V18 / 'fam' / 'out_c0d1ea5' / 'fam_off.json'))
    ap.add_argument('--out', default=str(HERE / 'G1E_FAMILIARITY.md'))
    a = ap.parse_args()
    sys.path.insert(0, str(Path(a.build).resolve()))
    from golfsim import familiarity as FAM, schedule as SCH
    from golfsim.course_library import default_library, course_place
    from golfsim.geography import COUNTRIES
    lib = default_library(SCH.DEFAULT)
    ON, OFF = load(a.on), load(a.off)
    summ = json.loads(Path(a.summary).read_text())
    year = ON['year']

    def club_at(rows, wk):
        cur = None
        for y_, w_, cid, basis in rows:
            if (y_, w_) <= (year, wk):
                cur = (cid, basis)
        return cur

    def base(g, cid, wk, people):
        """Season.course_baseline for golfer g at course cid in week wk of the season (places recorded at week 0;
        golfers' moves happen only at week 53)."""
        p = people.get(g)
        site = lib.sites.get(cid)
        if p is None or site is None:
            return 0.0, None
        b = FAM.baseline(course_place(site), (place(p['birth']), place(p['res'])))
        club = club_at(p['clubs'], wk)
        return FAM.home_floor(b, club is not None and club[0] == cid)

    L = ['# G1.e: same-seed season with the familiarity baseline on and off', '']
    L.append(f'Two fresh full-population worlds, seed {summ["seed"]}, build c0d1ea5, decision evidence off, one season '
             f'({year}) each, read-only from their archives: ON = `smoke/final_c0d1ea5/world_off` (the regional baseline '
             'and home-club floor on, the build default; "off" in that folder name refers to the decision evidence), '
             'OFF = `fam/out_c0d1ea5/world_famoff` (`Season.familiar_base_on = False` set before the season; '
             'fam/fam_off.py). Every outcome part differs between them (fam_off.json `parts_differing`: '
             + ', '.join(summ['parts_differing']) + ').')
    L.append('')
    # 1. divergence
    eo, ef = ON['events'], OFF['events']
    weeks = defaultdict(Counter)
    for eid in set(eo) | set(ef):
        x, y_ = eo.get(eid), ef.get(eid)
        w = (x or y_)['week']
        if not x or not y_:
            weeks[w]['held in one world only'] += 1
        elif x['field'] != y_['field']:
            weeks[w]['field differs'] += 1
        elif x['scores'] != y_['scores']:
            weeks[w]['same field, results differ'] += 1
        else:
            weeks[w]['identical'] += 1
    dw = min(w for w, c in weeks.items() if set(c) - {'identical'})
    first_ed = sorted(eid for eid, x in eo.items() if x['week'] == dw and eid in ef and x['scores'] != ef[eid]['scores'])
    L.append('## 1. Where the two worlds diverge')
    L.append('')
    L.append(table(['week', 'editions identical', 'same field, results differ', 'field differs', 'held in one world only'],
                   [(w, c['identical'], c['same field, results differ'], c['field differs'], c['held in one world only'])
                    for w, c in sorted(weeks.items()) if w <= dw + 2]))
    L.append('')
    L.append(f'The results first differ in week {dw}, the season\'s first week: every week-{dw} field is identical in the '
             f'two worlds (fields are set from the same starting state), and {len(first_ed)} of the '
             f'{sum(weeks[dw].values())} week-{dw} editions have different scores (first by id: {first_ed[0] if first_ed else "—"}). '
             f'Everything from week {dw + 1} on is a different world (fields differ from week {dw + 1}). The week-{dw} '
             'editions start from the same state with the same fields, so they allow a field-matched exploratory '
             'comparison (section 3) — not an isolated or causal measure of the baseline (see there why).')
    L.append('')
    # 2. what the baseline did
    starts_on = sum(len(s) for x in eo.values() for s in x['scores'])
    starts_off = sum(len(s) for x in ef.values() for s in x['scores'])
    fb = ON['familiar_base']
    hc_starts, hc_golfers = 0, set()
    for x in eo.values():
        for si, s in enumerate(x['scores']):
            cid = x['sites'][min(si, len(x['sites']) - 1)]
            for g in s:
                c = club_at((ON['people'].get(g) or {}).get('clubs', []), x['week'])
                if c and c[0] == cid and c[1] == 'country':
                    hc_starts += 1
                    hc_golfers.add(g)
    hc_from = Counter(p['hc_from'] for p in ON['people'].values())
    L.append('## 2. What the baseline did in the ON world')
    L.append('')
    L.append(f'- Starts where the regional baseline (home-club floor included) set the familiarity value (season file '
             f'`familiar_base`): {frac(sum(fb.values()), starts_on)} of all starts; golfers affected: {len(fb):,}.')
    L.append(f'- Starts at a golfer\'s home club found by country (the only case where the home-club floor can add '
             f'anything; it applies there only while fewer than 3 rounds were played — an upper bound, the floor is not '
             f'recorded per start): {hc_starts} starts by {len(hc_golfers)} golfers. Home-club familiarity source at the '
             'season end (people table): ' + ', '.join(f'{k} {v}' for k, v in hc_from.most_common()) + '.')
    L.append(f'- OFF world: `familiar_base` present ({OFF["has_familiar_base"]}) with {sum(OFF["familiar_base"].values())} '
             f'applications over {len(OFF["familiar_base"])} golfers — no baseline application recorded. Starts: '
             f'{starts_off:,} (ON {starts_on:,}).')
    L.append('')
    # 3. scoring: week-1 pairs
    assert ON['fam0_empty'] == ON['fam0_n'], 'creation familiarity not empty'
    pairs = defaultdict(list)          # (applied?, measure) -> differences ON - OFF
    n_app = Counter()
    app_golfers = set()
    for eid, x in eo.items():
        if x['week'] != dw or eid not in ef or x['field'] != ef[eid]['field']:
            continue
        for si, (sa, sb) in enumerate(zip(x['scores'], ef[eid]['scores'])):
            cid = x['sites'][min(si, len(x['sites']) - 1)]
            ma_, mb_ = round_means(sa), round_means(sb)
            r1a, r1b = ma_[0], mb_[0]
            for g in sa:
                rounds_ = min(len(sa[g]), len(sb[g]))
                b, basis = base(g, cid, dw, ON['people'])
                key = basis if b > 0 else 'none'           # rounds played before week 1: 0 for everyone (creation)
                n_app[key] += 1
                if b > 0:
                    app_golfers.add(g)
                pairs[(key, 'r1')].append((sa[g][0] - r1a) - (sb[g][0] - r1b))
                pairs[(key, 'r1raw')].append(sa[g][0] - sb[g][0])
                if rounds_:
                    pairs[(key, 'all')].append(vs_field(sa[g], ma_, rounds_) - vs_field(sb[g], mb_, rounds_))
    applied = sum(v for k, v in n_app.items() if k != 'none')
    in_fb = sum(1 for g in app_golfers if g in ON['familiar_base'])
    L.append('## 3. Scoring')
    L.append('')
    L.append(f'**Week {dw}: a field-matched exploratory comparison (not an isolated or causal effect).** Every '
             f'golfer\'s familiarity at creation is recorded empty (generation-0 people table: {ON["fam0_empty"]}/'
             f'{ON["fam0_n"]} golfers), so before week {dw} no rounds had been played anywhere and the baseline applied '
             'to a start exactly when it is positive for that golfer and course: reconstructed with the build\'s own '
             '`familiarity.baseline` and `home_floor` from the recorded birthplace, residence and home club '
             '(Season.course_baseline). Differences are ON − OFF for the same golfer in the same edition: round-1 '
             'score, round-1 score relative to the site\'s round-1 mean, and the mean over the rounds both worlds '
             'played of each round\'s score relative to that round\'s field mean. Why this is exploratory only: '
             'identical fields do not isolate the baseline\'s effect, because the engine\'s random stream is shared — '
             'once anything changes, every start\'s draws shift — so starts the baseline did not touch differ between '
             'the worlds too (the reference row), and subtracting that untreated reference row does not remove the '
             'contamination from the treated starts. Round 1 is the only round every starter played; the common-rounds '
             'and all-rounds comparison depends on who made the cut in each world, since rounds after the cut exist '
             f'only for those who made it. {applied} applied starts and {n_app["none"]} not-applied starts. Check: '
             f'{in_fb}/{len(app_golfers)} golfers with a reconstructed week-{dw} application are among the ON '
             'world\'s recorded `familiar_base` golfers.')
    L.append('')
    rows = []
    for key in sorted(n_app, key=lambda k: (k == 'none', k)):
        rows.append((f'baseline applied ({key})' if key != 'none' else 'baseline not applied (reference)', n_app[key],
                     msd(pairs[(key, 'r1raw')]), msd(pairs[(key, 'r1')]), msd(pairs[(key, 'all')])))
    bases = [k for k in n_app if k != 'none']
    allapp = [d for k in n_app if k != 'none' for d in pairs[(k, 'r1')]]
    allapp_all = [d for k in n_app if k != 'none' for d in pairs[(k, 'all')]]
    if len(bases) > 1:
        rows.append(('baseline applied (all bases)', applied, msd([d for k in n_app if k != 'none' for d in pairs[(k, 'r1raw')]]),
                     msd(allapp), msd(allapp_all)))
    L.append(f'Table: week-{dw} field-matched exploratory comparison, ON − OFF per start (negative = fewer strokes '
             'with the baseline on); mean (sd, naive se, n).')
    L.append('')
    L.append(table(['starts (week 1)', 'n', 'round-1 strokes, ON − OFF (all starters)', 'round-1 vs field, ON − OFF '
                    '(all starters)', 'common rounds vs field, ON − OFF (depends on the cut)'], rows))
    L.append('')
    L.append('The "se" values are naive sd/√starts: not clustered by event or field and not a calibrated causal '
             'uncertainty; no significance is claimed. The measured differences are reported as they are, with the '
             'caveats above; they do not show balance or prove an effect. One season, one seed.')
    L.append('')
    # after divergence: descriptive per world
    agg = {}
    for name, W in (('ON', ON), ('OFF', OFF)):
        stf = defaultdict(list)
        for eid, x in W['events'].items():
            if x['week'] <= dw:
                continue
            for si, s in enumerate(x['scores']):
                cid = x['sites'][min(si, len(x['sites']) - 1)]
                means = round_means(s)
                for g, v in s.items():
                    b, basis = base(g, cid, x['week'], W['people'])
                    m_ = vs_field(v, means) if v else None
                    if m_ is not None:
                        stf['eligible' if b > 0 else 'not eligible'].append(m_)
        agg[name] = stf
    L.append(f'**After week {dw} (descriptive across diverged worlds; no per-golfer causal reading).** Mean over rounds of '
             'a start\'s score relative to its round\'s field mean, for starts at courses where the baseline would '
             'apply by place (positive baseline for that golfer and course) and for the others. In the ON world the '
             'baseline is used only while the golfer\'s own rounds there are fewer than it; this split is by place '
             'only, in both worlds.')
    L.append('')
    L.append(table(['world', 'baseline-eligible starts: score vs field', 'other starts: score vs field'],
                   [(n, msd(agg[n]['eligible']), msd(agg[n]['not eligible'])) for n in ('ON', 'OFF')]))
    L.append('')
    # 4. season aggregates
    L.append('## 4. Season-level aggregates per world (descriptive)')
    L.append('')
    rows = []
    for name, W in (('ON', ON), ('OFF', OFF)):
        c = Counter()
        strokes = []
        for eid, x in W['events'].items():
            for si, s in enumerate(x['scores']):
                cid = x['sites'][min(si, len(x['sites']) - 1)]
                site = lib.sites.get(cid) or {}
                for g, v in s.items():
                    p = W['people'].get(g) or {}
                    home = (p.get('res') or {}).get('country') == site.get('country')
                    reg = (COUNTRIES[(p.get('res') or {}).get('country')].region == site.get('region')
                           if (p.get('res') or {}).get('country') in COUNTRIES else False)
                    c['home' if home else 'visitor'] += 1
                    c['home region' if reg else 'other region'] += 1
                    strokes += v
            for g in x['winners']:
                cid = x['sites'][0]
                site = lib.sites.get(cid) or {}
                p = W['people'].get(g) or {}
                c['win home' if (p.get('res') or {}).get('country') == site.get('country') else 'win visitor'] += 1
        rows.append((name, f'{c["home"] + c["visitor"]:,}', f'{S.mean(strokes):.3f} ({len(strokes):,} rounds)',
                     frac(c['home'], c['home'] + c['visitor']), frac(c['home region'], c['home region'] + c['other region']),
                     frac(c['win home'], c['win home'] + c['win visitor'])))
    L.append(table(['world', 'starts', 'scoring average, strokes per round (all rounds)', 'starts by golfers living in the '
                    'venue\'s country', 'starts by golfers living in the venue\'s region', 'wins (first site) by golfers '
                    'living in the venue\'s country'], rows))
    L.append('')
    L.append('"Home" is the golfer\'s residence at week 0 (recorded `first_residence`; golfers move only at week 53) '
             'against the course library\'s country and region of the venue. Venues outside the library count as '
             'visitors.')
    L.append('')
    # 5. timing
    L.append('## 5. Timing')
    L.append('')
    L.append(f'Season time with the baseline off: {summ["season_s_famoff"]} s; with it on (the final smoke\'s evidence-off '
             f'world): {summ["season_s_famon_smoke_off"]} s. These are one pair of total run times on a shared machine; '
             'no overhead claim is made from them.')
    L.append('')
    text = '\n'.join(L) + '\n'
    for pre in (str(V18) + '/', str(V18.resolve()) + '/'):
        text = text.replace(pre, '')
    Path(a.out).write_text(text)
    print('wrote', a.out, flush=True)


if __name__ == '__main__':
    main()
