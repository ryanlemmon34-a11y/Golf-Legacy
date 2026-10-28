# Long-world test: two worlds, 25 seasons each (2027-2051)

Seeds 2027 and 3031, full population, every shot simulated, engine commit b4b4658 (manifest in each
folder). Each folder holds the player-facing `REPORT.md`, the debug `DEBUG.md` (hidden attributes) and
the manifest. The history archives (~22 MB each) and resumable saves (~62 MB each) are not in git.

**About the "cash not reconciling" counts in section 1 of each report:** the run used a check with an
absolute tolerance of $0.000001, which flagged floating-point rounding (about 7 parts in 10^15) on the
balances of the richest players ($100M+). The check now uses a cent-or-relative tolerance. Verified
independently from the yearly records: in all 314,926 golfer-seasons, the change in cash equals the
recorded net to within $1 (whole-dollar rounding of the export). Staff payments equalled receipts, staff
invariants held and the population reconciled in every season of both worlds.

Known issue found by this run (see the session summary): adult amateurs outside college who never take
a job, and invitation-only fields that skip the affordability check, let a few amateurs run up debts far
beyond the credit limit ($120k-$167k by 2051).
