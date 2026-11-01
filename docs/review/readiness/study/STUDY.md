# Starting-ability study: evidence for review (experiment only)

**Status.** Experiment branch `build/v17-readiness-study` only. No game code changed (`golfsim/`, `tools/` and `tests/` are
identical to main, 18a8e23), no balance model chosen, nothing released, career mode untouched. Growth and decline laws
and parameters are unchanged in every arm. This is evidence and a recommendation for HAL and Ryan to review.

Files here: `study.py` (arms, replay, paired layer, projection), `validate.py` + `results/VALIDATION.md` (fail-closed
baseline validation), `provenance.py` (validation stamp and gates), `run.py` (runner), `report.py` +
`results/RESULTS.md` (all tables), `selftest.sh` + `results/SELFTEST.md` (negative tests).

## 1. The arms, and what each can and cannot do

| arm | readiness at entry | what it can change |
|---|---|---|
| A0 no change | youth deficit from the peak-age draw (the same draw that sets decline); raw potential before the 99 cap | baseline |
| A1 cap order | as A0, potential capped at 99 before the deficit | only candidates with raw potential above 99 |
| A2 independent | readiness tempo `27 + 2e`, e keyed by the candidate; the peak-age draw still sets decline | who is precocious; the tie between precocity and decline |
| A3 weak tie (rho 0.3) | tempo `27 + 2(rho z + sqrt(1 - rho^2) e)`, z from the unchanged peak-age draw | as A2, keeping a weak tie |
| A3r5 (rho 0.5) | sensitivity for A3 | as A3 |

- **A2/A3 cannot lower starting levels.** Their readiness tempo has the same distribution as the peak-age draw, N(27, 2),
  and is independent of potential and luck. Juniors' entry overall therefore has the same distribution under A0, A2
  and A3, and so does the frequency of near-finished teenagers. What these arms change is *who* is precocious, and
  whether being precocious goes with declining early.
- **Combined variants are not tested.** A2/A3 keep the existing cap order, so a cap-order-plus-tempo arm was not run.
- **Peak-age draw kept fixed.** The peak-age distribution is preserved, and the peak-age draw is the fixed input
  wherever correlation is tested.

## 2. Evidence layers and their limits

- **Validation (fail-closed).** A0 reproduces Test2 (seed 386509) cohort by cohort:
  - 114 of 114 cohorts (2028–2084 × 2 pathways) pass;
  - 41,439 of 41,439 entrant rows and 4,303,391 of 4,303,391 production draws are identical;
  - each entrant's recorded potential, peak age, aging rate and luck rebuild its production row exactly;
  - ρ = 1 gives A0, and evaluating an arm first never disturbs A0.

  The validator exits 1 unless conditions F1–F6 all hold:
  - F1: the 114-cohort boundary;
  - F2: per-cohort parity;
  - F3: 16,811 juniors in 2028–2083 plus 257 in 2084. The 2084 class is created at the close of the last season (2083)
    and never plays;
  - F4: 8 juniors at 80+ and 1 at 85+, Cárdenas on top;
  - F5: the only allocation discrepancy is the documented one;
  - F6: not a negative-test run.

  Its stamp is bound to the hashes of `study.py`, `validate.py`, the fixture and the `golfsim` sources. The runner and
  the report refuse a missing, failed or stale stamp. Negative tests N1–N5 and R1–R6 all behave as stated
  (`SELFTEST.md`).
- **Known discrepancy, documented separately.** For 2061 juniors, `entrant_rows` given the recorded shares (rounded to 6
  decimals) moves one place between Norway and Sweden. The two quota remainders differ by 0.0000050. A per-nation
  rounding bound is 0.0001485, so rounding is large enough to explain the swap. That it did is not established, and the
  cause is unresolved. The replay uses the recorded allocation, so it is unaffected.
- **Paired layer: recalculated selection.** Five seeds, 57 cohorts each. In each nation-year the same candidates face
  every arm under the existing rule's filter (scouting for juniors; tracking, status and sampling for new
  professionals). Starting nation profiles are used (they never change in a world). Shares, carry and national
  prestige are not modelled.
- **Replay layer: fixed recorded allocation.** Test2's own production candidates, taking each nation's first k passers
  with k = Test2's recorded allocation. This shows who enters given those counts. It cannot by itself establish
  whole-pipeline or national-share effects. The existing rule's pass counts are recalculated and reported separately.
- **Projections: controlled and bounded.** Each entrant is developed with the production `develop_week` / `age_year` to
  age 40 on a fixed schedule:
  - standard: 13 blocks a year of one four-round tournament, two training weeks and one rest week;
  - light, as sensitivity: one tournament, one training week and two rest weeks per block;
  - self-coached (quality 0.3), full competitive experience;
  - no injuries, paid work, money or access limits, quitting or retirement.

  These are not realized careers. They are not strict upper or lower bounds, since there is no coaching and
  participation is fixed. Years at 85+/90+ measure exposure at an absolute ability level, not ranking or competitive
  dominance.
- **Not compared.** No projection is compared with a realized Test2 figure. The review brief's 83.2 / 31 are the median
  career-peak overall and median peak age of a cohort defined in the archive. They are not an overall at age 31, and
  that cohort is not reconstructed here.
- **Run provenance.** The tables come from run `52f48b1674db1cb3`, started by `run.py` at 60c962b before the gate
  existed. Its manifest records the same `study.py`, fixture and `golfsim` digests as the passing stamp, and
  `report.py` checks this.

## 3. Findings

1. **Starting level and tail frequency: unchanged by A2/A3, as their construction implies.**

   Paired layer, juniors, mean over five seeds:

   | measure | A0 | A2 | A3 | A3r5 |
   |---|---|---|---|---|
   | passers per seed | 17,071 | 17,034 | 17,040 | 17,055 |
   | mean entry overall | 46.46 | 46.52 | 46.48 | 46.47 |
   | 99th percentile | 69.83 | 69.74 | 69.80 | 69.82 |
   | 75+, five-seed total | 191 | 194 | 192 | 200 |
   | 80+, five-seed total | 31 | 42 | 41 | 40 |
   | 85+, five-seed total | 8 | 8 | 7 | 6 |

   Per seed, 80+ goes 4/9/4/6/8 under A0 and 11/8/7/7/9 under A2 (higher in four of five seeds), while the wider 75+
   band (191 vs 194) and 85+ (8 vs 8) show no shift. The arms are not designed to change entry-overall frequencies:
   juniors' entry overall has the same distribution under A0, A2 and A3, so a difference in one narrow band is not
   evidence of a shift. No significance test is applied.
   Replay (Test2 candidates): 80+ is 8 under A0 against 10, 10 and 11, and 85+ is 1 in every arm.

   **A1** changes one Test2 junior, Cárdenas (96.09 → 94.21), and nobody's selection.
2. **Who is precocious, and the tie to decline: the actual change.**

   | measure | A0 | A2 | A3 | A3r5 |
   |---|---|---|---|---|
   | correlation of readiness gap with peak age, among passers | 0.854 | −0.001 | 0.243 | 0.411 |
   | mean peak (decline) age of passers | 26.10 | 27.00 | 26.73 | 26.55 |
   | mean peak (decline) age of passers who entered 75+ | 25.26 | 26.84 | 26.22 | 25.99 |

   Under A0, selecting on entry level also selects early decliners. A2 replaces about a quarter of each cohort with
   different individuals (4,312 out and 4,275 in per seed); the entry-overall distribution stays the same, but the
   selected entrants' mean decline age moves from 26.10 to 27.00.
3. **Scouting.**
   - Talented candidates (raw potential 80+) are kept 98.6% of the time under A0 and 99.1–99.3% under A2/A3.
   - Under A0, the talented candidates the scouts miss are late decliners (mean peak 31.0); under A2 the missed ones
     average 27.9.
   - Missed juniors never return as themselves.
   - The recalculated existing-rule junior total in the replay goes 17,068 → 16,917 / 16,952 / 17,021. That would be
     the year's total if an arm were implemented, and is a −0.9% to −0.3% change. National shares were not
     recomputed.
4. **The same golfer converges by the mid-20s** (key-matched common entrants, fixed raw-potential groups, paired
   layer). Under A2, the 10th–90th percentile difference from A0 is about ±6 at 18, ±3 at 21, ±1.2–1.3 at 25,
   ±0.6–0.7 at 30 and ±0.4–0.5 at 35–40. Medians stay near 0 throughout, and A3 and ρ 0.5 are narrower still. In the
   projection, readiness shapes roughly the first 5–7 years; after that, projected ability follows potential and the
   unchanged growth and decline laws.
5. **Elite exposure (projected, absolute ability, controlled schedule): no material change in the reported summaries.**

   | paired layer, per seed | A0 | A2 | A3 | A3r5 |
   |---|---|---|---|---|
   | reach 85+ | 22.8 | 22.0 | 21.8 | 21.4 |
   | reach 90+ | 4.8 | 4.6 | 4.6 | 4.6 |
   | golfer-years at 90+ | 68.2 | 68.4 | 68.2 | 67.8 |

   The median age at the projected maximum is 32 in every arm. The same Cárdenas candidate has 23 / 23 / 22 / 23
   projected years at 90+ (A0 / A1 / A2 / A3). Under A2 he enters at 88.7 instead of 96.1, but is at 97.2 by 25.
6. **Late bloomers: fewer threshold-defined late bloomers, with no lost development for the same candidates.**

   | paired layer, per seed | A0 | A2 | A3 | A3r5 |
   |---|---|---|---|---|
   | entered below 60 and reached 75+ | 17.6 | 12.2 | 13.6 | 15.8 |
   | entered below 65 and reached 80+ | 4.8 | 4.4 | 5.0 | 4.4 |
   | reached 80+ (any entry level) | 99.2 | 101.6 | 100.8 | 100.0 |
   | mean decline-peak age, below 60 -> 75+ group | 30.34 | 27.46 | 28.53 | 28.83 |
   | mean decline-peak age, below 65 -> 80+ group | 30.17 | 27.01 | 28.69 | 29.24 |

   These groups are defined by thresholds within each arm's own cohort, and entry readiness decides who enters below
   60 or 65, so their membership changes with the arm. Following the same candidates (`RESULTS.md` 3i: key-matched
   common entrants, paired layer):
   - all 88 of A0's below-60 → 75+ late bloomers are common entrants under A2, and all 88 still reach 75+ under A2;
   - 80 of the 88 enter at 60 or above under A2, so they leave the threshold group;
   - their projected maximum is slightly higher under A2 (median +0.41; 10th–90th percentile +0.07 to +0.79);
   - across all common entrants, 1,933 reach 75+ under A0 and 1,931 under A2 (86 only under A0, 84 only under A2).

   A3 and ρ 0.5 behave the same way (84 of 84 still reach 75+). So the lower count reflects who enters below the
   threshold, not slow developers declining before they mature. The mean decline-peak age of the threshold groups
   falls under A2 because readiness no longer tracks the decline draw.

## 4. Interpretation

- **What the arms are and are not.** The tested arms are not designed to reduce how often high entry overalls occur, and
  they do not. Under this controlled schedule they show no material change in the reported elite-exposure summaries
  (reaching 85+/90+, golfer-years at 90+, age at the projected maximum). The same candidate's projected ability is
  close to the same under every arm by the mid-20s.
- **What A2/A3 do change.** They change who is precocious, and the tie between precocity and decline. The selected
  entrants' mean decline age moves from 26.10 to 27.00 under A2, and about a quarter of each junior cohort is different
  individuals. They also produce fewer threshold-defined late bloomers. As the fixed-candidate check shows, that is a
  membership effect, not lost development.
- **What is untested.** None of these changes has been followed through careers. Access to events, earnings, survival
  (quitting and retirement), ranking and competition feedback could differ, and this study measures none of them.
- **Where an extreme entrant comes from.** In the generation model, Cárdenas came from raw potential 100.9 with an early
  tempo. Competitive dominance also depends on the field and on round-to-round variance, a separate question not
  studied here.
- **A1** is a consistency correction of negligible size at entry.

## 5. Recommendation for review (no decision taken, nothing implemented)

1. **Keep A0 (no change) for now.** The tested arms are not designed to make near-finished juniors rarer, and under this
   controlled schedule they show no material change in the reported elite-exposure summaries.
2. **A1 only as a consistency fix, if Ryan wants one.** It would be a rules-versioned change for fresh worlds only. It
   alters only candidates with raw potential above 99; it is low value and low risk, and is Ryan's call.
3. **Hold A2 and A3.** Neither lowers the entry distribution, so neither is a fix for the concern that prompted the
   study. If Ryan wants "precocious does not mean early decline" for realism, a weak tie (A3, ρ 0.3–0.5) keeps more of
   the existing tie than full independence. Its consequences for careers are untested.
4. **Further evidence, only with Ryan's approval.**
   - If the goal is fewer near-finished teenagers or less extreme dominance, a different study is needed: the shape of
     the readiness distribution's early tail or the potential tail (no hard caps), and, for dominance, competition
     variance.
   - If A2/A3 stay of interest, fresh-world runs could still show differences this study cannot: about a quarter of
     entrants change and their mean decline age moves. Such runs would measure access, earnings, survival, ranking and
     competition. Whether that is worth doing is Ryan's call.

## 6. Assumptions and limitations

- **Fixed inputs.** Nation profiles are the starting ones. The replay holds Test2's recorded allocations fixed. Shares,
  carry and national prestige are never recomputed.
- **Careers not simulated.** Access to events, earnings, survival (quitting and retirement), ranking and competition
  feedback are untested for every arm.
- **Projection simplifications.** One fixed schedule (plus a light sensitivity) and self-coaching. There are no
  injuries, permanent injury losses, quitting, retirement, money or access effects, and no competition. Category
  choice and aging use the production functions with candidate-keyed random numbers. The paired layer projects only
  entrants with stored potential 70+.
- **Not modelled.** Ranking, wins or competitive dominance. Exposure years are absolute-ability years.
- **Small samples at the top.** Only a handful of 80+ / 85+ entrants appear per 57 seasons, and the replay is a single
  seed. The paired layer's five seeds give the main estimates.
- **One weak-tie form tested.** A3's tie is a Gaussian mixture on the existing peak-age draw at ρ 0.3 (and 0.5). Other
  forms, and combinations with A1, are untested.

## 7. Reproduce

    cd docs/review/readiness/study
    python3 -I validate.py <checkout> <checkout>/tests/data/test2_nation_shares.json.gz results/validate.json results/VALIDATION.md
    python3 -I run.py <checkout> <checkout>/tests/data/test2_nation_shares.json.gz <workroot> 4
    python3 -I report.py <workroot>/<manifest hash> results/RESULTS.md results/results.json
    ./selftest.sh <checkout> <checkout>/tests/data/test2_nation_shares.json.gz <scratch> <workroot>/<manifest hash>

On 4 cores: validation about 2.5 minutes, the run about 16 minutes. Results go to RAM-backed scratch; only the
summaries are committed.
