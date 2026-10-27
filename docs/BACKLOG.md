# Golf Legacy — Backlog

Owner requirements and planned work, in rough order. "Built" items link to where they live.

## Built

- Shot-by-shot engine, 21 attributes, archetypes, calibration (`docs/ENGINE_DESIGN.md`)
- World calendar with the four fixed majors and real-life qualifying (`docs/CALENDAR_AND_QUALIFYING.md`)
- 380-course library with layouts and per-layout records (`docs/COURSE_LIBRARY.md`)
- Nations and the world population (`docs/WORLD_POPULATION.md`)
- Season system v1 with event and player prestige (`docs/SEASON_SYSTEM.md`)

## Prestige (owner, recorded for the backlog; first version built in the season system)

- **Every event has a prestige level** from: the quality of the course, the tour playing it, the quality
  of last year's field, and the prize money. *Built:* `golfsim/prestige.py`, updated after every edition.
- **Every tournament stays on the same week every year**, so the "opportunity" events that most great
  pros skip are the same events every season and build their own identity. *Built:* calendar weeks are
  fixed per series (tested); only rotating host cities change.
- **Prestige drives AI decisions on where to play.** *Built (v1):* golfers score each event by prestige,
  home country, travel, fatigue and their season plan; stars set a higher bar, so they skip opportunity
  events. Later: plan whole schedules around majors and favourite courses, play-in-form, defending
  titles, appearance fees, team events.
- **Winning higher-prestige events raises a player's prestige.** *Built (v1):* fame from every finish,
  scaled by event prestige; lasting legacy from majors and flagship wins.
- **Sponsors are driven by player prestige.** *Built (v1):* yearly sponsor income from prestige
  (reported). Next: a real finance model — contracts with brands (clubs, ball, apparel), bonuses for
  wins and majors, contract lengths, a player's money and expenses (travel, caddie, coach), and money as
  a constraint on mini-tour players' schedules.
- **Coaches:** hiring the best coaches depends on money and prestige (owner, career phase).

## Owner principles

- **The world evolves over time, with ups and downs over centuries.** No artificial ceilings or floors
  on talent: a weak era (best player 83) and a golden one (two players at 95) are both fine.
- Event prestige moves slowly (rolling 3–5 years); player prestige over about a year.
- Stamina matters across a season: tiredness affects mostly physical attributes and raises injury risk,
  especially with low injury resistance or older age.

## Next

1. **Player development** (owner): aging year to year, AI training decisions, coach quality and
   recommendations, potential, work ethic and coachability; new juniors entering the world each year;
   college players graduating and turning pro; retirements. Include lasting effects of serious
   injuries (lost power or stamina, re-injury risk) and training load as a source of fatigue.
2. **Nation improvement** (owner): nations' pool, development and pathway move with their golfers'
   results (a nation that wins majors grows more and better juniors a decade later).
3. **Long-term test with development on**: realistic careers and stable long-run trends.
4. **History generation**: simulate decades before the game starts so there are past champions,
   records and storylines from day one.
5. **High-school golf** (owner: later) and junior events.
6. **Storylines and the viewable history** (owner): season reviews, rivalries, streaks, records,
   player career pages.
7. **More courses** (hundreds to thousands; owner) and hand-designed elite courses with named holes.

## Known gaps in the season system v1

- Fields: no Monday qualifiers for regular tour events, no team college golf (players enter as
  individuals), no sponsor invitations beyond a few amateurs.
- The US Open final qualifying draws fewer entrants than real life (about 160 instead of ~900).
- World ranking uses a simplified OWGR formula; amateur ranking a simplified WAGR.
- Weather: wind and rain per round, no per-wave tee times or seasonal weather patterns.
