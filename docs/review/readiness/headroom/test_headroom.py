"""Unit tests of the headroom arms (experiment only).

    python3 -I -m unittest -v test_headroom      (from this folder; STUDY_CHECKOUT=<checkout>, default: this repo)
"""
import importlib.util
import os
import random
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
CHECKOUT = os.environ.get('STUDY_CHECKOUT', os.path.abspath(os.path.join(HERE, *['..'] * 4)))
import study as S  # noqa: E402
import plan_table as PT  # noqa: E402

S.setup(CHECKOUT)
B = [S.ARMS[a] for a in S.HEADROOM_ARMS]


def grid(lo=10.0, hi=36.0, step=0.01):
    n = int(round((hi - lo) / step))
    return [lo + i * step for i in range(n + 1)]


class Transform(unittest.TestCase):
    def test_identity_at_and_above_the_knee(self):
        for arm in B:
            K = arm.knee[0]
            for p in [K, K + 1e-9, 26.0, 27.0, 31.5, 40.0]:
                if p >= K:
                    self.assertEqual(S.tempo(arm, p, 0.0), p)

    def test_monotone_and_never_earlier(self):
        for arm in B:
            prev = None
            for p in grid():
                t = S.tempo(arm, p, 0.0)
                self.assertGreaterEqual(t, p - 1e-12)
                if prev is not None:
                    self.assertGreaterEqual(t, prev - 1e-12)
                prev = t

    def test_continuous_slope(self):
        """C1: the slope is 1 above K, s below K - w, and continuous at both joins."""
        for arm in B:
            K, w, s = arm.knee
            d = lambda x, e=1e-6: (S.tempo(arm, x + e, 0.0) - S.tempo(arm, x - e, 0.0)) / (2 * e)
            for x in (K, K - w):
                left = (S.tempo(arm, x, 0.0) - S.tempo(arm, x - 1e-7, 0.0)) / 1e-7
                right = (S.tempo(arm, x + 1e-7, 0.0) - S.tempo(arm, x, 0.0)) / 1e-7
                self.assertAlmostEqual(left, right, places=4)
            self.assertAlmostEqual(d(K + 1), 1.0, places=6)
            self.assertAlmostEqual(d(K - w - 1), s, places=6)
            for x in (K, K - w):                          # continuous values
                self.assertAlmostEqual(S.tempo(arm, x - 1e-9, 0.0), S.tempo(arm, x + 1e-9, 0.0), places=6)

    def test_low_gap_tail_is_continuous_without_a_floor(self):
        """Earlier draws keep the smallest headroom: headroom keeps falling as p falls (no floor, no star class)."""
        for arm in B:
            hs = [S.deficit(18, S.tempo(arm, p, 0.0), p, 1.0) for p in (24.0, 22.0, 20.0, 18.0, 16.0, 14.0)]
            self.assertEqual(hs, sorted(hs, reverse=True))
            self.assertTrue(all(a > b for a, b in zip(hs, hs[1:])))

    def test_headroom_never_below_a0(self):
        for arm in B:
            for p in grid(14.0, 30.0, 0.05):
                self.assertGreaterEqual(S.deficit(18, S.tempo(arm, p, 0.0), p, 1.0), S.deficit(18, p, p, 1.0) - 1e-12)

    def test_plan_table(self):
        rows, shares = PT.table()
        z3 = [hs for z, p, hs in rows if z == -3][0]
        self.assertEqual([round(h, 2) for h in z3], [1.98, 3.39, 4.99])
        z5 = [hs for z, p, hs in rows if z == -5][0]
        self.assertEqual([round(h, 2) for h in z5], [0.0, 1.27, 3.39])


class Candidates(unittest.TestCase):
    def cand(self, kind='juniors', pot=80.0, peak=21.0, luck=3.0, age=18):
        # (pot, peak, aging, luck, eps, u_keep, scout, age, u_status, u_club, u_sample)
        return (pot, peak, 1.0, luck, 0.0, 0.0, 0.0, age, 0.0, 0.9, 0.0)

    def test_potential_target_kept_and_promotion_effect_separate(self):
        c = self.cand(pot=80.0, peak=21.0, luck=3.0)       # A0 entry 80 - 1.98 + 3 = 81.02 > 80: promoted
        _, r0, _ = S.paired_outcome('juniors', c, 'USA', S.ARMS['A0'])
        _, r2, f2 = S.paired_outcome('juniors', c, 'USA', S.ARMS['B2'])
        _, rp, _ = S.paired_outcome('juniors', c, 'USA', S.ARMS['B2p'])
        self.assertGreater(r0[4], 80.0)
        self.assertEqual(r0[2], r0[4])                    # A0 stores the promoted entry overall
        self.assertEqual(r2[2], r0[2])                    # B2 keeps A0's target
        self.assertLess(r2[4], r0[4])                     # ... with a lower entry
        self.assertLess(rp[2], r0[2])                     # B2p: the production rule lowers stored potential
        self.assertEqual(rp[2], max(80.0, rp[4]))

    def test_untouched_candidate_identical(self):
        c = self.cand(pot=75.0, peak=27.3, luck=-1.0)
        for arm in B:
            ref = S.ARMS['A1'] if arm.cap_first else S.ARMS['A0']
            self.assertEqual(S.paired_outcome('juniors', c, 'USA', arm)[:2], S.paired_outcome('juniors', c, 'USA', ref)[:2])

    def test_new_professional_rule_is_age_coherent(self):
        c = self.cand(kind='new_pros', pot=70.0, peak=21.5, luck=0.5, age=23)
        for arm in B:
            _, _, f = S.paired_outcome('new_pros', c, 'USA', arm)
            t = f['tempo']
            self.assertEqual(f['cur18'], 70.0 - S.deficit(18, t, 21.5, 1.0) + 0.5)
            self.assertEqual(f['cur'], 70.0 - S.deficit(23, t, 21.5, 1.0) + 0.5)

    def test_selection_reads_only_observable_ability(self):
        """Two candidates with the same entry overall and coins are kept alike whatever their hidden potential."""
        a = self.cand(pot=70.0, peak=27.0, luck=0.0)
        cur = S.paired_outcome('juniors', a, 'USA', S.ARMS['B2'])[2]['cur18']
        for arm in B:
            rng = random.Random(3)
            for _ in range(200):
                u, sc = rng.random(), rng.gauss(0, 4)
                x = (70.0, 27.0, 1.0, 0.0, 0.0, u, sc, 18, 0.0, 0.9, 0.0)
                y = (80.0, 27.0, 1.0, cur - (80.0 - S.deficit(18, 27.0, 27.0, 1.0)), 0.0, u, sc, 18, 0.0, 0.9, 0.0)
                self.assertEqual(S.paired_outcome('juniors', x, 'USA', arm)[0],
                                 S.paired_outcome('juniors', y, 'USA', arm)[0])

    def test_a0_unchanged_from_the_reviewed_library(self):
        """A0 and A1 outcomes equal the reviewed study's library (5c7dce9) on paired candidates."""
        spec = importlib.util.spec_from_file_location('reviewed_study', os.path.join(HERE, '..', 'study', 'study.py'))
        R = importlib.util.module_from_spec(spec)
        sys.modules['reviewed_study'] = R                 # (dataclasses need the module registered)
        spec.loader.exec_module(R)
        R.setup(CHECKOUT)
        n = 0
        for kind in ('juniors', 'new_pros'):
            for country in ('USA', 'Argentina', 'Fiji'):
                cands = S.paired_candidates(kind, 2041, 11, country)
                self.assertEqual(cands, R.paired_candidates(kind, 2041, 11, country))
                for c in cands:
                    for a in ('A0', 'A1'):
                        self.assertEqual(S.paired_outcome(kind, c, country, S.ARMS[a])[:2],
                                         R.paired_outcome(kind, c, country, R.ARMS[a])[:2])
                        n += 1
        self.assertGreater(n, 10000)


if __name__ == '__main__':
    unittest.main()
