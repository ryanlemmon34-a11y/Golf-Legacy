"""The long-run diagnostics count what they claim: exit reasons by episode, comebacks apart, cohorts by
arrival, returns home in date order, no seeded late bloomers, milestone excerpts.

Run from the project folder:  python -m unittest discover -s tests -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import long_run_report as R                                           # noqa: E402
import long_world as LW                                               # noqa: E402


def row(status='pro', lifestyle='full_time', tier=4, wins=None, wr=None):
    r = dict.fromkeys(LW.ROW, 0)
    r.update(status=status, lifestyle=lifestyle, tier=tier, wins_by_tier=wins or {}, wr=wr, net=0, cash=0,
             next_tier=tier, events=10)
    return r


def world():
    """Golfers over 2027-2036: 1 seeded professional who stays; 2 an arrival who leaves young (part-time
    pro), comes back and is still playing; 3 an arrival who leaves young for good (became caddie; an
    earlier decision belongs to no episode's end); 4 a seeded late starter on the Premier Tour."""
    years = range(2027, 2037)
    rows = {y: {} for y in years}
    for y in years:
        rows[y][1] = row(tier=1)
        rows[y][4] = row(tier=1 if y >= 2030 else 2)
    for y in (2028, 2029, 2033, 2034, 2035, 2036):
        rows[y][2] = row()
    for y in (2030, 2031, 2032):
        rows[y][2] = row(lifestyle='part_time')
    for y in (2028, 2029, 2030):
        rows[y][3] = row(wins={4: 1} if y == 2029 else {})
    rows[2031][3] = row(status='caddie', lifestyle='retired')
    golfers = {1: dict(name='A', country='USA', born=2000, initial=True, created=2027, history=[]),
               2: dict(name='B', country='USA', born=2010, initial=False, created=2028,
                       history=[(2028, 'Arrived on the scene at 18 (US College Division I)')]),
               3: dict(name='C', country='USA', born=2010, initial=False, created=2028,
                       history=[(2028, 'Turned professional at 18, starting on the X Tour'),
                                (2030, 'Became a caddie')]),
               4: dict(name='D', country='USA', born=1990, initial=True, created=2027, history=[])}
    transitions = {2027: [{'gid': 3, 'kind': 'part-time pro', 'p': 0.1}],          # (not at an episode's end)
                   2029: [{'gid': 2, 'kind': 'part-time pro', 'p': 0.5}],          # decided at a season's end
                   2030: [{'gid': 3, 'kind': 'became caddie', 'p': 0.6}],
                   2032: [{'gid': 2, 'kind': 'comeback', 'age': 23}]}
    return {'rows': rows, 'golfers': golfers, 'transitions': transitions, 'first': 2027, 'years': 10,
            'majors': {'2035:USA_OPEN': 1}, 'number_one': {2035: 1}, 'checks': {}, 'extras': {}, 'perf': {}}


class ReportRuleTests(unittest.TestCase):
    def test_episodes_and_exit_reasons_by_episode(self):
        d = world()
        self.assertEqual(R.episodes(d['rows'], 2), [[2028, 2029], [2033, 2036]])
        dbg = {y: {gid: [50.0, 80.0] for gid in (1, 2, 3, 4)} for y in d['rows']}
        for y in d['rows']:                                           # 1 and 4 are the top 5% too
            dbg[y][1] = dbg[y][4] = [50.0, 60.0]
        text = '\n'.join(R.section_potential(d, dbg))
        self.assertIn('ended young and undeveloped, then came back (comeback episode): 1', text)
        self.assertIn('ended young and undeveloped, not back by the end of the run: 1', text)
        self.assertIn('became caddie 1', text)                         # the decision at that episode's end
        self.assertNotIn('part-time pro 1', text.split('by the recorded decision:')[1].split('\n')[0])

    def test_cohorts_by_arrival(self):
        d = world()
        self.assertEqual(R.arrival(d, 1), 'starting world: professional')
        self.assertEqual(R.arrival(d, 2), 'later: junior (18)')
        self.assertEqual(R.arrival(d, 3), 'later: new professional')
        d['rows'][2027][5] = row(status='amateur', tier=6)
        d['golfers'][5] = dict(name='E', country='USA', born=2009, initial=True, created=2027, history=[])
        self.assertEqual(R.arrival(d, 5), 'starting world: amateur')

    def test_weekly_ranking_reaches_number_one(self):
        class Arch:
            years = [2030]
            def ranking(self, y, w):
                return [3, 1] if w == 20 else [1, 3]
        self.assertEqual(R.weekly_best(Arch())[3], 1)                  # No. 1 for one week counts
        d = world()
        text = '\n'.join(R.section_generations(d, {}, best={3: 1, 1: 2}))
        self.assertIn('weekly world ranking', text)
        self.assertIn('| later: new professional | 1 | 1 | 1 |', text)

    def test_return_home_must_follow_the_move_abroad(self):
        home = {'year': 2030, 'reason': 'returned home (after college)'}
        away = {'year': 2033, 'reason': 'closer to the X Tour events'}
        self.assertFalse(R.returned_after_abroad([home, away]))
        self.assertTrue(R.returned_after_abroad([away, {'year': 2036, 'reason': 'returned home'}]))

    def test_no_seeded_late_bloomer_and_milestone_excerpts(self):
        d = world()
        a = LW.analyse(d, 3)
        text = '\n'.join(LW.interesting(d, a))
        self.assertNotIn('Late bloomer', text)                         # 4 is seeded: their start is unknown
        lines = LW.milestones(d, a, 1)
        self.assertIn('In the starting world', lines[0])
        self.assertTrue(any('Won the USA Open (major No. 1)' in x for x in lines))
        self.assertTrue(any('World No. 1 at a season\'s end' in x for x in lines))
        self.assertIn('In all: 10 full-time professional seasons', lines[-1])

    def test_majors_are_numbered_in_the_order_they_were_played(self):
        """Three majors in one season: weeks 18, 24 and 30 (Tour Masters, Premier Tour Championship,
        Britannia Open), whose names sort the other way round."""
        d = world()
        d['majors'] = {'2035:BRITANNIA_OPEN': 1, '2035:TOUR_MASTERS': 1, '2035:PREMIER_TOUR_CHAMPIONSHIP': 1,
                       '2034:USA_OPEN': 1}
        a = LW.analyse(d, 3)
        won = [x.split(': ', 1)[1] for x in LW.milestones(d, a, 1, limit=99) if 'major No.' in x]
        self.assertEqual(won, ['Won the USA Open (major No. 1)', 'Won the Tour Masters (major No. 2)',
                               'Won the Premier Tour Championship (major No. 3)', 'Won the Britannia Open (major No. 4)'])
        self.assertEqual(sorted(d['majors'], key=LW.major_order),
                         ['2034:USA_OPEN', '2035:TOUR_MASTERS', '2035:PREMIER_TOUR_CHAMPIONSHIP', '2035:BRITANNIA_OPEN'])


if __name__ == '__main__':
    unittest.main()
