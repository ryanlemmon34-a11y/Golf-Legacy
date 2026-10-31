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
