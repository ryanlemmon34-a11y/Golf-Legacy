#!/bin/bash
# Exact-head final gates on the candidate c0d1ea5, each alone, after the comparison arms:
# full suite, full-population smoke (2 seasons evidence on + 1 off, same seed), wide-screen navigation.
Q=/tmp/claude-0/-home-user-golf-legacy/dd633163-5093-57b8-a35e-3e668bc4257e/scratchpad/v18/queue
V=/tmp/claude-0/-home-user-golf-legacy/dd633163-5093-57b8-a35e-3e668bc4257e/scratchpad/v18
until grep -q "ARMS DONE" $Q/summary.txt 2>/dev/null; do sleep 30; done
wt=$Q/wt_final2; head=$(git -C $wt rev-parse --short=7 HEAD)
echo "$(date -u +%H:%M:%S) QUEUE13 START (exact-head final gates on $head)" >> $Q/summary.txt
start=$(date +%s)
(cd $wt && timeout 14400 nice -n 19 python -m unittest discover -s tests > $Q/final2_suite.log 2>&1); rc=$?
echo "$(date -u +%H:%M:%S) final_suite $head exit $rc $(( $(date +%s) - start ))s $(grep -E '^Ran|^OK|^FAILED' $Q/final2_suite.log | tr '\n' ' ')" >> $Q/summary.txt
start=$(date +%s)
(cd $V/smoke && timeout 7200 python3 full_pop_smoke.py $wt $V/smoke/final_$head 4207 2 > $V/smoke/final_$head.out 2>&1); rc=$?
echo "$(date -u +%H:%M:%S) smoke $head exit $rc $(( $(date +%s) - start ))s $(tail -1 $V/smoke/final_$head.out)" >> $Q/summary.txt
out=$V/ui/final_$head; mkdir -p $out; cp -r $V/smoke/final_$head/world_on $out/world
(cd $wt && nice -n 19 python3 tools/observer.py $out/world --port 8793 > $out/server.log 2>&1 &)
for i in $(seq 1 60); do curl -s -o /dev/null --max-time 2 http://localhost:8793/ && break; sleep 2; done
(cd $V/ui && BASE=http://localhost:8793 OUT=$out LIMIT=70 timeout 3600 nice -n 19 node nav_check.js > $out/nav.out 2>&1); rc=$?
pkill -f "tools/observer.py $out/world"
echo "$(date -u +%H:%M:%S) ui_nav $head exit $rc $(head -1 $out/nav.out)" >> $Q/summary.txt
echo "$(date -u +%H:%M:%S) QUEUE13 DONE" >> $Q/summary.txt
