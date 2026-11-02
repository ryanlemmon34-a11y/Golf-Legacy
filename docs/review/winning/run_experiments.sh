#!/usr/bin/env bash
# Every controlled experiment of the study, with its exact configuration. Research only: no engine code changes.
# Usage: run_experiments.sh SAVE CAPDIR EXPDIR [step...]   (steps: rounds weather fixed validate archetypes sd)
# CAPDIR must hold a replay.py capture whose MANIFEST.json marks the 2027 season verified; every experiment
# re-checks the manifest, the task hashes and the no-op equality before measuring anything.
set -euo pipefail
SAVE=$1; CAP=$2; EXP=$3; shift 3
STEPS=${*:-rounds weather fixed validate archetypes sd}
HERE=$(cd "$(dirname "$0")" && pwd)
cd "$HERE"
EV3=2027_BRITANNIA_OPEN,2027_PT_FRANCE_OPEN,2027_CH_EUROPE_01
ARCH='arch:Uniform'
for a in 'All-Rounder' 'Power Hitter' 'Precision Ball-Striker' 'Short-Game Artist' 'Strategic Technician' \
         'Aggressive Shotmaker' 'Effortless Power' 'Elite Putter'; do
  ARCH="$ARCH,arch:$a,arch:$a:neutral"
done
for step in $STEPS; do case $step in
  rounds)      # tier 1: +5 / -5 on all 21 attributes; ranks 1, 10, 40; three events; 8,000 paired samples per arm
    python3 exp_attrs.py rounds "$CAP" "$SAVE" "$EXP" --events $EV3 --ranks 1,10,40 --n 8000 --chunk 2000 \
      --deltas 5,-5 --procs 4 --tag rounds_grid ;;
  weather)     # matched weather arms: 12 direction/gust scenarios x 30 paired shot seeds; four events
    python3 exp_weather.py "$CAP" "$SAVE" "$EXP" --events 2027_BRITANNIA_OPEN,2027_PT_SCOTLAND_OPEN,2027_PT_FRANCE_OPEN,2027_CH_EUROPE_01 \
      --scen 12 --reps 30 --chunk 10 --procs 4 ;;
  fixed)       # tier 2 (conditional approximation): 500 production field replicates x 16 subject replays
    for e in 2027_BRITANNIA_OPEN 2027_PT_FRANCE_OPEN; do
      python3 exp_fixed.py "$CAP" "$SAVE" "$EXP" --event $e --ranks 1,10 --reps 500 --k 16 --deltas 5,-5 --procs 4
      python3 exp_fixed.py "$CAP" "$SAVE" "$EXP" --event $e --ranks 10 --reps 500 --k 16 --arms "base,$ARCH" \
        --procs 4 --tag fixed_arch_${e}
    done ;;
  validate)    # tier 3 (full production events, paired seeds) for the fixed-field validation
    python3 exp_attrs.py events "$CAP" "$SAVE" "$EXP" --events 2027_BRITANNIA_OPEN --ranks 1 --n 1500 --chunk 100 \
      --arms base,short_putting+5,power+5,driving_accuracy+5,putting_consistency+5 --procs 4 --tag events_validation_br1
    python3 exp_attrs.py events "$CAP" "$SAVE" "$EXP" --events 2027_BRITANNIA_OPEN --ranks 10 --n 1500 --chunk 100 \
      --arms 'base,short_putting+5,power+5,arch:Aggressive Shotmaker,arch:Strategic Technician' --procs 4 \
      --tag events_validation_br10 ;;
  archetypes)  # tier 1 for the fixed-Overall archetype profiles (ranks 10 and 40: no clipping)
    python3 exp_attrs.py rounds "$CAP" "$SAVE" "$EXP" --events $EV3 --ranks 10,40 --n 8000 --chunk 2000 \
      --arms "base,$ARCH" --procs 4 --tag rounds_arch ;;
  sd)          # equal-SD perturbations (Premier/major golfer-season SDs, results/attr_sd_premier.json), rank 10
    ARMS=base,$(python3 -c "import json;d=json.load(open('results/attr_sd_premier.json'))['sd'];print(','.join(f'{k}+{v}' for k,v in d.items()))")
    python3 exp_attrs.py rounds "$CAP" "$SAVE" "$EXP" --events $EV3 --ranks 10 --n 8000 --chunk 2000 \
      --arms "$ARMS" --procs 4 --tag rounds_sd ;;
  *) echo "unknown step $step"; exit 2 ;;
esac; done
