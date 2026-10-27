# Golf Legacy v0.13 — scored calendar integration (EXPERIMENTAL)

This is the next **working Python engine revision**, based on the frozen v0.7/v0.8 golf simulation and the v0.11 calendar, following the v0.12 development/test plan. It is not a playable desktop application, is not the proposed 6,000-golfer universe, and has not yet passed the 60-year realism tests. Earlier source packages are not overwritten.

## What changed

- A stable **52-week cascade** with one major and no other events in weeks 14, 19, 24, and 30.
- **40 combined Tier 0+1 events**: 4 majors, 36 Premier events (8 flagship, 20 standard, 8 opportunity). At least one opportunity event follows each major in weeks 15, 20, 25, 31.
- Tournament lengths of **18/36/54/72 holes** executed by the actual chronological, hole-by-hole scoring engine, with proper no-cut/cut configurations, tee-order pairings, live cut/lead pressure, ties and playoffs.
- Tournament-specific prize pools. All paid purses reconcile against their scheduled event pool.
- Targeted qualifying results are **recorded and propagated into the relevant later major**; the major does not fabricate players to fill its field.
- Experimental weekly world ranking with 104-week decay and no conventional world-ranking points for 18/36-hole qualifiers or short local events; separate tour-season scoring.
- **SQLite historical archive** storing physical 18-hole scorecards as compact 18-byte binary records, tee assignments, round results, earnings, qualifying-exemption provenance, weekly ranking snapshots, and dated course/hole record changes.
- Added four source-country entries needed by the newer calendar: Wales, Chile, Fiji, Papua New Guinea.

## Quick start (requires Python 3.10+; no third-party runtime dependencies)

From the directory containing this README:

```bash
python -m unittest discover -s tests -v
python engine_v013.py --seed 2601 --population 450 --years 2 --events-scale 0.25 --db my_first_world.sqlite --out my_first_results --quiet
python audit_v013.py my_first_world.sqlite --output my_first_audit.json
```

The reduced example is a functionality test: events may be underfilled because the field is artificially small. The `--db` parameter enables permanent local SQLite results (omit it to use a transient in-memory database). `--events-scale 1` requests the full calendar, but that is **not** a promise of stable 60-year performance.

Existing frozen dependency implementations are in `reference/`; the new source is in `engine_v013.py`, `rankings.py`, `history_store.py`, `audit_v013.py`. The packaged `results/` includes example one-year and two-year outputs and an archived two-year SQLite database. The final package deliberately excludes interrupted benchmark databases.

## Current scope and limitations

1. No simulated college/amateur career population; **two amateur-only qualifying event series per year are deferred** to avoid falsely using professionals as amateurs. Accordingly, majors are presently underfilled.
2. The world ranking is **OWGR-inspired**, not a verified reproduction of the official field-strength/scoring formula: v0.13 still uses a pre-event technical-ability proxy. There is no historical calibration of the ranking-points curve yet.
3. Real weekly AI scheduling, qualified tour-card categories, Q-school, multiple memberships and true season-long membership retention are not finished. The previous engine's basic entry decisions remain in use outside selected major invitations.
4. The full-scale engine has not been proven fast while writing and querying many years of persistent SQLite history. Completed full-calendar **in-memory** measurement is ~29 seconds of simulation for one 1,700-golfer year; the archived, larger-world timing remains to be measured.
5. This release has 33 circuits and roughly 360 annual fixtures, **not** 40 circuits, 6,000 golfers, or 500–600 fixtures. Larger tests should follow the gates in `NEXT_TEST_GATES.md`.
6. Venue identities and course-record histories are preserved; course redesigns and separate layout versions remain future features.

See `TEST_REPORT_V013.md` for measured results and `NEXT_TEST_GATES.md` before beginning the next realism test.
