"""Career year end (docs/career/YEAR_END.md): the season review and annual intent, the controlled golfer's winter
choices, the staged winter, the newcomer choice, control stints, paid work weeks, the format-1 upgrade.

On the career fixture world (seed 11, scale 0.05), a career played (resting) to its first season review; built once
per process (about 1.5 minutes) and copied for each test.

Run from the project folder:  python -m unittest tests.test_career_year_end -v
"""
from __future__ import annotations

import shutil
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))
import career_fixture as F                                             # noqa: E402
from golfsim import career as CA                                       # noqa: E402
from golfsim import residence as RES                                   # noqa: E402
from golfsim.finance import WORK_WAGE                                  # noqa: E402
from golfsim.session import Session, StaleCursor                       # noqa: E402

REST = {'kind': 'rest'}
POLICY = {'selected': 'accept', 'qualifying': 'skip'}
HIDDEN = ('potential', 'ceilings', 'peak_age', 'aging_rate')
_CACHE = {}


def act(s, body, key, **kw):
    return s.career_action(dict({'schema': CA.SCHEMA}, **body), op_key=key, **kw)


def plan(s, block, weeks=None):
    y, w0 = block
    body = {'type': 'plan_block', 'block': [y, w0], 'version': s.season.career.version,
            'weeks': {str(w): (weeks or {}).get(w, REST) for w in CA.open_weeks(s.cursor, w0)}, 'policy': POLICY}
    return act(s, body, f'plan-{y}-{w0}-{s.season.career.version}')


def play_to_review(s, tag):
    """Advance, planning rest and declining offers, until the year end asks something. Returns its decisions."""
    for n in range(80):
        s.advance_career('next', op_key=f'{tag}{n}')
        pend = s.season.career.pending()
        ye = [d for d in pend if d['kind'] in CA.YEAR_END_KINDS]
        if ye:
            return ye
        for d in pend:
            if d['kind'] == 'plan':
                plan(s, d['payload']['block'])
            elif d['kind'] in CA.OFFER_KINDS:
                act(s, {'type': 'decide', 'decision': d['id'], 'answer': 'decline'}, f'{tag}d{d["id"]}')
            elif d['kind'] in ('unsupported', 'replan'):
                raise AssertionError(d['text'])
    raise AssertionError('no season review within 80 advances')


def review_fixture():
    if 'review' not in _CACHE:
        s = Session.open(F.copy_of(F.first_boundary()))
        act(s, {'type': 'new_career'}, 'new')
        play_to_review(s, 'a')
        s.close()
        _CACHE['review'] = s.dir
    return _CACHE['review']


def at_review():
    return Session.open(F.copy_of(review_fixture()))


def decide(s, d, answer, key=None, **kw):
    return act(s, {'type': 'decide', 'decision': d['id'], 'answer': answer,
                   'version': s.season.career.version}, key or f'ans-{d["id"]}-{answer}', **kw)


def one(s, kind):
    ds = s.season.career.pending((kind,))
    assert len(ds) == 1, (kind, s.season.career.pending())
    return ds[0]


def reopen(s):
    d = s.dir
    s.close()
    return Session.open(d)


def staffed(s):
    """The controlled golfer given a coach and a caddie (fixture set-up: the rested fixture golfer has neither)."""
    st, g = s.season.staff, s.season.g[s.season.career.golfer_id]
    co = next(x for x in sorted(st.coaches.values(), key=lambda x: x.id) if x.id not in st.coach_of.values())
    ca = next(x for x in sorted(st.caddies.values(), key=lambda x: x.id) if x.id not in st.caddie_of.values())
    st.assign_coach(s.season, g, co, 'fee', (2028, 52), 'golfer', 'test set-up')
    st.assign_caddie(s.season, g, ca, (2028, 52), 'test set-up')
    s._commit()
    return co, ca


class Review(unittest.TestCase):
    def test_the_review_comes_before_any_winter_part(self):
        s = at_review()
        self.assertEqual(s.cursor, {'year': 2028, 'week': 52, 'phase': 'end'})
        self.assertEqual(s.season.winter_parts_done(2028), 0)
        self.assertNotIn(2029, s.season.juniors_added)
        d = one(s, 'season_review')
        self.assertEqual(d['options'], ['keep', 'switch', 'end_career'])
        self.assertEqual([x['key'] for x in d['payload']['choices']], d['options'])
        out = s.advance_career('next', op_key='again')                 # nothing runs while it is open
        self.assertEqual(out['weeks'], [])
        self.assertEqual(s.season.winter_parts_done(2028), 0)
        ye = CA.view(s.season, s.cursor)['year_end']
        self.assertEqual(ye['stage'], 'season_review')
        self.assertEqual(ye['review']['recorded_weeks'], 52)
        self.assertEqual(sum(ye['review']['activity'].values()), 52)
        for k in ('wins', 'top10', 'best_finish', 'income', 'world_rank', 'amateur_rank', 'overall_start'):
            self.assertIn(k, ye['review'])                             # always present (None when not known)
        s.close()

    def test_end_career_at_the_review(self):
        s = at_review()
        gid = s.season.career.golfer_id
        decide(s, one(s, 'season_review'), 'end_career')
        c = s.season.career
        self.assertEqual((c.status, tuple(c.ended)), ('ended', (2028, 52)))
        self.assertEqual(c.stints[-1]['to'], [2028, 52])
        s.advance(1)                                                    # the whole winter, all AI, then week 1
        self.assertEqual(s.cursor['year'], 2029)
        self.assertFalse(c.controls(gid))
        s.close()

    def test_stale_and_duplicate(self):
        s = at_review()
        d = one(s, 'season_review')
        v = s.season.career.version
        with self.assertRaises(CA.StaleCareer):
            act(s, {'type': 'decide', 'decision': d['id'], 'answer': 'keep', 'version': v - 1}, 'stale')
        r1 = act(s, {'type': 'decide', 'decision': d['id'], 'answer': 'keep', 'version': v}, 'k')
        r2 = act(s, {'type': 'decide', 'decision': d['id'], 'answer': 'keep', 'version': v}, 'k')    # replayed
        self.assertEqual(r1, r2)
        self.assertEqual(s.season.career.winter[2028], {'intent': 'keep'})
        with self.assertRaises(CA.CareerError):                         # resolved: never answered twice
            act(s, {'type': 'decide', 'decision': d['id'], 'answer': 'switch'}, 'k2')
        old = dict(s.cursor)
        s.advance_career('next', op_key='n')
        with self.assertRaises(StaleCursor):
            act(s, {'type': 'decide', 'decision': d['id'], 'answer': 'keep'}, 'k3', expected=old)
        s.close()


class Keep(unittest.TestCase):
    def run_keep(self, reload_each):
        s = at_review()
        g = s.season.g[s.season.career.golfer_id]
        g.tour = 'AM_NORTH_AMERICA'                                     # a series amateur: a real career choice
        co, ca = staffed(s)
        steps = [lambda s: decide(s, one(s, 'season_review'), 'keep'),
                 lambda s: s.advance_career('next', op_key='w0'),
                 lambda s: decide(s, one(s, 'winter_career'), 'turn_pro'),
                 lambda s: decide(s, one(s, 'winter_staff'), 'let_go_caddie'),
                 lambda s: s.advance_career('next', op_key='w1')]
        for step in steps:
            step(s)
            if reload_each:
                s = reopen(s)
        return s, g.id, co, ca

    def test_kept_golfers_winter_is_the_players(self):
        s, gid, co, ca = self.run_keep(reload_each=True)
        c, g = s.season.career, s.season.g[gid]
        self.assertEqual(s.cursor, {'year': 2029, 'week': 1, 'phase': 'start'})
        self.assertEqual((c.status, c.golfer_id), ('active', gid))
        self.assertEqual((g.status, g.lifestyle), ('pro', 'full_time'))     # turn_pro, by the engine's own rule
        self.assertEqual(g.tour, 'MN_US_SUNBELT')
        st = s.season.staff
        self.assertIsNone(st.caddie(gid))                                # let go
        self.assertEqual(c.winter[2028]['career'], 'turn_pro')
        self.assertEqual(c.winter[2028]['staff'], {'coach': 'keep', 'caddie': 'let_go'})
        self.assertIn(2029, s.season.juniors_added)                      # the rest of the winter ran, once
        self.assertEqual(s.season.winter_parts_done(2028), 3)
        s.close()

    def test_reloads_between_stages_change_nothing(self):
        a, *_ = self.run_keep(reload_each=False)
        b, *_ = self.run_keep(reload_each=True)
        self.assertEqual(F.digest(a), F.digest(b))
        self.assertEqual(a.season.career.winter, b.season.career.winter)
        a.close()
        b.close()

    def test_winter_choices_close_with_their_stage(self):
        s = at_review()
        s.season.g[s.season.career.golfer_id].tour = 'AM_NORTH_AMERICA'
        s._commit()
        decide(s, one(s, 'season_review'), 'keep')
        s.advance_career('next', op_key='w0')
        d = one(s, 'winter_career')
        with self.assertRaises(CA.CareerError):
            decide(s, d, 'not_an_option')
        out = s.advance_career('next', op_key='w1')                      # the open choice holds the winter
        self.assertEqual(out['weeks'], [])
        self.assertEqual(s.season.winter_parts_done(2028), 1)
        s.close()

    def test_a_retirement_leads_to_the_newcomer_choice(self):
        s = at_review()
        gid = s.season.career.golfer_id
        s.season.g[gid].tour = 'AM_NORTH_AMERICA'
        s._commit()
        decide(s, one(s, 'season_review'), 'keep')
        s.advance_career('next', op_key='w0')
        decide(s, one(s, 'winter_career'), 'retire')
        out = s.advance_career('next', op_key='w1')
        c = s.season.career
        self.assertEqual(s.season.g[gid].lifestyle, 'retired')
        self.assertEqual(c.status, 'choosing')
        self.assertEqual(c.stints[-1]['to'], [2028, 53])
        self.assertEqual(out['stop']['kind'], 'decision')
        self.assertEqual(one(s, 'choose_newcomer')['payload']['year'], 2029)
        s.close()


class Switch(unittest.TestCase):
    def switched(self):
        s = at_review()
        gid = s.season.career.golfer_id
        decide(s, one(s, 'season_review'), 'switch')
        return s, gid

    def test_the_former_golfer_is_the_ais_for_the_whole_winter(self):
        s, gid = self.switched()
        c = s.season.career
        self.assertEqual(c.status, 'choosing')
        self.assertFalse(c.controls(gid))
        self.assertEqual(c.stints[0]['to'], [2028, 52])
        called = []
        real = __import__('golfsim.careers', fromlist=['x']).apply_player_winter
        with mock.patch('golfsim.careers.apply_player_winter', side_effect=lambda *a: called.append(a) or real(*a)):
            out = s.advance_career('next', op_key='w')
        self.assertEqual(called, [])                                    # no player winter for anyone
        self.assertEqual(c.winter[2028], {'intent': 'switch'})
        self.assertEqual(s.cursor, {'year': 2029, 'week': 1, 'phase': 'start'})
        self.assertEqual(out['stop']['kind'], 'decision')
        s.close()

    def test_candidates_are_real_stable_and_public(self):
        s, gid = self.switched()
        s.advance_career('next', op_key='w')
        d = one(s, 'choose_newcomer')
        ids = d['payload']['candidates']
        self.assertEqual(len(ids), CA.CANDIDATES)
        cls = {g for g, r in s.season.creations[2029].items() if r['path'] == 'junior'}
        self.assertTrue(set(ids) <= cls)                                # genuine members of the class
        self.assertEqual(ids, CA.candidates(s.season, 2029))
        n_golfers = len(s.season.world.golfers)
        s = reopen(s)
        s.advance_career('next', op_key='w2')                           # asked again: the same decision
        self.assertEqual(one(s, 'choose_newcomer')['payload']['candidates'], ids)
        self.assertEqual(len(s.season.world.golfers), n_golfers)        # none created
        for x in CA.view(s.season, s.cursor)['year_end']['candidates']:
            for h in HIDDEN:
                self.assertNotIn(h, x)
        with self.assertRaises(CA.CareerError):                         # nothing else while choosing
            plan(s, (2029, 1))
        outsider = next(g for g in sorted(cls) if g not in ids)
        with self.assertRaises(CA.CareerError):
            decide(s, one(s, 'choose_newcomer'), str(outsider))
        s.close()

    def test_choosing_starts_a_new_stint(self):
        s, gid = self.switched()
        s.advance_career('next', op_key='w')
        d = one(s, 'choose_newcomer')
        pick = d['payload']['candidates'][3]
        r = decide(s, d, str(pick))
        c = s.season.career
        self.assertEqual((r['golfer'], c.golfer_id, c.status), (pick, pick, 'active'))
        self.assertEqual([x['golfer_id'] for x in c.stints], [gid, pick])
        self.assertEqual(c.stints[1]['from'], [2029, 1])
        self.assertEqual((c.controlled_at(2028, 30), c.controlled_at(2029, 1)), (gid, pick))
        self.assertEqual(CA.view(s.season, s.cursor)['stints'][1]['golfer_id'], pick)
        s.close()

    def test_end_career_instead_of_a_newcomer(self):
        s, gid = self.switched()
        s.advance_career('next', op_key='w')
        decide(s, one(s, 'choose_newcomer'), 'end_career')
        c = s.season.career
        self.assertEqual((c.status, tuple(c.ended)), ('ended', (2029, 1)))
        self.assertEqual(len(s.advance(1)), 1)
        s.close()


class Residence(unittest.TestCase):
    def test_the_player_decides_a_move_the_rule_offers(self):
        # the fixture's golfer has no move case; take control of one who has (a test set-up only)
        for answer in ('stay', 'move'):
            s = at_review()
            c = s.season.career
            gid = 146
            g = s.season.g[gid]
            c.golfer_id = c.stints[0]['golfer_id'] = gid
            s._commit()
            decide(s, one(s, 'season_review'), 'keep')
            s.advance_career('next', op_key='w0')
            for d in s.season.career.pending(CA.YEAR_END_KINDS):
                decide(s, d, d['options'][0])
            s.advance_career('next', op_key='w1')
            d = one(s, 'winter_residence')
            opt = d['payload']
            self.assertEqual(d['options'], ['stay', f'move:{opt["country"]}'])
            cash0 = g.cash
            decide(s, d, 'stay' if answer == 'stay' else d['options'][1])
            s.advance_career('next', op_key='w2')
            home = s.season.places.home[gid][0]
            if answer == 'stay':
                self.assertEqual(c.winter[2028]['residence'], 'stay')
                self.assertEqual(home, opt['from'])
            else:
                self.assertEqual(home, opt['country'])
                self.assertLess(g.cash, cash0)                            # paid from their own money
            s.close()


class PaidWork(unittest.TestCase):
    def test_a_professional_short_of_money_plans_paid_work(self):
        s = at_review()
        gid = s.season.career.golfer_id
        s.season.g[gid].tour = 'AM_NORTH_AMERICA'
        s._commit()
        decide(s, one(s, 'season_review'), 'keep')
        s.advance_career('next', op_key='w0')
        decide(s, one(s, 'winter_career'), 'turn_pro')
        s.advance_career('next', op_key='w1')
        s.advance_career('next', op_key='w2')                            # 1 January: backers, sponsors
        g = s.season.g[gid]
        for d in s.season.career.pending(CA.OFFER_KINDS):
            decide(s, d, 'decline')
        ok = s.season.needs_paid_work(g, 2029)
        if not ok:                                                      # (make them short of money: test set-up)
            g.cash = g.backing = g.backer_funds = 0.0
            s.season.ledgers.get(2028, {}).pop(gid, None)
            s._commit()
        wk = CA.planner(s.season, s.cursor, 2029, 1)['weeks'][0]['work']
        self.assertEqual(wk, {'available': True, 'wage': WORK_WAGE, 'why': ''})
        plan(s, (2029, 1), {w: {'kind': 'work'} for w in (1, 2, 3, 4)})
        led0 = s.season.ledgers.get(2029, {}).get(gid)
        w0 = led0.work if led0 is not None else 0.0
        out = s.advance_career('period', op_key='p')
        self.assertEqual(len(out['weeks']), 4)
        self.assertEqual(s.season.activity_counts[2029][gid]['work'], 4)
        self.assertAlmostEqual(s.season.ledgers[2029][gid].work - w0, 4 * WORK_WAGE)
        self.assertFalse([d for d in s.season.career.pending() if d['kind'] == 'unsupported'])
        s.close()

    def test_an_amateur_cannot_plan_paid_work(self):
        s = at_review()
        decide(s, one(s, 'season_review'), 'keep')
        s.advance_career('next', op_key='w')
        s.advance_career('next', op_key='w2')
        for d in s.season.career.pending(CA.OFFER_KINDS):
            decide(s, d, 'decline')
        self.assertFalse(CA.planner(s.season, s.cursor, 2029, 1)['weeks'][0]['work']['available'])
        with self.assertRaisesRegex(CA.CareerError, 'paid work'):
            plan(s, (2029, 1), {1: {'kind': 'work'}})
        s.close()


class MultiYear(unittest.TestCase):
    def test_two_seasons_kept_then_a_switch_and_the_former_golfer_carries_on(self):
        s = at_review()
        first = s.season.career.golfer_id
        decide(s, one(s, 'season_review'), 'keep')
        for n in range(6):                                              # the 2028 winter: whatever it asks, no change
            s.advance_career('next', op_key=f'k{n}')
            if s.cursor['year'] == 2029:
                break
            for d in s.season.career.pending(CA.YEAR_END_KINDS):
                decide(s, d, d['options'][0])
        s = reopen(s)
        play_to_review(s, 'b')                                         # the whole 2029 season, played as the player
        self.assertEqual(s.cursor, {'year': 2029, 'week': 52, 'phase': 'end'})
        ye = CA.view(s.season, s.cursor)['year_end']
        self.assertEqual((ye['year'], ye['review']['golfer_id'], ye['review']['recorded_weeks']), (2029, first, 52))
        decide(s, one(s, 'season_review'), 'switch')
        s = reopen(s)
        s.advance_career('next', op_key='w')
        d = one(s, 'choose_newcomer')
        pick = d['payload']['candidates'][0]
        decide(s, d, str(pick))
        s = reopen(s)
        for n in range(4):
            for d in s.season.career.pending():
                if d['kind'] == 'plan':
                    plan(s, d['payload']['block'])
                elif d['kind'] in CA.OFFER_KINDS:
                    decide(s, d, 'decline')
            s.advance_career('next', op_key=f'c{n}')
        c = s.season.career
        self.assertEqual([x['golfer_id'] for x in c.stints], [first, pick])
        self.assertEqual((c.stints[0]['from'], c.stints[0]['to']), ([2028, 1], [2029, 52]))
        self.assertGreaterEqual(s.cursor['week'], 2)
        g = s.season.g[first]
        if g.lifestyle != 'retired':                                    # the AI plans and plays the former golfer
            self.assertTrue(s.season.plans.get(first))
            self.assertGreater(sum(s.season.activity_counts[2030][first].values()), 0)
        recs = [r for (y, w), r in c.weekly_recaps.items() if y == 2030]
        self.assertTrue(recs and all(r['golfer_id'] == pick for r in recs))
        s.close()


class Format(unittest.TestCase):
    def test_a_format_1_record_is_upgraded_with_its_history(self):
        s = at_review()
        c = s.season.career
        c.format = 1
        del c.stints, c.winter
        s._commit()
        s = reopen(s)
        c = s.season.career
        self.assertEqual(c.format, CA.FORMAT)
        self.assertEqual(c.stints, [{'golfer_id': c.golfer_id, 'from': list(c.started), 'to': None,
                                     'how': dict(c.entry)}])
        self.assertEqual(c.winter, {})
        s.close()

    def test_an_ended_format_1_career_stays_ended(self):
        s = at_review()
        c = s.season.career
        decide(s, one(s, 'season_review'), 'end_career')
        c.format = 1
        del c.stints, c.winter
        s._commit()
        s = reopen(s)
        c = s.season.career
        self.assertEqual(c.status, 'ended')
        self.assertEqual(c.stints[0]['to'], list(c.ended))
        s.advance(1)
        self.assertEqual(c.status, 'ended')                             # nothing resurrected
        s.close()


if __name__ == '__main__':
    unittest.main()
