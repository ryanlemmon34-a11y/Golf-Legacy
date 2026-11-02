"""H1 from exact entrant records (no simulation): every paired-layer junior who enters near-finished (stored potential
80+, stored potential minus entry overall <= 3) under A0, B1 or B2, as the same candidate under all three arms.

    python3 -I h1_rows.py <checkout> <run directory> <out.md> <out.json>

Columns: candidate key; peak-age draw p; career luck (entry overall minus raw potential plus the youth deficit, as the
generator added it; '-' where the entry was capped at 99); the youth tempo under each arm; entry overall, stored
potential and the stored-potential gap (stored potential minus entry) under A0 / B1 / B2; whether the arm touches the
candidate (p below its knee: B1 24.5, B2 25.5).
"""
import json
import os
import pickle
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import study as S  # noqa: E402

S.setup(sys.argv[1])
RUN, OUT_MD, OUT_JSON = sys.argv[2], sys.argv[3], sys.argv[4]
MAN = json.load(open(os.path.join(RUN, 'manifest.json')))
ARMS = ('A0', 'B1', 'B2')
KNEE = {'B1': S.ARMS['B1'].knee[0], 'B2': S.ARMS['B2'].knee[0]}

ents = {a: {} for a in ARMS}
for s in MAN['config']['paired_seeds']:
    r = pickle.load(open(os.path.join(RUN, f'paired_{s}_juniors.pkl'), 'rb'))
    if r.get('manifest') != MAN['hash']:
        raise SystemExit('manifest mismatch')
    for a in ARMS:
        for e in r['entrants'][a]:
            ents[a][e['key']] = e


def near(e):
    return e is not None and e['pot_s'] >= 80 and e['pot_s'] - e['cur'] <= 3


keys = sorted({k for a in ARMS for k, e in ents[a].items() if near(e)})
rows = []
for k in keys:
    base = next(ents[a][k] for a in ARMS if k in ents[a])
    p, pot, aging = base['peak'], base['pot'], base['aging']
    row = {'key': k, 'p': p, 'raw_potential': pot}
    a0 = ents['A0'].get(k)
    if a0 is not None and a0['cur'] < 99:
        row['luck'] = a0['cur'] - (pot - S.deficit(18, a0['tempo'], p, aging))
    else:
        row['luck'] = None
    for a in ARMS:
        e = ents[a].get(k)
        row[a] = None if e is None else {'tempo': e['tempo'], 'entry': e['cur'], 'stored': e['pot_s'],
                                         'gap': e['pot_s'] - e['cur'], 'near': near(e)}
    row['touched'] = {a: p < KNEE[a] for a in KNEE}
    rows.append(row)


def cell(x, nd=2):
    return '-' if x is None else f'{x:.{nd}f}'


L = ['# H1 from exact entrant records: near-finished high-potential juniors (paired layer, five seeds)', '',
     f'Run {MAN["hash"]}. Near-finished: stored potential 80+ and stored potential minus entry overall <= 3, from the '
     'entrant records themselves (no histogram). Every candidate near-finished under any of A0, B1, B2, followed under '
     'all three. Luck: what the generator added to raw potential minus the youth deficit (A0 tempo = p).', '',
     '| candidate | p | touched by B1 (p < 24.5) / B2 (p < 25.5) | raw potential | luck | A0 tempo, entry, stored, gap | '
     'B1 tempo, entry, stored, gap | B2 tempo, entry, stored, gap | near-finished A0 / B1 / B2 |',
     '|---|---|---|---|---|---|---|---|---|']
for r in rows:
    arms = []
    for a in ARMS:
        x = r[a]
        arms.append('not an entrant' if x is None else
                    f'{x["tempo"]:.2f}, {x["entry"]:.2f}, {x["stored"]:.2f}, {x["gap"]:.2f}')
    L.append(f'| {r["key"]} | {r["p"]:.3f} | {"yes" if r["touched"]["B1"] else "no"} / {"yes" if r["touched"]["B2"] else "no"} | '
             f'{r["raw_potential"]:.2f} | {cell(r["luck"])} | ' + ' | '.join(arms) + ' | '
             + ' / '.join('yes' if r[a] and r[a]['near'] else 'no' for a in ARMS) + ' |')
n = {a: sum(1 for r in rows if r[a] and r[a]['near']) for a in ARMS}
L += ['', f'Near-finished entrants: A0 {n["A0"]}, B1 {n["B1"]}, B2 {n["B2"]}.']
json.dump(rows, open(OUT_JSON, 'w'), indent=1)
open(OUT_MD, 'w').write('\n'.join(L) + '\n')
print('\n'.join(L))
