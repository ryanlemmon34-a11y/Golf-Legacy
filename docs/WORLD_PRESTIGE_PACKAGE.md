# World prestige package (roadmap P2; rules 2026-11-05)

Five-year prestige for events, courses and nations, and each nation's share of the fixed yearly cohorts of new
golfers (owner decision D7). Golfer prestige is unchanged: the 52-week fame plus legacy model stays as it was.

Code: `golfsim/prestige.py` (events, courses), `golfsim/participation.py` (nations), `golfsim/population.py`
(`entrant_rows`: the cohort-share rule; `expected_shares`), `golfsim/careers.py` (the two pathways call it),
`golfsim/season.py` (state, updates, season end, old saves), `golfsim/archive.py` (the season record),
`golfsim/rules.py` (rules 2026-11-05 and three rule texts), `tools/observer_prestige.py` and `tools/observer.py`
(columns and bars). Tests: `tests/test_nation_shares.py`, `tests/test_world_prestige.py`.

Every constant below is in one commented block marked **PROPOSED calibration** (`prestige.py` for events and
courses, `participation.py` for nations): starting values to measure, not proven ones.

## 1. Event prestige: five calendar years

The four factors (tour standing 35 %, field 30 %, purse 20 %, course quality 15 %) are unchanged. What changed is
the window:

| Item | Rule | Constant |
|---|---|---|
| Window | the calendar year of the edition and the four before | `EVENT_YEARS = 5` |
| Smoothing | weights by age 1.0, 0.9, 0.8, 0.7, 0.6 (this year's edition carries 1.0 / 4.0 = a quarter, exactly the old model's share for one edition) | `YEAR_WEIGHTS` |
| Skipped editions | a year with no edition (not held: nobody entered) is left out; the other years' weights are renormalised. Two editions in one year count as their mean. No edition in five years: prestige stays where it was | |
| Warm-up | a new world assumes each event's **four** years before the first season were played at its expected starting factors (the same expected values the old model seeded). The first real edition therefore carries a quarter of the weight, the assumed years leave the window one a season, and from the fifth season the window holds only real editions | `WARMUP_YEARS = 4` |
| Annual movement limit | after an edition, prestige may differ from its value at the start of that calendar year by at most 6 points either way (the raw window value is recomputed each year from the factors, so a capped move is only delayed, never lost) | `EVENT_MAX_MOVE = 6.0` |
| Field quality | the best 30 entrants' world ranking positions (amateur ranking for amateur events) **as ranked the week the event was played** -- unchanged, and never later career peaks | |

Sustained field quality raises prestige: each strong field enters five years of the window. Why 6 points: in the
old model a single extreme field could move an event by ~7.5 points (30 % x 100 / 4); 6 keeps ordinary moves
untouched and slows only shocks. Qualifying stages keep their starting prestige, as before.

## 2. Course prestige

A separate value from physical quality. The course factor in event prestige still reads only the course's
class and layout (`COURSE_QUALITY`), so **course prestige never feeds event prestige**: a strong field cannot
upgrade its own venue and feed back into its own score.

* Each season, a course records the highest prestige (as played) of the events it hosted.
* At each season's end it is set **for the next season** from the five completed seasons before it (the
  current season never counts: a one-season lag): the recency-weighted mean (weights 1.0..0.6 by age) of the
  seasons in which it hosted something, moved at most 10 points a season (`COURSE_MAX_MOVE`). A course that
  hosted nothing in those five seasons loses 10 % a season (`COURSE_FADE = 0.9`).
* Warm-up: the four seasons before the world began are assumed to have hosted what its first season's plan
  gives it, at the events' starting prestige. Courses that never hosted have no prestige (shown blank).

### Venue selection: proposed, not implemented

Venues come from the course library (`course_library.py`), which plans every edition of every event from the
calendar and a seed and is **shared by every world in a process** (`default_library`). Making venue choice read
one world's course prestige would mean a per-world library (or a per-world venue overlay) and a change to how
saves store the library -- a large change, so per the brief it is proposed here instead:

1. Once a season ends, for each event whose prestige has been at least ~8 points above its venue's course
   prestige for three consecutive seasons (sustained, not one field), consider moving its **next-but-one**
   season's edition (two-season lag: the decision at the end of Y affects Y+2, so no edition can upgrade the
   venue it is being played on, and course prestige read at Y never includes Y) to a better course.
2. Candidates: courses in the event's existing host-city pool (geography), of a class its level allows
   (`LEVEL_LAYOUTS`: capacity and layout), free that week (availability), preferring the course it already
   uses unless the candidate's course prestige or class is clearly higher (tradition: a home course is kept
   unless the gap is large; a stable tie-break by seed and course id).
3. Host-quality development (a course's class rising over decades) would be a separate, slower rule.

## 3. National prestige and cohort shares (D7)

### No extra golfers

| Step | Rule |
|---|---|
| Total | each pathway's yearly total is what the **existing** rule creates from the nation profiles the world began with (`Participation.baseline`), with the existing random streams (`{seed}:juniors:{year}:{country}`, `{seed}:new-pros:{year}:{country}`): today's year-to-year variation, independent of prestige |
| Starting shares | each nation's expected share of the golfers the existing rule creates in that pathway: candidates (from its pool) x the chance one passes the filter (from its development), by numerical integration, no random draws (`population.expected_shares`); fixed at world creation, stored and shown |
| Current shares | starting share x participation multiplier, normalised to 100 % |
| Allocation | the total split by current shares, largest remainders first; ties by the larger quota, then the nation's name |
| Generation | each nation draws from its own existing distribution (same mean from its development, same filter) until exactly its allocation has passed: first the existing rule's own draws, then further draws continuing the same stream. Draw d is fixed by (seed, pathway, year, nation, d) |

So a share changes how many golfers come from a nation, never their talent and never the total; with every
nation allocated exactly what the existing rule gave it, the golfers are the existing rule's own (tested).
Nothing reads or changes `development`, `pool` or any potential or ability parameter. Only future entrants
are affected; nationality never changes. Shares and allocations are recorded every season (archived) and
shown on the nation pages.

Example (the owner's): a nation holding 1 of 100 places whose prestige doubles its multiplier gets 2; the total
stays 100 and the other nations lose exactly 1 between them (`test_a_rising_nation_gains_exactly_what_the_others_lose`,
also with real draws).

### National prestige: success beyond pre-event expectation

* In every event except qualifying stages each starter earns the fame points of their finish (event prestige
  cubed times the finish's share: majors count far more than mini tours).
* Before each event, each starter is expected to take a part of the fame the event hands out, from what is
  known then -- who entered and their Overall at the time:
  `(1 - EXPECT_SKILL) / field size + EXPECT_SKILL x softmax(Overall / EXPECT_TAU)`, with `EXPECT_SKILL = 0.5`,
  `EXPECT_TAU = 4.0`. Half is "being in the field", half is ability: a favourite who wins gains something, an
  outsider who wins gains much more, and a nation with many entrants gets no credit for numbers alone.
  Actual and expected totals are equal over all nations at every event: national prestige is zero-sum.
* Over the last five completed seasons (weights 1.0..0.6 by age; fewer while the world is young):
  `R = (A5 + 150) / (E5 + 150)` -- the pseudo-count `NATION_PSEUDO = 150` fame points (a major win at prestige
  ~95 is worth ~86, so nearly two major wins) steadies small samples -- and `prestige = 50 + 25 x log2 R` within 0-100.
  50 = as expected, 75 = twice the expected success, 25 = half.

### Multiplier and long-term bounds

* Target multiplier `4 ^ ((prestige - 50) / 50)`: 0.25 at prestige 0, 1 at 50, 2 at 75, 4 at 100
  (`MULT_MIN = 0.25`, `MULT_MAX = 4.0`).
* Yearly change at most x1.10 or /1.10 (`MULT_STEP`). Decided at each season's end for the next season's
  entrants (one-season lag).
* **Long-term bounds.** A nation's multiplier is between 0.25 and 4 times its starting value. From 1 it takes
  at least `ceil(ln 4 / ln 1.1) = 15` seasons of sustained prestige 100 to reach 4 (or 15 of sustained
  prestige 0 to reach 0.25); sustained prestige 75 (twice the expected success for five years) holds it at 2.
  Shares are normalised, so a nation's share relative to its start is `m / (the world's share-weighted mean
  multiplier)`: for a small nation, 4x when the rest of the world stays at 1, up to 16x if every other nation
  sat at 0.25; the other way down to 1/4 (1/16 at the extreme). A nation with most of the cohort (the USA)
  cannot multiply its share the same way -- its share is capped by 100 % -- but it can lose most of it.
* Why wider than 0.5-2.0: the owner wants meaningful long-term market-share movement, not a near-baseline
  lock. 0.5-2.0 would cap a small nation at about twice its start whatever decades of success; 0.25-4
  allows real shifts while the 10 % yearly step keeps every year smooth.

### Starting shares (actual values)

From the starting nation profiles (`nations.py`), by `Participation(nations(), 2027).starting_table()` (numerical
integration, no random draws; the same for every seed). Expected golfers a year under the existing rule: juniors
298.7, new professionals 428.5. For comparison, the existing rule's realised totals for seed 2027, 2028-2037:
juniors 269, 302, 295, 303, 297, 295, 310, 286, 271, 297 (mean 292.5); new professionals 458, 462, 399, 450, 443,
422, 464, 438, 441, 439 (mean 441.6). (Those means are within about one and two standard errors of the
expected totals respectively; the longer check is `Baseline.test_expected_shares_match_the_existing_rule`,
not yet run -- see section 6.)

| Nation | Pool | Dev | Juniors share | Juniors expected/yr | New pros share | New pros expected/yr |
|---|---|---|---|---|---|---|
| USA | 100 | 63.5 | 33.59% | 100.4 | 33.85% | 145.1 |
| Japan | 40 | 56.5 | 8.17% | 24.4 | 8.01% | 34.3 |
| England | 22 | 64 | 7.65% | 22.9 | 7.71% | 33.1 |
| Australia | 16 | 63 | 5.19% | 15.5 | 5.23% | 22.4 |
| South Korea | 18 | 60.5 | 4.90% | 14.6 | 4.90% | 21.0 |
| South Africa | 10 | 66 | 3.98% | 11.9 | 4.02% | 17.2 |
| Canada | 13 | 60 | 3.41% | 10.2 | 3.41% | 14.6 |
| Sweden | 7 | 64.5 | 2.52% | 7.5 | 2.54% | 10.9 |
| Scotland | 8 | 62.5 | 2.50% | 7.5 | 2.52% | 10.8 |
| France | 9 | 60.5 | 2.45% | 7.3 | 2.45% | 10.5 |
| Spain | 7 | 63 | 2.28% | 6.8 | 2.29% | 9.8 |
| China | 10 | 56 | 1.97% | 5.9 | 1.93% | 8.3 |
| Germany | 9 | 56.5 | 1.84% | 5.5 | 1.80% | 7.7 |
| Denmark | 4 | 67 | 1.70% | 5.1 | 1.72% | 7.4 |
| Ireland | 6 | 60.5 | 1.64% | 4.9 | 1.63% | 7.0 |
| Thailand | 5 | 61 | 1.41% | 4.2 | 1.41% | 6.1 |
| India | 6 | 55 | 1.10% | 3.3 | 1.07% | 4.6 |
| Norway | 2.5 | 66 | 1.00% | 3.0 | 1.01% | 4.3 |
| Argentina | 3 | 63 | 0.97% | 2.9 | 0.98% | 4.2 |
| Italy | 3.5 | 60 | 0.92% | 2.8 | 0.92% | 3.9 |
| Mexico | 3.5 | 60 | 0.92% | 2.8 | 0.92% | 3.9 |
| New Zealand | 3 | 62 | 0.90% | 2.7 | 0.91% | 3.9 |
| Northern Ireland | 2.5 | 64 | 0.87% | 2.6 | 0.88% | 3.8 |
| Netherlands | 3.5 | 58 | 0.80% | 2.4 | 0.79% | 3.4 |
| Belgium | 2 | 64 | 0.70% | 2.1 | 0.70% | 3.0 |
| Finland | 2 | 63 | 0.65% | 2.0 | 0.65% | 2.8 |
| Taiwan | 3 | 56.5 | 0.61% | 1.8 | 0.60% | 2.6 |
| Wales | 2.5 | 58 | 0.57% | 1.7 | 0.56% | 2.4 |
| Austria | 2 | 61 | 0.57% | 1.7 | 0.57% | 2.4 |
| Colombia | 1.8 | 60.5 | 0.49% | 1.5 | 0.49% | 2.1 |
| Philippines | 2.2 | 56 | 0.43% | 1.3 | 0.42% | 1.8 |
| Chile | 1.5 | 61 | 0.42% | 1.3 | 0.42% | 1.8 |
| Switzerland | 2 | 54 | 0.34% | 1.0 | 0.33% | 1.4 |
| Malaysia | 2 | 53 | 0.32% | 0.9 | 0.30% | 1.3 |
| Zimbabwe | 1 | 61 | 0.28% | 0.8 | 0.28% | 1.2 |
| Portugal | 1.5 | 52 | 0.22% | 0.7 | 0.21% | 0.9 |
| Brazil | 1.5 | 50 | 0.19% | 0.6 | 0.18% | 0.8 |
| Kenya | 1.2 | 52 | 0.18% | 0.5 | 0.17% | 0.7 |
| Indonesia | 1.5 | 49 | 0.17% | 0.5 | 0.16% | 0.7 |
| Czechia | 1.2 | 50 | 0.15% | 0.5 | 0.14% | 0.6 |
| Singapore | 1 | 52 | 0.15% | 0.4 | 0.14% | 0.6 |
| Vietnam | 1.2 | 46 | 0.11% | 0.3 | 0.10% | 0.4 |
| United Arab Emirates | 0.8 | 50 | 0.10% | 0.3 | 0.09% | 0.4 |
| Morocco | 0.8 | 48 | 0.09% | 0.3 | 0.08% | 0.3 |
| Poland | 0.8 | 46 | 0.07% | 0.2 | 0.07% | 0.3 |
| Peru | 0.6 | 48 | 0.06% | 0.2 | 0.06% | 0.3 |
| Namibia | 0.4 | 52 | 0.06% | 0.2 | 0.06% | 0.2 |
| Nigeria | 0.6 | 45 | 0.05% | 0.1 | 0.04% | 0.2 |
| Egypt | 0.6 | 44 | 0.05% | 0.1 | 0.04% | 0.2 |
| Fiji | 0.3 | 52 | 0.05% | 0.1 | 0.04% | 0.2 |
| Zambia | 0.4 | 48 | 0.04% | 0.1 | 0.04% | 0.2 |
| Saudi Arabia | 0.5 | 46 | 0.04% | 0.1 | 0.04% | 0.2 |
| Turkey | 0.6 | 42 | 0.04% | 0.1 | 0.03% | 0.1 |
| Mauritius | 0.3 | 48 | 0.03% | 0.1 | 0.03% | 0.1 |
| Qatar | 0.3 | 45 | 0.03% | 0.1 | 0.02% | 0.1 |
| Bahrain | 0.2 | 44 | 0.02% | 0.0 | 0.01% | 0.1 |
| Oman | 0.2 | 44 | 0.02% | 0.0 | 0.01% | 0.1 |

Read with the bounds: a nation with 0.05 % of the juniors (about one junior every seven years) at the
maximum multiplier 4 has about 0.2 %, about one every two years; the USA at 0.25 would fall from 33.6 % to about
11 % if the rest of the world stayed at 1.

## 4. Saves, rules, archive, observer

* `RULES_VERSION = '2026-11-05'` with a `VERSIONS` entry and rule texts `event-prestige`, `course-prestige`,
  `nation-shares` (rules page).
* `Season.__setstate__`: an older save's event factor list is converted to the five-year window (played
  editions take their years from the prestige history, the four assumed ones the years before the world
  began); course prestige starts empty (rated from the first season end after loading); national prestige
  starts at 50 with multipliers 1 and starting shares from the save's nation profiles.
* Season files carry `prestige` (`golf-legacy-prestige/1`): every event's prestige as the season ended, every
  course's prestige for the next season, and for nations the prestige, ratio, multiplier, shares, actual and
  expected fame of the season, the next season's totals, allocations and the existing rule's own counts, and
  the starting shares.
* Observer: Prestige columns on Tournaments and Courses (sortable per page; "List by prestige" sorts the whole
  list), Prestige / Multiplier / Share / Starting share columns on Nations; dated bars on a tournament's page
  (end of each season, then now), a course's page (each season's value, set when the season before ended)
  and a nation's page (prestige and junior share per entrant season, with a table of shares and the golfers
  actually received).

## 5. Measurement (small scale)

**Not run yet.** A machine-wide CPU hold stopped all simulations and measurements while this package was
written. The script is ready (it reports, per season on two seeds at `scale=0.05`: cohort totals, event prestige
moves and how many hit the 6-point limit, majors' prestige, mean course prestige, the top shares and the
biggest multiplier movers, plus a calibration table of actual against expected fame by Overall band for the
expectation model). No results are claimed here until it has run.

## 6. What has and has not been run (state of this commit)

Written under a CPU hold: only tiny unit tests were allowed, at `nice -n 19`.

**Run, passing (13 tests, under a second each):**

```
python -m unittest tests.test_world_prestige.EventWindow tests.test_world_prestige.CourseLag \
  tests.test_nation_shares.SmoothingAndBounds \
  tests.test_nation_shares.TotalsAndAllocation.test_allocation_sums_and_is_reproducible \
  tests.test_nation_shares.TotalsAndAllocation.test_shares_sum_to_one \
  tests.test_nation_shares.TotalsAndAllocation.test_a_rising_nation_gains_exactly_what_the_others_lose \
  tests.test_nation_shares.TalentUnchanged.test_the_draw_code_never_reads_prestige_or_shares -v
```

These include the owner's D7 acceptance example
(`test_a_rising_nation_gains_exactly_what_the_others_lose`): a nation holding 1 of 100 places has its multiplier
doubled, gets 2, the total stays 100 and the others lose exactly 1 between them, none gaining; then the same
with real junior draws for one year (the total is unchanged and the other nations lose exactly the nation's
gain). Also run: the starting-share table above (numerical integration) and ten years of the existing rule's
realised totals.

**Not run yet** (they need cohort draws or season simulation; to run once the hold is lifted):

* Light (seconds, cohort draws only, no season): the rest of `tests.test_nation_shares` --
  `TotalsAndAllocation.test_the_total_is_the_existing_rules_whatever_the_shares`,
  `TotalsAndAllocation.test_existing_rule_draws_are_reused_exactly`, `TalentUnchanged` (two cohort tests),
  `Baseline` (15 years of juniors and 4 of new professionals against the expected shares).
* Medium: `tests.test_nation_shares.InTheWorld` (builds a 0.05-scale Season and pickles it: deterministic
  resume, nationality unchanged).
* Heavy (a simulated season or more): `tests.test_world_prestige.InASession` (one season and three weeks,
  archive record and every observer view), and the existing modules touched: `tests.test_season`,
  `tests.test_population`, `tests.test_development`, `tests.test_amateur_residence`,
  `tests.test_history_consistency`, `tests.test_observer_history`, `tests.test_living_views`.
* The two-seed measurement (section 5).

## 7. Open questions

1. Expectation model: half field presence, half ability (`EXPECT_SKILL`, `EXPECT_TAU`). Pure ability-based
   expectation would leave shares near baseline (success beyond a rating-based expectation is mostly noise);
   pure field presence would turn development differences into a steady drift of shares toward high-
   development nations. The half/half blend is a proposal; the calibration table in section 5 (once run) will show how well
   the ability half fits.
2. The bounds 0.25-4 and the 10 % step: the owner's call on how far and how fast.
3. The venue-selection link (section 2) is proposed, not built.
4. Small worlds (`scale` < 1) still receive full-size cohorts (the existing pathways ignore `scale`); unchanged.
5. Course prestige uses the best event hosted each season; a course hosting many mid events and one hosting
   one major look different only through that maximum.
