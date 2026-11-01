#!/bin/sh
# run.sh CODE LABEL [--profile]: one season (2084) of a fresh copy of the indexed Test2 master (/dev/shm/v17/master:
# test2_orig + the archive index its first open builds), PYTHONHASHSEED=0, 4 workers. The copy stays in
# /dev/shm/v17/w_LABEL for eqcheck/reopen; timing in runs/phases_LABEL.json (on disk).
H=/tmp/claude-0/-home-user-golf-legacy/dd633163-5093-57b8-a35e-3e668bc4257e/scratchpad/v19
W=/dev/shm/v17/w_$2
rm -rf $W && cp -r /dev/shm/v17/master $W
cd $H/perf17
P=""; [ "$3" = "--profile" ] && P="--profile runs/prof_$2"
PYTHONHASHSEED=0 TMPDIR=/dev/shm/v17/tmp python3 phases.py $1 $W --workers 4 --out runs/phases_$2.json $P > runs/phases_$2.out 2>&1
echo "exit $?" >> runs/phases_$2.out
