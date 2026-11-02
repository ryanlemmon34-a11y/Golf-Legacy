#!/bin/bash
# Negative tests for the study's validation and gates (experiment only). Each case states the exit code it must
# give and the failure it must name; the script exits 1 if any case does not behave as stated.
#   selftest.sh <checkout> <fixture> <scratch dir> <run dir to test report.py against (or "")>
set -u
CO=$1; FX=$2; T=$3; RUNDIR=${4:-}
HERE=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$T"
fails=0
expect() {   # name, wanted rc, pattern the output must contain, command...
  local name=$1 want=$2 pat=$3; shift 3
  out=$("$@" 2>&1); rc=$?
  if [ "$rc" = "$want" ] && grep -qE -- "$pat" <<<"$out"; then r=PASS; else r=FAIL; fails=$((fails+1)); fi
  printf '| %s | %s | %s | %s | %s |\n' "$name" "$want" "$rc" "$pat" "$r"
  printf '%s\n' "$out" > "$T/$(tr -c 'A-Za-z0-9' _ <<<"$name").log"
}
echo '| case | wanted exit | got | must name | result |'
echo '|---|---|---|---|---|'
V="python3 -I $HERE/validate.py $CO"
# tampered fixtures (copies; the original is never written)
python3 -I - "$FX" "$T" <<'PY'
import gzip, json, sys
fx = json.load(gzip.open(sys.argv[1], 'rt'))
a = json.loads(json.dumps(fx)); al = a['years']['2050']['allocated']['juniors']; al['USA'] -= 1; al['Canada'] += 1
json.dump(a, gzip.open(sys.argv[2] + '/fx_alloc.json.gz', 'wt'))
b = json.loads(json.dumps(fx)); b['years']['2050']['totals']['juniors'] += 1
json.dump(b, gzip.open(sys.argv[2] + '/fx_total.json.gz', 'wt'))
PY
expect 'N1 subset of years' 1 'F1 cohort boundary' $V "$FX" "$T/n1.json" "$T/n1.md" --stamp "$T/n1_stamp.json" --years 2041-2041
expect 'N2 wrong baseline (A1 as A0)' 1 "F2 every cohort passes a-e: .*\(2041, 'juniors'\)" $V "$FX" "$T/n2.json" "$T/n2.md" --stamp "$T/n2_stamp.json" --years 2041-2041 --negative-baseline A1
expect 'N3 tampered allocation (2050 juniors)' 1 "F5 .*found \[\[2050, 'juniors'\]" $V "$T/fx_alloc.json.gz" "$T/n3.json" "$T/n3.md" --stamp "$T/n3_stamp.json" --years 2050-2050
expect 'N4 tampered total (2050 juniors)' 1 "F2 every cohort passes a-e: .*\(2050, 'juniors'\)" $V "$T/fx_total.json.gz" "$T/n4.json" "$T/n4.md" --stamp "$T/n4_stamp.json" --years 2050-2050
expect 'N5 full years, wrong baseline' 1 'F4 tail counts' $V "$FX" "$T/n5.json" "$T/n5.md" --stamp "$T/n5_stamp.json" --negative-baseline A1
expect 'N6 headroom arm wider than declared (B2 knee 27.5 checked as 25.5)' 1 'F7 headroom arms change only what they declare: .*untouched candidate changed' $V "$FX" "$T/n6.json" "$T/n6.md" --stamp "$T/n6_stamp.json" --years 2041-2041 --negative-scope
expect 'T1 unit tests of the transform and arms' 0 '^OK' bash -c "cd '$HERE' && STUDY_CHECKOUT='$CO' python3 -m unittest test_headroom"
python3 -I -c "import json,sys; s=json.load(open(sys.argv[1])); print('N5 stamp passed', s['passed'], 'checks', s['checks'])" "$T/n5_stamp.json"
R="python3 -I $HERE/run.py $CO $FX $T/runs 1 --check-only"
expect 'R1 runner, no stamp' 2 'no validation stamp' $R --stamp "$T/missing.json"
expect 'R2 runner, failed stamp' 2 'validation did not pass' $R --stamp "$T/n1_stamp.json"
cp -r "$HERE" "$T/study_copy" && echo '# a later edit' >> "$T/study_copy/study.py"
expect 'R3 runner, stale stamp (study.py edited)' 2 'stale validation: study.py' python3 -I "$T/study_copy/run.py" "$CO" "$FX" "$T/runs" 1 --check-only --stamp "$HERE/results/validation_stamp.json"
expect 'R4 runner, current passing stamp' 0 'validation stamp ok' $R
if [ -n "$RUNDIR" ]; then
  expect 'R5 report, failed stamp' 2 'validation did not pass' python3 -I "$HERE/report.py" "$RUNDIR" "$T/r.md" "$T/r.json" --stamp "$T/n1_stamp.json"
  expect 'R6 report, current passing stamp' 0 'Headroom study: results' python3 -I "$HERE/report.py" "$RUNDIR" "$T/r.md" "$T/r.json"
fi
echo
echo "selftest: $fails case(s) not as stated"
exit $((fails > 0))
