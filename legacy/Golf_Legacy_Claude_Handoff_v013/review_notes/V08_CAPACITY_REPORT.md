# Golf Legacy: Expanded-World Capacity Benchmark (v0.8 experiment)

**Purpose:** Test whether substantially more golfers and tournaments can be supported without changing hole-by-hole tournament scoring or the underlying v0.7 athlete, staff, finance, and national-open calculations. This is a **one-season capacity experiment**, not a validated multi-decade population model or a new official simulation version.

## Real measurements

| Metric | Frozen v0.7 full calendar | Expanded-calendar experiment |
|---|---:|---:|
| Starting golfers | 1,700 | 4,500 |
| Professional circuits | 18 | 33 |
| Completed tournaments | 191 | 341 |
| Competitive holes scored | 1,203,516 | 1,980,648 |
| Funded tournament starts | 20,133 | 31,733 |
| Full tournament fields | 191 / 191 | 341 / 341 |
| Canceled events | 0 | 0 |
| Recorded integrity errors | 0 | 0 |
| Prize/economics validation errors | 0 | 0 |
| Simulation time | 33.62 s | 122.98 s |
| Peak resident memory | 156.4 MB | 230.6 MB |

Both tests used world seed **1217** in the same execution environment. The original scoring, cut, pressure, tee grouping, economic-eligibility, national-open, and championship behavior were not intentionally changed. The expanded variant adds fifteen fictional regional/mini-tour circuits: one secondary regional and two local professional circuits for each of the five geographical regions. Each new circuit schedules ten events per year. All values for fees, salaries, purses and costs remain fictional scenario assumptions.

**Important:** These are not controlled same-world comparisons: adding golfers and tours changes event scheduling, fields, and random-number consumption. Numbers provide *capacity and timing evidence*, not evidence that career realism has improved.

## Calendar audit

- 341 tournaments spread across 48 weeks; as many as 17 simultaneous events.
- 28 national opens, all hosted in their named countries through the inherited v0.7 scheduling logic.
- Zero course/week double bookings.
- Tier 1 has tournaments in only **25** distinct weeks, Tier 2 in **29**, Tier 3 in **38**, and Tier 4 in **30**. Thus, the calendar is **not yet weekly at every level**.
- **Three same-tour/same-week collisions** appear between Premier Tour events and majors (weeks 21, 31, 41). They are not flagged by the existing validation; design proper major/open weeks and opposite-field exceptions explicitly rather than silently accepting them.

## Why the capacity result doesn't prove the long-run roster works

- Only **one year** was completed. Full tournament fields at year one do not show the same fields will be filled in year 15 or 60.
- v0.7 seeds the starting roster with several events' worth of *opening scenario bankroll*, improving early-season affordability. Long-run funding constraints may reduce entries.
- There is still no independent amateur, college, local-competitor, part-time-professional, or multi-national affiliation pipeline.
- Tour eligibility is simplified, and the national-open frequency needs full-calendar balancing.
- While 4,500 golfers were initially created, only **26 replacement entrants** were generated during the first season. Starting and yearly entrant population sizes are different; rare-prodigy incidence must be calibrated by birth/new-entrant cohort, not multiplied blindly by an enormous starting roster.
- The expanded benchmark generated **zero explicitly flagged rare prodigies**. That is not unusual at the current generation probability and a one-season observation window, but means no claim is possible about legendary careers.
- Working memory and save-history growth after 60–200 years have not been tested in this expanded configuration.

## Actual performance conclusion

The larger season took ~123 seconds to calculate almost 2 million holes. At the same average annual rate, 60 years would take **at least about 123 minutes** before file exports; 100 years **about 205 minutes**. These are flat-rate illustrations, **not forecasts**: roster dynamics, persistent records, new event schedules and database costs can shift runtime materially. Therefore, the detailed Python loop is not acceptable for satisfying the desired centuries-long interactive game at full scale.

## Recommended architecture and next tests

1. **Freeze reference behavior.** Add golden-seed tournament fixtures and invariant checks for chronological hole order, both starting tees, cut-line pressure, world-state and prize conservation, plus deterministic encounter outcomes wherever identical RNG streams are available.
2. **Optimize without simplifying golf.** Cache immutable course/hole/attribute terms before rounds; update only state-dependent form, pressure, fatigue and live-leaderboard terms. Improve field-selection indexes so weekly entry allocation is not a full linear scan of the golfer database for every event. Compare pure Python, compiled/JIT scoring, and native Rust against identical tests.
3. **Keep a local native engine + web-style UI.** Rust core and Tauri UI (after benchmark confirms benefits), SQLite-backed permanent history, in-memory active population, batched event transactions and periodic save/checkpointing. This does not require paid hosting or recurring subscriptions.
4. **Model population as a funnel.** Juvenile/college/national amateur circuits, pro qualifiers, mini-tours, part-time players, domestic invitation slots, retirements and returns. Allocate whole weeks simultaneously so a golfer cannot be booked into two courses, and leave real competition for tournament places.
5. **Use a test matrix:** ~4,500 golfers / 341 events (current proof of capacity); ~8,000 / 500–700 events; then 15,000–25,000 named active and part-time competitive golfers / 800–1,500 events if actual performance and economics support it. Do not force all amateurs/local golfers to play 20 events/year.
6. **Run full 60-year seeded worlds once throughput allows.** Examine full birth cohorts, age of first/last victory, tour-card survival, financial dropouts, occasional local-player late bloomers, major dominance, country development, and course-record longevity. Keep hole-by-hole scoring for each sanctioned tournament.

## Practical spending recommendation

**Spend $0 on infrastructure at first.** Use free local development tooling, SQLite and local saves. If performance remains inadequate **after measured optimization**, consider a one-time hardware upgrade informed by benchmarks on the actual Windows PC. No cloud-server subscription is required for a single-player personal game.

## Reproducing

Extract this package and run from its root:

```
python benchmark.py --population 1700 --events-scale 1 --years 1 --seed 1217 --output baseline_retest.json
python bench_expanded.py --population 4500 --extra 3 --years 1 --seed 1217 --out expanded_retest.json
python calendar_audit.py
```

`benchmark.py` invokes `_schedule()` once to inspect the calendar before running, consuming schedule RNG; the expanded benchmark derives its expected number of tournaments without that extra schedule call. Both runs are deterministic independently with their recorded method, but should not be used to compare matched per-golfer outcomes.

The original engine in `source/working/` is retained for reproducibility. The only simulation code newly created for this experiment is `capacity_engine_v08.py`, which appends feeder circuits.
