# Familiarity, course geography and Aggression (roadmap G1, G2)

Rules version **2026-11-08**. Code: `golfsim/familiarity.py`, `Season.course_baseline` and `_for_course`
(`golfsim/season.py`), `course_library.course_place` / `venue_role`, the engine (`golfsim/engine.py`).
Course use and the courses that host no events: `docs/COURSE_LIBRARY.md`.

## Geography that already existed

Birthplace and residence are recorded per person with dates (`docs/RESIDENCE.md`, `Season.places`):
birthplace fixed (country, state / province, or country only when the hometown is not in the geography),
residence changing only by dated moves (`Places.residence_at`). Nothing new is stored on golfers; the
baseline reads `Places`. Courses now record their state / province, normalised from the city with the same
table (`course_place`; `None`, shown "unknown", when the city is not in the geography).

## Familiarity

Familiarity is the competitive rounds a golfer has played on a course (any layout; match-play and playoff
holes count in rounds' worth). The engine turns it into a value, `1 - exp(-rounds / 15)`, which lowers
decision noise (up to 20 %), tightens approaches (up to 2 %) and improves reads on the greens. A caddie's
rounds there add a little more.

### Regional baseline (simulation change)

| Course is in... | Engine is given at least | Familiarity value |
|---|---|---|
| the golfer's birthplace state / province, or the one they live in now | 3 rounds (`REGION_ROUNDS`) | 0.18 |
| the same country, where the state / province is unknown for the golfer or the course | 1.5 rounds (`COUNTRY_ROUNDS`) | 0.10 |
| anywhere else (including another state of the same country) | nothing | 0 |

- **A floor, not a bonus.** The engine is given `max(rounds played, baseline)`. A golfer with 20 rounds at
  their home course gets exactly what 20 rounds give; the baseline never adds on top and never gives more
  than three real rounds would.
- **Counted once.** Birthplace and residence are matched separately and the larger match is used once.
  Someone born and living in Merseyside gets the same as someone who only lives there; a region match and
  a country-only match give the region match, not the sum.
- **No separate home advantage** exists anywhere else in the engine or the season.
- **Dated.** Residence is where they live at the time of the event (`Places.home` then); after a
  move the new region counts, and the birthplace region still does.
- **Honest unknowns.** People whose places were never recorded (legacy) get no baseline; a course outside
  the geography matches by country only.
- **Recorded.** The record of rounds played is unchanged (the floor is applied only to the copy the engine
  plays with). Each season records, per golfer, the starts where the baseline set the value
  (`Season.familiar_base`, archived as the season file's `familiar_base`).
- **Bounded effect.** The whole familiarity effect between 0 and 15 rounds is small (the balance report's
  familiarity section); the baseline is a fraction of it, so it nudges local golfers, it does not decide
  events. Its measured size is one of the checks to run after the CPU hold (below).

### Home clubs (owner decision on unused local courses)

Every golfer whose residence is recorded has a **home club** where they live (`golfsim/home_clubs.py`,
`Season.home_clubs`): a municipal course in their state / province if there is one, else another course
there that is not an elite venue; where the state / province has none (or is unknown), the same choice within
their country. The pick is a stable draw per golfer and place (reproducible, independent of processing
order). It is recorded with its date when they enter the world and again only when they move
(`[year, week, course, basis, place]`; `None` when their country has no course), after each winter's moves.

It feeds only the existing familiarity mechanism: the home club counts as at least `REGION_ROUNDS` like any
course in their own state / province. A club in their own state / province already has that floor, so it
adds nothing there; only a club found by country gains it. Always the larger of rounds played, the regional
baseline and that floor -- never a sum, no separate home advantage, no practice-round count.

Archived as `people.json` `golfer.home_club` (the dated list) and captured live, together with the
golfer's familiarity at the current club recorded explicitly (`golfer.home_club_familiarity`: rounds actually
played there, the rounds and value the engine uses, and their source; `home_clubs.familiarity_at_club`). The
profile names the home club (and earlier ones) and shows those recorded figures -- never a value inferred from
the top-ten list, which a home club may be outside of; with no record, no figure is claimed and the course page counts the golfers whose home club it is. Venue use of local
courses: `docs/COURSE_LIBRARY.md`, "Local hosting".

### Profiles

The playing tab shows the golfer's ten most familiar courses, ranked by competitive rounds actually played
(ties by course id). For each: the rounds played, and separately **the familiarity the engine uses** for
this golfer there -- `1 - exp(-r / 15)` of the larger of rounds played and the regional baseline (own state /
province, country where unknown, or home club) -- with where that value comes from, and a link to the course.
A local golfer with 1 round at a course in their own state shows 1 round played and 18.1 % (the engine's
3 rounds), not 6.4 %. A line states the baseline their birthplace and residence give, naming identical places
once, and the home club is named. A caddie's familiarity is the caddie's own (combined in the engine) and is
not shown here. The live view captures the top ten now; archived histories carry the top ten as the history
ends (`people.json` `golfer.familiar`, from rules 2026-11-08; older histories say "not recorded").

## Aggression (roadmap G2)

Aggression is the existing 0-100 personality trait, now **shown** on the playing tab ("Playing style":
the value, cautious below 35, balanced 35-65, attacking above 65, and what it means; live view
`aggression`, archived `people.json` `golfer.aggression`). Its effect on play is **unchanged**.

- **A style, not a grade.** Higher is not better. It tilts four choices in the engine: driver off the tee
  (`_tee_plan`), aiming at the flag or the safe part of the green (`_attack_pin`), going for a par 5 in two
  (`_go_or_lay_up`) and attempting the recovery from the trees rather than punching out.
- **Stable.** Set when the golfer enters the world (`population._personality`), never written again:
  aging (`development.age_year`), injuries (`serious_injury`), results and careers change attributes,
  never personality. An aging attacking golfer stays attacking.
- **Reach is physical.** `_reach` is the longest full shot from that lie (3-wood from the fairway, less from
  rough or a fairway bunker) and follows distance: Power (which declines after the prime and with long
  injuries) and season fatigue. A shot beyond reach is always a lay-up, however aggressive; Aggression only
  weighs choices that are possible, and Course Management sets how well they are judged. So the older
  attacker still goes for the par 5s they can reach and lays up at those they no longer can. The decision was
  moved into `_go_or_lay_up` / `_reach` without changing it (288 rounds identical to the previous engine,
  same seeds) so the interaction can be tested directly. Both take `dfac`, the shot's effective-distance
  factor for the conditions (1.0 = calm, the current engine): a caller with wind (the weather package)
  passes its wind-adjusted factor so reach is the physical reach in those conditions.
- **No second risk score.** None was needed: what a golfer can sensibly attempt already follows from their
  physical state and course management.

Tests: `tests/test_aggression_visible.py` (reach and aggression, no decline with age or injury, no code that
writes a trait, no risk score, profile text and rule text).

## To run after the CPU hold

- Full test suite; observer/archive integration tests.
- A seeded season with and without the baseline (same seed; `Season.familiar_base_on = False` for the second arm): starts affected (`familiar_base`), the change in
  scoring average for local golfers at regional events (expected a few hundredths of a stroke), timings.
- `tools/equivalence_check.py` and the determinism replay with the new rules version.
- In that season: home clubs given to every placed golfer (basis region / country counts), moves giving new
  ones, archive `golfer.home_club`; venues of the first season against the library replay (local hosting);
  course pages of an adopted municipal course and of a home club.
