# GOLF LEGACY — Complete Claude Handoff

**Created:** October 26, 2026 (project conversation timeline)  
**Verified source release:** Golf Legacy v0.13 **experimental** Python world simulator  
**Goal:** Hand this ZIP to Claude for a serious engineering/design review and continued work while preserving every previously agreed game requirement.

## Quick read (five files)

1. **`GAME_REQUIREMENTS_MASTER.md`** — the consolidated, detailed product specification: vision, monthly career management, golfer/staff traits, national pipelines, tours, week cascade, four majors, formats, records, ranking, finances, speed and future UI.
2. **`IMPLEMENTATION_STATUS.md`** — the honest feature-by-feature status and actual v0.13 test results.
3. **`DEVELOPMENT_ROADMAP.md`** — prioritized implementation gates and what needs to pass before the next two 60-year simulations.
4. **`RUN_INSTRUCTIONS.md`** — how to run the working code, including the simple Windows batch files.
5. **`CLAUDE_REVIEW_PROMPT.md`** — a ready-to-copy request telling Claude how to examine and critique the package.

## Folders

- `source/`: **working Python engine**; all required imports in `source/reference/`, tests in `source/tests/`. It is not just snippets or mock code.
- `sample_results/`: actual **two-year, small-scale SQLite history database**, independent audit and summary; also a no-archive one-year benchmark summary.
- `review_notes/`: original latest v0.13 handoff/report/remaining gates, original v0.6 start/continue/change report, archived v0.7 two-60-year test report and v0.8 expanded benchmark report.
- `original_design_docs/`: verbatim v0.10 feature design, v0.11 calendar/variable-format design, v0.12 ranking/qualification/scale test plan.
- `SHA256_MANIFEST.txt`: hashes for integrity/provenance of distributed files.
- `TEST_EXECUTION_LOG.txt`: the tests and archive audits rerun while building this handoff.

## Current engine reality in one paragraph

The latest v0.13 engine generates fictional worlds and runs variable-format tournament scores hole by hole with live pressure, cuts, pairings and prizes; the global calendar reserves the four majors and 40 combined top-tier events; selected qualifiers grant traced entries; weekly world rankings are **provisional**; a real SQLite archive preserves recorded holes and other event history. It has passed small-scale tests. It **does not yet** implement complete amateur/college systems, a robust weekly AI planner/full tour-card allocator, complete sponsor/prestige/staff ecosystems, a finished manager interface, nor a tested 6,000-golfer persistent 60-year world. Preserve that distinction.

## To give Claude everything

Upload **this entire ZIP**, not only `GAME_REQUIREMENTS_MASTER.md`. Ask it to read `START_HERE.md` and `CLAUDE_REVIEW_PROMPT.md` first. The source imports `source/reference` modules and will fail if those files are omitted. Claude can examine the included two-year DB without any credentials or internet access.

## Version lineage (simplified)

- v0.1–0.3: fictional golfer growth, early tournament and 30-year world tests; calibration of young careers.
- v0.4–0.6: more sophisticated golf ability, scoring concentration, finances and career survival; v0.6 handed off and audited.
- v0.7: home-country national opens and **two small-population 60-year scored worlds**.
- v0.8: 4,500-golfer / 33-circuit / 341-event single-season **capacity** benchmark.
- v0.9–v0.12: global 52-week calendar; four major blackouts; weekly AI design; variable tournament lengths; ranking/qualification design and test stages.
- **v0.13 latest working Python engine:** integrates calendar formats and selected qualifications, provisional ranking, scorecard database. **Not yet equivalent to full approved requirements**.

## Recommended first action

Ask Claude to run tests and audit, map design requirements to source, identify major implementation/realism gaps, then propose a narrow tested patch. Avoid a speculative wholesale framework switch until scoring/database benchmarks justify it. Future desktop plan is local-first Tauri/React UI + Rust scoring if helpful, but current engine is entirely standard-library Python.
