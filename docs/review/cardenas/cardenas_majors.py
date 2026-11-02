"""Martin Cardenas (PID 19411) in the original Test2 save: his actual major ledger, read-only (no simulation).

    python3 -I cardenas_majors.py <save folder> <out dir>

Reads the save's published history (archive/MANIFEST.json and the season files it names), hashing every file read,
and writes ledger.csv, ledger.json and SUMMARY.md. A start is an appearance in a major's recorded finish (any site);
the denominator of every rate is starts, never majors held. Status: 'finished' (an official position), 'MC' (no
position after the cut rounds), 'WD/DQ' (no position, fewer rounds than the cut). The champion is the one golfer
recorded at position 1 (a playoff decides a tie for first; the archive records the playoff in 'playoffs').
"""
import csv
import gzip
import hashlib
import json
import sys
from pathlib import Path

SAVE, OUT = Path(sys.argv[1]), Path(sys.argv[2])
PID = 19411
OUT.mkdir(parents=True, exist_ok=True)


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


man = json.loads((SAVE / 'archive' / 'MANIFEST.json').read_text())
meta = json.loads((SAVE / 'gen_000070' / 'meta.json').read_text())
people_file = SAVE / 'archive' / man['files']['people']
people = json.load(gzip.open(people_file, 'rt'))
me = people[str(PID)]
born = me.get('born')
prov = {'save': str(SAVE.name), 'current': json.loads((SAVE / 'CURRENT').read_text()),
        'world_id': meta['world_id'], 'engine': meta['engine'], 'generation': meta['generation'],
        'cursor': meta['cursor'], 'state_sha256': meta['sha256'], 'manifest_generation': man['generation'],
        'people_file': people_file.name, 'people_sha256': sha(people_file), 'years': [], 'person': {
            'id': PID, 'name': me.get('name'), 'country': me.get('country'), 'born': born}}
rows, held, anomalies = [], {}, []
for y in man['years']:
    f = SAVE / 'archive' / man['files']['years'][str(y)] if str(y) in man['files']['years'] else \
        SAVE / 'archive' / man['files']['years'][y]
    prov['years'].append({'year': y, 'file': f.name, 'sha256': sha(f)})
    data = json.load(gzip.open(f, 'rt'))
    majors = [e for e in data['events'] if e.get('kind') == 'major']
    held[y] = [e['id'] for e in majors]
    for e in majors:
        fin = [r for site in e['finish'] for r in site]
        first = [r[0] for r in fin if r[1] == 1]
        if len(first) != 1:
            anomalies.append({'event': e['id'], 'position_1': first, 'playoff': e.get('playoff'),
                              'playoffs': e.get('playoffs')})
        champion = first[0] if len(first) == 1 else None
        mine = [r for r in fin if r[0] == PID]
        if not mine:
            continue
        _, pos, total = mine[0]
        scores = {}
        for site in e['scores']:
            scores.update(site)
        rounds = len(scores.get(str(PID), []))
        cut_rounds = 2 if e.get('rounds', 4) == 4 else None
        if pos is not None:
            status = 'finished'
        elif cut_rounds is not None and rounds >= cut_rounds:
            status = 'MC'
        else:
            status = 'WD/DQ'
        tied = sum(1 for r in fin if r[1] == pos) > 1 if pos is not None else False
        rows.append({'year': y, 'event_id': e['id'], 'name': e['name'], 'week': e['week'],
                     'age': (y - born) if born is not None else None, 'rounds': rounds, 'status': status,
                     'finish': pos, 'tied': tied, 'total': total, 'won': champion == PID,
                     'winner_id': champion, 'field': len(fin), 'playoff': e.get('playoff')})
    print(y, len(majors), 'majors;', sum(1 for r in rows if r['year'] == y), 'starts', flush=True)

with open(OUT / 'ledger.csv', 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)


def rate(rs):
    n = len(rs)
    k = lambda f: sum(1 for r in rs if f(r))
    return {'starts': n, 'wins': k(lambda r: r['won']), 'top5': k(lambda r: r['finish'] is not None and r['finish'] <= 5),
            'top10': k(lambda r: r['finish'] is not None and r['finish'] <= 10), 'cuts_made': k(lambda r: r['status'] == 'finished'),
            'MC': k(lambda r: r['status'] == 'MC'), 'WD/DQ': k(lambda r: r['status'] == 'WD/DQ')}


bands = {'all': rows, '18-29': [r for r in rows if r['age'] < 30], '30-39': [r for r in rows if 30 <= r['age'] < 40],
         '40+': [r for r in rows if r['age'] >= 40]}
summary = {b: rate(rs) for b, rs in bands.items()}
years = sorted({r['year'] for r in rows})
best = None
for y0 in range(years[0], years[-1] - 8):
    rs = [r for r in rows if y0 <= r['year'] <= y0 + 9]
    s = rate(rs)
    key = (s['wins'], -y0)
    if best is None or key > best[0]:
        best = (key, y0, s)
per_year = [{'year': y, 'majors_held': len(held[y]), **rate([r for r in rows if r['year'] == y])} for y in man['years']]
json.dump({'provenance': prov, 'rows': rows, 'summary': summary, 'best_10_seasons': {'from': best[1], 'to': best[1] + 9, **best[2]},
           'per_year': per_year, 'anomalies': anomalies}, open(OUT / 'ledger.json', 'w'), indent=1)
print(json.dumps({'summary': summary, 'best': best[1:], 'anomalies': len(anomalies),
                  'majors_held_total': sum(len(v) for v in held.values())}, indent=1))
