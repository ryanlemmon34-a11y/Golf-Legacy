"""The work pathway (rules 2026-11-03; minimum age 18 since rules 2026-11-10, 21 in worlds started before it): a
full-time non-college amateur of the minimum age or over, outside the amateur top 300,
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
        cases = (({'born': 2010}, {}, 'under 18'),                        # 17 in 2027 (rules 2026-11-10)
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


class Age18Tests(unittest.TestCase):
    """Rules 2026-11-10: the minimum age is 18 (it had been 21) and nothing else changes. Boundary cases, each with
    every other condition met, so only the one under test differs. No season is played."""

    def candidate(self, age=18, n=WP.WEEKS, **kw):
        s, g = world(born=2027 - age, **kw)
        if n:
            s.cash_blocked[1] = n
        return s, g

    def took_work(self, s, g, week=13):
        WP.decide(s, 2027, week)
        return g.lifestyle == 'part_time' and bool(s.work_pathway[2027])

    def feed(self, s, g, weeks):
        for i, why in enumerate(weeks):
            WP.count(s, g, 2027, i + 1, why)

    def test_new_worlds_use_18(self):
        s, _ = world()
        self.assertEqual((WP.MIN_AGE, WP.MIN_AGE_BEFORE), (18, 21))
        self.assertEqual(s.work_pathway_min_age, 18)
        self.assertEqual(WP.min_age(s), 18)

    def test_age_18_qualifies_17_does_not(self):
        for age in (18, 19, 20):
            s, g = self.candidate(age)
            self.assertEqual(WP.why_not(s, g, 2027), [], age)
            self.assertTrue(self.took_work(s, g), age)
            self.assertEqual(s.work_pathway[2027][0]['age'], age)
            self.assertEqual(s.work_pathway[2027][0]['weeks_blocked'], WP.WEEKS)
        s, g = self.candidate(17)
        self.assertEqual(WP.why_not(s, g, 2027), ['under 18'])
        self.assertFalse(self.took_work(s, g))
        self.assertEqual(g.lifestyle, 'full_time')
        self.assertEqual(s.cash_blocked[1], WP.WEEKS)                    # the evidence is kept, not spent

    def test_the_top_300_rule_is_unchanged(self):
        for rank, takes in ((1, False), (300, False), (301, True), (None, True)):
            s, g = self.candidate(18)
            if rank is not None:
                s.am_pos[1] = rank
            self.assertEqual(self.took_work(s, g), takes, rank)
            if not takes:
                self.assertEqual(WP.why_not(s, g, 2027), [f'amateur ranking {rank}'])
        self.assertEqual(WP.OUTSIDE_TOP, 300)

    def test_support_and_family_money_exclude(self):
        s, g = self.candidate(18)
        s.am_support[1] = {'band': 'C'}
        self.assertEqual(WP.why_not(s, g, 2027), ['holds amateur support'])
        self.assertFalse(self.took_work(s, g))
        s, g = self.candidate(18, backing=1.0)
        self.assertEqual(WP.why_not(s, g, 2027), ['family money left'])
        self.assertFalse(self.took_work(s, g))

    def test_seven_counted_weeks_are_not_enough_eight_are(self):
        s, g = self.candidate(18, n=0)
        self.feed(s, g, [BLOCK] * 7)
        self.assertFalse(self.took_work(s, g))
        WP.count(s, g, 2027, 8, BLOCK)
        self.assertEqual(s.cash_blocked[1], 8)
        self.assertTrue(self.took_work(s, g))
        self.assertEqual(WP.WEEKS, 8)

    def test_pauses_do_not_count_an_affordable_week_resets(self):
        s, g = self.candidate(18, n=0)
        self.feed(s, g, [BLOCK] * 4 + ['injured', 'no suitable event scheduled',
                                        'not eligible for the events scheduled'] + [BLOCK] * 3)
        self.assertEqual(s.cash_blocked[1], 7)                           # paused, neither counted nor reset
        self.assertFalse(self.took_work(s, g))
        s, g = self.candidate(18, n=0)
        self.feed(s, g, [BLOCK] * 7 + ['played: first choice', BLOCK])
        self.assertEqual(s.cash_blocked[1], 1)                           # an affordable week starts it again
        self.assertFalse(self.took_work(s, g))

    def test_decided_only_at_the_monthly_plan(self):
        s, g = self.candidate(18, n=0)
        self.feed(s, g, [BLOCK] * 11)                                    # counting never moves anyone
        self.assertEqual(g.lifestyle, 'full_time')
        self.assertTrue(self.took_work(s, g, week=13))
        import inspect
        import re
        from golfsim import season as SE
        src = inspect.getsource(SE)
        self.assertEqual(src.count('WP.decide('), 1)                     # only from the monthly plan ...
        self.assertIn('WP.decide(self, year, week0)', inspect.getsource(SE.Season.plan_block))
        self.assertEqual(src.count('.plan_block('), 1)                   # ... made every 4 weeks (1, 5, 9 ... 49)
        self.assertTrue(re.search(r'if self\.development and \(week - 1\) % 4 == 0:\n\s+self\.plan_block\(year, week\)',
                                  src))

    def test_college_and_part_time_golfers_are_not_tracked(self):
        for kw in ({'tour': 'CO_EAST'}, {'lifestyle': 'part_time'}):
            s, g = self.candidate(18, n=0, **kw)
            self.feed(s, g, [BLOCK] * 9)
            self.assertNotIn(1, s.cash_blocked, kw)
            s.cash_blocked[1] = 9                                        # even with a count, never moved
            WP.decide(s, 2027, 13)
            self.assertFalse(s.work_pathway[2027], kw)
            self.assertEqual(g.tour, kw.get('tour', 'AM_X'))

    def test_no_grant_and_no_start_guaranteed(self):
        s, g = self.candidate(18, cash=-812.4)
        before_g, before_s = dict(vars(g)), set(vars(s))
        self.assertTrue(self.took_work(s, g))
        changed = {k for k in vars(g) if vars(g)[k] != before_g.get(k)}
        self.assertEqual(changed, {'lifestyle'})                         # cash, family money, status, tour as they were
        self.assertEqual((g.cash, g.backing, g.status), (-812.4, 0.0, 'amateur'))
        self.assertEqual(set(vars(s)), before_s)                         # no new grant, entry or reservation
        self.assertFalse(s.am_support)
        self.assertEqual(s.amateur_work_from, {1: (2027, 13)})

    def test_older_saves_keep_21(self):
        import pickle
        from golfsim.population import generate_world
        from golfsim.season import Season
        new = Season(generate_world(seed=17, scale=0.02), seed=17, development=True, workers=1)
        self.addCleanup(new.close)
        self.assertEqual(new.work_pathway_min_age, 18)
        state = new.__getstate__()
        state.pop('work_pathway_min_age')                                # saved under rules 2026-11-03 to -09
        old = Season.__new__(Season)
        old.__setstate__(pickle.loads(pickle.dumps(state)))
        self.assertEqual(old.work_pathway_min_age, 21)
        self.assertTrue(old.work_pathway_on)
        again = Season.__new__(Season)                                   # a 2026-11-10 save keeps 18
        again.__setstate__(pickle.loads(pickle.dumps(new.__getstate__())))
        self.assertEqual(again.work_pathway_min_age, 18)
        for s, takes in ((old, False), (again, True)):
            g = next(x for x in sorted(s.world.golfers, key=lambda x: x.id) if WP.tracked(x))
            g.born, g.backing = 2027 - 19, 0.0
            s.am_pos.pop(g.id, None)
            s.am_support.pop(g.id, None)
            s.cash_blocked[g.id] = WP.WEEKS
            self.assertEqual(WP.why_not(s, g, 2027), [] if takes else ['under 21'])
            WP.decide(s, 2027, 5)
            self.assertEqual(g.lifestyle == 'part_time', takes)
            self.assertEqual(len(s.work_pathway[2027]), int(takes))

    def test_rules_version(self):
        from golfsim import rules as R
        self.assertEqual(R.RULES_VERSION, '2026-11-10')
        dates = [v for v, _ in R.VERSIONS]
        self.assertEqual(dates, sorted(dates))
        self.assertEqual(len(dates), len(set(dates)))
        self.assertEqual(dates[-2:], ['2026-11-09', '2026-11-10'])
        text = dict(R.VERSIONS)['2026-11-10']
        self.assertIn('minimum age is 18', text)
        self.assertIn('Nothing else in the pathway changes', text)
        self.assertIn('keep the minimum age of 21', text)
        self.assertEqual(R.RULES['work-pathway'][2], '2026-11-10')
        self.assertIn('aged 18 or over', R.RULES['work-pathway'][1])


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
