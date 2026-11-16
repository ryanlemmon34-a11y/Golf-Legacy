# Coach's advice for the period

Engine module: `golfsim/career_advice.py`. Read model: `view['advice']`.

The advice is read only, with no random draw and no hidden ratings. It is a starting suggestion for each open week of
the current four-week period. The player edits it and saves it; the engine validates the plan exactly as it validates
any plan. The advice changes no rule.

## Evidence

The advice uses only what the planner already shows (`week_compare`) and the scouting read:

| Factor | Source | Rule |
|---|---|---|
| Entry outlook | `entry_outlook` | open / ahead +2, near capacity +1, at cut-off or unknown +0.5, quota-limited 0, behind −3 |
| Stakes | `opportunities` rows still needing a result | +2: "a result here can earn a place in …" |
| Pathway | the event's tour is the golfer's own tour | +1.5 |
| Course fit and familiarity | `course_fit.points` | +0.5 × points |
| Cost | cost compared with the money available for golf | −1 if it is more than half; never suggested if it can't be paid |
| Load | tournaments recorded or suggested in the 4 weeks before | at most 2 in any 4-week stretch |
| Fatigue | `career.readiness` and the engine's rest and training formulas | rest when fatigue is above the 20 % threshold |
| Injury | recorded injury window | rest |
| Training area | the visible weakness order (observed levels), perceived growth room (scouting: an opinion with uncertainty) and the coach's public speciality | weakness (number of categories − rank), plus room (little 0, some 1, considerable 2, unknown 0.5), plus speciality +1 |

How each week is decided:
* An event is suggested when its score is at least 2 and the load rule allows it. A suggested event falls back to the
  training area.
* Otherwise the week goes to training, or to rest when training isn't available to the golfer.
* Fatigue after a tournament isn't forecast. Weeks after a suggested event are judged without a fatigue figure, and
  the advice says so.

## Contract

    {block: [y, w0], judge: coach name | null, source: 'coach' | 'self',
     weeks: {"w": {recommended: {kind: 'event', event_id, fallback} | {kind: 'train', category} | {kind: 'rest'},
                   reasons: [{code, text}], alternatives: [{choice, name?, for: [{code, text}], against: [...]}],
                   events_considered: [{event_id, score}]}},
     policy: {selected: 'accept', qualifying: 'enter' | 'skip'},
     training_table: [{category, score, weakest_rank, growth_room, growth_room_uncertainty, coach_speciality}],
     basis: [codes], note}

Reason codes:
* Event weeks: `stakes`, `pathway`, `entry_outlook`, `course_fit`, `cost`, `not_guaranteed`, `load`.
* Training weeks: `visible_weakness`, `growth_room`, `growth_room_unknown`, `coach_speciality`, `no_strong_event`.
* Rest weeks: `fatigue`, `injured`, `no_training`.
* Alternatives' trade-offs: `no_results`, `fatigue_train`, `fatigue_rest`, `no_development`.

## Fairness

* Every input is evidence the player sees, built by rules that read only the golfer, the event and the records. None
  of them reads who controls the golfer.
* The advice doesn't feed back into any engine rule.
* AI golfers plan with the engine's own rules (`Season.plan_block`), which the advice doesn't change.

## Tests

`tests/test_career_advice.py` (3 tests):
* Read only and deterministic: the world digest is unchanged, and the suggested plan is accepted by the engine's own
  validation.
* The rules: stakes and own tour preferred; the load cap; nothing suggested behind the cut-off or when unaffordable;
  rest when tired or injured; recorded play counts toward the load.
* The training pick uses weakness, growth room and coach speciality.
