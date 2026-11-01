# Readiness, generation and decline: a proposal for discussion (no change made)

**Status.** Discussion only, under the design hold: no decline, generation or potential change is implemented or
proposed for this release. Everything below describes the current model (as coded on build/v17-integration
18a8e23), the evidence from the Test2 world, options, and the evidence each option would need before Ryan decides.
Figures marked *(brief)* are from HAL's review brief on Test2; the rest are read from the code.

## 1. What Test2 shows *(brief)*

- **One extreme entrant.** Cárdenas entered at 18 with overall 96.09 and potential 99 (11 of 21 attributes at 99;
  raw potential 100.881, peak age 20.892, aging rate 0.718, youth gap 1.867). He was the only 85+ entrant among
  16,811 juniors; only 8 entered at 80+. He peaked at 98.1 at 23, won 39 majors, spent 689 weeks at No. 1 (last major
  at 47, last Premier win at 52) and retired at 60 after five starts in his last season (one cut, world ranking 1117).
- **Ordinary development already includes rapid organic growth.** The mature 4,814-junior cohort's peak age median is
  28; juniors with potential 80-90 (n = 31) start at a median 72.27 and reach 83.2 at 31; other arcs such as
  74.86 -> 91.5 at 34 and 60.94 -> 81.8 at 34 exist.
- **Decline among survivors.** Overall change 30 -> 40: -3.6; 40 -> 50: -9.6; 50 -> 60: -13.4. Only nine Premier or major
  wins by golfers aged 50+ across 2,280 such events, and none in a major.
- **Separate question.** The 39-major dominance is a competition-calibration question (field strength, variance),
  not only a generation one, and is kept apart here.

## 2. How the model makes these (as coded)

**Generation** (`population.candidates`, `_make_golfer`). Each candidate draws a potential (normal around the nation's
development mean), a peak age `~ N(27, 2.0)` (unbounded) and an aging rate (lognormal, sd 0.3). Their current overall
is

    current = potential - age_deficit(age, peak_age, aging_rate) + career luck
    age_deficit: young part 0.36 x (peak_age - age)^1.55; old part 0.15 x aging_rate x (age - peak_age - 7)^1.6

so **readiness at entry is not a quantity of its own**: an 18-year-old's distance from potential is set entirely by
how far their peak age is from 18. A typical peak at 27 leaves about 10.9 points to grow (0.36 x 9^1.55; the code's
docstring rounds this to ~12); a peak at 20.9 (about three standard deviations early) leaves 1.9. Combined with a top-tail potential, that is a finished player at 18. The
ceilings (`init_ceilings`) then spread whatever gap there is over the attributes (wider for physical in the young,
for mental at all ages), capped at 99.

**Growth** (`development.develop_week`). Each week moves attributes toward their ceilings in proportion to the gap,
times a learning rate that is highest at 18-21 (1.2 -> 1.15) and falls with age (0.6 at 30, 0.25 at 40), times work
ethic and coaching; tournaments teach the mental game; young golfers also mature physically every week.

**Decline** (`development.age_year`). Once a year: physical attributes fall from `peak_age + 3`
(-0.30 x rate x years^0.7), technique from `peak_age + 8` (-0.15 x rate x years^0.7); the mental game keeps maturing
with competitive experience until 48 and declines after 55. Serious injuries can remove some physical attributes
for good.

## 3. Readiness separated from potential: options

The brief's constraints: separate readiness from potential, keep organic rapid growth, no age ban and no universal
cliff.

| | Option | What changes | Keeps | Risks / open questions |
|---|---|---|---|---|
| **A** | **Readiness as its own draw** (recommended for study) | An entrant's distance from potential at entry becomes its own draw (for example a lognormal "readiness gap" whose median follows the current age curve), independent of potential and of the peak age; the peak age keeps governing when decline starts | Potential and its tail; peak-age effects on decline; a gifted junior can still close the gap fast (learning rate 1.2 at 18) | Needs a target for how ready the readiest 18-year-olds may be; changes every new world's cohort shape (fresh worlds only) |
| B | Bound the peak-age draw | Truncate `N(27, 2.0)` (for example at 2.5 sd) or soften its lower tail | Everything else | Also moves decline timing for early peakers; closer to an age rule; does not separate readiness from potential |
| C | Soft top-tail compression of entry overall | A smooth saturating map above about 85 (no cliff) on the entry overall only | Potential, growth, decline | A cosmetic squash rather than a mechanism; hides rather than explains |
| D | No generation change | -- | Everything | Leaves Cárdenas-type entrants possible (one in 16,811 here); dominance handled, if at all, as the separate calibration question |

**Recommendation for discussion:** study A, with B as the fallback if A's parameters cannot be justified.

## 4. Decline: what to look at before any change

The survivor curve (-3.6 / -9.6 / -13.4 a decade from 30) is of the same shape as the creation curve the model uses
to set starting ratings (below potential at aging rate 1 and peak 27: about 2.6 by 40, 7.0 by 45 and 12.7 by 50).
That curve only sets entrants' starting overall; the yearly decline is `age_year`, a different function, and survivors
are a selected group (those who kept playing), so this is a shape comparison, not a calibration check. No 50+ major in 57 seasons is not by itself out of line with real golf, where
a major won at 50 or later is very rare. No change is proposed. If Ryan wants more late-career competitiveness, the
candidates are a later technique decline (from `peak_age + 8`) or a slower physical one, each measured first:

- per-attribute decline from the archived development evidence (the aging source, by age and aging rate);
- late-career starts, cuts and retirements (who keeps playing, and why: the survivor curve is a selected group);
- the share of top-20 finishes by age band in Premier events and majors, against a target table Ryan approves.

## 5. Evidence before any decision

1. **Fixed-input replay of generation:** re-draw the 57 Test2 junior cohorts under each option (same seeds, same
   potentials) and compare entry overall distributions, the count of 80+ and 85+ entrants per decade, the readiness
   gap, and how many Cárdenas-like entrants appear. No world is changed.
2. **Fresh-world runs** for the option chosen (two or more seeds, several seasons, as for the nation rules): cohort
   growth arcs (median and 90th percentile overall by age), time to the top 10, and the share of majors won by
   golfers in their first five seasons.
3. **Versioning:** any change would be a new rules version for fresh worlds only; saves from before keep their rules.

## 6. Questions for Ryan

1. How ready should the readiest 18-year-olds be? (For example: at most a handful of 85+ entrants a decade, or none
   above a soft level, with the fastest still able to reach the top by 20-21 through play and training.)
2. Should readiness depend on pathway (college, national programme) or nation development, or be the same everywhere?
3. Is the current decline acceptable, or should late-career competitiveness be measured against a target table?
4. Should the 39-major dominance be treated separately (competition variance, field strength) after generation is
   settled?
