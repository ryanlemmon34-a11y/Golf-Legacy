# Verification Checklist for Claude

Before changing code, please replicate these tests from the extracted handoff directory:

1. `cd source && python -m unittest discover -s tests -v` (8/8 should pass)
2. `python audit_v013.py ../sample_results/two_season_final.sqlite` (should pass, 243 events, 986,832 holes)
3. `python engine_v013.py --seed 1217 --population 450 --years 1 --events-scale 0.08 --stop-week 52 --db ../fresh_review.sqlite --out ../fresh_review_results --quiet`
4. `python audit_v013.py ../fresh_review.sqlite` (should pass, roughly 75 events; fixed seed and same implementation expected)
5. Inspect exact scorecard data in `rounds`, audit live pressure/pairing input logic, and enumerate weaknesses not caught by current unit tests.
6. Validate SHA-256 checksums in `SHA256_MANIFEST.txt` using `python VERIFY_PACKAGE.py` from root.

Any change to scoring math or field allocation will change seeded outcomes. Keep clear version history, justify each algorithm change, and record before/after results; do not claim regression equivalence solely because fields changed but no exceptions occurred.
