# Decision evidence (E1): scheduling and career-decision inputs

Recording only. The monthly planner (`Season.plan_block`) and the winter career rules (`careers.decide`)
computed their targets, terms and probabilities and then threw them away; from this build each season file
keeps them, so a report can say *why* a golfer played, trained, rested or worked, and what went into a
retirement, a stop, or turning professional. Nothing is decided differently: no random number is drawn, no
draw moves, no working table gains a key, no iteration order changes, and the rules version
(`golfsim/rules.py`) is unchanged. Seasons played before this build (the pinned A-D runs among them) have no
evidence: their season files have no `decision_evidence` key, and readers return "not recorded" -- the
evidence is never estimated for them.

Code: `golfsim/decision_evidence.py` (record, archive block, reader); recording calls in
`golfsim/season.py` (`plan_block`) and `golfsim/careers.py` (`decide`, and an optional `ev` dict on
`runway_years`, `desire_to_continue`, `p_stop_chasing`, `p_retire`, `p_turn_pro`, `p_amateur_job`,
`p_comeback` that receives each term exactly as computed). Switch: `Season.record_decisions` (on in every
new or loaded world; off keeps nothing and is the previous build's behaviour). Reader:
`Archive.decision_evidence(person, year)` or `decision_evidence.read(season_file, person)`.

## Season file: `decision_evidence`

    {"format": "golf-legacy-decision-evidence/1",
     "definitions": {...every field name, code and scale below...},
     "schedule": {"<person id>": {...one golfer's season of monthly plans...}},
     "careers":  {"<person id>": [[...one career evaluation...], ...]}}

`definitions` repeats the field lists, codes and scales, so a reader takes them from the file it reads.

### `schedule`: the monthly plans

Every active golfer is planned for at weeks 1, 5, ... 49 (13 plans; `plan_blocks`), each plan covering four
weeks (`plan_every`). One record per golfer evaluated, holding columns with one entry per plan (entry k is the
plan made in week `w + 4k`):

| key | field | unit / scale | meaning |
|---|---|---|---|
| `w` | first plan week | week | the week of the first plan recorded (1 for a whole season) |
| `n` | started | starts | events already played this season when the plan was made (pace = target x week / 52 - started; the starts of the previous four weeks = this entry minus the one before) |
| `x` | fatigue | x100 | season fatigue at the plan (0 fresh .. 100 exhausted; the planner rests any week it starts above 25 -- a recorded 25 may be just over or under) |
| `m` | funds_k | $1000s, two significant figures (whole thousands below 100) | spendable funds at the plan (`Season.spendable`: what trips are paid from; may be negative) |
| `c` | weeks | 8 characters a plan | the four weeks' availability (`o` an affordable eligible event, `u` eligible events but none affordable, `e` events at their level in their region but none they may enter, `n` no suitable event), then the activity planned for each week (`P` play, `T` train, `R` rest, `W` paid work); `-` x 8: plan not recorded |
| `d` | dev_train | x10 | the planner's value of a training week this month (development value of training the chosen category, with coaching; scaled down for part-timers) |
| `i` | injured_weeks | weeks | weeks from the plan's first week until they may enter again (0 fit); only present for golfers injured at some plan |
| `f` | flags | bits | 1 `can_work` (paid work was an option: money genuinely short), 2 `stuck` (cannot cover committed costs, or could afford nothing eligible), 4 `major_caution` (a top-100 player with a major in the next weeks), 8 `no_affordable_plan` (no combination was affordable: the fallback plan); only present for golfers with any |
| `t` | target | list, kept when it changes | `[week, role, base, stamina, prestige, target]`: `Season.target_events` by its parts -- `target = base + stamina + prestige`. Roles: `part_time_pro` 6, `part_time_amateur` 8, `club_pro` 12, `college` 24, `amateur` 16 (base only); `premier` 15 + 8 x stamina/100 - 4 when their prestige is 65 or more; `pro` 19 + 8 x stamina/100 |
| `s` | terms | list, kept when any changes | `[week, bar, dev_play, work_value, load4, rest_keep, injury_risk]`, stored as round(value x `term_scale` = 1, 10, 10, 1000, 1000, 10000): `bar` the least event value worth playing (`Season.bar`), `dev_play` the development value of a tournament week, `work_value` the value of a paid work week (-1: not an option), `load4` the fatigue a four-round week adds, `rest_keep` the share of fatigue kept after a rest week (recovery), `injury_risk` the injury base x resistance x age x stamina factors the planner charges a playing week (times 1 + 6 x fatigue squared, x 400) |
| `over` | -- | count | plans not kept by the bound (a plan made twice in a week, or beyond 13); absent normally |

The planner's choice for a week to play is `event value - bar + dev_play - fatigue cost - injury cost - net
trip cost`, against `dev_train` (or `work_value`, or a forced rest when fatigue starts above 0.25); the event
values themselves are not kept (see the gaps below), but availability, fatigue, the bar, development values,
injury and money are.

### `careers`: the winter's career evaluations

Each golfer the winter's rules evaluated (`careers.decide`; college golfers are not evaluated for retirement --
the rules give them no chance -- so they have rows only when they graduate). One row per evaluation, at most
three a winter (`career_rows`):

    [model, p, u, outcome, *terms, *inputs]

`p` the probability (4 decimals), `u` the uniform draw it was compared with (the decision happened when
`u < p`), `outcome` 1/0, then the model's logit terms (2 decimals; they sum to logit(p); `None` when the term is
not part of the model in that case) and the inputs behind them that the season file does not already hold
(`None`: not available at the decision). Terms are signed as they enter the logit.

| model | when | terms | inputs |
|---|---|---|---|
| `retire_tour` | full-time professionals and full-time amateurs outside college | `base` -6.5, `age` 0.22 x (age - 30), `standing` 1.2 x (1 - money-list standing), `opportunity` -1.0 x the tier's opportunity, `injury` (0.06 x injury weeks + 0.8 x lasting-damage injuries) | age, tier, money_rank_pct (None for non-professionals: standing 0.5), lasting_damage |
| `retire_job` | part-timers and club professionals | `base` (-4.4 club pro, -2.2 otherwise), `age`, `engaged` (-0.6 x share of target played + top 10s), `drift` (2.4 x chose not to play), `blocked` (0.8 x could not play), `standing` (-1.5 x ranking standing), `progress`, `willingness`, `injury` | age, target, drift, blocked, rank, lasting_damage |
| `stop_chasing` | full-time professionals (after the backers' review) | `base` -4.5, `pressure` 4 / (1 + runway), `short_runway` 2.2 x max(0, 1 - runway), then minus each part of the desire to continue: `progress`, `opportunity`, `secured`, `willingness`, `life` (the pull of an ordinary life by age), `injury`, `lasting_damage` | age, tier, runway (years), shortfall_k (season cost beyond income, $1000s), own_funds_k (None when the season pays for itself), target, lasting, and when they stopped and did not join the staff: p_club, p_amateur, u_where (where they went) |
| `turn_pro` | amateurs graduating from college or outside it | `base`, `standing` (amateur ranking), `means` (savings and family money), `willingness`, `wins`, `age` (None when graduating) | age, graduating, am_rank |
| `amateur_job` | full-time amateurs outside college, 19 or over, who did not turn professional | `base`, `age`, `runway`, `debt` | age, runway, cash_k |
| `comeback` | part-time professionals | `base`, `results`, `funded`, `age`, `injury`, `willingness` | age, top3, progress |

The season's results the models read (events, wins, top 10s, rankings, injury weeks, money) are in the same
file's `careers` rows; age is the season year minus the birth year (`people.json.gz`).

## Bound and size

Rows are bounded by structure: 13 plans per golfer-season (one per monthly plan; a plan made twice, or a 14th,
is counted in `over`, never kept) and at most 3 career rows per golfer-winter, each a fixed width of small
integers, rounded floats and short codes. Measured (one archived season, seed 97, gzip as written):

| world | golfers | season file without | evidence | growth | per golfer-season |
|---|---|---|---|---|---|
| scale 0.03 | 200 | 533,140 B | 28,469 B | 5.3% | 142 B |
| scale 0.10 | 639 | 1,543,866 B | 84,884 B | 5.5% | 133 B |

A mature full world's season file is about 13.5 MB for about 13,200 golfers (about 1 kB each; 2083 in the
50-season world), so at roughly 110-130 bytes a golfer-season the evidence would add about 1.5-1.7 MB a season
(about 11-13%). Most of it is the per-plan columns (fatigue, funds, plan codes, the bar and development
values); the career rows are about a quarter.

## Not recorded (remaining gaps)

- The weekly entry choice: which event a golfer entered among those on offer, the per-event values
  (`Season.event_value`: prestige, travel, streak, pace, major caution, tiredness, defending champion) and
  trip costs. The monthly plan and the week's access outcome (`careers[...]['access']`, `denied`) are kept;
  the event-by-event comparison is not.
- The planner's per-week event values, trip costs, expected prizes and the chosen plan's total value (only
  availability codes, funds and the terms above).
- The coach / caddie career draw when a golfer retires or stops chasing (`staff.former_golfer_role`: its two
  probabilities and draw); the outcome is in the transitions.
- The backers' review (`careers.review_backers`, `p_backers_continue` terms); the transitions keep its outcome
  with backing, progress, places secured and, when the golfer pays their own way, the forecast.
- Inputs a model does not use are not inputs of that decision and are not recorded: turning professional
  reads amateur standing, means, willingness, wins and age -- not earnings against costs or places secured;
  retirement from a tour reads money-list standing, not savings.
