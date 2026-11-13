# Development rules dev-3: elite tail, prodigy readiness, seeded money by standing

Branch: the combined testing branch `build/realism-youth-aging-longirons`, on top of `c9f53d3`. Not main; no
career-mode merge. New worlds get `dev-3`; worlds created earlier keep `dev-1` or `dev-2` exactly (versions are
checked by membership in `realism.READY_RULES / ATTRIBUTE_AGING / ELITE_RULES`, never by `== CURRENT`).

Owner decisions (2026-11-12): A and B approved; C (experience taper) removed; seeded money relative to the
professional pool, not to the theoretical 99.

## What changed (new worlds only)

- **A. Elite tail** (`realism.elite_potential`). Potential above 89 is compressed smoothly towards 95:
  `p' = 89 + 6 (1 - e^-(p-89)/6)`. 90 → 89.9, 91.8 → 91.2, 95 → 92.8, 99 → 93.9. Monotone, unchanged below 89.
  The golfer's level moves by the same amount (growing room kept). Applied to the starting world, juniors and new
  professionals after scouts, colleges and tours have chosen: identities, paths, nations and counts are unchanged.
- **B. Prodigy readiness** (`realism.prodigy_floor`). The minimum room to grow at 18 is 4.5 + 0.5 per point of
  potential above 85 (half at 19, none from 20). Ordinary juniors are untouched.
- **C. Removed.** Aging is dev-2's, bit for bit.
- **Seeded money by standing** (`finance.MoneyStanding`). Money a new world invents before anything is played
  (starting savings, the backers' seeding estimate, seeded fame → prestige → sponsors, and a newly arriving
  professional's savings) follows the golfer's mid-rank percentile among the world's non-retired professionals
  ("class" = the professional competitive pool: not an age cohort and not one tour), read as the Overall at the same
  standing of a typical starting world (`finance.MONEY_REFERENCE`, `tools/money_reference.py`). Ties share a
  standing; an empty pool or a pool of one is the middle. Years on tour (savings accumulate from 21, at most eight
  years), status (amateurs and club professionals keep flat amounts) and the 0.2 fame factor for amateurs are kept.
  In-season money was already results-based and is unchanged.

## Evidence so far (kinds kept apart)

Generation only (no golf played):
- Starting worlds, 31 seeds, dev-2 → dev-3 (`gen_compare_31_seeds.json`): #1–#2 gap median 2.37 → 1.41, 90th
  percentile 5.83 → 3.55, max 8.14 → 5.98; best rating max 98.8 → 93.9; attributes at 99 for the #1 median 6 → 4
  (max 19 → 10). Every golfer's path identical; 1–7 golfers changed per world. Seed 416342: Rory Wilson 98.63 →
  93.87, gap 8.14 → 3.55.
- Junior classes, 6 seeds × 54 years (324 classes, 97,257 juniors): identical golfers and paths in every class; 99
  juniors changed. Best entry ratings 94.25 / 94.11 / 93.22 → 84.80 / 84.75 / 84.61.
- Starting money (5 seeds): the richest professional of seed 416342 $199.5M → $66.9M; a world whose #1 is 86.8 or
  88.8 now seeds its #1 like any world's #1; all-professional totals about the same ($1.4–1.7B).

Controlled projection (production `develop_week` / `age_year` on a fixed schedule; no access, money, injuries,
coaching or retirement; `junior_projection_6_seeds.json`): dev-2 potential 92+ (n = 13) median peak 93.24 → 91.74,
years at 90+ 18.8 → 13.2; potential 84–87 unchanged, 87–89 nearly unchanged (median peak 87.25 → 87.12, entry
76.51 → 76.48), 89–92 slightly lower (median peak 89.71 → 89.51). James Garside's class (seed 416342, 2040): entry 94.11 → 84.75,
age 19 95.3 → 87.2, peak 97.96 → 93.39, ceilings at 99 18 → 0.

Played (full-size world, seed 416342, dev-3, 5 seasons 2027–2031 only; the run stopped at the tool's 420 s season
safeguard because it shared the CPU with the test suite): 0 reconcile errors, 0 staff violations, population checks
passed each season. Rory 93.8 → 92.7 (Test3: 98.5 → 97.3), gap 3.5 → 2.0 (Test3: 8.0 → 5.9), majors 6 of 20 (Test3:
7), Premier-tier wins 11 (Test3: 23). Five seasons say nothing about long-term balance.

Compatibility: dev-1 and dev-2 generation, junior and new-professional classes and 15 years of aging fingerprint
identical to `c9f53d3` (`dev2_fingerprint.py`); a dev-1 world and a dev-2 world each played two seasons
(scale 0.1) are identical to `c9f53d3` (`season_fp.py`). These run the code directly; the observer itself keeps
older worlds browse-only (see step 4 below).

## Fresh-world tests for Ryan

1. Check out the testing branch at the commit named in the hand-off, in a new folder (your other worlds are not
   touched):
   ```
   git fetch origin build/realism-youth-aging-longirons
   git worktree add ../golf-dev3-test origin/build/realism-youth-aging-longirons
   cd ../golf-dev3-test
   git log --oneline -1
   python tools/observer_app.py --worlds worlds-dev3-test --workers 1 --open
   ```
   (Or download the ZIP, unzip into a new folder and double-click `RUN_OBSERVER_WINDOWS.bat`.)
2. Create new worlds (several seeds; include 416342). Rules should show version `2026-11-17`. Worlds created earlier
   keep their rules.
3. What to look at:
   - the world's best in each season and the gap to #2 (expected: rarely more than about 3–4; nobody near 99 in
     everything);
   - 18–19-year-old prodigies: very good, still growing, rarely top-10 in the world in their first season;
   - how long one golfer stays #1, majors per golfer, ages of major winners;
   - starting money: seeded by each professional's standing among all the world's professionals (every tour,
     mini tours included), so the best are rich but not hundreds of millions, and a world whose best are in the 80s
     seeds them like one whose best are in the 90s; amateurs and club professionals keep their flat amounts;
   - Premier fields (36 Premier + 4 majors a year), no zero-start full-time amateur or college seasons, money
     reconciling (the observer's checks).
4. Existing worlds (Test3 and every world created on an earlier build) are **browse-only** in this build: the
   observer continues only worlds saved by the same engine (owner decision, 31 October 2026), and these changes
   give a new engine. Continue an old world with the build that created it; test these changes on fresh worlds.
   (The code still keeps each world's own rules: a dev-1 or dev-2 world loaded by this code plays dev-1 or dev-2,
   verified against `c9f53d3`.)

## Limits

- The settings (knee 89, span 6; prodigy 0.5 per point from 85) are judged on generation, projection and five played
  seasons. They are not calibrated on long played careers; the fresh tests are the evidence that matters.
- A gap of up to about 6 can still occur at the start when there is simply no second elite golfer.
- Mental attributes and green reading still mature to 99 in long careers (C was declined).
- Pool size matters for standing: the best of a very small world reads lower than the best of a full one.
