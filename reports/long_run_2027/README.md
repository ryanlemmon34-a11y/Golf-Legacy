# 50-season run, seed 2027

- `LONG_RUN.md` — the long-run diagnostic (`tools/long_run_report.py`): money, access, residence, high-potential
  leavers, generations, interesting careers, population and the season skip by season.
- `REPORT.md`, `DEBUG.md` — the standard long-world reports (`tools/long_world.py`).
- `LONG_RUN_original.md`, `REPORT_original.md` — the reports exactly as the run wrote them (kept; see
  *Corrections* below). `DEBUG.md` regenerated identically.
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

**Timings in the run are pessimistic** (before this pass's performance work; see `docs/BACKLOG.md` for the
after figures): the harness keeps 50 seasons of diagnostic rows in the same process,
which slows Python's garbage collection everywhere. A clean process, opened on a copy of the final world (season
51, 13,187 active golfers), skipped a season in **267.6 s**: simulate and reload 171.6 s, save 21.3 s, publish
5.3 s, the observer's overview 69.3 s (it builds the in-memory records: peak memory 9.1 GB).

## Corrections (reports regenerated from the saved data)

`LONG_RUN.md` and `REPORT.md` were regenerated from the run's saved data and archive (on a copy of the world;
the original was not opened) with corrected diagnostics. What changed:

| Claim in the original | Corrected | Why |
|---|---|---|
| 5 high-potential golfers "left before developing" (2 caddies, 2 coaches, 1 back to amateur) | 20 full-time episodes ended young and undeveloped and the golfer had not come back by 2076: part-time pro 7, back to amateur 5, became caddie 2, became coach 2, college to amateur 2, amateur took a job 2. A further 3 such episodes ended in a comeback; 6 of the 2,127 were never full-time in the archive; 1,654 episodes were completed (developed, or 27+); 655 episodes were still unfolding at the end (counted per episode: a golfer can have several) | The original counted only three kinds of exit and took a reason from any season; now each episode takes the decision recorded at its own last season, and comebacks, never-full-time, completed and unfolding careers are kept apart |
| Later arrivals: world No. 1 8, top 10 53 | By **weekly** ranking: later juniors 12 No. 1 / 65 top 10, later new professionals 0 / 0; starting-world professionals 8 / 43, starting-world amateurs 0 / 2 | The original used year-end rankings and lumped cohorts. Felix Moore and Brian Sullivan were weekly No. 1 (year-end best: 2) |
| Major wins: starting world 69, later 131 | Starting-world professionals 64, starting-world amateurs 5, later juniors 129, later new professionals 2 | Cohorts described accurately (initial amateurs apart) |
| Starting-world golfers "arrived 2027" | "starting world: professional / amateur" | Their careers began before the archive |
| Moved abroad for their career and later returned home: 59 | 50 | Now checked in order: the return must come after the move abroad |
| Late bloomer: Hunter Baker (born 1992, in the starting world) | Rupert Gillard (arrived 2028 at 18, first Premier season at 32) | Starting-world golfers are no longer eligible: their first archived Premier season is not their first |
| Career excerpts: the first 14 log lines (often all amateur wins) | Milestones: arrival, levels reached, first wins by level, majors, No. 1, career changes, comebacks, retirement, totals | |
| Annual net per season | Reported as recorded, **flagged**: this engine (7334ffe) archived the net before winter expenses, and support-funded moves were drawn in the next year's ledger | Not reconstructable exactly from the saved data (cash reconciled every year) |

Unchanged: reconciliation (0 failing seasons), debt, backing, access, mini-tour causes, residence move counts,
population and the run's timings.
