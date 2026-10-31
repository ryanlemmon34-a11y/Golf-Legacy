# Long runs after this pass: seeds, lengths, time and stopping conditions (for approval)

Nothing here has run. The plan follows the owner's instruction of 31 October 2026: full-population fresh worlds on
the reference calendar (v2), this build (injury timing, the major-trip guarantee, amateur support as an initial
calibration); no continuation of Test 1 or any old world.

## Why these lengths

- **Full careers need the early procedural cohorts followed through retirement.** Juniors enter at 18; retirements
  in Test 1 ran from the late 30s to 57 (Harper retired at 54, Shi at 57). The juniors created in a world's first
  five seasons reach 58-62 by its 45th season, so a 45-season run sees almost all of them retire, including
  late-career decline. Thirty seasons is an early/mid-career checkpoint (they are 48-52), not full careers.
- **Secondary seeds** of 10 seasons establish entry and early development only (cohorts aged 18-28), to check that
  the primary seed's early patterns are not one world's accident.
- **The funding comparison** plays the same seed with and without amateur support from the same start, so its
  differences are the support's (the baseline is commit `32bc43d`, the build just before amateur support). It
  compares unchanged affordability rules and outcomes in aggregate, not identical fields: once major and
  amateur participation changes, later rankings, money and careers diverge, as they should.

## The runs

| Run | Seed | Code | Length | Questions |
|---|---|---|---|---|
| A. Full careers | 360013 | this build | 45 seasons | Development by source, age and level for procedural cohorts through retirement; peak ages and duration; physical, technical and mental decline; how the strongest careers (a Harper-like 89 at 19) arise; retirement ages; the support's long-run effect on amateurs who turn professional |
| B. Secondary seed, with support | 2027 | this build | 10 seasons | Entry and early development on a second world; the support's recipients, spending and early career effects |
| C. Funding baseline | 2027 | `32bc43d` | 10 seasons | The same world without amateur support: the comparison arm for B |
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

Each run stops and is reported, with what it had saved, if:

1. a season takes more than twice its estimate (above about 7 minutes);
2. an exception, a failed checkpoint or a failed publication occurs;
3. a reconciliation fails: a golfer's cash against their ledgers, amateur support drawn against its cap or its
   payments, or development evidence against the attribute changes (beyond 0.015 Overall);
4. free disk falls below 3 GB;
5. the active population moves more than 20 % from its starting size in either direction (reported at once:
   either a defect or a calibration question).

One determinism spot check is made in run B: its season 5 is replayed from its season 4 checkpoint and must give
identical digests (tools/equivalence_check.py).

## What comes back

A report per question with the evidence (tables by cohort, age and level; the funding comparison side by side),
the measured time per season and archive and index growth -- before any calibration is proposed.
