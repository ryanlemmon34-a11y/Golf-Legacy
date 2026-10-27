# Golf Legacy — Shot Engine Design (v1 prototype)

This document explains how the new engine decides what happens on the course, in plain language.
It replaces the v0.13 "one dice roll per hole" scoring. The v0.13 handoff is preserved untouched in
`legacy/` for reference.

## 0. Core requirement: every shot, everywhere (owner, non-negotiable)

**Every competitive shot in the world is simulated**, at every level, from high-school and local
amateur events through college, mini-tours, Challenger, Premier and the majors. No event, tour or
skill level may be scored with a shortcut (a drawn round score, a per-hole dice roll, or a
"fast-forward" approximation), no matter how many tours, golfers and events the universe grows to.

**A season must still simulate quickly.** As the world grows, speed comes from engineering, never
from cutting golf:

- Compile each golfer's ratings into shot parameters once per round (already done) and keep the
  per-shot work small.
- Play the week's independent tournaments in parallel across CPU cores, each with its own seeded random
  stream, so results stay identical regardless of core count or playback speed.
- Profile the hot loop. Options, in order: tighter pure-Python code, PyPy (free, often several times
  faster on this kind of code), then a compiled core (e.g. Rust) implementing the *same* rules and
  checked against the Python engine with identical seeds.
- Measure season time as the world grows; treat a slowdown as an engineering task, not a reason to
  simplify the simulation.

Current speed: roughly 35-50 microseconds per hole for professionals (about 9 microseconds per shot)
in plain Python on one core. Weaker golfers take more shots per hole, so lower-tier events cost more
per hole.

## 1. Rating scale

Every attribute uses one 0–100 scale anchored to real playing levels (set by the owner):

| Overall | Level | Expected score, mid test course |
|---|---|---|
| 10 | High school, 12–15 handicap | ~98.5 |
| 25 | Good enough to enter amateur events | ~85 |
| 40 | Wins amateur events (≈ scratch) | ~79.5 |
| 50 | Mini-tour professional | ~77 |
| 60 | Challenger tour regular | ~75 |
| 71 | Lower-half Premier Tour pro | ~72.8 |
| 75 | Premier Tour average | 72.0 |
| 85 | Top-10 in the world | ~70.2 |
| 90 | World No.1 level | ~69.2 |
| 95+ | Generational | ~68.1 |

Amateur targets come from real handicap math applied to the test course's measured tournament set-up
(course rating ~78, slope ~147). On the easiest course in the world, Cedar Creek Municipal (rating ~70,
slope ~96), the same 12–15 handicapper averages about 85. Premier Tour players span roughly 66–92,
about 4.5 strokes per round from the weakest member to the best — the same spread as real tours.

## 2. The 21 rated attributes

| Group | Attribute | Where it acts |
|---|---|---|
| Physical | Power | Driving distance, the club hit into greens, reaching par 5s / drivable par 4s |
| | Stamina | Fatigue build-up late in a round and late in a week (and later: across a season) |
| | Recovery | How fatigue carries from round to round within an event (and later: between events) |
| | Injury Resistance | Career/injury system only — no direct effect on a single shot |
| Long game | Driving Accuracy | Angular spread off the tee (longer drives spray further for the same rating) |
| | Long Irons | Approaches from ~200+ yards (own-club distance), long par 3s, par 5s in two |
| | Mid/Short Irons | Approaches from ~140–180 yards |
| | Wedge Play | Approaches inside ~115 yards, pitches and wedge lay-up shots |
| | Ball-Flight Control | Reduces wind effect, shapes around doglegs |
| Short game | Chipping/Pitching | Proximity, duff/thin risk and chip-ins around the green |
| | Bunker Play | Greenside sand (proximity, failing to get out) and fairway bunker approaches |
| | Recovery Play | Trees (punch-out vs hero shot), thick rough, awkward lies |
| Putting | Short Putting | Make rate inside ~8–12 feet |
| | Lag Putting | How far long putts finish from the hole (three-putt avoidance) |
| | Green Reading | Make rate on breaking putts; matters more on sloped, fast greens |
| Consistency | Ball-Striking Consistency | Day-to-day ball-striking form and mishit rate |
| | Putting Consistency | Day-to-day putting form and short-putt lapses |
| Mental | Composure | Size of the pressure penalty (cut line, contention, final holes) |
| | Resilience | How long and how badly a bad hole lingers |
| | Course Management | Quality of strategic choices: club off the tee, attack/centre-of-green, go/lay up, punch out |
| | Focus | Mental-error rate, rising with fatigue and pressure |

Hidden personality (0–100): Big-Stage Temperament (modifies pressure), Aggression (biases decisions
toward risk), Adaptability, Coachability, Work Ethic (the last three are for the career/training system).

The **overall rating** is a weighted average of the attributes. The weights are *measured*, not guessed:
each is that attribute's measured stroke value (75% normal rounds, 25% Sunday-in-contention), from
`tools/balance_test.py --weights-only`. That is what makes golfers of different types but equal overall
score alike on a balanced course.

## 3. How a hole is played

All randomness comes from one seeded random generator, so a seed reproduces every shot.

1. **The day's form.** Each round draws a ball-striking form and a putting form; each tournament week
   draws a smaller week form shared by all four rounds. Consistency attributes control the spread.
   This is how a 71 can have the week of his life.
2. **Tee shot (par 4/5).** The golfer weighs driver, 3-wood and long iron against the hole's width,
   rough and hazards (expected-strokes estimate + management noise + aggression bias). Distance and
   angular spread come from Power and Driving Accuracy, widened by wind (minus Ball-Flight Control),
   pressure, lingering bad holes and fatigue. The ball finishes in the fairway, rough, a fairway bunker,
   the trees, water (penalty, drop) or out of bounds (stroke and distance). Doglegs punish drives that
   run through the corner unless the golfer shapes it. Drivable par 4s can finish on the green.
3. **Approach.** Proximity depends on distance measured in the golfer's own clubs (a short hitter hits a
   longer club from the same yardage), the lie (rough is worse, less so with good Recovery Play), the
   matching iron/wedge skill, firm greens, wind and form. The ball lands in two dimensions around the aim
   point; the golfer either aims at the pin or the safe side of the green. The green's size and the pin
   position decide whether it holds the green, finds sand, water or rough, or leaves a short-sided chip.
   On par 5s the golfer decides to go for it or lay up to a wedge distance. Mishits mostly come up short.
4. **Around the green.** Chips and bunker shots finish at a distance set by skill, lie, green speed and
   slope; they can be duffed or thinned, stay in the bunker, or be holed.
5. **Trouble.** From the trees: punch out safely, or attempt the recovery (Recovery Play sets the odds).
6. **Putting.** Make probability starts from the real tour make-rate curve by distance, shifted by Short
   Putting, Green Reading, green speed/slope, familiarity, caddie reading, today's putting form,
   pressure, lapses and lingering bad holes. Misses leave a comeback putt set by Lag Putting.

## 4. Courses

Holes are described by what changes where shots finish: length and elevation, fairway width, rough width
and severity, what lies beyond (open / trees / water / OB), dogleg bend and where the fairway runs out,
fairway bunkers, green size/speed/slope/firmness, greenside bunkers, water guarding a side of the green,
and wind exposure. Difficulty is never a flat penalty: weak players miss more fairways and greens, so
hazards and fast greens punish them far more.

**Difficulty is skill-dependent.** Fast, sloped greens magnify poor lag putting and green reading; firm
greens magnify weak approach play (high, soft Ball-Flight Control helps); slick chips magnify weak short
games. On a neutral course (like Ashford Ridge) these effects vanish, so the same golfers can be close
on an easy course and miles apart on a brutal one. Drives deep into the trees can be lost or unplayable
(penalty), which is where most of a weak golfer's penalty strokes come from on a tree-lined course.

**Club choice depends on the golfer.** Each hole, the golfer weighs driver / 3-wood / iron against the
hole's trouble *using their own accuracy*. Good course managers follow the sensible plan; poor ones
overuse driver (ego) and make noisier choices. So a long-hitting mini-tour pro who out-drives tour
players on a wide course does not get to swing freely on a tight one without paying for it.

Calibration courses (`golfsim/course.py`):

- **Ashford Ridge** — the hand-built mid-difficulty test course, par 72, 7,174 yards; each hole has a note.
- **Meadowbrook** (easy), **Blackthorn National** (hard), **Old Elm** (tight, tree-lined, tiny greens),
  **Saltcliff Links** (open, firm, windy) — derived variants for course-fit testing.

- **Georgia National** — hand-built, the hardest course in the world (fictional, Athens, Georgia), home
  of the Legends of Golf Masters Event: 7,600+ yards, big elevation changes, pines, water through the
  second nine, the fastest and most contoured greens in golf. Every hole is named and described.
  Calibrated against real Masters patterns by `tools/major_test.py` (winning score, field scoring
  average, cut line, playoffs, favourite and long-shot win rates, number of different champions).

Each course gets a scratch score and a USGA-style slope by simulation, so generated courses can be sorted
from very easy to brutal with evidence.

## 5. Caddies and familiarity

Caddie skills: Strategy (better decisions), Green Reading (helps most on sloped greens and for weak
readers), Yardage (closer approaches, less wind damage), Course Knowledge (stands in for the player's own
familiarity), Mental Support (pressure, bad-hole recovery), Communication (multiplies all of the above).
An average (50) caddie is neutral. Effects are deliberately small and situational.

Familiarity grows with competitive rounds on a course (with diminishing returns) and slightly improves
putting reads, approach distance control and decisions.

## 6. Calibration references

Tour-average (75) targets: ~298-yard drives, ~60% fairways, ~65–68% greens in regulation, ~56–58%
scrambling, ~50% sand saves, ~29–30 putts, ~0.5 three-putts per round, ~3.5–4 birdies per round, round
standard deviation ~2.8–3.0. Strokes-gained uses an approximation of the published PGA Tour shot baseline
(Broadie). The amateur scale uses USGA course-rating/slope logic. See `reports/BALANCE_REPORT.md` for the
current measured values.

## 7. Known limitations of this prototype

- Pressure in the tournament harness is set from the position at the start of each round; the full world
  engine will feed it live from the chronological tee sheet (v0.13's best feature, to be carried over).
- Weather is wind speed and rain only; no per-wave weather or seasons yet.
- Distance may still be ~20–40% more valuable than real-world estimates; revisit once world-level
  season stats exist.
- Amateur levels (10–40) are calibrated to ±1.5 strokes; professionals to ±0.5.
- Stamina/Recovery mostly matter across weeks and seasons, which needs the calendar/season simulation.
- Performance: ~35–50 microseconds per hole in pure Python (≈2–3 minutes of scoring for a 6,000-golfer
  season on one core; independent tournaments can run in parallel).

## 8. Next: the world course library (planned)

Hundreds, then thousands, of fictional courses, each in a real city where that style makes sense:
links on the Scottish and Irish coasts, sandbelt in Melbourne, desert in Arizona and the Gulf, mountain
courses in Colorado and the Alps, tropical resorts in Florida, Thailand and Hawaii, parkland and
woodland across Europe, North America and Japan.

- **City database:** real cities with country, region, climate and terrain tags, and a weight for how
  much golf the country has (the USA, UK, Japan, Canada, Australia, etc. get the most courses).
- **Style templates:** each style sets realistic ranges for length, width, rough, trees/water, bunkering,
  green size/speed/slope/firmness and wind; course class (championship / member / resort / municipal)
  sets length and set-up.
- **Hole-by-hole generation** with a sensible par mix and routing variety, fictional local-language
  names, opening year and a fictional architect (later: renovations as versioned layouts).
- **Automatic rating:** every generated course is simulated with benchmark golfers to get its scratch
  score and slope, so the world can be sorted from very easy to brutal with evidence.
- **Hand-built legends:** the major venues (Georgia National plus rotating pools for the other three
  majors) and a handful of famous national-open courses are designed by hand like Georgia National.

## 9. Owner requirements recorded for the career/training phase (not built yet)

- AI golfers decide their own training focus; the human player sets it monthly.
- Coaches recommend training. Better coaches pick the right training at the right time (coach skill
  drives recommendation quality — separate from how well they teach).
- Hiring a top coach depends on both money and the golfer's prestige.
- Prestige is built by winning, weighted by the prestige of the event won.
- The expanded attribute list gives more distinct things to train.
