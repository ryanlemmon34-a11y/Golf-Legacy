"""College amateurs at home in ordinary open amateur events (rules 2026-11-11).

In an ordinary open amateur event (the regular events of a regional amateur series) a college amateur whose home
region (where they live) is the series' region enters at the members' class, and members and these college players
rotate by their amateur (tier 6) starts this season, not every start. Everything else keeps its order: closed,
national and elite championships, professional and college events, out-of-region golfers, capacity. Worlds saved
before the rule keep the old order.

Small fixtures only (no season is played). Run from the project folder:
    python -m unittest tests.test_college_open_access -v
"""
from __future__ import annotations

import pickle
import random
import sys
import unittest
from collections import Counter, defaultdict
from pathlib import Path
from types import SimpleNamespace as NS
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from golfsim import rules as R                                            # noqa: E402
from golfsim.calendar import Edition, Series, WorldCalendar               # noqa: E402
from golfsim.season import (AMATEUR_OPEN_EXPANSION, OPEN_AMATEUR_REGIONS, ROTATION_RANK_STARTS, Season,  # noqa: E402
                            _dd_counter, _dd_list, ordinary_open_amateur)

YEAR = 2030


def series(sid='AM_NORTH_AMERICA_T1', tour='AM_NORTH_AMERICA', tier=6, category='regular', eligibility='amateur',
           host='USA', city='Atlanta, Georgia', kind='amateur', field=4, week=20):
    return Series(sid, sid, tour, tier, kind, category, 36, field, week, eligibility, host, (city,))


OPEN_NA = series()
OPEN_NA_2 = series('AM_NORTH_AMERICA_T2')
OPEN_EU = series('AM_EUROPE_T1', 'AM_EUROPE', host='Spain', city='Madrid')
CLOSED_NA = series('AM_NORTH_AMERICA_CHAMPIONSHIP', category='circuit_championship', field=60)
NATIONAL = series('NATIONAL_AMATEUR_USA', 'AMATEUR', category='national_amateur', field=120)
ELITE = series('USA_AMATEUR', 'AMATEUR', category='elite_amateur', field=156)
QUALIFIER = series('USA_AMATEUR_QUALIFYING', 'QUALIFYING', tier=7, kind='qualifying', category='qualifier')
COLLEGE_EV = series('CO_US_D1_01', 'CO_US_D1', tier=5, kind='college', eligibility='college', field=84)
PRO_EV = series('CH_AMERICAS_01', 'CH_AMERICAS', tier=2, kind='pro', eligibility='pro', field=144)
MINI_EV = series('MN_US_SUNBELT_01', 'MN_US_SUNBELT', tier=4, kind='pro', eligibility='pro', field=120)


def golfer(gid, tour, status='amateur', country='USA'):
    return NS(id=gid, tour=tour, status=status, country=country, lifestyle='full_time')


class Stub(Season):
    """A Season with only what priority and the regular entries read (no world, no calendar, no play)."""

    def __init__(self, golfers, home=None, new_rules=True, seed=7):
        self._golfers = list(golfers)
        self.g = {g.id: g for g in golfers}
        self.home = home or {}                    # gid -> country of residence (else their nationality)
        self.college_open_access = new_rules
        self.open_am_starts = defaultdict(Counter)
        self.played = defaultdict(_dd_list)
        self.am_pos, self.wr_pos, self.rights = {}, {}, {}
        self.year, self.seed = YEAR, seed
        self.injured, self.plans, self.development = {}, {}, False
        self._caddie_week, self._week_shut, self._week_first = set(), set(), {}
        self.staff = NS(caddie=lambda gid: None)
        self.cal = NS(spec=NS(travel=False))
        self.event_routes = defaultdict(dict)
        self.entry_stats = defaultdict(_dd_counter)
        self.entry_wants, self.entry_misses = defaultdict(Counter), defaultdict(Counter)

    # what the regular entries read about each golfer: everyone eligible, willing and able to pay
    def home_country(self, g):
        return self.home.get(g.id, g.country)

    def active_golfers(self):
        return self._golfers

    def eligible(self, g, s, week):
        return True

    def bar(self, g):
        return 0.0

    def spendable(self, g, year):
        return 1e9

    def golfer_week(self, g, year, week):
        return None

    def base_value(self, g, ed, country):
        return 0.0

    def event_value(self, g, ed, week, rng, country, cost, gw, base):
        return 60.0 if ed.series.series_id.endswith('T1') else 55.0

    def winners_now(self):
        return set()

    def school_starts(self, gid, n):
        """n college-event (tier 5) starts this season: counted in every start, not in amateur starts."""
        self.played[YEAR][gid].extend(range(1, n + 1))

    def open_starts(self, gid, n):
        """n open amateur (tier 6) starts this season, as play records them (both counts)."""
        self.played[YEAR][gid].extend(range(30, 30 + n))
        self.open_am_starts[YEAR][gid] += n


def pair(new_rules=True, home=None, **kw):
    member = golfer(1, 'AM_NORTH_AMERICA')
    college = golfer(2, 'CO_US_D1')
    s = Stub([member, college], home={2: 'USA', **(home or {})}, new_rules=new_rules, **kw)
    return s, member, college


class OrdinaryOpenTests(unittest.TestCase):
    def test_which_events_are_ordinary_open(self):
        self.assertTrue(ordinary_open_amateur(OPEN_NA))
        self.assertTrue(ordinary_open_amateur(OPEN_EU))
        for s in (CLOSED_NA, NATIONAL, ELITE, QUALIFIER, COLLEGE_EV, PRO_EV, MINI_EV,
                  series('AM_NORTH_AMERICA_T9', eligibility='mid_amateur'),
                  series('CP_NORTH_AMERICA_01', 'CP_NORTH_AMERICA', tier=8, kind='club_pro', eligibility='club_pro')):
            self.assertFalse(ordinary_open_amateur(s), s.series_id)

    def test_real_calendars(self):
        """In both calendars the ordinary open events are exactly the regular events of the six regional amateur
        series; the circuit, national and elite championships are not."""
        self.assertEqual(set(OPEN_AMATEUR_REGIONS), {'AM_NORTH_AMERICA', 'AM_EUROPE', 'AM_ASIA', 'AM_OCEANIA',
                                                     'AM_AFRICA', 'AM_LATAM'})
        self.assertEqual(OPEN_AMATEUR_REGIONS['AM_ASIA'], ('Asia', 'Middle East'))
        for v in ('v1', 'v2'):
            cal = WorldCalendar(2027, v)
            ordinary = {x.series_id for x in cal.series if ordinary_open_amateur(x)}
            regular6 = {x.series_id for x in cal.series if x.tier == 6 and x.category == 'regular'}
            self.assertEqual(ordinary, regular6, v)
            self.assertTrue(ordinary)
            others6 = Counter(x.category for x in cal.series if x.tier == 6 and x.series_id not in ordinary)
            self.assertEqual(set(others6), {'circuit_championship', 'national_amateur', 'elite_amateur'}, v)


class ClassAndRotationTests(unittest.TestCase):
    def test_equal_class_in_home_region_open_event(self):
        s, member, college = pair()
        self.assertEqual(s.priority(college, OPEN_NA)[0], 10)
        self.assertEqual(s.priority(member, OPEN_NA)[0], 10)
        old, member, college = pair(new_rules=False)
        self.assertEqual(old.priority(college, OPEN_NA)[0], 12)               # (before: after the members)
        # a college player at an international university living in Europe: at home in Europe's series
        intl = golfer(3, 'CO_INTL', country='Sweden')
        s = Stub([intl], home={3: 'England'})
        self.assertEqual(s.priority(intl, OPEN_EU)[0], 10)

    def test_reciprocal_low_amateur_start_priority(self):
        s, member, college = pair()
        s.open_starts(college.id, 1)
        s.open_starts(member.id, 3)
        self.assertLess(s.priority(college, OPEN_NA), s.priority(member, OPEN_NA))
        s, member, college = pair()
        s.open_starts(college.id, 3)
        s.open_starts(member.id, 1)
        self.assertLess(s.priority(member, OPEN_NA), s.priority(college, OPEN_NA))
        # the ranking head start is kept: a top-ranked member with two more starts still goes first
        s, member, college = pair()
        s.am_pos[member.id] = 1
        s.open_starts(member.id, ROTATION_RANK_STARTS - 1)
        self.assertLess(s.priority(member, OPEN_NA), s.priority(college, OPEN_NA))
        s.open_starts(member.id, 1)                                           # ... and not with one more
        self.assertLess(s.priority(college, OPEN_NA), s.priority(member, OPEN_NA))

    def test_school_starts_leave_the_rotation_unchanged(self):
        s, member, college = pair()
        s.open_starts(college.id, 2)
        s.open_starts(member.id, 3)
        before = s.priority(college, OPEN_NA)
        s.school_starts(college.id, 12)
        self.assertEqual(s.priority(college, OPEN_NA), before)
        self.assertLess(s.priority(college, OPEN_NA), s.priority(member, OPEN_NA))
        old, member, college = pair(new_rules=False)                         # (before: school starts counted)
        old.open_starts(college.id, 2)
        before = old.priority(college, OPEN_NA)
        old.school_starts(college.id, 12)
        self.assertGreater(old.priority(college, OPEN_NA), before)

    def test_other_access_unchanged(self):
        """Same priority keys as before for: closed (circuit championship), national and elite championships,
        qualifiers, college events, professional events, out-of-region college players, and other amateurs."""
        out = golfer(4, 'CO_US_D1', country='Spain')                         # at college in the USA, living
        intl = golfer(5, 'CO_INTL', country='Japan')                          # ... (legacy) in Spain; in Japan
        visitor = golfer(6, 'AM_EUROPE', country='USA')                       # a European series member
        local = golfer(7, 'AM_EUROPE', country='Canada')                      # nationality only (class 13)
        pro = golfer(8, 'MN_US_SUNBELT', status='pro')
        member, college = golfer(1, 'AM_NORTH_AMERICA'), golfer(2, 'CO_US_D1')
        people = [member, college, out, intl, visitor, local, pro]
        home = {2: 'USA', 4: 'Spain', 5: 'Japan', 6: 'Spain', 7: 'Canada', 8: 'USA'}
        new, old = Stub(people, home), Stub(people, home, new_rules=False)
        for s in (new, old):
            for i, g in enumerate(people):
                s.school_starts(g.id, 5 + i)
                s.open_starts(g.id, i % 3)
                s.am_pos[g.id] = 100 * (i + 1)
                s.wr_pos[g.id] = 300 * (i + 1)
        for ev in (CLOSED_NA, NATIONAL, ELITE, QUALIFIER, COLLEGE_EV, PRO_EV, MINI_EV):
            for g in people:
                self.assertEqual(new.priority(g, ev), old.priority(g, ev), (ev.series_id, g.id))
        for g in (out, intl, visitor, local):                                 # out of region in North America
            self.assertEqual(new.priority(g, OPEN_NA), old.priority(g, OPEN_NA), g.id)
            self.assertGreater(new.priority(g, OPEN_NA)[0], 10)
        for g in (college, intl, pro):                                        # out of region in Europe
            self.assertEqual(new.priority(g, OPEN_EU), old.priority(g, OPEN_EU), g.id)
        # home region is where they live: the US college player living in Spain is at home in Europe's series
        self.assertEqual((old.priority(out, OPEN_EU)[0], new.priority(out, OPEN_EU)[0]), (12, 10))
        # only the home-region college player's class moves; members keep theirs (their key counts amateur starts)
        self.assertEqual((new.priority(member, OPEN_NA)[0], new.priority(college, OPEN_NA)[0]), (10, 10))
        self.assertEqual((old.priority(member, OPEN_NA)[0], old.priority(college, OPEN_NA)[0]), (10, 12))


class FieldFillingTests(unittest.TestCase):
    """The regular entries (deferred acceptance) with two ordinary open events in one week."""

    def fill(self, new_rules=True, seed=7):
        people = [golfer(i, 'AM_NORTH_AMERICA') for i in range(1, 11)] + \
                 [golfer(i, 'CO_US_D1') for i in range(11, 21)]
        s = Stub(people, {g.id: 'USA' for g in people}, new_rules=new_rules, seed=seed)
        for g in people:
            s.open_starts(g.id, g.id % 4)
            if g.tour == 'CO_US_D1':
                s.school_starts(g.id, 8)
        eds = [Edition(YEAR, OPEN_NA, 'Atlanta, Georgia'), Edition(YEAR, OPEN_NA_2, 'Atlanta, Georgia')]
        venues = {e.event_id: [NS(city=e.city)] for e in eds}
        fields = {}

        def commit(ed, sites, how):
            self.assertNotIn(ed.event_id, fields)
            fields[ed.event_id] = [list(x) for x in sites]
        with mock.patch('golfsim.finance.event_cost', return_value=0.0):
            s.regular_entries(eds, YEAR, 20, random.Random(seed), venues, defaultdict(set), commit)
        return s, {eid: sites[0] for eid, sites in fields.items()}

    def test_fixed_capacity_no_duplicates_deterministic(self):
        cap = int(OPEN_NA.field * AMATEUR_OPEN_EXPANSION)
        s, fields = self.fill()
        _, old = self.fill(new_rules=False)
        for f in (fields, old):
            self.assertEqual(sorted(len(x) for x in f.values()), [cap, cap])   # full, never over the field
            ids = [gid for x in f.values() for gid in x]
            self.assertEqual(len(ids), len(set(ids)))                         # nobody entered twice
        self.assertEqual(self.fill()[1], fields)                              # same seed: the same fields
        self.assertEqual(self.fill(seed=7)[1], fields)
        # who got in: the fewest amateur starts first, members and college players alike
        placed = {gid for x in fields.values() for gid in x}
        starts = {g.id: s.open_am_starts[YEAR][g.id] for g in s._golfers}
        self.assertLess(max(starts[g] for g in placed), 3)
        self.assertTrue(any(s.g[g].tour == 'CO_US_D1' for g in placed))
        self.assertTrue(any(s.g[g].tour == 'AM_NORTH_AMERICA' for g in placed))
        old_placed = {gid for x in old.values() for gid in x}                 # (before: every member first,
        self.assertEqual(Counter(s.g[g].tour for g in old_placed),            # college players the rest)
                         {'AM_NORTH_AMERICA': 10, 'CO_US_D1': 2 * cap - 10})

    def test_ties_broken_by_the_entry_draw(self):
        people = [golfer(1, 'AM_NORTH_AMERICA'), golfer(2, 'CO_US_D1')]
        s = Stub(people, {2: 'USA'})
        a, b = (s.priority(g, OPEN_NA) for g in people)
        self.assertEqual(a[:2], b[:2])                                        # same class, same rotation
        self.assertNotEqual(a, b)                                             # the seeded draw decides
        self.assertEqual(a[2], s.entry_ticket(people[0], OPEN_NA))
        self.assertEqual(Stub(people, {2: 'USA'}).priority(people[0], OPEN_NA), a)


class SavedWorldTests(unittest.TestCase):
    def test_new_worlds_use_it_older_saves_keep_the_old_order(self):
        from golfsim.population import generate_world
        s = Season(generate_world(seed=17, scale=0.05), seed=17, development=True, workers=1)
        self.assertTrue(s.college_open_access)
        college = next(g for g in s.world.golfers if g.tour == 'CO_US_D1' and g.status == 'amateur'
                       and s.home_region(g) == 'North America')
        cal_ev = next(x for x in s.cal.series if x.tour == 'AM_NORTH_AMERICA' and ordinary_open_amateur(x))
        self.assertEqual(s.priority(college, cal_ev)[0], 10)
        state = s.__getstate__()
        again = Season.__new__(Season)
        again.__setstate__(pickle.loads(pickle.dumps(state)))                 # a new world's save keeps it
        self.assertTrue(again.college_open_access)
        self.assertEqual(again.priority(college, cal_ev), s.priority(college, cal_ev))
        for k in ('college_open_access', 'open_am_starts'):                   # a save from before 2026-11-11
            state.pop(k)
        old = Season.__new__(Season)
        old.__setstate__(pickle.loads(pickle.dumps(state)))
        self.assertFalse(old.college_open_access)
        self.assertEqual(old.priority(college, cal_ev)[0], 12)
        old.played[old.year][college.id] = list(range(1, 7))                  # every start counts, as before
        rank = old.am_pos.get(college.id)
        expected = 6 + ROTATION_RANK_STARTS * (min(1.0, rank / 1500) if rank else 1.0)
        self.assertEqual(old.priority(college, cal_ev)[1], expected)
        s.close()


class RulesTests(unittest.TestCase):
    def test_version(self):
        dates = [v for v, _ in R.VERSIONS]
        self.assertEqual(dates, sorted(dates))
        self.assertEqual(len(dates), len(set(dates)))
        self.assertEqual(R.RULES_VERSION, '2026-11-11')
        self.assertIn('2026-11-11', dates)
        self.assertEqual(R.RULES['open-amateur'][2], '2026-11-11')
        text = dict(R.VERSIONS)['2026-11-11']
        for fact in ('same class', 'amateur (tier 6) starts', 'Unchanged', 'field sizes', 'Worlds started earlier'):
            self.assertIn(fact, text)


if __name__ == '__main__':
    unittest.main()
