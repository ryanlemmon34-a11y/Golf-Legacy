# v17 simulation performance: outcome-identical shortcuts measured on Test2 (season 2084)

**Outcome.** Four exact-result shortcuts were tried. All four together leave the season exactly as before (saved state and history byte for byte, reopened world part by part), but the season is not measurably faster: the before/after difference is smaller than this machine's run-to-run variation. Following the review judgement (identical outcomes alone are no reason to keep extra caching), **one change is kept** -- a one-line reduction with no new state -- and three are measured and not kept. No speedup is claimed.

**Scope.** Exact-result work only; intentional behaviour changes (nations, injury, early-pro) are in other branches. The 120 s target is the owner's hardware (16 logical CPUs); this is a shared 4-CPU VM, so the figures are relative.

## Method

- Before: afa5e4a. After (the measured candidate): build/v17-sim-perf 5b6909e (all four shortcuts). Same engine otherwise.
- World: the Test2 release save (seed 386509, 57 seasons, cursor 2084 week 1), copied from the read-only extracted release into an indexed master (its first open builds the 1.3 GB archive index: 281.8 s here, then 19.2 s); each run starts from a fresh copy of the master. The user's save is never written and is not marked compatible; the after-build opens its copy with allow_other_engine (test copies only).
- Storage: disposable copies in RAM-backed /dev/shm (16 GB tmpfs; 15.5 GB RAM available at the start), never the session disk; logs, timings, profiles and digests on disk (`runs/`).
- One full season through Session.advance (52 weeks, year end, one commit), PYTHONHASHSEED=0, 4 workers, `phases.py` (wall-clock per phase, no profiler in timed runs). Two pairs in opposite orders, each run alone on the machine.
- Equivalence, after each pair: `eqcheck.py` (decompressed state pickle byte for byte; every published history file decoded) and, for the first pair, `reopen2.py` (each world reopened by its own build: the state parts of tools/equivalence_check.parts and the published history digested one season at a time -- the harness's own parts() decodes all 58 seasons at once and was killed for memory, rc 137, so it was replaced).

## Equivalence

- Pair 1: state pickle IDENTICAL (342,617,291 bytes decompressed); 63 history files EQUIVALENT (eqcheck rc 0).
- Pair 2: EQUIVALENT again (eqcheck rc 0).
- Reopen digests (pair 1, `runs/reopen2_base.json` and `runs/reopen2_cand.json`): IDENTICAL, 16 parts (cursor, decision_evidence, development, diagnostics, familiarity, fatigue_injuries, finances, history, moments, performance, published_years, rankings, records, results, rounds_and_holes, staff).

## Season timings (seconds)

| run | order in pair | advance | worker busy | plan_block | regular_entries | develop_week | record_event | special_field | _commit | end_of_season |
|---|---|---|---|---|---|---|---|---|---|---|
| afa5e4a (base) | 1st | 209.28 | 268.6 | 22.87 | 21.54 | 11.13 | 10.76 | 4.31 | 29.88 | 4.16 |
| candidate (cand) | 2nd | 219.85 | 270.7 | 21.83 | 23.29 | 11.37 | 11.92 | 5.02 | 28.53 | 7.07 |
| candidate (cand2) | 1st | 204.18 | 268.3 | 21.79 | 22.38 | 11.34 | 10.82 | 4.28 | 24.21 | 4.29 |
| afa5e4a (base2) | 2nd | 215.28 | 267.4 | 22.66 | 21.79 | 11.37 | 10.83 | 4.19 | 28.88 | 6.62 |

Means: afa5e4a 212.3 s, candidate 212.0 s (difference -0.3 s, -0.1%). Spread between repeats of one build: 6.0 s and 15.7 s; in both pairs the first run was about 11 s faster than the second (an order effect, cancelled by the reversed pair). Single phases vary by several seconds between runs of the same code (save 24.2-29.9 s; year end 4.2-7.1 s).

## Per change (cost and benefit)

Call counts from four instrumented weeks of Test2 2084 (`perchange.py`, afa5e4a code; 30.7 s); per-call times measured old against new on the same world's inputs; season estimates scale the per-call saving by the season's calls (from the profiled season where available).

| change | calls (4 weeks) | per call, old -> new | estimated saving a season | added state | decision |
|---|---|---|---|---|---|
| `_seed` remembers BLAKE2 hashes (LRU 65,536) | 67,277 (65,500 distinct: hit rate 2.6%) | 734.1 ns -> 158.2 ns on a hit only | about none (hits are rare; misses pay the cache) | 7.9 MB when full | not kept |
| prize forecast kept per golfer-week and tier | 62,052 forecasts, 31,390 distinct | 1001.4 ns per forecast avoided | about 0.4 s | a dict per golfer-week | not kept |
| `overall_rating` weight total summed once | 151,812 | 2188.9 ns -> 1886.6 ns | about 0.6 s | a module constant | not kept (below the noise; adds state) |
| `eligible` reads TOUR_COUNTRIES | 144,422 (about 3.4 million a season in the profile) | 570.1 ns -> 138.5 ns (the set itself) | about 1.5 s | none (the frozensets already exist) | **kept** |

## What is kept

build/v17-sim-perf now changes one line of golfsim/season.py: Season.eligible takes each tour's countries from TOUR_COUNTRIES (the frozensets the module already builds once per tour) instead of building the set on every call. Exact by construction (the same membership test on the same countries) and checked against a copy of the replaced function for every golfer and every regular event of a small world, in two weeks each (tests/test_perf_v17.py); it is also a subset of the measured candidate, whose season was byte-identical. Its estimated saving (about 1.5 s of a roughly 210 s season here, 0.7%) is below what a season A/B can resolve on this machine, so it is kept as a simple reduction, not as a demonstrated speedup.

## Remaining time and what would move it

The main process's serial work dominates what is left (planning 22 s, entries 22 s, saving 24-30 s, development 11 s, recording 11 s on this machine; tournaments run on the workers in parallel). Exact-result shortcuts give little more, as in the previous round. Larger gains need an owner decision (unchanged from docs/PERFORMANCE_REVIEW.md): per-golfer random streams so planning and entries can run in parallel (a new engine for new worlds), incremental checkpoints, or declaring outcome-equivalent engines compatible.

Also found: the Test2 release save has no archive index, so its first open rebuilds it (281.8 s here, 1.3 GB); later opens take 19.2 s.
