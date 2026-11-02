# The four skips in the full suite on d619dd6 (messages verbatim from a verbose re-run of these modules, all OK)

- test_outcomes_are_identical_to_the_parent_build (tests.test_decision_evidence_world.DecisionEvidenceWorld.test_outcomes_are_identical_to_the_parent_build) ... skipped 'set GOLF_PARENT_CHECKOUT to the parent build'
- test_retirement_into_a_staff_role_each_once (tests.test_observer_gaps.WorldGaps.test_retirement_into_a_staff_role_each_once) ... skipped 'no golfer became a coach or caddie in this small world'
- test_a_golfer_who_became_staff_keeps_one_identity (tests.test_observer_profiles.ProfilesAndStatsTests.test_a_golfer_who_became_staff_keeps_one_identity) ... skipped 'no golfer became staff in this short world (checked on the 50-season copy)'
- test_recording_changes_no_outcome (tests.test_upsets.HeavyEquivalenceTests.test_recording_changes_no_outcome) ... skipped 'whole-season run: set GOLF_HEAVY_TESTS=1'

Two need an environment setting (a parent checkout for an equivalence check; a whole-season heavy test); two need data the small test worlds did not produce (no golfer moved into a staff role).
