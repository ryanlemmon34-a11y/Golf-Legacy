#!/bin/bash
# Bounded validation after the final gates, each alone (no other heavy job): full-population save/reopen
# determinism replay, then one same-seed familiarity-off season. Disk headroom checked before each new world
# (stop if free < 3.4 GB, above the harness's 3 GB guard); originals are never touched.
Q=/tmp/claude-0/-home-user-golf-legacy/dd633163-5093-57b8-a35e-3e668bc4257e/scratchpad/v18/queue
V=/tmp/claude-0/-home-user-golf-legacy/dd633163-5093-57b8-a35e-3e668bc4257e/scratchpad/v18
B=$V/arms/build_c0d1ea5
until grep -q "QUEUE13 DONE" $Q/summary.txt 2>/dev/null; do sleep 30; done
head=$(git -C $B rev-parse --short=7 HEAD); dirty=$(git -C $B status --porcelain | wc -l)
free() { df --output=avail -B1M /tmp | tail -1; }
echo "$(date -u +%H:%M:%S) QUEUE14 START on $head dirty=$dirty free $(free) MB" >> $Q/summary.txt
# the observer-check copy of the smoke world is disposable once navigation is done (its source, the smoke world, stays)
ui=$V/ui/final_$head/world
if [ -d $ui ] && [ -d $V/smoke/final_$head/world_on ] && grep -q "ui_nav $head" $Q/summary.txt; then
  rm -rf $ui; echo "$(date -u +%H:%M:%S) removed the navigation copy $ui (source kept); free $(free) MB" >> $Q/summary.txt
fi
if [ $(free) -lt 3400 ]; then echo "$(date -u +%H:%M:%S) QUEUE14 STOP: free disk $(free) MB < 3400" >> $Q/summary.txt; exit 1; fi
R=$V/det; mkdir -p $R
start=$(date +%s)
(cd $B && timeout 3600 python tools/long_world.py --session --seeds 4207 --years 2 --workers 2 --pathway-min-age 18 \
   --college-open-access on --keep-after 1 --out $R/det4207 > $R/det4207.log 2>&1); rc=$?
echo "$(date -u +%H:%M:%S) det_run $head exit $rc $(( $(date +%s) - start ))s $(grep -c 'done (' $R/det4207.log) seasons" >> $Q/summary.txt
if [ $rc -eq 0 ]; then
  start=$(date +%s)
  (cd $B && timeout 3600 python tools/determinism_replay.py --out $R/det4207 --seed 4207 --workers 2 > $R/replay.log 2>&1); rc=$?
  echo "$(date -u +%H:%M:%S) det_replay $head exit $rc $(( $(date +%s) - start ))s identical=$(grep -o '"identical": [a-z]*' $R/replay.log | head -1)" >> $Q/summary.txt
fi
if [ $(free) -lt 3400 ]; then echo "$(date -u +%H:%M:%S) QUEUE14 STOP before familiarity: free disk $(free) MB < 3400" >> $Q/summary.txt; exit 1; fi
start=$(date +%s)
(cd $V/fam && timeout 3600 python3 fam_off.py $B $V/fam/out_$head 4207 $V/smoke/final_$head/smoke.json > $V/fam/fam_$head.out 2>&1); rc=$?
echo "$(date -u +%H:%M:%S) fam_off $head exit $rc $(( $(date +%s) - start ))s $(tail -1 $V/fam/fam_$head.out | cut -c1-300)" >> $Q/summary.txt
echo "$(date -u +%H:%M:%S) QUEUE14 DONE free $(free) MB" >> $Q/summary.txt
