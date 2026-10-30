# Roadmap v14 build: what is in it, how to try it, and what is left

**Build**: branch `build/v14` (GitHub: Golf-Legacy), engine and observer code as of commit `1023dc5` (the commits
after it change only documentation and one test). It starts from the playtest build `7d8e6ed` (branch `main`, unchanged) and
includes the performance branch `perf/season-speed` (outcome-identical changes, reviewed separately in
`docs/PERFORMANCE_REVIEW.md`). Nothing was merged into `main`; the paused world, the playtest installation and
every save were left alone; no long simulation was run; nothing was bought or sent anywhere.

## Status

### Delivered (for review on this build)

| Item | Where |
|---|---|
| Performance work finished and reported (measured; outcomes identical; not enough for the two-minute goal at season 51) | `docs/PERFORMANCE_REVIEW.md`; branch `perf/season-speed` |
| Playoffs: every player listed (Won / Lost playoff, out at extra hole N), entrants and extra holes counted, each extra hole kept from now on, per-site playoffs for multi-site qualifiers; older editions say holes were not recorded | event pages, replay; `tests/test_playoffs.py` |
| "No starts": every barrier and choice with its weeks out of the weeks recorded, never "voluntary" when a barrier was involved; the season page's week-by-week ledger | `docs/ZERO_START_REVIEW.md`; `tests/test_access_ledger.py` |
| Full-time amateur zero-start investigation (read-only; no change made) | `docs/ZERO_START_REVIEW.md`, `tools/zero_start_audit.py` |
| Majors + Premier button on every event-count page; ratings and the world ranking stay global | Stats, golf statistics, profiles, records; `tests/test_scopes.py` |
| Overall on Stats, sortable both ways over the whole list (current / last recorded / start of season) | `tests/test_peak_overall.py` |
| (Recorded) Peak Overall on profiles: date, age, coverage, earliest-attainment ties; captured without random draws | `tests/test_peak_overall.py` |
| Spoiler-safe workflow: persistent Hide results, Watch from round 1, explicit Reveal final, same revealed state on every page | header, calendar, events; `tests/test_spoilers.py` |
| Reference calendar (v2) for new worlds: majors 15/20/25/30, the 36 Premier events at their reference weeks, post-major opportunity weeks 16/21/26/31, qualifying waves with one attempt, cut-off snapshots, target-year amateur rights, the post-week-33 amateur award, qualifying-series allocations, Asian Q-School week 51, day-level travel, the rights ledger, each season's calendar version recorded | `docs/CALENDAR_V2.md`, `docs/CALENDAR_MANIFEST.md`; `tests/test_calendar_v2.py` |
| Classic calendar (v1) kept exactly for existing worlds (byte-identical calendar; identical outcomes) | `tests/test_calendar_v2.py`; see Evidence |

### Deferred (approved, not in this build)

- Old-world calendar migration (needs a separate approval; see `docs/CALENDAR_V2.md`, "Migration").
- "Currently projected / still able to qualify" views (the ledger records earned and conditional places only).
- A per-tour standings-lock / rights-effective table beyond the Q-School weeks and championships by week 48.
- A day-ordered engine for same-week feeders (all feeders are in earlier weeks, validated).
- The per-region amateur affordability comparison before any access change (`docs/ZERO_START_REVIEW.md`).
- Full-size v2 runs and season-1 / season-100 timing of v2 (only after you clear the frozen-playtest boundary).

### Blocked

- **The Test1 archive on Google Drive**: `drive.google.com` is not reachable from the build environment
  (blocked by its network settings), so the named Test1 cases were checked from the roadmap's own figures and
  fixtures, not from your files. To make it readable here, add `drive.google.com` (and
  `drive.usercontent.google.com`) to the environment's allowed domains, or share the archive another way.

### Decision pending (yours)

- The **parent/child tour filter** (not implemented, as asked).
- Whether to **adopt the reference calendar for an existing world** (a copy, at a season boundary).
- The **performance options** in `docs/PERFORMANCE_REVIEW.md`: per-golfer random streams (a new engine for new
  worlds), incremental checkpoints, or declaring outcome-equivalent engines.
- Whether the **Kenya Open effect** under v2 is acceptable (see Known risks).
- Whether to **merge** this build (or only the performance branch) into `main` after your review.

## How to try it (Windows)

1. GitHub → Golf-Legacy → branch **build/v14** → **Code → Download ZIP**; unzip into a **new folder** (not your
   playtest folder).
2. Double-click `RUN_OBSERVER_WINDOWS.bat` there (if the playtest observer is running too, this one opens on the
   next free port).
3. **Create** a world; *Calendar* defaults to **Reference**. Your earlier worlds open as "another engine":
   browse them read-only, or Copy with "continue with this engine" (the copy keeps the classic calendar).
4. Try: *Hide results* in the header, advance a few weeks, open an event from the calendar (it starts at round
   one), *Reveal final result*; a major's page shows the qualification ledger; *Stats* → sort by Overall;
   a profile's Ratings show the peak; *Rules* shows the world's calendar and every major's categories.

Details: `docs/OBSERVER_ALPHA.md` ("Trying the v14 build").

## Evidence

**Calendar versions.** The classic calendar built by this build is identical to the playtest build's (same
series, editions, venues and 520 courses; the series list hashes to the same value). A classic world played
112 weeks (two season ends) on this build and on the previous commit gives identical results, round scores,
prizes, golfers (ratings, status, money), entry routes, tour cards and world ranking (seed 73, 3 % population,
checked twice: after the engine change and on the final code). The reference calendar validates with no
problems (anchors, five-week spacing, 8/20/8 Premier, opportunity weeks, every fixed week, venue pools, feeders
before fields), and its course library validates.

**Focused tests added in this build** (all passing on the final code):

| Module | Tests |
|---|---|
| `test_playoffs` | 5 |
| `test_access_ledger` | 6 |
| `test_scopes` | 4 |
| `test_peak_overall` | 12 |
| `test_spoilers` | 6 |
| `test_calendar_v2` | 22 |
| `test_performance_equivalence` (performance branch) | 7 |

**Whole suite** on the final code (`1023dc5`, every module, 6 at a time): 37 modules, 437 tests; 36 modules
passed (1 test skipped by design). `test_history_consistency` failed once: its last check rendered a profile three
times in a row right after a republished season, while the statistics were being rebuilt in the background, so
the renders could differ under load (a timing race in the test, not in the observer: the page correctly says
"working out the statistics" until they are ready). The test now waits for the rebuild and renders once; the
module then passed (4 of 4). The performance branch alone: 31 of 31 modules (its `test_realism` helper fixed,
40 of 40).

Tests written around the classic weeks (Masters in week 18, USA qualifying in weeks 19-23) now pin their
fixture to the classic calendar, which every existing world keeps; the reference calendar has its own tests.
Two existing assertions were corrected after the new calendar exposed them: a playoff test assumed tied
runners-up are always paid alike (an amateur tied for second is never paid), and a finance test re-derived a
"paying their own way" decision after later winter changes (the decision now keeps the figures it used, shown
in the profile's decisions).

**Performance.** Performance branch (4-CPU machine, disposable copies): season 1 116.3/113.3 s → 112.2/111.9 s;
season 51 214.2/213.0 s → 202.6/204.4 s; outcomes identical. Calendar v2 against v1 on the same small world
(10 % population, 4 workers, alternating): one season 21.0/20.6 s (v1) vs 24.6/21.5 s (v2), with about 4 % more
editions held under v2 (729 vs 702). No full-size or multi-season v2 timing was run (not yet authorised).

## Known risks

- **Season time is still over two minutes** at season 51 on the 4-CPU test machine, and the laptop trend
  points to about 250 s by season 100 on the playtest build. The fixes here are exact but small; the remaining
  options change outcomes or the engine guard and need your decision.
- **Kenya Open under v2**: over a full season the opportunity events stay star-light (median 0 of the world top 30,
  the same as classic), but the Kenya Open (week 10) draws 17 of the top 30 under v2 against 2 under classic --
  an emergent scheduling effect of the earlier Masters (nobody is forced in or kept out). Measured on one
  full-population season per calendar (seed 2027), run in the build environment to diagnose a test.
- **Hide results** keeps hidden editions out of lists, recaps, moments, tournament summaries and finish
  filters, but totals (stats, rankings, records, prize money, golf statistics) count every result and can give
  a hidden result away; those pages say so.
- **The rights ledger is observation only** and new: places earned before a world started using this build are
  not in it; a classic world records it from now on.
- **Engine change**: this build is "another engine" for every existing world (as the performance branch alone
  would be); Copy-and-continue is safe but each copy then plays on this build.
- **v2 is unproven at full size over many seasons**: field fills, membership start coverage and lower-tier
  participation have been checked on small worlds and one full season only.
