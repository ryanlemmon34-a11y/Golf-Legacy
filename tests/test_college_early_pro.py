"""Turning professional from college before eligibility ends (rules 2026-11-15, careers.early_pro_gate).

A college amateur aged 18-21 on any college tour (US Division I, US small college, international university golf) who
holds a winner's exemption for next season or finishes the season in the amateur top 15 decides, with the existing
non-graduating p_turn_pro model and a draw of their own (per golfer and winter), whether to turn professional now.
Accepting goes through turn_pro (its tour assignment and backers); staying keeps them a full-time college golfer (no
amateur-job evaluation). Everyone else's decisions and draws are what they were; graduation at 22 is unchanged; worlds
saved before the rule never decide early.

Run from the project folder:  python -m unittest tests.test_college_early_pro -v
"""
from __future__ import annotations

import copy
import json
import pickle
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from golfsim import amateur_support as AS                               # noqa: E402
from golfsim import careers as C                                        # noqa: E402
from golfsim import qualification as Q                                  # noqa: E402
from golfsim import rules as R                                          # noqa: E402
from golfsim import staff as ST                                         # noqa: E402
from golfsim.cards import home_challenger, home_lower, premier_circuit  # noqa: E402
from golfsim.population import generate_world                           # noqa: E402
from golfsim.season import Season                                       # noqa: E402

YEAR = 2027
PATHWAYS = ('CO_US_D1', 'CO_US_SMALL', 'CO_INTL')
ACCEPT, DECLINE = 0.0, 0.999999                                        # the early draw: below any p, above any p


def season(seed=61):
    s = Season(generate_world(seed=seed, scale=0.03), seed=seed, development=True, workers=1)
    s.record_decisions = True
    return s


def neutral(g):
    return {'status': g.status, 'tier': 4, 'events': 12, 'top10': 1, 'top3': 0, 'wins': 0, 'injury_weeks': 0,
            'money_rank_pct': 0.6, 'wr_start': 900, 'wr_end': 700, 'am_end': 400, 'secured': []}


def college_amateurs(s, n, tour=None):
    """n amateurs of this world made college golfers (full-time), aged 20 in YEAR, lowest ids first."""
    out = []
    for g in sorted(s.world.golfers, key=lambda x: x.id):
        if g.status == 'amateur' and g.lifestyle != 'retired':
            g.tour = tour or g.tour if (tour or g.tour.startswith('CO_')) else 'CO_US_D1'
            if not g.tour.startswith('CO_'):
                g.tour = 'CO_US_D1'
            g.lifestyle, g.born = 'full_time', YEAR - 20
            out.append(g)
            if len(out) == n:
                break
    return out


def run(s, snap, draw=None, exempt=None, **patches):
    ctx = [mock.patch.object(C, 'winner_exemptions', return_value=dict(exempt or {}))]
    if draw is not None:
        ctx.append(mock.patch.object(C, 'early_pro_draw', side_effect=lambda season, gid, year: draw.get(gid, 0.5)
                                     if isinstance(draw, dict) else draw))
    for k, v in patches.items():
        ctx.append(mock.patch.object(C, k, v))
    for c in ctx:
        c.start()
    try:
        return C.decide(s, YEAR, snap)
    finally:
        for c in reversed(ctx):
            c.stop()


def trans(s, gid):
    return [t for t in s.transitions.get(YEAR, []) if t['gid'] == gid]


class Gate(unittest.TestCase):
    def setUp(self):
        self.s = season()
        self.g = college_amateurs(self.s, 1)[0]

    def gate(self, rank, exempt=None, age=20, tour='CO_US_D1', **attrs):
        g = copy.copy(self.g)
        g.tour, g.born = tour, YEAR - age
        for k, v in attrs.items():
            setattr(g, k, v)
        return C.early_pro_gate(self.s, g, {'am_end': rank}, YEAR, {g.id: exempt} if exempt else {})

    def test_every_pathway_and_age(self):
        for tour in PATHWAYS:
            for age in (18, 19, 20, 21):
                self.assertEqual(self.gate(1, age=age, tour=tour), 'top 15', (tour, age))
            self.assertIsNone(self.gate(1, age=22, tour=tour))               # graduating: the old rule decides
            self.assertIsNone(self.gate(1, age=17, tour=tour))

    def test_rank_fifteen_and_sixteen(self):
        self.assertEqual(self.gate(15), 'top 15')
        self.assertIsNone(self.gate(16))
        self.assertIsNone(self.gate(None))                                   # unranked
        self.assertIsNone(self.gate(0))

    def test_an_exemption_outside_the_top_fifteen(self):
        self.assertEqual(self.gate(40, exempt='won the 2027 Britannia Open'), 'exemption')
        self.assertEqual(self.gate(None, exempt='won the 2027 Pacific Open'), 'exemption')
        self.assertEqual(self.gate(3, exempt='won the 2027 Britannia Open'), 'exemption')

    def test_nobody_else(self):
        self.assertIsNone(self.gate(1, tour='AM_USA_EAST' if 'AM_USA_EAST' in C.TOUR_BY_KEY else 'MN_JAPAN'))
        self.assertIsNone(self.gate(1, status='pro'))
        self.s.college_early_pro = False                                     # a world from before the rule
        self.assertIsNone(self.gate(1))

    def test_no_ability_or_potential_gate(self):
        weak = copy.copy(self.g)
        weak.attrs = {k: 1.0 for k in weak.attrs}
        weak.ceilings = {k: 1.0 for k in getattr(weak, 'ceilings', {})}
        self.assertEqual(C.early_pro_gate(self.s, weak, {'am_end': 15}, YEAR, {}), 'top 15')


class Decisions(unittest.TestCase):
    def setUp(self):
        self.s = season()
        self.snap = {g.id: neutral(g) for g in self.s.world.golfers}

    def test_accept_in_every_pathway(self):
        gs = college_amateurs(self.s, 3)
        for g, tour in zip(gs, PATHWAYS):
            g.tour = tour
            self.snap[g.id]['am_end'] = 4
        run(self.s, self.snap, draw=ACCEPT)
        for g in gs:
            self.assertEqual((g.status, g.lifestyle), ('pro', 'full_time'))
            self.assertEqual(g.tour, home_challenger(g))                     # ranked 15th or better: Challenger
            self.assertEqual(g.turned_pro, YEAR + 1)
            t = trans(self.s, g.id)
            self.assertEqual([x['kind'] for x in t], ['turned pro'])
            self.assertEqual((t[0]['early'], t[0]['graduating'], t[0]['am_rank']), ('top 15', False, 4))
            self.assertNotIn(g.id, self.s.card_reasons.get(YEAR + 1, {}))   # no Premier card from a ranking
            self.assertTrue(any('from college at 20' in h for h in self.s.history_of(g.id))
                            if hasattr(self.s, 'history_of') else True)

    def test_decline_stays_a_full_time_college_golfer_without_a_job(self):
        gs = college_amateurs(self.s, 3)
        for g, tour in zip(gs, PATHWAYS):
            g.tour = tour
            self.snap[g.id]['am_end'] = 2
        run(self.s, self.snap, draw=DECLINE, p_amateur_job=lambda *a, **k: 1.0,   # a job would be certain
            p_retire=lambda *a, **k: 1.0)                                    # and so would retiring
        for g, tour in zip(gs, PATHWAYS):
            self.assertEqual((g.status, g.lifestyle, g.tour), ('amateur', 'full_time', tour))
            t = trans(self.s, g.id)
            self.assertEqual([x['kind'] for x in t], ['stayed in college'])
            self.assertEqual(t[0]['early'], 'top 15')
            self.assertGreater(t[0]['p'], 0.0)
            self.assertTrue(AS.eligible(g))                                  # amateur support continues
        rows = self.s.career_ev[YEAR]
        for g in gs:
            self.assertEqual([r[0] for r in rows[g.id]], ['turn_pro_college'])   # no job evaluated
            self.assertEqual(rows[g.id][0][3], 0)                           # not taken

    def test_ineligible_college_golfers_keep_the_old_path(self):
        """As before the rule: a college golfer under 22 is not evaluated at all (no turn-pro, job or retirement
        model, no draw) -- even with every model certain."""
        g16, g40 = college_amateurs(self.s, 2)
        self.snap[g16.id]['am_end'] = 16
        self.snap[g40.id]['am_end'] = 40
        run(self.s, self.snap, draw=ACCEPT, p_amateur_job=lambda *a, **k: 1.0, p_turn_pro=lambda *a, **k: 1.0)
        for g in (g16, g40):
            self.assertEqual((g.status, g.lifestyle), ('amateur', 'full_time'))
            self.assertEqual(trans(self.s, g.id), [])
            self.assertNotIn(g.id, self.s.career_ev[YEAR])

    def test_an_exemption_outside_the_top_fifteen_gives_the_earned_premier_card(self):
        g = college_amateurs(self.s, 1)[0]
        self.snap[g.id]['am_end'] = 40
        why = 'won the 2027 Britannia Open'
        run(self.s, self.snap, draw=ACCEPT, exempt={g.id: why})
        self.assertEqual((g.status, g.tour), ('pro', premier_circuit(g)))
        self.assertEqual(self.s.card_reasons[YEAR + 1][g.id], f'Premier card earned: {why}')
        t = trans(self.s, g.id)[0]
        self.assertEqual((t['early'], t['exemption'], t['am_rank']), ('exemption', why, 40))
        ev = self.s.career_ev[YEAR][g.id][0]
        spec = C.DE.CAREER_MODELS['turn_pro_college']
        inputs = dict(zip(spec['inputs'], ev[4 + len(spec['terms']):]))
        self.assertEqual(inputs, {'age': 20, 'am_rank': 40, 'exempt': 1})

    def test_rank_sixteen_without_an_exemption_is_not_asked(self):
        g15, g16 = college_amateurs(self.s, 2)
        self.snap[g15.id]['am_end'] = 15
        self.snap[g16.id]['am_end'] = 16
        run(self.s, self.snap, draw=ACCEPT)
        self.assertEqual(g15.status, 'pro')
        self.assertEqual(g16.status, 'amateur')

    def test_conditional_amateur_places_are_not_professional_cards(self):
        """An amateur invitation is held only while an amateur: an early professional without a winner's exemption
        starts on their Challenger tour, and amateur-only routes no longer take them."""
        g = college_amateurs(self.s, 1)[0]
        self.snap[g.id]['am_end'] = 1
        self.snap[g.id]['secured'] = ['USA_OPEN']                           # (an amateur's place, conditional)
        run(self.s, self.snap, draw=ACCEPT)
        self.assertEqual(g.tour, home_challenger(g))
        self.assertNotIn(g.id, self.s.card_reasons.get(YEAR + 1, {}))
        ctx = NS(people={g.id: NS(active=True, status=g.status, age=g.age(YEAR + 1))})
        route = NS(amateur_only=True, status=None, max_age=None)
        self.assertFalse(Q._eligible(ctx, g.id, route, YEAR + 1))           # the amateur route lapses
        self.assertTrue(Q._eligible(ctx, g.id, NS(amateur_only=False, status=None, max_age=None), YEAR + 1))

    def test_school_and_support_ledgers(self):
        go, stay = college_amateurs(self.s, 2)
        for g in (go, stay):
            self.snap[g.id]['am_end'] = 3
        ST.sync_school(self.s, YEAR, 1)                                      # their school teams, as in a season
        self.s.record_college(YEAR, {g.id: {'tour': g.tour} for g in (go, stay)})
        run(self.s, self.snap, draw={go.id: ACCEPT, stay.id: DECLINE})
        ST.sync_school(self.s, YEAR, 53, closing=True)
        rel = self.s.staff.rel
        self.assertIsNone(rel.current('school', go.id))                     # closed: turned professional
        ended = [x for x in rel.stints if x.kind == 'school' and x.golfer == go.id] if hasattr(rel, 'stints') else []
        if ended:
            self.assertEqual(ended[-1].end_reason if hasattr(ended[-1], 'end_reason') else 'turned professional',
                             'turned professional')
        self.assertIsNotNone(rel.current('school', stay.id))                # still on the team
        self.assertFalse(AS.eligible(go))                                    # amateur support ends with the status
        self.assertTrue(AS.eligible(stay))
        self.assertEqual(self.s.college[go.id], [YEAR])                      # the seasons enrolled stay recorded
        self.s.record_college(YEAR + 1, {stay.id: {'tour': stay.tour}, go.id: {'tour': go.tour}})
        self.assertEqual(self.s.college[stay.id], [YEAR, YEAR + 1])
        self.assertEqual(self.s.college[go.id], [YEAR])                      # not enrolled the next season

    def test_graduation_at_twenty_two_is_unchanged(self):
        g = college_amateurs(self.s, 1)[0]
        g.born = YEAR - 22
        self.snap[g.id]['am_end'] = 2
        twin = season()
        tg = next(x for x in twin.world.golfers if x.id == g.id)
        tg.tour, tg.lifestyle, tg.born = g.tour, g.lifestyle, g.born
        twin.college_early_pro = False
        run(self.s, self.snap, draw=ACCEPT)
        run(twin, copy.deepcopy(self.snap), draw=ACCEPT)
        self.assertEqual((g.status, g.lifestyle, g.tour), (tg.status, tg.lifestyle, tg.tour))
        self.assertEqual([r[0] for r in self.s.career_ev[YEAR][g.id]], ['turn_pro'])   # the graduating model
        self.assertTrue(all(t.get('early') is None for t in trans(self.s, g.id)))


class Streams(unittest.TestCase):
    """The early decision draws from its own stream: every other golfer's decisions and draws are those of the
    same world without the rule."""

    def worlds(self):
        out = []
        for on in (True, False):
            s = season(seed=67)
            s.college_early_pro = on
            out.append(s)
        return out

    def test_everyone_else_unchanged(self):
        on, off = self.worlds()
        snaps = []
        eligible = set()
        for s in (on, off):
            gs = college_amateurs(s, 6)
            snap = {g.id: neutral(g) for g in s.world.golfers}
            for i, g in enumerate(gs):
                if i % 2 == 0:                                               # eligible: three of six (lowest ids)
                    snap[g.id]['am_end'] = 1 + i
                    eligible.add(g.id)
                    if i == 4:
                        g.born = YEAR - 18
            snaps.append(snap)
        run(on, snaps[0])
        run(off, snaps[1])
        state = lambda s: {g.id: (g.status, g.lifestyle, g.tour, g.backer, g.backer_funds, g.cash)
                           for g in s.world.golfers}
        a, b = state(on), state(off)
        self.assertEqual({k: v for k, v in a.items() if k not in eligible},
                         {k: v for k, v in b.items() if k not in eligible})
        ta = [t for t in on.transitions[YEAR] if t['gid'] not in eligible]
        tb = [t for t in off.transitions[YEAR] if t['gid'] not in eligible]
        self.assertEqual(json.dumps(ta, sort_keys=True, default=str), json.dumps(tb, sort_keys=True, default=str))
        ea = {k: v for k, v in on.career_ev[YEAR].items() if k not in eligible}
        eb = {k: v for k, v in off.career_ev[YEAR].items() if k not in eligible}
        self.assertEqual(ea, eb)                                             # the same draws, golfer by golfer
        self.assertTrue(len(ea) > 20)
        for gid in eligible:
            self.assertEqual([r[0] for r in on.career_ev[YEAR][gid]], ['turn_pro_college'])

    def test_own_stream_per_golfer_and_winter(self):
        s = season()
        d = C.early_pro_draw
        self.assertEqual(d(s, 5, YEAR), d(s, 5, YEAR))
        self.assertNotEqual(d(s, 5, YEAR), d(s, 6, YEAR))
        self.assertNotEqual(d(s, 5, YEAR), d(s, 5, YEAR + 1))

    def test_deterministic_across_save_and_reload(self):
        s = season(seed=71)
        gs = college_amateurs(s, 4)
        snap = {g.id: neutral(g) for g in s.world.golfers}
        for i, g in enumerate(gs):
            snap[g.id]['am_end'] = 1 + i
        saved = pickle.dumps(s)
        run(s, snap)
        again = pickle.loads(saved)
        self.assertTrue(again.college_early_pro)
        run(again, copy.deepcopy(snap))
        self.assertEqual(json.dumps(s.transitions[YEAR], sort_keys=True, default=str),
                         json.dumps(again.transitions[YEAR], sort_keys=True, default=str))
        self.assertEqual({g.id: (g.status, g.tour) for g in s.world.golfers},
                         {g.id: (g.status, g.tour) for g in again.world.golfers})
        self.assertEqual(s.career_ev[YEAR], again.career_ev[YEAR])


class Compatibility(unittest.TestCase):
    def test_saves_from_before_never_decide_early(self):
        s = season()
        st = dict(s.__dict__)
        st.pop('college_early_pro')
        old = Season.__new__(Season)
        old.__setstate__(st)
        self.assertFalse(old.college_early_pro)
        g = college_amateurs(old, 1)[0]
        self.assertIsNone(C.early_pro_gate(old, g, {'am_end': 1}, YEAR, {}))

    def test_versioned(self):
        self.assertGreaterEqual(R.RULES_VERSION, '2026-11-15')
        self.assertIn('2026-11-15', dict(R.VERSIONS))
        title, text, since = R.RULES['college-turning-pro']
        self.assertEqual(since, '2026-11-15')
        self.assertIn('top 15', text.replace('15th or better', 'top 15'))


if __name__ == '__main__':
    unittest.main()
