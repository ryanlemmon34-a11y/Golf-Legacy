# Career roadmap: implementation status, dependencies and engine contracts (updated 2026-11-16)

Verified baseline `wip/consolidated-career-update` @ 8580171 (full per-module regression, docs below). Bounded
completion on `feature/career-completion` (from 8580171): course fit on selected rows, living history, period
scouting with growth room, entry outlook, coach's advice. **Not ready for Ryan's test until the combined regression
and HAL's UI wiring are verified.** HAL owns UI; Claude owns engine, persisted decisions and evidence, and the read
models below.

Status words: **done** (engine and tests on this branch), **partial**, **in progress** (this checkpoint),
**not implemented**, **blocked** (needs a decision or input), **deferred** (long-term, not to be raced).

## Inventory

| item | engine status | notes / owner |
|---|---|---|
| Truthful entry reasons, closeness only from decision-time data | **done** (355555d) | `career.week_entry`, `ENTRY_TEXT`; older weeks `recorded: false`. HAL renders (8d02cb7). |
| Truthful entry *chances* before deciding (forward-entry expectations) | **done: history plus qualitative outlook (no chances)** (feature/career-completion) | `week_compare` play rows' `entry_outlook` (docs/career/ENTRY_OUTLOOK.md): the golfer's entry class now against how the field closed last edition; `unknown` with the reason when unsupported; measured calibration in the doc, never shown as numbers. |
| Default "yes" acceptance (selected / qualifying) | **partial** | Engine takes whatever policy is posted; the default is the form's (HAL). Engine default when a policy is omitted: not added (would change the command contract) — can add on request. |
| Visible current qualifications and placement unlocks | **done (engine read model, first version)** | `golfsim/opportunities.py`: `career.view()['opportunities']` from the implemented routes (major exemptions with their stated finish, qualifying stages, qualifier targets); status already_qualified / needs_result / awaiting_selection / not_eligible. Tour cards and winner exemptions held: HAL's `career_context`. US college qualifiers plug in when built. |
| Early invitation notices | **done (decided places only)** | At each period start a notice (`kind: 'secured'`) for each place now held on recorded facts and not noticed before (`opportunities.held_places`: major exemptions, earned qualifying places, a v3 college championship place), with its route; exactly once (`career.secured_seen`) across reloads and interruptions. Nothing is announced about places not yet decided. |
| Usable coach / caddie offers | **done (reworked)** | Market offers answered at the same point of the 1 January market as an AI golfer's (probe on a copy; same draw); the earlier holds were withdrawn after the parity audit. Paired human/AI tests. |
| Player choosing staff themselves (hire a coach/caddie) | **done (engine)** | `staff_policy` command: seek_coach / seek_caddie = 'no' (default, earlier behaviour) / 'yes' / 'ask'; coach_approaches / caddie_approaches = 'ask' (default) / 'decline' (every market approach answered no, as on the spot) (the 1 January market stops with a `market_choice` decision, yes/no). Looking runs the AI's own search: same ranking, same coaches' and caddies' answers. `career.view()['staff_policy']`. |
| Thirteen fixed four-week periods; interruptions resume within the period, one recap | **done (verified)** | tests/test_period_cadence.py. |
| Editable four-week plan accepting coach advice | **done (engine advice: feature/career-completion; UI wiring: HAL)** | `career.view()['advice']` (docs/career/COACH_ADVICE.md): play / train / rest per open week from stakes, pathway, entry outlook, course fit, cost, load, fatigue formulas, visible weakness, perceived growth room and coach speciality, by fixed rules; read only; the suggestion is a valid plan. Replaces HAL's interim helper's rules once wired. |
| Season results / season review | **done** | `year_end.review` (YEAR_END.md), weekly recaps with entry evidence. |
| Factual inbox / calendar / recaps | **partial** | Engine: notices, log, decisions, recaps, planner, `week_entry`. Inbox/calendar presentation: HAL. |
| Trophies (majors, college, amateur championships) with engraving and multi-win history | **done (engine read model)** | From recorded winners only (`ctx.results` keeps every winner for good). Contract below. |
| Per-category fallible potential letter grades | **done (engine read model; period cadence and growth room: feature/career-completion)** | `golfsim/scouting.py`: looks at control start, each period start, the first week after a coach change and the season's end (the career's gate only); level read over 12 weeks of looks, trend over at least 26 weeks; the judge's seeded persistent error; never ceilings or potential. Grades A/B/C/D/F only; `growth_room` qualitative with uncertainty and basis; `unknown` without evidence. |
| Optional goals | **done (engine)** | `set_goal` / `drop_goal` commands (versioned, exactly-once), at most 5 active; kinds win / play_in / world_rank / amateur_rank; status derived from records; read by no rule (tested: world unchanged). `career.view()['goals']`. |
| Relationships, timeline / living history | **done (engine read model; tour and injury history: feature/career-completion)** | `career.view()['timeline']`: control stints, answered decisions, trophies, wins and top-10s, coach/caddie partnerships, tour / status transitions (`career.status_log`, logged once when first seen under control; nothing earlier inferred), injury onsets (from the weekly recaps' onset episodes, once each), from records only. |
| Course fit and recorded familiarity in event choice | **done (v3; owner-authorized 2026-11-15)** | docs/career/COURSE_FIT.md; selected rows too (feature/career-completion). |
| Distinctive fictional tournament names | **done (v3 new worlds)** | golfsim/event_names.py: the ordinary numbered events get place names (town + optional course feature + kind suffix), deterministic, unique, no real brands, places tied to famous real events avoided; ids, weeks, venues, Premier/anchor names unchanged; v1/v2 unchanged. |
| College qualifier overhaul (4 early-spring qualifiers, 39 each, all US college tours, heats) | **done (engine), calendar v3** | docs/career/COLLEGE_QUALIFIERS.md; `schedule.NEW_WORLD = 'v3'` for the app (HAL: observer_app new-world calendar); engine DEFAULT stays v2; v1/v2 unchanged. |
| Same-year USA Open place for the college national champion (amateur) | **done (v3), enabled 2026-11-15 on HAL's final-scope confirmation** | Route `U2C`: championship (week 22) before final qualifying (24) and the Open (25); amateurs only; tests for timing, status, no invented place, the World University champion not included. |
| Finance trace | **done (engine read model)** | `career.view()['money']`: funds now (cash, family backing, backers' money, spendable), this and last season's ledgers line by line (null when nothing was booked), golfsim/career_money.py. |
| Sponsor / backer explanations | **done (engine read model, first version)** | `money.sponsor` (contract, Prestige, the rule) and `money.backer` (deal, put up / returned this season, last deal ended). |
| Annual tracking | **done (engine read model)** | `career.view()['seasons_summary']`: one row per controlled season (events, wins, top 10s, prize money, ranks), from the recorded weeks. |
| Old-save continuation (Patrick / CareerTest saves) | **not a release requirement (Ryan, 2026-11-15); not enabled** | Source engine 57c4719 is `rules_changed` (fatigue fix); migration proposal only (ENGINE_MIGRATION.md). Not enabled. |
| Encyclopedia entry | **deferred** | After career testing (BACKLOG item 6). |
| Performance target (120 s) | **no regression measured; target not re-measured** | Same container, same seed (11), full scale, 1 worker, regression run paused, all-AI season 1 (52 weeks + winter + save, generation/creation excluded): 5582e27 v2 238.6 / 233.8 s; 9aa0273 v2 236.1 / 233.6 s (identical digest 63c8b06b…); 9aa0273 v3 241.4 / 235.2 s. The 120 s target is defined on the owner's 16-worker machine (BACKLOG: season 1 measured there at 47.9 s); not comparable to this container. |
| Commercial: Steam, Birth (origin) mode, mods | **deferred (long term)** | Not part of this update. |
| Automatic world prologue | **not approved** | Not built. |

## Dependency plan (engine) — as built

All seven original steps are built: consolidation; trophies; potential estimates; qualifications read model and early
notices; timeline and goals; the college qualifier overhaul (v3, U2C on); staff hiring, finance trace, sponsor
explanations, annual tracking and fictional names. The bounded completion (feature/career-completion) was built in
this order: course fit on selected rows (needs course fit); living history (needs the timeline); period scouting and
growth room (needs scouting); entry outlook (needs field history); coach's advice (needs all of these). Open: HAL's UI
wiring of the new keys; the combined regression; the encyclopedia (deferred); commercial items (deferred).

## Engine contracts (agreed shapes, engine side)

All read only, in the committed career view (`career.view`) or callable on the committed snapshot; every key always
present; `null` = not available (e.g. an older save), `[]` = none.

### Trophies — `career.view()['trophies']` (HAL's shape, extended)

```
trophies: [ {event_id: "2029:USA_AMATEUR", series_id: "USA_AMATEUR", event_name: <contextual label>, year: 2029,
             winner_id: 8291, winner_name: "Reed Mann", kind: "major" | "college" | "amateur",
             times_won: 2,                       # this golfer's wins of this trophy up to and including this year
             during_control: true} ]             # won while the player controlled them (stints)
```
For the controlled golfer (all their recorded wins, before or during control). `null` only if the career is gone;
`[]` if none. Trophies: the four majors (`kind 'major'`); College National Championship, Small College National
Championship, World University Championship (`'college'`); elite and national amateur championships (`'amateur'`).
Regionals, conference events and qualifiers are not trophies. Engraving: `golfsim.awards.engraving(season,
series_id)` -> `[{year, winner_id, winner_name}]` oldest first (every recorded year of that trophy in this world).
Ties are decided by the event's own playoff (one winner per edition); multi-site events have no trophy.

### Potential estimates — `career.view()['scouting']` (implemented)

`as_of` is a list `[year, week]` (not an object); `grade` is one of `A`, `B`, `C`, `D`, `F` (no `E`) or `null`.

```
scouting: { as_of: [year, week] | null, source: "coach" | "self" | null, judge: name | null,
            categories: [ {category: "putting", grade: "A".."F" | null, confidence: "low" | "medium" | "high" | null,
                           growth_room: {label: "little"|"some"|"considerable"|"unknown",
                                         uncertainty: "narrow"|"moderate"|"wide"|null,
                                         basis: ["age_curve", "observed_trend"?, "coach_read"|"self_read"], explanation},
                           evidence: {observations, looks_in_read, span_weeks, trend_available, trend_weeks},
                           explanation: str | null, history: [{year, week, grade, reason}]} ] }
```
Looks (`reason`): `start` (control starts), `period` (each period start), `coach_change` (the first week after the
coach changed), `season_end`; written by the career's gate as the world advances, never by a read, each with its own
seeded observation error. The level read is the mean of the looks of the last 12 weeks; the observed trend needs at
least 26 weeks of looks (the look nearest a season back, annualised). Grade from the projected category level: the
level read + the development still typical for the age (the youth part of the public age curve only: nothing from 27
on; old-age decline is never counted as room) + the observed trend (before 27: faster or slower than typical; from 27:
only improvement actually seen), through the judge's scouting error (a seeded,
persistent per-judge view; firmer the more seasons watched). `growth_room` is that projected gain in words (little up
to 1.5, some up to 5, considerable above), with uncertainty from the judge's remaining error (one step wider without
a trend) -- never a ceiling and never a grade minus a level. Never reads ceilings or potential. `grade: null` and
`growth_room.label: 'unknown'` when nothing has been observed (or a read from an older build lacks it). The read's
explanation states the age curve's sign ("typically still gains", "at their peak", "typically loses"). Grade colours
are HAL's.

### Opportunities — `career.view()['opportunities']` (implemented)

`[{event: {id, series_id, label, week, year}, condition: {kind: 'win'|'finish'|'qualifying_place', text,
positions: [..]|null, top: n|null, places: n|null, site_places: [..]|null}, target: {id, series_id, label, week,
year}, route: {code, label, source}, status: 'already_qualified'|'needs_result'|'awaiting_selection'|'not_eligible',
restrictions: [str], decided: null}]`, for events from the current week to the season's end, sorted by week.
Only implemented routes (qualification._rules, qualification.stages, event_labels.target); `top` and `positions`
come from the route's own selector; a qualifier whose places the rule does not state as a number has
`places: null` and the text "finish in a qualifying place (the field rule)". `already_qualified` only on recorded
facts (`qualification.secured_places`, `earned_exemptions` as of now). Read only; no random draw.

### Week comparison — `golfsim.decision_support.week_compare(season, career, golfer, year, week)` (implemented)

`{week, year, play: [{event_id, name, eligible, why, cost, tour, selected_field?, opportunities: [...], last_edition
(ordinary rows), course_fit (COURSE_FIT.md; selected rows too), entry_outlook (ENTRY_OUTLOOK.md)}],
train: [{category, grade, confidence, observed_level, weakest_rank, observed_as_of}], rest: {fatigue_after},
load: {fatigue, performance_threshold, train_fatigue_after, rest_fatigue_after, played_last_4, played_last_8,
injured_until, recorded_weeks}}`. Grades and levels are the career's recorded observations (scouting), not
ceilings; fatigue forecasts are career.readiness's (the engine's own formulas).

### Timeline — `career.view()['timeline']` (implemented)
`[{date: [year, week], kind: 'control'|'decision'|'trophy'|'result'|'staff'|'tour'|'injury', text, golfer_id}]`,
oldest first, from records only (golfsim/career_story.py). `tour`: a status / tour / lifestyle change from
`career.status_log`, dated when the career's gate first saw it (week 53 = the winter); the first sight of a golfer is
a baseline, never a transition. `injury`: one per onset episode kept in the weekly recaps.

### Coach's advice — `career.view()['advice']` (implemented)
See docs/career/COACH_ADVICE.md for the contract and rules; `null` outside an active career's open weeks.

### Goals — `career.view()['goals']` (implemented)
Commands: `{schema: 1, type: 'set_goal', goal: {kind: 'win'|'play_in', series_id, by_year} | {kind: 'world_rank'|
'amateur_rank', top, by_year}, version}` -> `{ok, goal: 'G<n>'}`; `{schema: 1, type: 'drop_goal', goal_id}`.
View: `[{id, kind, series_id?, label?, top?, by_year, status: 'active'|'achieved'|'missed'|'dropped', achieved:
[year, week]|null, progress: {position}|null, set: [year, week], golfer_id}]`, newest first. No rule reads goals.

## Course fit and familiarity in event choice (2026-11-15, owner-authorized addition)

Calendar v3 only. A bounded term in every golfer's event appeal (−3..+5 points), with the same number shown to the
player as `week_compare[week].play[i].course_fit`. The v3 golden was re-baselined as an intended change; the v2
goldens are unchanged. See COURSE_FIT.md.
