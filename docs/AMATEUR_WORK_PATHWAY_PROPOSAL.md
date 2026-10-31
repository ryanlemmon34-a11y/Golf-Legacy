# Persistently cash-blocked adult amateurs: the work / part-time pathway

Status: **implemented as an initial calibration (rules 2026-11-03, `golfsim/work_pathway.py`)**, approved by the
owner on 31 October 2026 with the thresholds below. **Minimum age lowered from 21 to 18 in rules 2026-11-10**
(approved by the reviewer under the owner's delegation); nothing else in the pathway changed, and worlds started
before 2026-11-10 keep the minimum age of 21. It does not sponsor anyone: amateur support
(`docs/AMATEUR_SPONSORSHIP_PROPOSAL.md`) is for amateurs who show success; this is for the ones who cannot afford
to play at all. It is an employment-and-golf pathway, not sponsorship, forced retirement or guaranteed success.

## As implemented

**Who**: a full-time amateur outside college, aged 18 or over (since rules 2026-11-10; 21 or over before), outside
the amateur ranking's top 300 (or unranked), holding no amateur support this season, with no family money left.

**Minimum age (rules 2026-11-10)**: 18, lowered from 21 (`work_pathway.MIN_AGE`). Only the age changed: the eight
counted cash-blocked weeks, the counts, pauses and resets, no family money left, no amateur support held, the
top-300 rule, full-time non-college amateurs only, and the decision at the monthly plan are as before. Nobody is
given money and no start is guaranteed. The minimum in force is recorded on the season
(`Season.work_pathway_min_age`): new worlds have 18, and a save from before 2026-11-10 is resumed with 21
(`Season.__setstate__`), so an older world plays on unchanged. Tests: `tests.test_work_pathway.Age18Tests`.

**Counting the evidence** (every full-time non-college amateur is counted, so the groups left out can be measured
too), from the weekly access ledger the observer already shows:

| A week recorded as | Effect on the count | Why |
|---|---|---|
| could not afford any event (an eligible event existed; none was affordable from spendable funds, support included) | **+1** | The only genuine affordability block |
| injured | pause (no change) | An injury is not money |
| no suitable event scheduled; not eligible for the events scheduled | pause | Gaps in the calendar (off weeks, the winter between seasons) must not erase the evidence, nor count as it |
| played; declined; chose to train or rest; shut out of a full field | **reset to 0** | They could pay for an event that week, so they were not blocked |

The count carries across the year end. **Decision**: at each monthly plan (weeks 1, 5, 9, ... 49), before the
month is planned, a candidate whose count has reached **8** takes a job from that block on: a part-time (working)
amateur with the salary, living costs and schedule every working amateur has. The date, the weeks counted, the
golfer's age, amateur rank, cash and the reason ("could not afford to play: took work") are recorded
(`work_pathway` in the season's archive file) and written in the career history. Each full-time amateur's longest
count in the season is archived too (`cash_blocked_max`), for measuring prolonged blocks among those left out
(younger, ranked or supported amateurs). Tests: `tests/test_work_pathway.py`.

## Departures from the proposal (flagged for the owner)

1. **The way back.** The proposal said the existing winter comeback decision lets a part-timer return to
   full-time. That was wrong for amateurs (`careers.p_comeback` is for professionals only). Resolved since
   rules 2026-11-06: the owner approved a return to full-time amateur golf (D5) and HAL decided its thresholds
   under the owner's delegation (D5a): `golfsim/amateur_return.py`, below.
2. **Funds test.** "Spendable funds below the cheapest eligible event" is not tested separately: it is exactly
   what the ledger's "could not afford any event" means each counted week. "No family money left" is checked
   when the decision is made.
3. **Timing.** The decision waits for the next monthly plan after the 8th counted week, so the count when a job
   is taken is 8 to 11 (the proposal's "from the next monthly block").
4. **Consecutive.** "8 consecutive weeks" is 8 counted weeks with pauses allowed in between, as the owner
   directed (calendar gaps must not keep erasing the evidence).

## Return to full-time amateur golf (rules 2026-11-06; provisional calibration)

Each winter a working amateur outside college who did not turn professional may return, if all three hold:
**a full season in work** since taking the job (a mid-season job counts from the next season; working before
the world's records began counts); **sustainable funding** -- no debt, and savings plus family money covering a
full-time amateur season of golf (16 events at their own average trip cost last season, or a regional amateur
trip when they played fewer than 3); support and salary never count; and **results** in the season just ended --
amateur ranking inside the top 300, a win or top-3, or a rise of 100+ places. Then a chance, never certain:

    sig(-3.0 + 2.0 x results + 0.6 x min(2, savings / season cost) + 1.5 x (drive - 0.5) - 0.12 x max(0, age - 23))
      x (1 - their chance of taking a job again next winter, a year older with that season paid for), at most 60 %

No age is excluded; the last factor makes the chance fall with age consistently with the existing job decision
(which makes full-time adult amateurs ever likelier to take work through their mid-twenties), so a return that
would be undone a year later is correspondingly unlikely. The switch is never a way out of debt. Recorded as a
career decision ("amateur returned to full-time golf") with its facts, and in the career history.

**Measured so far (provisional, tiny sample):** a 5 % world (seed 93) over three seasons: 3, 2 and 1 returns
(ages 23-30); 2 of the returners took a job again the next winter in 2028 and 2 in 2029; none was cash-blocked
into the work pathway. The flip rate needs a full-population measurement before the numbers are anything but
provisional.

**Measured on the full population (31 October 2026, candidate `c0d1ea5`; accepted provisionally, no tuning).**
Four comparison runs, read only (seed 4207 for 10 seasons in three arms, seed 5309 for 5 seasons). The report is
`docs/review/arms_comparison/ARMS_COMPARISON.md`, sections 5 and 5.1, on branch `build/v16-report`.
- Returns: 1,166 by 1,125 people. Over all return evaluations, p = 0 included, the rate is 1.60 %; over the
  eligible evaluations (p > 0) it is 7.8 %. By age band, eligible rates are 18-20 4/9, 21-24 25.7 %, 25-29 6.0 %,
  30+ 0.1 %.
- 157 returns came in a run's last season and are censored, not counted as successes.
- Of the 1,009 observed returns, in the next season:
  - 0 had a cash-blocked week and 0 re-entered the work pathway;
  - 505 took a job again the following winter (36 % at 21-24, 71 % at 25-29). This is a separate event: the
    ordinary winter job decision.
- The return rule discounts that next-winter job decision with the same function on projected inputs, so it is a
  proxy. On the 989 evaluated the next winter, the anticipated chances sum to 431.9 against 505 realised.

## The original proposal

### Proposed rule

Checked at each monthly plan (every 4 weeks), for a **full-time, non-college amateur aged 21 or over** with **no
amateur support** and **outside the amateur ranking's top 300**:

1. **Cash-blocked**: the week ledger has recorded "could not afford" as the reason for **8 consecutive weeks**
   (two monthly plans), they have **no family money left**, and their spendable funds are **below the cost of their
   cheapest eligible event**.
2. **Response**: from the next monthly block they take a job -- they become a part-time (working) amateur with the
   existing salary and living costs, keep playing the local events their week allows, and the decision is
   recorded with its date and reason ("could not afford to play: took work").
3. **Way back**: unchanged -- the existing winter comeback decision lets a part-timer return to full-time when
   their savings and results allow.

Nothing is forced on anyone ranked, supported, in college, under 21, injured (injury is a different reason in the
ledger) or simply choosing not to play; nobody's costs are waived and nobody is given money.

### Thresholds (approved)

| Threshold | Proposed | Why |
|---|---|---|
| Minimum age | 21 (18 since rules 2026-11-10) | Median age of the stuck seasons is 23; younger golfers mostly have family money or college |
| Standing | outside the amateur top 300, no amateur support | The supported and ranked are excluded by construction |
| Weeks cash-blocked | 8 in a row | Two monthly plans: one bad month is not enough |
| Funds test | below the cheapest eligible event, no family money left | The ledger's own definition of unaffordable |
| Timing | from the next monthly block | Instead of waiting for the season's end |

### Expected effect (to be measured, not assumed)

Most of the ~35 zero-start full-time amateur seasons a season in a mature world become part-time seasons with a
few local starts; the second and later empty seasons in a row (42 % of them in Test 1) mostly disappear. The
amateur ranking and the professional pipeline are unaffected (the golfers concerned are unranked). It changes
outcomes: a new rules version for new worlds, measured in the funding comparison run before any further tuning.
