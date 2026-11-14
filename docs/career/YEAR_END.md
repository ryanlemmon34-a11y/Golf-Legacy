# Career year end — engine flow and UI contract

Branch `feature/career-year-end` (from `ui/career-experience-v2` 30b9fed, plus the UI dropdown commit d890ab9
cherry-picked unchanged). The engine owns this; HAL owns every page. Nothing here changes `tools/observer_career.py`.

## The stages

The cursor stays at week 52 `'end'` through the winter while a golfer is controlled; the winter runs in three parts
(`Season.winter_part`, the same code in the same order as the all-AI winter `Season.end_of_season`), with the
player's stages between them. Every answer is a committed `decide` command; every stage survives a save and reload.

| # | cursor | stage (`year_end.stage`) | what happens |
|---|---|---|---|
| S0 | 52 end, parts done 0 | `season_review` | **Annual intent**, before any of the winter: `keep`, `switch` or `end_career`. Pending offers must be answered first. |
| S1 | — | (engine) | Winter part 0, *close*: standings, snapshot, college record, tour cards, prestige, caddie reputations. |
| S2/S3 | 52 end, parts done 1 | `winter_choices` | Kept golfer only: `winter_career` (their path for next season) and `winter_staff` (keep or let go). A stage with one possible answer is answered automatically, with a notice. |
| S4 | — | (engine) | Winter part 1, *decide*: every golfer's career decisions (the controlled golfer's are the player's answers, applied by the same functions), aging, the new junior class and late entrants, the staff year. |
| S5 | 52 end, parts done 2 | `winter_residence` | Kept golfer only, and only when the residence rule names a better home: `stay` or `move:<country>`. Unaffordable: stays automatically, with a notice. |
| S6 | — | (engine) | Winter part 2, *settle*: residence moves, staff moves, settlement; archive; cursor → next year week 1 `'start'`. |
| S7 | next year 1 start | `choose_newcomer` | After a switch, or when the kept golfer retired or died over the winter: one of ten juniors of the new class, or `end_career`. Before anything of the new season runs. |

* **Switch** ends the stint at once (`to: [year, 52]`); the career is `'choosing'`; the former golfer is an AI golfer
  for the whole winter (the player never makes their winter choices) and afterwards. Stage `winter_ai` until 1 January.
* **End career** at S0 or S7: status `'ended'`, every golfer under AI control, nothing resurrected later.
* A **retirement** the player chose (or a death over the winter) closes the stint `to: [year, 53]` and leads to S7.
* Old saves holding a pending `season_end` stop (format 1 builds) still get that stop answered as before (`return_to_ai`).

## Commands (schema 1, unchanged)

All through the existing endpoint: `{"schema": 1, "type": "decide", "decision": "<id>", "answer": "<key>", "version": <career version>}`
with the cursor `expected` and an `op_key`, exactly like offers. The server's `/career/decide` already passes
`decision` and `answer` through unchanged. Exactly-once: an op_key replay returns the first result; a stale `version`
raises `StaleCareer`; a stale cursor `StaleCursor`; a resolved decision is never answered twice; an answer outside
the decision's `options` is refused; a year-end answer outside its stage is refused.

* `season_review`: `keep` | `switch` | `end_career`
* `winter_career`: one of the decision's option keys (see below)
* `winter_staff`: `keep` | `let_go_coach` | `let_go_caddie` | `let_go_both` (only those that apply)
* `winter_residence`: `stay` | `move:<country>` (exactly the option given)
* `choose_newcomer`: the candidate's golfer id **as a string** (e.g. `"1749"`) | `end_career`
* While `'choosing'`, only the `choose_newcomer` decision is accepted (no plan, no end_control).

`winter_career` keys by situation (the first always changes nothing):

| golfer | keys |
|---|---|
| college amateur under 22 | `stay_in_college`, plus `turn_pro` when the early-pro rule allows (winner's exemption or amateur top 15) |
| college amateur at 22 | `amateur_with_job`, `turn_pro` |
| other amateur | `continue`, `turn_pro`, `take_job` (full-time, 19+) or `return_full_time` (part-time, when the amateur-return rule is on and not blocked), `retire` |
| part-time professional | `continue`, `comeback`, `retire` |
| full-time professional | `keep_chasing`, `club_pro`, `regain_amateur`, `part_time_pro`, `retire` |
| club professional | `continue` (answered automatically) |

## The read model: `career.view(...)['year_end']`

Inside the committed career view (the one observer_live already snapshots), so the renderer never queries the
season. `null` outside the year end. **Every key below is always present; a value the records cannot give is
`null`** (never absent).

```
year_end = {
  "year": 2028,                       # the season under review
  "stage": "season_review" | "winter_choices" | "winter_residence" | "winter_running" | "winter_ai" | "choose_newcomer",
  "winter_parts_done": 0..3,
  "version": 43,                      # career version to post back
  "review": {
     "year", "golfer_id", "name", "age", "status", "lifestyle", "tour",
     "recorded_weeks": 52, "complete": true,          # weeks the career recorded for this golfer this season
     "events", "wins", "top10", "missed_cuts",
     "best_finish": {"position", "event", "tied"} | null,
     "prize_money": 0.0, "income": number | null,     # income: the season's ledger, null if none was kept
     "activity": {"play": n, "train": n, "rest": n, "work": n},   # only kinds that occurred
     "overall_start": number | null, "overall_now": number | null,
     "world_rank": int | null, "amateur_rank": int | null, "funds": number | null
  },
  "decisions": [                      # the open year-end decisions (S2/S3 may have two at once)
     {"id": "D16", "kind": "winter_career", "text": "...", "options": ["continue", ...],
      "choices": [{"key": "turn_pro", "label": "Turn professional", "facts": {...}}, ...]}
  ],
  "offers": ["D12"],                  # pending coach/caddie/job offers that must be answered before S0's answer
  "answers": {"intent": "keep", "career": "turn_pro", "staff": {"coach": "keep", "caddie": "let_go"}, "residence": "stay"},
  "candidates": [ ... ] | null        # S7 only: same as the choose_newcomer choices' facts
}
```

`choices[].facts` by kind (keys present only where listed):

* `season_review`: `{"detail": str}`
* `winter_career`: `turn_pro` → `{"tour": str, "amateur_rank": int|null, "reason"?: str, ...}`; `comeback`/`part_time_pro` → `{"tour"}`;
  `return_full_time` → `{"results", "season_cost"}`; a blocked return shows `{"cannot_return_full_time": reason}` on the first option.
* `winter_staff`: `{}` (the decision payload also carries `coach`/`caddie` ids)
* `winter_residence`: `stay` `{}`; `move:<c>` `{"cost", "travel_saved" (negative = more travel), "own"}`
* `choose_newcomer`: candidate `{"id", "name", "country", "age", "status", "lifestyle", "tour", "overall", "attrs": [[group, [[key, value], ...]], ...], "funds"}`
  — public profile only: no potential, ceilings, peak age, aging rate. `end_career` → `{"detail"}`.

Also new in the career view: `"stints": [{"golfer_id", "name", "from": [y, w], "to": [y, w] | null, "how": {...}}]`,
and each weekly recap now records `golfer_id`.

Example JSON for each stage, generated by `tests/career_year_end_fixtures.py`: `docs/career/year_end_fixtures/`.

## Paid work weeks (professional pathway)

A week choice `{"kind": "work"}` in `plan_block`. Allowed by the engine's own rule (`Season.needs_paid_work`): a
full-time professional whose funds would not cover three months of living costs — the test the AI planner's paid work
rests on. Paid `WORK_WAGE` (900) through the normal weekly finances; no development that week (as the AI's). Once
planned, a work week stands even if a prize arrives (as the AI's do). An injured golfer short of money does light work
automatically, as every golfer does. The old `unsupported/paid_work` hard stop is gone.

`planner(...)['weeks'][i]['work'] = {"available": bool, "wage": 900, "why": "" | reason}`.

## Candidates

`career.candidates(season, year)`: the junior class of `year` as the normal rules created it (no golfer is created
here), a seeded uniform sample (`{seed}:career:candidates:{year}`) of at most 10, sorted by id; the whole class when
it has 10 or fewer. Stored in the decision when first asked, so it is stable across reloads; no reroll.

## Policy defaults (safe, changeable)

1. A college golfer cannot retire in the winter (the AI's college golfers never do).
2. Retiring as the player gives no coach/caddie role (the AI's retirement roles are not offered).
3. Residence: only `stay` or the rule's own destination, at the rule's cost; offered whenever the rule names one
   (the AI moves with a probability; the player decides).
4. No resuming a golfer after a switch.
5. A kept golfer who retires goes straight to the newcomer choice.
6. Paid work is the player's choice when allowed; the engine never forces it on a healthy golfer (the AI would plan it).
7. Ten candidates, or the whole class if smaller.

## Compatibility

* Career record format 2 (stints, winter answers). A format-1 record is upgraded when read: its history becomes one
  stint (closed if the career ended). Nothing recorded is reinterpreted; an ended career stays ended.
* **That is record migration only.** Any golfsim change gives a new engine fingerprint, so worlds saved by 30b9fed
  (CareerTest1 included) still open browse-only. Making them continuable needs an explicit engine-migration path,
  which is *not* enabled here (see the integration report).
* All-AI worlds are unchanged: the all-AI golden digests (`tests/test_career_foundation.AllAI`) hold.
