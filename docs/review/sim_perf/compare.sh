#!/bin/sh
# compare.sh BASE_LABEL CAND_LABEL BASE_CODE CAND_CODE: the two advanced copies compared -- saved state (decompressed
# pickle bytes) and every published history file (decoded), then each reopened by its own build and digested part by
# part (equivalence_check.parts); results in runs/ (on disk).
H=/tmp/claude-0/-home-user-golf-legacy/dd633163-5093-57b8-a35e-3e668bc4257e/scratchpad/v19/perf17
cd $H
python3 eqcheck.py /dev/shm/v17/w_$1 /dev/shm/v17/w_$2 > runs/eq_$1_$2.txt 2>&1; echo "eqcheck rc=$?" >> runs/eq_$1_$2.txt
PYTHONHASHSEED=0 TMPDIR=/dev/shm/v17/tmp python3 reopen.py $3 /dev/shm/v17/w_$1 runs/reopen_$1.json > /dev/null 2>runs/reopen_$1.err; echo "reopen $1 rc=$?"
PYTHONHASHSEED=0 TMPDIR=/dev/shm/v17/tmp python3 reopen.py $4 /dev/shm/v17/w_$2 runs/reopen_$2.json > /dev/null 2>runs/reopen_$2.err; echo "reopen $2 rc=$?"
python3 - <<PY
import json
a = json.load(open('runs/reopen_$1.json'))['parts']; b = json.load(open('runs/reopen_$2.json'))['parts']
diff = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
print('reopen digests:', 'IDENTICAL' if not diff else 'DIFFERENT ' + str(diff), len(a), 'parts')
PY
tail -3 runs/eq_$1_$2.txt
