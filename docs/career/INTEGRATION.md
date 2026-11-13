# Career slice + realism (dev-3): integration test build

Branch `integration/career-realism-v1`. Test build only. `main`, `build/career-v1-foundation` and
`build/realism-youth-aging-longirons` are unchanged. This is **not full career mode**: it is the existing
career Phases A/B four-week slice running on the current realism rules.

## What is combined

| Source | Head | Brings |
|---|---|---|
| `build/realism-youth-aging-longirons` | `52870f5` (code of `7e88aa2`) | dev-3 rules for new worlds (elite tail, prodigy readiness, standing-based seeded money), dev-2 aging, long-irons table, observer UI polish, backlog item 6 (Golfer Encyclopedia Entry, roadmap only) |
| `build/career-v1-foundation` | `c3847d3` | Career Phase A (human-control foundation) and Phase B (four-week observer slice), docs in `docs/career/` |

The branch is cut from `52870f5` with `c3847d3` merged into it.
- Both branches already contain the engine fix `46013a5`, so only the changes made after it on each branch are new.
- One textual conflict: the observer sidebar in `tools/observer.py`. It keeps the realism UI's sidebar markup with the
  career section first, as the career branch had it. `/career/plan` highlights "Career" in the sidebar.
- `golfsim/season.py` and `tools/observer_app.py` merged without conflict. Every realism hook (dev rules, standing-based
  seeded fame, aging rules) is present.
- The career start takes a member of the junior class the world itself generated, so the controlled newcomer comes
  from the world's own development rules (dev-3 in new worlds). No career code path creates golfers.
- No option C, no new calibration, no ten-candidate setup, no annual switching, no new career phases.

## Equivalence and compatibility (measured)

- **All-AI equivalence against dev-3:**
  - The career fixture (seed 11, scale 0.05; one season, then 12 weeks committed one at a time) gives identical
    digests on the realism build `52870f5` and on this build: `c6230d8e…c25b` and `80ad8e6f…b8a9`.
  - `tests/test_career_foundation.py` now carries these as its reference.
  - The career branch's old reference (main 18a8e23 + engine fix) cannot hold. The long-irons table (rules 2026-11-16)
    changes play in every world, whatever its development rules: a dev-1 fixture gives `360fed3a…a165` on `52870f5`
    and on this build alike.
- **dev-1 and dev-2 fixtures:** identical on `52870f5` and this build (dev-1 `360fed3a…`/`a234d058…`, dev-2
  `f8061e78…`/`e4957fe2…`).
- **Fresh full-size worlds** (seeds 416342, 8675309, 2027):
  - Generation is identical to `52870f5`: every golfer's ratings, potential, ceilings, cash, backing, peak age and
    aging rate.
  - So is season seeding (fame and prestige). Seed 416342 starts with Rory Wilson at 93.87 and $66.9M, as in the dev-3
    test build.
- **Old saves:** this build has a new engine fingerprint (`50c43358…`).
  - Test4's two saves (engine `1a3af910…`) and every older world are listed as "saved by an earlier engine" and can only
    be browsed.
  - Nothing is migrated or reinterpreted. Continue those worlds with the build that created them.

## Launch on Windows

1. Unzip `Golf-Legacy-<sha>.zip` into a **new, empty folder** (not over an existing checkout).
2. Run `python tools/observer_app.py --worlds worlds-integration-test --workers 1 --open` from that folder.
   `worlds-integration-test` is a new library folder, so no existing world is touched.
   - Alternatively, double-click `RUN_OBSERVER_WINDOWS.bat`, which opens its own default library folder.
3. **World library → Start a new career.** The observer creates a fresh world and plays its first season under AI. It
   then hands you one of that world's own 2028 juniors at 1 January of the second season.
4. Follow the career walkthrough (`docs/career/PHASE_B_WALKTHROUGH.md`, "Try it", steps 2–6):
   - plan a four-week block (events, training, rest; fallback; selection and qualifying policies);
   - advance;
   - answer offers;
   - reload;
   - return the golfer to AI.
5. Fresh all-AI worlds work as before (World library → New world). Their ratings and money are the dev-3 test build's.

## What the career slice does not do

These were already not built on the career branch and are unchanged by the integration:
- **The winter:** turning pro, residence, retirement, college moves and the season review. The career stops before the
  winter; hand the golfer back to AI to continue.
- **Setup choices:** no customisation, choice of newcomer, rerolls, ten-candidate setup or annual switching, and no
  entry into an existing world.
- **Staff and money:** no golfer-initiated staff hiring, paid work weeks, sponsorship decisions or full finance ledger.
- **Interface:** no separate inbox and no mobile layout.
- **Other:** no Birth of Pro Golf, and no Golfer Encyclopedia Entry (backlog item 6, after career functionality testing).

## Tests

Measured on the code of this commit. The only changes after `01a7340` are this document, the scripts in
`docs/career/integration/` and the career test's reference digests.
- **Career foundation** (`tests.test_career_foundation`, model/API): 25 tests OK, including all-AI equivalence against
  dev-3.
- **Career, session, observer and UI** (`test_observer_career`, `test_session`, `test_observer_app`, `test_ui_shell`,
  `test_ui_help`, `test_ui_profiles`, `test_ui_results`): 96 tests OK.
  - These are the observer over HTTP, rendering HTML with the real routes and the origin, cross-site and identity
    guards. No browser is driven.
- **Realism and UI-assertion modules** (`test_realism_pass1`, `test_dev3_elite_money`, `test_aggression_visible`,
  `test_nation_achievement`, `test_v17_integration`, `test_world_prestige`): 75 tests OK.
- **All-AI digests and fresh full-size worlds:** `docs/career/integration/allai_digest*.py` and `fresh_fp.py`, run on
  `52870f5` and on this build (results above).
- **Career on a full-size fresh world** (`docs/career/integration/career_smoke_full.py`, seed 416342, model/API through
  `Session`, no browser): 19 of 19 checks.
  - Start on a genuine 2028 junior generated under dev-3, with no potential or ceilings in the view.
  - A second career refused.
  - The first stop for a plan (a coach offer was waiting as well).
  - An ineligible event refused with its reason. An event with a training fallback, training and rest planned. The
    week-1 entry was not accepted (field full), so the fallback applied, with a notice.
  - Stale career version and wrong-date requests refused. A repeated request not run twice.
  - Save and reopen identical.
  - Twelve more blocks planned, with a coach offer declined.
  - A safe stop at week 52 before the winter (no 2029 class created).
  - Return to AI, the world continuing under AI into 2029, and a reopen afterwards.
  - Run time: 336 s for the first season and 768 s in all, on this 2-core cloud machine (not Ryan's).
- **Full suite:** run on this exact commit. The result and any failure with its baseline status are in the hand-off
  note, not in this file, so that the tested commit and the shipped commit are the same.

**Limits of these checks:**
- No real browser: page layout, JavaScript behaviour and Windows-specific launching were not exercised here.
- Performance is from the cloud machine only.
- One full-size career season was played; long played careers under the integration have not been run.
