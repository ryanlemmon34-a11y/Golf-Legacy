# Long runs after this pass: seeds, lengths, time and stopping conditions (for approval)

Approved by the owner and HAL on 31 October 2026, with one change: the funding comparison's two arms run the same
build. Full-population fresh worlds on the reference calendar (v2), on the frozen diagnostic build (injury timing,
the major-trip guarantee, the N-most-recent qualification windows, the work pathway, amateur support as an initial
calibration); no continuation of Test 1 or any old world. The commits each run used are recorded in the
diagnostic report.

## Why these lengths

- **Full careers need the early procedural cohorts followed through retirement.** Juniors enter at 18; retirements
  in Test 1 ran from the late 30s to 57 (Harper retired at 54, Shi at 57). The juniors created in a world's first
  five seasons reach 58-62 by its 45th season, so a 45-season run sees almost all of them retire, including
  late-career decline. Thirty seasons is an early/mid-career checkpoint (they are 48-52), not full careers.
- **Secondary seeds** of 10 seasons establish entry and early development only (cohorts aged 18-28), to check that
  the primary seed's early patterns are not one world's accident.
- **The funding comparison** plays the same seed with and without amateur support from the same start, on the
  same build: every rule (qualification, injuries, the work pathway) is identical and support is switched off for
  the comparison arm alone (`tools/long_world.py --no-amateur-support`, `Season(amateur_support=False)`), so the
  differences are the support's. (The earlier plan used an older commit as the baseline; that would have mixed
  several policy changes into the comparison.) It compares outcomes in aggregate, not identical fields: once
  major and amateur participation changes, later rankings, money and careers diverge, as they should.

## The runs

| Run | Seed | Code | Length | Questions |
|---|---|---|---|---|
| A. Full careers | 360013 | this build | 45 seasons | Development by source, age and level for procedural cohorts through retirement; peak ages and duration; physical, technical and mental decline; how the strongest careers (a Harper-like 89 at 19) arise; retirement ages; the support's long-run effect on amateurs who turn professional |
| B. Secondary seed, with support | 2027 | this build | 10 seasons | Entry and early development on a second world; the support's recipients, spending and early career effects |
| C. Funding baseline | 2027 | this build, support off | 10 seasons | The same world without amateur support: the comparison arm for B |
| D. Secondary seed | 3031 | this build | 10 seasons | Entry and early development on a third world |

## Time (estimated from measurements on this 4-CPU machine)

A fresh full-population world's first season takes about 2 minutes and later seasons more as the history grows
(about 3.4 minutes by season 51 in the earlier performance review). The paired three-season measurement of this
pass gives the current build's first seasons (pass report).

- A: about 2 h 15 min - 2 h 45 min.
- B, C, D: about 25-30 min each.
- **Total about 3 h 30 min - 4 h 15 min**, one run after another; about 2 h 45 min - 3 h if two run side by side
  (each with two worker processes).

## Stopping conditions

Each run stops and is reported, with what it had saved, if (`tools/long_world.py`, `safeguards`):

1. a season takes more than 7 minutes (420 s: a runaway safeguard on this machine, not the performance target);
2. an exception, a failed checkpoint or a failed publication occurs;
3. a reconciliation fails: a golfer's cash against their ledgers, family and backers' money, staff payments
   against receipts, amateur support drawn against its cap and its payments, development evidence against the
   change in Overall (beyond 0.015), or the population's accounting (start - exits + arrivals = end);
4. free disk falls below 3 GB.

The active population moving more than 20 % from its starting size is a **diagnostic flag**, not a stop: it is
recorded with that season's arrivals and exits (the accounting is checked every season), and the report says
whether it is legitimate growth or a defect.

One determinism spot check is made in run B: the world is copied after its 4th season and its 5th season is
replayed from the copy (`tools/determinism_replay.py`); every digest of tools/equivalence_check.py must match.

## Performance

The 120-second target is the owner's, on their own machine with a defined workload; final acceptance uses their
results. Here the hardware, the workload (full population, two worker processes per run, the observer's season
skip) and each season's time are reported as measured, and a matched before-and-after measurement on this
machine (the same seed's first season on the previous build and this one, side by side) shows whether this pass
regressed anything.

## What comes back

A report per question with the evidence (tables by cohort, age and level; the funding comparison side by side),
the measured time per season and archive and index growth -- before any calibration is proposed.
