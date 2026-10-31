# Recruitment package (roadmap S2/S3): richer scouting and two-way staff recruitment

Rules version **2026-11-04** (rule `staff-recruitment`). Code: `golfsim/staff.py` (the constants block under
"recruitment (rules 2026-11-04)", `firming`, `scouting_estimate`, `coach_rates`, `coach_takes`,
`golfer_answers`, `caddie_answers`, `loyalty`, `approach`, `start_of_season`), `golfsim/history.py`
(`Stint.reason_accept`, `Stint.declined`, `Relations.refusals`), `tools/observer.py` / `tools/observer_history.py`
(display). Tests: `tests/test_recruitment.py`. Design: `docs/COACHES_AND_CADDIES.md`.

**Every constant below is PROPOSED, not final.** They are starting values chosen to keep the world's staff
numbers where they were while making each side's choice visible; the owner approves them (or not) before they
are treated as settled.

## What changed

1. **Assessments firm up with seasons watched.** Each coach-player pair keeps how many winters that coach has
   looked at that player (`Staff.watched`). The scout's error (their persistent misjudgement plus the yearly
   wobble) is multiplied by `1/sqrt(1 + 0.5 (n - 1))` for n seasons watched (capped at six: x0.53). A coach keeps
   following up to 20 players whose projected level came within 4 points of their bar; the rest of the 60 they
   look at are new. The inputs are unchanged: the level seen with error, the growth typical for the age and last
   year's real improvement. Hidden potential and ceilings are never read.
2. **Coach motivations.** Development coaches (the existing youth specialists) rank prospects by the room to
   grow they see (+0.6 per point) and last year's rise above the typical (+0.5 per point). The other coaches
   ("coaches of established players") rank by achievement anyone can see (Prestige / 10 plus up to 3 for a world
   ranking inside 200 or an amateur ranking inside 300), a known fit from working together before, and earned
   major places this season (+1 each, up to 3). The bar for a share deal (projected level and at least 6 points
   of room) is unchanged. When a golfer asks to become a paying client, a coach with room nearly always says yes;
   as the book fills, they keep places for the players they look for (young improvers / established results and
   major places), and a known poor fit counts against.
3. **Two-way.** A golfer approached for a share deal may refuse (less likely from a well-known coach, more likely
   while a college team coaches them or when last season's prize money makes 5% costly). A golfer asking a coach
   to take them on tries the coaches they like best in turn. A tour professional offers the bag first to caddies
   they worked well with, then by reputation; a caddie weighs the golfer's results (last season's prize money on
   the scale a caddie's reputation follows, or Prestige), a known fit and time together, and a Premier card, and
   becomes readier to accept with each bag refused that winter.
4. **Loyalty.** A golfer approached while coached weighs the newcomer's extra reputation (+1.2 per 10 points,
   capped at 25 points) against loyalty = 4 x rapport + 1 x fit + 1.5 x evidence-weighted results together. The old
   rule (switch with 85% chance to any coach 5+ reputation points better) is gone. Winter departures keep their
   existing odds, which already read progress, rapport, fit and money; retirement is unchanged.
5. **Reasons recorded.** Each stint keeps why it was proposed (`reason_start`) and why the other side accepted
   (`reason_accept`); every refusal is in `Relations.refusals` with both ids, who asked and why, who said no and
   why, and the partnership the golfer kept (if any), where it is also listed (`Stint.declined`). A golfer who
   leaves for an approach has `left for an approach from <coach>` as the stint's end reason. All of it is in the
   archive's `relations.json.gz`. Profiles show how each partnership began (with the acceptance reason), how many
   approaches a golfer turned down while in it, and a table of approaches turned down -- for a golfer, coach or
   caddie whether or not any partnership ever began, and for the current season before it is archived (the live
   snapshot, `tools/observer_live.py`, carries this season's refusals and each stint's acceptance reason and
   declined approaches, as it already carried this season's stints).

6. **Staff who make the first move** (added after review, same rules version). *Coaches of established
   players* (reputation 55+, room in their book) court established golfers of any age near them -- separate
   from youth scouting -- looking at the 30 most accomplished within reach (achievement at least 4) and offering
   a fee to the one they rate highest, one offer a winter (`established_approaches`). *Caddies without a bag*
   look at the 30 golfers wanting a caddie in their region with the best results and offer to carry the bag of
   the one they would most readily accept (at least 85%), one offer a winter (`caddie_approaches`). The golfer's
   answer respects the existing affordability rules (`coach_budget`, `caddie_budget`), loyalty to a current
   partner and shared history (`golfer_answers(..., 'fee')`, `golfer_takes_caddie`). Stints record the true
   initiator (`started_by` 'coach' or 'caddie'); refusals record who asked. One offer per pair per winter
   across every path (`offered`); a golfer whose partnership began in this market is not courted again until the
   next; an existing partnership ends only after the golfer accepts another. Each path has its own seeded random
   stream, so replay is deterministic.

## The constants (proposed)

| Constant | Value | Why |
|---|---|---|
| `SCOUT_LOOK` | 60 | Unchanged sample size. |
| `WATCH_FOLLOW`, `WATCH_FOLLOW_MARGIN` | 20, 4.0 | A third of the sample is people they already rate; enough for firming to matter without freezing who gets seen. |
| `WATCH_FIRMING`, `WATCH_MAX` | 0.5, 6 | Two seasons cut the error by ~18%, four by ~37%; it never reaches certainty (late bloomers can still be missed). |
| `WATCH_FORGET` | 2 (others 1) | Keeps the record bounded: about one winter's looks plus the followed players. |
| `DEV_GROWTH`, `DEV_RISE` | 0.6, 0.5 | The old ranking used +0.3 x room for everyone; development coaches now lean harder on growth. |
| `ELITE_GROWTH`, `ELITE_ACHIEVED`, `ELITE_FIT`, `ELITE_MAJORS` | 0.1, 1.0, 1.0, 1.0 | Achievement ~0-13 points; a major place is worth about as much as 10 Prestige. |
| `COACH_TAKES_BASE`, `_INTEREST`, `_FULL` | 5.5, 1.2, 5.0 | An empty book refuses ~1-2%; a book 5/6 full refuses about half of the clients it is not looking for. A first try (6.0 for _FULL, base 5.0) produced ~100-130 coach refusals a season and was softened. |
| `GOLFER_SAYS_YES` | 1.8 | ~86% acceptance before other terms, close to the old fixed 85%. |
| `GOLFER_REP`, `GOLFER_FIT`, `GOLFER_COLLEGE`, `GOLFER_EARNING` | 0.3, 0.5, 0.8, 1.0 | Modest nudges with visible reasons. |
| `SWITCH_BASE`, `SWITCH_GAIN`, `SWITCH_CAP` | -0.5, 1.2, 2.5 | With nothing built: ~52% for a 5-point better coach, ~87% for 20 points. |
| `LOYALTY_RAPPORT`, `LOYALTY_FIT`, `LOYALTY_RESULTS` | 4.0, 1.0, 1.5 | A full season together (rapport ~0.7) already outweighs a 20-point gain; good rapport, fit and results push a switch below 10% (tested). |
| `CADDIE_SAYS_YES`, `CADDIE_PAY`, `CADDIE_FIT`, `CADDIE_STABLE`, `CADDIE_WAITING` | 2.5, 0.6, 1.0, 0.5, 0.5 | A top caddie (85) turns down most low-earning Challenger bags but relents after a few refusals; ordinary caddies almost always accept. |

| `ESTABLISHED_REP`, `ESTABLISHED_BAR` | 55, 4.0 | Only coaches with some standing court stars; a candidate needs Prestige ~40 or Prestige ~25 with a top-100 ranking. |
| `ESTABLISHED_LOOK`, `ESTABLISHED_OFFERS` | 30, 1 | Bounded search and one fee offer a winter per coach. |
| `GOLFER_FEE_YES`, `GOLFER_COACHABLE` | 0.5, 1.0 | A golfer without a coach accepts a paid approach ~62% before terms, more if coachable or the coach is well known. |
| `CADDIE_LOOK`, `CADDIE_OFFERS`, `CADDIE_APPROACH_MIN` | 30, 1, 0.85 | Bounded search; one offer a winter per free caddie, only to a golfer they would readily accept. |
| `GOLFER_CADDIE_YES`, `GOLFER_CADDIE_REP` | 1.5, 0.5 | ~82% before terms; less when the caddie is less known than the golfer's own results. |

## Measured before/after (proposed values)

**The tables below were measured BEFORE item 6 (staff who make the first move) was added and have NOT been
re-run since** (CPU hold). One tiny check of the extended market, not a measurement: the first winter of seed
2027 at scale 0.1 (unscaled coaches) gave 300 caddie partnerships, 277 of them started by the caddie (in a
world's first winter every caddie is free, so caddies move first almost everywhere; later winters have few free
caddies), 58 fee partnerships started by coaches of established players (golfers aged 24-47) beside 200 hired by
golfers, and 30 caddie offers and 47 coach offers turned down by golfers.

Small worlds, `workers=1`, `generate_world(seed, scale=0.15)`, three seasons (2027-2029), measured with the same
script (`tools/staff_market_measure.py`, table by `tools/staff_market_compare.py`) on both builds (before = commit a11f29a, after = this branch). Because the generated starting coaches are
not scaled with the population (480 at any scale), both arms scaled them by 0.15 for the measurement so that a
small world has the full world's coaches per golfer and capacity binds as it does at full scale. The population
grows each season in a small world (juniors arrive at full-world rates), so later seasons are larger. Shares and
counts are at each season's start; endings and refusals are those dated in that season (its winter market at week
1 included). Values are season 1 / 2 / 3.

**Seed 2027 (both arms run):**

| Measure (season 1 / 2 / 3) | Seed 2027 before | Seed 2027 after |
|---|---|---|
| Coach partnerships (season start) | 328 / 524 / 685 | 323 / 525 / 717 |
|   of which share deals | 44 / 77 / 106 | 38 / 61 / 96 |
| Caddie partnerships | 341 / 480 / 782 | 339 / 482 / 766 |
| Coach stints begun | 328 / 220 / 205 | 323 / 216 / 230 |
| Coach stints ended | 21 / 36 / 70 | 13 / 26 / 79 |
|   ended: retirement | 14 / 20 / 43 | 6 / 10 / 49 |
|   ended: golfer change | 4 / 6 / 4 | 5 / 8 / 5 |
|   ended: coach moved on | 3 / 7 / 10 | 2 / 6 / 10 |
|   ended: money | 0 / 1 / 13 | 0 / 1 / 15 |
|   ended: left for a better-known offer | 0 / 2 / 0 | 0 / 1 / 0 |
| Caddie stints ended | 25 / 49 / 105 | 23 / 58 / 97 |
|   ended: retirement | 13 / 25 / 38 | 15 / 34 / 29 |
|   ended: golfer change | 8 / 17 / 39 | 6 / 17 / 38 |
|   ended: money | 4 / 7 / 28 | 2 / 7 / 30 |
| Mean length of ended coach stints (yrs) | 1.00 / 1.53 / 2.03 | 1.00 / 1.49 / 1.94 |
| Mean length of ended caddie stints (yrs) | 0.98 / 1.47 / 1.53 | 1.00 / 1.54 / 1.49 |
| Refusals: golfer said no to a coach | 0 / 0 / 0 | 8 / 10 / 14 |
| Refusals: coach said no to a golfer | 0 / 0 / 0 | 47 / 38 / 47 |
| Refusals: caddie said no to a golfer | 0 / 0 / 0 | 64 / 26 / 82 |
| Share with a coach: Premier | 0.84 / 0.97 / 0.95 | 0.86 / 0.96 / 0.96 |
| Share with a coach: Challenger | 0.51 / 0.82 / 0.49 | 0.49 / 0.84 / 0.52 |
| Share with a coach: pro other | 0.10 / 0.06 / 0.04 | 0.06 / 0.07 / 0.05 |
| Share with a coach: pro part-time | 0.00 / 0.10 / 0.19 | 0.00 / 0.14 / 0.19 |
| Share with a coach: college | 0.17 / 0.13 / 0.10 | 0.14 / 0.11 / 0.12 |
| Share with a coach: amateur | 0.03 / 0.04 / 0.05 | 0.03 / 0.04 / 0.05 |
| Mean Overall change, <=23 none | 1.54 / 1.51 / 1.48 | 1.54 / 1.50 / 1.48 |
| Mean Overall change, <=23 fee | 0.46 / 0.35 / 0.75 | 0.69 / 0.52 / 0.67 |
| Mean Overall change, <=23 share | 1.40 / 1.23 / 1.16 | 1.41 / 1.27 / 1.24 |
| Mean Overall change, 24-30 none | 0.19 / 0.28 / 0.25 | 0.21 / 0.28 / 0.23 |
| Mean Overall change, 24-30 fee | 0.17 / 0.20 / 0.21 | 0.16 / 0.20 / 0.22 |
| Mean Overall change, 31+ none | -0.41 / -0.51 / -0.52 | -0.40 / -0.48 / -0.52 |
| Mean Overall change, 31+ fee | -0.27 / -0.31 / -0.33 | -0.27 / -0.32 / -0.34 |
| Reconcile errors / staff violations | 0/0 / 0/0 / 0/0 | 0/0 / 0/0 / 0/0 |
| Coach paid == received; caddie paid == received | True/True / True/True / True/True | True/True / True/True / True/True |

**Seed 3031 (before only — the after arm has NOT been run yet:** a CPU hold on the shared machine stopped new measurement runs; the command is in *Status* below):

| Measure (season 1 / 2 / 3) | Seed 3031 before |
|---|---|
| Coach partnerships (season start) | 361 / 534 / 675 |
|   of which share deals | 41 / 68 / 91 |
| Caddie partnerships | 331 / 482 / 766 |
| Coach stints begun | 361 / 197 / 188 |
| Coach stints ended | 23 / 31 / 81 |
|   ended: retirement | 18 / 15 / 45 |
|   ended: golfer change | 3 / 5 / 10 |
|   ended: coach moved on | 2 / 10 / 7 |
|   ended: money | 0 / 0 / 17 |
|   ended: left for a better-known offer | 0 / 1 / 2 |
| Caddie stints ended | 30 / 51 / 106 |
|   ended: retirement | 15 / 26 / 43 |
|   ended: golfer change | 8 / 20 / 45 |
|   ended: money | 7 / 5 / 18 |
| Mean length of ended coach stints (yrs) | 1.00 / 1.52 / 2.05 |
| Mean length of ended caddie stints (yrs) | 0.98 / 1.35 / 1.49 |
| Refusals: golfer said no to a coach | 0 / 0 / 0 |
| Refusals: coach said no to a golfer | 0 / 0 / 0 |
| Refusals: caddie said no to a golfer | 0 / 0 / 0 |
| Share with a coach: Premier | 0.84 / 0.96 / 0.97 |
| Share with a coach: Challenger | 0.68 / 0.78 / 0.47 |
| Share with a coach: pro other | 0.19 / 0.10 / 0.03 |
| Share with a coach: pro part-time | 0.00 / 0.10 / 0.14 |
| Share with a coach: college | 0.18 / 0.10 / 0.09 |
| Share with a coach: amateur | 0.04 / 0.08 / 0.07 |
| Mean Overall change, <=23 none | 1.52 / 1.65 / 1.52 |
| Mean Overall change, <=23 fee | 0.90 / 1.11 / 0.74 |
| Mean Overall change, <=23 share | 1.30 / 1.22 / 1.30 |
| Mean Overall change, 24-30 none | 0.14 / 0.24 / 0.25 |
| Mean Overall change, 24-30 fee | 0.17 / 0.20 / 0.22 |
| Mean Overall change, 31+ none | -0.45 / -0.51 / -0.50 |
| Mean Overall change, 31+ fee | -0.27 / -0.30 / -0.34 |
| Reconcile errors / staff violations | 0/0 / 0/0 / 0/0 |
| Coach paid == received; caddie paid == received | True/True / True/True / True/True |

What the numbers say:

- **Partnership counts, coached share by level, mean partnership length and development by coaching status
  are within run-to-run noise** of the build before (the coached share at every level moves by a few points at
  most). Share deals are ~10-15% fewer: some young players now say no (8-14 a season), mostly college players.
- **Refusals happen on every side**: golfers ~10, coaches ~40-50 (their books are full in these worlds), caddies
  25-80 a season (most in the first season, when no prize money is yet recorded and caddies judge by Prestige
  alone).
- **A partnership ending only because of a better-known offer is rare**: 1 of 118 coach endings in the three
  seasons of seed 2027 (2 of 127 before).
- **Finance reconciles and capacity holds** in every season of both arms (`tools/long_world.checks`: no reconcile
  errors or staff violations; coach and caddie payments equal receipts).
- Run time is unchanged (264 s before, 267 s after for seed 2027).

## What I am unsure of

- **Small-world measurements.** Three seasons at scale 0.15 cannot show long-run effects (loyalty and firming
  matter most after several seasons); a full-scale multi-season run should confirm before approval.
- **Coach refusals** are concentrated in nearly full books; whether coaches should turn away paying clients at
  all while they have room (the ~1-2% at an empty book) is a design choice for the owner.
- **Caddie refusals in the first season** are higher because no prize money has been recorded yet; Prestige is
  the fallback. A world with a recorded past would not see this.
- **Who counts as "elite".** Every coach who is not a youth specialist uses the established-success motivation,
  including modest club teachers; reputation could gate it instead.
- **The hiring step's own view of the golfer's weakest area** (pre-existing, unchanged) still comes from the
  golfer's imperfect reading of their own ceilings (`perceived_gap`); none of the new decisions read it.
- **Saved state grows** by the watched record (~13k entries at scale 0.1; at most ~480 coaches x 60 a winter plus
  followed players, bounded by forgetting) and the refusal log (tens to a few hundred records a season).
- **One seed only so far** for the after arm (see Status): the conclusions above are provisional until seed 3031
  is measured.

## Status: what has and has NOT been run

Run (on this branch's code, final proposed constants; HEAD after the review fix also merges origin/build/v16):
- Measurement, seed 2027, scale 0.15, three seasons, both arms (table above).
- `tests.test_recruitment`: AssessmentTests, MotivationTests, TwoWayTests, LoyaltyTests and
  HiddenTests.test_new_decision_code_never_reads_potential_or_ceilings -- 9 tests, OK. (An earlier run of
  these plus the other two HiddenTests -- 11 tests, OK -- was on the first constants, before
  `COACH_TAKES_BASE/_FULL` were softened from 5.0/6.0 to 5.5/5.0.)
- After the review fix (refusals shown without any partnership, and live): the same 9 plus
  `tests.test_recruitment.ObserverRefusalTests` (3 fixture tests, no world) -- 12 tests, OK, with `nice -n 19`.

- After item 6 (staff who make the first move): `tests.test_recruitment` Assessment, Motivation, TwoWay,
  Loyalty, Hidden (all three), ObserverRefusal and Initiative tests -- 19 tests, OK, with `nice -n 19` (tiny
  worlds, the market only).

> **Update, 31 October 2026.** Recruitment has since been measured descriptively on the candidate `c0d1ea5` (seeds 4207 and 5309, read only): offers, acceptances, refusals and their reasons by year, in `docs/review/arms_comparison/` on branch `build/v16-report`. The constants are kept as the playtest baseline (D21). The list below is kept as written.

NOT yet run (blocked by the CPU hold):
- Any measurement with item 6 (both seeds' after arms need re-running).
- Measurement, seed 3031, after arm:
  `python tools/staff_market_measure.py . 3031 0.15 3 after_3031.json` (before: the same script with ROOT a
  checkout of a11f29a), then `python tools/staff_market_compare.py before_3031.json after_3031.json`. The script
  scales `staff.INITIAL_COACHES` by the world's scale in both arms.
- `tests.test_recruitment.WorldTests` (determinism and finance/capacity: two runs of a scale-0.05 world through a
  season, ~40 s), `HiddenTests.test_shifting_hidden_potential_changes_no_staff_outcome` and
  `HiddenTests.test_saves_from_before_two_way_recruitment_load_with_defaults`.
- The neighbouring modules: tests.test_staff, tests.test_living_views, tests.test_history,
  tests.test_history_consistency, tests.test_finance_integration, tests.test_observer_history.
