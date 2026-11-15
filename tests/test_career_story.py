"""Optional goals (persisted, read by no rule) and the career timeline (records only).

On the career fixture world (seed 11, scale 0.05); each test on its own temporary copy.

Run from the project folder:  python -m unittest tests.test_career_story -v
"""
from __future__ import annotations

import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))
import career_fixture as F                                             # noqa: E402
from test_careertest2_fixes import Copy, act, started                 # noqa: E402
from golfsim import career as CA                                       # noqa: E402
from golfsim.session import Session                                    # noqa: E402


def goal(s, g, key):
    return act(s, {'type': 'set_goal', 'goal': g, 'version': s.season.career.version}, key)


class Goals(unittest.TestCase):
    def test_set_validate_drop_and_replay(self):
        with Copy() as s:
            started(s)
            r = goal(s, {'kind': 'play_in', 'series_id': 'USA_AMATEUR', 'by_year': 2029}, 'g1')
            self.assertEqual(goal(s, {'kind': 'play_in', 'series_id': 'USA_AMATEUR', 'by_year': 2029}, 'g1'), r)
            v = CA.view(s.season, s.cursor)['goals']
            self.assertEqual((len(v), v[0]['status'], v[0]['label'][:9]), (1, 'active', 'USA Amate'))
            for bad, key in (({'kind': 'fame'}, 'b1'), ({'kind': 'win', 'series_id': 'NOPE', 'by_year': 2028}, 'b2'),
                             ({'kind': 'world_rank', 'top': 0, 'by_year': 2028}, 'b3'),
                             ({'kind': 'win', 'series_id': 'USA_AMATEUR', 'by_year': 2027}, 'b4')):
                with self.assertRaises(CA.CareerError):
                    goal(s, bad, key)
            with self.assertRaises(CA.StaleCareer):
                act(s, {'type': 'set_goal', 'goal': {'kind': 'world_rank', 'top': 10, 'by_year': 2030},
                        'version': s.season.career.version - 1}, 'stale')
            for i in range(4):
                goal(s, {'kind': 'world_rank', 'top': 100 + i, 'by_year': 2030}, f'x{i}')
            with self.assertRaises(CA.CareerError):                      # at most five at a time
                goal(s, {'kind': 'amateur_rank', 'top': 5, 'by_year': 2030}, 'x9')
            act(s, {'type': 'drop_goal', 'goal_id': r['goal']}, 'd1')
            v = {x['id']: x for x in CA.view(s.season, s.cursor)['goals']}
            self.assertEqual(v[r['goal']]['status'], 'dropped')
            d = s.dir
            s._commit()
            s.close()
            s2 = Session.open(d)                                       # kept across a reload
            self.assertEqual({x['id']: x for x in CA.view(s2.season, s2.cursor)['goals']}, v)
            s2.close()

    def test_progress_from_records_and_no_effect_on_the_world(self):
        with Copy() as a, Copy() as b:
            ga = started(a)
            started(b)
            r = goal(a, {'kind': 'win', 'series_id': 'NATIONAL_AMATEUR_ARGENTINA', 'by_year': 2028}, 'g')
            goal(a, {'kind': 'amateur_rank', 'top': 1000, 'by_year': 2028}, 'r')
            a.advance_career('next', op_key='a')
            b.advance_career('next', op_key='a')
            self.assertEqual(F.digest(a), F.digest(b))                 # goals change nothing in the world
            v = {x['id']: x for x in CA.view(a.season, a.cursor)['goals']}
            self.assertEqual(v[r['goal']]['status'], 'active')
            a.season.ctx.results[('NATIONAL_AMATEUR_ARGENTINA', 2028)] = {0: [(ga.id, 1)]}   # (test set-up)
            v = {x['id']: x for x in CA.view(a.season, a.cursor)['goals']}
            self.assertEqual(v[r['goal']]['status'], 'achieved')
            state = random.getstate()
            CA.view(a.season, a.cursor)
            self.assertEqual(random.getstate(), state)


class Timeline(unittest.TestCase):
    def test_from_records(self):
        with Copy() as s:
            g = started(s)
            s.advance_career('next', op_key='a')
            for d in s.season.career.pending(CA.OFFER_KINDS):
                act(s, {'type': 'decide', 'decision': d['id'], 'answer': 'decline'}, f'o{d["id"]}')
            t = CA.view(s.season, s.cursor)['timeline']
            self.assertEqual(t[0]['kind'], 'control')
            self.assertEqual(t[0]['date'], [2028, 1])
            self.assertIn(g.name, t[0]['text'])
            self.assertEqual(t, sorted(t, key=lambda x: (tuple(x['date']), x['kind'], x['text'])))
            for x in t:
                self.assertIn(x['kind'], ('control', 'decision', 'trophy', 'result', 'staff'))


if __name__ == '__main__':
    unittest.main()
