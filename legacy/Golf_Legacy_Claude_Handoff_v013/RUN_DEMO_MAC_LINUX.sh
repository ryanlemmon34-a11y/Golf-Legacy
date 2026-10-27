#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p demo_output
cd source
python3 -m unittest discover -s tests -v
python3 engine_v013.py --seed 1217 --population 450 --years 1 --events-scale 0.08 --stop-week 52 --db ../demo_output/demo.sqlite --out ../demo_output/reports --quiet
python3 audit_v013.py ../demo_output/demo.sqlite --output ../demo_output/audit.json
