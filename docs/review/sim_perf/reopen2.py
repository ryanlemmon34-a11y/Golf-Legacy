"""Reopen a saved world with a given checkout and digest it part by part, memory-bounded: the simulation state parts
of tools/equivalence_check.parts (results, performance, rounds and holes, development, familiarity, finances, staff,
fatigue and injuries, rankings, records, moments, history log, cursor), and the published history one file at a time
(each season decoded, digested, freed; development and decision evidence digested on their own, as parts() does).
equivalence_check.parts decodes every season at once, which a 58-season world cannot hold in memory.
    PYTHONHASHSEED=0 python3 reopen2.py CODE WORLD OUT.json"""
import json, sys
from pathlib import Path
code, world, out = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
sys.path.insert(0, code)
sys.path.insert(0, str(Path(code) / 'tools'))
from golfsim.session import Session
from golfsim.archive import _read, read_manifest
import equivalence_check as EQ

s = Session.open(world, workers=1, allow_other_engine=True)
try:
    parts = EQ.parts(s, world / '__no_archive__')          # (state parts only: no MANIFEST there)
finally:
    s.close()
a = world / 'archive'
man = read_manifest(a)
seasons, diag, dec = {}, {}, {}
for y, f in sorted(man['files']['years'].items()):
    d = _read(a / f)
    diag[y] = EQ.digest(EQ.canon(d.pop('diagnostics', None)))
    dec[y] = EQ.digest(EQ.canon(d.pop('decision_evidence', None)))
    seasons[y] = EQ.digest(EQ.canon(d))
    del d
other = {k: EQ.digest(EQ.canon(_read(a / f) if f.endswith('.gz') else json.loads((a / f).read_text())))
         for k, f in man['files'].items() if k != 'years'}
parts['published_years'] = EQ.digest((man['years'], seasons, other))
parts['diagnostics'] = EQ.digest(diag)
parts['decision_evidence'] = EQ.digest(dec)
Path(out).write_text(json.dumps({'code': code, 'world': str(world), 'parts': parts, 'seasons': seasons}, indent=1,
                                sort_keys=True))
print(json.dumps(parts, indent=1, sort_keys=True))
