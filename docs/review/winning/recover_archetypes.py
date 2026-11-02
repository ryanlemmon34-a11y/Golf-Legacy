"""Recover each golfer's native generated archetype by replaying their own generation stream, and keep a label
ONLY when the complete creation attribute vector is reproduced from it (read-only; nothing in the save changes).

Usage: python recover_archetypes.py SAVE_DIR OUT_DIR

Why replay: the archive does not store the archetype label (it lives only in the pickled checkpoint, which this
study does not open). Every generated golfer draws from its own stream, random.Random(f'{seed}:golfer:{id}')
(initial world), f'{seed}:j{year}:golfer:{id}' (junior class) or f'{seed}:p{year}:golfer:{id}' (new
professionals): first the archetype (one rng.choices over the eight archetypes, equal weights in every nation:
nations.STYLES carries no archetype multipliers), then one gauss(0, 5) per attribute in ATTRIBUTE_KEYS order
(population._build_attrs). The attributes are then re-centred by a common shift (and clamped to 1..99) and
rounded to 0.1.

Validation (all 21 attributes, never Overall alone: every archetype is centred on the same Overall):
  residual_k = recorded_k - (archetype offset_k + nation tilt_k + age shift_k + replayed noise_k)
must be the same number for every attribute that is not clamped (1.0 or 99.0): the common re-centring shift.
Rounding to 0.1 allows a spread of at most 0.1 (+ float slack). A label is VERIFIED when the drawn archetype's
spread is <= 0.11 with at least 15 unclamped attributes and every clamped attribute is consistent with the clamp;
VERIFIED_CLAMPED when 8-14 attributes are unclamped (the rest consistent with the clamp) and no other archetype comes
within 1 point; the other seven archetypes' spreads are reported too
(identifiability margin). A golfer whose stream does not reproduce the vector is UNMATCHED and gets no label.
Golfers with no creation record (none archived: the cohort created for the unplayed next season) are UNKNOWN.
"""
from __future__ import annotations

import csv
import gzip
import io
import json
import random
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2]))
import common as C  # noqa: E402
from golfsim.golfer import ARCHETYPES  # noqa: E402
from golfsim.nations import NATIONS, STYLES  # noqa: E402
from golfsim.population import age_attribute_shift  # noqa: E402
from golfsim.ratings import ATTRIBUTE_KEYS  # noqa: E402

TOL = 0.11
NAMES = list(ARCHETYPES)


def stream_key(seed, path, year, gid):
    if path == 'initial':
        return f'{seed}:golfer:{gid}'
    if path == 'junior':
        return f'{seed}:j{year}:golfer:{gid}'
    if path == 'late_entrant':
        return f'{seed}:p{year}:golfer:{gid}'
    raise ValueError(path)


def spread(rec, base):
    """(spread of the residuals over unclamped attributes, their number, clamp-consistent?). Clamp-consistent: every
    attribute recorded at 99.0 (1.0) would sit at or above 99 (at or below 1) after the common shift."""
    res = [r - b for r, b in zip(rec, base) if 1.0 < r < 99.0]
    if not res:
        return 99.0, 0, False
    c = sorted(res)[len(res) // 2]
    clamp_ok = all((b + c >= 99.0 - 0.05) if r >= 99.0 else (b + c <= 1.05) if r <= 1.0 else True
                   for r, b in zip(rec, base))
    return max(res) - min(res), len(res), clamp_ok


def check(seed, gid, cr, style):
    rng = random.Random(stream_key(seed, cr['path'], cr['year'], gid))
    drawn = rng.choices(NAMES, [1.0] * len(NAMES))[0]
    noise = [rng.gauss(0, 5.0) for _ in ATTRIBUTE_KEYS]
    tilt = STYLES[style][0]
    age = cr['age']
    out = {}
    for a in NAMES:
        off = ARCHETYPES[a][0]
        base = [off.get(k, 0.0) + tilt.get(k, 0.0) + age_attribute_shift(k, age, None) + n
                for k, n in zip(ATTRIBUTE_KEYS, noise)]
        out[a] = spread(cr['attrs'], base)
    return drawn, out


def main():
    save, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    meta = C.save_meta(save)
    seed = int(meta['world_id'].split('-')[0])
    people = C.load_json_gz(save / 'archive' / f'people.g{meta["generation"]:06d}.json.gz')
    style = {c: p.style for c, p in NATIONS.items()}
    rows, stat = [], Counter()
    seen = set()
    for y, p in C.year_files(save).items():
        cr_all = (C.load_year(p).get('diagnostics') or {}).get('created') or {}
        for gid_s, cr in cr_all.items():
            gid = int(gid_s)
            seen.add(gid)
            country = people[gid_s]['country']
            drawn, sp = check(seed, gid, cr, style[country])
            s, n, clamp_ok = sp[drawn]
            alt = min(v[0] for a, v in sp.items() if a != drawn)
            if s <= TOL and n >= 15 and clamp_ok:
                status = 'verified'
            elif s <= TOL and n >= 8 and clamp_ok and alt > 1.0:
                status = 'verified_clamped'          # fewer unclamped attributes; the clamped ones are consistent
            else:
                status = 'unmatched'
            ok = status != 'unmatched'
            stat[(cr['path'], status)] += 1
            rows.append((gid, cr['path'], cr['year'], country, cr['age'], cr['overall'],
                         drawn if ok else '', status, round(s, 4), n, round(alt, 3)))
    golfers = [int(g) for g, v in people.items() if 'golfer' in v]
    unknown = sorted(set(golfers) - seen)
    for gid in unknown:
        v = people[str(gid)]
        rows.append((gid, 'none', v.get('created'), v['country'], None, None, '', 'unknown', None, None, None))
        stat[('none', 'unknown')] += 1
    rows.sort()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(['gid', 'path', 'created_year', 'country', 'age_at_creation', 'overall_at_creation', 'archetype',
                'status', 'spread', 'n_unclamped', 'best_alt_spread'])
    w.writerows(rows)
    with gzip.open(out / 'archetypes.csv.gz', 'wt', encoding='utf-8') as f:
        f.write(buf.getvalue())
    summ = {'save_meta': meta, 'tolerance': TOL, 'counts': {f'{a}/{b}': v for (a, b), v in sorted(stat.items())},
            'archetype_counts_verified': Counter(r[6] for r in rows if r[7].startswith('verified')),
            'verified_clamped': [r for r in rows if r[7] == 'verified_clamped'],
            'min_alt_spread_verified': min(r[10] for r in rows if r[7].startswith('verified')),
            'max_spread_verified': max(r[8] for r in rows if r[7].startswith('verified')),
            'scripts_commit': C.git_head()}
    (out / 'archetypes_summary.json').write_text(json.dumps(summ, indent=1))
    print(json.dumps(summ, indent=1))


if __name__ == '__main__':
    main()
