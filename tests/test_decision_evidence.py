"""Decision evidence (recording only, golfsim.decision_evidence): the monthly planner's target and its components with
the fatigue and injury context of each plan, and each winter career evaluation's terms. Quick checks, no season is
played: the target's parts add up to Season.target_events for every role; every career model gives exactly the
same probability with the evidence kept as without, and its recorded terms sum to its logit; the winter's decisions
(every draw) are identical with recording on and off; the record's shape and bounds; the archive block's round trip
and a season file without it reading as not recorded.

Whole-season outcome equivalence (results, finances, ratings, the published season) is in
tests/test_decision_evidence_world.py (plays seasons: run separately).

Run from the project folder:  python -m unittest tests.test_decision_evidence -v
"""
from __future__ import annotations

import json
import math
import random
import sys
import unittest
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from golfsim import careers as C                                        # noqa: E402
from golfsim import decision_evidence as DE                             # noqa: E402
from golfsim.population import generate_world                           # noqa: E402
from golfsim.season import PREMIER_TOURS, Season                        # noqa: E402

YEAR = 2027


def season(seed=97):
    return Season(generate_world(seed=seed, scale=0.03), seed=seed, development=True, workers=1)


def logit(p):
    return math.log(p / (1 - p))


def rows_for(g):
    """A few completed-season rows of different shapes (results, ranking, money, injury)."""
    base = {'status': g.status, 'tier': 4, 'events': 12, 'top10': 1, 'top3': 0, 'wins': 0, 'injury_weeks': 0,
            'money_rank_pct': 0.6, 'wr_start': 900, 'wr_end': 700, 'am_end': 150, 'secured': []}
    return [base, dict(base, events=0, wins=2, top3=3, injury_weeks=9, wr_end=1500, am_end=None,
                       money_rank_pct=0.1, secured=['a place'], promoted=True),
            dict(base, events=30, demoted=True, wr_start=None, wr_end=None, am_end=4)]


class TargetParts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = season()

    def test_parts_add_up_to_the_target_for_every_role(self):
        s = self.s
        roles = set()
        import copy
        pro = next(g for g in s.world.golfers if g.status == 'pro')
        made = []                                                         # every role, whatever this world holds
        for status, lifestyle, tour in (('pro', 'full_time', 'MINI_USA'), ('pro', 'part_time', 'MINI_USA'),
                                        ('pro', 'retired', ''), ('club_pro', 'part_time', '')):
            h = copy.deepcopy(pro)
            h.status, h.lifestyle, h.tour = status, lifestyle, tour
            made.append(h)
        for g in list(s.world.golfers) + made:
            legacy = len(s.legacy)
            role, base, stam, pres = DE.target_parts(s, g)
            self.assertEqual(len(s.legacy), legacy)                       # reads without adding keys
            self.assertAlmostEqual(base + stam + pres, s.target_events(g), places=9, msg=(g.id, role))
            roles.add(role)
        self.assertEqual(roles, set(DE.TARGET_ROLES))

    def test_the_premier_prestige_part(self):
        s = self.s
        g = next(g for g in s.world.golfers if g.tour in PREMIER_TOURS and g.lifestyle == 'full_time')
        before = s.fame.get(g.id)
        try:
            s.fame[g.id] = 10 ** 6                                      # a star: plays four fewer
            self.assertEqual(DE.target_parts(s, g)[3], -4)
            self.assertAlmostEqual(sum(DE.target_parts(s, g)[1:]), s.target_events(g), places=9)
        finally:
            if before is None:
                del s.fame[g.id]
            else:
                s.fame[g.id] = before


class CareerTerms(unittest.TestCase):
    """Each model's probability is the same with the evidence kept, and its terms sum to logit(p)."""

    @classmethod
    def setUpClass(cls):
        cls.s = season()

    def check(self, p_plain, p_ev, ev, terms):
        self.assertEqual(p_plain, p_ev)                                   # bit for bit
        if 1e-12 < p_ev < 1 - 1e-12:
            self.assertAlmostEqual(sum(ev[k] for k in terms if ev.get(k) is not None), logit(p_ev), places=7)

    def golfers(self, pred, n=25):
        return [g for g in self.s.world.golfers if pred(g)][:n]

    def test_retire(self):
        s = self.s
        models = set()
        for g in self.golfers(lambda g: True, 80):
            for row in rows_for(g):
                ev = {}
                p = C.p_retire(s, g, row, YEAR, ev=ev)
                models.add(ev['model'])
                self.check(C.p_retire(s, g, row, YEAR), p, ev, DE.CAREER_MODELS[ev['model']]['terms'])
        self.assertEqual(models, {'retire_job', 'retire_tour'})

    def test_stop_chasing(self):
        s = self.s
        for g in self.golfers(lambda g: g.status == 'pro' and g.lifestyle == 'full_time'):
            for row in rows_for(g):
                ev = {}
                p, why = C.p_stop_chasing(s, g, row, YEAR, ev=ev)
                p0, why0 = C.p_stop_chasing(s, g, row, YEAR)
                self.assertEqual(why, why0)
                self.check(p0, p, ev, DE.CAREER_MODELS['stop_chasing']['terms'])
                self.assertEqual(ev['in_runway'], why['runway'])
                self.assertIsNotNone(ev['in_shortfall'])

    def test_turn_pro_amateur_job_comeback(self):
        s = self.s
        for g in self.golfers(lambda g: g.status == 'amateur'):
            for row in rows_for(g):
                for grad in (False, True):
                    ev = {}
                    p = C.p_turn_pro(s, g, row, YEAR, grad, ev=ev)
                    self.check(C.p_turn_pro(s, g, row, YEAR, grad), p, ev, DE.CAREER_MODELS['turn_pro']['terms'])
                    self.assertEqual(ev['age'] is None, grad)             # graduating: age is no term
                ev = {}
                p = C.p_amateur_job(s, g, row, YEAR, ev=ev)
                self.check(C.p_amateur_job(s, g, row, YEAR), p, ev, DE.CAREER_MODELS['amateur_job']['terms'])
        for g in self.golfers(lambda g: g.status == 'pro'):
            for row in rows_for(g):
                ev = {}
                p = C.p_comeback(s, g, row, YEAR, ev=ev)
                self.check(C.p_comeback(s, g, row, YEAR), p, ev, DE.CAREER_MODELS['comeback']['terms'])


class WinterDecisions(unittest.TestCase):
    """careers.decide on two identical worlds, recording on and off: every decision, draw and change is the same
    (the evidence takes each draw where the rules always took it)."""

    def test_same_decisions_with_and_without_recording(self):
        out = []
        for on in (True, False):
            s = season(seed=41)
            s.record_decisions = on
            snap = {g.id: r for g, r in zip(s.world.golfers, (rows_for(g)[g.id % 3] for g in s.world.golfers))}
            counts = C.decide(s, YEAR, snap)
            state = [(g.id, g.status, g.lifestyle, g.tour, g.backer, g.backer_funds, g.backer_stale, g.cash)
                     for g in s.world.golfers]
            out.append((counts, json.dumps(s.transitions[YEAR], sort_keys=True, default=str), state,
                        sorted(s.history.items()), s.career_ev.get(YEAR, {})))
        (c1, t1, st1, h1, ev1), (c0, t0, st0, h0, ev0) = out
        self.assertEqual(c1, c0)
        self.assertEqual(t1, t0)
        self.assertEqual(st1, st0)
        self.assertEqual(h1, h0)
        self.assertEqual(ev0, {})                                         # off: nothing kept
        self.assertTrue(ev1)
        evaluated = {g.id for g in season(seed=41).world.golfers if g.lifestyle != 'retired'}
        self.assertTrue(set(ev1) <= evaluated)
        for gid, rows in ev1.items():
            self.assertLessEqual(len(rows), DE.CAREER_ROWS)
            for r in rows:
                spec = DE.CAREER_MODELS[r[0]]
                self.assertEqual(len(r), 4 + len(spec['terms']) + len(spec['inputs']))
                self.assertEqual(r[3], int(r[2] is not None and r[2] < r[1]))   # the draw against p (None: none)
        kinds = {r[0] for rows in ev1.values() for r in rows}
        self.assertTrue({'retire_tour', 'stop_chasing', 'turn_pro'} <= kinds, kinds)
        # every recorded decision that happened is in the transitions with the same probability
        happened = {(t['gid'], t.get('p')) for t in json.loads(t1) if 'p' in t}
        for gid, rows in ev1.items():
            for r in rows:
                if r[3]:                                                  # (every model notes its p)
                    self.assertIn((gid, r[1]), happened, (gid, r))


    def test_models_stood_in_for_record_nothing_and_change_nothing(self):
        """A test standing in for a model (returning p without filling the evidence) must not break the winter:
        such an evaluation keeps no row; the decisions are those of the run with recording off."""
        from unittest import mock
        out = []
        for on in (True, False):
            s = season(seed=43)
            s.record_decisions = on
            snap = {g.id: r for g, r in zip(s.world.golfers, (rows_for(g)[g.id % 3] for g in s.world.golfers))}
            with mock.patch.object(C, 'p_retire', return_value=0.0), mock.patch.object(C, 'p_turn_pro', return_value=0.0):
                counts = C.decide(s, YEAR, snap)
            out.append((counts, json.dumps(s.transitions[YEAR], sort_keys=True, default=str), s.career_ev.get(YEAR, {})))
        (c1, t1, ev1), (c0, t0, _) = out
        self.assertEqual((c1, t1), (c0, t0))
        kinds = {r[0] for rows in ev1.values() for r in rows}
        self.assertNotIn(None, kinds)
        self.assertFalse(kinds & {'retire_tour', 'retire_job'})        # the stood-in model: nothing kept
        self.assertIn('turn_pro', kinds)                                # (named by decide; its terms are empty)


def stub():
    return SimpleNamespace(plan_ev=defaultdict(dict), career_ev=defaultdict(dict), played={YEAR: {}}, fame={},
                           legacy={})


def plan(s, g, week0, **kw):
    weeks = list(range(week0, week0 + 4))
    args = dict(target=19 + 8 * g.attrs['stamina'] / 100, weeks=weeks, avail={w: 'ok' for w in weeks},
                acts=['play', 'train', 'rest', 'work'], inj_until=0, now=0, f0=0.237, played0=week0 // 4, money0=-2600.0,
                bar=31.27,
                dp=0.43, dt=0.12, work_v=-1.0, load4=0.0981, rest_rec=0.4751, risk=0.00322, can_work=False,
                stuck=False, major=False, fallback=False)
    args.update(kw)
    DE.record_plan(s, g, YEAR, week0, **args)


class RecordShape(unittest.TestCase):
    def setUp(self):
        self.g = SimpleNamespace(id=7, lifestyle='full_time', status='pro', tour='MINI_X', attrs={'stamina': 50.0})

    def test_a_season_of_plans_is_bounded(self):
        s = stub()
        for w in range(1, 53, 4):
            plan(s, self.g, w)
        plan(s, self.g, 49)                                               # made twice: not kept
        plan(s, self.g, 53)                                               # beyond the bound: not kept
        rec = s.plan_ev[YEAR][7]
        self.assertEqual(len(rec['n']), DE.PLAN_BLOCKS)
        self.assertEqual(len(rec['c']), DE.PLAN_BLOCKS * DE.CODE_LEN)
        self.assertEqual(rec['over'], 2)
        self.assertEqual(len(rec['t']), 1)                                # unchanged: kept once
        self.assertEqual(len(rec['s']), 1)
        self.assertNotIn('i', rec)                                        # never injured, no flags: no column
        self.assertNotIn('f', rec)
        self.assertEqual(rec['c'][:8], 'ooooPTRW')
        self.assertEqual(rec['x'][0], 24)
        self.assertTrue(all(isinstance(v, int) for k in 'nxmd' for v in rec[k]))

    def test_changes_gaps_injury_and_flags(self):
        s = stub()
        plan(s, self.g, 1)
        plan(s, self.g, 9, bar=40.0, inj_until=12, now=0, can_work=True, stuck=True,
             avail={9: 'unaff', 10: 'inelig', 11: 'none', 12: 'ok'})   # week 5 not recorded
        rec = s.plan_ev[YEAR][7]
        self.assertEqual(rec['n'][1], None)
        self.assertEqual(rec['c'][8:16], '-' * 8)
        self.assertEqual(rec['c'][16:20], 'uen' + 'o')
        self.assertEqual(rec['i'], [0, 0, 3])
        self.assertEqual(rec['f'], [0, 0, 3])
        self.assertEqual([x[0] for x in rec['s']], [1, 9])                # the bar changed

    def test_career_rows_are_bounded(self):
        s = stub()
        for _ in range(DE.CAREER_ROWS + 2):
            DE.record_career(s, YEAR, self.g, 'amateur_job', 0.25, 0.1, {'base': -1.2, 'age': 0.1, 'runway': -0.4,
                                                                        'debt': 0.0, 'in_age': 23, 'in_runway': 1.0,
                                                                        'in_cash': -1234.0})
        rows = s.career_ev[YEAR][7]
        self.assertEqual(len(rows), DE.CAREER_ROWS)
        self.assertEqual(rows[0], ['amateur_job', 0.25, 0.1, 1, -1.2, 0.1, -0.4, 0, 23, 1, -1])


class AmateurReturn(unittest.TestCase):
    """The return to full-time amateur golf (format /2): the same chance and facts with the evidence kept, and the
    terms give it back (p = min(cap, sig(sum of terms) x keep_up)); a blocked case keeps why."""

    def setUp(self):
        from unittest import mock
        p = mock.patch.object(C, 'runway_years', return_value=2.0)       # (as tests.test_amateur_return does)
        p.start()
        self.addCleanup(p.stop)
        sys.path.insert(0, str(ROOT / 'tests'))
        import test_amateur_return as TAR
        self.world, self.standing = TAR.world, TAR.standing

    def test_terms_and_inputs(self):
        from golfsim import amateur_return as AR
        for kw in ({}, {'cash': 90000.0}, {'born': 1990}, {'work_from': None}):
            s, g, row = self.world(**kw)
            ev = {}
            p, facts = AR.chance(s, g, row, YEAR, self.standing(row['am_end']), ev=ev)
            self.assertEqual((p, facts), AR.chance(s, g, row, YEAR, self.standing(row['am_end'])))
            self.assertGreater(p, 0)
            x = sum(ev[k] for k in DE.CAREER_MODELS['amateur_return']['terms'])
            self.assertAlmostEqual(min(AR.CAP, 1 / (1 + math.exp(-x)) * ev['in_keep_up']), p, places=12)
            self.assertEqual(ev['in_capped'], 1 / (1 + math.exp(-x)) * ev['in_keep_up'] > AR.CAP)
            self.assertEqual(ev['in_season_cost'], AR.season_cost(s, g, YEAR, row))
            st = stub()
            DE.record_career(st, YEAR, g, 'amateur_return', p, 0.99, ev)
            r = st.career_ev[YEAR][g.id][0]
            spec = DE.CAREER_MODELS['amateur_return']
            self.assertEqual(len(r), 4 + len(spec['terms']) + len(spec['inputs']))
            self.assertEqual(r[3], 0)

    def test_a_blocked_return_keeps_why_and_draws_nothing(self):
        from golfsim import amateur_return as AR
        for kw, code in (({'work_from': (YEAR, 13)}, 'work'), ({'cash': 100.0}, 'funds')):
            s, g, row = self.world(**kw)
            ev = {}
            p, _ = AR.chance(s, g, row, YEAR, self.standing(row['am_end']), ev=ev)
            self.assertEqual(p, 0.0)
            self.assertEqual(ev['in_blocked'], code)
            st = stub()
            DE.record_career(st, YEAR, g, 'amateur_return', p, None, ev)
            r = st.career_ev[YEAR][g.id][0]
            self.assertEqual(r[:4], ['amateur_return', 0, None, 0])
            self.assertEqual(r[4:4 + 5], [None] * 5)                      # no terms: the chance was never formed
            self.assertEqual(r[-1], code)


class Mortality(unittest.TestCase):
    """The winter's mortality draws (format /2): the same deaths with the evidence kept; every evaluation counted
    in its age band, each death in full, and a survivor's draw reproducible from the rule."""

    def test_same_deaths_bands_and_draws(self):
        sys.path.insert(0, str(ROOT / 'tests'))
        import test_mortality as TM
        from golfsim import mortality as M
        runs = []
        for on in (True, False):
            s = TM.population()
            if on:
                s.record_decisions, s.mortality_ev = True, defaultdict(dict)
            out = M.winter(s, YEAR)
            runs.append((s, out))
        (s1, out1), (s0, out0) = runs
        self.assertEqual(out1, out0)
        self.assertEqual(s1.deaths, s0.deaths)
        self.assertEqual(dict(s1.history), dict(s0.history))
        self.assertTrue(out1)
        book = s1.mortality_ev[YEAR]
        evaluated = sum(1 for pid, rec in M.people(s0).items() if M.eligible(rec))
        self.assertEqual(sum(b[0] for b in book['bands'].values()), evaluated)
        self.assertEqual(sum(b[2] for b in book['bands'].values()), len(out1))
        self.assertEqual(set(book['died']), {pid for pid, _ in out1})
        for pid, (age, q, u) in book['died'].items():
            self.assertEqual(age, s1.deaths[pid]['age'])
            self.assertAlmostEqual(q, M.annual_risk(age), places=5)
            self.assertAlmostEqual(u, M.draw(s1.seed, YEAR, pid), places=5)
            self.assertLess(u, q + 1e-5)
        expected = sum(M.annual_risk(YEAR - rec['born']) for rec in M.people(s0).values() if M.eligible(rec))
        self.assertAlmostEqual(sum(b[1] for b in book['bands'].values()), expected, places=6)
        s1.plan_ev, s1.career_ev = {}, {}
        blk = json.loads(json.dumps(DE.season_block(s1, YEAR)))
        pid = next(iter(book['died']))
        got = DE.read({'decision_evidence': blk}, pid)
        self.assertEqual(got['mortality'], dict(zip(('age', 'p', 'u'), book['died'][pid])))
        self.assertEqual(blk['mortality']['bands']['90'][0], book['bands'][90][0])


class ArchiveRoundTrip(unittest.TestCase):
    def test_round_trip_and_not_recorded(self):
        s = stub()
        g = SimpleNamespace(id=7, lifestyle='full_time', status='pro', tour='MINI_X', attrs={'stamina': 50.0})
        for w in (1, 5, 9):
            plan(s, g, w, played0=w // 2)
        plan(s, g, 13, played0=6, inj_until=15, can_work=True, bar=40.0)
        DE.record_career(s, YEAR, g, 'retire_tour', 0.0123, 0.5, {'base': -6.5, 'age': 0.1, 'standing': 0.2,
                                                                  'opportunity': -0.15, 'injury': 0.0, 'in_age': 30,
                                                                  'in_tier': 4, 'in_money_rank_pct': 0.4})
        blk = DE.season_block(s, YEAR)
        chunk = json.loads(json.dumps({'year': YEAR, 'decision_evidence': blk}))   # as written and read back
        got = DE.read(chunk, 7)
        self.assertTrue(got['recorded'])
        sch = got['schedule']
        self.assertEqual([r['week'] for r in sch], [1, 5, 9, 13])
        self.assertEqual([r['started'] for r in sch], [0, 2, 4, 6])
        self.assertEqual([r['last4'] for r in sch], [None, 2, 2, 2])
        self.assertEqual(sch[0]['fatigue'], 0.24)
        self.assertEqual(sch[0]['funds_k'], -3)
        self.assertEqual(sch[0]['plan'], ['play', 'train', 'rest', 'work'])
        self.assertEqual(sch[0]['availability'], ['ok'] * 4)
        self.assertEqual(sch[0]['target']['role'], 'pro')
        self.assertEqual(sch[0]['target']['target'], 23)
        self.assertEqual(sch[0]['terms']['bar'], 31)
        self.assertAlmostEqual(sch[0]['terms']['load4'], 0.098)
        self.assertAlmostEqual(sch[0]['terms']['injury_risk'], 0.0032)
        self.assertEqual(sch[3]['terms']['bar'], 40)
        self.assertEqual(sch[3]['injured_weeks'], 2)
        self.assertEqual(sch[3]['flags'], ['can_work'])
        self.assertEqual(sch[2]['flags'], [])
        self.assertAlmostEqual(sch[1]['pace'], 23 * 5 / 52 - 2, places=2)
        car = got['careers'][0]
        self.assertEqual((car['model'], car['p'], car['u'], car['outcome']), ('retire_tour', 0.0123, 0.5, 0))
        self.assertEqual(car['terms']['base'], -6.5)
        self.assertEqual(car['inputs'], {'age': 30, 'tier': 4, 'money_rank_pct': 0.4, 'lasting_damage': None})
        self.assertEqual(DE.read(chunk, 8), {'recorded': True, 'schedule': [], 'careers': [],
                                             'mortality': None})                     # not evaluated
        self.assertEqual(DE.read({'year': YEAR}, 7), {'recorded': False})                     # older season file
        self.assertEqual(DE.read({'decision_evidence': dict(blk, format='other/9')}, 7), {'recorded': False})
        v1 = {k: v for k, v in chunk['decision_evidence'].items() if k != 'mortality'}       # a /1 season file
        v1['format'] = 'golf-legacy-decision-evidence/1'
        old = DE.read({'decision_evidence': v1}, 7)
        self.assertEqual(old['schedule'], got['schedule'])
        self.assertEqual(old['careers'], got['careers'])
        self.assertIsNone(old['mortality'])
        self.assertIsNone(DE.season_block(stub(), YEAR))                  # nothing kept: no key written

    def test_the_season_file_carries_the_block(self):
        import tempfile
        from golfsim.archive import ArchiveWriter
        s = season()
        g = s.world.golfers[0]
        plan(s, g, 1)
        with tempfile.TemporaryDirectory() as d:
            chunk = ArchiveWriter(d, s, touch=False).year_chunk(s, YEAR)
        self.assertEqual(chunk['decision_evidence'], DE.season_block(s, YEAR))
        self.assertEqual(chunk['decision_evidence']['format'], DE.FORMAT)
        s.plan_ev.clear()
        with tempfile.TemporaryDirectory() as d:
            self.assertNotIn('decision_evidence', ArchiveWriter(d, s, touch=False).year_chunk(s, YEAR))

    def test_rules_and_observer_untouched(self):
        self.assertNotIn('decision_evidence', (ROOT / 'golfsim' / 'rules.py').read_text())
        for p in (ROOT / 'tools').glob('observer*.py'):                  # (recording only: nothing shows it yet)
            self.assertNotIn('decision_evidence', p.read_text(), p.name)


if __name__ == '__main__':
    unittest.main()
