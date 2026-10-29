# Golf Legacy

A text-based golf world simulator. This folder holds the new **shot-by-shot simulation engine**
(prototype v1) and the full v0.13 ChatGPT handoff, preserved unchanged in `legacy/`.

## Core requirement

Every competitive shot in the world is simulated, at every level from high-school events to the
majors, and a full season must still run quickly. See `docs/ENGINE_DESIGN.md`, section 0.

## What's here

| Path | What it is |
|---|---|
| `golfsim/` | The engine: ratings, golfers, courses, shot-by-shot hole simulation, stats, tournaments (stroke and match play), world calendar, geography, major qualification, course library, course records, nations and the world population, season engine, prestige and tour cards, development, finances and careers |
| `tools/observer.py` | The observer (alpha): world library, background advances, linked history pages (`observer_app.py` server, `observer_jobs.py` jobs, `observer_live.py` committed snapshot, `observer_worlds.py` create/copy/export); see `docs/OBSERVER_ALPHA.md` |
| `tools/world.py` | Create and advance a world from the command line |
| `tools/balance_test.py` | Runs the balance study and writes `reports/BALANCE_REPORT.md` |
| `tools/calibrate.py` | Quick rating-ladder check against target scores |
| `tools/calendar_report.py` | Writes the full world calendar to `reports/CALENDAR_REPORT.md` |
| `tools/history_test.py` | Runs the world for decades with development on and writes `reports/WORLD_HISTORY_REPORT.md` |
| `tools/season_test.py` | Plays several full seasons of the whole world and writes `reports/SEASON_TEST_REPORT.md` |
| `tools/world_report.py` | Generates the starting world of golfers and writes `reports/WORLD_POPULATION_REPORT.md` |
| `tools/build_course_library.py` | Rates every course layout and writes `data/` and `reports/COURSE_LIBRARY_REPORT.md` |
| `tools/qualifying_demo.py` | Plays two seasons at the top of the calendar and builds the major fields by the qualifying rules |
| `tools/major_test.py`, `tools/high_school_test.py` | Realism tests at Georgia National and Cedar Creek |
| `tests/` | Automated correctness and balance tests |
| `docs/ENGINE_DESIGN.md` | Plain-language explanation of how the engine works |
| `docs/CALENDAR_AND_QUALIFYING.md` | The world calendar and how players get into the majors |
| `docs/COURSE_LIBRARY.md` | The 380 courses, their layouts, venues and records |
| `docs/WORLD_POPULATION.md` | Nations and how the world's golfers are generated |
| `docs/SEASON_SYSTEM.md` | The season engine, event and player prestige, rankings, money and tour cards |
| `docs/DEVELOPMENT_AND_CAREERS.md` | Development, the monthly plan, money and careers |
| `docs/OBSERVER_ALPHA.md` | How to play the observer alpha, supported saves, bug reports, acceptance checklist |
| `docs/UI_REQUIREMENTS_V1.md` | The V1 interface requirements and what the alpha already covers |
| `docs/BACKLOG.md` | Owner requirements and planned work (current order: observer alpha first) |
| `data/` | Generated course library (`course_library.json`) and layout ratings |
| `reports/` | Latest reports (balance, majors, high school, calendar, qualifying, course library, world population, multi-season test, world history) |
| `legacy/` | The original v0.13 package, untouched |

## Playing it: the observer (alpha)

Double-click **`RUN_OBSERVER_WINDOWS.bat`** (Python 3.11+, nothing else to install): your browser opens the
world library, where you create or open a world, advance it a week, four weeks or to the end of the season,
and explore its people, tournaments, courses, nations, tours, records and history. **Report a problem**
packages a saved world for us. How to stop, reopen, which saves are supported and a short acceptance
checklist: `docs/OBSERVER_ALPHA.md`. From a terminal: `python tools/observer.py --open`.
`RUN_BENCHMARK_WINDOWS.bat` times a season skip on your computer and writes `benchmark_result.txt`.

## Running it (Windows)

1. Install Python 3.11 or newer from python.org (tick "Add Python to PATH").
2. Double-click `RUN_TESTS_WINDOWS.bat` to run the tests.
3. Double-click `RUN_BALANCE_TEST_WINDOWS.bat` to regenerate the balance report (about 5–6 minutes).

Or from a terminal in this folder:

```
python -m unittest discover -s tests -v
python tools/calibrate.py
python tools/balance_test.py          # add --quick for a faster, smaller run
```

No extra packages are needed — standard Python only.
