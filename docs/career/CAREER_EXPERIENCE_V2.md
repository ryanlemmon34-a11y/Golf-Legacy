# Career experience v2

The career dashboard now puts recorded results before the next plan. This is a presentation and observation update, not a balance change.

## What changed

- Player identity hero and grouped, measured attribute bars using the observer's existing light/dark palette.
- Latest four-week review, with actual weekly activities, planned intentions, tournament finishes and recorded rounds/prizes, fatigue movement, and overall development.
- Development is split into its recorded sources. Natural maturation is not credited to training.
- A readiness panel displays fatigue on its actual 0–100% scale, the engine's 20% performance threshold, and estimated fatigue after a rest or training week without a tournament.
- A four-card planner separates tournament entry, training, rest, fallback choices and selection policies.
- Previous periods remain available. Support team, finances and pending decisions stay alongside the review.
- The period advance is the emphasized action so the player regularly sees what happened.

## Evidence and compatibility

Snapshots are recorded only for the controlled golfer after completed simulation weeks. Existing saves remain loadable and begin collecting feedback prospectively. Missing past history, missing rounds and unknown awards are not invented. Partial periods are explicitly labeled. Hidden ceilings and potential are not sent to the career UI.

Recorded overall changes are rounded to three decimals and source contributions to four decimals. Small arithmetic differences between displayed totals can reflect rounding. Source category deltas are preserved in saved evidence. No random draws or simulation decisions are introduced by recording.

## Verification

- 13 observer-flow and feedback tests passed, including HTTP forms, refusal/stale actions, save/reopen, interrupted and failed advancement, source attribution and identical simulation outcomes with feedback disabled.
- Three presentation tests cover missing evidence, partial periods, escaping, tied finishes and estimated readiness.
- Existing career foundation coverage passed after an initial privacy wording failure was corrected; the final focused privacy test passed.
- Browser visual signoff remains outstanding: the cloud browser could not access the local observer, and its security policy disallowed local-file previews. Static HTML was captured successfully, but a print renderer was not faithful to browser layout and is not treated as visual verification.

## Suggested acceptance pass

Open an existing career, plan an event/training/rest period, advance it, and compare the review with the linked event result. Verify a new career's empty state, pending decision controls, planner cancellation, narrow/desktop layouts and both themes. Existing saves will need one newly played week before feedback appears.
