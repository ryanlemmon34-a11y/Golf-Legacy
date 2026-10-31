"""Before/after table from staff_market_measure.py outputs (docs/RECRUITMENT_PACKAGE.md).
Usage: python tools/staff_market_compare.py before.json after.json [before2.json after2.json ...]"""
import json
import sys
from collections import defaultdict

files = sys.argv[1:]
pairs = [(json.load(open(files[i])), json.load(open(files[i + 1]))) for i in range(0, len(files), 2)]


def per_season(d, f):
    return [f(r) for _, r in sorted(d['rows'].items())]


def fmt(xs):
    return ' / '.join('—' if x is None else (f'{x:.2f}' if isinstance(x, float) else str(x)) for x in xs)


rows = [
    ('Coach partnerships (season start)', lambda r: r['coach_pairs']),
    ('  of which share deals', lambda r: r['share_deals']),
    ('Caddie partnerships', lambda r: r['caddie_pairs']),
    ('Coach stints begun', lambda r: r['began'].get('coach', 0)),
    ('Coach stints ended', lambda r: r['ended'].get('coach', 0)),
    ('  ended: retirement', lambda r: r['causes'].get('coach retirement', 0)),
    ('  ended: golfer change', lambda r: r['causes'].get('coach golfer change', 0)),
    ('  ended: coach moved on', lambda r: r['causes'].get('coach staff moved on', 0)),
    ('  ended: money', lambda r: r['causes'].get('coach money', 0)),
    ('  ended: left for a better-known offer', lambda r: r['causes'].get('coach offer', 0)),
    ('Caddie stints ended', lambda r: r['ended'].get('caddie', 0)),
    ('  ended: retirement', lambda r: r['causes'].get('caddie retirement', 0)),
    ('  ended: golfer change', lambda r: r['causes'].get('caddie golfer change', 0)),
    ('  ended: money', lambda r: r['causes'].get('caddie money', 0)),
    ('Mean length of ended coach stints (yrs)', lambda r: r['mean_len']['coach']),
    ('Mean length of ended caddie stints (yrs)', lambda r: r['mean_len']['caddie']),
    ('Refusals: golfer said no to a coach', lambda r: r['refusals'].get('coach refused by golfer', 0)),
    ('Refusals: coach said no to a golfer', lambda r: r['refusals'].get('coach refused by coach', 0)),
    ('Refusals: caddie said no to a golfer', lambda r: r['refusals'].get('caddie refused by caddie', 0)),
]
for lvl in ('Premier', 'Challenger', 'pro other', 'pro part-time', 'college', 'amateur'):
    rows.append((f'Share with a coach: {lvl}', lambda r, l=lvl: r['coached_share'].get(l)))
for k in ('<=23 none', '<=23 fee', '<=23 share', '24-30 none', '24-30 fee', '31+ none', '31+ fee'):
    rows.append((f'Mean Overall change, {k}', lambda r, k=k: r['dev'].get(k, [None])[0]))
rows.append(('Reconcile errors / staff violations', lambda r: f"{r['checks']['reconcile_errors']}/{r['checks']['staff_violations']}"))
rows.append(('Coach paid == received; caddie paid == received',
             lambda r: f"{r['checks']['coach_paid'] == r['checks']['coach_received']}/{r['checks']['caddie_paid'] == r['checks']['caddie_received']}"))

head = '| Measure (season 1 / 2 / 3) |' + ''.join(f' Seed {b["seed"]} before | Seed {b["seed"]} after |' for b, _ in pairs)
print(head)
print('|---|' + '---|---|' * len(pairs))
for name, f in rows:
    print(f'| {name} |' + ''.join(f' {fmt(per_season(b, f))} | {fmt(per_season(a, f))} |' for b, a in pairs))
