# Desktop interface cleanup on the realism testing branch

The `build/realism-youth-aging-longirons` branch now combines the existing realism playtest with the observer interface cleanup. It does **not** include the separate career-preview gameplay, and main is unchanged.

The UI changes only read and present the same committed world. Simulation calculations, RNG, engine fixes, save formats, development rules, population, and existing worlds are unchanged by this batch. Existing realism caveats in [RESULTS.md](../realism/RESULTS.md) still apply.

## What changed

- Search in the header includes golfers, coaches and caddies. All people is also a sidebar destination, with remembered views and a back-to-results link.
- Results Clear stays on Results. Apply retains tournament, honor and qualifying context. Each column sorts all matching results before the 50-row pagination, with unrecorded values last in either direction.
- The sidebar identifies the current section and stays available on long pages. The header keeps the current world/date and primary Advance week action visible. Longer skips are grouped under Longer advance, with the same cursor and one-time request safeguards.
- Playing profiles begin with a compact, explicitly dated summary and the recorded trophy case. Sections link to seasons, status, ratings/health, performance, stories and places. Less-used details expand on demand; nothing was removed. Other tabs do not repeat the full current snapshot, and historical seasons lead with that season's context.
- Tables have keyboard-operable sorting, sticky headers and identity columns inside scroll regions, numeric alignment and consistent pagination. Career totals remain in a footer when sorting both season results and golf statistics. Expanded tour rows retain their season and age even after sorting.
- The overview places rankings beside season progress and recent winners on a wide desktop.
- Partial careers, current-season figures, retired final ratings, missing values and historical-season facts remain distinguished. Lengthy definitions can be expanded; coverage warnings stay visible.
- Small question-mark controls explain all 21 attributes, Overall, rating groups, person Prestige, Aggression and common statistics. Hover or keyboard focus opens a description; click can hold it open, Escape dismisses it, and scrolling clears it. The numbers remain displayed. Popovers are outside the table's clipping region and positioned away from the triggering cell.

Descriptions distinguish causal simulation inputs from recorded outcomes. Attribute wording was checked against `golfsim/engine.py` (`Player`, `play_hole`, tee and approach decisions), fatigue/injury/scheduling in `golfsim/season.py`, prestige and staff functions, and metric definitions in `golfsim/golfstats.py`. They describe the current rules without exposing hidden potential. Tournament and course Prestige explain event appeal, points and venue selection; national Prestige explains how future entrants' country shares shift without changing worldwide population totals or talent. These were checked against venue reviews, `golfsim/prestige.py` and `golfsim/participation.py` and retain the existing detailed page explanations.

The career preview remains a separate build on `build/career-v1-foundation`. This published cleanup does not change its decision/plan interface or introduce career gameplay into the realism test. The shared Stop control now also recognizes a career-advance job, for compatibility with a future integration.

## Launch the combined build

Follow the existing [realism test instructions](../realism/TESTING.md), fetching the current branch head. For an existing realism checkout, first preserve any local edits, then use a normal fast-forward pull. Use its separate test-world library rather than your original saves.

## Automated checks

From the repository root:

```
python -m unittest tests.test_ui_shell tests.test_ui_profiles tests.test_ui_results tests.test_ui_help tests.test_server_sort -v
python -m unittest tests.test_observer_app tests.test_observer_profiles tests.test_observer_history tests.test_views tests.test_myworld tests.test_golf_stats -v
python -m unittest discover -s tests -v
```

The new UI suites use synthetic records and renderer checks, not altered simulation outcomes. Results tests include more than one page, all nine sort columns in both directions, stable ties, zero versus missing prizes, and query preservation. Help tests check preserved numeric values, separate help/sort controls, source-grounded descriptions, escaping, and focus/hover/Escape/click/scroll behavior using a Node DOM harness. That harness is not a browser or a visual test.

A disposable saved-world renderer sweep covered 38 routes, including populated saved views and both statistics modes after the background history build completed. It checked column semantics and numeric-rating help, compiled every embedded script with Node, and verified unchanged hashes for committed save generations and archive JSON. This does not measure pixel layout.

## Desktop playtest checklist

At 1920×1080 and 2560×1440, in light and dark mode:

1. Search for a coach or caddie who has never played. Open the profile, then use Back to People. Confirm the exact search and sort remain.
2. Open a golfer with several seasons. Check summary, honors and season totals. Open Ratings & health through both the section link and the recorded-peak link, then change the rating-history selector. It should return to that chart, not the page top. Expand tour rows and sort them; every row should still identify its season.
3. Open Results. Filter a season, then Clear. Confirm Results remains selected. Sort prize or event across more than 50 starts; page forward and back. Apply a second filter without losing an honor/tournament/qualifying scope.
4. Sort a season table using only Tab and Enter or Space. Career totals must stay at the bottom. Scroll a wide table both directions; headings and the golfer/name column should remain visible. Check that missing entries remain distinct from recorded zeroes.
5. Open a historical season and a retired golfer. Dates and final ratings must not imply current-season facts.
6. On a disposable test world, advance a week; try a repeated click and browser refresh. Open Longer advance, enter an invalid season count, close it, and check that Advance week still works. Reopen it, then start a four-week advance and Stop. Completed weeks should be preserved, with no duplicate advance. Multi-season requests must still validate their season count.
7. Reopen the world and repeat the search/profile/Results/Back flow. Existing saved views should still work.
8. Hover and Tab to help controls in Ratings, Prestige and statistics headers. Check that a readable explanation appears without changing any number or sorting the table. Dismiss with Escape, move focus away, scroll the table, and try a control near each viewport edge. Confirm mouse movement into the popover keeps it readable and a screen reader announces the description.

## Visual verification limitation

The implementation environment could render all tested application routes and run HTTP/HTML checks, but could not start Chromium because its runtime denied the required socket. The supported remote browser also could not connect to the local preview. Therefore screenshots, desktop layout dimensions, and real-browser keyboard interaction were **not** verified here. The checklist above remains the visual playtest, not a claim that it passed.
