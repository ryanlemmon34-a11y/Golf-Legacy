# Readiness, generation and decline: a proposal for discussion (no change made)

**Status.** Discussion only, under the design hold. No decline, generation or potential change is implemented, and
no new balance experiment will be run without Ryan's approval. This note describes the current model (as coded on
build/v17-integration 18a8e23), the Test2 evidence, the questions a study would have to answer, and the evidence it
would need. Figures marked *(brief)* are from HAL's review brief on Test2; the rest are read from the code.

## 1. What Test2 shows *(brief)*

- **One extreme entrant.** Cárdenas entered at 18 with overall 96.09 and potential 99 (11 of 21 attributes at 99;
  raw potential 100.881, peak age 20.892, aging rate 0.718, youth gap 1.867). He was the only 85+ entrant among
  16,811 juniors (one in 57 seasons); only 8 entered at 80+. He peaked at 98.1 at 23, won 39 majors, spent 689 weeks at
  No. 1 (last major at 47, last Premier win at 52) and retired at 60 after five starts in his last season (one cut,
  world ranking 1117).
- **Ordinary development already includes rapid organic growth.** The mature 4,814-junior cohort's peak age median is
  28; juniors with potential 80-90 (n = 31) start at a median 72.27 and reach 83.2 at 31; arcs such as 74.86 -> 91.5
  at 34 and 60.94 -> 81.8 at 34 exist.
- **Decline among survivors.** Overall change 30 -> 40: -3.6; 40 -> 50: -9.6; 50 -> 60: -13.4. Nine Premier or major
  wins by golfers aged 50+ across 2,280 such events; none in a major.
- **Separate question.** The 39-major dominance is also a competition-calibration question (field strength,
  variance) and is kept apart here.

## 2. How the model makes these (as coded)

**Generation** (`population.candidates`, `_make_golfer`). Each candidate draws a potential (normal around the nation's
development mean), a peak age `~ N(27, 2.0)` (unbounded) and an aging rate (lognormal, sd 0.3). The current overall is

    current = min(99, raw potential - age_deficit(age, peak_age, aging_rate) + career luck)
    age_deficit: young part 0.36 x (peak_age - age)^1.55; old part 0.15 x aging_rate x (age - peak_age - 7)^1.6

and only afterwards is the stored potential set to `min(raw potential, 99)` (raised to the current overall if that
is higher). Two consequences:

- **Readiness at entry is not a quantity of its own:** an 18-year-old's distance from potential is set by how far the
  peak age is from 18. A typical peak at 27 leaves about 10.9 points to grow (0.36 x 9^1.55; the docstring rounds to
  ~12); a peak at 20.9 (about three standard deviations early) leaves 1.9.
- **Cap order.** The deficit is subtracted from the *raw* potential before the 99 cap, so a raw potential above 99
  partly offsets the youth deficit. For Cárdenas (raw 100.881, deficit 1.867, career luck about -2.92) this gives 96.09;
  capping first (99 - 1.867 - 2.92) would give 94.21. This is an inconsistency worth fixing in any study, but it is not
  a complete answer: 94.21 is still the only such entrant and still a near-finished 18-year-old.

The ceilings (`init_ceilings`) spread the gap over the attributes (wider for physical in the young, for mental at all
ages), capped at 99.

**Growth** (`development.develop_week`). Each week closes a *fraction* of the gap to the ceilings: the gap times a base
rate (0.016 a training week, 0.008 a tournament) times a learning rate that is highest at 18-21 (1.2 -> 1.15) and falls
with age (0.6 at 30, 0.25 at 40), times work ethic and coaching; tournaments teach the mental game; the young also
mature physically every week. A high learning rate does not guarantee that a gifted 18-year-old reaches elite level by
20-21: it closes part of the remaining gap each week, and the gap shrinks as it closes.

**Decline** (`development.age_year`). Once a year: physical attributes fall from `peak_age + 3`
(-0.30 x rate x years^0.7), technique from `peak_age + 8` (-0.15 x rate x years^0.7); the mental game keeps maturing
with competitive experience until 48 and declines after 55. Serious injuries can remove some physical attributes
for good. The same peak age therefore sets both how ready a young golfer is and when they decline.

## 3. What a study would compare

Constraints (brief): separate readiness from potential, keep organic rapid growth, keep rare already-elite teenagers
possible and keep late bloomers, no hard age or overall cap and no universal cliff. During the comparison growth and
decline stay as they are; only how an entrant's starting point is drawn changes.

| | Model of developmental tempo | What it would mean | Questions it raises |
|---|---|---|---|
| **0** | **No change (the baseline)** | Readiness follows the peak-age draw; raw potential before the cap | The reference every alternative is measured against |
| 1 | Cap order corrected only | Cap potential at 99 before subtracting the deficit | Small effect at the very top (Cárdenas 96.09 -> 94.21); no change to tempo |
| 2 | Independent readiness | Readiness drawn separately from potential and from the peak age (which keeps setting decline) | If its distribution is unchanged, rare ready teenagers stay exactly as rare; decoupled from decline, an early-ready golfer with a late decline could dominate for longer, not shorter |
| 3 | Weakly correlated tempo | One latent "developmental tempo" that sets both readiness and the timing of decline, with only a weak tie between them (or a shared tempo with independent noise) | Gives a coherent trajectory: early-ready golfers tend, but are not forced, to peak and decline earlier; the strength of the tie is the open parameter |

Bounding the peak-age draw (truncating `N(27, 2.0)`) is not proposed as a fallback: it moves decline timing too and is
close to an age rule. No option is recommended yet; the comparison is what the study would decide.

No target is set for how many very ready entrants there should be. This save had one 85+ entrant in 57 seasons; a
target such as "a handful a decade" would make them more common, not rarer, and has no support here.

## 4. Decline: what to look at before any change

The survivor curve (-3.6 / -9.6 / -13.4 a decade from 30) has the same shape as the creation curve the model uses to
set starting ratings (below potential at aging rate 1 and peak 27: about 2.6 by 40, 7.0 by 45 and 12.7 by 50). That
curve only sets entrants' starting overall; the yearly decline is `age_year`, a different function, and survivors are
a selected group (those who kept playing), so this is a shape comparison, not a calibration check. No 50+ major in 57
seasons is not by itself out of line with real golf, where a major won at 50 or later is very rare. No change is
proposed. If Ryan wants to look at late-career competitiveness, the measurements would come first:

- per-attribute decline from the archived development evidence (the aging source, by age and aging rate);
- late-career starts, cuts and retirements (who keeps playing, and why: the survivor curve is selected);
- the share of top-20 finishes by age band in Premier events and majors, against a target table Ryan approves.

## 5. Evidence a study would need (only with Ryan's approval)

1. **A coherent latent trajectory:** for each candidate model, the implied overall at 18 and at later ages (21, 25,
   30, 35, 40) under the unchanged growth and decline, so readiness, peak and decline are seen as one path.
2. **Generation replay including selection:** re-run candidate generation for the 57 Test2 cohorts with the same seeds
   -- the candidate pool, career luck, scouting noise and the keep / pass chances that decide who enters -- not only
   re-score the juniors who were kept. A change in readiness changes who is kept, so a held-cohort replay alone would
   mislead.
3. **Fresh-world runs** for any option taken forward (two or more seeds, several seasons, like the nation A/B, with
   only the generation flag differing): growth arcs (median and 90th percentile overall by age), time to the top 10,
   majors won in a golfer's first five seasons, and how long the most dominant careers last.
4. **Versioning:** any change would be a new rules version for fresh worlds only; saves from before keep their rules.

## 6. Questions for Ryan

1. Is a study of developmental tempo wanted at all, or is the current generation (one Cárdenas in 57 seasons)
   acceptable as a rare event?
2. If studied: should readiness and the timing of decline be tied (option 3) or independent (option 2)?
3. Should the cap-order inconsistency be corrected on its own (option 1), as a small consistency fix for new worlds?
4. Should readiness depend on pathway (college, national programme) or nation development, or be the same everywhere?
5. Should late-career competitiveness be measured against a target table before any decline change is considered?
6. Should the 39-major dominance be treated separately (competition variance, field strength)?
