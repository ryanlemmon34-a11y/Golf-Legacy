# What decides who wins in Test2: Overall, archetypes, attributes and weather

Read-only study for Ryan's four questions. It is on its own branch (`research/attribute-winning-analysis`, from
released main `18a8e23`). **No balance, engine, growth, scoring, weather or generation change is made or
recommended here.** Parameter changes wait until this audit has been reviewed.

Plan: `PLAN.md`. Code map: `ATTRIBUTE_MAP.md`. All tables are in `results/`.

Scope of the evidence:

- **Intervals.** Every interval is a within-world stability measure: a bootstrap over this one world's golfers
  or editions, or the SE over simulation replicates. None is seed-to-seed uncertainty, and none is a
  calibration against real golf.
- **Cárdenas** is reported as an example and a sensitivity, never as the calibration.
- **Controlled experiments** use verified early-era events (2027). They are not all-era evidence and not
  Cárdenas-specific counterfactuals.

## 1. Data and provenance

**Save.** Test2: world `386509-1793467568`, generation 70 (2084 start), checkpoint sha256 `c55bbd2f…`, engine
`1949ff63…` = commit `c0d1ea5`, calendar v2. Only the JSON history is read, through the manifest's own file
list; the pickled checkpoint is never opened. File hashes are in `results/audit.json`.

**Editions.**

- 83,181 editions in all.
- **81,871 primary editions**: one site, stroke play, not qualifying, with a pre-event estimate stored by the
  engine. Every field reconciles exactly with all starters (made cut, missed cut, withdrawn) and has exactly one
  champion; the reconciliation failure count is 0.
- 1,139 qualifying editions and 171 match-play editions are excluded.
- 179 primary editions with a single entrant are excluded from the favourite and archetype tables.

**Pre-event Overall** is stored per entrant at 0.1 resolution (`upset.inputs`), computed in the worker from the
golfers that played, before any shot. Full pre-event attributes are not archived.

**Native archetypes** are not archived either. They are recovered by replaying each golfer's own generation
stream, and a label is kept only when all 21 creation attributes reproduce:

- 47,284 golfers are verified;
- Cárdenas is verified with clamping (10 attributes at 99, the other 11 exact; label: Power Hitter);
- 704 golfers, the unplayed 2084 class, are unknown;
- labels cover 100% of archived starts;
- no label is inferred from results.

**Exact replay.** The save's own engine (`c0d1ea5`, run here on Linux and Python 3.13; the save was written on
Windows and Python 3.15) replays its history. Every week is checked against the archive (the exact edition set,
every finish and every round's conditions), and every capture is bound to its archived finish. **Seasons
2027–20xx verified, 0 mismatches** (`results/capture_manifest.json`). The replay captures every starter's exact
pre-event state, and complete tasks for the selected events.

**Scoring code.** The scoring code (`engine.py`, `tournament.py`, `weather.py`, `ratings.py`, `golfer.py`,
`course.py`, `baseline.py`, `familiarity.py`, `upsets.py`) is identical in main `18a8e23` and `c0d1ea5`.
`play_site` is unchanged.

**Experiments** run on main and pass two no-op checks before any measurement:

- `play_site` on the captured task reproduces the archived edition exactly;
- the harness path with explicit conditions does too.

## 2. How often does the best Overall win?

"Best entrant" means the highest stored pre-event Overall. When the best are tied (2.1% of editions), the tie is
treated as a set and reported separately (`results/favourite.json`, `results/fav_*.csv`). The interval shown is
a golfer-clustered bootstrap.

| Editions | Unique best entrant wins | Top 3 | Top 10 | Misses the cut | Winner's Overall rank: 1 / ≤5 / median |
|---|---|---|---|---|---|
| All primary (79,936 with a unique best) | **12.1%** [11.7, 12.5] | 29.7% | 57.0% | 4.3% | 12.2% / 36.1% / 10 |
| Professional tiers 0–4 (38,843) | **10.3%** [9.9, 10.8] | 26.0% | 52.3% | 7.9% | 10.4% / 32.0% / 12 |
| Majors (224) | **21.0%** (47) | 46.4% | 71.4% | 4.9% | 20.6% / 50.0% / 5.5 |
| Premier (2,018) | **12.3%** [7.8, 16.2] | 28.4% | 52.0% | 11.4% | 12.3% / 32.2% / 14 |

**Majors are dominated by Cárdenas.**

- Only 9 golfers were ever the unique best entrant in a major, so the clustered interval (5–31%) means little.
- Cárdenas was the best entrant in 92 majors and won 34 of them (37%). He won 5 of the 72 other majors he
  started.
- His verified ledger: 164 major starts, 39 wins.
- Without him:
  - in the 132 majors where he was not (and did not tie for) the best entrant, the best entrant won **9.8%**;
  - in the 64 majors he did not enter, **14.8%**;
  - removing him changes the all-level rates by less than 0.2 points.

**What moves the rate** (professional tiers 0–4, unique best):

- **The gap to the second-best entrant:** 7.3% when the best is ahead by 0.1–0.9 Overall, then 8.6%, 10.4% and
  13.5%, rising to **22.3%** when ahead by 5 or more.
- **Field depth** (entrants within 2 Overall of the best): 14.5% when nobody is that close, then 10.1%, 7.4% and
  5.7%, falling to **4.0%** with 9 or more.
- **Field size** (all levels): 25.7% in fields of 30 or fewer, then 15.3%, 11.0% and 8.8%, down to **7.5%** in
  fields of 145 or more.
- **Rounds:** 4-round events give the lowest rate (10.3%). Bigger, deeper fields play 4 rounds.
- **Era:** flat across six decades (9.7–11.3%).
- **Origin:** initial seeded golfers 13.0%, juniors 12.3%, late entrants 10.9%.

**Volatility and depth.**

- **Tier-2 tours** stand out: the best entrant wins 6.6% and misses **16.3%** of cuts.
- They have the deepest fields: the smallest gap between first and second (1.77) and the most entrants within 2
  (3.5).
- Fatigue does not explain it. In the verified replay seasons 2027–2035, tired best entrants (fatigue above 0.2)
  miss 19% of cuts and rested ones 18%.
- Premier best entrants miss 11.4% of cuts.

**The stored win estimates.** The engine's estimates (`upset-model-1`, Overall only) are close to observed
frequencies but slightly over-confident above 15%:

| Estimated win chance | Observed |
|---|---|
| 0.172 | 0.155 |
| 0.239 | 0.218 |

They are a model approximation, not independent truth.

**Real golf, as context only.** No reliable long-run public rate exists for how often the betting favourite wins
a PGA Tour event; published samples suggest favourites win a minority of the time
([Action Network](https://www.actionnetwork.com/golf/2019-masters-betting-preview-analysis-golf-favorites-rory-mcilroy),
[Golf.com](https://golf.com/lifestyle/how-often-favorites-win-tournaments/)). An extreme peak is Tiger Woods in
2000, with 9 wins from 20 starts
([Golf Channel](https://www.golfchannel.com/news/tiger-woods-2000-season-results-stats-wins-highlights-majors-scoring-average-finishes)).
These are not calibration targets.

## 3. Which archetypes win most?

Native verified labels (`results/arch_*.csv`):

- **E_equal**: the wins expected if every entrant were equally likely (opportunity only).
- **E_ovr**: the wins expected from each starter's pre-event Overall within the field, from a conditional logit
  on the gap to the best (quadratic per round count, blind to archetype).
- **E_std**: a non-parametric cross-check by Overall rank, level and rounds.

O/E is an **association**, not a fully controlled causal comparison. The Overall model is pooled, over-predicts
the strongest favourites (`arch_clogit_calibration.csv`: 0.55 predicted against 0.47 observed in the top band),
and archetypes also differ in personality, development and access.

Archetypes are equally likely at creation (12.2–12.7% each), and their starts and Overall mix are nearly
identical (mean pre-event Overall 55.6–56.1 across all levels).

| Archetype (all levels, 7.79M starts) | Win share | Wins / 100 starts | Top 10 / 100 | Made cut / 100 (cut events) | O / E_equal | **O / E_ovr** [interval] | Top-10 O / E |
|---|---|---|---|---|---|---|---|
| Aggressive Shotmaker | 15.6% | 1.27 | 12.4 | 47.7 | 1.22 | **1.26** [1.24, 1.28] | 1.08 |
| Effortless Power | 13.7% | 1.10 | 12.0 | 48.9 | 1.05 | **1.05** [1.03, 1.06] | 1.02 |
| All-Rounder | 12.8% | 1.05 | 11.9 | 49.4 | 1.02 | **1.02** [1.00, 1.04] | 1.04 |
| Short-Game Artist | 11.5% | 1.00 | 11.4 | 49.2 | 0.96 | **0.99** [0.97, 1.02] | 1.00 |
| Elite Putter | 11.9% | 1.00 | 11.6 | 49.0 | 0.96 | **0.99** [0.97, 1.01] | 1.02 |
| Power Hitter | 13.2% | 1.13 | 12.0 | 47.9 | 1.06 | **0.97** [0.95, 0.99] | 0.97 |
| Precision Ball-Striker | 11.2% | 0.92 | 11.5 | **49.9** | 0.88 | **0.90** [0.88, 0.92] | 0.98 |
| Strategic Technician | 10.2% | 0.90 | 10.8 | 48.1 | 0.85 | **0.82** [0.81, 0.84] | 0.89 |

**Majors and Premier, without Cárdenas** (O / E_ovr):

| Archetype | O / E_ovr |
|---|---|
| Aggressive Shotmaker | 1.35 |
| Short-Game Artist | 1.12 |
| Elite Putter | 0.99 |
| All-Rounder | 0.97 |
| Effortless Power | 0.95 |
| Strategic Technician | 0.94 |
| Power Hitter | 0.90 |
| Precision Ball-Striker | **0.73** |

**Majors alone.** Raw major wins favour Power Hitters (29% of major wins), but that is Cárdenas. Adjusted for
Overall, Power Hitters are 0.9–1.2 with wide intervals. The major-only sample (228 editions) is too small to rank
archetypes.

**Stable splits.** The ordering holds:

- for initial seeded golfers and for later entrants;
- at ages 25–35;
- at every level from club pro to Premier.

**Interpretation, to be tested in section 4.** Aggressive Shotmakers win about a quarter more than their Overall
predicts, yet make the *fewest* cuts and gain much less in top-10s (1.08) than in wins (1.26). That is the
signature of **higher score variance** at an equal mean: more very low weeks and more bad ones. Precision
Ball-Strikers show the reverse: the most cuts made, fewer wins. Big fields reward variance at the top. The
controlled fixed-Overall profiles in section 4 test this directly.

## 4. Which attributes matter most and least? (experiments)

*Pending: tier 1 round scoring (grid running), tier 2 fixed-field conditional estimates, tier 3 full-event
validation, fixed-Overall archetype profiles and equal-SD perturbations.*

## 5. How much does weather change who wins?

### 5a. Recorded weather (descriptive, associations only)

All 228,604 recorded rounds carry seasonal conditions. Every course's metadata was verified against the save
(520 of 520). By course style:

| Style | Typical wind | Mean recorded wind (p90) | Wet-round rate |
|---|---|---|---|
| Links | 19 mph | 16.1 (23.8) | 20.8% |
| Coastal | 16 | 15.6 (23.3) | 15.0% |
| Parkland | 9.2 | 9.0 | 15.5% |
| Woodland | 7.1 | 6.8 | 15.9% |
| Desert | 11.5 | 11.5 | 3.6% |

Wetness follows the climate tables (`wx_coverage_climate_month.csv`).

Professional tiers 0–4, within-course associations (course fixed effects; covariates: field depth, field size,
rounds; cluster-robust by course):

| Outcome | Per 1 mph of mean wind | Per wet round |
|---|---|---|
| Field's average score per round | **+0.115** (±0.003) | **+0.28** (±0.01) |
| SD of finishers' totals | **+0.037** (±0.002) | **+0.089** (±0.012) |
| Best entrant wins (probability) | **+0.0005** (±0.0004) | −0.002 (±0.002) |
| log(winner's Overall rank) | −0.003 (±0.002) | +0.007 (±0.009) |

The "per wet round" column is the change in the event's average score per round for each wet round it had.

The descriptive picture is that wind and rain raise everyone's scores and spread the field, but hardly change
whether the best player wins. By wind band, the professional best-entrant win rate is 10.1% below 6 mph and
12.1% at 22 mph or more. These bands are confounded by course and field, and the within-course estimate is close
to zero.

### 5b. Matched counterfactuals

*Pending. The design is the same real fields, golfer states and courses with only the conditions changed: calm,
10, 20 and 28 mph, each dry and wet, in seasonal mode. There are 12 independent direction and gust scenarios,
paired shot seeds, and a re-randomised calm floor.*

## 6. Skill, depth, volatility (to be completed)

## 7. Limitations (to be completed)

## 8. Reproduce

```
SAVE=<Test2 save dir>; D=/dev/shm/aw/data; O=/dev/shm/aw/out
python extract.py $SAVE $D
python recover_archetypes.py $SAVE $D
python favourite.py $D $O
python archetypes.py $D $SAVE $O
python weather_desc.py $D $SAVE $O
python replay.py <c0d1ea5 checkout> $SAVE <work> --seasons N --capture <cap> --editions $D/editions.csv.gz
python exp_attrs.py rounds <cap> $SAVE <exp> --events 2027_BRITANNIA_OPEN,2027_USA_OPEN,2027_PT_FRANCE_OPEN,2027_CH_EUROPE_01 --ranks 1,10,40 --n 16000 --deltas 5,-5
```
