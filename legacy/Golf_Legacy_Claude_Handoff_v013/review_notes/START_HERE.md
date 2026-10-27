# Golf Legacy v0.6 — start here

A tested working revision of the preserved v0.3 project, **not a validated real-world career prediction model**. The original Library archive and conversation were not overwritten. No paid services were used.

## What changed
- Stronger persistent elite skill, with a smooth taper for extreme ratings instead of unchecked acceleration or forced winners.
- More coherent veteran development, recovered temporary slumps, working course familiarity and major experience.
- Funded participation and training; distinct downshifts, hiatus, returns and retirement. Real observed progress can earn more patience, not unlimited money.
- Regional mini circuits, earned premier eligibility after major wins, conserved purses/tied payouts and no double-booked venues.
- Annual recaps based on recorded results and events. Optional sponsorship remains **off**.

## Six additional 30-year tests, with two final candidate worlds

Earlier v0.4/v0.5 worlds exposed problems and were retained as diagnostics. Final v0.6 uses fresh seeds, 1,700 active slots and the full 2027–2056 calendar:

| Final world | Tournaments | Major champions / 120 majors | Most majors by one golfer | Mean champion age |
|---|---:|---:|---:|---:|
| Seed 909 | 5,730 | 66 | 8 | 33.2 |
| Seed 1001 | 5,730 | 70 | 6 | 34.0 |

Independent audits found **zero integrity errors** across 3,694,511 ledger transactions, 1,207,980 funded starts and 11,460 purses/venue-weeks. Mini-tier participation now has a median of **eight starts in each of the last ten seasons**, versus two in the earlier bottlenecked worlds; progress-based decisions are now reachable. This does not guarantee profitability.

**Important:** neither final world generated a flagged rare-prodigy candidate. These results do not prove that extreme early careers are calibrated. The earlier 18-majors-by-26 outlier is preserved, with separate controlled stress diagnostics rather than hidden or rewritten history. In 200 complete tournament fixtures per version, the extreme profile won 52.5% under v0.5 and 26.0% under v0.6; this is not a real-world probability or full-career validation.

## Examples that actually happened
- **Kai Zhang, seed 1001:** returned from hiatus at 32, won two mini-circuit events in 2029 and was promoted.
- **Hugo Ito, seed 909:** a logged financial downshift in 2039 was followed by promotion back to tier 3, without a tournament win that year.
- **Peter Hayes of Japan, seed 909, ID 3124:** won his first two recorded majors at 23 after earlier mini, regional and challenger wins.

Exact dates and source dossiers are in `recaps/V06_EMERGENT_EXAMPLES.md`; no invented causes or future outcomes are claimed.

## Run it
Python 3.10 or later; tested with Python 3.12.14. Simulation and tests use only the standard library. From this directory:

```bash
python working/engine_v06.py --seed 909 --years 30 --population 1700 --out my_world
python working/analyze_v04.py my_world
python working/analyze_v05_careers.py my_world
python recaps/annual_recaps.py --input my_world --out my_recaps --source-format golf-legacy-v06 --label "My v0.6 run"
python working/run_two_v06.py --out reproduced_worlds
```

Defaults: sponsorship off, outside-work contributions on, declared four-event opening reserve for established players. See `working/frozen_config_v06.json`. Preserve `working/` and `economics/` as sibling directories.

```bash
python -m unittest discover -s working -p 'test*.py'
python -m unittest discover -s economics -p 'test*.py'
python -m unittest discover -s review -p 'test*.py'
python -m unittest discover -s recaps -p 'test*.py'
python review/audit_exports.py my_world --out my_world/general_audit.json
python review/audit_economics_exports.py my_world --out my_world/economics_audit.json
```

## Read next
- `CHANGE_REPORT.md`: real changes, failed experiments and limitations.
- `CONTINUE_PROJECT.md`: handoff for the original project conversation.
- `economics/FINAL_V06_ECONOMICS_REVIEW.md`: finances, progression and sensitivity evidence.
- `research/`: source-linked derived evidence and methods.
- `recaps/examples/`: final annual recaps and fact audits.
- `review/`: independent tests and completed audits.

**Still provisional:** rare readiness, financial assumptions, younger lower-tier populations, flat travel costs and simplified qualifying/card rules. Ratings are not OWGR. Current top-125 histories are survivor-conditioned, not a measure of every aspiring professional's chance of success. Active/late-entering careers remain censored. Do not treat two final worlds as proof of balance.
