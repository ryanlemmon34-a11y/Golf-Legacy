"""Nations' shares of the new golfers, rounded fairly over time (rules 2026-11-13; population.allocate_with_carry).

Each year's fixed total is split by the shares as before, but each nation's unrounded fraction is carried forward
instead of being dropped, so a small nation with a positive share is not shut out for ever. Invariants: the total
is exactly the year's total; the carries keep their sum (0 from a world's start); every carry stays within (-1, 2)
(never more than one place ahead, never more than about one behind -- two only after a year places are taken back);
deterministic; no minimum place and no extra golfers. Worlds saved before the rule keep the year-by-year rounding.

The fixed-input replay uses the 57 seasons of shares and totals archived in the Test2 world (seed 386509, engine
1949ff63): tests/data/test2_nation_shares.json.gz (shares and totals per entrant season and pathway, as recorded).

Run from the project folder:  python -m unittest tests.test_nation_quota_carry -v
"""
from __future__ import annotations

import gzip
import json
import pickle
import random
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from golfsim import participation as PT                                   # noqa: E402
from golfsim import population as P                                       # noqa: E402
from golfsim import rules as R                                            # noqa: E402
from golfsim.nations import nations                                       # noqa: E402

DATA = Path(__file__).resolve().parent / 'data' / 'test2_nation_shares.json.gz'


def run(totals_and_shares, carry_on=True):
    """[(total, shares)] year by year -> (allocations, carries after each year)."""
    carry, allocs, carries = {}, [], []
    for total, shares in totals_and_shares:
        if carry_on:
            a, carry = P.allocate_with_carry(total, shares, carry)
        else:
            a = P.allocate(total, shares)
        allocs.append(a)
        carries.append(dict(carry))
    return allocs, carries


class Invariants(unittest.TestCase):
    def random_years(self, seed, years=600, nations_n=57):
        rng = random.Random(seed)
        names = [f'N{i:02d}' for i in range(nations_n)]
        base = {c: rng.random() ** 3 for c in names}          # a few large, many tiny
        out = []
        for y in range(years):
            m = {c: base[c] * rng.uniform(0.25, 4) for c in names}
            if y % 50 == 7:
                m[names[3]] = 0.0                             # a share that drops to nothing for a year
            out.append((rng.choice((0, 1, 5, 669, 727, 778)) if y % 97 == 0 else rng.randint(669, 778), m))
        return out

    def test_exact_totals_bounded_carries_conserved_sum(self):
        for seed in range(6):
            years = self.random_years(seed)
            allocs, carries = run(years)
            for (total, _), a, c in zip(years, allocs, carries):
                self.assertEqual(sum(a.values()), total)
                self.assertTrue(all(v >= 0 for v in a.values()))
                self.assertAlmostEqual(sum(c.values()), 0.0, places=6)
                self.assertTrue(all(-1 < v < 2 for v in c.values()), min(c.values()))

    def test_cumulative_allocation_tracks_cumulative_quota(self):
        years = self.random_years(11)
        allocs, _ = run(years)
        cum_q, cum_a = {}, {}
        for (total, shares), a in zip(years, allocs):
            sh = P.normalised(shares)
            for c in sh:
                cum_q[c] = cum_q.get(c, 0.0) + total * sh[c]
                cum_a[c] = cum_a.get(c, 0) + a[c]
                self.assertLess(abs(cum_q[c] - cum_a[c]), 2.0)    # never further than the carry bound

    def test_deterministic_and_order_independent(self):
        years = self.random_years(3, years=40)
        a1, c1 = run(years)
        a2, c2 = run([(t, dict(reversed(list(s.items())))) for t, s in years])
        self.assertEqual(a1, a2)
        self.assertEqual(c1, c2)

    def test_ties_by_larger_quota_then_name(self):
        a, c = P.allocate_with_carry(1, {'B': 0.5, 'A': 0.5}, {})
        self.assertEqual(a, {'A': 1, 'B': 0})                  # the same tie rule as allocate
        a, c = P.allocate_with_carry(1, {'B': 0.5, 'A': 0.5}, c)
        self.assertEqual(a, {'A': 0, 'B': 1})                  # B is now owed the place
        self.assertEqual(c, {'A': 0.0, 'B': 0.0})

    def test_without_carry_it_is_the_earlier_rounding(self):
        years = self.random_years(5, years=30)
        self.assertEqual(run(years, carry_on=False)[0], [P.allocate(t, s) for t, s in years])

    def test_small_shares_get_places_over_time_and_never_borrow(self):
        """Morocco, Poland and Fiji style: quotas of 0.2, 0.05 and 0.6 a golfer a year among large nations."""
        shares = {'Big': 700.0, 'Mid': 26.15, 'Morocco': 0.2, 'Poland': 0.05, 'Fiji': 0.6}
        years = [(727, shares)] * 100
        before = run(years, carry_on=False)[0]
        after, carries = run(years)
        self.assertEqual([sum(a[c] for a in before) for c in ('Morocco', 'Poland', 'Fiji')], [0, 0, 100])
        # (the old rounding: never for the two smallest, and one EVERY year for a 0.6 remainder -- 100, not 60)
        for c, q in (('Morocco', 0.2), ('Poland', 0.05), ('Fiji', 0.6)):
            got = sum(a[c] for a in after)
            self.assertAlmostEqual(got, 100 * q, delta=1.0)                  # about its quota over time
            self.assertTrue(all(a[c] <= 1 for a in after))                   # one at a time, never a run ahead
        self.assertEqual([sum(a.values()) for a in after], [727] * 100)

    def test_zero_and_tiny_totals(self):
        a, c = P.allocate_with_carry(0, {'A': 0.5, 'B': 0.5}, {'A': 0.9, 'B': -0.9})
        self.assertEqual(a, {'A': 0, 'B': 0})
        self.assertEqual(c, {'A': 0.9, 'B': -0.9})                         # nothing to give: owed stays owed
        a, c = P.allocate_with_carry(1, {'A': 0.5, 'B': 0.5}, {'A': 0.9, 'B': -0.9})
        self.assertEqual(a, {'A': 1, 'B': 0})

    def test_places_taken_back_when_whole_parts_exceed_the_total(self):
        a, c = P.allocate_with_carry(2, {'A': 1, 'B': 1, 'C': 1, 'D': 0, 'E': 0},
                                     {'A': 1/3, 'B': 1/3, 'C': 1/3, 'D': -0.9, 'E': -0.1})
        self.assertEqual(sum(a.values()), 2)
        self.assertAlmostEqual(sum(c.values()), 0.0)
        self.assertTrue(all(-1 < v < 2 for v in c.values()))


class UnsupportedLedgers(unittest.TestCase):
    """A ledger no world reaches (review repro, exact fractions): it is rejected with a clear error before anything
    is generated or recorded, instead of silently giving the wrong total."""

    def ledger(self):
        from fractions import Fraction as F
        shares = {'A': F(1, 2), 'B': F(1, 2), **{c: F(0) for c in 'CDEFG'}}
        carry = {'A': F(19, 10), 'B': F(19, 10), **{c: F(-19, 25) for c in 'CDEFG'}}
        self.assertEqual(sum(carry.values()), 0)                          # it sums to 0, inside (-1, 2)
        return shares, carry

    def test_rejected_not_silently_wrong(self):
        shares, carry = self.ledger()
        with self.assertRaises(P.CarryLedgerError) as cm:
            P.allocate_with_carry(1, shares, carry)
        self.assertIn('a total of 1 would give 2 places', str(cm.exception))

    def test_nothing_generated_or_recorded(self):
        shares, carry = self.ledger()
        prof = {c: p for c, p in list(nations().items())[:7]}
        names = list(prof)
        sh = {names[i]: shares[k] for i, k in enumerate('ABCDEFG')}
        cy = {names[i]: carry[k] for i, k in enumerate('ABCDEFG')}
        rep = {}
        one = lambda kind, year, seed, profiles: {c: ((['row'] if c == names[0] else []), None) for c in profiles}
        with mock.patch.object(P, 'existing_rule', one), self.assertRaises(P.CarryLedgerError):   # a total of 1
            P.entrant_rows('juniors', 2031, 7, prof, shares=sh, report=rep, carry=cy)
        self.assertEqual(rep, {})                                         # no report: nothing allocated
        pt = PT.Participation(prof, 2027)
        before = (dict(pt.carry['juniors']), dict(pt.carry_settled), dict(pt.history))
        with self.assertRaises(P.CarryLedgerError):
            P.allocate_with_carry(1, sh, cy)
        self.assertEqual((pt.carry['juniors'], pt.carry_settled, pt.history), before)

    def test_carry_for_an_unknown_nation_is_rejected(self):
        with self.assertRaises(P.CarryLedgerError):
            P.allocate_with_carry(5, {'A': 1.0}, {'Z': 0.5})

    def test_every_reachable_settlement_meets_the_postcondition(self):
        """From an empty ledger, years of varying exact-fraction shares and totals never raise."""
        from fractions import Fraction as F
        rng = random.Random(41)
        names = [f'N{i}' for i in range(9)]
        carry = {}
        for _ in range(3000):
            sh = {c: F(rng.randint(0, 40), 7) for c in names}
            if not any(sh.values()):
                sh[names[0]] = F(1)
            total = rng.choice((0, 1, 2, 3, rng.randint(0, 50)))
            out, carry = P.allocate_with_carry(total, sh, carry)
            self.assertEqual(sum(out.values()), total)
            self.assertEqual(sum(carry.values()), 0)


class InTheWorld(unittest.TestCase):
    def test_participation_carries_saves_and_repeats(self):
        pt = PT.Participation(nations(), 2027)
        self.assertTrue(pt.carry_on)
        c0 = pt.carry_for('juniors', 2028)
        self.assertEqual(c0, {})
        alloc, after = P.allocate_with_carry(700, pt.shares('juniors'), c0)
        pt.record(2028, 'juniors', {'total': 700, 'allocated': alloc, 'existing': {}, 'carry_before': c0,
                                    'carry_after': after})
        self.assertEqual(pt.carry_for('juniors', 2029), after)
        self.assertEqual(pt.carry_for('juniors', 2028), c0)               # a repeat of 2028 starts the same
        back = pickle.loads(pickle.dumps(pt))
        self.assertEqual(back.carry_for('juniors', 2029), after)
        self.assertEqual(pt.history[2028]['carry']['juniors'], {c: round(v, 6) for c, v in after.items()})

    def test_saves_from_before_keep_the_year_by_year_rounding(self):
        pt = PT.Participation(nations(), 2027)
        st = dict(pt.__dict__)
        for k in ('carry_on', 'carry', 'carry_settled'):
            st.pop(k)
        old = PT.Participation.__new__(PT.Participation)
        old.__setstate__(st)
        self.assertFalse(old.carry_on)
        self.assertIsNone(old.carry_for('juniors', 2030))

    def test_entrant_rows_total_and_report(self):
        prof = nations()
        rep, carry = {}, {}
        rows = P.entrant_rows('juniors', 2031, 7, prof, shares=P.expected_shares('juniors', prof), report=rep,
                              carry=carry)
        self.assertEqual(len(rows), rep['total'])
        self.assertEqual(sum(rep['allocated'].values()), rep['total'])
        self.assertEqual(rep['carry_before'], {})
        self.assertAlmostEqual(sum(rep['carry_after'].values()), 0.0, places=9)

    def test_versioned(self):
        self.assertGreaterEqual(R.RULES_VERSION, '2026-11-13')
        self.assertIn('2026-11-13', dict(R.VERSIONS))
        self.assertIn('carried forward', R.RULES['nation-shares'][1])


@unittest.skipUnless(DATA.exists(), 'the Test2 share fixture is not present')
class Test2Replay(unittest.TestCase):
    """Fixed inputs: the 57 seasons of shares and totals as the Test2 world recorded them (no world is played)."""

    @classmethod
    def setUpClass(cls):
        cls.d = json.load(gzip.open(DATA, 'rt'))

    def series(self, kind):
        return [(self.d['years'][y]['totals'][kind], self.d['years'][y]['shares'][kind])
                for y in sorted(self.d['years'], key=int) if kind in self.d['years'][y].get('totals', {})]

    def test_recorded_allocations_are_the_year_by_year_rounding(self):
        """The recorded allocations are allocate() of the recorded shares, except where two remainders are closer
        than the shares' 6-decimal rounding can tell apart (one such year-pathway: 2061 juniors, Sweden and Norway,
        remainders 0.461843 and 0.461838)."""
        close = 0
        for kind in ('juniors', 'new_pros'):
            ys = sorted((y for y in self.d['years'] if kind in self.d['years'][y].get('allocated', {})), key=int)
            for y in ys:
                r = self.d['years'][y]
                a, want = P.allocate(r['totals'][kind], r['shares'][kind]), r['allocated'][kind]
                if a != want:
                    sh, t = P.normalised(r['shares'][kind]), r['totals'][kind]
                    rem = [t * sh[c] % 1 for c in a if a[c] != want[c]]
                    self.assertLess(max(rem) - min(rem), t * 57 * 0.5e-6, (kind, y))
                    close += 1
        self.assertLessEqual(close, 1)

    def test_every_positive_share_nation_receives_entrants_over_57_years(self):
        never_before, never_after = set(), set()
        for kind in ('juniors', 'new_pros'):
            ser = self.series(kind)
            old = run(ser, carry_on=False)[0]
            new, carries = run(ser)
            cum_q = {}
            for (total, sh), a in zip(ser, new):
                self.assertEqual(sum(a.values()), total)
                for c, s in P.normalised(sh).items():
                    cum_q[c] = cum_q.get(c, 0.0) + total * s
            for c in cum_q:
                got_old, got_new = sum(a[c] for a in old), sum(a[c] for a in new)
                self.assertLess(abs(cum_q[c] - got_new), 2.0, (kind, c))
                if cum_q[c] >= 1.0:
                    self.assertGreaterEqual(got_new, 1, (kind, c))           # owed at least one: received one
            never_before |= {c for c in cum_q if sum(a[c] for a in old) == 0}
            never_after |= {c for c in cum_q if sum(a[c] for a in new) == 0}
        both = {c for c in never_before if all(sum(a[c] for a in run(self.series(k), carry_on=False)[0]) == 0
                                               for k in ('juniors', 'new_pros'))}
        self.assertEqual(len(both), 14)                                        # as the review found
        self.assertTrue(never_after < never_before)


if __name__ == '__main__':
    unittest.main()
