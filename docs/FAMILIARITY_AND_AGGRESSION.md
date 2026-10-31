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

## To run after the CPU hold

- Full test suite; observer/archive integration tests.
- A seeded season with and without the baseline (same seed; `Season.familiar_base_on = False` for the second arm): starts affected (`familiar_base`), the change in
  scoring average for local golfers at regional events (expected a few hundredths of a stroke), timings.
- `tools/equivalence_check.py` and the determinism replay with the new rules version.
