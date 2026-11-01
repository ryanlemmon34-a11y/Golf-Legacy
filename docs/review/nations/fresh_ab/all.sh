#!/bin/sh
# nation A/B on one build (the integration): 'on' = nation rules as built, 'off' = the same build with only the nation
# flags off; two seeds, 4 seasons each; worlds in /dev/shm (deleted after); results and logs here (disk)
H=/tmp/claude-0/-home-user-golf-legacy/dd633163-5093-57b8-a35e-3e668bc4257e/scratchpad/v19/nation_multiseed
CODE=${1:-/dev/shm/v17/wt_int}
for seed in 11 23; do
  for arm in on off; do
    W=/dev/shm/v17/nat_${arm}_$seed; rm -rf $W
    TMPDIR=/dev/shm/v17/tmp timeout 5400 python3 $H/run.py $CODE $W $seed 4 $H/${arm}_$seed.json $arm > $H/${arm}_$seed.log 2>&1
    echo "$arm $seed rc=$?"
    rm -rf $W
  done
done
