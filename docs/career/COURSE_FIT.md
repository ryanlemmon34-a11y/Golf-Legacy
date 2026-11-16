# Course fit and recorded familiarity in choosing events

Owner authorization: Ryan via HAL, 2026-11-15 21:16. This is a bounded addition that supersedes the feature freeze.
Engine: `golfsim/course_fit.py`. Switched on by `schedule.Spec.course_fit`, which is True for calendar **v3** (the
new-world calendar) only. Calendars v1 and v2 are unchanged.

## What it does

An event's appeal (`Season.event_value`) gains a small, bounded term for every golfer, AI or player alike:

    points = FIT_WEIGHT x fit + FAM_WEIGHT x familiarity     (FIT_WEIGHT 3, FAM_WEIGHT 2)

### fit (from -1 to 1)

`fit` measures what the course asks for against the golfer's relative strengths.

What the course asks for is worked out from its actual hole data. Each characteristic is a z-score against the
course library's measured means, clipped to [-1, 1]:

| Category | Course characteristics used |
|---|---|
| Physical | length |
| Long game | length, fairway width, rough severity |
| Short game | green size, greenside bunkers |
| Putting | green speed, contours |
| Mental | water and out-of-bounds, wind exposure × typical wind |

The golfer's relative strengths come from **current** attributes only: each category's level minus their own
average. It never uses ceilings or potential.

A golfer with no relative strength has a fit of 0.

### familiarity (from 0 to 1)

`familiarity` is the recorded competitive rounds the golfer has played on that course (`Golfer.familiarity`), passed
through the engine's own curve, `familiarity.value`. The regional baseline is a playing rule, so it is not counted
here.

### Size of the term

The term can move an event's appeal by at most −3 / +5 points:

* On real golfers and courses, its standard deviation is about 0.6 points.
* The existing per-choice noise has a standard deviation of 3.
* Prestige, travel (±6), costs, fatigue, major rest (−6/−8) and defending champion (+5) are all larger.

So it reorders close choices. It does not dominate.

### What it does not do

* No random draw. The draw count for each choice is unchanged.
* No eligibility, budget, field-size, priority or admission rule reads it. The term is added only after an event has
  passed `eligible` and the affordability check.
* Nothing in how a tournament is played changes. The engine, familiarity's playing effect and the regional baseline
  are untouched.
* Events played at several courses (qualifier heats) get no term for anyone, because the course isn't known at entry.

## Player evidence (snapshot contract for HAL)

`view['week_compare'][week]['play'][i]['course_fit']` is `CF.evidence(...)`. It is the same number the choice uses.

In a v2 or v1 world it is `None`.

For a single-site event in a v3 world:

    {"course": "<name>", "course_id": "...", "layout": "Championship", "sites": 1,
     "fit": -1..1, "familiarity_rounds": 4.0, "familiarity": 0..1, "points": -3..5,
     "factors": [{"category": "putting", "demand": -1..1, "points": 0.42}, ...],   # five categories, fixed order
     "weights": {"fit": 3.0, "familiarity": 2.0},
     "note": "How the course suits your current game and how well you know it: ... Not a forecast of your result."}

For a multi-site event:

    {"course": null, "sites": n, "points": 0.0, "fit": null, "familiarity": null, "weights": {...}, "note": "..."}

`factors[].points` are the per-category contributions before the overall fit is clipped. Attribute levels are not
shown, because the player sees their own levels through scouting.

Present `points` as a small part of appeal, never as an expected result or a guarantee.

## Intended outcome changes and golden impact

This deliberately changes which events AI golfers choose in **v3 worlds**. So all-AI v3 outcomes change, and the v3
golden is re-baselined, not passed off as unchanged:

* `tests/test_college_qualifiers.py` `V3_2028_W26`:
  * Before: `34e21453…565e5c`.
  * After: `1599ebb9…d3a234`.
  * Both values are recorded in the test.
* The v2 and v1 goldens (`tests/test_career_foundation` all-AI constants) are **unchanged**, because the rule is off
  there.

Measured on v3, seed 11, scale 0.05, rule on vs off (same world otherwise). The figures count single-site
non-qualifying entries:

| Period | Entries changed | Winners changed |
|---|---|---|
| Week 1 | 2 of 82 (2.4 %) | 1 of 4 events |
| Weeks 1–4 | 11 of 663 (1.7 %) | 4 of 34 events |
| Full 2027 season | 11.9 % | 226 of 435 events |

The direct effect is about 2 % of entries. The season figure is mostly divergence: once a field differs, results,
money, rankings and later choices differ too. That is expected of any change to choices, and it doesn't mean the
term is large.

Existing saves (fingerprint) are affected as for any engine change: older saves open browse-only.

## Tests

`tests/test_course_fit.py` (10 tests):

* The term is v3-only.
* Boundedness, including extreme golfers and unlimited familiarity.
* Sensible preference: a strong putter prefers the putting test, a long hitter prefers the other course, a level
  golfer gets a fit of 0, and appeal rises with familiarity up to `FAM_WEIGHT`.
* The term is small next to prestige and noise.
* Multi-site events carry no term.
* The evidence equals exactly what `event_value` adds (same draw), and shows no attribute levels.
* v2 has no evidence.
* No eligibility or capacity override: even at +1000, every evaluated option was eligible and affordable, and fields
  stayed within capacity.
* Deterministic replay, with the read model asked for every golfer and event each week changing nothing.
* The term really changes choices.

Human/AI parity: the player's options are valued in the same loop with the same function (`regular_entries` →
`event_value`), and the term reads only the golfer, the course and the rule, never who controls the golfer. The
existing paired human/AI tests run in v2 worlds, where the term is off. No separate v3 paired-career test was added.
