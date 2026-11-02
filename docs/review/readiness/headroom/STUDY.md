# Headroom study: evidence for review (experiment only)

**Status.**
- Approved experiment: Ryan, 2026-11-02 00:49 UTC. The approval covers testing and reporting only.
- Branch `build/v17-headroom-study`. The plan was published before any run (PLAN.md, 7058c05).
- No game code changed: `golfsim/`, `tools/` and `tests/` are identical to main 18a8e23.
- No balance change chosen, nothing released or merged.
- Evidence baseline: the reviewed readiness study, 5c7dce9.

**Run and provenance.**
- Run `66ec74cd4272f01c` from commit 37c1329 (`results/RESULTS.md`, `results/results.json`).
- The runner was gated on a passing fail-closed validation (`results/VALIDATION.md`):
  - the reviewed F1–F6 baseline checks;
  - plus F7, the mechanism scope: 14,939,472 candidate-arm pairs over all 114 cohorts, 2,931,473 of them touched
    below the knee, no violations.
- 11 unit tests (`test_headroom.py`); the self-test (`results/SELFTEST.md`) covers N1–N6, T1 and R1–R6.

## 1. What was tested

**The mechanism.**
- Only the tempo used in the youth deficit changes: a smooth (C¹), monotone transform of the unchanged peak-age draw.
- Identity at or above a knee K; slope s below K − w; a quadratic blend in between.
- Decline still uses the unchanged draw, so precocity keeps its order and its tie to decline.
- The same tempo serves new professionals at the age-18 tracking check and at entry.
- Scouting and status decisions see only observable ability.

**Isolation.**
- Every candidate keeps its latent potential, luck, aging, coins, attribute and personality draws and RNG keys.
- B1, B2 and B2c also keep each candidate's A0 stored-potential target.

| arm | knee, blend, slope | candidates touched | cap order | stored potential |
|---|---|---|---|---|
| A0 / A1 | none | 0 | raw first / cap first | production rule |
| B1 mild | 24.5, 2, 0.5 | 10.6% | raw first | A0 target |
| B2 stronger | 25.5, 2, 0.3 | 22.7% | raw first | A0 target |
| B2c | as B2 | 22.7% | cap first | A0 target |
| B2p | as B2 | 22.7% | raw first | production rule (promotion effect) |

The parameters are test points, not approved tunings.

## 2. Evidence layers and limits (as in the reviewed study)

- **Candidate level (paired layer).** 574,731 junior candidates per seed, five seeds. Results before and after the
  scouts' filter.
- **Selected entrants.**
  - Recalculated selection: paired layer.
  - Test2's fixed recorded allocation: replay layer, seed 386509, first k passers. It cannot show whole-pipeline or
    national-share effects. The existing rule's pass counts are recalculated separately.
- **Fixed-candidate trajectories.**
  - Key-matched common entrants, under unchanged growth and decline laws, on a controlled schedule: 13 blocks of one
    four-round tournament, two training weeks and one rest week a year.
  - Self-coached, with no injuries, money or access limits, quitting or retirement.
  - These are not realized careers and not strict bounds.
  - Years at 85+/90+ are absolute-ability exposure, not ranking or dominance.
  - No universal real-world overall target is set.

## 3. Findings

**H1. Near-finished high-potential entrants: B2 makes them rarer; B1 barely touches them.** Paired layer, five
seeds; selected juniors with stored potential 80+:

| measure | A0 | B1 | B2 |
|---|---|---|---|
| entrants with headroom ≤ 3 (count, five seeds) | 7 | 6 | 2 |
| share ≤ 3 | 1.2% | 1.0% | 0.3% |
| share ≤ 5 | 6.4% | 6.3% | 5.4% |
| 10th-percentile headroom | 5.65 | 5.67 | 6.07 |
| median headroom | 11.12 | 11.12 | 11.12 |

- The case was already rare under A0: 7 such entrants in 285 cohorts, about 1.4 per 57 seasons.
- Of A0's 7, 4 come from an early peak-age draw and 3 from large positive career luck without one. Production stores
  such luck as potential: stored potential is max(capped raw potential, entry overall). The tempo transform cannot
  reach the luck-driven cases, which is why headroom ≤ 5 falls only from 6.4% to 5.4%.
- Entry tail, five-seed totals (A0 / B1 / B2): 80+ is 31 / 31 / 27; 85+ is 8 / 8 / 7; 90+ is 2 / 2 / 2.
- Mean entry overall: 46.46 / 46.40 / 46.26, inside the ≤ 0.3 hypothesised.
- Replay (Test2): the 80+/85+/90+ entry counts are unchanged at 8 / 1 / 1. Cárdenas enters at 96.09 (A0), 94.63 (B1),
  93.02 (B2) and 91.14 (B2c).

**H2. Potential is preserved in the isolation arms; the promotion effect is separate.**
- B1, B2 and B2c store exactly A0's potential target; F7 checked every entrant. The built golfer's potential differs
  by at most 0.1, from the production builder rounding up to the next 0.1.
- Ceiling profiles do change. Mean change per touched entrant under B2: physical +0.18, mental +0.12, technical
  categories −0.07. The largest single-golfer category-ceiling change is 3.38. Entry attributes fall uniformly
  (−0.58 per category).
- B2p (production storage) gives 75 entrants per seed a lower stored potential (mean −0.91, up to 2.40). In the replay,
  the 68 affected candidates lose a median 0.55 of projected maximum. The isolation arms avoid this; a production
  implementation would have to choose explicitly.

**H3. The same candidates converge quickly, so the hypothesised delays were too large.**
- Touched common entrants (B2, paired layer) start a median 0.13–0.48 lower at 18, depending on potential band, and
  are within 0.1 by 25.
- Time to elite (paired layer, B2): of those reaching 80 under A0, 6.0% get there later (mean delay 0.07 years,
  largest 5). For 85, 1.8% are later and 2 of 114 no longer reach it by 40. For 90, 1 of 24 is later.
- The hypothesised 1–3-year delays for early-tempo, high-potential candidates did not appear: most touched candidates
  move only a little.
- Cárdenas under B2 first reaches 95 at 20 instead of 18, and his projected years at 90+ stay at 23.

**H4. Rare teenage stars: entries fall slightly under B2; projected teen stars are unchanged.**
- 80+ at entry falls 31 → 27, and 85+ falls 8 → 7.
- Projected "85+ by 20" stays at 19 in every arm, and all 19 of A0's are still teen stars under B1 and B2.
- "90+ by 21" stays at 4. The prediction that teen stars would become rarer was refuted.

**H5. Late bloomers are unaffected, as designed.**
- Entered below 60 and reached 75+: 17.6 per seed in every arm.
- All 88 of A0's late bloomers are still common entrants and all still reach 75+.
- Common entrants reaching 75+: 1,986 under A0, 1,975 under B2.

**H6. Selection: B2 costs more passers than hypothesised.**
- Under the existing rule, junior passers fall 0.63% (B1) and 2.65% (B2): 107 and 453 per seed, with no newly
  selected candidates.
- Every dropped candidate has raw potential below 75 (mean 50) and an early draw. Entering slightly lower, they fall
  below the scouts' keep line.
- The hypothesis said under 1–2%; B2 exceeds it.
- If implemented, the year's junior total, which entrant_rows takes from the existing rule, would fall by about that
  much unless the scouts' rule were recalibrated.
- New professionals rise slightly (+0.16% / +0.48%), because fewer candidates are tracked as juniors.
- Recalculated replay totals: juniors 17,068 → 16,958 / 16,630; new professionals 24,371 → 24,410 / 24,489.

**H7. The cap order stays explicit.**
- Exactly one candidate differs between A1 and A0, and between B2c and B2: raw potential 99.24, entry −0.24.
- Cárdenas's B2c entry of 91.14 is B2 and the cap order combined.

**Exposure (absolute ability, projected): no material change.**
- Per seed, A0 / B2: reach 85+ is 22.8 / 22.4; reach 90+ is 4.8 / 4.8; golfer-years 90+ is 68.2 / 67.8.
- Median age at the projected maximum is 32 in every arm.
- The light schedule shows the same pattern.

## 4. Fresh worlds: not run, and why

The plan conditioned bounded paired fresh worlds on promising generation results. They were not run:
- **Small effects to look for.** Generation changes are small where careers would show them. Exposure, teen stars and
  late bloomers are unchanged, and the near-finished case moves from about 1.4 to 0.4 per 57 seasons.
- **Too few affected golfers.** A bounded run (2 seeds × several seasons) would contain almost none of them, so
  access, earnings, survival and competition effects could not be distinguished from run-to-run variation.
- **The largest effect is already measured.** That effect is B2's −2.65% junior passers. It needs a design decision
  first (accept it, or recalibrate the scouts' rule), not a fresh-world test.
- **Cost and priorities.** A full-population fresh world takes about 155 s per season here, with 4 workers. Career-mode
  development was authorized meanwhile and needs the same resources.

So these effects remain untested: access, earnings, survival, ranking and competition feedback, the starting world
(the transform was applied to entrant cohorts only), and national-share recalculation. Such runs can be done if Ryan
wants them; the runner pattern (substituting the cohort draw functions after world creation) is described in the
run notes.

## 5. Recommendation for review (no decision taken, nothing implemented)

1. **Do not adopt B1.** It changes almost nothing at the top: near-finished share 1.2% → 1.0%, tail counts unchanged.
2. **B2 is a usable but modest option.**
   - Benefits: it gives the rare early-tempo prodigy a little more room (near-finished high-potential entrants 7 → 2 in
     285 cohorts; Cárdenas 96.1 → 93.0), and leaves potential, teen stars, late bloomers and projected exposure
     unchanged.
   - Costs: about 2.6% fewer juniors pass scouting unless that rule is recalibrated; touched golfers' ceiling profiles
     shift slightly toward physical and mental; and a few candidates reach elite levels later.
   - Adopting it would need a rules-versioned change for fresh worlds, plus a decision on the junior total and on how
     potential is stored.
3. **A different mechanism is needed if the goal is clearly more room for every near-finished elite entrant.** About
   half of the remaining cases come from career luck, which production also stores as potential. Options include how
   entry luck is applied to young entrants, or how much of it is stored as potential. Each is a separate,
   approval-requiring design question with its own side effects. Neither was tested here.
4. **Fresh worlds.** Run bounded fresh worlds only after Ryan picks a candidate and settles the junior-total question.

## 6. Limitations

- **Fixed inputs.** The replay holds Test2's recorded allocations, and nation profiles are the starting ones. Shares,
  carry and prestige are not recomputed. The starting world is untouched.
- **Projections.** One controlled schedule, plus a light sensitivity. No coaching, injuries, money, access, quitting or
  retirement.
- **Small samples at the top.** The extreme tail has single-digit counts per 285 cohorts.
- **Parameters tested.** Only two settings of one transform family, plus the explicit cap-order and storage variants.

## 7. Reproduce

    cd docs/review/readiness/headroom
    python3 -I plan_table.py <checkout>
    STUDY_CHECKOUT=<checkout> python3 -m unittest -v test_headroom
    python3 -I validate.py <checkout> <checkout>/tests/data/test2_nation_shares.json.gz results/validate.json results/VALIDATION.md
    python3 -I run.py <checkout> <checkout>/tests/data/test2_nation_shares.json.gz <workroot> 4
    python3 -I report.py <workroot>/<manifest hash> results/RESULTS.md results/results.json
    ./selftest.sh <checkout> <checkout>/tests/data/test2_nation_shares.json.gz <scratch> <workroot>/<manifest hash>

On 4 cores: validation about 3.6 minutes, the run about 16 minutes.
