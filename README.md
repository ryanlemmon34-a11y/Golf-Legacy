# Golf Legacy

A text-based golf world simulator. This folder holds the new **shot-by-shot simulation engine**
(prototype v1) and the full v0.13 ChatGPT handoff, preserved unchanged in `legacy/`.

## Core requirement

Every competitive shot in the world is simulated, at every level from high-school events to the
majors, and a full season must still run quickly. See `docs/ENGINE_DESIGN.md`, section 0.

## What's here

| Path | What it is |
|---|---|
| `golfsim/` | The engine: ratings, golfers, courses, shot-by-shot hole simulation, stats, tournaments (stroke and match play), world calendar, geography, major qualification |
| `tools/balance_test.py` | Runs the balance study and writes `reports/BALANCE_REPORT.md` |
| `tools/calibrate.py` | Quick rating-ladder check against target scores |
| `tools/calendar_report.py` | Writes the full world calendar to `reports/CALENDAR_REPORT.md` |
| `tools/qualifying_demo.py` | Plays two seasons at the top of the calendar and builds the major fields by the qualifying rules |
| `tools/major_test.py`, `tools/high_school_test.py` | Realism tests at Georgia National and Cedar Creek |
| `tests/` | Automated correctness and balance tests |
| `docs/ENGINE_DESIGN.md` | Plain-language explanation of how the engine works |
| `docs/CALENDAR_AND_QUALIFYING.md` | The world calendar and how players get into the majors |
| `reports/` | Latest balance report |
| `legacy/` | The original v0.13 package, untouched |

## Running it (Windows)

1. Install Python 3.10 or newer from python.org (tick "Add Python to PATH").
2. Double-click `RUN_TESTS_WINDOWS.bat` to run the tests.
3. Double-click `RUN_BALANCE_TEST_WINDOWS.bat` to regenerate the balance report (about 5–6 minutes).

Or from a terminal in this folder:

```
python -m unittest discover -s tests -v
python tools/calibrate.py
python tools/balance_test.py          # add --quick for a faster, smaller run
```

No extra packages are needed — standard Python only.
