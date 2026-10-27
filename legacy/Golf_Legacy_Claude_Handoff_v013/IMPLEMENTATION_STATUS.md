# Implementation Status: What v0.13 REALLY Does

**Source of truth:** `source/engine_v013.py`, its imports in `source/reference/`, `source/rankings.py`, `source/history_store.py`, and tests in `source/tests/test_v013.py`. All runnable from Python 3.10+ standard library only. Do not confuse the approved vision with the shipped prototype.

## A. Status by system

| Component | Status | Verification / qualification |
|---|---|---|
| Generated persistent fictional professional golfer population | **Implemented, incomplete scope** | Generates regular professionals with distinct current attributes, ages, countries, archetype-like profiles, development and exits; lacks complete university/amateur/part-time tiers |
| Generated staff with coach/caddie links | **Partial** | Inherited staff identities and associations; not complete autonomous coaching/caddie market, salary negotiation, scalable career histories and synergies |
| Hole-by-hole chronological scoring | **Implemented** | v0.7 scoring inherited; v0.13 wraps four event formats; live cut and lead pressure, pairing, playoffs, cut/payout tests |
| Correct 18/36/54/72-hole events | **Implemented** | Scorecard round counts, cuts and prizes tested; explicit format metadata |
| Correct tee groups / AM–PM waves / weekend pairs | **Implemented in tested cases** | Event-level and SQLite tests; full range of small field edge cases still deserves additional tests |
| Course-specific holes and familiarity | **Partial** | Individual holes/courses and inherited familiarity present; layout versioning and broad geographical course quality incomplete |
| Four major-only weeks | **Implemented** | Weeks 14/19/24/30, global calendar assertions |
| 40 elite events (4 major + 36 premier) | **Implemented in calendar** | Tier 1 split 8 flagship, 20 standard, 8 opportunity; W15/20/25/31 opportunity slots |
| Fixed qualifiers and named national-open links | **Partial** | Week 13 feeder and W27 national open tested into W14 and W30 respectively; full paths not built |
| No fictitious amateur-only qualifiers | **Implemented safe deferral** | Two amateur-only fixtures NOT scored because eligible amateur population isn't implemented |
| World pro ranking | **Provisional** | Rolling 104-week weighting/divisor math and snapshots tested; field strength based on technical ability proxy, **not calibrated real adjusted scoring** |
| Tour standings | **Partial** | Event/tour-season records exist; full membership/card rules and robust promotion/relegation not integrated |
| Global weekly AI schedule utility and waitlists | **Not implemented** | Inherited simpler field/schedule logic, not rolling 8–12-week dynamic planner / entry lifecycle |
| Full amateur/college ranks, qualification | **Not implemented** | Major fields deliberately underfilled rather than fictitiously populated |
| Large 6,000-person, 40-circuit, 500–600 event season | **Not tested / not built** | v0.13 baseline 1,700 active golfers, 33 circuits, 360 fixture rows, 358 completed events |
| Country infrastructure growth | **Implemented, poorly calibrated** | Real existing national growth feedback; 60-year tests show excessive saturation in small-country cohorts |
| National open home-star guest starts | **Implemented, simple rule** | Includes elite home invite with budget/calendar checks; identity currently one country string |
| Event-specific purses & financed entry | **Implemented, partial realism** | Conserved purses, cash-gated entries; cost magnitudes and career options not empirically fitted |
| Full persistent archive for scored events | **Implemented, tested at small scale** | SQLite stores 18-byte per-round hole arrays, pairings/tee starts, entries, exemptions, weekly rank snapshots, course/hole records |
| Durable 200-year incremental save | **Not implemented / not demonstrated** | Year-end staging, crash safe weekly/monthly journaling and archival scalability still needed |
| Prestige, hype, sponsorship and staff-market effects | **Not implemented to approved design** | No full separate prestige/hype economy; do not imply operational player prestige exists |
| Monthly human manager UI, spectator & retire/recreate | **Not implemented** | Current output is CLI + CSV/SQLite, not playable career management |
| World encyclopedia UI | **Not implemented** | Directories for golfers/caddies/coaches/courses/tours are product requirements only |
| Tauri/Rust/React desktop port | **Not implemented** | Current engine Python; optimization path recommendation only |

## B. Validated tests / actual measurements

- **Fresh review in this handoff:** `cd source && python -m unittest discover -s tests -v` → **8/8 passed**. See `TEST_EXECUTION_LOG.txt` for evidence recorded from clean package.
- v0.13 built **300 calendars** across five 60-year seeded batches (not 300 scored seasons) with zero anchor/format drift violations.
- v0.13 full calendar one year: seed 1217, **1,700 golfers / 360 scheduled fixtures / 358 completed / two amateur-only qualifiers deferred / 1,352,916 scored holes**, runtime ~28.916s *without permanent SQLite writes*. Exactly **241 unfilled major slots** across four majors due incomplete eligibility. Zero engine/purse-validation errors reported.
- v0.13 persistent historical two-year test at 450 golfers and quarter calendar: **243 events, 21,851 entrants, 54,824 rounds, 986,832 individual hole scores, 104 weekly ranking snapshots, 482 qualifying exemptions, 7,539 dated course/hole record changes**. Independent integrity audit **0 errors**. **41 low-field warnings**; small world insufficient to fill lower fields stably.
- v0.7 older two 60-year SMALL scale tests: 450 active golfers, ~25% calendar, 4 majors yearly. 1217 had 16-major leader and 2601 had 14-major leader, with 109 unique major winners in each world. ~34 average major champion age. **Not distribution estimates at intended full-world population**. Home-country national opens passed attendance and record checks. Several nations saturated near infrastructure cap.
- v0.8 single-year expanded capacity: **4,500 golfers, 33 circuits, 341 completed events, 1,980,648 holes in ~122.98s**, no integrity/finance errors, but engine and calendar differ from v0.13.

## C. Technical architecture currently in package

```
source/engine_v013.py           # CLI; integrates v0.11 calendar with inherited v0.7 scoring/world
source/rankings.py              # ranking book, time decay, provisional field-strength ranking
source/history_store.py        # SQLite schema, event/round/blob records, checkpoint
source/audit_v013.py            # independent archive validation
source/reference/engine.py      # earliest generation
source/reference/engine_v02.py  # hole simulation early version
source/reference/engine_v03.py  # inherited attributes, entities and golfers
source/reference/engine_v04.py  # performance calibration
source/reference/engine_v05.py  # financial and career mechanics integration
source/reference/engine_v05_growth.py
source/reference/engine_v06.py  # more career/country corrections
source/reference/engine_v07.py  # national opens
source/reference/capacity_engine_v08.py
source/reference/calendar_generator_v011.py
source/reference/career_economics.py
source/tests/test_v013.py
```

The v0.13 engine uses `sys.path.insert` for source/reference, so **do not drop reference files** when sending it elsewhere. The directory tree here has been preserved so it runs on extraction without changing imports. No dependency installation is needed for the current source.

## D. Accuracy pitfalls for outside reviewers

1. The approved 15 skills reflect design. Existing source's Golfer data model and scoring formulas were inherited from earlier versions and **may not match every named rating in the new spec**. Do an attribute-to-formula mapping audit before claiming 15 skills have independent scoring effects.
2. “OWGR-inspired” does not mean official OWGR conformity. Treat ranking strength, divisor and allocations as game model requiring calibration.
3. Some major fields are short **on purpose**, not an allocator that is fully fixed. Need real amateur, club-pro and other qualification routes.
4. The sample archive is fully scored for its simulation subset, but it doesn't stand in for a realistic 6k-golfer world.
5. Staff and outside-work money are inherited model components; sponsor-driven prestige/contracts remain future features.
6. “Every golfer history for centuries” is the goal. v0.13 demonstrates permanent event/hole history for a two-year small test, **not 200-year storage performance or complete all-career audit**.
7. Do not silently expand or simplify the golf logic while making this runnable in new environments.

## E. Key commands

```bash
cd source
python -m unittest discover -s tests -v
python engine_v013.py --seed 2601 --population 450 --years 1 --events-scale 0.1 --stop-week 24 --db ../output/review_world.sqlite --out ../output/review_results --quiet
python audit_v013.py ../output/review_world.sqlite --output ../output/review_audit.json
```

The short partial-year command above is for rapid runnable review. A database audit of a **partial** year including week 14 and 19 can pass; full-year production tests should run all 52 weeks. See `RUN_INSTRUCTIONS.md` for complete options and sample archive audit.
