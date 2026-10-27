# Golf Legacy — World Population and Nations

Code: `golfsim/nations.py` (nation profiles), `golfsim/names.py` (names), `golfsim/population.py`
(generator). Report: `python tools/world_report.py` → `reports/WORLD_POPULATION_REPORT.md`.

## What it makes

The starting world for 2027: about **6,200 competitive golfers** from 56 countries, generated in about
2 seconds, the same every time for the same seed. Every golfer has:

- a name in their country's language (no copies of famous real golfers; every name unique),
  nationality, hometown, birth year, height and handedness;
- an archetype, all 21 attributes and a personality (big stage, aggression, adaptability, coachability,
  work ethic);
- a status (professional, amateur or club professional) and a membership (Premier Tour circuit,
  Challenger, Regional or Mini tour, US Division I, US small college or international university golf,
  or a regional amateur series);
- hidden development values for the development system: **potential** (the overall they can reach),
  **prime age** and **aging rate**.

| Level | Golfers | Average overall (default world) |
|---|---|---|
| Premier Tour | 300 | ~74 |
| Challenger tours | ~940 | ~66 |
| Regional tours | ~520 | ~57 |
| Mini tours | ~1,600 | ~54 |
| College | ~880 | ~47 |
| Amateurs | ~1,600 | ~37 |
| Club professionals | ~330 | ~45 |

## No ceiling: eras rise and fall (owner principle)

The world is meant to evolve over centuries with ups and downs, so nothing caps the best players.
Each golfer's talent is drawn naturally from their nation's pool (the only limit is the rating scale's
99). The spread of talent is set so a *typical* world resembles today's game, but any one world — and,
once development is built, any one era — can be weak or golden: across generated worlds the No.1 ranges
from about 89 to 99 (median ~93), and the number of players rated 90+ from none to five. The default world
(seed 2027) happens to start in a down era: its best player is 87.

## How nations work

Every country has a starting **nation profile**:

| Value | Meaning |
|---|---|
| Pool | How many serious golfers the country has (USA 100, Japan 40, England 22, Korea 18 ... Bahrain 0.2) |
| Development | Coaching, facilities, junior programmes and competition, 0–100. Raises how much of their talent golfers realise. |
| Pathway | Access to elite college golf and academies. Decides how many young players reach US college golf. |
| Style | Playing tendencies: power (USA, Canada), links (UK and Ireland), precision (Japan, Korea, China, Taiwan), touch (Spain, Latin America, Italy), complete (Scandinavia, Germany, France...), striker (South Africa, Australia), touch_sea (Southeast Asia, India), raw (emerging golf nations) |

A nation's golfers draw their potential around a mean set by its development; its pool sets how many
there are. So a big country with average coaching (Japan) produces many good players and a few great
ones, while a small country with excellent coaching (Denmark, South Africa) punches above its size.
The starting values were tuned so the world's top 200 matches the real men's world ranking by
nationality (USA ~76, England ~15, Japan, Australia, South Africa, Korea ~10, Sweden, Canada ~6...),
averaged over many generated worlds. Any single world varies, like real generations do.

These are starting values. The **nation-improvement model** (next phase) will move development, pool
and pathway over time from each country's results: a nation whose golfers win big events gets more
juniors, better coaching and better access to college golf a decade later.

## Age

Golfers improve until their prime (around 27, varying by golfer): about 12 points short of their
potential at 18 and 4 short at 23. They hold their level to their mid-thirties, then decline (about 2
points by 40, 7 by 45, 13 by 50), faster or slower depending on their own aging rate. Strength and
stamina fade first; composure and course management keep improving with experience. The world's top
200 average about 31 years old, with about a fifth of the top 25 under 26.

## Status and membership

- Golfers over 22 turn professional if they are good enough (half of them by an overall of 47; almost
  all by 55). The best college-age players may turn professional early.
- Those who don't make it stay amateur (mid-amateurs) or become club professionals.
- Professionals are ranked by reputation (ability plus a little career luck) and fill the Premier Tour
  (the top 300; the best 125 on Premier Tour Americas, the rest on their home circuit), then their
  region's Challenger, Regional and Mini tours. Each Challenger tour is at least 60% from its own
  countries and each Regional tour 75%, with a minimum standard to join.
- College-age amateurs go to US Division I (all Americans and, depending on their country's pathway,
  many internationals), US small-college golf or international university golf.

## Calendar change

A **Japan Challenge Circuit** (12 events, the real ABEMA Tour's place) was added to the calendar, so
Japan's many professionals below the Japan Golf Tour have a home tour. The course library still
covers it within 380 courses.

## Not built yet

- Juniors and high-school golfers (owner decision: later).
- Year-to-year development (training, coaches, aging each season) and the nation-improvement model.
- Career histories before 2027 (past results, past champions): to come from simulating history.
