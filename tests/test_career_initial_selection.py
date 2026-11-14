"""Initial player selection (docs/career/INITIAL_SELECTION.md): before a career, the player chooses one of ten genuine
juniors of the season's class -- the same seeded sample and public facts as the annual newcomer choice.

On the career fixture world (seed 11, scale 0.05) at its second season's 1 January.

Run from the project folder:  python -m unittest tests.test_career_initial_selection -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))
import career_fixture as F                                             # noqa: E402
from golfsim import career as CA                                       # noqa: E402
from golfsim.session import Session, StaleCursor                       # noqa: E402

HIDDEN = ('potential', 'ceilings', 'peak_age', 'aging_rate')


def fresh():
    return Session.open(F.copy_of(F.first_boundary()))


def start(s, golfer, key='start', **kw):
    return s.career_action({'schema': CA.SCHEMA, 'type': 'new_career', 'golfer': golfer}, op_key=key, **kw)


class InitialSelection(unittest.TestCase):
    def test_the_offer_is_ten_real_juniors_stable_and_public(self):
        s = fresh()
        v = CA.start_view(s.season, s.cursor)
        self.assertEqual(v['year'], 2028)
        ids = [c['id'] for c in v['candidates']]
        self.assertEqual(len(ids), CA.CANDIDATES)
        cls = {g for g, r in s.season.creations[2028].items() if r['path'] == 'junior'}
        self.assertTrue(set(ids) <= cls)
        self.assertEqual(v['class_size'], len(cls))
        self.assertEqual(ids, CA.candidates(s.season, 2028))          # the annual choice's sample
        self.assertEqual(v['options'], [str(i) for i in ids])
        self.assertEqual([c['facts'] for c in v['choices']], v['candidates'])
        for c in v['candidates']:
            for h in HIDDEN:
                self.assertNotIn(h, c)
        n, before = len(s.season.world.golfers), F.digest(s)
        again = CA.start_view(s.season, s.cursor)                      # read only, and stable
        self.assertEqual(again, v)
        self.assertEqual((len(s.season.world.golfers), F.digest(s)), (n, before))
        d = s.dir
        s.close()
        s = Session.open(d)                                           # and across a reload
        self.assertEqual(CA.start_view(s.season, s.cursor), v)
        s.close()

    def test_choosing_one(self):
        s = fresh()
        v = CA.start_view(s.season, s.cursor)
        pick = v['candidates'][4]['id']
        r = start(s, str(pick))
        c = s.season.career
        self.assertEqual((r['golfer'], c.golfer_id, c.status), (pick, pick, 'active'))
        self.assertEqual(c.entry['candidates'], CA.CANDIDATES)
        self.assertEqual(c.stints, [{'golfer_id': pick, 'from': [2028, 1], 'to': None, 'how': c.entry}])
        self.assertIsNone(CA.start_view(s.season, s.cursor))           # a career exists now
        s.close()

    def test_invalid_stale_and_replayed(self):
        s = fresh()
        v = CA.start_view(s.season, s.cursor)
        cls = sorted(g for g, r in s.season.creations[2028].items() if r['path'] == 'junior')
        outsider = next(g for g in cls if g not in [c['id'] for c in v['candidates']])
        for bad in (str(outsider), v['candidates'][0]['id'], 'x', None):  # not offered / not a string id
            with self.assertRaises(CA.CareerError):
                start(s, bad, key=f'bad-{bad}')
        self.assertIsNone(s.season.career)
        old = dict(s.cursor)
        r1 = start(s, v['options'][2], key='k', expected=old)
        r2 = start(s, v['options'][2], key='k', expected=old)          # replayed: the first result
        self.assertEqual(r1, r2)
        with self.assertRaises(CA.CareerError):                       # a second career: refused
            start(s, v['options'][3], key='k2')
        s.advance_career('next', op_key='a')
        with self.assertRaises(StaleCursor):
            start(s, v['options'][3], key='k3', expected=old)
        s.close()

    def test_the_world_is_the_same_whoever_is_chosen_until_play(self):
        # choosing draws nothing from the world: two different picks leave identical worlds before anything runs
        a, b = fresh(), fresh()
        v = CA.start_view(a.season, a.cursor)
        start(a, v['options'][0])
        start(b, v['options'][1])
        self.assertEqual(F.digest(a), F.digest(b))
        a.close()
        b.close()

    def test_the_original_command_still_draws_from_the_class(self):
        s = fresh()
        r = s.career_action({'schema': CA.SCHEMA, 'type': 'new_career'}, op_key='legacy')
        self.assertIn('seeded uniform draw', s.season.career.entry['rule'])
        self.assertIn(r['golfer'], s.season.creations[2028])
        s.close()

    def test_no_offer_outside_a_season_start(self):
        s = fresh()
        s.advance(1)
        self.assertIsNone(CA.start_view(s.season, s.cursor))
        s.close()


if __name__ == '__main__':
    unittest.main()
