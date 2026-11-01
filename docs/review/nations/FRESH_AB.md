# Nations: fresh-world A/B on one engine (rules on vs only the nation flags off)

Bounded check of the two approved nation changes (carry-forward, rules 2026-11-13; visible achievement, 2026-11-14) in re-simulated worlds. **Attribution:** both arms run the same integrated build (build/v17-integration 4018797c: injury, nations, early-pro and the observer work), the same seed and the same everything else; the "off" arm only sets `participation.carry_on = achievement_on = False` right after the world is created, before any cohort is allocated (`run.py` asserts nothing was allocated yet). So the arms differ in the nation rules alone -- not in early-pro or injury, which both arms have. Once the first allocation differs, the worlds re-simulate differently, so differences also include ordinary run-to-run variation; two seeds and four winters are a bounded check, not a calibration. A whole-integration comparison against afa5e4a is a separate smoke check.

Full-population worlds, 4 workers, seeds 11 and 23, four winters each (entrant years 2028-2031); worlds in RAM-backed /dev/shm (not kept), results here. **Scope:** `run.py` reads the running session's in-memory participation history; it does not reopen the saved state or read the archive back, and it does not count generated golfers. Those checks are done separately (FRESH_READBACK.md). `all.sh` runs `run.py`; per-season measures in `on_*.json` / `off_*.json`.

| seed | arm | entrant year | totals exact | carry min / max (sum) | prestige min-max | multipliers | at cap / floor | USA share | top-5 share | nations below 45 | achievement min-max | nations never given a newcomer (of 57 with a share) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 11 | on | 2028 | yes | -0.516 / 0.486 (-1e-06) | 42.7-61.3 | 0.909-1.100 | 0 / 0 | 33.40% | 58.96% | 7 | 0.772-1.329 | 16 of 57 |
| 11 | on | 2029 | yes | -0.535 / 0.458 (+3e-06) | 40.5-57.6 | 0.826-1.210 | 0 / 0 | 34.23% | 59.56% | 9 | 0.736-1.306 | 10 of 57 |
| 11 | on | 2030 | yes | -0.538 / 0.527 (+3e-06) | 38.0-61.6 | 0.751-1.286 | 0 / 0 | 35.03% | 59.70% | 10 | 0.706-1.457 | 7 of 57 |
| 11 | on | 2031 | yes | -0.499 / 0.520 (+4e-06) | 38.8-60.8 | 0.733-1.348 | 0 / 0 | 35.09% | 59.85% | 12 | 0.689-1.424 | 3 of 57 |
| 11 | off | 2028 | yes | – | 43.6-63.5 | 0.909-1.100 | 0 / 0 | 33.31% | 58.48% | 2 | – | 16 of 57 |
| 11 | off | 2029 | yes | – | 40.6-58.1 | 0.826-1.210 | 0 / 0 | 34.63% | 59.00% | 3 | – | 16 of 57 |
| 11 | off | 2030 | yes | – | 40.7-59.3 | 0.772-1.294 | 0 / 0 | 34.27% | 58.71% | 2 | – | 16 of 57 |
| 11 | off | 2031 | yes | – | 40.0-60.2 | 0.757-1.326 | 0 / 0 | 34.47% | 59.20% | 3 | – | 15 of 57 |
| 23 | on | 2028 | yes | -0.558 / 0.456 (-3e-06) | 38.8-59.6 | 0.909-1.100 | 0 / 0 | 32.63% | 58.84% | 7 | 0.685-1.373 | 16 of 57 |
| 23 | on | 2029 | yes | -0.538 / 0.486 (+4e-06) | 38.9-60.6 | 0.826-1.210 | 0 / 0 | 33.54% | 59.29% | 7 | 0.685-1.403 | 12 of 57 |
| 23 | on | 2030 | yes | -0.511 / 0.556 (+3e-06) | 40.9-57.6 | 0.778-1.233 | 0 / 0 | 33.59% | 59.12% | 7 | 0.736-1.287 | 10 of 57 |
| 23 | on | 2031 | yes | -0.451 / 0.546 (+1e-06) | 40.4-58.2 | 0.766-1.254 | 0 / 0 | 33.89% | 59.16% | 9 | 0.736-1.318 | 4 of 57 |
| 23 | off | 2028 | yes | – | 42.2-60.3 | 0.909-1.100 | 0 / 0 | 32.37% | 58.86% | 5 | – | 16 of 57 |
| 23 | off | 2029 | yes | – | 40.3-58.6 | 0.826-1.210 | 0 / 0 | 32.70% | 58.96% | 7 | – | 16 of 57 |
| 23 | off | 2030 | yes | – | 39.9-56.9 | 0.755-1.209 | 0 / 0 | 33.31% | 58.90% | 3 | – | 14 of 57 |
| 23 | off | 2031 | yes | – | 39.4-57.4 | 0.745-1.196 | 0 / 0 | 33.48% | 58.97% | 3 | – | 14 of 57 |

**Reading.**
- Totals: every season of both arms allocates exactly the fixed cohort totals.
- Carry-forward: carries stay within about ±0.56 (the ledger allows (−1, 2)); their sum stays within a few millionths of zero (the recorded carries are rounded). Nations with a share that had never received a newcomer fall from 16 to 3 (seed 11) and 16 to 4 (seed 23) in four winters with the rules on; with them off, 16 to 15 and 16 to 14.
- Visible achievement: more nations end below 45 with the rules on (2031: 12 and 9 on, 3 and 3 off, seeds 11 / 23). That count alone does not show a wider overall spread: the 2031 min-max ranges are close (seed 11: 38.8-60.8 on, 40.0-60.2 off; seed 23: 40.4-58.2 on, 39.4-57.4 off). (The 8 against 3 below 45 quoted elsewhere is the Test2 fixed-input replay in 2084, a different measurement.) No nation reached the multiplier cap or floor; multipliers stay within 0.73-1.35.
- Concentration: USA share in 2031 is 35.08% / 33.89% on against 34.47% / 33.48% off (seed 11 / 23); top-5 share 59.85% / 59.16% on against 59.19% / 58.97% off.
- No new design change is proposed here (owner instruction: no new balance changes; the small-breakthrough limitation stays as reviewed).
