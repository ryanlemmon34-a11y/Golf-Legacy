# Attribute map: where each rating acts (engine of main `18a8e23`, identical to the save's `c0d1ea5`)

Line numbers refer to `golfsim/` at `18a8e23`. The scoring files (`engine.py`, `tournament.py`, `ratings.py`,
`weather.py`, `golfer.py`, `course.py`, `baseline.py`, `familiarity.py`) are byte-identical at `c0d1ea5`.

`R.X` is a piecewise-linear table in `ratings.py` (`interp`), clamped outside 0–100, and `norm(r) = r/100`.

Classes:

- **D**: direct, every round. The attribute changes a shot parameter whenever its shot type occurs.
- **C**: conditional. It acts only in some situations: pressure, wind, wet, round 2–4, trouble.
- **I**: indirect. It never touches a shot, only availability (fatigue between events, injury), planning,
  development or careers.

`OVERALL_WEIGHTS` (`golfer.py:12`) say how the Overall rating is computed. They were set from measured stroke
values in calm, pressure-free conditions (`tools/balance_test.py`). They are **not** contributions to winning:
winning also depends on variance, conditions and field.

## The 21 attributes

| Attribute | Overall weight | Class | Where it acts | Notes |
|---|---|---|---|---|
| power | .146 | D (+C, I) | `R.DRIVE_DISTANCE` → `pl.drive` (`engine.py:195`). | |
| stamina | .045 | D in-round, C, I | Effects listed below the table. | Physical. |
| recovery_rate | .012 | C, I | Effects listed below the table. | **No effect in round 1.** |
| injury_resistance | 0 | **I only** | No engine use. Its only effect is injury chance per event (`season.py:2468`) and the planner's injury risk (`season.py:2998`). | **Zero direct shot effect by construction** (the sanity check). Its value is availability (starts not lost to injury), which a fixed-field experiment cannot show. |
| driving_accuracy | .114 | D | `R.DRIVE_SIGMA` → `pl.sigma`: the tee shot's lateral spread (`engine.py:197`); lay-ups use 0.55·sigma. | |
| long_irons | .068 | D | `R.APPROACH_MULT` → `m_long`, approach proximity from ≥200 yd effective (blended 180–200; `engine.py:198`, `approach_mult`). Also feeds the par-5 go/lay-up value. | **`APPROACH_MULT` is flat (1.05) from 25 to 60:** a change wholly inside 25–60 changes no shot parameter (exact zero, the second sanity check) even though Overall moves. |
| mid_irons | .098 | D | `m_mid` for 140–180 yd (blended 115–140 and 180–200). Also the contact floor, below. | The contact floor is not flat in 25–60, so long_irons' flatness does not carry over. |
| wedges | .051 | D | `m_wedge` ≤115 yd (blended to 140). Also the contact floor and the par-5 lay-up value (`engine.py:467`). | |
| ball_flight | .035 | C (wind, firm greens, doglegs) | Effects listed below the table. | Matters little in calm air. |
| chipping | .064 | D | `R.SHORT_MULT` → `m_chip` (chip proximity and chip-in chance) and `R.CHIP_FAIL` (duffs and thins). | |
| bunker | .025 | D (C: in sand) | `m_sand` (sand proximity, holed bunker shots, fairway-bunker approaches `lie_m = 1.25 + 0.5·m_sand`) and `R.BUNKER_FAIL` (×1.25 on wet sand). | |
| recovery_play | .020 | C (trouble, rough) | `R.RECOVERY_SUCCESS`: shots from the trees (`engine.py:206`, 653–676). `R.ROUGH_SKILL`: approach and around-green penalties from rough, including wet-rough severity. | |
| short_putting | .068 | D | `R.PUTT_SHORT_SHIFT`: make-probability logit shift, full weight ≤8 ft, fading to 28 ft. | |
| lag_putting | .045 | D | `R.LAG_MULT`: leave distance after a missed putt and the make shift on long putts. | Speed control is amplified on fast or sloped greens (`lag^2.5`). |
| green_reading | .050 | D (C: slope) | `R.READ_SHIFT`: make shift scaled by slope and distance. `read_n` lowers the hard-green penalty and the gain from the caddie's reading. | |
| striking_consistency | .028 | D, **variance** | Effects listed below the table. | Acts on **variance** as well as on the mean. |
| putting_consistency | .016 | D, **variance** | `R.PUTT_LAPSE` (lapses on putts ≤8 ft, more under pressure and fatigue). `R.PUTT_FORM_SD` is the SD of the day's putting form; the week's putting form SD is scaled the same way. | Mostly variance. |
| composure | .035 | **C (pressure)** | `pressure_effect = press·(1 − 0.85·composure)(1 − 0.25·big_stage)(1 − 0.07·caddie)` (`engine.py:273`). Pressure widens dispersion (+15%·press) and raises error rates (×(1 + 0.9·press)), chip and bunker fails, and the putting shift. | **No effect without pressure.** |
| resilience | .015 | C (after bogeys) | `tilt_decay = (0.88 − 0.62·resilience)…` (`engine.py:223`). After a bogey or worse, "tilt" builds up (dispersion, errors, putting) and decays by this factor each hole. | |
| management | .038 | D (decisions), C (wind) | Effects listed below the table. | |
| focus | .026 | D (C: wet) | `R.MENTAL_ERROR` adds to the per-shot error chance (`err_p`, with fatigue and pressure terms). In wet rounds its rain discomfort is reduced by focus (`engine.py:216`). | |

**power: details.**

- It also changes:
  - the reach of a 3-wood (`reach_fw = 0.9·drive`), which drives par-5 and long par-4 go/lay-up choices;
  - the effective approach distance `de = dist·(298/drive)^0.5`, so shorter hitters play longer clubs;
  - the fairway-bunker reach.
- Lateral spread in yards grows with distance: accuracy is angular, so `sigma ∝ drive/298` (`engine.py:197`).
- Indirect: season fatigue cuts distance by 3% per unit of tiredness (`engine.py:232`).

**stamina: effects.**

- In-round fatigue: `fatigue_round = (1 − stam)·0.9` (`engine.py:225`), ramping over the 18 holes. It raises
  dispersion (×(1 + 0.08·fat)), errors (×(1 + 0.7·fat)) and the putting penalty (−0.15·fat).
- Rounds 2–4: `fatigue_week` is damped by (1 − 0.4·stam).
- Season fatigue above 0.2 also weighs on it.
- Indirect:
  - fatigue accumulated per event (`season.load`, `season.py:2464`);
  - injury chance (`season.py:2468`);
  - the planner's target number of events (`season.py:966`);
  - training load.

**recovery_rate: effects.**

- Within the week: `fatigue_week = (round − 1)·0.22·(1 − rec)·(1 − 0.4·stam)` (`engine.py:226`).
- Indirect: how fast season fatigue fades during rest weeks (`season.py:2507`) and in planning (`season.py:2979`).

**ball_flight: effects** (`bfc = norm(ball_flight)`).

- **Wind:**
  - the dispersion factor `wind_f = 1 + wind·exposure·(0.55 − 0.40·bfc)…`;
  - it wins back 35%·bfc of the headwind distance loss (`_hole_wind`, `wind_distance`);
  - it reduces gusts (×(1 − 0.30·bfc)).
- Dogleg shaping (`engine.py:590`).
- Approaches to firm or downwind greens (`firm_m` amplification 1.4 − 0.8·bfc).

**striking_consistency: effects.**

- `R.MISHIT_RATE`, the chance a shot is mishit: shorter, double spread, and on approaches mostly short.
- `R.STRIKE_FORM_SD`, the SD of the day's dispersion multiplier, a log-normal.
- The week's strike form SD is scaled the same way (`WeekForm.draw`).
- One third of the contact floor: `R.CONTACT_FLOOR((mid + wedges + strike)/3)` adds a fixed proximity miss
  below 75.

**management: effects.**

- `R.DECISION_NOISE`: noise in club, attack, lay-up and recovery choices, also reduced by caddie strategy and
  familiarity.
- An over-used driver: the penalty `0.10·(1 − mgmt)²` (`engine.py:412`).
- Seasonal wind:
  - `wind_skill = 1 − 0.20·(mgmt − 0.75)`, so better managers play the wind better;
  - gusts ×(1 − 0.20·(mgmt − 0.75)).

## Personality (hidden traits)

| Trait | Shot effect | Class |
|---|---|---|
| aggression | Leans to the driver off the tee (−0.06·aggr), attacks pins (+0.6·aggr), goes for par-5 greens in two (−0.15·aggr) and takes on the miracle shot from the trees (−0.12·aggr). It raises **variance**: more birdie chances and more big numbers. | D (decisions) |
| big_stage | Cuts the cost of pressure (×(1 − 0.25·big_stage)). It also feeds career decisions. | C (pressure) |
| adaptability, coachability, work_ethic | None in a round. They act on residence, staff and development. | I |

The archetypes carry personality bases (`golfer.ARCHETYPES`):

| Archetype | Personality base |
|---|---|
| Aggressive Shotmaker | aggression 85 |
| Power Hitter | aggression 65 |
| Effortless Power | aggression 45, big_stage 70 |
| Strategic Technician | aggression 35 |
| Others | 50 |

Generated golfers draw each trait around the base with N(base, 14) (`population._personality`).

## Other inputs to a round (held fixed in the attribute experiments)

- **Caddie:** green_reading, yardage, strategy, mental_support and course_knowledge, all scaled by communication.
- **Course familiarity:** `fam` lowers decision noise, approach proximity and the wind penalty.
- **Form:**
  - week form: one draw per event, scaled by striking and putting consistency;
  - day form: per round.
- **Pressure.** This is a stroke-play harness (`tournament.play_event`). Pressure is set at the start of each
  round from the golfer's position:
  - round 2 near the projected cut;
  - round 3 within 3 of the lead;
  - the final round within 3 or 6 of the lead.

  It is scaled by event prestige.
- **Conditions:**
  - seasonal wind speed and direction per hole, and gusts;
  - wet rounds;
  - pin difficulty.

  All are shared by every golfer in the round. There is no tee-wave split, and adding one is out of scope.

## Indirect pathways (not in a fixed-field experiment)

- **Development** (`development.py`): every attribute grows and declines through its category (physical, long
  game, short game, putting, mental). Ceilings, training, play growth, aging and lasting injury damage
  (`serious_injury`: power, stamina, injury resistance…) all work through categories.
- **Access and opportunity:**
  - Overall and results decide entry, tours, rankings and money;
  - stamina sets the planner's appetite for events;
  - injury_resistance and stamina set availability.

  Planning also uses composure and management (`careers.py:561`) and big_stage and work_ethic (career
  decisions).

The controlled experiments measure only the direct and conditional shot effects. The archive analyses (fields
as they really were) include the indirect pathways but cannot separate them.
