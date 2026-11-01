"""Per season and nation, from the Test2 archive (read only): actual fame A (recomputed), the participation-only
expectation P (each site's fame split equally among its starters: ability ignored), starts, and wins by kind."""
import gzip, json, os, sys
sys.path.insert(0, sys.argv[3])
from golfsim import prestige as PR
A = sys.argv[1]
man = json.load(open(os.path.join(A, 'MANIFEST.json')))
people = json.load(gzip.open(os.path.join(A, man['files']['people'])))
country = {}
for pid, p in (people.items() if isinstance(people, dict) else []):
    country[int(pid)] = p.get('country')
out = {}
for y, f in sorted(man['files']['years'].items(), key=lambda x: int(x[0])):
    d = json.load(gzip.open(os.path.join(A, f)))
    book = {}
    for e in d['events']:
        if e.get('kind') == 'qualifying':
            continue
        p = e.get('prestige')
        if p is None:
            continue
        for si, site in enumerate(e.get('finish') or []):
            n = len(site)
            if not n:
                continue
            vals = [PR.fame_points(p, pos) for _, pos, _ in site]
            tot = sum(vals)
            for (gid, pos, _), v in zip(site, vals):
                c = country.get(gid)
                b = book.setdefault(c, {'A': 0.0, 'P': 0.0, 'starts': 0, 'wins': {}})
                b['A'] += v
                b['P'] += tot / n
                b['starts'] += 1
                cls = 'major' if e.get('kind') == 'major' else 'tier1' if e.get('tier') == 1 else                     'tier2_4' if (e.get('tier') or 9) <= 4 else 'tier5_8'
                bc = b.setdefault('by', {}).setdefault(cls, [0.0, 0.0, 0])
                bc[0] += v
                bc[1] += tot / n
                bc[2] += 1
                if pos == 1 and si == 0:
                    k = 'major' if e.get('kind') == 'major' else 'tier1' if e.get('tier') == 1 else f"tier{e.get('tier')}"
                    b['wins'][k] = b['wins'].get(k, 0) + 1
    out[y] = book
    print(y, len(book), flush=True)
json.dump(out, gzip.open(sys.argv[2], 'wt'))
