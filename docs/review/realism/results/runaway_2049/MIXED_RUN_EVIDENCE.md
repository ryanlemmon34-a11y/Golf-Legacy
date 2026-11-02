# Seed 2027: the mixed-version continuation, terminal evidence

Small extracts only. The raw world data (saves, run state, archive: about 1.2 GB) stays in the run directory
`/dev/shm/fw/dev2_2027_mixed` of the session machine; its hashes are below.

## 1. The original run stopped in 2049 (engine `d619dd6`)

`original_run_extract.log` has lines of `/dev/shm/fw/dev2_2027.log`:
- the start;
- seasons 2046–2048, all with reconcile errors 0+0;
- the worker's traceback ending `RuntimeError: Runaway hole: 60 strokes on hole 17 (engine bug)`;
- the main process's traceback through `run_world` → `s.run_year(y)`.

## 2. The continuation from the 2048 checkpoint (realism + fix `c528575`)

`mixed_continuation.log` is the whole terminal log of the continuation (1,980 bytes). It has:
- the provenance block it printed at start: both engines, and the 2048 checkpoint's save and state hashes
  (`95e03eec…640e`, `35cd2323…e9f2`);
- `resumed after 22 seasons (d619dd6666)`;
- seasons 2049–2054;
- the restart line `resumed after 27 seasons (c528575f96)`;
- seasons 2055 and 2056.

Every season line reads `reconcile errors 0+0, staff violations 0, population ok`.

The cumulative seconds reset at the restart. The first process was killed by the memory limit while writing its
save after 2054. Kernel log on the session machine:

```
[30592.942888] Memory cgroup out of memory: Killed process 29792 (python3) total-vm:3000712kB, anon-rss:2585960kB, file-rss:2692kB, shmem-rss:128kB, UID:0 pgtables:5276kB oom_score_adj:0
```

What happened next:
- The partial `seed_2027.save.tmp` was ignored.
- The last complete checkpoint was "seed 2027 after 2053": a save and a run state with 27 seasons.
- The run continued from that checkpoint on the same engine, with 1 worker; 2054 was replayed.

## 3. Completion: final save metadata and hashes

Final save header (`seed_2027.save`):

```
{'format': 'golf-legacy-save/1', 'commit': 'c528575f962220bb75f5076ea60ada564398d092',
 'engine': 'f0529419945617bc2c8431b04146f681360bd3c9', 'year': 2056, 'note': 'seed 2027 after 2056'}
```

Run outputs (sha256):

```
seed_2027.save           81dd24b605e2734b917c895a0d99c81183f079290f80821a1b1461486256d1b1
seed_2027.state.pkl      d4bf8501aef2a14af1d2290c8961801c44bef242505a2f707c33c77fe1731dfd
seed_2027.json.gz        2a36fc7d9f8a7a3a7be2e285391c6637c0232c0d83e3368b3f4404b137fe4e91
seed_2027.debug.json.gz  5d0af91f91a7faca6eb0393c6c9e3c5c70d4eb54142fc9e6544c6df924187396
PROVENANCE.json          be1b0fb435b7c42dd69954aad2f7d2ea643fa1f13e98750710ba664206289f91
manifest.json            799ae46983e657a45b9f901bca5fd844fff4906e3106ab12f76ae9f4d6e80c5b
```

- `PROVENANCE_mixed.json` (beside this file) is that `PROVENANCE.json`.
- It has `completion`: 30 contiguous seasons 2027–2056, the 2049 failure season crossed, and the final save engine
  `f0529419`.
- It has one `restarts` entry, for the out-of-memory kill.
- The run's `manifest.json` names the commit as `d619dd6 (seasons to 2048) + c528575 (seasons from 2049)` and
  records 30 completed seasons.
