"""Caddie offers hold the caddie for the player (docs/career/CAREERTEST2_FIXES.md, section 1b): a caddie whose offer
goes to the controlled golfer makes no further offer and is not hired by anyone else until the player answers.

On the career fixture world (seed 11, scale 0.05); each test works on its own copy in a temporary folder, removed
afterwards.

Run from the project folder:  python -m unittest tests.test_caddie_reservation -v
"""
from __future__ import annotations

import random
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))
from test_careertest2_fixes import Copy, act, started                 # noqa: E402
from golfsim import staff as ST                                        # noqa: E402

_HIRED = []


def hired_caddie():
    """A free caddie the AI market hires on 1 January 2028 in this world (found once, on its own copy)."""
    if not _HIRED:
        with Copy() as s:
            started(s)
            st = s.season.staff
            free = {k.id for k in st.caddies.values() if k.status == 'active' and k.id not in st._bags()}
            s.advance_career('next', op_key='a')
            _HIRED.append(min(free & st._bags()))
    return _HIRED[0]


def offer(s, kid, when=(2028, 1)):
    se = s.season
    g = se.g[se.career.golfer_id]
    d = se.career.staff_offer(se, 'caddie', se.staff.caddies[kid], g, 'test offer', when)
    s._commit()
    return d


def accept(s, d, key='acc'):
    with mock.patch.object(ST, 'caddie_budget', return_value=1e9):     # (affordability is not under test here)
        return act(s, {'type': 'decide', 'decision': d['id'], 'answer': 'accept'}, key)


class CaddieReservation(unittest.TestCase):
    def test_without_the_hold_the_market_takes_the_caddie(self):
        # the defect, reproduced: the offered caddie was hired by another golfer before the player answered
        kid = hired_caddie()
        with Copy() as s:
            g = started(s)
            d = offer(s, kid)
            with mock.patch.object(ST, 'caddie_reservations', return_value=set()):
                s.advance_career('next', op_key='a')
            st = s.season.staff
            self.assertIn(kid, st._bags())
            r = accept(s, d)
            self.assertFalse(r['ok'])
            self.assertIn('they now carry another bag', r['reason'])
            self.assertIsNone(st.caddie(g.id))

    def test_the_offer_holds_the_caddie_through_the_market(self):
        kid = hired_caddie()
        with Copy() as s:
            g = started(s)
            d = offer(s, kid)
            self.assertEqual(ST.caddie_reservations(s.season), {kid})
            s.advance_career('next', op_key='a')                      # 1 January: the whole staff market
            st = s.season.staff
            self.assertNotIn(kid, st._bags())                         # nobody else took them
            r = accept(s, d)
            self.assertTrue(r['ok'], r)
            self.assertIs(st.caddie(g.id), st.caddies[kid])
            self.assertEqual(sum(1 for x in st.caddie_of.values() if x == kid), 1)   # one bag
            self.assertEqual(ST.caddie_reservations(s.season), set())  # consumed by the acceptance
            with self.assertRaises(Exception):
                accept(s, d, 'acc2')                                  # never accepted twice

    def test_an_offer_to_the_player_ends_the_caddies_offers(self):
        with Copy() as s:
            g = started(s)
            se = s.season
            k = next(x for x in sorted(se.staff.caddies.values(), key=lambda x: x.id)
                     if x.status == 'active' and x.id not in se.staff._bags())
            r = ST.caddie_offer(se, k, g, 'test offer', (2028, 1), random.Random(1))
            self.assertEqual(r, 'held')                               # (true: caddie_approaches stops here)
            self.assertEqual(ST.caddie_reservations(se), {k.id})
            self.assertNotIn(k.id, se.staff._bags())                  # nothing assigned until the player answers

    def test_releases(self):
        kid = hired_caddie()
        with Copy() as s:
            g = started(s)
            se, st = s.season, s.season.staff
            d = offer(s, kid)
            act(s, {'type': 'decide', 'decision': d['id'], 'answer': 'decline'}, 'dec')
            self.assertEqual(ST.caddie_reservations(se), set())       # released on decline
            d2 = offer(s, kid, (2028, 2))
            st.caddies[kid].status = 'retired'
            self.assertEqual(ST.caddie_reservations(se), set())       # stopped working: nothing held
            st.caddies[kid].status = 'active'
            st.assign_caddie(se, g, st.caddies[kid], (2028, 2), 'test set-up', 'test set-up')
            self.assertEqual(ST.caddie_reservations(se), set())       # their own caddie: not counted
            self.assertEqual(d2['status'], 'pending')

    def test_a_failed_replacement_keeps_the_current_caddie(self):
        kid = hired_caddie()
        with Copy() as s:
            g = started(s)
            se, st = s.season, s.season.staff
            old = next(k for k in sorted(st.caddies.values(), key=lambda k: k.id)
                       if k.status == 'active' and k.id not in st._bags() and k.id != kid)
            st.assign_caddie(se, g, old, (2028, 1), 'test set-up', 'test set-up')
            d = offer(s, kid)
            st.caddies[kid].status = 'retired'
            r = accept(s, d)
            self.assertFalse(r['ok'])
            self.assertIn('no longer working', r['reason'])
            self.assertIs(st.caddie(g.id), old)                       # nothing ended
            d2 = offer(s, kid, (2028, 2))
            st.caddies[kid].status = 'active'
            r = accept(s, d2, 'acc2')                                  # a successful replacement: one step
            self.assertTrue(r['ok'], r)
            self.assertIs(st.caddie(g.id), st.caddies[kid])
            self.assertNotIn(old.id, st._bags())

    def test_an_old_offer_that_lost_its_caddie_says_so(self):
        kid = hired_caddie()
        with Copy() as s:
            g = started(s)
            se, st = s.season, s.season.staff
            d = offer(s, kid)
            d['payload'].pop('reserved')                              # an offer an earlier build made
            other = next(x for x in sorted(se.world.golfers, key=lambda x: x.id)
                         if x.id != g.id and x.lifestyle != 'retired' and x.id not in st.caddie_of)
            st.assign_caddie(se, other, st.caddies[kid], (2028, 1), 'test set-up', 'test set-up')
            r = accept(s, d)
            self.assertFalse(r['ok'])
            self.assertIn('earlier build', r['reason'])
            self.assertEqual(d['status'], 'withdrawn')

    def test_all_ai_worlds_hold_nothing(self):
        with Copy() as s:
            self.assertIsNone(s.season.career)
            self.assertEqual(ST.caddie_reservations(s.season), set())


if __name__ == '__main__':
    unittest.main()
