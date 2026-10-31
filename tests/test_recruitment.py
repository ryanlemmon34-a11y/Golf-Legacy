"""Two-way recruitment of coaches and caddies (rules 2026-11-04): assessments that firm up with seasons
watched, coaches' motivations, refusals with reasons, loyalty, the record kept on both profiles, determinism,
money and capacity, and no reads of hidden potential or ceilings.

Run from the project folder:  python -m unittest tests.test_recruitment -v
"""
from __future__ import annotations

import ast
import copy
import inspect
import json
import pickle
import random
import sys
import textwrap
import unittest
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
from golfsim import staff as ST                                       # noqa: E402
from golfsim.archive import ArchiveWriter                              # noqa: E402
from golfsim.history import Relations                                  # noqa: E402
from golfsim.population import age_deficit, generate_world             # noqa: E402
from golfsim.season import Season                                      # noqa: E402


def fresh(seed=41, scale=0.05):
    return Season(generate_world(seed=seed, scale=scale), seed=seed, development=True, workers=1)


_SMALL = []


def small():
    """A scale-0.1 world after its first winter's market (built once, when a test first needs it)."""
    if not _SMALL:
        s = fresh(41, 0.1)
        s.start_year(2027)
        _SMALL.append(s)
    return _SMALL[0]


class _Stub:
    """An rng whose draws are fixed (a decision then follows its probability against this value)."""

    def __init__(self, u):
        self.u = u

    def random(self):
        return self.u


def young(s, n, max_age=21):
    return [g for g in sorted(s.world.golfers, key=lambda x: x.id)
            if g.lifestyle != 'retired' and g.status == 'amateur' and g.age(2027) <= max_age][:n]


class AssessmentTests(unittest.TestCase):
    def test_firming_shrinks_with_seasons_watched(self):
        f = [ST.firming(n) for n in range(1, ST.WATCH_MAX + 3)]
        self.assertEqual(f[0], 1.0)
        self.assertTrue(all(a > b for a, b in zip(f[:ST.WATCH_MAX - 1], f[1:ST.WATCH_MAX])))
        self.assertEqual(f[ST.WATCH_MAX - 1], f[-1])                      # no further after WATCH_MAX seasons

    def test_error_shrinks_with_seasons_watched_from_observable_inputs(self):
        """The same coach's error about the same player shrinks exactly by firming(n); what is left is the
        observable projection (level seen, growth for the age, last year's rise)."""
        s = small()
        players = young(s, 30)
        for cid in (11, 12, 13):
            for g in players:
                est = lambda sd, n: ST.scouting_estimate(s, g, 2027, random.Random(f'{cid}:{g.id}'), sd, cid, n)
                clean = est(0.0, 1)                                       # no scouting error at all
                e1 = est(9.0, 1) - clean
                for n in (2, 4):
                    self.assertAlmostEqual(est(9.0, n) - clean, ST.firming(n) * e1, places=9)
                    self.assertLess(abs(est(9.0, n) - clean), abs(e1) + 1e-12)
                last = s.overall_start.get(2026, {}).get(g.id)
                age = g.age(2027)
                typical = age_deficit(age, 27.0) - age_deficit(age + 1, 27.0)
                seen = clean - age_deficit(age, 27.0) - 1.5 * ((g.overall - last if last is not None else 0.0) - typical)
                self.assertLess(abs(seen - g.overall), 10.0)              # the level, seen with error
        # hidden potential and ceilings are invisible to a scout
        g = players[0]
        twin = copy.deepcopy(g)
        twin.potential = min(99.0, g.potential + 25)
        twin.ceilings = {k: 99.0 for k in g.ceilings}
        for n in (1, 3):
            a = ST.scouting_estimate(s, g, 2027, random.Random(5), 9.0, 7, n)
            b = ST.scouting_estimate(s, twin, 2027, random.Random(5), 9.0, 7, n)
            self.assertEqual(a, b)

    def test_seasons_watched_are_recorded_per_coach_and_player(self):
        s = fresh(43)
        st = s.staff
        home = s.home_country
        g = next(g for g in young(s, 400, 22) if any(c.status == 'active' and s.places.country(c.id, c.country) == home(g)
                                                     for c in st.coaches.values()))
        c = next(c for c in sorted(st.coaches.values(), key=lambda c: c.id)
                 if c.status == 'active' and s.places.country(c.id, c.country) == home(g))
        st.watched[(c.id, g.id)] = (2, 2026, True)                        # watched twice, still following
        st.watched[(c.id, -1)] = (4, 2024, False)                         # long forgotten
        s.start_year(2027)
        self.assertEqual(st.watched[(c.id, g.id)][:2], (3, 2027))         # followed, and one more season watched
        self.assertNotIn((c.id, -1), st.watched)
        this = [w for w in st.watched.values() if w[1] == 2027]
        self.assertGreater(len(this), 100)
        self.assertTrue(all(w[0] >= 1 for w in this))


class MotivationTests(unittest.TestCase):
    def setUp(self):
        self.s = s = fresh(44)
        self.a, self.b = young(s, 2, 20)                                   # same age band, both amateurs
        a, b = self.a, self.b
        s.overall_start[2026] = {a.id: a.overall - 7.0, b.id: b.overall - 0.3}   # a rose fast last year
        s.am_pos.pop(a.id, None)
        s.wr_pos.pop(a.id, None)
        s.fame[a.id] = 0.0
        s.legacy[a.id] = 0.0
        s.fame[b.id] = 100.0                                              # b has established results
        s.am_pos[b.id] = 2
        self.majors = {b.id: 1}
        st = self.st = ST.Staff()
        rng = random.Random(1)
        self.dev = st.new_coach(rng, 'USA', 2027, 45, 60, 60, 'putting', True, 60, 'test')
        self.est = st.new_coach(rng, 'USA', 2027, 45, 60, 60, 'putting', False, 60, 'test')

    def test_development_and_established_coaches_rank_the_same_candidates_differently(self):
        s, st, a, b = self.s, self.st, self.a, self.b
        rate = lambda c, g: ST.coach_rates(s, st, c, g, 2027, 72.0, 8.0, self.majors.get(g.id, 0))
        (dev_a, why_dev_a), (dev_b, _) = rate(self.dev, a), rate(self.dev, b)
        (est_a, _), (est_b, why_est_b) = rate(self.est, a), rate(self.est, b)
        self.assertGreater(dev_a, dev_b)                                  # growth first
        self.assertGreater(est_b, est_a)                                  # achievement first
        self.assertIn('fast improver', why_dev_a)
        self.assertIn('development coach', why_dev_a)
        self.assertIn('established results', why_est_b)
        self.assertIn('established players', why_est_b)

    def test_who_a_coach_with_a_filling_book_takes_on(self):
        s, st, a, b = self.s, self.st, self.a, self.b
        take = lambda c, g: ST.coach_takes(s, st, c, g, 2027, c.capacity - 1, self.majors.get(g.id, 0))
        self.assertGreater(take(self.dev, a)[0], take(self.est, a)[0])
        self.assertGreater(take(self.est, b)[0], take(self.dev, b)[0])
        self.assertGreater(ST.coach_takes(s, st, self.est, a, 2027, 0)[0], 0.95)   # room: rarely a no
        self.assertIn('young players', take(self.dev, b)[2])
        self.assertIn('established results', take(self.est, a)[2])


class TwoWayTests(unittest.TestCase):
    def test_refusals_happen_on_every_side_and_are_recorded_with_reasons(self):
        s = small()
        st = s.staff
        refs = st.rel.refusals
        self.assertEqual({r[6] for r in refs}, {'golfer', 'coach', 'caddie'})
        for kind, staff, golfer, year, week, asked, said_no, why, no, kept in refs:
            self.assertIn(staff, st.coaches if kind == 'coach' else st.caddies)
            self.assertIn(golfer, s.g)
            self.assertEqual((year, week), (2027, 1))
            self.assertTrue(why and no)
            self.assertNotEqual(asked, said_no)
            if said_no != 'golfer':                                        # (a player who said no to a share
                began = [x for x in st.rel.of_golfer(golfer, kind)         # deal may still hire that coach)
                         if x.staff == staff and x.start == (2027, 1)]
                self.assertEqual(began, [])                                # no partnership began
        logged = [t for gid in {r[2] for r in refs} for _, _, t in s.history[gid]]
        self.assertTrue(any('Turned down an approach from' in t for t in logged))
        self.assertTrue(any('declined to work with them' in t for t in logged))
        new = [x for x in st.rel.stints if x.kind in ('coach', 'caddie') and x.start == (2027, 1)]
        self.assertTrue(new)
        self.assertTrue(all(x.reason_start and x.reason_accept for x in new))

    def test_a_caddie_weighs_earnings_fit_and_stability(self):
        s = small()
        st = s.staff
        k = copy.deepcopy(next(iter(st.caddies.values())))
        k.id, k.reputation = -5, 85.0
        premier = next(g for g in s.world.golfers if g.tour.startswith('PT_') and g.lifestyle != 'retired')
        challenger = copy.deepcopy(premier)
        challenger.tour = next(t for t in ST.TOUR_BY_KEY if ST.TOUR_BY_KEY[t].tier == 2)
        poor, rich = ST.caddie_answers(st, k, challenger, 30.0), ST.caddie_answers(st, k, premier, 95.0)
        self.assertLess(poor[0], 0.5)
        self.assertGreater(rich[0], 0.95)
        self.assertEqual(poor[2], 'wanted a bag with bigger earnings')
        self.assertGreater(ST.caddie_answers(st, k, challenger, 30.0, turned_down=4)[0], poor[0])   # waiting wears
        self.assertGreater(ST.caddie_answers(st, k, premier, 30.0)[0], poor[0])                     # a Premier card


class LoyaltyTests(unittest.TestCase):
    def test_a_better_known_offer_alone_does_not_end_a_good_partnership(self):
        s = fresh(45)
        st = s.staff
        g, h = young(s, 2, 21)
        rng = random.Random(3)
        cur = st.new_coach(rng, 'USA', 2027, 50, 55, 55, 'putting', False, 40, 'test')
        offer = st.new_coach(rng, 'USA', 2027, 50, 70, 70, 'putting', True, 90, 'test')
        st.assign_coach(s, g, cur, 'share', (2024, 1), 'coach', 'test', 'test')
        st.rel.add_work('coach', g.id, 80.0, 2026)                         # years of work together
        st.rel.pair('coach', cur.id, g.id).fit = 1.0
        st.rel.current('coach', g.id).seasons += [(2025, 0.6, 1.0), (2026, 0.6, 1.0)]   # progress together
        st.assign_coach(s, h, cur, 'share', (2027, 1), 'coach', 'test', 'test')         # brand new, nothing built
        p_good, _, no = ST.golfer_answers(s, st, g, offer, 2027)
        p_new, yes, _ = ST.golfer_answers(s, st, h, offer, 2027)
        self.assertLess(p_good, 0.1)
        self.assertGreater(p_new, 0.5)
        self.assertTrue(no.startswith(f'stayed with {cur.name}'))
        self.assertIn('a strong working relationship', no)
        # the same draw: the good partnership holds, the new one does not
        kept = st.rel.current('coach', g.id)
        self.assertFalse(ST.approach(s, offer, g, 'saw promising growth', (2027, 1), _Stub(0.3)))
        self.assertTrue(ST.approach(s, offer, h, 'saw promising growth', (2027, 1), _Stub(0.3)))
        self.assertIs(st.coach(g.id), cur)
        self.assertIs(st.coach(h.id), offer)
        self.assertEqual(kept.declined, [(2027, 1, offer.id, no)])
        left = [x for x in st.rel.of_golfer(h.id, 'coach') if x.end]
        self.assertEqual(left[0].reason_end, f'left for an approach from {offer.name}')
        self.assertEqual(st.rel.current('coach', h.id).reason_accept, yes)
        # recorded on the stints both people share, and archived so either profile can show them
        tables = ArchiveWriter.state_tables(SimpleNamespace(created={}, initial=set()), s)
        rel = Relations.load(json.loads(json.dumps(tables['relations.json.gz'])))
        for x in (kept, st.rel.current('coach', h.id), left[0]):
            a = next(y for y in rel.of_golfer(x.golfer) if y.id == x.id)
            b = next(y for y in rel.of_staff(x.staff) if y.id == x.id)
            self.assertIs(a, b)
            self.assertEqual((a.reason_start, a.reason_accept, a.reason_end), (x.reason_start, x.reason_accept, x.reason_end))
            self.assertEqual([tuple(d) for d in a.declined], [tuple(d) for d in x.declined])
        self.assertEqual(rel.refusals, [list(r) for r in st.rel.refusals])
        self.assertEqual(rel.refusals[0][9], kept.id)                      # the partnership the golfer kept


class WorldTests(unittest.TestCase):
    """Two runs of the same small world: one season and the next winter's market."""

    @classmethod
    def setUpClass(cls):
        import long_world as LW
        cls.runs = []
        for _ in range(2):
            s = fresh(47)
            before = sum(1 for g in s.world.golfers if g.lifestyle != 'retired')
            s.run_year(2027)
            checks = LW.checks(s, 2027, s.snapshots[2027], before)
            s.start_year(2028)
            cls.runs.append((s, checks))

    def test_same_seed_same_staff_outcomes(self):
        (a, _), (b, _) = self.runs
        self.assertEqual(json.dumps(a.staff.rel.export()), json.dumps(b.staff.rel.export()))
        self.assertEqual(a.staff.watched, b.staff.watched)
        self.assertEqual((a.staff.coach_of, a.staff.deal, a.staff.caddie_of), (b.staff.coach_of, b.staff.deal, b.staff.caddie_of))
        self.assertTrue(a.staff.rel.refusals)
        self.assertTrue(any(x.end and x.end[0] == 2027 for x in a.staff.rel.stints if x.kind != 'school'))

    def test_money_reconciles_and_capacity_holds(self):
        s, c = self.runs[0]
        self.assertEqual(c['reconcile_errors'], 0)
        self.assertEqual(c['staff_violations'], 0)
        self.assertAlmostEqual(c['coach_paid'], c['coach_received'], places=2)
        self.assertAlmostEqual(c['caddie_paid'], c['caddie_received'], places=2)
        self.assertGreater(c['caddie_paid'], 0)
        st = s.staff                                                       # and after the next winter's market
        load = Counter(st.coach_of.values())
        self.assertTrue(all(n <= st.coaches[cid].capacity for cid, n in load.items()))
        shares = Counter(cid for gid, cid in st.coach_of.items() if st.deal[gid] == 'share')
        self.assertTrue(all(n <= st.coaches[cid].capacity // 3 for cid, n in shares.items()))
        self.assertEqual(len(set(st.caddie_of.values())), len(st.caddie_of))
        self.assertTrue(all(st.coaches[cid].status == 'active' for cid in st.coach_of.values()))
        self.assertTrue(all(st.caddies[kid].status == 'active' for kid in st.caddie_of.values()))


class HiddenTests(unittest.TestCase):
    NEW = ('firming', 'scouting_estimate', 'motivation', 'recent_rise', 'earned_majors', 'achievement', 'coach_rates',
           'loyalty', 'last_prize', 'golfer_answers', 'coach_takes', 'results_level', 'caddie_answers', 'approach')

    def test_new_decision_code_never_reads_potential_or_ceilings(self):
        """Every name, attribute and string the new decisions use (docstrings aside), and every function they
        call in this module, checked for potential, ceilings and the golfer's own reading of them."""
        seen, todo = set(), list(self.NEW)
        while todo:
            name = todo.pop()
            if name in seen:
                continue
            seen.add(name)
            tree = ast.parse(textwrap.dedent(inspect.getsource(getattr(ST, name))))
            docs = {id(f.body[0].value) for f in ast.walk(tree) if isinstance(f, ast.FunctionDef)
                    and isinstance(f.body[0], ast.Expr) and isinstance(f.body[0].value, ast.Constant)}
            for node in ast.walk(tree):
                if isinstance(node, ast.Attribute):
                    word = node.attr
                elif isinstance(node, ast.Name):
                    word = node.id
                    if inspect.isfunction(getattr(ST, word, None)) and getattr(ST, word).__module__ == ST.__name__:
                        todo.append(word)                                  # follow calls within staff.py
                elif isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docs:
                    word = node.value
                else:
                    continue
                for bad in ('potential', 'ceiling', 'perceived_gap'):
                    self.assertNotIn(bad, word.lower(), f'{name}: {word}')
        self.assertIn('trend', seen)                                       # (the calls were followed)

    def test_shifting_hidden_potential_changes_no_staff_outcome(self):
        def market(shift):
            s = fresh(48)
            for g in s.world.golfers:
                g.potential = min(99.0, g.potential + shift)
            s.start_year(2027)
            return json.dumps(s.staff.rel.export()), s.staff.watched
        self.assertEqual(market(0.0), market(20.0))

    def test_saves_from_before_two_way_recruitment_load_with_defaults(self):
        s = fresh(49)
        s.start_year(2027)
        del s.staff.watched, s.staff.rel.refusals
        for x in s.staff.rel.stints:
            del x.declined
        t = pickle.loads(pickle.dumps(s))
        self.assertEqual((t.staff.watched, t.staff.rel.refusals), ({}, []))
        self.assertTrue(all(x.declined == [] for x in t.staff.rel.stints))
        s.close()
        t.close()


class ObserverRefusalTests(unittest.TestCase):
    """Approaches turned down show on the profiles of a golfer, coach or caddie with whom no partnership ever began,
    from the history and, before the season is archived, from the running world's snapshot (no world needed)."""
    GOLFER, COACH, CADDIE = 101, 201, 301

    @classmethod
    def setUpClass(cls):
        import observer as O
        import observer_history as OH
        import observer_live as OL
        cls.O, cls.OH, cls.OL = O, OH, OL

    def relations(self, year):
        rel = Relations(1)
        rel.refuse('coach', self.COACH, self.GOLFER, (year, 1), 'coach', 'golfer', 'saw promising growth',
                   'happy with their college team\'s coaching')
        rel.refuse('caddie', self.CADDIE, self.GOLFER, (year, 1), 'golfer', 'caddie', 'the best caddie they could afford',
                   'wanted a bag with bigger earnings')
        return rel

    def world(self, archive_rel=None, live_rel=None):
        people = {self.GOLFER: {'name': 'G', 'golfer': {}}, self.COACH: {'name': 'C', 'coach': {'status': 'active'}},
                  self.CADDIE: {'name': 'K', 'caddie': {'status': 'active'}}}
        a = None
        if archive_rel is not None:
            a = SimpleNamespace(rel=archive_rel, people=people, years=[2027], golfer_staff=archive_rel.of_golfer,
                                staff_clients=lambda pid, role=None: [])
        live = None
        if live_rel is not None:
            live = SimpleNamespace(people=people, coach_of={}, caddie_of={}, wr={},
                                   refusals=self.OL._refusals(live_rel, [2027] if a else [], 2027))
        return SimpleNamespace(a=a, live=live, person_link=lambda pid: f'[{pid}]',
                               person=lambda pid: people.get(pid))

    def check(self, w, year):
        golfer = self.OH.team_history(w, self.GOLFER)
        self.assertIn('Approaches turned down (2)', golfer)
        self.assertIn('happy with their college team&#x27;s coaching', golfer)
        self.assertIn('wanted a bag with bigger earnings', golfer)
        self.assertIn(f'{year} wk 1', golfer)
        for pid, role, why in ((self.COACH, 'coach', 'saw promising growth'),
                               (self.CADDIE, 'caddie', 'the best caddie they could afford')):
            page = self.O._staff(w, pid, role)
            self.assertIn('Approaches turned down (1)', page)
            self.assertIn(why, page)
        return golfer

    def test_refusal_only_people_show_their_refusals_from_the_history(self):
        golfer = self.check(self.world(archive_rel=self.relations(2027)), 2027)
        self.assertNotIn('(this season)', golfer)

    def test_this_seasons_refusals_show_before_the_season_is_archived(self):
        golfer = self.check(self.world(archive_rel=Relations(1), live_rel=self.relations(2028)), 2028)
        self.assertIn('(this season)', golfer)
        golfer = self.check(self.world(live_rel=self.relations(2027)), 2027)        # nothing archived yet
        # a refusal in both the history and the snapshot is one record, read once
        both = self.world(archive_rel=self.relations(2027), live_rel=self.relations(2027))
        both.live.refusals = [list(r) for r in self.relations(2027).refusals]
        self.assertIn('Approaches turned down (2)', self.OH.team_history(both, self.GOLFER))

    def test_live_snapshot_stints_carry_acceptance_and_declined(self):
        rel = Relations(1)
        s = rel.begin('coach', self.COACH, self.GOLFER, (2028, 1), 'share', 'coach', 'saw promising growth',
                      accept='a share deal costs nothing now')
        rel.refuse('coach', 999, self.GOLFER, (2028, 1), 'coach', 'golfer', 'established results',
                   'stayed with C: a good fit')
        got = self.OL._stints(rel, [2027], 2027)
        self.assertEqual(got[0]['reason_accept'], 'a share deal costs nothing now')
        self.assertEqual(got[0]['declined'], [[2028, 1, 999, 'stayed with C: a good fit']])
        s.declined.append((2028, 2, 998, 'later'))
        self.assertEqual(len(got[0]['declined']), 1)                      # the snapshot is a copy
        self.assertEqual(self.OL._refusals(rel, [2027], 2027)[0][9], s.id)


if __name__ == '__main__':
    unittest.main()
