# Pass of 31 October 2026: HAL's review of 324e263, the expanded roadmap, fresh worlds only

**Asked for**: the owner's prompt of 31 October (HAL's review of `build/v16` at `324e263`; the expanded roadmap as the
full pre-playthrough scope; where they differ, the prompt wins: no old-world compatibility, no resuming previous
saves). **Branch**: `build/v16` (no merge: that needs a separate approval). Nothing was deleted; no old world was
continued; no multi-hour run was started.

## Completed (each package its own commit, with its tests)

| Package | Commit | Changes simulation? | What |
|---|---|---|---|
| 1. Review fixes | `5fdc76b` | **Yes** (injury length) | Staff seasons end-exclusive (week-1 ends, reunions, archive bounds); first appearance back counts qualifying, first main event shown apart; an injury announced as n weeks keeps a golfer out of exactly n weeks of entries (across the year end too); the recorded per-pair fit and rapport shown on both profiles (the v16 report's claim corrected); inaugural Masters invitees documented under the major-trip guarantee; all-majors funding tests |
| 3. Qualification windows | `c28bf77` | No | Every windowed route's rule, current-edition handling and exact expiries (`docs/QUALIFICATION_WINDOWS.md`), boundary tests for today's definitions, one policy choice flagged |
| 2. Fresh worlds only | `dd0bb27` | No | Unsupported saves (earlier engine, older format, classic calendar) named with reasons: browse and copy only, never continued, changed or deleted; new worlds always v2; checkpoints record their calendar |
| 4. Long histories | `17c673b` | No | A world's index validated and missing or stale seasons rebuilt on opening; a side index outside the folder for read-only histories; exports include the index by default |
| 5. Coaches and Prestige | `32bc43d` | No (shown identical) | Coach teaching and scouting shown and recorded each season; Prestige for every golfer (profile, season rows, sortable directory) and for coaches and caddies (their reputation, by role); recruitment design note |
| 6. Amateur support | AMATEUR_COMMIT | **Yes** | Bands A/B/C ($25k/$12k/$5k) as an initial calibration, in kind for events, caddie and coaching; observable eligibility; week-1 budget, in-season A/B upgrades, one-band renewal decline; ends on turning pro or retiring; payment order school/club, support, golfer, organizer; every payment recorded; measured over three seasons |
| 7. Reconciliation and validation | this commit | No | Roadmap status (`docs/BACKLOG.md`), long-run plan for approval (`docs/LONG_RUN_PLAN.md`), this report |

*Measurement and validation results: in progress (added when they finish).*

