# v17 simulation performance: outcome-identical shortcuts (Test2, season 2084) -- UNVERIFIED DRAFT

**Status: unverified.** Published for source review while the Test2 before/after timings and the state, history and
reopen equivalence runs are pending. Nothing here is measured yet.

**Scope.** Exact-result performance work only: every change gives exactly what the code it replaced gave (no
probability, draw, order or recorded fact changes). Intentional behaviour changes (nations, injury, early-pro) are in
other branches and are not measured here. The 120 s season target is the owner's hardware (16 logical CPUs); this
machine is a shared 4-CPU virtual machine, so its figures are relative evidence, not the target.

**Method.**
- Build before: afa5e4a. Build after: build/v17-sim-perf (afa5e4a + the shortcuts below). Same engine otherwise.
- World: the Test2 release save (seed 386509, 57 seasons, cursor 2084 week 1), copied read-only from the extracted
  release into an indexed master (its first open builds the 1.3 GB archive index: 281.8 s here, then 19 s), and each
  run starts from a fresh copy of that master. The user's save is never opened for writing and is not marked
  compatible: the after-build opens its copy with allow_other_engine (a test copy only).
- Storage: the disposable copies are in RAM-backed /dev/shm (16 GB tmpfs, 15 GB RAM available at the start), not the
  session disk (kept above its 3 GB floor); every log, timing, profile and digest is written to the scratchpad on disk.
- One full season (52 weeks and the year end, one commit), PYTHONHASHSEED=0, 4 workers, through Session.advance as the
  observer's skip does (perf/phases.py: wall-clock per phase; no profiler in the timed runs). Before and after run
  alone on the machine, one after the other.
- Equivalence: (1) the saved simulation state (decompressed pickle) byte for byte and every published history file
  (decoded) -- perf/eqcheck.py; (2) each advanced world reopened by its own build and digested part by part
  (tools/equivalence_check.parts: results, performance, rounds and holes, development, familiarity, finances, staff,
  fatigue and injuries, rankings, records, moments, history log, cursor, published history and its evidence).

**Changes** (golfsim/season.py, golfsim/golfer.py; tests/test_perf_v17.py checks each against the code it replaced):
1. Season.eligible reads each tour's countries from TOUR_COUNTRIES (already built once per tour) instead of building
   the set on every call (1-2 million calls a season).
2. _seed remembers its BLAKE2 hashes (bounded LRU of 65,536 keys): drive and entry-ticket seeds recur every week.
3. Weekly entries keep each golfer's prize forecast per tier for the week (expected_prize's own arithmetic).
4. overall_rating's default weight total is summed once (the same float).

**Results.** (to be filled from runs/)
