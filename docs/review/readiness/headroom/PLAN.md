# Headroom study: plan, stated before any run

**Approval.** Ryan approved testing this "more room to develop" approach (2026-11-02 00:49 UTC). The approval covers
testing and reporting only. Nothing here is a balance change, a release or a merge.

**Baselines.**
- Evidence: the reviewed readiness study, `build/v17-readiness-study` 5c7dce9.
- Production: main 18a8e23.

**Scope.**
- Branch `build/v17-headroom-study`, folder `docs/review/readiness/headroom/`. The reviewed study folder is untouched.
- Career mode and Birth of Pro Golf are out of scope.
- Growth (`develop_week`) and decline (`age_year`) laws and parameters are unchanged in this comparison.
- Potential is not lowered for anyone; there is no teen cap; decline is not steepened.

## Mechanism (exact)

**What produces near-finished teenagers today.** A new golfer's current overall is potential minus a youth deficit
plus career luck. The youth deficit at age a is `0.36 * (T - a)^1.55` for T > a, and T is the peak-age draw,
N(27, 2). The same draw also times decline. A candidate with an early draw therefore enters close to their potential:
T = 21 (z = −3) leaves 1.98 points of headroom at 18, against 10.85 at the typical T = 27.

**The change.** Only the tempo T used in the youth deficit changes. It becomes a smooth, monotone transform of the
same peak-age draw p:

    T(p) = p                                                   if p >= K
    T(p) = K - (s (K - p) + (1 - s) / (2w) (w^2 - (p - K + w)^2))   if K - w <= p < K   (quadratic blend)
    T(p) = K - (1 - s) w / 2 - s (K - p)                        if p < K - w

- **Shape.** It is continuous with a continuous slope (C¹): slope 1 above the knee K, blending to slope s over w
  years. Below the blend, each year by which a draw is earlier than the knee counts as s years.
- **Unchanged parts.**
  - Decline still uses the unchanged peak-age draw, so the age_year law is identical.
  - Because the transform is monotone in p, precocity keeps its order and stays fully rank-correlated with decline.
  - Scouting and status decisions still see only observable ability.
  - The scouts' projection uses the typical tempo 27, which the transform leaves alone.

| arm | knee K | blend w | slope s | candidates touched (p < K) | cap order | stored potential |
|---|---|---|---|---|---|---|
| A0 no change | - | - | - | 0 | raw before cap | production rule |
| A1 cap order (reference) | - | - | - | 0 | cap first | production rule |
| B1 mild | 24.5 | 2 | 0.5 | 10.6% | raw before cap | A0's target kept |
| B2 stronger | 25.5 | 2 | 0.3 | 22.7% | raw before cap | A0's target kept |
| B2c (explicit combination) | 25.5 | 2 | 0.3 | 22.7% | cap first | A0's target kept |
| B2p (promotion effect) | 25.5 | 2 | 0.3 | 22.7% | raw before cap | production rule |

- **Same candidates, same values.** Every candidate keeps its latent potential, luck, aging rate, peak-age draw, scouting
  and status coins, attribute and personality draws and RNG keys under every arm (candidate-aligned replay and paired
  layer, as validated in the reviewed study).
- **Age-coherent new professionals.** The same transformed tempo T is used both for their age-18 tracking check and for
  their entry at 21–26.
- **Potential target (isolation).** Production stores potential as max(capped raw potential, entry overall), so a
  candidate whose luck lifted entry above capped potential has that higher value stored. B1, B2 and B2c keep each
  candidate's A0 stored-potential target, so eventual potential is identical across arms. B2p applies the production
  rule to B2's lower entry instead; the difference from B2 is the inherited promotion effect, measured on its own.
- **Ceiling profiles.** Attribute ceilings are rebuilt by the production `init_ceilings` from the larger gap. Their
  per-category profile changes even when overall potential is equal, and that change is reported.

**Headroom at 18 by peak-age z** (no randomness; reproduced by `plan_table.py`):

| z | p | A0 | B1 | B2 |
|---|---|---|---|---|
| 0 | 27 | 10.85 | 10.85 | 10.85 |
| −1 | 25 | 7.35 | 7.35 | 7.42 |
| −1.5 | 24 | 5.79 | 5.83 | 6.39 |
| −2 | 23 | 4.36 | 4.75 | 5.86 |
| −2.5 | 22 | 3.09 | 4.03 | 5.42 |
| −3 | 21 | 1.98 | 3.39 | 4.99 |
| −3.5 | 20 | 1.05 | 2.79 | 4.57 |
| −4 | 19 | 0.36 | 2.24 | 4.16 |
| −5 | 17 | 0.00 | 1.27 | 3.39 |

| share of candidates with headroom at 18 at most | A0 | B1 | B2 |
|---|---|---|---|
| 3 | 0.56% | 0.045% | < 0.0001% |
| 4 | 1.63% | 0.58% | 0.0013% |
| 5 | 3.84% | 3.11% | 0.14% |
| 6 | 7.65% | 7.52% | 3.24% |

**The low-gap tail.** It stays continuous with no floor: the earliest draws still have the smallest headroom. Whether
an exceptional teenage star appears still depends on potential and luck. Rare-star frequency is measured, not
assumed.

**These numbers are test points, not approved tunings.** Mild and stronger bracket a range. The knees sit 1.25 and
0.75 SD early, so the typical and late majority is untouched.

## Rationale

- **It targets the cause.** The previous study showed that decoupling readiness from decline (A2/A3) leaves the entry
  distribution unchanged. Near-finished entrants come from the early tail of the readiness tempo. Thinning that tail
  smoothly gives the most precocious candidates more room to develop, and touches no one with typical or late tempo.
- **It keeps what Ryan asked to keep.** Potential, the growth law (so rapid development), the decline law and the
  readiness/decline ordering are all unchanged.

## Hypotheses (to be confirmed or refuted)

- **H1. Entry tail.** B1 and B2 reduce the near-finished share among high-potential entrants (headroom ≤ 3 or ≤ 5,
  stored potential 80+) and the 85+/90+ entry tail. Median and mean entry overall move little (for juniors under 0.3
  points), because only 10.6% / 22.7% of candidates are touched, and only by a few points.
- **H2. Potential.** Stored potential is identical to A0 for every common entrant in B1, B2 and B2c, by construction. B2p
  lowers it for some positive-luck early-tempo candidates; the count and size are measured.
- **H3. Same-candidate trajectories.** Touched candidates start lower and reach the levels A0 reached later (time to
  80/85/90 rises by about 1–3 years for early-tempo, high-potential candidates). By the mid-to-late 20s they converge
  close to their A0 path; the projected maximum may differ slightly where early physical decline overlaps the longer
  growth. Untouched candidates are identical.
- **H4. Rare stars.** 80+ and 85+ entries at 18 still occur but less often (B2 less than B1). Projected "teen stars"
  (85+ by age 20) become rarer. The size of each drop is measured.
- **H5. Late bloomers.** Candidates with p >= K are untouched, so late developers are unaffected. Threshold-defined
  late-bloomer counts can shift only through who is touched; this is checked with fixed candidates.
- **H6. Selection.** The scouts' rule is unchanged. Touched low-potential candidates enter slightly lower, so a few
  fewer pass, and the recalculated existing-rule totals fall slightly (< 1–2%). Dropped and newly selected entrants are
  listed by potential, tempo and entry band.
- **H7. Cap order.** A1's effect is limited to raw potential above 99, and B2c ≈ B2 plus that effect.

## Measures, kept apart by evidence layer

- **Candidate level (paired layer, before selection).**
  - Entry-overall and headroom distributions of all generated junior candidates.
  - High-potential headroom (median, 10th percentile, share at most 3 / 5).
  - Kept share by potential and tempo band.
- **Selected entrants.**
  - Paired layer (recalculated selection, five seeds) and Test2 replay (fixed recorded allocation).
  - Passers; dropped and newly selected entrants (counts and characteristics).
  - Entry distribution and 75+/80+/85+/90+ tails; stored potential and headroom; ceiling-profile change by category.
  - Recalculated existing-rule totals, reported separately from the fixed-allocation entrants.
- **Fixed-candidate trajectories** (key-matched common entrants, fixed raw-potential groups), under unchanged
  training, growth and decline:
  - deltas at 18/21/25/30/35/40;
  - time to 80/85/90;
  - change in projected maximum;
  - teen stars (85+ by 20, 90+ by 21);
  - late bloomers, threshold groups plus fixed candidates;
  - new professionals.
  - Cárdenas as one example, not the calibration target.
- **Cohort exposure summaries.** Reach 85+/90+ and golfer-years at 85+/90+. These are absolute-ability exposure, not
  ranking or dominance.
- **Light-schedule sensitivity.**

**Evidence boundaries (as in the reviewed study).**
- Projections are controlled: fixed schedule, self-coached, no injuries or retirement. They are neither real careers
  nor strict bounds.
- The replay holds Test2's recorded allocations fixed.
- No universal real-world overall target is set.

**Provenance.**
- A fail-closed validator: the F1–F6 baseline checks plus F7, the mechanism scope. F7 requires:
  - untouched candidates (p ≥ K) identical to A0/A1 under the B arms;
  - T ≥ p always;
  - B1/B2/B2c entrants keep A0's potential target.
- A stamp bound to the sources and the input fixture; a gated runner and report; negative tests; unit tests of the
  transform.

**Fresh worlds.** These come next only if generation looks promising. Bounded paired fresh worlds (same seeds, A0
against the chosen arms) would test access, earnings, survival and competition effects that generation cannot show.
If they are not run, the reason is reported.
