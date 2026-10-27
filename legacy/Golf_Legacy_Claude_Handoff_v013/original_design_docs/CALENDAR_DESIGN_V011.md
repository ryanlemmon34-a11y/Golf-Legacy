# Golf Legacy — v0.11 Calendar & Tournament Format Rules

**Status: Calendar generator and automated audits implemented. Hole-by-hole world-scoring engine NOT YET adapted to variable event length. No new 60-year golf history simulation has been run.**

**Supersedes:** v0.9 calendar preview for calendar planning; incorporates v0.10 cascading-priority and fixed-week qualifying philosophy. Does **not** supersede the v0.7 detailed hole-by-hole scoring model or overwrite the v0.8 capacity experiment.

## What changed

The calendar assigns an explicit, persistent **18-, 36-, 54-, or 72-hole format** to every competition. Each event edition stores `holes`, `rounds`, `round_days`, `cut_after_holes`, `cut_top_n`, `prestige`, `purse_usd`, `entry_priority`, and qualification/advancement fields. The same named event series keeps its length, prestige and purse in subsequent years unless a future explicit historical rule changes it. Venues and non-anchored week numbers may rotate.

Events remain distinct from tour prestige: a premier tour's short event can be much more prestigious and better paid than a mini-tour's long tournament, while **within the same tour and event class**, longer events are more prestigious and offer more money. National opens receive a historic championship bonus. Amateur and qualifying competition has $0 prize money in the fixture model regardless of length; this respects non-professional entries rather than pretending length always implies monetary winnings.

## Suggested length frequencies by tour tier

| Event category | 18h | 36h | 54h | 72h |
|---|---:|---:|---:|---:|
| Four global majors | 0% | 0% | 0% | 100% |
| Premier | 0% | 0% | 15% | 85% |
| Challenger | 0% | 10% | 60% | 30% |
| Regional | 15% | 45% | 35% | 5% |
| Mini-tour | 45% | 40% | 15% | 0% |

The percentages are initial **fictional game-balance distributions** rather than real-world population estimates. A National Open is upgraded to 54h or 72h regardless of its host circuit's ordinary mix. Four high-prestige National Opens are fixed at 72h and provide direct major qualification. Every week-13/18/23/29 final qualifier also has an explicit length. Qualifiers are *additional* scheduled fixtures and not yet played by the v0.7 engine.

### How the cut works

- **18 holes:** Saturday, one round, no cut.
- **36 holes:** Saturday/Sunday, two rounds, no cut by default.
- **54 holes:** Friday/Saturday/Sunday. Challenger regular events and national opens cut after 36 holes; other 54-hole events are generally no-cut. `cut_top_n` includes ties when the scoring engine implements it.
- **72 holes:** Thursday–Sunday, four rounds. Most pro and all four major events cut after 36 holes; 72-hole entry-level exceptions can be no-cut.
- **Ties for first:** future engine must run the applicable playoff rules for *all* lengths. Do not truncate the event or generate a winner from a precomputed total.

### Prestige and purse model

The fixture generator uses initial **tunable fictional** economy constants:

| Tier | Base prestige | Base purse (54-hole equivalent) |
|---|---:|---:|
| Premier | 82 | $3,000,000 |
| Challenger | 61 | $750,000 |
| Regional | 42 | $140,000 |
| Mini-tour | 23 | $30,000 |

Within a tier, a regular event has a format prestige adjustment of -6 / 0 / +5 / +10 (18/36/54/72 holes). Purse multipliers are 0.45 / 0.70 / 1.00 / 1.35. A National Open adds +8 prestige and a 1.4 purse multiplier. All major fixtures are prestige 100, 72 holes and have a proposed $17,000,000 purse. Qualifying events offer no purse. Prestige and prize pool are separate from the golfers' **personal** prestige/hype, which is a future feature.

**Interpretation:** Longer tournaments generally mean more prestige, larger prize funds and stronger advancement pathways, but event stature and tour level still matter. A 36-hole American Open final qualifier is a deliberate exception: its finishers can earn major entry because its formal purpose is qualification, not because 36 holes are inherently more valuable than 72.

### Qualification and advancement

- **Direct to major** (`qualification_target=MAJOR_N`): An outcome in a specified qualifying or historic event gives an earned entry opportunity, subject to eligibility, duplicates, exemptions and target field-lock deadlines.
- **Staged qualifying** (`qualification_target=QUAL_*`): 18-hole local qualifying can feed 36-hole regional qualifying, which can feed final qualifying, which then feeds the major.
- **Higher-tier eligibility** (`advancement_path=TIER_*_QUALIFYING`): Selected 54- and 72-hole ordinary tournaments and national opens offer their winner eligibility for a future higher-tier qualifying route. This is *not* automatic promotion or a tour card.
- Most ordinary 18- and 36-hole events award points/reputation locally, not direct elite invitations. Longer events are more likely to convey a qualifying opportunity; historic qualifier exceptions are explicitly named.

These links are **calendar metadata only** at v0.11. The actual entry allocator/qualification award logic remains to be integrated and validated in a scoring-world engine revision. The list of modeled major feeders does not yet cover the complete college and global amateur pathway envisioned for the full game.

## Locked championship weeks and static feeder series

| Week | Event | Holes | Qualification consequence |
|---:|---|---:|---|
| 13 | Legends Masters Final Invitational Qualifier | 54 | Winner qualifies for Week 14 |
| **14** | **Legends of Golf Masters Event** | **72** | Only competition worldwide |
| 18 | Premier Professional Qualification Championship | 72 | Top eligible club professionals qualify for Week 19 |
| **19** | **Premier Tour Championship** | **72** | Only competition worldwide |
| 21 | Scotland National Open | 72 | Winner qualifies for Week 30 |
| 22 | Kenya National Open | 72 | Winner qualifies for Week 30 |
| 23 | American Open Final Qualifying | 36 | Top eligible finishers qualify for Week 24 |
| **24** | **American Open** | **72** | Only competition worldwide |
| 25 | Japan National Open | 72 | Winner qualifies for Week 30 |
| 27 | Australia National Open | 72 | Winner qualifies for Week 30 |
| 29 | Brittania Open Final Qualifying | 36 | Top eligible finishers qualify for Week 30 |
| **30** | **Brittania Open** | **72** | Only competition worldwide |

Additional amateur and regional qualifying is scheduled in other weeks. The four major weeks remain **globally exclusive**: no simultaneous tour/mini/college/amateur/qualifying events. All higher-priority events are assigned first, then national opens, then other tour events. Any other schedule conflict must be resolved before field lock, with weekly AI scheduling planned in v0.10.

## Event-series identity and historical records

Every event has stable `series_id` and annual `event_id=YEAR:SERIES_ID`. All five 60-year calendar batches passed checks ensuring format, purse and prestige do not drift between editions of the same event series. National opens retain the same host tour even when course/date rotate. Majors keep their fixed week and their established course policy (Masters venue fixed, others rotated). For true historical realism, course layouts should be versioned and their records stored against the layout that was played.

## 2027 generated fixture example

- 33 professional circuits, 337 professional tour events plus four majors = 341 pro/major event editions.
- 28 National Opens **within** those 337 ordinary tour slots, not on top of them.
- 17 separate qualifying fixtures, giving **358 scheduled competitions**.
- 88 18-hole, 108 36-hole, 100 54-hole, and 62 72-hole fixtures.
- Theoretical field-entry hole capacity falls from 2,229,408 if every ordinary event was 72 holes to 1,415,538 with realistic formats, about **36.6% fewer maximum scheduled entrant holes**. This is *not* a measured CPU benchmark and does not incorporate actual field entry, cuts, weather, cancellations or playoffs.

## Validation evidence

`test_calendar_v011.py` generated **300 season calendars**: 60 seasons with five independent random seeds (42, 1217, 2601, 202, 404). Tests passed for:

- week-14/19/24/30 exclusivity;
- fixed dates for historic qualifying/national-open anchor series;
- existing tour event totals, no duplicate tour/week or course/week;
- correct format / round count / cut restrictions;
- stable event-series length, purse and prestige across six decades;
- nonnegative, zero-prize qualifiers and paid professional championships;
- strictly increasing prestige and purses for longer regular tournaments *within a tier*;
- real chronological ordering of qualifying stages ahead of their targets;
- all four majors remaining 72 holes.

The test does **not** prove that 60 years of golf results or tour membership behavior are realistic. Those require a future full-world simulation with the revised scoring engine.

## Before the next historical simulation — required engine integration

1. Migrate the tournament engine from an assumed four-round format to `event.rounds` (1–4), preserving day/tee-time and hole-by-hole order.
2. Implement per-event 18/36/54/72 scoring, with `cut_after_holes` and `cut_top_n`, including ties. Correct pairing formats must be chosen for each round and field, including single-round no-cut local events.
3. Wire `purse_usd` to event-level payouts and ledger reconciliation instead of silently applying host-tour generic purses. Qualifiers have no prize purse and may have entry/travel costs.
4. Wire the schedule to the weekly global entry allocator; honor `entry_priority`, formal exemption sources, qualifiers, lock times and post-win rescheduling.
5. Save every sanctioned scorecard with the **actual** number of rounds and layout version, and differentiate 18/36/54/72-hole championship and course records.
6. Rerun gameplay audits for each format, cuts, top finishers, playoff resolution, course records, qualifiers and money; only then repeat the 60-year worlds.

**Do not substitute fake round scores, discard detail, or simplify the golf engine to get speed.** Shorter events are simulated thoroughly; there are just genuinely fewer rounds to play.
