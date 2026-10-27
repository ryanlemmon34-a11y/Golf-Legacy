# Code & Data Architecture for Claude Review

## 1. Current execution sequence (v0.13)

`engine_v013.py` is the entry point. It subclasses the v0.8 capacity world, which inherits earlier v0.7 → v0.6 → v0.5 → v0.3 engine layers. It imports the v0.11 calendar generator for fixture metadata and adds its own revision for the 8/20/8 Premier categories.

Simplified causal sequence for one simulated season:

```
CREATE / UPDATE WORLD
  ├─ generated golfers, courses, regions, and staff (legacy model)
  ├─ initialize economy / start-of-year resources
  └─ revised_calendar(year, seed) -> stable fixtures

FOR week 1..52, in scheduled order
  ├─ advance funds / career opportunity
  ├─ choose lawful-ish entry field (not yet full statuses / global weekly planner)
  ├─ for each tournament:
  │   ├─ group and order players
  │   ├─ simulate chronological scoring per physical hole
  │   ├─ apply live cut/leaderboard pressure
  │   ├─ run configured cuts / playoff
  │   ├─ pay and reconcile event purse
  │   ├─ grant only defined earned exemptions
  │   └─ store full event/round/qualification/record facts in SQLite RAM stage
  └─ recompute provisional world ranking and save snapshot

END YEAR
  ├─ assess economy, tour movement, development and retirement
  ├─ add replacement golfers as necessary (not yet broad amateur birth cohorts)
  ├─ evolve countries
  └─ if durable --db path: checkpoint season's records into SQLite file
```

### Source layers

- `source/engine_v013.py`: major weeks and counts; explicit format, event purse, selected feeder entries, qualification ledger, entry sources, season runner, exports.
- `source/reference/calendar_generator_v011.py`: original week-based calendar, course policy and format distributions.
- `source/reference/engine_v07.py`: home-country national open invitations as a special path.
- `source/reference/capacity_engine_v08.py`: capacity tour extensions.
- `source/reference/engine_v03.py`, other `engine_v*`: golfer model, long-term growth, hole scoring, group order, injuries, nation evolution.
- `source/reference/career_economics.py`: paid starts and cash economics.
- `source/rankings.py`: 104-week world points / 54-72-hole award restrictions and weekly ranking ledger; ability-proxy field strength.
- `source/history_store.py`: RAM staging SQLite and durable archive with compact holes.
- `source/audit_v013.py`: independent SQLite schema consistency and golf-result auditor.

**Architectural risk:** Deep inheritance of earlier engine classes makes the complete behavior harder to reason about. A reviewer should map method resolution and data state transitions before refactoring. Propose modular separation only after characterization tests stabilize current behavior.

## 2. Current actual persisted schema

Defined in `source/history_store.py` (`DDL` constant); not the planned ultimate schema.

| Table | Primary use | Important caveat |
|---|---|---|
| `events` | Edition ID, series, year/week, host course ID, holes, tour, purse, winner, cut/playoff details | No separate future course-layout-version/entrant-affiliation history yet |
| `entries` | Golfer-event participation, finish/place, cumulative strokes, number of holes actually completed, purse, entry reason | Entry lifecycles and rich priority metadata missing |
| `rounds` | Physical order 18-hole bytes, round score, pairing ID, start tee and time slot | `holes` BLOB contains exactly 18 integer bytes per round; no per-shot ball-flight |
| `exemptions` | Historical target series, golfer, source edition, source type, earned week and expiry | Only a subset of major qualification routes exist |
| `ranking_snapshots` | Compressed weekly `[[golfer_id, ranking_average],...]` pairs | Ranking formula is provisional; rankings not yet replay-calibrated to official method |
| `course_record_history` | Dated round course record changes tied to competitor/event | Future configuration-specific layouts needed |
| `hole_record_history` | Dated individual physical-hole record changes | Future hole layout/tee versions needed |

**Not currently fully archival in this store:** active golfer snapshots and complete lifelong attributes/career metadata, evolving staff contracts, player hype/prestige, course layout renovations, national infrastructure change provenance, financial/cash ledger and true membership-card histories. Some details are exported elsewhere in the older reference model, but the v0.13 `HistoryStore` should not be described as a complete lifetime immutable universe database yet.

## 3. Key invariants

- For each `rounds` row, `length(holes) == 18`, `sum(holes) == gross_strokes`.
- For each completed entrant, sum of `rounds` totals agrees with event entry strokes and actual 18/36/54/72-format / cut.
- Three-player or two-player groups, physical hole order and tee assignments are consistent with event round format.
- No golfer participates in two scored tournament fields in the same week.
- Exactly one event worldwide in weeks 14/19/24/30, and all four are majors.
- Every major entry resulting from a previous win/qualifier references an existing earlier source edition.
- Tournament payouts sum to configured pool; no unpaid entrant receives imaginary money.
- Course/hole record updates strictly improve the previous best (subject to layouts).
- Week ranking snapshot IDs unique and decompression/reopen succeeds.

The independent audit checks a subset of these; some scheduling invariants rely on engine/calendar tests instead of archived record-level enforcement. Improve cross-layer coverage before full-scale benchmarking.

## 4. Data model we ultimately want (NOT yet implemented)

Create stable, normalized IDs for `countries`, `regions`, `institutions`, `golfers`, `archetypes`, `personality/ceiling profiles`, `staff`, `relationships`, `golfer_course_familiarity`, `courses`, `course_layouts`, `course_holes`, `tours`, `tour_memberships`, `tournament_series`, `tournament_editions`, `eligibility_categories`, `entry_requests`, `entry_status_history`, `qualifying_provenance`, `tee_groups`, `rounds`, `hole_scores`, `playoffs`, `world_ranking_points`, `tour_standings`, `amateur_standings`, `country_development`, `economics_ledger`, `public_reputation/hype`, `sponsorships`, `milestone_events`, `career_status_history`, `course_record_events`, `staff_career_history`.

We need a versioned immutable **event edition** and always link qualification to its exact edition (`source_event_id`, `target_event_id`, `earned_at`, `status/expiry`). Staff “associated major” should join a dated golfer-staff contract against the actual major date rather than rely only on ever-coached flags.

### SQLite performance considerations

- Index on `(event_id,golfer_id)` for entries and rounds, `(golfer_id,year/week)` for career views, `(course/layout,year/week)` for record browses, `(series_id,year)` for series history, and `(country,year)` for nation growth.
- Keep hot active state in RAM; avoid per-hole database I/O. Write at **safe frequent checkpoints** (weekly/monthly) using batched transactions, and persist RNG/week/round state to recover interruptions without corruption.
- Current v0.13 uses in-memory staging and **season-end durable checkpoint only**. Thus full-size 200-year production durability and write-cost requirements remain unmet.
- Test archive volume after 200 years and query latency using realistic history, not just empty index pages. Assess splitting static source/historical large blobs into compact immutable separate tables if needed, but never destroy scorecards.

## 5. Scientific simulation testing rules

- Separate testing of **mechanical validity** (scorecard sums, pairings, money, eligibility) from **statistical realism** (career curve, number of 10-major golfers, dominant eras).
- Do not treat five seeded 30-year worlds as a reliable probability estimate for very rare event tails. Increase seeds when evaluating generational talent rarity. Use complete careers or account for censoring when prospect starts near run end.
- Compare old and new scoring under matched tournament fixture conditions (same golfers/courses/seeds where possible), then run distributional tests across multiple changed worlds without expecting identical careers.
- Keep scoring seed and tournament generation independent from exports/UI. Move toward per-event separate deterministic random streams before threaded concurrent simulation.
- The final player should be able to inspect any recorded win, major berth, course record, or career transition with consistent historical provenance.
