# Full suite on the engine fix (fix/engine-dogleg-retee)

The suite ran in the fix branch's worktree. Its code is engine `e99cb20`; the branch head `46013a5` adds only a
fixture-note correction. Each module ran on its own, at low priority, with `TMPDIR` in RAM. It finished at about
10:05 UTC on 2026-11-02.

**Result:** 90 modules (main's 89 plus `tests/test_tee_plan.py`): 1,147 tests run, 4 skipped (1,143 non-skipped), 0
failures. (An earlier total, 1,144, missed the three single-test modules, "Ran 1 test".)
`SUMMARY.txt` has one line per module.

The four skips are the same as on the realism branch's suite (`../suite_d619dd6/SKIPS.md`):
- `test_decision_evidence_world` and `test_upsets` need an environment setting;
- `test_observer_gaps` and `test_observer_profiles` need a golfer who moved into a staff role, which the small test
  worlds did not produce.

The combined-branch checks after integration are in `../combined_checks/`:
- realism + fix `c528575`: 8 modules, 148 tests;
- career + fix `8a2b92a`: 5 modules, 90 tests;
- the fix's focused set: 11 modules, 186 tests, 1 skipped.
