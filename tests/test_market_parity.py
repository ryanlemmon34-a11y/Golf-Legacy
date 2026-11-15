"""The 1 January staff market treats the player like any golfer (career.market_question, staff.market_answer):
an approach to the controlled golfer stops the market -- on a throwaway copy -- before it runs; the player's answer is
applied at the same point of the real market with the same draw an AI golfer's answer takes. No place is held, no
offers pile up, nothing is allocated before the answer.

Paired worlds: the same state and the same choice, once answered by the player and once by an AI golfer (its answer
forced to the same choice), must give identical worlds.

On the career fixture world (seed 11, scale 0.05); each world on its own temporary copy.

Run from the project folder:  python -m unittest tests.test_market_parity -v
"""
from __future__ import annotations

import random
import shutil
import sys
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))
import career_fixture as F                                             # noqa: E402
from test_careertest2_fixes import act                                 # noqa: E402
from golfsim import career as CA                                       # noqa: E402
from golfsim import staff as ST                                        # noqa: E402
from golfsim.session import Session                                    # noqa: E402

SEED_PICK = 'test:market'


def world():
    return Session.open(F.copy_of(F.first_boundary()))


def drop(s):
    d = s.dir
    s.close()
    shutil.rmtree(Path(d).parent, ignore_errors=True)


def the_golfer(s):
    """The golfer the career will take (the original new_career draw), without starting it."""
    se = s.season
    cls = sorted(gid for gid, r in se.creations.get(2028, {}).items() if r.get('path') == 'junior')
    return random.Random(f'{se.seed}:career:newcomer:2028').choice(cls)


def coaches_for(s, gid, n=2):
    """`n` active coaches with room for a share student and better known than the golfer's coach (test choice)."""
    st = s.season.staff
    out = []
    for c in sorted(st.coaches.values(), key=lambda c: (-c.reputation, c.id)):
        k = sum(1 for x in st.coach_of.values() if x == c.id)
        sh = sum(1 for g2, x in st.coach_of.items() if x == c.id and st.deal.get(g2) == 'share')
        if c.status == 'active' and k + 1 <= c.capacity and sh + 1 <= c.capacity // 3 and st.coach(gid) is not c:
            out.append(c)
        if len(out) == n:
            return out
    raise AssertionError('no coach')


def injected(cids, gid, kind='coach'):
    """Make the market's established-player step open with approaches to `gid` (test set-up, identical in both
    worlds): the coaches (or caddies) in `cids`, in order, each through the market's own approach function."""
    real_est = ST.established_approaches
    real_cad = ST.caddie_approaches

    def est(season, year, offered, students, majors=None):
        if kind == 'coach':
            g = season.g[gid]
            for cid in cids:
                c = season.staff.coaches[cid]
                offered.add(('coach', cid, gid))
                ST.approach(season, c, g, 'test approach', (year, 1), random.Random(f'{SEED_PICK}:{cid}'),
                            students, {}, 'share')
        return real_est(season, year, offered, students, majors)

    def cad(season, year, offered):
        if kind == 'caddie':
            g = season.g[gid]
            for kid in cids:
                offered.add(('caddie', kid, gid))
                if ST.caddie_offer(season, season.staff.caddies[kid], g, 'test approach', (year, 1),
                                   random.Random(f'{SEED_PICK}:{kid}')):
                    break
        return real_cad(season, year, offered)
    return [mock.patch.object(ST, 'established_approaches', est), mock.patch.object(ST, 'caddie_approaches', cad)]


def forced_ai(gid, answers):
    """The AI golfer `gid` answers approaches as `answers` ({(kind, staff id): 'accept'|'decline'}) says."""
    real_g, real_c = ST.golfer_answers, ST.golfer_takes_caddie

    def ga(season, st, g, c, year, arrangement='share'):
        p, yes, no = real_g(season, st, g, c, year, arrangement)
        a = answers.get(('coach', c.id)) if g.id == gid else None
        return (p, yes, no) if a is None else ((1.0 if a == 'accept' else 0.0), 'accepted by the player',
                                               'declined by the player')

    def gc(season, st, g, k, year):
        p, yes, no = real_c(season, st, g, k, year)
        a = answers.get(('caddie', k.id)) if g.id == gid else None
        return (p, yes, no) if a is None else ((1.0 if a == 'accept' else 0.0), 'accepted by the player',
                                               'declined by the player')
    return [mock.patch.object(ST, 'golfer_answers', ga), mock.patch.object(ST, 'golfer_takes_caddie', gc)]


def staffed(s, gid):
    """Give golfer `gid` a coach and a caddie in this world (so neither world's own staff search looks at them)."""
    se, st = s.season, s.season.staff
    g = se.g[gid]
    c0 = next(c for c in sorted(st.coaches.values(), key=lambda c: (c.reputation, c.id))
              if c.status == 'active' and sum(1 for x in st.coach_of.values() if x == c.id) < c.capacity)
    k0 = next(k for k in sorted(st.caddies.values(), key=lambda k: (k.reputation, k.id))
              if k.status == 'active' and k.id not in st._bags())
    st.assign_coach(se, g, c0, 'fee', (2027, 52), 'golfer', 'test set-up')
    st.assign_caddie(se, g, k0, (2027, 52), 'test set-up', 'test set-up')
    s._commit()


def run_player(answers, kind='coach', ids=None, reload_each=False):
    """The career world: the golfer is the player's; each market question is answered from `answers`."""
    s = world()
    gid = the_golfer(s)
    staffed(s, gid)
    ids = ids or [c.id for c in coaches_for(s, gid)]
    asked = []
    with ExitStack() as stack:
        for p in injected(ids, gid, kind):
            stack.enter_context(p)
        act(s, {'type': 'new_career'}, 'new')
        assert s.season.career.golfer_id == gid
        for n in range(6):
            out = s.advance_career('next', op_key=f'a{n}')
            if s.cursor['phase'] != 'start':
                break
            d = next(d for d in s.season.career.pending() if d['payload'].get('market'))
            key = (d['kind'].split('_')[0], d['payload']['staff'])
            asked.append(key)
            self_check = s.season.staff.assignments if False else None   # noqa: F841
            act(s, {'type': 'decide', 'decision': d['id'], 'answer': answers[key]}, f'm{n}')
            if reload_each:
                d0 = s.dir
                s.close()
                s = Session.open(d0)
    return s, gid, ids, asked


def run_ai(answers, gid, ids, kind='coach'):
    """The same world without a career: the golfer is an AI golfer whose answers are forced to `answers`."""
    s = world()
    staffed(s, gid)
    with ExitStack() as stack:
        for p in injected(ids, gid, kind) + forced_ai(gid, answers):
            stack.enter_context(p)
        s.season.start_year(2028)                                     # 1 January only
        s.state['cursor'] = {'year': 2028, 'week': 1, 'phase': 'week'}  # (where the career world's cursor stands)
    return s


class MarketParity(unittest.TestCase):
    def check(self, choice, kind='coach'):
        s0 = world()
        gid = the_golfer(s0)
        staffed(s0, gid)
        if kind == 'coach':
            ids = [c.id for c in coaches_for(s0, gid)]
        else:
            st = s0.season.staff
            ids = [k.id for k in sorted(st.caddies.values(), key=lambda k: (k.weekly_fee, k.id))
                   if k.status == 'active' and k.id not in st._bags()][:2]
        drop(s0)
        answers = {(kind, i): a for i, a in zip(ids, choice)}
        with ExitStack() as stack:
            if kind == 'caddie':                                      # (both worlds: a budget that affords them,
                stack.enter_context(mock.patch.object(ST, 'caddie_budget', return_value=1e9))   # the same rule)
            a, _, _, asked = run_player(answers, kind, ids)
            b = run_ai(answers, gid, ids, kind)
        expect = [(kind, ids[0])] if (kind == 'caddie' and choice[0] == 'accept') else [(kind, i) for i in ids]
        self.assertEqual(asked, expect)                               # one at a time, in market order
        self.assertEqual(F.digest(a), F.digest(b))                     # the same world as an AI golfer's answer
        self.assertEqual(a.season.staff.coach_of, b.season.staff.coach_of)
        self.assertEqual(a.season.staff.caddie_of, b.season.staff.caddie_of)
        self.assertEqual(a.season.staff.deal, b.season.staff.deal)
        return a, b, gid, ids

    def test_accept_then_decline(self):
        a, b, gid, ids = self.check(['accept', 'decline'])
        self.assertEqual(a.season.staff.coach(gid).id, ids[0])
        st = a.season.staff
        c = st.coaches[ids[0]]
        self.assertLessEqual(sum(1 for x in st.coach_of.values() if x == c.id), c.capacity)
        self.assertLessEqual(sum(1 for g2, x in st.coach_of.items() if x == c.id and st.deal.get(g2) == 'share'),
                             c.capacity // 3)
        drop(a), drop(b)

    def test_decline_both(self):
        a, b, gid, ids = self.check(['decline', 'decline'])
        self.assertNotIn(getattr(a.season.staff.coach(gid), 'id', None), ids)
        drop(a), drop(b)

    def test_decline_then_accept(self):
        a, b, gid, ids = self.check(['decline', 'accept'])
        self.assertEqual(a.season.staff.coach(gid).id, ids[1])
        drop(a), drop(b)

    def test_caddie_accept(self):
        a, b, gid, ids = self.check(['accept', 'accept'], kind='caddie')
        self.assertEqual(a.season.staff.caddie(gid).id, ids[0])
        drop(a), drop(b)

    def test_caddie_decline(self):
        a, b, gid, ids = self.check(['decline', 'decline'], kind='caddie')
        drop(a), drop(b)


class MarketQuestions(unittest.TestCase):
    def test_the_world_waits_and_nothing_is_allocated_before_the_answer(self):
        s = world()
        gid = the_golfer(s)
        staffed(s, gid)
        ids = [c.id for c in coaches_for(s, gid)]
        with ExitStack() as stack:
            for p in injected(ids, gid):
                stack.enter_context(p)
            act(s, {'type': 'new_career'}, 'new')
            before = F.digest(s)
            out = s.advance_career('next', op_key='a')
            self.assertEqual(s.cursor, {'year': 2028, 'week': 1, 'phase': 'start'})   # 1 January has not run
            self.assertEqual(F.digest(s), before)
            self.assertNotIn(2028, s.season.assignments)
            d = s.season.career.pending()[0]
            self.assertEqual((d['kind'], d['payload']['staff'], d['deadline']), ('coach_offer', ids[0], [2028, 1]))
            self.assertIn('answer now', d['text'])
            self.assertEqual(out['stop']['ids'], [d['id']])
            self.assertEqual(len(s.season.career.pending()), 1)       # one offer at a time, never several held
            out2 = s.advance_career('next', op_key='b')               # asked again: the same question, nothing run
            self.assertEqual(out2['stop']['ids'], [d['id']])
            act(s, {'type': 'decide', 'decision': d['id'], 'answer': 'accept'}, 'x')
            with self.assertRaises(CA.CareerError):                   # one answer
                act(s, {'type': 'decide', 'decision': d['id'], 'answer': 'decline'}, 'y')
        drop(s)

    def test_reloads_between_answers_change_nothing(self):
        answers = None
        s0 = world()
        gid = the_golfer(s0)
        staffed(s0, gid)
        ids = [c.id for c in coaches_for(s0, gid)]
        drop(s0)
        answers = {('coach', ids[0]): 'decline', ('coach', ids[1]): 'accept'}
        a, *_ = run_player(answers, ids=ids)
        b, *_ = run_player(answers, ids=ids, reload_each=True)
        self.assertEqual(F.digest(a), F.digest(b))
        self.assertEqual(a.season.career.market_answers, b.season.career.market_answers)
        drop(a), drop(b)

    def test_no_approach_no_stop_and_reads_change_nothing(self):
        s = world()
        act(s, {'type': 'new_career'}, 'new')
        out = s.advance_career('next', op_key='a')
        self.assertNotEqual(s.cursor['phase'], 'start')               # nothing asked: 1 January ran
        self.assertFalse([d for d in s.season.career.pending() if d['payload'].get('market')])
        before = F.digest(s)
        for _ in range(3):                                            # repeated reads of every read model
            v = CA.view(s.season, s.cursor)
            CA.week_entry(s.season, s.season.career, 2028, 1)
            CA.planner(s.season, s.cursor, 2028, 1)
            self.assertIsNotNone(v['scouting'])
        self.assertEqual(F.digest(s), before)
        drop(s)


if __name__ == '__main__':
    unittest.main()
