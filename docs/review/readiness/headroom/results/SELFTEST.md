# Headroom study self-test: negative cases for validation and the gates

Output of `selftest.sh` against run 66ec74cd4272f01c (scratch copies in /dev/shm; the original fixture and stamp are never written). Each case must exit with the stated code and name the stated failure; the script exits 1 otherwise.

| case | wanted exit | got | must name | result |
|---|---|---|---|---|
| N1 subset of years | 1 | 1 | F1 cohort boundary | PASS |
| N2 wrong baseline (A1 as A0) | 1 | 1 | F2 every cohort passes a-e: .*\(2041, 'juniors'\) | PASS |
| N3 tampered allocation (2050 juniors) | 1 | 1 | F5 .*found \[\[2050, 'juniors'\] | PASS |
| N4 tampered total (2050 juniors) | 1 | 1 | F2 every cohort passes a-e: .*\(2050, 'juniors'\) | PASS |
| N5 full years, wrong baseline | 1 | 1 | F4 tail counts | PASS |
| N6 headroom arm wider than declared (B2 knee 27.5 checked as 25.5) | 1 | 1 | F7 headroom arms change only what they declare: .*untouched candidate changed | PASS |
| T1 unit tests of the transform and arms | 0 | 0 | ^OK | PASS |
N5 stamp passed False checks [['F1 cohort boundary', True], ['F2 every cohort passes a-e', False], ['F3 junior reconciliation', True], ['F4 tail counts and top junior', False], ['F5 allocation discrepancies are exactly the documented one', True], ['F7 headroom arms change only what they declare', True], ['F6 not a negative-test run', False]]
| R1 runner, no stamp | 2 | 2 | no validation stamp | PASS |
| R2 runner, failed stamp | 2 | 2 | validation did not pass | PASS |
| R3 runner, stale stamp (study.py edited) | 2 | 2 | stale validation: study.py | PASS |
| R4 runner, current passing stamp | 0 | 0 | validation stamp ok | PASS |
| R5 report, failed stamp | 2 | 2 | validation did not pass | PASS |
| R6 report, current passing stamp | 0 | 0 | Headroom study: results | PASS |

selftest: 0 case(s) not as stated
rc=0
