"""Decision evidence on a played world (plays a season twice: run on its own, not with the quick tests).

- Outcome equivalence: the same small world and seed played through one archived season with the evidence kept and
  with it off (the parent build's behaviour: recording is the only difference) -- every part tools/equivalence_check
  digests (results, performance, development / ratings, finances and ledgers, staff, fatigue and injuries, rankings,
  records, moments, history, the published season without its `decision_evidence`) is identical. With
  GOLF_PARENT_CHECKOUT naming a checkout of the parent build (15374c9), the same world is also played there in a
  subprocess and its digests compared.
- The archived evidence: every golfer in the season file was evaluated by each of the season's 13 monthly plans; the
  target's parts add up; each plan's weeks are four availability codes and four activities; career rows agree with
  the winter's transitions; Archive.decision_evidence reads it back, and the season-file growth is reported.

Run from the project folder:  python -m unittest tests.test_decision_evidence_world -v
"""
from __future__ import annotations

import gzip
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
import equivalence_check as EQ                                          # noqa: E402
from golfsim import decision_evidence as DE                             # noqa: E402
from golfsim.archive import Archive, _read, read_manifest               # noqa: E402
from golfsim.population import generate_world                           # noqa: E402
from golfsim.session import Session                                     # noqa: E402

SEED, SCALE, WEEKS = 97, 0.03, 53                  # one season, archived (the winter's decisions included)

PARENT_SCRIPT = r'''
import json, sys
from pathlib import Path
sys.path.insert(0, '.')
sys.path.insert(0, 'tools')
import equivalence_check as EQ
from golfsim.population import generate_world
from golfsim.session import Session
d = Path(sys.argv[1])
s = Session.create(d, seed=int(sys.argv[2]), workers=1, world=generate_world(seed=int(sys.argv[2]), scale=float(sys.argv[3])))
s.advance(int(sys.argv[4]))
print(json.dumps(EQ.parts(s, d)))
s.close()
'''


def play(path, record):
    s = Session.create(path, seed=SEED, workers=1, world=generate_world(seed=SEED, scale=SCALE))
    s.season.record_decisions = record
    s.advance(WEEKS)
    parts = EQ.parts(s, path)
    year = s.season.first_year
    s.close()
    return parts, year


class DecisionEvidenceWorld(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.on, cls.year = play(cls.tmp / 'on', True)
        cls.off, _ = play(cls.tmp / 'off', False)
        a = cls.tmp / 'on' / 'archive'
        cls.season = _read(a / read_manifest(a)['files']['years'][cls.year])

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_outcomes_are_identical_with_recording_on_and_off(self):
        for k in self.on:
            if k != 'decision_evidence':
                self.assertEqual(self.on[k], self.off[k], k)
        self.assertIn('published', self.on)                               # (a season was archived and compared)
        self.assertNotEqual(self.on['decision_evidence'], self.off['decision_evidence'])   # (and kept only when on)

    @unittest.skipUnless(os.environ.get('GOLF_PARENT_CHECKOUT'), 'set GOLF_PARENT_CHECKOUT to a checkout of 15374c9')
    def test_outcomes_are_identical_to_the_parent_build(self):
        parent = Path(os.environ['GOLF_PARENT_CHECKOUT'])
        out = subprocess.run([sys.executable, '-c', PARENT_SCRIPT, str(self.tmp / 'parent'), str(SEED), str(SCALE),
                              str(WEEKS)], cwd=parent, capture_output=True, text=True, check=True)
        theirs = json.loads(out.stdout.strip().splitlines()[-1])
        for k in theirs:
            if k != 'decision_evidence':
                self.assertEqual(self.on[k], theirs[k], k)

    def test_the_archived_evidence(self):
        d, year = self.season, self.year
        blk = d['decision_evidence']
        self.assertEqual(blk['format'], DE.FORMAT)
        sch = blk['schedule']
        self.assertEqual(set(sch), set(d['careers']))                     # every golfer of the season, no one else
        weeks_played = {}
        for e in d['events']:
            for site in e['finish']:
                for gid, _, _ in site:
                    weeks_played.setdefault(str(gid), []).append(e['week'])
        for gid, rec in sch.items():
            self.assertEqual(rec['w'], 1)
            self.assertEqual(len(rec['n']), DE.PLAN_BLOCKS)
            self.assertEqual(len(rec['c']), DE.PLAN_BLOCKS * DE.CODE_LEN)
            self.assertNotIn('over', rec)
            for t in rec['t']:
                self.assertAlmostEqual(t[2] + t[3] + t[4], t[5], delta=0.011)
            self.assertEqual(rec['n'], sorted(rec['n']))                  # starts so far only grow
            for k, n in enumerate(rec['n']):                              # ... and match the season's editions
                self.assertEqual(n, sum(1 for w in weeks_played.get(gid, ()) if w < 1 + 4 * k), (gid, k))
            self.assertTrue(set(rec['c']) <= set('ouen') | set('PTRW'))
            self.assertTrue(all(0 <= x <= 100 for x in rec['x']))
        transitions = {(t['gid'], t.get('p')) for t in d['transitions'] if 'p' in t}
        for gid, rows in blk['careers'].items():
            self.assertLessEqual(len(rows), DE.CAREER_ROWS)
            for r in rows:
                if r[3]:
                    self.assertIn((int(gid), r[1]), transitions, (gid, r))

    def test_the_archive_reads_it_back(self):
        a = Archive(self.tmp / 'on' / 'archive')
        try:
            gid = next(iter(self.season['decision_evidence']['schedule']))
            got = a.decision_evidence(int(gid), self.year)
            self.assertTrue(got['recorded'])
            self.assertEqual(len(got['schedule']), DE.PLAN_BLOCKS)
            self.assertEqual(got, DE.read(self.season, gid))
        finally:
            a.close()
        b = Archive(self.tmp / 'off' / 'archive')                         # a season kept without it
        try:
            self.assertEqual(b.decision_evidence(int(gid), self.year), {'recorded': False})
        finally:
            b.close()

    def test_growth_is_small(self):
        ev = self.season['decision_evidence']
        rest = {k: v for k, v in self.season.items() if k != 'decision_evidence'}
        z = lambda o: len(gzip.compress(json.dumps(o, separators=(',', ':')).encode(), 6))
        growth = z(self.season) - z(rest)
        per_golfer = growth / len(ev['schedule'])
        print(f'\ndecision evidence: {growth} bytes ({100 * growth / z(rest):.1f}% of the season file), '
              f'{per_golfer:.0f} bytes a golfer-season', file=sys.stderr)
        self.assertLess(per_golfer, 200)                                 # measured 117-150 on small worlds


if __name__ == '__main__':
    unittest.main()
