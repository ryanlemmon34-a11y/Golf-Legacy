# Advance invitations (calendar v4)

Engine: `golfsim/invitations.py`, with these hooks:
* `Season.play_prepared_week` → `INV.step`;
* `Season.special_field` → `INV.event_field`;
* `career.invitation_decisions`;
* `entry_outlook.invitation` and `entry_outlook.route`;
* `career._entries`.

The lifecycle is switched on by `schedule.Spec.advance_invitations`, which is True only in the new `v4` calendar spec
(v3 plus this). New worlds use v4: `schedule.NEW_WORLD = 'v4'`.

Older worlds and goldens:
* v1, v2 and v3 worlds are unchanged, and so are their goldens: the v3 golden in `tests/test_college_qualifiers.py`
  still passes.
* Older saves open browse-only, by the engine fingerprint, as for any engine change. No migration.
* Ryan's save isn't touched.

## Scope: three routes into a field

| Route | Fields | What changes in v4 |
|---|---|---|
| `invitation` | every national amateur championship; the elite amateur championships chosen by ranking (Latin America, Africa, Britannia, European, Asia-Pacific, USA Mid-Amateur) | the advance lifecycle below |
| `earned` | majors (exemptions), circuit championships, the college postseason, the Premier finals, the USA Amateur (qualifying plus exemptions) | nothing: set in the event week, with the period policy `selected` |
| `qualifier` | qualifying events the entrant decides on (`career.entrant_decides`) | nothing: they are never replaced by invitations |

The planner rows carry `route`: `entry` (an ordinary entry request), `invitation`, `earned` or `qualifier`.

## Lifecycle (deterministic; no random draw)

For an edition in week E:

1. **Offer week O = E − LEAD.**
   * LEAD is 4 weeks for national amateur championships and 6 weeks for elite ones.
   * An early-season event is offered in the December before, for example week 50 of 2027 for week 2 of 2028.
   * The selection snapshot uses the same rule the event-week selection used: amateur ranking, then observed form,
     then id; host country first, then its region up to a quarter of the field; the elite region and mid-amateur age
     rules.
   * The first `field` golfers are `invited`. The next quarter of the field (at least 4) are `alternate`s, in order.
   * Injury doesn't stop an offer. The answer deals with it.
2. **Response deadline R = O + 2.** Every answer is applied at the start of week R, before any field.
   * **AI golfers** answer by `rule_answer`: accept (or stand by) when still eligible, not injured past E on the
     recorded injury, able to afford the trip now, and free of a clash with places already held that week (same days,
     or travel the engine forbids). Otherwise they decline.
   * **The player** answers the career decision `invitation`, which is due at R. It is shown from O+1 and blocks only
     at R.
   * Under the explicit career setting `invitation_policy: 'auto'`, the player's answer is the same rule.
   * A golfer who no longer meets the criteria, or a player with no answer (only possible if the career stops
     blocking), gets `expired`.
   * Places declined or expired go to stand-by alternates in order (`promoted`).
3. **Event week E.** Every taken place is checked again:
   * still eligible;
   * not injured;
   * not already playing those days (fields of majors and championships are set first);
   * the trip possible;
   * affordable now (the cost is checked again).

   Anyone who fails is `withdrawn`, with the reason. Each such genuine vacancy goes to the next stand-by alternate who
   passes the same checks (`entered`, `late: true`; log event `late_replacement`). There is never a late place
   without a withdrawal.
4. **Money.** Costs are charged only when played, through the existing reserve-and-charge path. A declined, expired
   or withdrawn place costs nothing. Travel prices are unchanged, and there are no school-term rules.

Editions whose offer week came before the world began (for example the first weeks of a world's first season) have
no ledger. They are selected in the event week, as before.

## Schema

`season.invitations[event_id]` is saved with the world, and the season before last is pruned on 1 January:

    {event_id, series_id, name, category, year, week, days, field, offer_at: [y, w], deadline: [y, w],
     entries: [{golfer_id, role: 'invited'|'alternate', order, status, answered_at: [y, w]|null,
                by: 'ai'|'player'|'auto'|null, reason: str|null, status_before?, late?}],
     log: [{date: [y, w], golfer_id|null, event, reason}],
     played?: [y, w]}

Entry statuses:
* Invited: `offered`, then `accepted`, `declined` or `expired`.
* Alternate: `offered`, then `standby`, `declined` or `expired`. A stand-by alternate then becomes `promoted` (at R),
  is entered with `late: true` (at E), or ends `unused`.
* At E, a taken place becomes `entered` or `withdrawn`. `status_before` keeps the status it had.

## Career contract

Decision `kind: 'invitation'`, one per offer, key `('invitation', event_id)`, due at R:
* Options are `('accept', 'decline')` for an invited place and `('standby', 'decline')` for an alternate.
* `payload`:

      {event_id, series_id, name, golfer_id, route: 'invitation', role, order, field,
       event_week: [y, E], days, city, country, cost_estimate, deadline: [y, R],
       conflicts: [{kind: 'invitation'|'plan'|'earned', event_id, name, text}], group: [y, O]}

  All offers sent the same week share `group`.

The answer is stored in `career.invitation_answers[event_id]` and applied at R. It can be given once, and is refused
once the deadline has passed.

Setting: `{'type': 'invitation_policy', 'value': 'ask'|'auto'}`. With `auto` no decision is made, and a notice
records the invitation once. The setting is shown as `view.invitation_policy`.

`view.entries` lists the golfer's invitations:

    [{event_id, name, route, role, order, status, status_text, event_week, offer_at, deadline,
      cost_estimate (open places only), reason, history}]

`entry_outlook` statuses for invitation rows:
* `invitations_later`: before O, with the offer week. No forecast is made.
* `invited`, `accepted`, `alternate_standby`, `declined`, `not_invited`, `expired`, `withdrawn`, `alternate_unused`.

The coach's advice counts an `accepted` invitation in the load, like a held place. An `invited` one is mentioned,
not counted.

Two changes from the first contract I sent:
* A late replacement ends as `entered` with `late: true`, not as a separate status.
* `alternate_unused` was added.

## Calendar review (v4 = v3 calendar; no calendar change)

**Qualifying chains have time between stages:**
* USA Open: local qualifying in weeks 17, 19 and 21; final qualifying in weeks 22 (international) and 24; the Open
  in week 25.
* Britannia Open: regional qualifying in weeks 26 and 27; final qualifying in week 28; the Open in week 30.
* USA Amateur: qualifying in week 30; the championship in week 33.
* Club professionals: sectionals in week 12; the championship in week 18.
* College: qualifiers in weeks 10–13; the national championship in week 22.

**Invitations and qualifying:** one invitation field shares days with a qualifier. The Britannia Amateur (week 26,
all week) overlaps Britannia regional qualifying wave 1 (week 26, Monday). Wave 2 in week 27 stays open, so no change
is needed. Accepting the invitation is the player's informed choice: the decision lists clashes the engine knows of.

**Early-season events:** 7 to 9 editions a season are offered in the December before (seeds 11 and 23).

**Known limitation:** venue moves are decided at the year end (`review_venues`), after December offers. An
early-season edition's city can therefore change after its offer. The decision shows the city at the time of the
offer; the event-week checks and charges use the actual venue.

## Fairness and determinism

* One rule answers for every AI golfer, and for the player's `auto` setting.
* The player's own answers go through the same deadline step.
* Paired test: the player answering what the rule answers (or `auto`) gives the AI's ledger exactly.
* No random draw: the world's random streams are untouched (golden replay).

## Tests

`tests/test_advance_invitations.py` (17 tests):
* the spec;
* the lead times by type and the December rollover;
* answers and promotions at the deadline;
* fields come only from the ledger, and late places only for withdrawals;
* never two fields on the same days;
* an idempotent weekly step;
* paired AI/player answers (`ask` and `auto`);
* the offer shown the week after the offer, with cost, place, dates and conflicts; due only at the deadline; repeated
  gates give one decision; answers survive save and load; answered once; applied at the deadline;
* a decline spends nothing and isn't played;
* `auto` needs no decision;
* outlook and route read models, read only;
* the event-week checks: injury, cost and clash withdrawals, each replaced one for one in alternate order;
* no withdrawal means no late place;
* the rule declines when injured or clashing;
* a player with no answer expires and the place passes on;
* the v4 golden, run twice.
