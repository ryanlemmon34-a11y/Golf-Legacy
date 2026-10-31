#!/bin/bash
# Skip-reason identification on c0d1ea5 (after queue14, alone): the full suite's default output gives the skip count
# (4) but not which tests; this verbose run of only the tests that can skip names them and their reasons. It is a
# separate run for identification; the authoritative result remains the full suite's.
Q=/tmp/claude-0/-home-user-golf-legacy/dd633163-5093-57b8-a35e-3e668bc4257e/scratchpad/v18/queue
until grep -q "QUEUE14 \(DONE\|STOP\)" $Q/summary.txt 2>/dev/null; do sleep 30; done
wt=$Q/wt_final2; head=$(git -C $wt rev-parse --short=7 HEAD)
echo "$(date -u +%H:%M:%S) QUEUE15 START (skip reasons on $head)" >> $Q/summary.txt
start=$(date +%s)
(cd $wt && timeout 3600 nice -n 19 python -m unittest -v \
  tests.test_living_views.RatingsOverTime.test_injured_now \
  tests.test_realism.FundingTests.test_a_cheaper_event_is_still_an_option \
  tests.test_session.EngineIdTests.test_a_source_copy_without_git_has_the_same_engine_id \
  tests.test_session.TransactionTests.test_a_lock_left_by_a_dead_process_is_released \
  tests.test_observer_gaps.WorldGaps.test_first_shared_majors_each_once \
  tests.test_observer_gaps.WorldGaps.test_retirement_into_a_staff_role_each_once \
  tests.test_mortality_world.SmallWorld.test_archive_only_browsing_shows_deaths \
  tests.test_decision_evidence_world.DecisionEvidenceWorld.test_outcomes_are_identical_to_the_parent_build \
  tests.test_observer_profiles.ProfilesAndStatsTests.test_a_golfer_who_became_staff_keeps_one_identity \
  tests.test_amateur_support.Rules.test_school_and_club_events_draw_nothing \
  tests.test_amateur_support.Seasons.test_it_is_archived \
  tests.test_upsets.HeavyEquivalenceTests > $Q/skip_reasons.log 2>&1); rc=$?
echo "$(date -u +%H:%M:%S) skip_reasons $head exit $rc $(( $(date +%s) - start ))s $(grep -c 'skipped' $Q/skip_reasons.log) skipped: $(grep 'skipped' $Q/skip_reasons.log | sed 's/ \.\.\. skipped/:/' | tr '\n' ';' | cut -c1-600)" >> $Q/summary.txt
echo "$(date -u +%H:%M:%S) QUEUE15 DONE" >> $Q/summary.txt
