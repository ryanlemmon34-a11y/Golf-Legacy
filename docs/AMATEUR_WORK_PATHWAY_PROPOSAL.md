# Persistently cash-blocked adult amateurs: the work / part-time pathway

Status: **implemented as an initial calibration (rules 2026-11-03, `golfsim/work_pathway.py`)**, approved by the
owner on 31 October 2026 with the thresholds below. It does not sponsor anyone: amateur support
(`docs/AMATEUR_SPONSORSHIP_PROPOSAL.md`) is for amateurs who show success; this is for the ones who cannot afford
to play at all. It is an employment-and-golf pathway, not sponsorship, forced retirement or guaranteed success.

## As implemented

**Who**: a full-time amateur outside college, aged 21 or over, outside the amateur ranking's top 300 (or
unranked), holding no amateur support this season, with no family money left.

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
   full-time. That was wrong for amateurs: the comeback decision (`careers.p_comeback`) applies to professionals
   only. A working amateur's existing route to full-time golf is **turning professional** at a season's end
   (`careers.p_turn_pro`, which already considers part-time amateurs; after 27 it is recorded as a comeback).
   There is no return to full-time *amateur* golf, for this pathway or for amateurs who took a job at a season's
   end. Nothing new was added; a return to full-time amateur golf when savings recover would be a new behaviour
   and needs a decision.
2. **Funds test.** "Spendable funds below the cheapest eligible event" is not tested separately: it is exactly
   what the ledger's "could not afford any event" means each counted week. "No family money left" is checked
   when the decision is made.
3. **Timing.** The decision waits for the next monthly plan after the 8th counted week, so the count when a job
   is taken is 8 to 11 (the proposal's "from the next monthly block").
4. **Consecutive.** "8 consecutive weeks" is 8 counted weeks with pauses allowed in between, as the owner
   directed (calendar gaps must not keep erasing the evidence).

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
| Minimum age | 21 | Median age of the stuck seasons is 23; younger golfers mostly have family money or college |
| Standing | outside the amateur top 300, no amateur support | The supported and ranked are excluded by construction |
| Weeks cash-blocked | 8 in a row | Two monthly plans: one bad month is not enough |
| Funds test | below the cheapest eligible event, no family money left | The ledger's own definition of unaffordable |
| Timing | from the next monthly block | Instead of waiting for the season's end |

### Expected effect (to be measured, not assumed)

Most of the ~35 zero-start full-time amateur seasons a season in a mature world become part-time seasons with a
few local starts; the second and later empty seasons in a row (42 % of them in Test 1) mostly disappear. The
amateur ranking and the professional pipeline are unaffected (the golfers concerned are unranked). It changes
outcomes: a new rules version for new worlds, measured in the funding comparison run before any further tuning.
