"""Nations' shares of the fixed new-golfer cohorts (rules 2026-11-05; owner decision D7; golfsim/participation.py and
population.entrant_rows): prestige never adds or removes a golfer -- it only moves how each year's fixed number is
shared between nations -- and never changes a nation's talent, or anyone's nationality.

Run from the project folder:  python -m unittest tests.test_nation_shares -v
"""
from __future__ import annotations

import inspect
import math
import pickle
import random
import statistics as S
import sys
import unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from golfsim import participation as PT                                   # noqa: E402
from golfsim import population as P                                       # noqa: E402
from golfsim.nations import nations                                       # noqa: E402

SEED = 2027


# ---- the rule as it stood before rules 2026-11-05 (verbatim loops from population.py at 87c2a21) -----------------
def old_juniors(year, seed, profiles):
    rows = []
    for country, prof in profiles.items():
        n = max(0, round(prof.pool * P.CANDIDATES_PER_POOL * P.JUNIOR_SHARE))
        mu = P.BASE_POTENTIAL + P.DEV_EFFECT * (prof.development - 60)
        crng = random.Random(f'{seed}:juniors:{year}:{country}')
        for _ in range(n):
            pot = crng.gauss(mu, P.POTENTIAL_SD)
            peak = crng.gauss(27.0, 2.0)
            aging = math.exp(crng.gauss(0, 0.3))
            cur = pot - P.age_deficit(18, peak, aging) + crng.gauss(0, P.CAREER_LUCK_SD)
            if cur < P.KEEP_OVERALL:
                continue
            cur = min(cur, 99.0)
            pot = max(min(pot, 99.0), cur)
            if P._keep_young(cur, 18, crng.random(), crng.gauss(0, P.SCOUTING_SD)):
                rows.append((country, 18, pot, peak, cur, 'amateur', aging))
    return rows


def old_new_pros(year, seed, profiles):
    rows = []
    for country, prof in profiles.items():
        n = max(0, round(prof.pool * P.CANDIDATES_PER_POOL * P.JUNIOR_SHARE * P.NEW_PRO_SCALE))
        mu = P.BASE_POTENTIAL + P.DEV_EFFECT * (prof.development - 60)
        crng = random.Random(f'{seed}:new-pros:{year}:{country}')
        for _ in range(n):
            pot = crng.gauss(mu, P.POTENTIAL_SD)
            peak = crng.gauss(27.0, 2.0)
            aging = math.exp(crng.gauss(0, 0.3))
            luck = crng.gauss(0, P.CAREER_LUCK_SD)
            age = crng.choice(P.NEW_PRO_AGES)
            cur18 = pot - P.age_deficit(18, peak, aging) + luck
            tracked = cur18 >= P.KEEP_OVERALL and P._keep_young(cur18, 18, crng.random(), crng.gauss(0, P.SCOUTING_SD))
            cur = pot - P.age_deficit(age, peak, aging) + luck
            if tracked or cur < P.KEEP_OVERALL:
                continue
            cur = min(cur, 99.0)
            pot = max(min(pot, 99.0), cur)
            if P._status(max(age, 23), cur, prof, crng.random(), crng) != 'pro':
                continue
            if crng.random() < P._keep_probability('pro', age, cur):
                rows.append((country, age, pot, peak, cur, 'pro', aging))
    return rows


OLD = {'juniors': old_juniors, 'new_pros': old_new_pros}
PROFILES = nations()


def skewed(kind, boost, factor):
    """Expected shares with `boost` multiplied by `factor` (normalised): another prestige allocation."""
    base = P.expected_shares(kind, PROFILES)
    return P.normalised({c: s * (factor if c == boost else 1.0) for c, s in base.items()})


class TotalsAndAllocation(unittest.TestCase):
    def test_the_total_is_the_existing_rules_whatever_the_shares(self):
        for kind in P.PATHWAYS:
            for year in (2030, 2041):
                old = OLD[kind](year, SEED, PROFILES)
                counts = Counter(r[0] for r in old)
                for shares in (None, skewed(kind, 'Fiji', 30.0), skewed(kind, 'USA', 0.25), skewed(kind, 'Japan', 3.0)):
                    rep = {}
                    rows = P.entrant_rows(kind, year, SEED, PROFILES, shares=shares, report=rep)
                    self.assertEqual(len(rows), len(old), (kind, year))           # never one more or fewer
                    self.assertEqual(rep['total'], len(old))
                    self.assertEqual(rep['existing'], {c: counts.get(c, 0) for c in PROFILES})
                    self.assertEqual(Counter(r[0] for r in rows), {c: n for c, n in rep['allocated'].items() if n})

    def test_existing_rule_draws_are_reused_exactly(self):
        """With each nation allocated exactly what the existing rule gave it, the rows are the existing rule's."""
        for kind in P.PATHWAYS:
            old = OLD[kind](2033, SEED, PROFILES)
            counts = Counter(r[0] for r in old)
            shares = {c: counts.get(c, 0) / len(old) for c in PROFILES}
            rows = P.entrant_rows(kind, 2033, SEED, PROFILES, shares=shares)
            self.assertEqual(sorted(rows), sorted(old))

    def test_allocation_sums_and_is_reproducible(self):
        shares = P.expected_shares('juniors', PROFILES)
        for total in (0, 1, 7, 100, 301):
            a = P.allocate(total, shares)
            self.assertEqual(sum(a.values()), total)
            self.assertEqual(a, P.allocate(total, dict(reversed(list(shares.items())))))   # order-independent
            for c, k in a.items():
                self.assertLess(abs(k - total * shares[c]), 1.0)
        tie = P.allocate(1, {'B': 0.5, 'A': 0.5})
        self.assertEqual(tie, {'A': 1, 'B': 0})                               # ties: by name

    def test_shares_sum_to_one(self):
        pt = PT.Participation(PROFILES, 2027)
        rng = random.Random(4)
        for _ in range(5):
            for c in pt.multiplier:
                pt.multiplier[c] = rng.uniform(PT.MULT_MIN, PT.MULT_MAX)
            for kind in P.PATHWAYS:
                self.assertAlmostEqual(sum(pt.shares(kind).values()), 1.0, places=12)
                self.assertAlmostEqual(sum(pt.base_share[kind].values()), 1.0, places=12)

    def test_a_rising_nation_gains_exactly_what_the_others_lose(self):
        """The owner's example: a nation holding 1 of 100 places rises to 2; the total stays 100 and the
        others lose exactly 1 between them (none gains)."""
        pt = PT.Participation(PROFILES, 2027)
        before = P.allocate(100, pt.shares('juniors'))
        self.assertEqual(sum(before.values()), 100)
        done = False
        for c in sorted(before, key=lambda c: (-pt.base_share['juniors'][c], c)):
            if before[c] != 1:
                continue
            pt.multiplier = {k: 1.0 for k in pt.multiplier}
            pt.multiplier[c] = 2.0
            after = P.allocate(100, pt.shares('juniors'))
            if after[c] != 2:
                continue
            self.assertEqual(sum(after.values()), 100)
            others = [k for k in before if k != c]
            self.assertEqual(sum(before[k] - after[k] for k in others), 1)
            self.assertTrue(all(after[k] <= before[k] for k in others))
            done = True
            break
        self.assertTrue(done, 'no nation holding exactly 1 of 100 places to test with')
        # and with real golfers: the same year's juniors, the nation's share doubled
        kind, year = 'juniors', 2031
        base = P.expected_shares(kind, PROFILES)
        c = next(k for k in sorted(base, key=lambda k: -base[k]) if 0.004 < base[k] < 0.02)
        r0, r1 = {}, {}
        a = P.entrant_rows(kind, year, SEED, PROFILES, report=r0)
        b = P.entrant_rows(kind, year, SEED, PROFILES, shares=skewed(kind, c, 2.0), report=r1)
        self.assertEqual(len(a), len(b))
        gain = r1['allocated'][c] - r0['allocated'][c]
        self.assertGreater(gain, 0)
        self.assertEqual(sum(r0['allocated'][k] - r1['allocated'][k] for k in PROFILES if k != c), gain)


class SmoothingAndBounds(unittest.TestCase):
    def test_prestige_scale_and_small_samples(self):
        self.assertEqual(PT.nation_prestige([])[0], 50.0)                      # no evidence: as expected
        self.assertAlmostEqual(PT.nation_prestige([(10.0, 10.0)] * 5)[0], 50.0)
        big = PT.nation_prestige([(2000.0, 1000.0)] * 5)[0]
        self.assertAlmostEqual(big, 50 + 25 * math.log2((2000 * 4 + PT.NATION_PSEUDO) / (1000 * 4 + PT.NATION_PSEUDO)))
        small = PT.nation_prestige([(20.0, 10.0)] * 5)[0]                     # the same ratio, a tiny sample
        self.assertLess(abs(small - 50), abs(big - 50) / 3)
        self.assertEqual(PT.nation_prestige([(1e9, 1.0)])[0], 100.0)
        self.assertEqual(PT.nation_prestige([(0.0, 1e9)])[0], 0.0)

    def test_multiplier_level_and_yearly_change_are_bounded(self):
        self.assertAlmostEqual(PT.target_multiplier(50), 1.0)
        self.assertAlmostEqual(PT.target_multiplier(100), PT.MULT_MAX)
        self.assertAlmostEqual(PT.target_multiplier(0), PT.MULT_MIN)
        self.assertAlmostEqual(PT.target_multiplier(75), 2.0)
        m, path = 1.0, []
        for _ in range(30):                                                   # sustained prestige 100
            new = PT.next_multiplier(m, 100.0)
            self.assertLessEqual(new / m, PT.MULT_STEP + 1e-12)
            m = new
            path.append(m)
        self.assertEqual(path[-1], PT.MULT_MAX)
        years = next(i for i, v in enumerate(path, 1) if v >= PT.MULT_MAX)
        self.assertEqual(years, math.ceil(math.log(PT.MULT_MAX) / math.log(PT.MULT_STEP)))   # 15 years
        for _ in range(40):                                                   # then sustained prestige 0
            new = PT.next_multiplier(m, 0.0)
            self.assertGreaterEqual(new / m, 1 / PT.MULT_STEP - 1e-12)
            m = new
        self.assertEqual(m, PT.MULT_MIN)

    def test_long_term_share_can_move_substantially(self):
        """Sustained success for decades moves a small nation's share by a large factor (D7 clarification)."""
        pt = PT.Participation(PROFILES, 2027)
        c = 'Fiji'
        start = pt.shares('juniors')[c]
        for y in range(2027, 2027 + 25):
            for k in pt.baseline:                                             # it beats expectation, the rest as expected
                pt.note_site(y, [(k, 60.0, 1.0)])
            pt.success[y][c] = [3000.0, 300.0]
            pt.close_season(y)
            hist = pt.history[y + 1]
            self.assertAlmostEqual(sum(hist['shares']['juniors'].values()), 1.0, places=4)   # (recorded rounded)
            self.assertAlmostEqual(sum(pt.shares('juniors').values()), 1.0, places=12)
        self.assertEqual(pt.multiplier[c], PT.MULT_MAX)
        self.assertGreater(pt.shares('juniors')[c] / start, 3.5)

    def test_close_season_once_and_window_is_five_seasons(self):
        pt = PT.Participation(PROFILES, 2027)
        pt.success[2027] = {'Fiji': [500.0, 50.0]}
        pt.close_season(2027)
        m = pt.multiplier['Fiji']
        pt.close_season(2027)                                                 # (again: no second step)
        self.assertEqual(pt.multiplier['Fiji'], m)
        self.assertAlmostEqual(m, PT.MULT_STEP)
        for y in range(2028, 2033):
            pt.close_season(y)                                                # nothing more: 2027 leaves the window
        self.assertNotIn(2027, pt.success)
        self.assertAlmostEqual(pt.prestige['Fiji'], 50.0)


class TalentUnchanged(unittest.TestCase):
    def test_the_draw_code_never_reads_prestige_or_shares(self):
        for fn in (P._junior_draw, P._new_pro_draw, P._mu, P._Stream):
            src = inspect.getsource(fn)
            for word in ('share', 'prestige', 'multiplier', 'alloc'):
                self.assertNotIn(word, src, (fn.__name__, word))
        src = inspect.getsource(PT)
        for word in ('.development =', '.pool =', 'potential', '.pathway ='):
            self.assertNotIn(word, src)

    def test_a_nations_entrants_are_the_same_draws_whatever_its_share(self):
        """More places: the same golfers first, then the next draws of the same stream (never different ones)."""
        for kind in P.PATHWAYS:
            lo = [r for r in P.entrant_rows(kind, 2035, SEED, PROFILES, shares=skewed(kind, 'Sweden', 0.3)) if r[0] == 'Sweden']
            hi = [r for r in P.entrant_rows(kind, 2035, SEED, PROFILES, shares=skewed(kind, 'Sweden', 3.0)) if r[0] == 'Sweden']
            self.assertGreater(len(hi), len(lo))
            self.assertEqual(lo, hi[:len(lo)])                                # (entrant_rows keeps draw order)

    def test_ability_distribution_does_not_depend_on_share(self):
        small, large = [], []
        for year in range(2030, 2036):
            small += [r[4] for r in P.entrant_rows('juniors', year, SEED, PROFILES, shares=skewed('juniors', 'Japan', 0.5))
                      if r[0] == 'Japan']
            large += [r[4] for r in P.entrant_rows('juniors', year, SEED, PROFILES, shares=skewed('juniors', 'Japan', 2.0))
                      if r[0] == 'Japan']
        self.assertGreater(len(large), 1.6 * len(small))
        se = math.hypot(S.stdev(small) / math.sqrt(len(small)), S.stdev(large) / math.sqrt(len(large)))
        self.assertLess(abs(S.mean(small) - S.mean(large)), 4 * se + 0.5)


class Baseline(unittest.TestCase):
    def test_expected_shares_match_the_existing_rule(self):
        """Multipliers all 1: the expected shares are what the existing rule produces on average."""
        for kind, years in (('juniors', range(2030, 2045)), ('new_pros', range(2030, 2034))):
            tot = Counter()
            n = 0
            for y in years:
                rows = OLD[kind](y, SEED, PROFILES)
                tot.update(r[0] for r in rows)
                n += len(rows)
            exp = P.expected_counts(kind, PROFILES)
            self.assertLess(abs(sum(exp.values()) * len(years) - n) / n, 0.04, kind)   # totals: within 4 %
            share = P.expected_shares(kind, PROFILES)
            for c in ('USA', 'Japan', 'England', 'South Korea', 'Australia'):
                obs = tot[c] / n
                se = math.sqrt(share[c] * (1 - share[c]) / n)
                self.assertLess(abs(obs - share[c]), 4 * se + 0.003, (kind, c, obs, share[c]))

    def test_multipliers_of_one_change_nothing_but_the_rounding(self):
        pt = PT.Participation(PROFILES, 2027)
        for kind in P.PATHWAYS:
            self.assertEqual(pt.shares(kind), pt.base_share[kind])
            rep = {}
            P.entrant_rows(kind, 2030, SEED, PROFILES, baseline=pt.baseline, shares=pt.shares(kind), report=rep)
            self.assertEqual(rep['total'], len(OLD[kind](2030, SEED, PROFILES)))
            self.assertEqual(rep['allocated'], P.allocate(rep['total'], pt.base_share[kind]))


def pre_fix_entrant_rows(kind, year, seed, profiles, shares):
    """entrant_rows as it stood at d187a56 (draws capped at 400 per golfer owed + 1000, then RuntimeError): the
    outcomes the fix must keep wherever that cap was never reached."""
    base = P.existing_rule(kind, year, seed, profiles)
    alloc = P.allocate(sum(len(r) for r, _ in base.values()), shares)
    rows = []
    for country, prof in profiles.items():
        k = alloc.get(country, 0)
        got, st = base[country]
        got = list(got)
        if len(got) < k:
            limit = st.draws + 400 * (k - len(got)) + 1000
            while len(got) < k:
                if st.draws >= limit:
                    raise RuntimeError(f'{country}: {k} {kind} not reached in {st.draws} draws')
                r = st.draw()
                if r is not None:
                    got.append(r)
        rows.extend(got[:k])
    return rows


# nations whose new professionals pass the filter rarely (about 1 in 300 to 1 in 650: low development)
RARE = [c for c in PROFILES if P.pass_chance('new_pros', PROFILES[c].development) < 1 / 300]


def extreme(kind, favoured, up=4.0, down=0.25):
    """Expected shares with `favoured` nations at the top multiplier and the rest at the bottom (normalised):
    the largest share a small nation can reach (16 x its start)."""
    base = P.expected_shares(kind, PROFILES)
    return P.normalised({c: s * (up if c in favoured else down) for c, s in base.items()})


class DrawCap(unittest.TestCase):
    """A nation owing golfers keeps drawing from its own stream until its quota has passed: no cap, no shortfall, no
    reassigned places (population.py, block comment step 5). Before the fix the draws stopped at 400 per golfer
    owed + 1000 and raised RuntimeError."""

    @staticmethod
    def own_passers(kind, year, seed, country, n):
        """The first n golfers who pass in the nation's own stream: its talent distribution conditional on the
        nation, exactly as the existing rule draws it (no other nation's draws, no re-weighting)."""
        st = P._Stream(kind, year, seed, country, PROFILES[country])
        out = []
        while len(out) < n:
            r = st.draw()
            if r is not None:
                out.append(r)
        return out

    def check(self, kind, year, seed, shares, fixed_total=None):
        rep = {}
        rows = P.entrant_rows(kind, year, seed, PROFILES, shares=shares, report=rep)
        self.assertEqual(len(rows), rep['total'], (kind, year, seed))               # ACTUAL total = the fixed cohort
        if fixed_total is not None:
            self.assertEqual(len(rows), fixed_total)
        self.assertEqual(sum(rep['allocated'].values()), rep['total'])
        self.assertEqual(Counter(r[0] for r in rows), {c: n for c, n in rep['allocated'].items() if n})
        for c in RARE:                       # the nations the old cap failed: their own stream's passers, in order
            mine = [r for r in rows if r[0] == c]
            self.assertEqual(mine, self.own_passers(kind, year, seed, c, len(mine)), (kind, year, seed, c))
        return rows, rep

    def test_czechia_2029_seed_99_is_filled_from_its_own_stream(self):
        """The serialized queue's crash (tests.test_living_views, seed 99, end of 2028): Czechia's one new professional
        of 2029 was not reached in 1590 draws (its first passer is draw 2161) and the season stopped."""
        rows, rep = self.check('new_pros', 2029, 99, None)
        self.assertEqual(rep['existing']['Czechia'], 0)
        self.assertEqual(rep['allocated']['Czechia'], 1)
        self.assertGreater(rep['draws']['Czechia'], 1590)
        st = P._Stream('new_pros', 2029, 99, 'Czechia', PROFILES['Czechia'])
        first = next(r for r in iter(st.draw, 'never') if r is not None)          # the stream's own next passer
        self.assertEqual([r for r in rows if r[0] == 'Czechia'], [first])
        self.assertEqual(rep['draws']['Czechia'], st.draws)

    def test_no_crash_and_quotas_hold_over_many_years_seeds_and_small_nations(self):
        """No RuntimeError; the actual number created is the fixed cohort (the pre-2026-11-05 rule's own count, computed
        independently by old_new_pros / old_juniors); every nation gets exactly its quota; and the rare nations'
        golfers are their own stream's passers (the conditional talent distribution, by construction)."""
        self.assertGreaterEqual(len(RARE), 15)
        for seed in (99, 7, 2027):
            for year in (2029, 2034, 2041, 2050):
                fixed = len(old_new_pros(year, seed, PROFILES))
                self.check('new_pros', year, seed, None, fixed)
                self.check('new_pros', year, seed, extreme('new_pros', RARE), fixed)   # rare nations at 16 x their start
            year = 2029 + seed % 5
            self.check('juniors', year, seed, extreme('juniors', RARE), len(old_juniors(year, seed, PROFILES)))

    def test_conditional_talent_is_unchanged_past_the_old_cap(self):
        """Statistical companion to the by-construction check: golfers reached only past the old cap (the fix's
        path) have the same Overall distribution as the same nations' golfers within it."""
        early, late = [], []
        for seed in range(1, 41):
            for c in ('Turkey', 'Vietnam', 'Poland'):
                st = P._Stream('new_pros', 2031, seed, c, PROFILES[c])
                cap = P._cand_n('new_pros', PROFILES[c]) + 400 + 1000
                for _ in range(6000):
                    r = st.draw()
                    if r is not None:
                        (early if st.draws <= cap else late).append(r[4])
        self.assertGreater(min(len(early), len(late)), 60)
        se = math.hypot(S.stdev(early) / math.sqrt(len(early)), S.stdev(late) / math.sqrt(len(late)))
        self.assertLess(abs(S.mean(early) - S.mean(late)), 4 * se)

    def test_outcomes_are_unchanged_wherever_the_old_cap_was_enough(self):
        compared = 0
        for seed, year in ((2027, 2030), (99, 2028), (7, 2033)):
            for kind in P.PATHWAYS:
                for shares in (P.expected_shares(kind, PROFILES), extreme(kind, RARE, 2.0, 0.8)):
                    try:
                        old = pre_fix_entrant_rows(kind, year, seed, PROFILES, shares)
                    except RuntimeError:
                        continue
                    self.assertEqual(P.entrant_rows(kind, year, seed, PROFILES, shares=shares), old, (kind, year, seed))
                    compared += 1
        self.assertGreaterEqual(compared, 8)

    def test_the_extreme_tail_terminates_with_the_exact_quota(self):
        """Development 0 (the bottom of the scale: a new professional passes about 1 in 100,000, a junior 1 in 9,300):
        the stream still reaches the exact quota, each golfer from that nation's own stream, and the total holds."""
        from dataclasses import replace
        self.assertGreater(P.pass_chance('new_pros', 0), 1 / 120000)
        self.assertGreater(P.pass_chance('juniors', 0), 1 / 12000)
        now = dict(PROFILES)
        now['Turkey'] = replace(PROFILES['Turkey'], development=0)
        for kind, want in (('juniors', 4), ('new_pros', 2)):
            base = P.expected_shares(kind, PROFILES)
            rep = {}
            total = len(OLD[kind](2031, 5, PROFILES))
            shares = P.normalised({c: (want / total if c == 'Turkey' else s) for c, s in base.items()})
            rows = P.entrant_rows(kind, 2031, 5, now, baseline=PROFILES, shares=shares, report=rep)
            self.assertEqual(len(rows), total)
            k = rep['allocated']['Turkey']
            self.assertGreaterEqual(k, 1)
            mine = [r for r in rows if r[0] == 'Turkey']
            self.assertEqual(len(mine), k)
            st = P._Stream(kind, 2031, 5, 'Turkey', now['Turkey'])               # its own (development 0) stream
            own = []
            while len(own) < k:
                r = st.draw()
                if r is not None:
                    own.append(r)
            self.assertEqual(mine, own)
            self.assertEqual(rep['draws']['Turkey'], st.draws)


class InTheWorld(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from golfsim.season import Season
        cls.s = Season(P.generate_world(seed=31, scale=0.05), seed=31, development=True, workers=1)

    def test_entrants_resume_identically_and_nobody_changes_nationality(self):
        from golfsim import careers
        s = self.s
        s.participation.multiplier['Thailand'] = 2.5                       # some prestige history
        s.participation.multiplier['USA'] = 0.6
        before = {g.id: g.country for g in s.world.golfers}
        copy = pickle.loads(pickle.dumps(s))
        for season in (s, copy):
            careers.add_juniors(season, 2028)
            careers.add_new_professionals(season, 2028)
        rows = lambda season: [(g.id, g.name, g.country, round(g.overall, 6)) for g in season.world.golfers]
        self.assertEqual(rows(s), rows(copy))
        self.assertEqual(s.participation.history[2028], copy.participation.history[2028])
        self.assertTrue(all(g.country == before[g.id] for g in s.world.golfers if g.id in before))
        h = s.participation.history[2028]
        for kind in P.PATHWAYS:
            self.assertEqual(sum(h['allocated'][kind].values()), h['totals'][kind])
            self.assertEqual(h['totals'][kind], len(OLD[kind](2028, s.seed, s.participation.baseline)))
        new = Counter(g.country for g in s.world.golfers if g.id not in before)
        self.assertEqual(sum(new.values()), sum(h['totals'].values()))


if __name__ == '__main__':
    unittest.main()
