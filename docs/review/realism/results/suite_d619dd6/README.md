# Full suite on d619dd6 (frozen checkout)

Run with `docs/review/realism`'s runner: one module at a time, `nice -n 19`, `python3 -m unittest tests.<module>`,
2026-11-02 05:56–07:3x UTC.

**Result: 90 modules. On each module's final successful run: 1,148 tests run, 4 skipped (1,144 non-skipped), 0
failures.** `SUMMARY.txt` has one line per module run.

(An earlier total, 1,145, missed the three single-test modules, "Ran 1 test": `test_active_golfers`,
`test_benchmark_tool`, `test_perf_v17`.)

**First run of `test_long_run_safeguards`: 2 errors.**
- Both were in `test_a_good_season_passes` and `test_population_change_is_a_flag`, as
  `long_world.Stop: season 2030: 2.3 GB free (floor 3 GB)`.
- The harness's free-disk safeguard checks the folder its test writes to. That folder was the system temporary
  folder on the main disk, which had 2.3 GB free.
- From that point, the remaining modules and the re-run used `TMPDIR=/dev/shm/real/tmp` (RAM).
- The re-run passed 18 of 18. Its log replaced the first run's in `logs/`; the two `SUMMARY.txt` lines keep both
  results.

The four skips are in `SKIPS.md`, with their messages as the tests print them (from a verbose re-run of those four
modules).
