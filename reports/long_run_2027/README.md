# 50-season run, seed 2027

- `LONG_RUN.md` — the long-run diagnostic (`tools/long_run_report.py`): money, access, residence, high-potential
  leavers, generations, interesting careers, population and the season skip by season.
- `REPORT.md`, `DEBUG.md` — the standard long-world reports (`tools/long_world.py`).
- `manifest.json` — engine commit 7334ffe (clean tree), configuration, seed, hardware; `run.log` — per-season
  checks and timings as the run printed them.

Run: `python tools/long_world.py --seeds 2027 --years 50 --session --strict --out <dir>` on the development
container (Intel Xeon @ 2.10 GHz, 4 logical CPUs, 16 GB, Python 3.13), 3 h 14 min, every check passing in every
season.

**The world itself** (1 GB: session checkpoints, the archive with 50 season files and its index, the run's data and
debug files) is not in Git history. It was exported as `golf-legacy-world-2027-50y.tar.gz` (615 MB, sha256
`af1c16b9daea7063cb693b6d838ae1549f371dc0324f1ddf5ec3dbcfb2210b41`, delivered in two parts `.part-00` and `.part-01` with `EXPORT_README.md`). It contains the world,
`data/` (manifest, diagnostic and debug data, harness state, run log), the reports as generated, the engine as a
git bundle (tag `world-2027-50y-engine` = 7334ffe) and as a tarball, and `SHA256SUMS` for its 82 files.
Verified before delivery: the parts rejoin to that checksum; extracted, every inner checksum matched and the copy was
byte-identical to the run's directory; the archive read back (50 seasons, 49,378 people, index covering every
season); the session reopened from a clone of the bundle at generation 50, 1 January 2077 (13,187 active, 42,947
people). Durable hosting on GitHub was not possible from the session: creating releases is not permitted for this
session type, and Git LFS (`lfs.github.com`) is denied by the environment's network policy. **Keep the delivered
files**; the run's original directory stays in the temporary container, unchanged.

**Timings in the run are pessimistic:** the harness keeps 50 seasons of diagnostic rows in the same process,
which slows Python's garbage collection everywhere. A clean process, opened on a copy of the final world (season
51, 13,187 active golfers), skipped a season in **267.6 s**: simulate and reload 171.6 s, save 21.3 s, publish
5.3 s, the observer's overview 69.3 s (it builds the in-memory records: peak memory 9.1 GB).
