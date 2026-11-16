"""Course fit and recorded familiarity in choosing events (calendar v3; golfsim/course_fit.py, docs/career/COURSE_FIT.md).

Checks: the term is bounded and deterministic; it prefers, between otherwise equal courses, the one that asks for the
golfer's relative strengths and the one they know; it is added only to events the golfer may enter and afford (no
eligibility or capacity override); the read model draws no random number and changes nothing; replay is exact; and
the player's evidence is the same number the AI's choice uses. Calendars v1/v2 are unchanged (no term).

Run from the project folder:  python -m unittest tests.test_course_fit -v
"""
from __future__ import annotations

import random
import shutil
import sys
import tempfile
import unittest
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import career_fixture as F  # noqa: E402
from golfsim import course_fit as CF                                   # noqa: E402
from golfsim import decision_support as DS                             # noqa: E402
from golfsim import schedule as SCH                                    # noqa: E402
from golfsim.development import CATEGORIES                             # noqa: E402
from golfsim.population import generate_world                          # noqa: E402
from golfsim.season import Season                                      # noqa: E402
from golfsim.session import Session                                    # noqa: E402

_DIRS = []


def fresh(weeks=0, calendar='v3'):
    d = Path(tempfile.mkdtemp(prefix='course_fit_', dir=F.os.environ.get('TMPDIR')))
    _DIRS.append(d)
    s = Session.create(d / 'w', seed=11, world=generate_world(year=2027, seed=11, scale=0.05), workers=1,
                       calendar=calendar)
    if weeks:
        s.advance(weeks)
    return s


def tearDownModule():
    for d in _DIRS:
        shutil.rmtree(d, ignore_errors=True)


@contextmanager
def fit_rule(on):
    """Calendar v3 with the course-fit rule switched as given (test only)."""
    orig = SCH.spec
    SCH.spec = lambda v: replace(orig(v), course_fit=on) if v == 'v3' else orig(v)
    try:
        yield
    finally:
        SCH.spec = orig


def single_site(se, year):
    vs = se.venues(year)
    return [ed for ed in se.cal.editions(year) if len(vs[ed.event_id]) == 1]


class Term(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = fresh()
        cls.se = cls.s.season

    @classmethod
    def tearDownClass(cls):
        cls.s.close()

    def test_switched_on_for_v3_only(self):
        self.assertTrue(SCH.V3.course_fit)
        self.assertFalse(SCH.V2.course_fit)
        self.assertFalse(SCH.SPECS['v1'].course_fit)

    def test_bounded(self):
        """fit within [-1, 1], familiarity within [0, 1], points within [-FIT_WEIGHT, FIT_WEIGHT + FAM_WEIGHT]."""
        courses = [c for _, _, c in self.se.lib.layouts()]
        gs = self.se.active_golfers()[:120]
        for g in gs:
            for c in courses[::7]:
                e = CF.evaluate(g, c)
                self.assertLessEqual(abs(e['fit']), 1.0)
                self.assertTrue(0.0 <= e["familiarity"] <= 1.0)
                self.assertTrue(-CF.FIT_WEIGHT <= e["points"] <= CF.FIT_WEIGHT + CF.FAM_WEIGHT)
        # an extreme golfer and unlimited familiarity still stay inside the bound
        g = replace(gs[0], attrs={k: (99 if k in CATEGORIES['putting'] else 1) for k in gs[0].attrs},
                    familiarity={c.familiarity_key: 10_000 for c in courses})
        for c in courses:
            self.assertLess(CF.evaluate(g, c)['points'], CF.FIT_WEIGHT + CF.FAM_WEIGHT + 1e-9)

    def test_prefers_a_course_that_suits_and_one_they_know(self):
        courses = [c for _, _, c in self.se.lib.layouts()]
        putt = sorted(courses, key=lambda c: (CF.demand(c)['putting'] - CF.demand(c)['long_game'], c.layout_id))
        flat, putting_test = putt[0], putt[-1]
        g0 = self.se.active_golfers()[0]
        attrs = {k: 60.0 for k in g0.attrs}
        putter = replace(g0, attrs={k: (72.0 if k in CATEGORIES['putting'] else v) for k, v in attrs.items()},
                         familiarity={})
        hitter = replace(g0, attrs={k: (72.0 if k in CATEGORIES['long_game'] else v) for k, v in attrs.items()},
                         familiarity={})
        self.assertGreater(CF.evaluate(putter, putting_test)['points'], CF.evaluate(putter, flat)['points'])
        self.assertGreater(CF.evaluate(hitter, flat)['points'], CF.evaluate(hitter, putting_test)['points'])
        level = replace(g0, attrs=attrs, familiarity={})
        self.assertEqual(CF.evaluate(level, putting_test)['fit'], 0.0)            # no relative strength: no fit
        # familiarity: more recorded rounds, more appeal, never more than FAM_WEIGHT
        prev = CF.evaluate(level, flat)['points']
        for n in (1, 4, 12, 40, 100):
            p = CF.evaluate(replace(level, familiarity={flat.familiarity_key: n}), flat)['points']
            self.assertGreater(p, prev)
            self.assertLessEqual(p, CF.FAM_WEIGHT)
            prev = p

    def test_small_against_the_rest_of_an_events_appeal(self):
        """Over real golfers and this season's single-site events, the term's spread is small next to the existing
        per-choice noise (standard deviation 3) and prestige differences."""
        eds = single_site(self.se, 2027)[::6]
        pts = [CF.points(self.se, g, ed) for g in self.se.active_golfers()[:200] for ed in eds]
        mean = sum(pts) / len(pts)
        sd = (sum((p - mean) ** 2 for p in pts) / len(pts)) ** 0.5
        self.assertLess(sd, 1.5)
        prestige = sorted(self.se.event_prestige[ed.series.series_id] for ed in eds)
        self.assertGreater(prestige[-1] - prestige[0], 6 * (CF.FIT_WEIGHT + CF.FAM_WEIGHT))

    def test_multi_site_events_carry_no_term(self):
        vs = self.se.venues(2027)
        multi = [ed for ed in self.se.cal.editions(2027) if len(vs[ed.event_id]) > 1]
        self.assertTrue(multi)
        g = self.se.active_golfers()[0]
        for ed in multi:
            self.assertEqual(CF.points(self.se, g, ed), 0.0)
            self.assertEqual(CF.evidence(self.se, g, ed)['points'], 0.0)

    def test_evidence_is_the_number_the_choice_uses(self):
        """The player's evidence (week_compare's course_fit) is exactly what event_value adds for the same golfer,
        AI or player alike: event_value with the term minus without it, the same random draw."""
        se = self.se
        on = se.cal.spec
        g = next(x for x in se.active_golfers() if x.tour)
        for ed in single_site(se, 2027)[:25]:
            vc = 'US'                                                            # (base and cost are fixed)
            gw = se.golfer_week(g, 2027, ed.week)
            vals = []
            for fit in (True, False):
                with fit_rule(fit):
                    vals.append(se.event_value(g, ed, ed.week, random.Random(5), vc, cost=0.0, gw=dict(gw), base=50.0))
            self.assertIs(se.cal.spec, on)
            ev = DS._course_fit(se, g, ed.event_id)
            self.assertAlmostEqual(vals[0] - vals[1], ev['points'], places=9)
            self.assertEqual(ev['points'], CF.points(se, g, ed))
            self.assertNotIn('level', str(ev['factors']))                        # no attribute levels shown

    def test_v2_has_no_evidence(self):
        s = fresh(calendar='v2')
        g = s.season.active_golfers()[0]
        ed = single_site(s.season, 2027)[0]
        self.assertIsNone(CF.evidence(s.season, g, ed))
        self.assertEqual(CF.points(s.season, g, ed), 0.0)
        s.close()


class World(unittest.TestCase):
    def test_no_eligibility_or_capacity_override(self):
        """Even an absurd weight (+1000 for every event) is only ever added to events the golfer may enter and can
        pay for, and every field stays within its size: the term reorders choices, it opens no door."""
        s = fresh()
        se = s.season
        seen = []
        orig_points, orig_value = CF.points, Season.event_value

        def value(self, g, ed, week, rng, venue_country, cost=None, gw=None, base=None):
            seen.append((g.id, ed.series.series_id, week, self.eligible(g, ed.series, week),
                         cost is None or cost <= 0 or cost <= self.spendable(g, ed.year)))
            return orig_value(self, g, ed, week, rng, venue_country, cost, gw, base)
        CF.points = lambda season, g, ed, gw=None: 1000.0
        Season.event_value = value
        try:
            s.advance(8)
        finally:
            CF.points, Season.event_value = orig_points, orig_value
        self.assertTrue(seen)
        self.assertTrue(all(ok and paid for _, _, _, ok, paid in seen))
        for sid, fc in se.field_cutoffs.get(2027, {}).items():
            self.assertLessEqual(fc['admitted'], fc['capacity'], sid)
        s.close()

    def test_replay_and_no_extra_draws_from_the_read_model(self):
        """Two v3 worlds advanced the same weeks agree exactly; asking for the evidence (every golfer, every event)
        before each week changes nothing."""
        a, b = fresh(), fresh()
        for _ in range(6):
            se = b.season
            year, week = b.cursor['year'], b.cursor['week']
            for g in se.active_golfers()[:150]:
                for ed in se.cal.editions(year):
                    if ed.week == week:
                        CF.evidence(se, g, ed)
            a.advance(1)
            b.advance(1)
        self.assertEqual(F.digest(a), F.digest(b))
        a.close()
        b.close()

    def test_the_term_changes_choices(self):
        """It is a real input: with it off (otherwise the same v3 world) the AI's entries differ somewhere."""
        a, b = fresh(), fresh()
        a.advance(10)
        with fit_rule(False):
            b.advance(10)
        self.assertNotEqual(F.digest(a), F.digest(b))
        a.close()
        b.close()


class DemandCache(unittest.TestCase):
    """The demand cache is keyed by the Course object itself (a weak reference checks identity), never by layout id:
    the same layout id names different ground in worlds with other seeds (found by HAL on 811c179:
    jinlong-lakes-golf-club:Club, seed 11 vs 22)."""

    @classmethod
    def setUpClass(cls):
        from golfsim.course_library import CourseLibrary
        cls.a, cls.b = CourseLibrary(seed=11), CourseLibrary(seed=22)

    def uncached(self, c):
        CF._DEMAND.clear()
        out = CF.demand(c)
        CF._DEMAND.clear()
        return out

    def pairs(self):
        lb = {(site_key, c.layout_id): c for site_key, c in ((k, c) for _, k, c in self.b.layouts())}
        out = []
        for _, k, c in self.a.layouts():
            other = lb.get((k, c.layout_id))
            if other is not None and other.holes != c.holes:
                out.append((c, other))
        return out

    def test_same_layout_id_different_ground_either_order(self):
        pairs = self.pairs()
        self.assertTrue(pairs)                                              # the case exists
        truth = {id(c): self.uncached(c) for pair in pairs for c in pair}
        for order in (0, 1):
            CF._DEMAND.clear()
            for pair in pairs:
                for c in (pair if order == 0 else pair[::-1]):
                    self.assertEqual(CF.demand(c), truth[id(c)], c.layout_id)
        x, y = self.a.course('jinlong-lakes-golf-club:Club'), self.b.course('jinlong-lakes-golf-club:Club')
        self.assertNotEqual(self.uncached(x), self.uncached(y))
        CF._DEMAND.clear()
        self.assertEqual((CF.demand(x), CF.demand(y)), (self.uncached(x), self.uncached(y)))
        CF._DEMAND.clear()
        self.assertEqual((CF.demand(y), CF.demand(x)), (self.uncached(y), self.uncached(x)))

    def test_no_mutation(self):
        """Working out demand (cached or not) changes no course, and a returned dict cannot alter the cache."""
        import pickle
        cs = [c for _, _, c in self.a.layouts()][:40]
        before = [(pickle.dumps(c), dict(c.__dict__)) for c in cs]
        CF._DEMAND.clear()
        for c in cs:
            d = CF.demand(c)
            d['mental'] = 99.0
            self.assertNotEqual(CF.demand(c)['mental'], 99.0)
        self.assertEqual([(pickle.dumps(c), dict(c.__dict__)) for c in cs], before)

    def test_entries_die_with_their_course(self):
        import gc
        from dataclasses import replace as rep
        c = rep(next(c for _, _, c in self.a.layouts()))
        CF._DEMAND.clear()
        CF.demand(c)
        self.assertEqual(len(CF._DEMAND), 1)
        del c
        gc.collect()
        self.assertEqual(len(CF._DEMAND), 0)


class PlayerAIParity(unittest.TestCase):
    """Paired v3 worlds, the same state (week 18 of 2027, the week prepared), played once with a golfer left to the AI
    and once with the same golfer under a player's control whose plan enters the very event the AI chose. The
    options are valued the same (course-fit term included: the same numbers in both arms) and the worlds come out
    identical. A different player choice changes the world (the check can fail)."""

    @classmethod
    def setUpClass(cls):
        import pickle
        cls.s = fresh(17)
        cls.Y, cls.W = cls.s.cursor['year'], cls.s.cursor['week']
        cls.blob = pickle.dumps(cls.s.season, protocol=pickle.HIGHEST_PROTOCOL)
        cls.ai, cls.ai_vals = cls.arm()
        ent = {}
        for eid, r in cls.ai.results.items():
            if (r.year, r.week) == (cls.Y, cls.W):
                for site in r.finish:
                    for gid, _, _ in site:
                        ent[gid] = eid
        cls.entered = ent
        # golfers with a real choice whose AI choice was their first want (taken at the first ask)
        cands = [gid for gid, vals in sorted(cls.ai_vals.items()) if len({e for e, _ in vals}) >= 2 and gid in ent
                 and max(vals, key=lambda x: x[1])[0] == ent[gid]]
        by_event = {}
        for gid in cands:
            by_event.setdefault(ent[gid], gid)
        cls.pairs = [(gid, eid) for eid, gid in sorted(by_event.items())][:4]   # one golfer from up to four events

    @classmethod
    def tearDownClass(cls):
        cls.s.close()

    @classmethod
    def arm(cls, player=None):
        import pickle
        from golfsim import career as CA
        t = pickle.loads(cls.blob)
        vals = {}
        orig = Season.event_value

        def value(self, g, ed, week, rng, vc, cost=None, gw=None, base=None):
            v = orig(self, g, ed, week, rng, vc, cost, gw, base)
            vals.setdefault(g.id, []).append((ed.event_id, v))
            return v
        Season.event_value = value
        try:
            t.year = cls.Y
            t.prepare_week(cls.Y, cls.W)
            if player is not None:
                gid, eid = player
                c = CA.Career(gid, cls.Y, cls.W, {'rule': 'test'})
                c.plans[(cls.Y, CA.block_start(cls.W))] = {
                    'weeks': {cls.W: {'kind': 'event', 'event_id': eid, 'fallback': {'kind': 'rest'}}},
                    'policy': {'qualifying': 'enter', 'selected': 'accept'}, 'made': [cls.Y, cls.W]}
                t.career = c
            t.play_prepared_week(cls.Y, cls.W, [e for e in t.cal.editions(cls.Y) if e.week == cls.W])
        finally:
            Season.event_value = orig
        return t, vals

    @staticmethod
    def world_digest(t):
        import hashlib
        h = hashlib.sha256()
        for g in sorted(t.world.golfers, key=lambda g: g.id):
            h.update(repr((g.id, g.status, g.tour, round(g.overall, 6), round(g.cash, 4), round(g.backing, 4),
                           tuple(sorted(g.familiarity.items())))).encode())
        for eid in sorted(t.results):
            h.update(repr((eid, t.results[eid].finish)).encode())
        return h.hexdigest()

    def test_same_choice_same_world_and_same_values(self):
        self.assertGreaterEqual(len(self.pairs), 2)
        ai = self.world_digest(self.ai)
        for gid, eid in self.pairs:
            with self.subTest(golfer=gid, event=eid):
                t, vals = self.arm((gid, eid))
                self.assertEqual(t.career.golfer_id, gid)
                self.assertEqual(vals[gid], self.ai_vals[gid])            # the same appeal, term included
                self.assertEqual(vals, self.ai_vals)                      # and everyone else's
                ed = next(e for e in t.cal.editions(self.Y) if e.event_id == eid)
                self.assertNotEqual(CF.points(t, t.g[gid], ed), 0.0)     # the term is really there
                self.assertEqual(self.world_digest(t), ai)

    def test_a_different_choice_shows(self):
        gid, eid = self.pairs[0]
        other = next(e for e, _ in sorted(self.ai_vals[gid], key=lambda x: -x[1]) if e != eid)
        t, _ = self.arm((gid, other))
        self.assertNotEqual(self.world_digest(t), self.world_digest(self.ai))


if __name__ == '__main__':
    unittest.main()
