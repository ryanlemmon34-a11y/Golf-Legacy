"""Extract compact per-year facts from a Golf Legacy archive (JSON files only; the pickle is never loaded).
usage: python -I extract_save.py ARCHIVE_DIR OUT.json"""
import glob
import gzip
import json
import os
import sys

arch, out = sys.argv[1], sys.argv[2]
people = json.load(gzip.open(sorted(glob.glob(os.path.join(arch, 'people*.json.gz')))[-1]))
born = {k: v.get('born') for k, v in people.items()}
names = {k: v.get('name') for k, v in people.items()}
res = {'created': {}, 'season': {}, 'majors': [], 'premier_wins': [], 'access': {}}
for f in sorted(glob.glob(os.path.join(arch, 'years', '*.json.gz'))):
    y = json.load(gzip.open(f))
    yr = y['year']
    for gid, c in y['diagnostics'].get('created', {}).items():
        res['created'][gid] = {k: c[k] for k in ('year', 'path', 'age', 'overall', 'potential', 'ceilings', 'attrs',
                                                  'peak_age', 'aging_rate') if k in c}
    snap = {}
    for gid, c in y['careers'].items():
        r = c.get('ratings')
        if r:
            snap[gid] = [r[0], max(r[1:]), sum(1 for v in r[1:] if v >= 98.95), c.get('tier'), c.get('events', 0),
                         c.get('status'), c.get('majors', 0), c.get('wins', 0)]
    res['season'][yr] = snap
    nmaj = 0
    for e in y['events']:
        if e.get('category') == 'major' or (e.get('tier') == 1 and e.get('category') in ('major',)):
            pass
        cat = e.get('category')
        fin = e.get('finish')
        if not fin:
            continue
        rows = fin[-1] if isinstance(fin[0][0], list) else fin
        win = [r[0] for r in rows if r[1] == 1]
        if cat == 'major':
            res['majors'].append([yr, e['id'], win[0] if win else None])
            nmaj += 1
        elif e.get('tier') == 1:
            res['premier_wins'].append([yr, e['id'], win[0] if win else None, cat])
    print(yr, len(snap), nmaj, file=sys.stderr)
res['born'] = born
res['names'] = names
json.dump(res, open(out, 'w'))
