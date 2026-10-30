# Performance review: skip to the end of a season, and history browsing

Owner's brief (30 October 2026): "Skip to end of season" within two minutes in season 1 and season 100, history
browsing responsive as the world grows; measured, never by reducing the simulation. This work is on the branch
`perf/season-speed`, from the playtest build **7d8e6ed** (baseline). It is not merged: the playtest stays on one
build until the owner approves.

## Method

- **Machine** (all numbers here): Intel Xeon @ 2.10 GHz, 4 logical CPUs, 15.7 GB, Linux, Python 3.13.17; 4
  workers. Not the owner's laptop (16 logical CPUs; it ran season 1 in 47.9 s on an earlier build). Nothing was
  run on the playtest computer.
- **Worlds**: a fresh full-population world (seed 2027, 6,449 active golfers), and a disposable copy of the
  50-season world (seed 2027, made by engine 7334ffe; cursor 2077 week 1; 13,187 active golfers, 42,947 people;
  opened with "continue with this engine" on the copy). Season 51 is the oldest season a saved checkpoint allows.
  **There is no season-25 or season-100 checkpoint in a supported format** (the 25-season worlds are an older
  save format), so those seasons were not measured, and no long run was started to make one.
- **Timing**: `tools/benchmark_skip.py` (the end-to-end skip as the observer does it: simulate, save, publish,
  reload, overview), and a phase timer (wall-clock time of each part of the season in the main process, the
  workers' busy time, no profiler). Profiles (cProfile per phase, line profiles) only to find the work, never
  for the numbers. Runs alternated baseline / branch; the machine is a shared virtual machine and single phases
  vary by 10-15 % between identical runs.
- **Equivalence**: every change is checked by playing the same season from the same save with the baseline and
  with the branch (fixed hash seed, as Python randomises string hashing per process: the order a set of names is
  pickled in otherwise differs from run to run, with the same contents) and comparing the **saved simulation
  state byte for byte** (decompressed) and **every published history file** (decoded JSON). Differences of
  compression or gzip framing are reported apart; there are no others.

## Where the time goes (baseline, measured)

| Part of a skip (s) | season 1 | season 51 |
|---|---|---|
| whole advance (simulate + save) | 108.7 | 188.5 |
| tournaments on the workers (4 workers, 91-93 % busy) | ~55 | ~61 |
| main process: entries, planning, results, development, finances, rankings | ~46 | ~105 |
| year end (start, end, archive staging) | ~3.5 | ~9.6 |
| save and publish | 7.7 | 25.1 |

The shots are already simulated in parallel and the workers are kept busy; what grows with the world is the
main process's one-at-a-time work, which does not use more cores. On a 16-thread computer the parallel part
shrinks; the serial part is what decides season 100.

## Changes (each measured, each equivalent)

| Commit | Change | Measured on season 51 (baseline -> branch) |
|---|---|---|
| b0dd335 | Saves and history files compressed on threads (same bytes when read) | checkpoint pickle+compress 9.9 -> 6.5 s; 16 MB history file 1.42 -> 0.43 s |
| e6d84d6 | Per-hole course records in one loop; record and relationship exports without `asdict` | recording results 11.2 -> 9.6-10.3 s |
| 94745b0 | Rankings in one pass; fame summed only when it changes; prize forecasts remembered until they change | rankings 5.3 -> 4.3 s; fame 3.3 -> 2.1 s |
| d84a0d7 | Planner: shared-prefix search of week combinations; self-view rows; priorities once per week's entries | planning 23.8 -> 20.0-21.6 s |
| c7b0d7c | Development: coaching and experience only for training weeks; no unused gain | development 11.8 -> 9.1-10.4 s |
| (see log) | Stats: all-time sums kept in the store; each view queries only its columns | Stats 4.9 -> 0.4 s; Prize money 5.4 -> 1.1 s; golf statistics 4.6 -> 0.9 s |
| (see log) | Records: statistics cached beside the world; record lists remembered; scope filtered per edition | first Records page 9.5-15 s -> 0.2 s (cache); all 31 lists 75 -> 52 s first time, then instant |

## Results

Measured, end to end (`tools/benchmark_skip.py`: one season skipped as the observer does it, on a disposable copy;
two runs each, alternating baseline 7d8e6ed and branch; 4 workers):

| Skip one season | Baseline (s) | Branch (s) | Change |
|---|---|---|---|
| Season 1 (fresh world, 6,971 active golfers) | 116.3 / 113.3 | 112.2 / 111.9 | -3 % |
| Season 51 (50-season copy, 13,152 active, 43,683 people) | 214.2 / 213.0 | 202.6 / 204.4 | -5 % |
| of which: season-end save, season 51 | 20.5 / 19.8 | 15.7 / 15.0 | -24 % |
| of which: simulate, season 51 | 179.0 / 178.3 | 170.5 / 173.8 | -3 % |

| Peak memory (exact peak RSS) | Baseline | Branch |
|---|---|---|
| Season 1, main process | 730 MB | 770 MB |
| Season 51, main process | 2,578 MB | 2,640 MB (+2 %: remembered forecasts and the compression threads' buffers) |
| Season 51, all processes (PSS) | 4,135 MB | 4,256 MB |

History browsing (season 51 copy): Stats 4.9 s -> 0.4 s, Prize money 5.4 s -> 1.1 s, golf statistics 4.6 s -> 0.9 s;
Records: the first page after the statistics are cached 9.5-15 s -> 0.2 s (the very first opening of a copied
world still builds the cache once: 14 s above).

**Against the two-minute goal.** On this 4-CPU machine season 1 takes about 112 s and season 51 about 203 s. The
owner's laptop log (16 logical CPUs, playtest build) shows a skip growing by about 2 s a season, from 53 s in
season 1 to about 105 s by season 24; continued in a straight line that reaches about 250 s by season 100. The
exact-result changes here remove about 5 % at season 51 (mostly the save) and do not change that trend: the
growing part is the main process's one-at-a-time work, which grows with the number of people the world holds.
Reaching two minutes at season 100 needs one of the decisions below; nothing here reduced the simulation.

## Correctness evidence

- Season 1 (fresh world) and season 51 (50-season copy): **identical saved state** (53 MB and 244 MB
  decompressed) and **identical history** (6 and 56 files) to the baseline after the same season.
- Season 1 with 2 workers against the baseline with 4: one byte differs -- the saved worker count itself;
  everything simulated is identical. (Final runs: season 1 and season 51 state identical, 52,966,950 and
  243,781,198 bytes; history files differ only in gzip encoding.)
- The planner's new search against the old per-mask loop: identical choice and value on 230,000 random plans.
- Exports equal `dataclasses.asdict`; threaded gzip reads back byte for byte (pickle and JSON); rankings, fame
  and forecasts equal a full recomputation week by week; the store's all-time sums equal the seasons summed
  (all 42,947 people at season 51) and are not used once any season changes; the records cache and remembered
  lists equal a fresh reading (all 28 lists and scoped ones at season 51) and are not trusted for a
  republished season or another world's files.
- `tests/test_performance_equivalence.py` (7 tests) and the whole suite on the branch: 30 of 31 modules passed;
  `test_realism` failed one test because its helper writes a golfer's prize record directly, bypassing
  `learn_prize` (which clears that golfer's remembered forecasts), for two copies of the same golfer. The engine
  changes the record only through `learn_prize`; the helper now clears the memo too (fixed on the branch).

## Memory and disk

- Checkpoints: the same pickle, compressed in 4 MB members (about 0.05 % larger at season 51: 79.40 vs 79.37 MB).
- New derived files, rebuilt whenever they do not match the history: `observer_cache/history_stats.pkl`
  (61 MB at season 51, grows with the number of starts) and the statistics store's all-time tables (a few MB).
- Peak memory: up about 2 % at season 51 (table above).

## Compatibility

- The branch changes simulation code (outcomes identical), so its engine fingerprint differs from the
  playtest build's: a playtest world opens on the branch as "another engine" (browse read-only, or Copy and
  continue with this engine). Because the outcomes are identical, a copy continued on the branch plays exactly
  the seasons the playtest build would.
- Saves written by the branch are ordinary gzip (several members): the playtest build can read them.
- The statistics store (schema 4) is rebuilt once in the background on first opening (about 2 minutes for 51
  seasons here); the records cache is written on first use.
- No new dependency, service or cost; Windows launch unchanged (threads only).

## What remains, and what would need the owner's decision

The remaining time is spread over many parts of the main process, each now a few seconds (planning, entries,
development, recording, finances, rankings, year end, save). Exact-result shortcuts give little more. Larger
gains need one of these, each a decision for the owner:

1. **Give each golfer's monthly planning and entry choices their own random stream** (seeded per golfer and
   week) so they can be worked out on the worker processes in parallel. Deterministic and the same quality,
   but it changes which random numbers each golfer draws, so results differ from the current build from that
   point on: a new engine for new worlds, not for the running playtest.
2. **Save only what changed** between checkpoints (an incremental checkpoint format): the season-end save at
   season 51 is about 16 s here and grows with the people the world holds.
3. **Declare outcome-equivalent engines**: let a world made by a build known to give identical outcomes (as
   proved here) continue without the "another engine" copy step. A guard relaxation: owner's approval first.

Season 100 is untested: no checkpoint exists, and the population of the 50-season world doubled from season 1
(13,187 active golfers against 6,449), which is what the serial work grows with.
