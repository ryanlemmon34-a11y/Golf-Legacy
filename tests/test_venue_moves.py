"""Venue moves (rules 2026-11-05, 'venue-moves'): an event that has outgrown its venue moves to a better course in the
same city, decided at a season's end and played two seasons later; a per-world overlay on the shared course plan,
which itself never changes. No season is simulated here: a minimal stand-in carries only what Season.venues and
Season.review_venues read.

Run from the project folder:  python -m unittest tests.test_venue_moves -v
"""
from __future__ import annotations

import pickle
import sys
import unittest
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from golfsim import prestige as PR                                     # noqa: E402
from golfsim import schedule as SCH                                    # noqa: E402
from golfsim.course_library import default_library, event_level        # noqa: E402
from golfsim.season import EventResult, Season, all_moves, migrate_venue_moves, move_in_force   # noqa: E402

LIB = default_library(SCH.DEFAULT)
YEARS = range(2027, 2042)


class Stand(object):
    venues = Season.venues
    review_venues = Season.review_venues

    def __init__(self):
        self.lib, self.cal = LIB, LIB.calendar
        self.venue_moves, self.venue_watch, self.venue_moved = {}, {}, {}
        self.venue_log = defaultdict(list)
        self.event_prestige, self.course_prestige, self.results = {}, {}, {}

    def play(self, year, sid, prestige, venue_prestige):
        """The season's end as review_venues sees it: the edition played where venues() put it."""
        eid = f'{year}:{sid}'
        v = self.venues(year)[eid][0]
        self.results[eid] = EventResult(eid, sid, year, 0, [(v.course_id, v.layout, v.city)], [], prestige)
        self.event_prestige[sid] = prestige
        self.course_prestige[v.course_id] = venue_prestige
        return self.review_venues(year)


def better_course_exists(sid):
    """A single-site, non-major series on one planned course every year, with a physically better course its level
    may use in that city, free that week in every year."""
    s = LIB.calendar.by_id[sid]
    if s.kind in ('major', 'qualifying') or s.sites != 1:
        return False
    plan = [LIB.venues(y).get(f'{y}:{sid}') for y in YEARS]
    if any(not p or len(p) != 1 for p in plan) or len({p[0].course_id for p in plan}) != 1:
        return False
    cur = plan[0][0]
    q = PR.COURSE_QUALITY[(LIB.sites[cur.course_id]['cls'], cur.layout)]
    for cid in LIB.by_city[cur.city]:
        ok = LIB._eligible(cid, event_level(s))
        if cid == cur.course_id or not ok or PR.COURSE_QUALITY[(LIB.sites[cid]['cls'], ok[1])] <= q:
            continue
        if LIB.sites[cid]['cls'] == 'elite' and s.week in LIB.calendar.major_weeks:
            continue
        if all(cid not in {v.course_id for e in LIB.calendar.editions(y) if e.week == s.week
                           for v in LIB.venues(y)[e.event_id]} for y in YEARS):
            return True
    return False


SID = next((s.series_id for s in sorted(LIB.calendar.series, key=lambda s: s.series_id)
            if better_course_exists(s.series_id)), None)


@unittest.skipIf(SID is None, 'no series in the course plan with a free, better course in its city')
class VenueMoves(unittest.TestCase):
    def setUp(self):
        self.planned = {y: LIB.venues(y)[f'{y}:{SID}'][0] for y in YEARS}

    def test_sustained_gap_moves_two_seasons_later_and_never_touches_the_plan(self):
        st = Stand()
        for y in (2027, 2028):
            self.assertEqual(st.play(y, SID, 90.0, 50.0), [])            # one and two season ends: not yet
        moved = st.play(2029, SID, 90.0, 50.0)                            # the third: decided
        self.assertEqual(len(moved), 1)
        m = moved[0]
        self.assertEqual((m['from'], m['decided'], m['replaces']), (2029 + PR.VENUE_LAG, 2029,
                                                                     self.planned[2029].course_id))
        self.assertEqual(m['city'], self.planned[2029].city)                 # same city
        eid = lambda y: f'{y}:{SID}'
        self.assertEqual(st.venues(2030)[eid(2030)][0].course_id, self.planned[2030].course_id)   # the lag
        new = st.venues(2031)[eid(2031)][0]
        self.assertEqual(new.course_id, m['course'])
        q = lambda v: PR.COURSE_QUALITY[(LIB.sites[v.course_id]['cls'], v.layout)]
        self.assertGreater(q(new), q(self.planned[2031]))                # physically better
        self.assertTrue(LIB._eligible(new.course_id, event_level(LIB.calendar.by_id[SID])))   # its level may use it
        self.assertEqual(LIB.venues(2031)[eid(2031)][0], self.planned[2031])   # the shared plan is unchanged
        for y in (2031, 2035):                                           # never two events on a course in a week
            per_week = defaultdict(list)
            for e in LIB.calendar.editions(y):
                for v in st.venues(y)[e.event_id]:
                    per_week[e.week].append(v.course_id)
            for w, cs in per_week.items():
                self.assertEqual(len(cs), len(set(cs)), (y, w))

    def test_tradition_one_move_in_ten_seasons_and_the_count_resets(self):
        st = Stand()
        for y in range(2027, 2030):
            st.play(y, SID, 90.0, 50.0)
        self.assertEqual(st.venue_moved[SID], 2029)
        for y in range(2030, 2039):                                       # still far above: no second move yet
            self.assertEqual(st.play(y, SID, 99.0, 50.0), [])
        other = Stand()
        for y, gap in zip(range(2027, 2032), (10, 10, 1, 10, 10)):        # interrupted: the count starts again
            self.assertEqual(other.play(y, SID, 50.0 + gap, 50.0), [])
        self.assertEqual(len(other.play(2032, SID, 60.0, 50.0)), 1)

    def test_a_booked_course_keeps_the_planned_venue(self):
        st = Stand()
        for y in range(2027, 2030):
            st.play(y, SID, 90.0, 50.0)
        (key, (m,)), = st.venue_moves.items()
        y = 2033
        week = LIB.calendar.by_id[SID].week
        rival = next((e for e in LIB.calendar.editions(y) if e.week == week and e.series.series_id != SID
                      and len(LIB.venues(y)[e.event_id]) == 1), None)
        if rival is None:
            self.skipTest('no other single-site event that week')
        # a second move sends a different event of the same week to the same course
        rival_planned = LIB.venues(y)[rival.event_id][0]
        st.venue_moves[(rival.series.series_id, rival_planned.course_id)] = [dict(
            m, series=rival.series.series_id, **{'from': 2027})]
        st._venue_cache = {}
        vs = st.venues(y)
        got = {vs[rival.event_id][0].course_id, vs[f'{y}:{SID}'][0].course_id}
        # exactly one of them (the first in series-id order) takes it; the other keeps its planned course
        self.assertIn(m['course'], got)
        self.assertTrue(got & {rival_planned.course_id, self.planned[y].course_id})
        self.assertEqual(len(got), 2)

    # ---- repeated moves: an effective-dated history per (series, planned course) (review of ace3b2e) ---------------
    def free_in_city(self):
        """Courses in the event's city free in its week in every year of the plan, other than the planned one:
        [(course id, layout its level may use or None, physical quality or None)]."""
        a = self.planned[2027]
        s = LIB.calendar.by_id[SID]
        out = []
        for cid in sorted(LIB.by_city[a.city]):
            if cid == a.course_id or any(cid in {v.course_id for e in LIB.calendar.editions(y) if e.week == s.week
                                                 for v in LIB.venues(y)[e.event_id]} for y in YEARS):
                continue
            ok = LIB._eligible(cid, event_level(s))
            out.append((cid, ok[1] if ok else None,
                        PR.COURSE_QUALITY[(LIB.sites[cid]['cls'], ok[1])] if ok else None))
        return out

    def move(self, to, layout, decided, effective, replaces):
        return {'series': SID, 'course': to, 'layout': layout, 'city': self.planned[2027].city, 'from': effective,
                'decided': decided, 'planned': self.planned[2027].course_id, 'replaces': replaces,
                'replaces_layout': '', 'event_prestige': 90.0, 'course_prestige_before': 50.0}

    def test_repeated_moves_keep_every_move_by_effective_year(self):
        """A -> B decided 2029 (from 2031), then B -> C decided 2039 (from 2041)."""
        free = self.free_in_city()
        if len(free) < 2:
            self.skipTest('fewer than two free courses in the city')
        (b, lb, _), (c, lc, _) = free[0], free[1]
        a = self.planned[2027].course_id
        st = Stand()
        st.venue_moves[(SID, a)] = [self.move(b, lb or 'Championship', 2029, 2031, a)]
        st.venue_moves[(SID, a)].append(self.move(c, lc or 'Championship', 2039, 2041, b))
        got = lambda y: st.venues(y)[f'{y}:{SID}'][0].course_id
        self.assertEqual([got(y) for y in (2029, 2030)], [a, a])                   # not before its effective year
        self.assertEqual([got(y) for y in (2031, 2035, 2040)], [b, b, b])          # the first move keeps its years
        self.assertEqual([got(y) for y in (2041,)], [c])
        for y in (2031, 2040, 2041):                                                # no double-booking
            per_week = defaultdict(list)
            for e in LIB.calendar.editions(y):
                for v in st.venues(y)[e.event_id]:
                    per_week[e.week].append(v.course_id)
            self.assertTrue(all(len(cs) == len(set(cs)) for cs in per_week.values()), y)
        # saves keep the history (a Season pickles venue_moves as it is; SeasonSave checks a real Season)
        again = Stand()
        again.venue_moves = pickle.loads(pickle.dumps(st.venue_moves))
        self.assertEqual([again.venues(y)[f'{y}:{SID}'][0].course_id for y in (2030, 2031, 2040, 2041)], [a, b, b, c])
        self.assertEqual(len(all_moves(again.venue_moves)), 2)

    def test_a_second_decision_is_added_not_overwritten(self):
        free = [f for f in self.free_in_city() if f[1] is not None]
        if len(free) < 2:
            self.skipTest('fewer than two free courses its level may use in the city')
        free.sort(key=lambda f: (f[2], f[0]))
        b, lb, qb = free[0]                                            # first to the weakest free course ...
        if not any(q > qb for _, _, q in free):
            self.skipTest('no physically better course than the first move\'s')
        a = self.planned[2027].course_id
        st = Stand()
        st.venue_moves[(SID, a)] = [self.move(b, lb, 2029, 2031, a)]
        st.venue_moved[SID] = 2029
        for y in range(2031, 2040):                                    # ... then, ten seasons on, a better one
            moved = st.play(y, SID, 99.0, 50.0)
            self.assertEqual(st.results[f'{y}:{SID}'].sites[0][0], b)  # the venue actually played
            self.assertEqual(len(moved), 1 if y == 2039 else 0, y)     # (tradition: not before 2039)
        hist = st.venue_moves[(SID, a)]
        self.assertEqual([(m['decided'], m['from']) for m in hist], [(2029, 2031), (2039, 2041)])
        c = hist[1]['course']
        self.assertEqual(hist[1]['replaces'], b)
        got = lambda y: st.venues(y)[f'{y}:{SID}'][0].course_id
        self.assertEqual([got(y) for y in (2030, 2031, 2040, 2041, 2045)], [a, b, b, c, c])

    def test_saves_from_ace3b2e_migrate(self):
        m = self.move('x', 'Championship', 2029, 2031, 'a')
        self.assertEqual(migrate_venue_moves({(SID, 'a'): m}), {(SID, 'a'): [m]})
        later = self.move('y', 'Championship', 2039, 2041, 'x')
        self.assertEqual(migrate_venue_moves({(SID, 'a'): [later, m]}), {(SID, 'a'): [m, later]})
        self.assertEqual(move_in_force([m, later], 2040), m)
        self.assertEqual(move_in_force([m, later], 2041), later)
        self.assertIsNone(move_in_force([m, later], 2030))

    def test_majors_and_qualifying_never_move(self):
        st = Stand()
        for s in LIB.calendar.series:
            if s.kind in ('major', 'qualifying'):
                for y in (2027, 2028, 2029):
                    vs = LIB.venues(y).get(f'{y}:{s.series_id}')
                    if vs and len(vs) == 1:
                        st.play(y, s.series_id, 99.0, 0.0)
        self.assertEqual(st.venue_moves, {})


@unittest.skipIf(SID is None, 'no series in the course plan with a free, better course in its city')
class SeasonSave(unittest.TestCase):
    """A real Season (built, never simulated): a save keeps the whole move history and resolves the same venues."""

    def test_save_and_resume_keep_the_history(self):
        from golfsim.population import generate_world
        s = Season(generate_world(seed=41, scale=0.05), seed=41, workers=1)
        a = LIB.venues(2027)[f'2027:{SID}'][0]
        free = [cid for cid in sorted(LIB.by_city[a.city]) if cid != a.course_id
                and all(cid not in {v.course_id for e in LIB.calendar.editions(y) if e.week == LIB.calendar.by_id[SID].week
                                    for v in LIB.venues(y)[e.event_id]} for y in YEARS)]
        if len(free) < 2:
            self.skipTest('fewer than two free courses in the city')
        mk = lambda to, d, f, rep: {'series': SID, 'course': to, 'layout': 'Championship', 'city': a.city, 'from': f,
                                    'decided': d, 'planned': a.course_id, 'replaces': rep}
        s.venue_moves[(SID, a.course_id)] = [mk(free[0], 2029, 2031, a.course_id), mk(free[1], 2039, 2041, free[0])]
        s._venue_cache = {}
        got = lambda season: [season.venues(y)[f'{y}:{SID}'][0].course_id for y in (2030, 2031, 2040, 2041)]
        before = got(s)
        self.assertEqual(before, [a.course_id, free[0], free[0], free[1]])
        self.assertNotIn('_venue_cache', s.__getstate__())                       # (derived: not saved)
        again = pickle.loads(pickle.dumps(s))
        self.assertEqual(got(again), before)
        self.assertEqual(again.venue_moves, s.venue_moves)
        self.assertEqual(len(again.prestige_view()['venue_moves']), 2)
        s.close()


if __name__ == '__main__':
    unittest.main()
