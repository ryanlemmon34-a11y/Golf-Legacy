# Copy-and-Paste Prompt for Claude

You are reviewing an ongoing **Golf Legacy** project. I am the owner/designer, not a programmer. Please read the complete attached ZIP and **do not start rewriting the whole project** without examining the code and tests.

## What I want

I want a primarily personal, offline, single-player, text-based golf career simulation with a rich, searchable global history. My priority is **realistic, fully chronological hole-by-hole golf simulation** across 60-, 100-, and eventually 200-year worlds. I want 6,000+ active golfers initially with competitive amateur, part-time and international professional paths, dozens of tours, major qualifiers, dynamic national golf growth, individual career ups and downs, and permanent detailed records. My desired long-term performance target is around 120 seconds or less per full-size season including persistent history storage. I am willing to spend a modest one-time amount but want to avoid recurring fees. I need step-by-step guidance; I have no coding background.

## Read these in order

1. `START_HERE.md` — handoff entry point and file map.
2. `GAME_REQUIREMENTS_MASTER.md` — comprehensive approved/planned design requirements, IDs R01–R20.
3. `IMPLEMENTATION_STATUS.md` — exact existing vs missing behavior.
4. `DEVELOPMENT_ROADMAP.md` — proposed implementation gates.
5. `review_notes/README_START_HERE.md` and `review_notes/TEST_REPORT_V013.md` — original current release notes and measured results.
6. `source/engine_v013.py`, `source/rankings.py`, `source/history_store.py`, `source/audit_v013.py`, `source/reference/`, `source/tests/test_v013.py`.
7. `original_design_docs/` for the verbatim v0.10 scheduling/prestige/UI, v0.11 formats/calendar, v0.12 rankings/test plan. Earlier history and experiments are in `review_notes/`.

## First task: Independent technical and realism audit

1. **Run** `python -m unittest discover -s tests -v` inside `source/`, and run the included audit tool against the supplied SQLite archive. State the exact commands and results.
2. Map each important requirement to actual functions/classes/tests. Mark fully implemented, partially implemented, and absent. In particular, verify how many of the designed 15 golfer attributes actually influence scored holes, how pressure/cut/lead calculations work, how event/round lengths are handled, and whether the historical database is sufficiently complete.
3. Identify and prioritize correctness issues: chronological tee order, simultaneous events, qualification provenance and deadlines, ranking math/field strength, purse conservation, persistent staff/golfer histories, accidental full-score shortcuts, and SQLite crash safety.
4. Review architecture and runtime bottlenecks. Propose the least risky route to full 6,000-person/500–600-event seasons, retaining every competitive hole. Compare high-impact Python optimization (e.g. cache/Numba) against a limited Rust scoring core before recommending a complete rewrite.
5. Assess the realism/testing plan and recommend the **smallest next code patch** that removes a significant blocker. Give clear reasons and test evidence, not just speculative architecture.
6. Call out conflicts or ambiguity between this user's desired requirements and the implementation, but **do not silently change approved product goals**.

## How to communicate

- I'm not a programmer: explain results plainly and provide exact commands when necessary.
- Do not claim that planned college routes, historical UI, comprehensive tour cards, fully realistic OWGR, 6,000 golfers or 60-year v0.13 tests are already working.
- Do not promise invented speedups or prove realism from one cherry-picked world.
- Do not sacrifice chronological hole-by-hole fidelity, live pressure/cuts, real major entries or complete history for speed.
- Keep fixed 52-week schedule, four exclusive major weeks W14/W19/W24/W30 and 40 combined Tier 0/1 tournaments (4 majors, 36 regular Premier).
- Preserve the source baseline; any patch should include changed source, tests, a short change report, reproduced benchmarks and known limitations.

Please begin with a concise factual audit of the source and test results, then your three highest-priority next engineering steps. If you propose code changes, implement only the first bounded change and show how it was tested.
