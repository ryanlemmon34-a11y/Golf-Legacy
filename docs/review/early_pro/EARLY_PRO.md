# Early turn-pro evaluation for college amateurs under 22: expected exits (Test2 world, winters 2027–2082)

**Question.** Today, college amateurs (tour `CO_*`) are evaluated for turning pro only in the winter they turn 22. The
proposal is to also score them at ages 18–21 with the existing non-graduating model,
`p_turn_pro(..., graduating=False)`. That model is
`sig(-5.0 + 4.5·standing(am_end) + 0.6·means + 1.0·(will-0.5) + 0.4·min(2,wins) - 0.15·|age-21|)`.

**Gates compared:**
- **A**: every college amateur aged 18–21 is evaluated.
- **B**: only those who hold a winner's exemption for next season, or finish the season ranked ≤ 15 in the amateur
  ranking (the band where `turn_pro` already gives a Challenger card).
- **B′**: as B, but with a ranking cut of ≤ 60 (the lower-tour band).

**Population.** Every `CO_*` amateur aged 18–21 at winters 2027–2082: 49,410 golfer-winters, 12,998 golfers. None of
them graduates that winter.

**What these numbers are.** Expected values computed from the archived inputs, held fixed. No world was replayed.

## Two kinds of total

- **Expected decision-events** = Σp over every golfer-winter a gate evaluates. A golfer evaluated in several winters
  is counted in each of them. In reality, an early exit ends that golfer's later college evaluations. So these sums
  **overcount departures**. They are not unique exits.
- **Expected unique exits (survival-weighted)**. For each golfer, take the winters the gate would evaluate them, in
  order: p₁, p₂, …
  - Expected exit at winter t = p_t · Π_{s<t}(1 − p_s).
  - P(the golfer leaves early at some winter) = 1 − Π(1 − p_t).
  - "Golfer-winters evaluated (survival-weighted)" = Σ_t Π_{s<t}(1 − p_s). This is the expected number of evaluations
    that would still happen once earlier exits are taken out.

**Caveat.** Both totals keep every input as archived. In a real world, an early exit would also change:
- the golfer's later amateur ranking;
- other golfers' rankings, fields and amateur support;
- every later season.

So the survival-weighted figure is still a fixed-input approximation.

**Edge effect.** The archive starts in 2027, so golfers aged 19–21 in 2027 have no earlier winters to survive. In 2027,
unique exits therefore equal decision-events.

## Results

| | **A** (all) | **B** (exempt or rank ≤ 15) | **B′** (exempt or rank ≤ 60) |
|---|---|---|---|
| evaluated per winter, mean (min–max) | 882.3 (829–950) | 5.6 (1–11) | 17.1 (8–31) |
| golfer-winters / golfers evaluated, 56 winters | 49,410 / 12,998 | 314 / 142 | 957 / 434 |
| golfer-winters evaluated, survival-weighted | 48,204 (860.8 per winter, 807–925) | 223.1 (3.98 per winter, 0.71–9.0) | 777.1 (13.9 per winter, 7.4–31) |
| **expected unique exits, total** | **883.5** | **79.9** | **161.2** |
| **expected unique exits per winter**, mean (min–max) | **15.8** (13.7 in 2055 – 27.6 in 2027) | **1.43** (0.18 in 2051 – 3.85 in 2027) | **2.88** (1.43 in 2057 – 7.60 in 2027) |
| unique exits by age at exit: 18 / 19 / 20 / 21 | 214.3 / 188.0 / 223.1 / 258.2 | 27.3 / 12.5 / 16.4 / 23.8 | 48.3 / 27.3 / 37.6 / 47.9 |
| unique exits by rank at exit: 1–15 / 16–60 / 61–300 / 301+ / unranked | 71.9 / 83.1 / 188.9 / 539.4 / 0.1 | 79.9 / – / – / – / – | 72.9 / 88.3 / – / – / – |
| *expected decision-events (Σp, overcounts), total* | *979.0* | *121.4* | *222.7* |
| *decision-events per winter, mean (min–max)* | *17.5 (14.4–27.6)* | *2.17 (0.25–3.94)* | *3.98 (1.57–7.60)* |
| unique exits ÷ decision-events | 0.90 | 0.66 | 0.72 |
| p among evaluated: median / 90th / max | 0.011 / 0.033 / 0.761 | 0.363 / 0.587 / 0.761 | 0.189 / 0.455 / 0.761 |

**What those golfers actually did at 22** (expected unique exits, split):

| | A | B | B′ |
|---|---|---|---|
| turned pro at 22 anyway (a timing shift) | 538.7 (61%) | 70.5 (88%) | 135.7 (84%) |
| stayed amateur at 22 (would be new professionals) | 324.0 (37%) | 7.2 (9%) | 21.4 (13%) |
| still in college when the archive ends | 20.9 | 2.3 | 4.1 |

**Scale.** At graduation, college golfers actually turned pro at 112.2 per winter (94–132), 6,284 over 2027–2082. All
graduates, pro or not, averaged 219.8 per winter. Measured in unique exits per winter against that 112:
- A adds 15.8 (14%).
- B adds 1.43 (1.3%).
- B′ adds 2.88 (2.6%).

**Further findings:**
- **Exemptions add nobody beyond the rank criterion.** Only 11 golfer-winters (6 golfers) held a winner's exemption
  under 22, and every one also ranked ≤ 5.
- **Gate A is dominated by the model's floor.** 82% of A's unique exits are golfers ranked above 60, who would start
  on a mini tour (`turn_pro` gives a mini-tour card when am_rank > 60). They come from a p of about 1% applied to
  roughly 860 golfers every winter.

Per-winter series: `early_pro_per_winter.csv` (winter, gate, evaluated, survival-weighted evaluated, expected
decision-events, expected unique exits).

## Cárdenas (id 19411, CO_INTL, born 2023, willingness 0.35)

| winter | age | am rank | wins | exemption held for next season | money W → means | p (non-graduating model) | expected exit that winter (survival-weighted) | A / B / B′ |
|---|---|---|---|---|---|---|---|---|
| 2041 | 18 | 1 | 10 | none | $37.5k → 0.94 | 0.565 | 0.565 | yes / yes (rank) / yes |
| 2042 | 19 | 1 | 9 | won the 2042 Britannia Open (major) | $25.9k → 0.65 | 0.559 | 0.243 | yes / yes / yes |
| 2043 | 20 | 1 | 9 | won the 2043 Premier Tour Championship (major) | $12.8k → 0.32 | 0.548 | 0.105 | yes / yes / yes |
| 2044 | 21 | 1 | 8 | won the 2044 Premier Tour Championship | $0.8k → 0.02 | 0.540 | 0.047 | yes / yes / yes |
| 2045 | 22 | 1 | 11 | won the 2045 Premier Tour Championship | ≤ 0 → 0 (archived) | graduating: archived p 0.9453, u 0.1527 → turned pro with a Premier card | — | — |

- **Survival-weighted chance he leaves before 22: 0.960 under both B and B′** (and under A). Both gates evaluate him
  in all four winters, from his rank alone.
- An exit in 2041 would have come with a Challenger card. From 2042 on he held an exemption, so an exit would have
  come with a Premier card.
- His p barely changes across the four winters. The money he spends (means falls from 0.94 to 0.02) is offset by the
  age term.

## How the inputs were rebuilt

**Model check.** I recomputed every archived `turn_pro` evaluation in all 57 seasons (253,240 rows) from the model as
written in `careers.py`.
- p matches the archived value with **max |Δp| = 0.0035**, which is the rounding of the stored terms.
- There were no mismatches in age, amateur rank, standing or wins.
- The archived `am_rank` input equals the season file's `careers[gid].am_end`.
- The archived row stores the inputs `age, graduating, am_rank`. Means, willingness and wins are stored only as logit
  terms.

**Age, amateur rank and wins** are archived for every college golfer and are used exactly:
- age is `year − born` from the people table;
- amateur rank is `am_end` from the season's careers row;
- wins is `wins` from the same row.

**Money (the means term: cash plus family money).** Cash is not archived season by season. College golfers under 22
are never evaluated, so the archive has no means term for them either. I rebuilt cash plus family money (W) at each
winter as follows.
- **Ledger flows.** Every change to a golfer's cash goes through the season ledger. Over a season, W changes by the
  net the decision saw, minus family and backer support (support only moves money from the family pot into cash).
  Winter expenses after the decision are the settled net minus that figure.
- **Anchor 1, exact (54% of rows).** Every college golfer is evaluated at 22, and that archived evaluation stores the
  means term to two decimals. When the term is not clipped (between 0 and 1.2), it gives W at 22 to about ±$333.
  Walking the ledger flows backward then gives W at 21, 20, 19 and 18 exactly. This covers 26,792 golfer-winters.
- **Anchor 2, proxy (46% of rows).** The other golfers left college broke: 5,400 of 12,514 graduates had a means
  term of 0. For them, W comes from the monthly planner's week-1 funds, which the decision evidence stores in $1000s
  to two figures. From that figure I subtract the $8,000 credit line and any amateur-support budget already open at
  week 1, then add the season's ledger flow. The result is capped by the bound the graduation term implies (W ≤ 0 at
  22, worked backward). This covers 21,280 rows with that bound and 1,338 rows with no graduation yet.
- **Measured error.** I compared the proxy with the exact value on the 33,906 golfer-winters that have both. Median
  error −$133, median |error| $323, 90th-percentile |error| $5.2k. The larger errors come from coach fees the planner
  sets aside for four weeks, which are not archived.
- **±$5k sensitivity.** Moving every non-exact W down or up by $5k changes the totals by the following amounts. 96% of
  B's rows and 95% of B′'s rows are exact.

  | gate | unique exits (base) | W −$5k | W +$5k | decision-events (base) | W −$5k | W +$5k |
  |---|---|---|---|---|---|---|
  | A | 883.5 | 874.1 | 897.6 | 979.0 | 969.1 | 993.9 |
  | B | 79.9 | 79.8 | 80.1 | 121.4 | 121.2 | 121.6 |
  | B′ | 161.2 | 161.0 | 161.6 | 222.7 | 222.3 | 223.1 |

**Willingness** (`(work_ethic + big_stage)/200`). The people table keeps only `aggression` from a golfer's
personality. So I read willingness from the same graduation evaluation, which stores (will − 0.5) to two decimals.
- Personality never changes after creation, so the value at 22 is also the value at 18–21. This covers 48,072 rows
  (97%).
- For the 1,338 rows of golfers still in college when the archive ends, p is averaged over all 12,514 graduates'
  willingness values (mean 0.513, 10th–90th percentile 0.38–0.65).
- Using 0.5 for them instead changes the totals by at most 0.35 (A: unique exits 883.2).

**Exemptions.** I rebuilt `winner_exemptions(season, Y+1)` from the season files' event winners: position 1 in a major
in seasons Y−4..Y, or in a Premier (tier-1) event in Y−1..Y. I checked these against the next season's careers
`exemption` field:
- 11 agree.
- 0 appear only in the archive.
- 5 appear only in my rebuild. In all 5, the field had been overwritten by a later in-season win (for example,
  Cárdenas in 2042).

## Which gate keeps exits small and earned

| gate | unique exits per winter | share of decision-events from earned opportunities (rank ≤ 15 or exempt) | turned pro at 22 anyway |
|---|---|---|---|
| A | 15.8 | 12% | 61% |
| B | 1.4 | 100% | 88% |
| B′ | 2.9 | 55% | 84% |

Gate A's exits are 82% golfers ranked above 60.

## Files and how to rerun

Input folder: `test2_orig/` (the extracted save, read only). Standard-library Python.

    python3 -I extract.py test2_orig/archive facts.json.gz          # one pass, each season file decoded once
    python3 -I analyse.py facts.json.gz results.json early_pro_per_winter.csv

- `results.json` holds every figure above, plus the per-winter realised graduation counts, the model-check counts per
  season and the exemption cross-check.
- In `results.json`, gate B′ is stored under the key `B_prime`.
