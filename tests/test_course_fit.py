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


if __name__ == '__main__':
    unittest.main()
