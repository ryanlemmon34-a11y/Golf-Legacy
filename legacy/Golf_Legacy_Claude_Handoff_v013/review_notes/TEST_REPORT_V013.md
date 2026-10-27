# Golf Legacy v0.13 — implementation and test report

**Status:** experimental integration; targeted engine testing passed; full 6,000-golfer and 60-year realism tests **not yet run**.

## What we integrated and why

The old engine scored every event as a four-round competition, with tour-level prize economics. Meanwhile, the calendar preview included short 18/36/54-hole events, fixed major weeks, qualifying pathways, and distinct event purses. v0.13 connects the real calendar to the existing golf simulation **without changing its scoring-probability calibration**. Events now run the correct number of rounds, with independently checked archived scorecards and correct tournament-specific prize pools. The four global major weeks have one event each.

### Premier event structure

- Tier 0: **four 72-hole majors**, fixed in weeks 14/19/24/30.
- Tier 1: **36 regular events**: 8 flagship, 20 standard, 8 opportunity; four opportunity events follow the majors in weeks 15/20/25/31.
- Current calendar: **360 event fixtures per year**, some qualifying fixtures deliberately deferred until amateur eligibility exists.
- Tournament-series IDs retain lengths, prestige and purses across multiple years.

### Validation results

| Validation | Result |
| --- | --- |
| New integration unit/integration suite | **8 / 8 pass** |
| Frozen v0.7 and v0.6 regression tests | **8 pass** (2 v0.7 + 6 v0.6) |
| Generated calendar years | **300** (5 independent seeds × 60 years) |
| Major blackout violations | **0** |
| Stable series formats/purses violations | **0** |
| Cut/round/pairing/in-event purse reconciliation | Passes targeted cases |
| Week 13 qualifier winning berth → Week 14 major | Passes; source recorded |
| Week 27 Australia National Open → Week 30 Brittania major | Passes; source recorded |
| Amateur-only qualifier mistakenly awarded to pro | Prevented: event deferred |
| Persisted 2-year SQLite independent audit | **Pass: 0 archive integrity errors** |

## Full-calendar baseline — one year, *no persistent archive writes*

Command configuration: seed 1217, 1,700 active golfers, 2027, events_scale 1.0, all 52 weeks.

| Measure | Actual |
| --- | ---: |
| Scheduled fixtures | 360 |
| Completed events | **358** |
| Deferred amateur-only qualifiers | **2** |
| Competitive holes simulated | **1,352,916** |
| Simulation runtime | **28.916 seconds** (wall ~31.9 sec) |
| Engine validation errors | **0** |
| Prize reconciliation errors | **0** |
| Home-country national opens | **28** |
| Home-country elite visits | **53** |
| Unfilled major slots | **241** across four majors |

**Important:** The one-year run used `sqlite_history=False`, so its ~29-second figure **does not establish the speed of full durable archival**. The major fields were short because true amateur/college and comprehensive exemption pathways have not yet been implemented. It would be misleading to claim this world was already historically realistic or 6,000-golfer-ready.

## Persistent archive test — two years, artificially reduced world

Command configuration: seed 2601; **450 golfers**; 25% calendar; two complete years (2027 and 2028); permanent SQLite archive with year-end checkpoints.

| Measure | Actual |
| --- | ---: |
| Completed events | **243** |
| Player tournament entries | **21,851** |
| Archived 18-hole rounds | **54,824** |
| Archived individual hole scores | **986,832** |
| Full weekly ranking snapshots | **104** |
| Recorded qualification exemptions | **482** |
| Dated course-record changes | **743** |
| Dated hole-record changes | **6,796** |
| Independent archive-integrity errors | **0** |
| Prize-ledger reconciliation errors | **0** |
| Engine validation warnings | **41** (mostly low entrant counts) |

The 41 warnings are **real and not suppressed**: this tiny world is insufficient to fill all regional fields sustainably. The archive validation separately passed, including actual scorecards, pairing/tee information, cuts, event lengths, recorded qualification sources, and prize amounts.

The two-year SQLite artifact is `results/two_season_final.sqlite`, with independent audit JSON beside it. It can be opened with a local SQLite viewer without any hosted service.

## Performance and correctness limitations discovered

1. Writing every tournament result directly through persistent SQLite produced severe slowdown in longer/full-size benchmark attempts. v0.13 therefore builds a season's history in RAM and transfers it to durable SQLite through native database operations at the season boundary. This is **not yet benchmarked successfully at 1,700+ golfers for many seasons**. A full application will need safe periodic checkpoints (weekly/monthly or transactional WAL batches), plus crash recovery; year-only saving is not acceptable for a playable career game.
2. The ranking formula is only a placeholder for controlled test flows: 104-week weighting and divisor are correct to the design, but event strength is inferred from a technical-ability proxy rather than empirically adjusted performance. The scoring-point curve is not historically validated.
3. Major field eligibility is intentionally restricted to recorded routes and existing invitations. That prevents fictitious qualifiers, but it also produces small major fields until college/amateur qualifiers and full exemption categories exist.
4. The present championship history tests check how events are recorded, **not** whether realistic century-scale records, prize distributions and winner distributions are established. At present, no new 60-year realism run has been performed.

## Acceptance before the next full-scale realism test

See `NEXT_TEST_GATES.md`. The most important next task is **genuine amateur/college populations + entry allocator + sufficient field depth**, then ranking model calibration and long-archive performance before 6,000-golfer and 60-year runs.
