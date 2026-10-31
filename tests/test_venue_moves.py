"""Venue moves (rules 2026-11-05, 'venue-moves'): an event that has outgrown its venue moves to a better course in the
same city, decided at a season's end and played two seasons later; a per-world overlay on the shared course plan,
which itself never changes. No season is simulated here: a minimal stand-in carries only what Season.venues and
Season.review_venues read.

Run from the project folder:  python -m unittest tests.test_venue_moves -v
"""
from __future__ import annotations

import sys
import unittest
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from golfsim import prestige as PR                                     # noqa: E402
from golfsim import schedule as SCH                                    # noqa: E402
from golfsim.course_library import default_library, event_level        # noqa: E402
from golfsim.season import EventResult, Season                         # noqa: E402

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
        (key, m), = st.venue_moves.items()
        y = 2033
        week = LIB.calendar.by_id[SID].week
        rival = next((e for e in LIB.calendar.editions(y) if e.week == week and e.series.series_id != SID
                      and len(LIB.venues(y)[e.event_id]) == 1), None)
        if rival is None:
            self.skipTest('no other single-site event that week')
        # a second move sends a different event of the same week to the same course
        rival_planned = LIB.venues(y)[rival.event_id][0]
        st.venue_moves[(rival.series.series_id, rival_planned.course_id)] = dict(
            m, series=rival.series.series_id, **{'from': 2027})
        st._venue_cache = {}
        vs = st.venues(y)
        got = {vs[rival.event_id][0].course_id, vs[f'{y}:{SID}'][0].course_id}
        # exactly one of them (the first in series-id order) takes it; the other keeps its planned course
        self.assertIn(m['course'], got)
        self.assertTrue(got & {rival_planned.course_id, self.planned[y].course_id})
        self.assertEqual(len(got), 2)

    def test_majors_and_qualifying_never_move(self):
        st = Stand()
        for s in LIB.calendar.series:
            if s.kind in ('major', 'qualifying'):
                for y in (2027, 2028, 2029):
                    vs = LIB.venues(y).get(f'{y}:{s.series_id}')
                    if vs and len(vs) == 1:
                        st.play(y, s.series_id, 99.0, 0.0)
        self.assertEqual(st.venue_moves, {})


if __name__ == '__main__':
    unittest.main()
