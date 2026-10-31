# Major affordability scenario coverage

These are fictional NPC golfers from the seeded Golf Legacy save Test 1 10.30 (seed 360013), not real people or real financial records. The manifest was independently re-read from the published 2027-2083 archive and every selected refusal was checked against the final event field.

## Format and verified counts

Decode each case with `dict(zip(manifest['columns'], row))`. Shared unknown fields are in `common_unknown_fields`; null means unknown, never zero. Relative source-file paths, SHA256 hashes and ledger pointers retain provenance.

- 269 unique person/event/year refusals; 159 people.
- 221 amateurs, 42 professionals and 6 club professionals.
- 112 Britannia Opens, 99 USA Opens, 49 Tour Masters and 9 Premier Tour Championships.
- 172 conditional rights and 97 earned rights. Conditional amateur eligibility must be satisfied in reconstructed tests.
- Barnaby Harper (23529) has eight refusals. Two are in 2047; the previously analyzed six are the 2048-2050 subset. Only those six have separately labeled modeled trip costs.

## Economical acceptance test

Run 269 table-driven cases through the real major admission/funding path using small isolated fixtures, not 269 simulated worlds. Keep historical identifiers, major, country, status and route provenance, but explicitly construct an active, otherwise-eligible golfer with synthetic zero cash and no remaining credit or overlapping support. The old archive does not retain decision-time balances.

Use an explicit positive synthetic test cost or the current deterministic cost resolver; do not infer zero from a null recorded cost. Reset mutable state between rows. Confirm entry, exactly one funding transaction, correct treatment of covered travel/entry costs under the implemented guarantee policy, no disposable-cash windfall and no double funding on repeated processing. Covered costs must not also be charged to the golfer. Caddie fees follow their separate documented policy.

Keep a separate negative/control matrix for injury, retirement, expired eligibility, lost amateur status, no valid right, qualifying, ordinary events, sufficient funds and overlapping support. Where the production path requires a full field, use the smallest legal fixture and document the boundary. A helper-only test is not a substitute for admission-path coverage.

Report 269/269 distinct scenario IDs exercised, Harper 8/8 and modeled subset 6/6, exact commands, results and caveats. These are reconstructed scenarios, not exact historical replays. This manifest itself does not establish that the new code passes.

## F2 coverage test (added with tests/test_major_affordability_269.py; not part of HAL's manifest)

What it covers: every one of the 269 rows, by its category (status, major, earned or conditional, route codes:
49 categories), through today's real weekly entry path (`Season.run_week` for that major's week:
`special_field` -> `major_field` -> `lock_rights` -> the trip booked -> the round played -> `record_event`), in
the row's own year and week. For each row a synthetic golfer with the row's status, residence, lifestyle and a
caddie is made broke on purpose (no savings, credit line used up, no family money, no backers, no amateur
support), and only the facts that give the row's routes are recorded (a fresh qualification context per row).
Asserted per row (subTest by case_id): in the field by one of its own routes and played; the right recorded
'entered' with the row's routes and state and its money facts (could not pay; paid by the organizer); exactly one
organizer travel grant covering travel and entry, nothing in the golfer's events ledger, cash moving only by what
the books show; the caddie's week paid by the golfer. Each of the 172 conditional rows is also run with a golfer
who has turned professional: the place lapses ('expired: turned professional') and nothing is paid. Summary checks:
269/269 case ids; Harper 8/8 (2 recorded in 2047 + the 6 modeled 2048-2050).

What it does not do: it is not a replay of Test 1 and uses no historical balance or trip cost (none is recorded;
null stays unknown). The synthetic golfers are not the historical people, the costs are today's resolver's, and
the world is a tiny one (scale 0.01) with no other event played that week. Harper's modeled costs are only
labelled, never used. Run: `nice -n 19 python -m unittest tests.test_major_affordability_269 -v` (about 15 s).
