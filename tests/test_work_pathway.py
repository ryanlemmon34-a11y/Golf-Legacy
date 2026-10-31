"""The work pathway (rules 2026-11-03): a full-time non-college amateur aged 21+, outside the amateur top 300,
without amateur support and with no family money left, who could not afford any eligible event for 8 counted
weeks, takes a job at the next monthly plan and keeps playing as a part-time amateur.

Counting: only a genuine affordability block adds a week; an injury, a week with no suitable event and a week
with nothing they were eligible for pause the count (ordinary calendar gaps never erase it); any week they could
pay for an event resets it. The transition is recorded with its date and reason; the way back (turning
professional) is unchanged.

Run from the project folder:  python -m unittest tests.test_work_pathway -v
"""
from __future__ import annotations

import sys
import unittest
from collections import Counter, defaultdict
from pathlib import Path
from types import SimpleNamespace as NS
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from golfsim import work_pathway as WP                                   # noqa: E402

BLOCK = WP.COUNTS


class Golfer(NS):
    def age(self, year):
        return year - self.born


def world(**kw):
    g = Golfer(id=1, status='amateur', lifestyle='full_time', tour='AM_X', born=2000, backing=0.0, cash=-500.0)
    for k, v in kw.items():
        setattr(g, k, v)
    s = NS(g={1: g}, am_pos={}, am_support={}, work_pathway_on=True, history=defaultdict(list), amateur_work_from={})
    s.log = lambda gid, y, w, t: s.history[gid].append((y, w, t))
    WP.init(s)
    return s, g


class Counting(unittest.TestCase):
    def feed(self, s, g, weeks):
        for i, why in enumerate(weeks):
            WP.count(s, g, 2027, i + 1, why)
        return s.cash_blocked.get(g.id, 0)

    def test_only_affordability_blocks_count(self):
        s, g = world()
        self.assertEqual(self.feed(s, g, [BLOCK] * 3), 3)
        self.assertEqual(s.cash_blocked_max[2027][1], 3)

    def test_injury_and_calendar_gaps_pause(self):
        s, g = world()
        weeks = [BLOCK, 'no suitable event scheduled', BLOCK, 'injured', 'injured', BLOCK,
                 'not eligible for the events scheduled', BLOCK]
        self.assertEqual(self.feed(s, g, weeks), 4)                      # never reset, never counted

    def test_an_affordable_week_resets(self):
        for why in ('played: first choice', 'played: alternative', 'declined the events on offer', 'chose to train',
                    'chose to rest', 'shut out: every acceptable field full'):
            s, g = world()
            self.assertEqual(self.feed(s, g, [BLOCK] * 5 + [why]), 0, why)
            self.assertEqual(s.cash_blocked_max[2027][1], 5)              # the longest run stays recorded

    def test_counted_across_the_year_end(self):
        s, g = world()
        for w in (50, 51, 52):
            WP.count(s, g, 2027, w, BLOCK)
        WP.count(s, g, 2028, 1, 'no suitable event scheduled')            # the winter gap: a pause
        WP.count(s, g, 2028, 2, BLOCK)
        self.assertEqual(s.cash_blocked[1], 4)

    def test_only_full_time_non_college_amateurs_are_tracked(self):
        for kw in ({'status': 'pro'}, {'lifestyle': 'part_time'}, {'tour': 'CO_EAST'}):
            s, g = world(**kw)
            self.assertEqual(self.feed(s, g, [BLOCK] * 9), 0, kw)


class Deciding(unittest.TestCase):
    def blocked(self, n=WP.WEEKS, **kw):
        s, g = world(**kw)
        s.cash_blocked[1] = n
        return s, g

    def test_a_candidate_takes_work_with_the_facts_recorded(self):
        s, g = self.blocked(cash=-812.4)
        s.am_pos[1] = 301
        WP.decide(s, 2027, 13)
        self.assertEqual((g.status, g.lifestyle, g.tour), ('amateur', 'part_time', 'AM_X'))
        self.assertEqual(s.work_pathway[2027], [{'gid': 1, 'year': 2027, 'week': 13, 'age': 27, 'weeks_blocked': 8,
                                                 'am_rank': 301, 'cash': -812, 'reason': WP.REASON}])
        self.assertEqual(s.history[1][0][:2], (2027, 13))
        self.assertEqual(s.amateur_work_from[1], (2027, 13))           # the work start, for a later return
        self.assertNotIn(1, s.cash_blocked)

    def test_who_is_left_out(self):
        cases = (({'born': 2007}, {}, 'under 21'),                        # 20 in 2027
                 ({}, {'rank': 300}, 'amateur ranking 300'),
                 ({}, {'support': True}, 'holds amateur support'),
                 ({'backing': 1.0}, {}, 'family money left'))
        for kw, extra, why in cases:
            s, g = self.blocked(**kw)
            if 'rank' in extra:
                s.am_pos[1] = extra['rank']
            if extra.get('support'):
                s.am_support[1] = {'band': 'C'}
            self.assertIn(why, WP.why_not(s, g, 2027))
            WP.decide(s, 2027, 13)
            self.assertEqual(g.lifestyle, 'full_time', why)
            self.assertFalse(s.work_pathway[2027])

    def test_seven_weeks_is_not_enough(self):
        s, g = self.blocked(WP.WEEKS - 1)
        WP.decide(s, 2027, 13)
        self.assertEqual(g.lifestyle, 'full_time')

    def test_off_in_saves_from_before_the_pathway(self):
        s, g = self.blocked()
        s.work_pathway_on = False
        WP.decide(s, 2027, 13)
        self.assertEqual(g.lifestyle, 'full_time')


class InASeason(unittest.TestCase):
    """A small world: an adult amateur deep in debt is counted week by week from the access ledger and takes work
    at the first monthly plan after 8 counted weeks; the job's salary starts that week. (Amateur support is off and
    the ranking threshold lowered so that one golfer of a small world qualifies; the rule is otherwise as played.)"""

    def test_the_transition(self):
        from golfsim.population import generate_world
        from golfsim.season import Season
        s = Season(generate_world(seed=93, scale=0.05), seed=93, development=True, workers=1, calendar='v2',
                   amateur_support=False)
        try:
            s.start_year(2027)
            g = next(x for x in sorted(s.world.golfers, key=lambda x: x.id) if WP.tracked(x) and x.age(2027) >= 21)
            g.backing, g.cash = 0.0, -50000.0
            with mock.patch.object(WP, 'OUTSIDE_TOP', 0):
                for w in range(1, 18):
                    s.advance_week(2027, w)
            rec = s.work_pathway[2027]
            self.assertEqual(len(rec), 1)
            r = rec[0]
            self.assertEqual((r['gid'], r['reason']), (g.id, WP.REASON))
            self.assertEqual((r['week'] - 1) % 4, 0)                      # at a monthly plan
            self.assertGreaterEqual(r['weeks_blocked'], WP.WEEKS)
            acc = s.week_access[2027][g.id]
            self.assertGreaterEqual(acc[BLOCK], WP.WEEKS)                 # the evidence is the ledger's own
            self.assertEqual(g.lifestyle, 'part_time')
            self.assertGreater(s.ledgers[2027][g.id].salary, 0)           # the job pays from that week
            self.assertIn('took a job', s.history[g.id][-1][2])
            self.assertFalse(s.am_support)                                # (no support in this world)
            for x in s.world.golfers:                                     # nobody else moved by the pathway
                if x.id != g.id:
                    self.assertNotIn(x.id, [t['gid'] for t in rec])
        finally:
            s.close()


if __name__ == '__main__':
    unittest.main()
