# Coach's advice for the period

Engine module: `golfsim/career_advice.py`. Read model: `view['advice']`.

The advice is read only, with no random draw and no hidden ratings. It is a starting suggestion for each open week of
the current four-week period. The player edits it and saves it; the engine validates the plan exactly as it validates
any plan. The advice changes no rule.

## Evidence

The advice uses only what the planner already shows (`week_compare`) and the scouting read:

| Factor | Source | Rule |
|---|---|---|
| Entry outlook | `entry_outlook` | open / ahead +2, near capacity +1, at cut-off or unknown +0.5, quota-limited 0, behind −3 (a long shot: suggested only when everything else outweighs it, and then said first, code `long_shot`) |
| Stakes | `opportunities` rows still needing a result | +2: "a result here can earn a place in …" |
| Pathway | the event's tour is the golfer's own tour | +1.5 |
| Course fit and familiarity | `course_fit.points` | +0.5 × points |
| Cost | cost compared with the money available for golf | −1 if it is more than half; never suggested if it can't be paid |
| Load | tournaments recorded or suggested, plus held places and qualifying the suggested policy enters | at most 2 in any 4 consecutive weeks: a week is suggested only if the three weeks before hold fewer than 2 |
| Held places / qualifying | rule-selected rows: `entry_outlook.status == 'holds_place'`; qualifying by the engine's own test (`career.entrant_decides`), entered (`qualifying: 'enter'`) only when a result there can still earn a place | that week's competition comes first and counts in the load (code `committed`); the plan entry is training, or rest |
| Possible selections | other rule-selected rows | said (code `possible_selection`), not counted: selection isn't known in advance, so the real load can be higher |
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
* Event weeks: `long_shot`, `stakes`, `pathway`, `entry_outlook`, `course_fit`, `cost`, `not_guaranteed`, `load`.
* Any week: `committed` (a held place or qualifying first), `possible_selection`.
* Training weeks: `visible_weakness`, `growth_room`, `growth_room_unknown`, `coach_speciality`, `no_strong_event`.
* Rest weeks: `fatigue`, `injured`, `no_training`.
* Alternatives' trade-offs: `no_results`, `fatigue_train`, `fatigue_rest`, `no_development`.

## Fairness

* Every input is evidence the player sees, built by rules that read only the golfer, the event and the records. None
  of them reads who controls the golfer.
* The advice doesn't feed back into any engine rule.
* AI golfers plan with the engine's own rules (`Season.plan_block`), which the advice doesn't change.

## Tests

`tests/test_career_advice.py` (6 tests; two from HAL's review of 6d0d31e, one from the audit of b7fb0ee):
* Read only and deterministic: the world digest is unchanged, and the suggested plan is accepted by the engine's own
  validation.
* The rules: stakes and own tour preferred; the load cap; a weak event behind the cut-off not suggested (score below the bar); nothing unaffordable suggested;
  rest when tired or injured; recorded play counts toward the load.
* The training pick uses weakness, growth room and coach speciality.
* The load window's boundary: two tournaments in the three weeks before block a suggestion; one of them four weeks
  back does not; every 4-week window holds at most 2 (`LoadWindow`, from HAL's audit of b7fb0ee).
* A long shot (behind the cut-off) is suggested only when everything else outweighs it, with `long_shot` first.
* A held place takes a load slot. Qualifying is recognised by the engine's test, so rule text saying "qualifying"
  doesn't make an event qualifying. Possible selections are stated but not counted.
