# G1.e: same-seed season with the familiarity baseline on and off

Two fresh full-population worlds, seed 4207, build c0d1ea5, decision evidence off, one season (2027) each, read-only from their archives: ON = `smoke/final_c0d1ea5/world_off` (the regional baseline and home-club floor on, the build default; "off" in that folder name refers to the decision evidence), OFF = `fam/out_c0d1ea5/world_famoff` (`Season.familiar_base_on = False` set before the season; fam/fam_off.py). Every outcome part differs between them (fam_off.json `parts_differing`: development, diagnostics, familiarity, fatigue_injuries, finances, history, moments, performance, published, rankings, records, results, rounds_and_holes, staff).

## 1. Where the two worlds diverge

| week | editions identical | same field, results differ | field differs | held in one world only |
|---|---|---|---|---|
| 1 | 3 | 10 | 0 | 0 |
| 2 | 3 | 8 | 6 | 0 |
| 3 | 1 | 3 | 13 | 0 |

The results first differ in week 1, the season's first week: every week-1 field is identical in the two worlds (fields are set from the same starting state), and 10 of the 13 week-1 editions have different scores (first by id: 2027:AM_ASIA_001). Everything from week 2 on is a different world (fields differ from week 2). The week-1 editions start from the same state with the same fields, so they allow a field-matched exploratory comparison (section 3) — not an isolated or causal measure of the baseline (see there why).

## 2. What the baseline did in the ON world

- Starts where the regional baseline (home-club floor included) set the familiarity value (season file `familiar_base`): 6799/124224 (5.5%) of all starts; golfers affected: 3,899.
- Starts at a golfer's home club found by country (the only case where the home-club floor can add anything; it applies there only while fewer than 3 rounds were played — an upper bound, the floor is not recorded per start): 10 starts by 6 golfers. Home-club familiarity source at the season end (people table): region 6363, played 754, home club 3.
- OFF world: `familiar_base` present (True) with 0 applications over 0 golfers — no baseline application recorded. Starts: 124,254 (ON 124,224).

## 3. Scoring

**Week 1: a field-matched exploratory comparison (not an isolated or causal effect).** Every golfer's familiarity at creation is recorded empty (generation-0 people table: 6409/6409 golfers), so before week 1 no rounds had been played anywhere and the baseline applied to a start exactly when it is positive for that golfer and course: reconstructed with the build's own `familiarity.baseline` and `home_floor` from the recorded birthplace, residence and home club (Season.course_baseline). Differences are ON − OFF for the same golfer in the same edition: round-1 score, round-1 score relative to the site's round-1 mean, and the mean over the rounds both worlds played of each round's score relative to that round's field mean. Why this is exploratory only: identical fields do not isolate the baseline's effect, because the engine's random stream is shared — once anything changes, every start's draws shift — so starts the baseline did not touch differ between the worlds too (the reference row), and subtracting that untreated reference row does not remove the contamination from the treated starts. Round 1 is the only round every starter played; the common-rounds and all-rounds comparison depends on who made the cut in each world, since rounds after the cut exist only for those who made it. 56 applied starts and 1382 not-applied starts. Check: 56/56 golfers with a reconstructed week-1 application are among the ON world's recorded `familiar_base` golfers.

Table: week-1 field-matched exploratory comparison, ON − OFF per start (negative = fewer strokes with the baseline on); mean (sd, naive se, n).

| starts (week 1) | n | round-1 strokes, ON − OFF (all starters) | round-1 vs field, ON − OFF (all starters) | common rounds vs field, ON − OFF (depends on the cut) |
|---|---|---|---|---|
| baseline applied (region) | 56 | -0.857 (sd 2.746, se 0.367, n=56) | -0.730 (sd 2.704, se 0.361, n=56) | -0.220 (sd 2.776, se 0.371, n=56) |
| baseline not applied (reference) | 1382 | -0.044 (sd 2.132, se 0.057, n=1382) | +0.030 (sd 2.129, se 0.057, n=1382) | +0.017 (sd 2.190, se 0.059, n=1382) |

The "se" values are naive sd/√starts: not clustered by event or field and not a calibrated causal uncertainty; no significance is claimed. The measured differences are reported as they are, with the caveats above; they do not show balance or prove an effect. One season, one seed.

**After week 1 (descriptive across diverged worlds; no per-golfer causal reading).** Mean over rounds of a start's score relative to its round's field mean, for starts at courses where the baseline would apply by place (positive baseline for that golfer and course) and for the others. In the ON world the baseline is used only while the golfer's own rounds there are fewer than it; this split is by place only, in both worlds.

| world | baseline-eligible starts: score vs field | other starts: score vs field |
|---|---|---|
| ON | +0.577 (sd 4.289, se 0.049, n=7769) | +0.312 (sd 3.766, se 0.011, n=115017) |
| OFF | +0.705 (sd 4.205, se 0.048, n=7817) | +0.304 (sd 3.764, se 0.011, n=114999) |

## 4. Season-level aggregates per world (descriptive)

| world | starts | scoring average, strokes per round (all rounds) | starts by golfers living in the venue's country | starts by golfers living in the venue's region | wins (first site) by golfers living in the venue's country |
|---|---|---|---|---|---|
| ON | 124,224 | 75.159 (308,342 rounds) | 72002/124224 (58.0%) | 106263/124224 (85.5%) | 814/1458 (55.8%) |
| OFF | 124,254 | 75.161 (308,298 rounds) | 72035/124254 (58.0%) | 106288/124254 (85.5%) | 831/1454 (57.2%) |

"Home" is the golfer's residence at week 0 (recorded `first_residence`; golfers move only at week 53) against the course library's country and region of the venue. Venues outside the library count as visitors.

## 5. Timing

Season time with the baseline off: 203.0 s; with it on (the final smoke's evidence-off world): 177.6 s. These are one pair of total run times on a shared machine; no overhead claim is made from them.

