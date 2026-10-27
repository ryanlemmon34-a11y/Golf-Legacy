# Run and Audit Golf Legacy v0.13

## Requirements

- Windows 10/11, macOS, or Linux with **Python 3.10+** available on command line.
- No packages or paid services required for current code. Uses Python standard library and the built-in SQLite module.
- Extract the ZIP to a short ordinary folder (for example `C:\GolfLegacyClaudeReview` on Windows) and keep the entire `source/` directory intact. Do not move `engine_v013.py` away from its `reference/` folder: it imports required older engine modules.
- This is a **command-line prototype**, not yet an interactive game with menus.

## Easiest Windows method

1. Extract ZIP.
2. Open the extracted folder in File Explorer.
3. Double-click `RUN_TESTS_WINDOWS.bat` to run the automated tests (requires Python installed and on `PATH`).
4. Double-click `RUN_DEMO_WINDOWS.bat` to generate a small 2027 world, score tournaments, export CSV/JSON reports, and audit its SQLite database. This does not create a real 60-year world.
5. If Windows does not recognize `python`, try `py -3` in Command Prompt. You can edit the .bat script to use `py -3` instead of `python`.

## Terminal commands (cross-platform)

Run inside extracted `source/` directory:

```bash
python -m unittest discover -s tests -v
python engine_v013.py --seed 1217 --population 450 --years 1 --events-scale 0.08 --stop-week 52 --db ../demo_output/demo.sqlite --out ../demo_output/reports --quiet
python audit_v013.py ../demo_output/demo.sqlite --output ../demo_output/audit.json
```

The engine prints a JSON run summary. The auditor prints `"passed": true` and `"error_count": 0` if all its database integrity checks pass. Local field shortages or incomplete qualification can still be model limitations even if database integrity passes.

Optional: audit the included two-year SQLite archive without scoring a new world:

```bash
python audit_v013.py ../sample_results/two_season_final.sqlite --output ../demo_output/audit_existing.json
```

For reading the sample archive: SQLite DB Browser (optional third-party desktop UI) or Python's own `sqlite3` shell/API. Basic query example:

```python
import sqlite3
connection = sqlite3.connect('sample_results/two_season_final.sqlite')
for row in connection.execute('SELECT event_id,year,week,event,holes FROM events LIMIT 10'):
    print(row)
```

`audit_v013.py` is read-only for the DB; it does not modify saved records.

## Other engine options

`python engine_v013.py --help` shows:

- `--seed`: fixed random seed, default 1217.
- `--population`: active golfer target, default 450.
- `--years`: number of simulated seasons, default 1.
- `--events-scale`: portion of ordinary tournament series included, default .25. Fixed qualifying and major events remain.
- `--stop-week`: end after week 1–52, default 52. **Note:** archive audits expect all four major weeks, so use 52 for normal tests.
- `--db`: SQLite path. Omit to run using `:memory:` transient data.
- `--out`: directory to receive summaries, events, ranking awards, exemptions and featured score audit.
- `--quiet`: suppress annual progress logging.

### Example full-calendar season (not a 6,000-golfer test)

```bash
python engine_v013.py --seed 1217 --population 1700 --years 1 --events-scale 1 --db :memory: --out ../large_demo --quiet
```

This uses in-memory SQLite and **does not save a durable scorecard DB to disk**; it is useful for speed comparison only. A full durable DB run at this scale has not yet been validated for speed and resilience. Run the small demo first.

## Meaning of the archive

The database contains an `events` table, an `entries` table, compact `rounds` with **one 18-byte blob representing each 18-hole scorecard** (each byte one integer score), ranking snapshots, qualification exemptions and course/hole record histories. Exact columns are defined in `source/history_store.py` and should be inspected rather than inferred.

Every current test run creates fictional golfer identities and events. The example `two_season_final.sqlite` is deliberately a small 450-golfer/25%-calendar validation archive, not a final large-world historical save.

## Safety of modifications

If Claude edits the engine, have it clone this folder or put changes on a branch; do not overwrite `source/reference/*` to rewrite history. Execute `python -m unittest discover -s tests -v` and `python audit_v013.py` on new results before accepting any patch. Persist representative first-year and multi-year baselines for comparison.
