# Observer alpha — demonstration and measurements (29 October 2026)

Measured in this container (Intel Xeon 2.1 GHz, 4 logical CPUs, 15 GB, Python 3.13, Linux), observer
started as a user would (`python tools/observer.py --worlds <library> --workers 4`) and driven in Chromium
through its pages and buttons. Full population, seed 2027. Nothing was simulated beyond one season; the
original 50-season world was only read (copied first).

## Create → advance → inspect → save → close → resume → export a copied world

| Step | What happened | Time |
|---|---|---|
| Create "demo world", seed 2027 | Library → Create; the overview shows 2027, week 1 (1 January next) | 4.9 s |
| Double-click **Advance week** | One job, one week: 2027, week 2 (generation 1) | 5 s |
| **4 weeks**, browsing while it runs | A golfer page opened mid-advance showed 2027, week 2 (the committed snapshot) with the progress line "playing · 1/4 weeks"; then 2027, week 6 (generation 2) | 6 s |
| Follow links | Overview → an event → its course → its tournament → Back | — |
| **To end of season**, observer killed (SIGKILL) after 3 of 47 weeks | Restarted: the library showed "an advance did not finish"; Open: "An advance started … did not finish …; nothing of it was saved", world at 2027, week 6 (generation 2) | reopen 2 s |
| **To end of season** (47 weeks) | Season 2027 archived; Seasons lists its majors | 94.4 s job; 95.1 s click to overview |
| Records | Youngest major champions (with active/partial flags); most starts without a win on Premier Tour Europe (100 rows) | first list 0.3 s |
| **Quit**, restart, **Open** | Exit code 0; the world reopened at the same date, 2028, week 1 (1 January next) | — |
| **Copy** then **Report a problem** on the copy | The copy made, the original unchanged; a 19.6 MB diagnostic zip with the note | — |

Duplicate requests, a stop request, an injected failure, an observer killed mid-advance, browsing during an
advance, read-only browsing, worlds saved by another engine and the diagnostic package are also covered by
automated tests (`tests/test_observer_app.py`), against the same code paths the server uses.

## Found and fixed during the demonstration

- **Workers outliving a killed observer.** On Linux the engine's worker pool is forked from the server, so
  after a hard kill the four workers kept the server's listening port (the restarted observer had to take
  the next port) and waited forever. The observer now starts its workers fresh ('spawn', as Windows always
  does) and each worker exits when the observer is gone: after a hard kill, 0 workers left (4 before the
  fix). Equivalence: six full-population weeks (116 events, 14 playoffs, 3,059 missed cuts) give identical
  digests of every part of the world (results, statistics, development, familiarity, finances, staff,
  fatigue and injuries, rankings, records, moments, history, cursor) with the engine's pool and with the
  observer's.
- **A stale lock shown as "being advanced".** A lock left by a killed observer was shown with a manual
  release button although opening takes it over; now only a lock whose owner may still run is shown.
- **The Seasons page on 50 seasons took 36 s** (each season's recap decoded); now one index query (0.0 s).

## The 50-season world (a copy, engine 7334ffe → continued with this engine)

| What | Time |
|---|---|
| Copy with "continue with this engine" (834 MB) | 4.2 s |
| First open (one-time migration to a manifest and index upgrade) | 102.9 s |
| Later opens | 16.0 s |
| Snapshot capture (49,378 people) | 0.44-0.54 s |
| Pages: overview, rankings, person tabs, edition, tournament, courses, calendar, tours, tournaments | 0.06-0.26 s |
| Golfers directory (first) / filtered | 1.19 s / 0.20 s |
| Records: first list (statistics built) / later lists | 13.8 s / 2.2-2.9 s |
| Nations, a nation | 2.1 s, 2.0 s |
| A page while an advance runs | 0.19 s |
| One-week advance from 1 January (the year start runs with that week; then the save) | 33.2 s |
| First page after the advance (new snapshot and history) | 0.64 s |
| Per-page check that the committed checkpoint is intact (80 MB hashed) | 71-81 ms |
| Diagnostic package with the index / required files only | 811 MB zip (282 MB required + 973 MB index) |
| Main process peak RSS | 3.06 GB |

Not measured here: Windows, the owner's computer, season 100.
