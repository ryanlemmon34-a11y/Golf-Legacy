# 50-season run, seed 2027

- `LONG_RUN.md` — the long-run diagnostic (`tools/long_run_report.py`): money, access, residence, high-potential
  leavers, generations, interesting careers, population and the season skip by season.
- `REPORT.md`, `DEBUG.md` — the standard long-world reports (`tools/long_world.py`).
- `manifest.json` — engine commit 7334ffe (clean tree), configuration, seed, hardware; `run.log` — per-season
  checks and timings as the run printed them.

Run: `python tools/long_world.py --seeds 2027 --years 50 --session --strict --out <dir>` on the development
container (Intel Xeon @ 2.10 GHz, 4 logical CPUs, 16 GB, Python 3.13), 3 h 14 min, every check passing in every
season.

**The world itself** (session checkpoints, the archive with 50 season files and its index, the run's data and
debug files; 1 GB) is not in the repository: it is in the session container at
`/tmp/claude-0/-home-user-golf-legacy/dd633163-5093-57b8-a35e-3e668bc4257e/scratchpad/long_run_2027/`
(`world_2027/` opens with `python tools/observer.py <that dir>/world_2027`). The container is temporary.

**Timings in the run are pessimistic:** the harness keeps 50 seasons of diagnostic rows in the same process,
which slows Python's garbage collection everywhere. A clean process, opened on a copy of the final world (season
51, 13,187 active golfers), skipped a season in **267.6 s**: simulate and reload 171.6 s, save 21.3 s, publish
5.3 s, the observer's overview 69.3 s (it builds the in-memory records: peak memory 9.1 GB).
