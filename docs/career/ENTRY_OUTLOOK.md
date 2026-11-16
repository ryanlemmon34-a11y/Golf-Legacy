# Entry outlook

Engine module: `golfsim/entry_outlook.py`.
Read model: `view['week_compare'][week]['play'][i]['entry_outlook']`.
Read only, with no random draw.

## What it uses

The outlook uses only facts the engine's rules use or the world recorded:

* **Can the golfer request entry?** Eligibility and affordability now, from the engine's own checks
  (`career.week_options`), and whether the golfer is injured.
* **The golfer's entry class now.** This is `Season.priority`'s first element: playing rights, own tour or home
  members, home players at a national open, a higher, same or lower tour, or an amateur in a professional event.
  Fields admit classes in this order. Within a class, order goes by ranking, or by rotation and the entry draw where
  those rules apply.
* **How the field closed at the last recorded edition** (`Season.note_cutoff`, `opportunities.field_history`): the
  places, the requests, the number taken, whether it filled, and the class of the last golfer taken ahead of late
  fills.

It never uses this year's other entrants, which are unknown until entries close. It never gives a percentage or a
probability.

## Eligible, held and admitted are different things

* Rule-selected events report `rule_selected`. Being eligible is not being selected.
* `holds_place` appears only where the rules record a place (`opportunities.held_places`). Even then, the period
  policy must accept it.
* Admission is reported only after the field is decided (`career.week_entry`).

## Contract

    {status, label, your_class, your_class_label, last_edition: {year, capacity, asked, admitted, full, late_fills,
     closed_at, note} | null, reason, uncertainty}

| `status` | When |
|---|---|
| `injured` | An injury keeps the golfer out of this week's entries. |
| `not_eligible` | The entry rules don't admit the golfer now. The reason comes from the engine. |
| `cannot_afford` | Eligible, but the trip isn't affordable now. |
| `holds_place` | A rule-selected event in which the golfer holds a recorded place. |
| `rule_selected` | The event picks its own field. |
| `quota_limited` | The golfer is an amateur in a professional event, or a Premier member in a Challenger event. These get a limited number of places, and the record doesn't show how they were shared, so no judgement is given. |
| `open_last_time` | The field didn't fill last edition, and requests were below 80 % of the places. |
| `near_capacity_last_time` | The field didn't fill, but requests were at or above 80 % of the places. |
| `ahead_of_last_cutoff` | The field filled. The golfer's class comes before the class it closed at. |
| `at_last_cutoff` | The field filled. The golfer's class is the class it closed at; within it, ranking, rotation or the draw decides. |
| `behind_last_cutoff` | The field filled. The golfer's class comes after the class it closed at. |
| `unknown` | No recorded previous edition (a new series, an older save, or more than a season ago), or a full field whose closing class wasn't recorded. The reason is given. |

## Calibration and limits

These figures are measured, not shown in the game.

Setup:
* World: calendar v3, seed 11, scale 0.05, all AI.
* At every regular entry, each golfer's outlook for the event they wanted first was compared with whether they got
  into it.

Share of first-choice requests admitted, by status:

| Status | 2028 (2nd season) | 2029 (3rd season) |
|---|---|---|
| `open_last_time` | 72 % (14,674 requests) | 88 % (15,467) |
| `ahead_of_last_cutoff` | 73 % (2,099) | 59 % (9,000) |
| `near_capacity_last_time` | 33 % (1,785) | 25 % (673) |
| `at_last_cutoff` | 46 % (231) | 11 % (10,750) |
| `behind_last_cutoff` | 0 % (2,844) | 0.3 % (3,906) |
| `quota_limited` | 9 % (785) | 12 % (1,459) |

How to read this:
* The ordering is consistent in the third season. `behind` is a strong signal.
* `ahead` and `open` are favourable, but far from certain.
* Demand grows from season to season in a young world. Premier fields that didn't fill in a world's first season fill
  in its second, so the first season's history is the weakest guide.
* These rates depend on the world and its age, which is why they aren't shown to the player as numbers.

## Tests

`tests/test_entry_outlook.py` (6 tests) covers:
* each status from the engine's rule facts and a recorded edition;
* `unknown` without history;
* quota cases give no judgement;
* read only: world digest and field history unchanged, with no percentages in any text;
* every planner row carries an outlook.
