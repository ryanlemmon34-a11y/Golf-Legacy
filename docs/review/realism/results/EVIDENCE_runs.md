# Run evidence manifest: seed-3031 same-fix pair, and the run data lost on 2026-11-02

Machine-readable copy: `EVIDENCE_runs.json` (same folder).

## Summary

- **The seed-3031 run directories no longer exist.** Both arms' saves, run states, analysis exports and history
  archives were held in RAM (`/dev/shm`, a tmpfs) because the container disk was below the 3 GB free-space floor.
  The container restarted (system boot 2026-11-02 12:06:05 UTC), and the RAM filesystem was emptied.
- **No SHA-256 of those run files was recorded before the loss.** Their final-save headers can't be read, so this
  manifest does not claim any.
- **What remains** is what was pushed to GitHub before the restart: both arms' complete run logs, their run
  manifests, and the comparison tables. They are hashed below.
- **No code was lost.** Every branch head used here matches GitHub.

## Storage: what is durable

| storage | survives a container restart | survives the container being reclaimed | used for |
|---|---|---|---|
| RAM, `/dev/shm` (tmpfs) | **no** (lost on 2026-11-02 at 12:06 UTC) | no | the run directories (lost) |
| Container disk: `/home/user`, `/tmp`, scratchpad | yes (it survived this restart) | **no**: a per-session allowance, not off-container | nothing from these runs |
| GitHub `origin` | yes | **yes**: the only durable off-container copy | the small files below |

## Seed 3031: exact sources

Both arms were run from frozen, clean checkouts (`dirty: false` in each manifest), started together at
2026-11-02 09:00:01, on one 4-CPU cloud machine:

| arm | commit | engine fingerprint | seasons | holes played | run minutes |
|---|---|---|---|---|---|
| main + fix (dev-1) | `46013a575753bcf0a6ee79aec5637bb55be9d5bb` | `2abe4dc851f0d6e79b5f74a903568a8bf2f0346c` | 30 (2027–2056) | 178,555,856 | 167.9 |
| realism + fix (dev-2) | `c528575f962220bb75f5076ea60ada564398d092` | `f0529419945617bc2c8431b04146f681360bd3c9` | 30 (2027–2056) | 178,402,048 | 166.4 |

- **Commits:** main + fix is `fix/engine-dogleg-retee`; realism + fix is the realism branch's `c528575`.
- **Command,** run in each checkout:
  `python3 tools/long_world.py --seeds 3031 --years 30 --workers 2 --out OUT_DIR`
- **Comparison:** `compare_worlds.py`, sha256 below. Its tables were committed in `f985cad`.

## Seed 3031: surviving files (GitHub, branch `build/realism-youth-aging-longirons`, commit `f985cad`)

Paths are relative to `docs/review/realism/`.

| file | sha256 | bytes |
|---|---|---|
| `results/seed3031_logs/mainfix_3031.log` | `4eac44ba1650f61b2462156618db4ad5096f60c10da92a9065d6014877bfe368` | 3,301 |
| `results/seed3031_logs/realfix_3031.log` | `f911d4ca97a3488121ad727564f12afee034362865ad8faaf7aa95b485986107` | 3,300 |
| `results/seed3031_logs/manifest_mainfix.json` | `37547d0027a0710ff840cbc807b402c4de246029b74cb1444996a36ec8876b6d` | 1,629 |
| `results/seed3031_logs/manifest_realfix.json` | `76866ed8e2a71c09262aef25ab4812f87350c3b87ec1b4e71fc11b32d65bf663` | 1,629 |
| `results/world_seed3031_samefix30.md` | `2da12e6e76fc11b84b0857ac0d13e36212c8f4d8c8c707922c79a68b230d96fd` | 7,648 |
| `compare_worlds.py` | `dff42fc262937f814fe64f8d225ae4adacbd11af04929bdac8c1a237c3186bbf` | 16,341 |

## Seed 3031: lost files (no hashes recorded)

Each arm's run directory was `/dev/shm/fw/mainfix_3031` or `/dev/shm/fw/realfix_3031`. It held:
- the final save, `seed_3031.save`. Its header records the format, commit, engine, year and note. It was written
  by the same checkout as that arm's manifest, so its commit and engine would match the manifest's, but the header
  itself was never read or hashed.
- the run state, `seed_3031.state.pkl`;
- the analysis exports, `seed_3031.json.gz` and `seed_3031.debug.json.gz`;
- the history archive, `archive_3031/`;
- the reports, `REPORT.md` and `DEBUG.md`;
- `manifest.json` (a copy of it is committed).

**Size:** 393 MB per arm when last measured, at about season 10 (09:56 UTC). The final sizes were not measured.
Completed 30-season runs on the same harness measured 1.2 GB (seed 2027, mixed) and 1.3 GB (seed 2027, main).

## Capacity: the exact gap for any on-disk copy

- **Free on the container disk now:** 2,329,825,280 bytes.
- **Floor:** 3,000,000,000 bytes. This is your standing floor and also `DISK_FLOOR` in `tools/long_world.py`.
- **Already below the floor by** 670,174,720 bytes, before anything is written.
- **Compression barely helps.** Measured on an existing 3-season seed-3031 run: the archive and the `.json.gz`
  exports shrink by at most about 4%; the save is already gzip; only the run state shrinks, about 4×.
- **Need:** both arms' compressed exports are an estimated 2.1–2.6 GB, from the comparable 30-season sizes above.
- **The gap:** an on-disk copy needs that amount plus the 0.67 GB deficit, about **2.8–3.3 GB** more disk than the
  floor allows.

## How a reproduction could be checked (not run)

The runs used fixed commits and a fixed seed. A rerun of each arm with the command above, from a clean checkout of
the same commit, could be checked against this evidence:
- every per-season line of the committed logs (active golfers, reconciliation, staff, population), ignoring the
  season times;
- the manifest's holes played (178,555,856 for main + fix and 178,402,048 for realism + fix);
- the comparison tables, regenerated by `compare_worlds.py` at the hash above.

No rerun has been made. It would take about 2.8 hours with both arms running together on 4 CPUs.

## Seed 2027 run data lost in the same restart

Lost: the run directories `main_2027` (main `18a8e23`, 30 seasons, 1.3 GB), `dev2_2027` (`d619dd6`, to 2048 and
the failed 2049, about 0.9 GB), `dev2_2027_mixed` (the mixed-version continuation, 1.2 GB) and `dev2_2027_s22`
(the 22-season export, 15 MB). Also lost: their console logs, except the two committed below.

Surviving on GitHub (same branch and commit; paths relative to `docs/review/realism/`):

| file | sha256 | bytes |
|---|---|---|
| `results/world_seed2027_s22.md` | `8845e693f98c47112182b0c23a8c30e17f27588140fc4914cfa21dc005f6edd1` | 6,986 |
| `results/world_seed2027_mixed30.md` | `bf2563cdcae555364e04e52aebe7562344d69688f2096f58680dbc0934d11ae3` | 7,762 |
| `results/runaway_2049/PROVENANCE_mixed.json` | `be1b0fb435b7c42dd69954aad2f7d2ea643fa1f13e98750710ba664206289f91` | 1,918 |
| `results/runaway_2049/mixed_continuation.log` | `680cc6ea8ccb6cf77ae14c7785f61cc02dbaa338eac0d1bcbe1416f35d289cb6` | 1,980 |
| `results/runaway_2049/original_run_extract.log` | `3a76732c28896441ddd25a19c4dad70e7beb5d2928c0ab217ef3e5576289b7b9` | 1,390 |
| `results/runaway_2049/hole17_state.pkl` | `acedf03c40b7fe8ce1a403d013782510a876ba046c6cf45f44ce38ef8e406490` | 12,339 |

The hashes of the mixed run's 2048 checkpoint were recorded before the loss, in `PROVENANCE_mixed.json`:
- save, `seed 2027 after 2048`: sha256 `95e03eecd848fca0c789025b3d92c3815eb8d5e977c56781215347ca18cd640e`;
- run state, last season 2048: sha256 `35cd232326eb506d1b786754028e6a37eec1295115eb0dafc332f59e4698e9f2`.

## Also lost from RAM, all reproducible or already published

- The projection raw output (46 MB). It can be regenerated with the command in `RESULTS.md`; its hash is recorded
  there.
- Temporary checkouts and scratch for the research, headroom and readiness studies. Their branches are on GitHub.
- The worktree entries that pointed into `/dev/shm` are now stale. They have not been pruned.
