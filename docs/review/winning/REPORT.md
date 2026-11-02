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
every finish and every round's conditions), and every capture is bound to its archived finish.

- **Seasons 2027–2037 verified: 16,058 editions with 0 mismatches**, 15,805 primary-edition captures bound to their finishes, and 163 exact full tasks (`results/capture_manifest.json`,
  `results/replay_log.jsonl`).
- The replay was stopped at the start of 2038 to free CPU for the experiments. It can be resumed (`--resume`).
- **Compact captures** hold every starter's pre-event state, **quantized**: attributes and traits to 0.1,
  fatigue and familiarity as float32. They are not exact full state.
- **Full task pickles** of the selected events are **exact** and are used in the experiments.

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
  - of the 136 majors where he was not (and did not tie for) the best entrant, 132 had a unique best entrant, who
    won 13 of them (**9.8%**);
  - of the 64 majors he did not enter, 61 had a unique best entrant, who won 9 of them (**14.8%**);
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

**A broad pattern, not an identical order.** At the extremes, Aggressive Shotmaker is above 1 and Strategic
Technician and Precision Ball-Striker are below it. That holds:

- for initial seeded golfers and for later entrants;
- at ages 25–35;
- at most levels from club pro to Premier.

The middle of the order is not identical at every level. At Premier, for example, Strategic Technician (0.976)
sits above Effortless Power (0.941), and the middle archetypes' intervals overlap widely
(`arch_level_*.csv`).

**Interpretation, to be tested in section 4.** Aggressive Shotmakers win about a quarter more than their Overall
predicts, yet make the *fewest* cuts and gain much less in top-10s (1.08) than in wins (1.26). That is the
signature of **higher score variance** at an equal mean: more very low weeks and more bad ones. Precision
Ball-Strikers show the reverse: the most cuts made, fewer wins. Big fields reward variance at the top. The
controlled fixed-Overall profiles in section 4 test this directly.

## 4. Which attributes matter most and least?

### 4a. Where each attribute acts (`ATTRIBUTE_MAP.md`)

**Every shot:**

- power, driving_accuracy;
- the iron and wedge multipliers;
- chipping, bunker;
- short and lag putting, green_reading;
- the error rates: striking_consistency and focus;
- decision noise: management.

**Variance** (as well as the mean):

- striking_consistency: day and week strike form, mishits;
- putting_consistency: putting form, lapses.

**Only in some situations:**

- composure: only under pressure;
- recovery_rate: only in rounds 2–4;
- ball_flight: mainly wind, firm greens and doglegs;
- recovery_play: trees and rough;
- big_stage (a trait): pressure.

**No shot effect:** injury_resistance acts only on availability.

**Overall weights are not winning contributions.**

### 4b. The actual history: attribute shape and winning (association)

Data: the verified replay seasons 2027–2036, about 1.26M starts with quantized pre-event attributes
(`attr_assoc.py`, `results/attr_assoc.json`).

Model: a within-edition win model fitted one attribute at a time, with the Overall gap to the field's best plus
that attribute's deviation from the golfer's own Overall. Odds ratios are per 10 points above the golfer's own
Overall. Professional tiers 0–4:

| Relatively strong in… | Win odds at the same Overall |
|---|---|
| ball_flight | **×1.16** |
| familiarity with the course (per 10 rounds above the field mean) | ×1.11 |
| power | ×1.11 |
| recovery_play | ×1.10 |
| aggression (per 10 trait points) | ×1.07 |
| short_putting, chipping, bunker | ×0.97–0.98 |
| driving_accuracy, green_reading, lag_putting, putting_consistency | ×0.93 |
| composure | ×0.91 |
| focus | ×0.89 |
| management | ×0.88 |
| striking_consistency | **×0.84** |

These are associations and they largely restate the archetype result. The "consistency and control" profile
(Strategic Technician, Precision Ball-Striker) wins less than its Overall predicts. The "shot-making and
variance" profile (Aggressive Shotmaker) wins more.

injury_resistance shows ×1.05 even though it has **no shot effect at all**. That is the clearest sign that these
associations mix in correlated traits and careers. Mechanisms come from the controlled experiments below.

### 4c. Direct scoring value of each attribute (controlled, tier 1)

Design (`exp_attrs.py rounds`; full tables in `results/experiments/SUMMARY.md` and `rounds_grid.json`):

- **Events.** Three verified 2027 events, using each event's real course and seasonal conditions (a new draw per
  sample):
  - Britannia Open: major, links, typical wind 19 mph;
  - France Open: Premier, sheltered woodland, 6 mph;
  - CH Europe 01: tier 2, woodland.
- **Subjects.** The Overall-rank 1, 10 and 40 golfers of each field, with their own captured caddie, familiarity
  and fatigue.
- **Rounds.** One production round per sample, 8,000 paired samples per arm.
- **Contexts:**
  - R1: round 1, no pressure;
  - R4: round 4, in-week fatigue;
  - R4P: round 4 under final-round contention pressure.
- **Arms.** One attribute ±5 points, nothing else changed. Clipped arms are excluded and listed: 19 of 189 +5
  cells, mostly the rank-1 subject's attributes already at 94–99.

**Zero checks hold exactly.**

- injury_resistance gives Δ = 0 in every sample of every cell.
- Moving long_irons within its flat 25–60 band gives identical rounds (pilot).
- composure and recovery_rate are exactly 0 where the code says they cannot act (no pressure; round 1).

**Δ strokes per round for +5 points**, mean over the unclipped subject-event cells (negative is better; ± is the
RMS paired SE). The −5 arms mirror these within about 0.03, so the response is close to linear in this range.
mid_irons and wedges gain a little more going up than they lose going down: +5 gives −0.15 and −0.09, −5 gives
+0.12 and +0.07.

| Attribute | R1 | R4 | R4 + contention | Britannia (links, wind) | France (sheltered) | CH Europe (tier 2) |
|---|---|---|---|---|---|---|
| driving_accuracy | **−0.18** ± .02 | −0.20 | −0.17 | −0.18 | −0.18 | −0.19 |
| mid_irons | **−0.15** ± .02 | −0.14 | −0.14 | −0.13 | **−0.19** | −0.13 |
| power | **−0.12** ± .03 | −0.14 | −0.12 | −0.07 | −0.12 | **−0.17** |
| chipping | −0.11 ± .01 | −0.11 | −0.11 | −0.12 | −0.10 | −0.11 |
| wedges | −0.09 ± .02 | −0.09 | −0.09 | −0.09 | −0.08 | −0.11 |
| ball_flight | −0.09 ± .02 | −0.10 | −0.08 | **−0.17** | **−0.03** | −0.07 |
| short_putting | −0.08 ± .01 | −0.08 | −0.08 | −0.09 | −0.08 | −0.08 |
| green_reading | −0.08 ± .01 | −0.08 | −0.07 | −0.07 | −0.07 | −0.08 |
| long_irons | −0.08 ± .02 | −0.08 | −0.09 | −0.07 | −0.06 | −0.09 |
| stamina | −0.05 ± .01 | −0.06 | −0.06 | −0.06 | −0.04 | −0.06 |
| recovery_play | −0.05 ± .01 | −0.05 | −0.05 | −0.05 | −0.04 | −0.06 |
| striking_consistency | −0.04 ± .02 | −0.05 | −0.05 | −0.04 | −0.02 | −0.06 |
| lag_putting | −0.04 ± .01 | −0.04 | −0.04 | −0.04 | −0.03 | −0.04 |
| bunker | −0.03 ± .01 | −0.04 | −0.03 | −0.05 | −0.03 | −0.03 |
| focus | −0.03 ± .01 | −0.04 | −0.05 | −0.04 | −0.03 | −0.03 |
| management | −0.03 ± .02 | −0.03 | −0.03 | −0.02 | −0.03 | −0.03 |
| resilience | −0.03 ± .01 | −0.03 | −0.03 | −0.03 | −0.02 | −0.04 |
| putting_consistency | −0.02 ± .01 | −0.02 | −0.03 | −0.02 | −0.01 | −0.02 |
| recovery_rate | **0** | −0.06 | −0.06 | 0 | 0 | 0 |
| composure | **0** | **0** | **−0.10** | 0 | 0 | 0 |
| injury_resistance | **0** | **0** | **0** | 0 | 0 | 0 |

**What this shows about direct scoring:**

- **Largest per point, in every context:** driving_accuracy and mid_irons. Power, chipping and wedges are next.
- **Context matters:**
  - ball_flight is **among the strongest** on the tested windy links, not uniquely the strongest. At Britannia,
    driving_accuracy is −0.175 and ball_flight −0.172, from different unclipped cells with overlapping
    uncertainty. On sheltered woodland ball_flight is nearly irrelevant (−0.03);
  - power is worth less on links (−0.07) than on the two woodland courses (−0.12 to −0.17);
  - composure is worth −0.10 per round under final-round contention pressure and nothing otherwise;
  - recovery_rate acts only from round 2.
- **Smallest per point:** putting_consistency, resilience, management, focus and bunker (−0.02 to −0.03), and
  lag_putting (−0.04).
- **injury_resistance** has no direct scoring value by construction. Its value is availability, which this design
  cannot see; that is not "worthless".
- **Variance.** +5 on one attribute barely changes a round's spread. The largest change, from
  striking_consistency, is 1.1% less spread, with slightly fewer exceptional low rounds. Small changes in round SD
  cannot rule out larger effects in the winning tail, so the variance explanation of the archetype pattern
  (section 3) stays **pending**: the fixed-Overall profiles (4d) and the winning experiments (4e) test it.
- **Rankings among neighbours are not robust.** The per-event, per-subject ranks of the middle attributes move by
  several places (`SUMMARY.md`, rank table). Only the broad tiers are stable: top, middle, small, situational,
  zero.

These are strokes per round from a single golfer's production rounds. They are not win probabilities; winning
impact is section 4e.

### 4d. Fixed-Overall archetype profiles

*Pending (queued): the subject's 21 attributes are replaced by each native archetype profile at exactly the same
Overall, with the archetype's aggression and big_stage and with those set neutral.*

### 4e. Winning impact (tier 2 fixed-field screening, tier 3 full-event validation)

**Tier 2: the subject replayed against fixed production fields** (`exp_fixed.py`; a conditional approximation).

- **Design:**
  - 500 production replays of the whole event;
  - in each, the subject's own week is replayed 16 times with the production round code and `play_event`'s
    pressure and cut rules;
  - rivals' scores are frozen, so their pressure and cut responses to the subject are not modelled;
  - playoffs count as an equal share.
- **Events.** Britannia Open (links) and France Open (sheltered woodland).
- **Subjects.** The favourite (golfer 1, Overall 88.3, native Strategic Technician) and the rank-10 golfer.
- **Readout.** Δ win in percentage points per +5 (SE over field replicates), for the favourite. Clipped arms are
  excluded.

| Attribute (+5) | Britannia (base win 8.8%) | France (base win 9.8%) |
|---|---|---|
| driving_accuracy | +1.09 ± .30 | **+2.07** ± .32 |
| mid_irons | **+1.36** ± .34 | +1.21 ± .36 |
| wedges | +1.04 ± .29 | +0.96 ± .27 |
| short_putting | +0.98 ± .18 | +0.96 ± .17 |
| power | +0.95 ± .30 | +0.60 ± .35 |
| long_irons | +0.93 ± .29 | +0.58 ± .26 |
| ball_flight | +1.07 ± .32 | **+0.08** ± .20 |
| stamina | +0.33 ± .17 | +0.48 ± .18 |
| bunker, lag_putting, resilience, recovery_play, recovery_rate | +0.0 to +0.45 | +0.2 to +0.4 |
| putting_consistency | +0.11 ± .10 | +0.30 ± .09 |
| **striking_consistency** | **−0.02** ± .23 | **−0.04** ± .23 |
| injury_resistance | 0 (exact) | 0 (exact) |

For the rank-10 subject (base win 3.3% and 2.3%), the gains are smaller, and **striking_consistency +5 lowers the
win rate** (Britannia −0.17 ± .14; France −0.26 ± .13) while raising cuts (+0.25–0.5 points) and top-10s
(+0.3–0.5 points). That is the variance mechanism at attribute level: steadier play buys cuts, not wins.

**Tier 3: full production events, paired seeds**, 1,500 per arm, Britannia
(`results/experiments/events_validation_*.json`).

- **Baselines.**
  - Favourite: 9.0% in full events against 8.8% fixed-field.
  - Rank-10: 4.0% against 3.3% (fixed-field about 1.4 SE low).
- **Treatment effects, full against fixed-field, in points:**

  | Arm | Full | Fixed-field | Difference |
  |---|---|---|---|
  | Power +5, favourite | +0.8 ± 0.85 | +0.95 | agrees |
  | Short putting +5, favourite | +1.3 ± 0.44 | +1.0 | agrees |
  | Strategic Technician profile, rank 10 | −1.5 ± 0.65 | −1.8 | agrees |
  | Driving accuracy +5, favourite | **+2.8 ± 0.84** | +1.1 | 1.9 SE (full larger) |
  | Putting consistency +5, favourite | **−0.4 ± 0.25** | +0.1 | 1.9 SE (opposite sign; both small) |
  | Aggressive Shotmaker profile, rank 10 | −0.9 ± 0.7 | +0.2 | 1.5 SE |
  | Power +5, rank 10 | −0.1 ± 0.6 | +0.5 | 0.8 SE |

- **Overall.** Across these seven comparisons χ² ≈ 11.1 on 7 df (approximate p ≈ 0.13), so there is no
  systematic contradiction. But full events (SE 0.6–0.85 points) cannot confirm the fixed-field fine rankings,
  and two comparisons differ by about 1.9 SE.
- **Stream divergence in full events.** A +5 change alters 3–46% of rivals' totals, and an archetype profile 58%,
  through the shared stream.
- **Clipping as a no-op check.** short_putting +5 at rank 10 was clipped at 99, so the arm reproduced the
  baseline exactly.

**What is supported, and what is only screening:**

- **Supported (tier 2 in both events; tier 3 where tested at Britannia):**
  - the shot-making attributes give the largest win gains for a favourite, about +1 to +3 points of win
    probability per +5 at a 9% baseline: driving_accuracy, mid_irons, wedges, short_putting, power and
    long_irons. Full events tested driving_accuracy, power and short_putting, all positive;
  - ball_flight's win value is course-dependent (links, not sheltered woodland);
  - injury_resistance is zero;
  - **striking_consistency does not raise win chances in any tested cell** (every estimate ≤ 0), even though it
    lowers average scores slightly.
- **Small and inconsistent:** putting_consistency's win effect is +0.1 to +0.3 fixed-field but −0.4 ± 0.25 in
  full events.
- **Screening only:** the order within the top group, and every small difference among the middle attributes.

### 4f. Equal-SD perturbations

*Pending (queued).*

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

Professional tiers 0–4, within-course associations:

- course fixed effects;
- covariates: field depth, field size, rounds, year (era), the field's mean Overall and its top-10 mean Overall;
- cluster-robust by course;
- non-causal.

| Outcome | Per 1 mph of mean wind | Per wet round |
|---|---|---|
| **Cut survivors'** average score per round | **+0.114** (±0.003) | **+0.27** (±0.01) |
| SD of **cut survivors'** totals | **+0.037** (±0.002) | **+0.085** (±0.011) |
| Best entrant wins (probability) | +0.0006 (±0.0004) | −0.002 (±0.002) |
| log(winner's Overall rank) | −0.003 (±0.002) | +0.008 (±0.009) |

**Survivor-only measures.** The scoring rows use only the golfers who finished (made the cut). Who survives can
itself depend on the weather, so these are not whole-field effects. The controlled all-starter rounds 1–2
comparison is in 5b. The "per wet round" column is the change in the event's average for each wet round it had.

The descriptive picture is that windier and wetter events score higher and more spread among survivors. The best
entrant's win rate shows no detectable within-course association with wind (+0.06 ± 0.04 points per mph). This
is an association, not a causal estimate. By wind band, the professional best-entrant win rate is 10.1% below
6 mph and 12.1% at 22 mph or more. These bands are confounded by course and field, and the within-course
estimate is close to zero.

### 5b. Matched counterfactuals (controlled; `exp_weather.py`, `results/experiments/weather_cf*.{json,csv}`)

**Design.**

- **Events.** Four verified 2027 events:
  - Britannia Open and Scotland Open (links);
  - France Open (sheltered woodland, Premier);
  - CH Europe 01 (woodland, tier 2).
- **Held fixed:** the field, every golfer's captured state and the course.
- **Varied:** only the shared round conditions. All arms stay in the seasonal model; the classic default is
  never used. Arms:
  - calm (0 mph);
  - 10, 20 and 28 mph;
  - each dry and wet;
  - plus a second calm arm with independent shot seeds, which serves as the noise floor.
- **Scenarios.** Wind direction and gustiness come from 12 independently drawn seasonal scenarios per event.
  Each scenario × arm is played with 30 paired shot seeds; intervals bootstrap over scenarios.
- **These are repeated production comparisons, not "identical luck with only the weather changed".**
  - Same-seed arms do share each golfer's week form and the round-1 pin sheet, which are drawn before any shot.
  - After that, a weather change alters which draws are consumed, so later shots and the later rounds' pins
    differ.
  - Gusts are seeded by the conditions.

**Common penalty and spread.** All starters, rounds 1–2, so nobody is selected out. Δ strokes per round against
calm, [scenario interval]:

| Event | 10 mph | 20 mph | 28 mph | Calm, wet | 28 mph, wet | 36-hole SD, calm → 28 mph |
|---|---|---|---|---|---|---|
| Britannia Open (links) | +1.52 [1.40, 1.64] | +3.09 | **+4.43** | +0.34 | +5.06 | 5.94 → **7.82** (+32%) |
| Scotland Open (links) | +1.54 | +3.09 | **+4.44** | +0.41 | +5.06 | 5.47 → 6.96 (+27%) |
| France Open (sheltered woodland) | +0.48 | +0.94 | +1.33 | +0.66 | +1.99 | 5.57 → 5.87 (+5%) |
| CH Europe 01 (woodland) | +0.62 | +1.27 | +1.78 | +0.75 | +2.58 | 5.51 → 5.77 (+5%) |

**Field-average penalty.** On the links the field-average penalty is about 2.5–3.3 times the woodland one (for
example +4.43 against +1.33 and +1.78 strokes per round at 28 mph). That is a field average, not every golfer's
penalty. On the links the field's 36-hole spread also widens, which reflects golfers being affected differently;
it does not by itself mean more randomness for any individual golfer.

**Who wins: no consistent response resolved.**

- **The best entrant's win rate shows no consistent direction across the four fields.** At the Britannia Open,
  the two calm control arms (identical conditions, independent seeds) give 21/360 (5.8%) and 43/360 (11.9%);
  the weather arms give 8.6–10.8%. The other fields: France 8.1–11.9%, CH Europe 2.5–4.4%, Scotland 5.8–10.3%.
- **360 runs per arm cannot show that the favourite's or any individual's win probability "hardly changes".** The
  two calm controls are themselves noisy and their range is not a formal uncertainty band. No paired Δ-win
  interval or equivalence bound was computed. Modest changes in win probabilities therefore **remain
  uncertain**, neither shown nor excluded.
- **The median winner's Overall rank** is slightly better in wind (Britannia 14 → 12; Scotland 13 → 11–12;
  France 19 → 13–16). This is suggestive only, with no interval.
- **The win-distribution distance from calm** sits near the calm-versus-calm reroll value (0.27–0.35) for most
  arms and a little above it for strong wind on the Scotland Open links (0.35–0.38 against 0.27). The reroll
  value is a reference point, not a proven significance threshold.
- **Same winner as calm, seed for seed:** 4–9% in weather arms against 1–2% for independent calm reruns. The
  extra comes from the shared week form and first-round pins. Winner turnover in single replays cannot by itself
  establish how winning probabilities shift.

**Who gains relative to calm.** This is the correlation, across the real field, between an attribute and the
change in finishing percentile (negative means the attribute helps):

- **Links, 20–28 mph:**
  - ball_flight −0.81 to −0.90;
  - long_irons −0.38 to −0.45;
  - Overall −0.35 to −0.46: better players gain.
- **Sheltered woodland, 20–28 mph:** ball_flight −0.5 to −0.6.
- **Wet but calm:** little relative change, with no consistent attribute.

These correlations are confounded by how attributes cluster in real profiles. injury_resistance, which has **no
shot effect at all**, shows −0.31 to −0.38 at Britannia in strong wind. Only ball_flight's role is also a
documented mechanism (`ATTRIBUTE_MAP.md`; section 4c: +5 ball_flight is worth −0.17 strokes per round on links
against −0.03 on sheltered woodland).

**Answer to "how much did weather impact who won?", as far as this evidence goes:**

- **Scoring effects are clear.** Wind and rain raise scores for the whole field, with a field-average penalty
  about 2.5–3.3 times larger on exposed links than on sheltered woodland, and widen the field's spread on links.
- **The field is reordered towards ball-flight-strong golfers in links wind**, per the attribute correlations
  and the tier-1 mechanism.
- **No consistent favourite-win response was resolved** across the four fields. Modest changes in win
  probabilities remain uncertain at this sample size.
- No counterfactual is claimed for any specific historic edition beyond these verified 2027 events.

## 6. Skill, depth, volatility

### Day-to-day volatility (`volatility.py`, `results/volatility.json`)

Majors and Premier editions. The residual is a golfer's round minus that round's field mean (everyone who played
it). Three definitions, each a median over golfer-seasons, kept separate because they measure different things:

| Definition | Golfer-seasons | Median SD | Overall 80–85 | 85–90 | 90+ |
|---|---|---|---|---|---|
| A. Rounds 1–4, about the golfer's season mean | 16,897 | 3.48 | 3.33 | 3.21 | 3.20 |
| B. Rounds 1–4, about the golfer's own mean in each event | 16,897 | 3.39 | 3.22 | 3.10 | 2.98 |
| C. Rounds 1–2 only (every starter), about the event mean | 16,203 | 3.28 | 3.12 | 3.02 | 2.82 |

Definition A keeps week-to-week form and course fit inside the spread. B and C remove each golfer's event mean,
which also strips out shared event-level form and course fit, so they are not pure round-to-round noise either.

**The real-golf figure is a different measurement.** Data Golf publishes residual SDs (actual minus a model's
predicted strokes gained) of 2.72 for the best PGA Tour players, 2.75 for the middle and up to 3.23 for the
weakest ([Data Golf, 2026-02-18](https://datagolf.com/model-talk/2026-offseason-tweaks)). Their prediction
adjusts ability, time and course in its own way, and this world's Overall bands do not map onto their skill
groups. **No calibrated ratio between the two is claimed.**

The within-world pattern is clear: higher-Overall golfers are steadier in all three definitions.

## 7. Limitations

**Archive (one world, seed 386509)**

- Every interval describes stability within this world. A different seed, calendar or population could differ.
  No seed-to-seed variation was measured.
- Pre-event Overall is exact to the stored 0.1. Full pre-event attributes come only from the replay's compact
  capture for verified seasons (2027–2037), quantized to 0.1, plus exact full tasks for 163 selected events. No
  end-of-season or current rating is ever used as a pre-event value.
- The archetype and attribute "O/E" and odds ratios are associations. Archetypes also differ in personality,
  development, scheduling and access, and the Overall-only win model is pooled and slightly over-confident for
  strong favourites.
- Cárdenas dominates the major sample (92 of 224 majors as the best entrant). Major-only rates and rankings are
  imprecise; the clustered intervals over 9 golfers are not reliable.
- The weather associations are non-causal. Conditions follow course, climate and season. Within-course
  regressions with era, field-strength and depth covariates reduce, but do not remove, confounding. The
  finishers' scoring statistics are cut survivors.
- The volatility comparison with Data Golf is rough: their metric is a model residual, and this world's Overall
  bands do not map onto their skill groups.

**Controlled experiments**

- Early-era events only (2027: three events for the attribute grid, four for weather). They are not all-era
  evidence and not counterfactuals for Cárdenas or any later historic event.
- **Shared random stream.** One shot stream per site serves the whole field, and draws are conditional, so any
  change shifts later draws for everyone. Paired seeds are matched designs, not identical paths. The share of
  rivals whose totals changed is reported.
- **Gusts** are seeded by the conditions and the golfer, not by the shot seed. Replicates within one weather
  scenario share their gusts, so weather intervals bootstrap over scenarios.
- **Same-seed weather contrasts are repeated production comparisons, not "identical luck with only the weather
  changed".** A different wind or wetness changes which draws are consumed, so every later shot, and even later
  rounds' pin sheets (drawn from the same stream), follow a different path.
- **Fixed-field (tier 2) estimates** freeze rivals' scores, including their pressure and cut responses to the
  subject, and treat playoffs as an equal share. They are conditional approximations. **Their rankings are
  screening only** unless full production events (tier 3) support the treatment effects as well as the baseline
  rates.
- **+5 points** is a fixed step on a nonlinear, partly flat rating scale. −5, the equal-SD arms and several
  subjects show the dependence on level. Clipped arms are excluded and listed.
- **Indirect pathways** (development, availability, injuries, access, career decisions) are not in the fixed-field
  experiments. injury_resistance's value lies there.
- Morning and afternoon (tee-wave) weather is out of scope.

**Nothing here recommends a parameter change.** The findings are for review first.

## 8. Reproduce

```
SAVE=<Test2 save dir>; D=/dev/shm/aw/data; O=/dev/shm/aw/out
python extract.py $SAVE $D
python recover_archetypes.py $SAVE $D
python favourite.py $D $O
python archetypes.py $D $SAVE $O
python weather_desc.py $D $SAVE $O
python replay.py <c0d1ea5 checkout> $SAVE <work> --seasons N --capture <cap> --editions $D/editions.csv.gz
python volatility.py $SAVE $D $O
python attr_assoc.py <cap> $D $O
./run_experiments.sh $SAVE <cap> <exp> rounds weather fixed validate archetypes sd
#   rounds: exp_attrs.py rounds, events 2027_BRITANNIA_OPEN,2027_PT_FRANCE_OPEN,2027_CH_EUROPE_01,
#           ranks 1,10,40, n 8000, deltas 5,-5 (exact configurations of every step: run_experiments.sh)
python summarise.py <exp> <exp>/SUMMARY.md
```
