"""Stream the archived seasons once and write compact analysis tables (read-only; nothing in the save changes).

Usage: python extract.py SAVE_DIR OUT_DIR [--procs N]

Writes to OUT_DIR:
  editions.csv.gz   one row per archived edition (gap12: the true gap between the first and second highest
                    pre-event Overall, 0 when the best are tied; gap_next_distinct: best minus the next lower
                    distinct value) (every event, every year), with its classification:
                    primary = one site, stroke play, not a qualifying event, a stored pre-event estimate whose
                    entrant list reconciles exactly with every starter at that site (made cut, missed cut,
                    withdrawn), and exactly one champion. Every excluded edition carries its reason.
  starts.npz        one row per starter of a primary edition: edition index, golfer id, pre-event Overall in exact
                    integer tenths (ovr10, as stored: no float rounding in tie groups), finishing position (0 = no position: missed cut / withdrew), total strokes,
                    rounds played (scores recorded), which separates a missed cut from a withdrawal.
  audit.json        coverage counts (formats, estimates, reconciliation, conditions, creation records, ratings).

Pre-event Overall is the value the engine stored in the edition's estimate (golfsim/upsets.py), computed in the
worker from the golfer objects that played the event, before any shot. Nothing here uses end-of-season or
current ratings.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import sys
from collections import Counter
from multiprocessing import Pool
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

COLS = ['idx', 'year', 'week', 'eid', 'series', 'tour', 'tier', 'category', 'kind', 'rounds', 'match_play',
        'n_sites', 'primary', 'reason', 'n', 'n_made', 'cut_top', 'course', 'layout', 'city', 'par', 'prestige',
        'playoff_holes', 'n_playoff', 'winner', 'w_ovr', 'w_rank', 'max_ovr', 'n_max', 'next_ovr', 'gap12', 'gap_next_distinct',
        'top_ids', 'top_best_pos', 'top_won', 'mean_ovr', 'sd_ovr', 'top10_mean_ovr', 'model', 'fav', 'fav_p',
        'w_p', 'w_p_rank', 'margin', 'win_total', 'sd_made', 'cond_rows', 'cond_len', 'wind_mean', 'wind_max',
        'wet_rounds', 'gust_mean', 'pins', 'cardenas_in', 'cardenas_won']


def _r1(x):
    return None if x is None else round(float(x), 1)


def classify(e):
    """(primary?, reason)."""
    if e.get('match_play'):
        return False, 'match play'
    if e.get('kind') == 'qualifying':
        return False, 'qualifying event'
    if len(e.get('sites') or ()) != 1:
        return False, 'multi-site'
    u = e.get('upset') or {}
    if not u:
        return False, 'no stored estimate'
    if not u.get('estimated'):
        return False, 'estimate not made: ' + str(u.get('why'))
    if not u.get('inputs'):
        return False, 'estimate without inputs'
    if u.get('site') != 0:
        return False, 'estimate for another site'
    fin = (e.get('finish') or [[]])[0]
    ids = u['inputs']['ids']
    fids = [r[0] for r in fin]
    if len(set(ids)) != len(ids) or len(set(fids)) != len(fids):
        return False, 'duplicate ids'
    if set(ids) != set(fids):
        return False, 'field does not reconcile'
    if any(o is None for o in u['inputs']['overall']):
        return False, 'missing pre-event Overall'
    champs = [r for r in fin if r[1] == 1]
    if len(champs) != 1:
        return False, f'{len(champs)} champions'
    if u.get('winner') != champs[0][0]:
        return False, 'estimate winner differs'
    return True, ''


def year_rows(arg):
    y, path, layouts = arg
    d = C.load_year(path)
    rows, starts, aud = [], [], Counter()
    for e in d['events']:
        prim, reason = classify(e)
        aud[('format', e['category'], e['kind'], e['tier'], bool(e.get('match_play')), len(e.get('sites') or ()),
             e['rounds'])] += 1
        aud[('class', 'primary' if prim else reason)] += 1
        u = e.get('upset') or {}
        aud[('model', u.get('model'), bool(u.get('estimated')))] += 1
        cond_all = e.get('conditions') or []
        for site_c in cond_all:
            for row in site_c or ():
                aud[('cond_len', len(row))] += 1
        site = (e.get('sites') or [[None, None, None]])[0]
        r = dict(year=y, week=e['week'], eid=e['id'], series=e['series'], tour=e['tour'], tier=e['tier'],
                 category=e['category'], kind=e['kind'], rounds=e['rounds'], match_play=int(bool(e.get('match_play'))),
                 n_sites=len(e.get('sites') or ()), primary=int(prim), reason=reason, cut_top=e.get('cut_top'),
                 course=site[0], layout=site[1], city=site[2], prestige=e.get('prestige'),
                 playoff_holes=e.get('playoff') or 0)
        r['par'] = layouts.get((site[0], site[1]))
        c0 = cond_all[0] if cond_all else []
        if c0:
            r.update(cond_rows=len(c0), cond_len=len(c0[0]), wind_mean=round(sum(x[0] for x in c0) / len(c0), 2),
                     wind_max=max(x[0] for x in c0), wet_rounds=sum(x[1] for x in c0), pins=c0[0][2],
                     gust_mean=(round(sum(x[4] for x in c0) / len(c0), 3) if len(c0[0]) >= 5 else None))
        if prim:
            fin = e['finish'][0]
            ids, ovs = u['inputs']['ids'], u['inputs']['overall']
            ov = dict(zip(ids, ovs))
            win = u['winner']
            mx = max(ovs)
            top = sorted(g for g in ids if ov[g] == mx)
            below = [o for o in ovs if o < mx]
            pos = {g: p for g, p, _ in fin}
            tot = {g: t for g, _, t in fin}
            made = [t for _, p, t in fin if p is not None and t is not None]
            tops = [pos[g] for g in top if pos[g] is not None]
            srt = sorted(ovs, reverse=True)
            wt = tot[win]
            others = sorted(t for g, p, t in fin if g != win and p is not None and t is not None)
            pls = (e.get('playoffs') or [{}])[0].get('players') if e.get('playoffs') else None
            r.update(n=len(ids), n_made=len(made), winner=win, w_ovr=ov[win], w_rank=1 + sum(1 for o in ovs if o > ov[win]),
                     max_ovr=mx, n_max=len(top), next_ovr=(max(below) if below else None),
                     gap12=(0.0 if len(top) > 1 else round(mx - max(below), 1) if below else None),
                     gap_next_distinct=(round(mx - max(below), 1) if below else None),
                     top_ids=';'.join(map(str, top)),
                     top_best_pos=(min(tops) if tops else 0), top_won=int(win in top),
                     mean_ovr=round(float(np.mean(ovs)), 2), sd_ovr=round(float(np.std(ovs)), 2),
                     top10_mean_ovr=round(float(np.mean(srt[:10])), 2), model=u.get('model'),
                     fav=u.get('favourite'), fav_p=u.get('favourite_p'), w_p=u.get('p'), w_p_rank=u.get('rank'),
                     margin=(others[0] - wt if others else None), win_total=wt,
                     sd_made=(round(float(np.std(made)), 3) if len(made) > 1 else None),
                     n_playoff=(len(pls) if pls else (1 if not e.get('playoff') else None)),
                     cardenas_in=int(C.CARDENAS in ov), cardenas_won=int(win == C.CARDENAS))
            sc = (e.get('scores') or [{}])[0]
            for g, p, t in fin:
                starts.append((g, ov[g], p or 0, t if t is not None else -1, len(sc.get(str(g)) or ())))
            aud[('reconcile', 'mc_or_wd_rows')] += sum(1 for _, p, _ in fin if p is None)
        rows.append((r, starts if prim else None))
        starts = []
    cr = (d.get('diagnostics') or {}).get('created') or {}
    for v in cr.values():
        aud[('created', v.get('path'))] += 1
    rat = sum(1 for g, yrs in (d.get('careers') or {}).items() if isinstance(yrs, dict) and yrs.get('ratings'))
    aud[('careers_with_ratings',)] += rat
    aud[('rules', d.get('rules'))] += 1
    aud[('calendar', json.dumps(d.get('calendar', {}).get('version')))] += 1
    return y, rows, aud


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('save')
    ap.add_argument('out')
    ap.add_argument('--procs', type=int, default=3)
    a = ap.parse_args()
    save, out = Path(a.save), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    world = json.loads(C.archive_file(save, 'world').read_text())
    layouts = {(cid, lk): lv.get('par') for cid, c in world['courses'].items() for lk, lv in c['layouts'].items()}
    yf = C.year_files(save)
    jobs = [(y, str(p), layouts) for y, p in yf.items()]
    with Pool(a.procs) as pool:
        res = sorted(pool.map(year_rows, jobs, chunksize=1), key=lambda t: t[0])
    aud = Counter()
    buf = io.StringIO()
    w = csv.DictWriter(buf, COLS, extrasaction='raise')
    w.writeheader()
    E, G, O, P, T, R = [], [], [], [], [], []
    idx = 0
    for y, rows, au in res:
        aud.update(au)
        for r, st in rows:
            r['idx'] = idx
            w.writerow(r)
            if st:
                for g, o, p, t, rp in st:
                    E.append(idx); G.append(g); O.append(o); P.append(p); T.append(t); R.append(rp)
            idx += 1
    with gzip.open(out / 'editions.csv.gz', 'wt', encoding='utf-8') as f:
        f.write(buf.getvalue())
    np.savez_compressed(out / 'starts.npz', edition=np.array(E, np.int32), gid=np.array(G, np.int32),
                        ovr10=np.array([round(o * 10) for o in O], np.int16), pos=np.array(P, np.int16),
                        total=np.array(T, np.int16),
                        rounds_played=np.array(R, np.int8))
    prov = {'save_meta': C.save_meta(save), 'scripts_commit': C.git_head(), 'scripts_dirty': C.git_dirty(),
            'year_files': {y: {'name': Path(p).name, 'sha256': C.sha256(p)} for y, p in yf.items()},
            'editions': idx, 'starts': len(E)}
    audit = {'provenance': prov,
             'counts': [[list(k), v] for k, v in sorted(aud.items(), key=lambda kv: (str(kv[0][0]), -kv[1]))]}
    (out / 'audit.json').write_text(json.dumps(audit, indent=1, default=str))
    print(f'{idx} editions, {len(E)} primary starts -> {out}')


if __name__ == '__main__':
    main()
