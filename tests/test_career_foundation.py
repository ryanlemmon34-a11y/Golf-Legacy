"""Career mode foundation (roadmap Phases A and B; docs/career/PHASE_AB_PLAN.md): the control layer over the
world simulation, on a small fixture world (seed 11, scale 0.05) played to its first newcomer boundary.

Run from the project folder:  python -m unittest tests.test_career_foundation -v
"""
from __future__ import annotations

import json
import random
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))
import career_fixture as F                                             # noqa: E402
from golfsim import career as CA                                       # noqa: E402
from golfsim import staff as ST                                        # noqa: E402
from golfsim.season import Season                                      # noqa: E402
from golfsim.session import Session, StaleCursor, UnsupportedCareer    # noqa: E402

# digests of the fixture world under main 18a8e23 (all AI): after its first season, and after 12 more weeks
MAIN_SEASON1 = '25ca649704b1447f4d4767609aa8ba82d4133cf646185cd4c5d9715a4f1ce42b'
MAIN_2028_W12 = '6d82605695fe90648a02df645d78a52a6cdd145cb882da4231a013e44374d4cb'

REST = {'kind': 'rest'}
POLICY = {'selected': 'accept', 'qualifying': 'skip'}


def act(s, body, key, **kw):
    return s.career_action(dict({'schema': CA.SCHEMA}, **body), op_key=key, **kw)


def started(prefix='c'):
    """A copy of the fixture with a career begun, and its session."""
    s = Session.open(F.copy_of(F.first_boundary()))
    act(s, {'type': 'new_career'}, f'{prefix}-new')
    return s


def plan(s, block, weeks=None, policy=POLICY, key=None):
    y, w0 = block
    open_w = CA.open_weeks(s.cursor, w0)
    body = {'type': 'plan_block', 'block': [y, w0], 'version': s.season.career.version,
            'weeks': {str(w): (weeks or {}).get(w, REST) for w in open_w}, 'policy': policy}
    return act(s, body, key or f'plan-{y}-{w0}-{s.season.career.version}')


def first_event(s, week, pred=lambda e: True):
    pl = CA.planner(s.season, s.cursor, s.cursor['year'], CA.block_start(week))
    wk = next(x for x in pl['weeks'] if x['week'] == week)
    return next(e for e in wk['events'] if e['eligible'] and e['affordable'] and pred(e))


def golfer(s):
    return s.season.g[s.season.career.golfer_id]


class AllAI(unittest.TestCase):
    def test_all_ai_worlds_equal_main(self):
        """Without a career the engine and session behave exactly as main: the same world after a season and after
        twelve more weeks advanced one committed week at a time."""
        s = Session.open(F.copy_of(F.first_boundary()))
        self.assertEqual(F.digest(s), MAIN_SEASON1)
        for _ in range(12):
            s.advance_one_week(expected=s.cursor)
        self.assertEqual(F.digest(s), MAIN_2028_W12)
        self.assertIsNone(s.season.career)
        s.close()


class NewCareer(unittest.TestCase):
    def test_a_genuine_newcomer_once(self):
        d = F.copy_of(F.first_boundary())
        s = Session.open(d)
        n_people = len(s.season.world.golfers)
        r = act(s, {'type': 'new_career'}, 'n1')
        gid = r['golfer']
        rec = s.season.creations[2028][gid]
        self.assertEqual(rec['path'], 'junior')                    # one of the class the normal rules created
        self.assertEqual(len(s.season.world.golfers), n_people)    # nobody created, nobody duplicated
        self.assertEqual(act(s, {'type': 'new_career'}, 'n1'), r)  # the same request again: the stored result
        with self.assertRaises(CA.CareerError):
            act(s, {'type': 'new_career'}, 'n2')                   # one career per world
        s.close()
        s = Session.open(d)                                         # reopened: the same golfer, still one career
        self.assertEqual(s.season.career.golfer_id, gid)
        self.assertEqual(sum(1 for g in s.season.world.golfers if g.id == gid), 1)
        s.close()
        s2 = started('again')                                       # the pick is reproducible (seeded, not ability)
        self.assertEqual(s2.season.career.golfer_id, gid)
        s2.close()

    def test_only_at_a_season_start_with_a_class(self):
        from golfsim.population import generate_world
        s = Session.create(F.tmpdir() / 'w', seed=5, world=generate_world(year=2027, seed=5, scale=0.02), workers=1)
        with self.assertRaisesRegex(CA.CareerError, 'no newcomer class'):
            act(s, {'type': 'new_career'}, 'x')                     # 2027: the world's first class comes at its winter
        s.close()
        s = Session.open(F.copy_of(F.first_boundary()))
        s.advance(1)
        with self.assertRaisesRegex(CA.CareerError, '1 January'):
            act(s, {'type': 'new_career'}, 'y')
        s.close()


class Gates(unittest.TestCase):
    def test_stops_before_the_week_and_saves_the_decision(self):
        s = started()
        g0 = s.generation
        out = s.advance_career('next', expected=s.cursor, op_key='a')
        self.assertEqual(out['weeks'], [])                          # 1 January ran; no week played
        self.assertEqual(s.cursor, {'year': 2028, 'week': 1, 'phase': 'week'})
        self.assertGreater(s.generation, g0)                        # committed although no week was played
        kinds = [d['kind'] for d in s.season.career.pending()]
        self.assertEqual(kinds, ['plan'])
        d = s.dir
        s.close()
        s = Session.open(d)                                         # reload at the interruption: the same decision
        self.assertEqual([x['kind'] for x in s.season.career.pending()], ['plan'])
        self.assertEqual(s.cursor['phase'], 'week')
        self.assertEqual(s.advance(4), [])                          # the ordinary advance obeys the gate too
        self.assertEqual(s.cursor, {'year': 2028, 'week': 1, 'phase': 'week'})
        s.close()

    def test_period_and_counting_only_played_weeks(self):
        s = started()
        s.advance_career('next', op_key='a')
        e1 = first_event(s, 1)
        plan(s, (2028, 1), {1: {'kind': 'event', 'event_id': e1['event_id'],
                                'fallback': {'kind': 'train', 'category': 'putting'}},
                            2: {'kind': 'train', 'category': 'long_game'}})
        out = s.advance(2)                                          # two weeks means two played weeks
        self.assertEqual([r['completed'] for r in out], [(2028, 1), (2028, 2)])
        out = s.advance_career('period', op_key='p')
        self.assertEqual([r['completed'] for r in out['weeks']], [(2028, 3), (2028, 4)])
        self.assertEqual(out['stop']['kind'], 'period_end')
        self.assertEqual(s.cursor, {'year': 2028, 'week': 5, 'phase': 'week'})
        gid = s.season.career.golfer_id
        self.assertIn(gid, s.season.event_routes[2028][e1['event_id']])   # entered the planned event, and played it
        self.assertGreaterEqual(s.season.week_access[2028][gid]['played: first choice'], 1)
        self.assertEqual(s.season.activity_counts[2028][gid]['train'], 1)
        s.close()

    def test_the_ai_never_writes_the_human_plan(self):
        s = started()
        s.advance_career('next', op_key='a')
        plan(s, (2028, 1), {1: {'kind': 'train', 'category': 'mental'}, 2: {'kind': 'train', 'category': 'putting'}})
        s.advance(1)                                                # block planning ran for everyone
        gid = s.season.career.golfer_id
        self.assertEqual(s.season.plans[gid], {1: ('train', 'mental'), 2: ('train', 'putting'), 3: ('rest', None),
                                               4: ('rest', None)})
        s.close()

    def test_revalidated_after_preparation_before_any_consequence(self):
        s = started()
        s.advance_career('next', op_key='a')
        e1 = first_event(s, 1)
        plan(s, (2028, 1), {1: {'kind': 'event', 'event_id': e1['event_id'], 'fallback': {'kind': 'rest'}}})
        g = golfer(s)
        g.cash, g.backing = -1e7, 0.0                               # the money is gone before the week is played
        s.season.am_support.pop(g.id, None)
        s._commit()
        played0 = s.state['weeks_played']
        out = s.advance_career('period', op_key='b')
        self.assertEqual(out['weeks'], [])
        self.assertEqual(s.cursor['phase'], 'planned')              # prepared (block planned), nothing played
        self.assertEqual(s.state['weeks_played'], played0)
        d = s.season.career.pending()
        self.assertEqual([x['kind'] for x in d], ['replan'])
        self.assertIn('cannot afford', d[0]['text'])
        plan(s, (2028, 1), {1: {'kind': 'train', 'category': 'short_game'}})   # re-planned while prepared
        self.assertEqual(s.season.plans[g.id][1], ('train', 'short_game'))
        out = s.advance(1)
        self.assertEqual(out[0]['completed'], (2028, 1))
        self.assertEqual(s.season.week_activity[g.id], 'train')
        s.close()

    def test_injury_is_a_notice_not_a_decision(self):
        s = started()
        s.advance_career('next', op_key='a')
        e1 = first_event(s, 1)
        plan(s, (2028, 1), {1: {'kind': 'event', 'event_id': e1['event_id'], 'fallback': {'kind': 'rest'}}})
        g = golfer(s)
        s.season.injured[g.id] = (s.season.abs_week(2028, 3), 'test', 2)
        s._commit()
        out = s.advance(1)
        self.assertEqual(out[0]['completed'], (2028, 1))
        self.assertEqual(s.season.career.pending(), [])
        self.assertTrue(any(n['kind'] == 'injury' for n in s.season.career.notices))
        self.assertNotIn(g.id, s.season.event_routes[2028].get(e1['event_id'], {}))
        s.close()

    def test_entry_not_placed_takes_the_fallback(self):
        s = started()
        s.advance_career('next', op_key='a')
        e1 = first_event(s, 1)
        plan(s, (2028, 1), {1: {'kind': 'event', 'event_id': e1['event_id'], 'fallback': {'kind': 'rest'}}})
        with mock.patch.object(Season, '_career_entry', lambda self, car, g, y, w, opts, prefs: car.note(
                y, w, 'entry', 'not entered (test)', key=('noentry', y, w))):
            s.advance(1)
        gid = s.season.career.golfer_id
        self.assertEqual(s.season.week_activity[gid], 'rest')        # the player's fallback, not the AI's training
        s.close()

    def test_entries_go_through_the_shared_priority(self):
        s = started()
        s.advance_career('next', op_key='a')
        e1 = first_event(s, 1)
        plan(s, (2028, 1), {1: {'kind': 'event', 'event_id': e1['event_id'], 'fallback': {'kind': 'rest'}}})
        gid = s.season.career.golfer_id
        seen = []
        real = Season.priority

        def spy(self, g, ser):
            seen.append(g.id)
            return real(self, g, ser)
        with mock.patch.object(Season, 'priority', spy):
            s.advance(1)
        self.assertIn(gid, seen)                                     # no guaranteed entry: ordered like everyone
        s.close()


class Offers(unittest.TestCase):
    def offer(self, s, arrangement='share'):
        g = golfer(s)
        st = s.season.staff
        coach = next(c for c in sorted(st.coaches.values(), key=lambda c: c.id) if c.status == 'active'
                     and sum(1 for x in st.coach_of.values() if x == c.id) < c.capacity // 3)
        before = (dict(st.coach_of), dict(st.deal), len(st.rel.stints) if hasattr(st.rel, 'stints') else None)
        self.assertFalse(ST.approach(s.season, coach, g, 'test approach', (2028, 1), random.Random(3),
                                     arrangement=arrangement))
        self.assertEqual((dict(st.coach_of), dict(st.deal), len(st.rel.stints) if hasattr(st.rel, 'stints') else None),
                         before)                                     # nothing ended, assigned, charged or reserved
        s._commit()
        return coach, s.season.career.pending(('coach_offer',))[0]

    def test_pending_offer_then_one_acceptance(self):
        s = started()
        s.advance_career('next', op_key='a')
        coach, d = self.offer(s)
        self.assertEqual(d['deadline'], [2028, 5])
        r = act(s, {'type': 'decide', 'decision': d['id'], 'answer': 'accept'}, 'yes')
        self.assertTrue(r['ok'])
        self.assertIs(s.season.staff.coach(golfer(s).id), coach)
        self.assertEqual(act(s, {'type': 'decide', 'decision': d['id'], 'answer': 'accept'}, 'yes'), r)  # same key
        with self.assertRaisesRegex(CA.CareerError, 'already accepted'):
            act(s, {'type': 'decide', 'decision': d['id'], 'answer': 'accept'}, 'yes-again')
        self.assertEqual(sum(1 for x in s.season.staff.coach_of if x == golfer(s).id), 1)
        s.close()

    def test_acceptance_revalidates(self):
        s = started()
        s.advance_career('next', op_key='a')
        coach, d = self.offer(s)
        coach.status = 'retired'                                     # gone before the player answered
        s._commit()
        r = act(s, {'type': 'decide', 'decision': d['id'], 'answer': 'accept'}, 'yes')
        self.assertFalse(r['ok'])
        self.assertIn('no longer working', r['reason'])
        self.assertIsNone(s.season.staff.coach(golfer(s).id))
        s.close()

    def test_offer_deadline_stops_the_advance_and_blocks_handback(self):
        s = started()
        s.advance_career('next', op_key='a')
        _, d = self.offer(s)
        with self.assertRaisesRegex(CA.CareerError, 'Answer the pending offers first'):
            act(s, {'type': 'end_control'}, 'end')
        plan(s, (2028, 1))
        plan(s, (2028, 5))
        out = s.advance_career('period', op_key='p')                 # the offer is not due yet: weeks 1-4 play
        self.assertEqual(len(out['weeks']), 4)
        out = s.advance_career('period', op_key='q')                 # due before week 5: stops
        self.assertEqual(out['weeks'], [])
        self.assertIn(d['id'], out['stop']['ids'])
        act(s, {'type': 'decide', 'decision': d['id'], 'answer': 'decline'}, 'no')
        self.assertIsNone(s.season.staff.coach(golfer(s).id))
        self.assertEqual(len(s.advance_career('period', op_key='r')['weeks']), 4)
        s.close()


class WorkPathway(unittest.TestCase):
    def blocked(self):
        s = started()
        s.advance_career('next', op_key='a')
        g = golfer(s)
        g.tour, g.lifestyle, g.backing = 'AM_NORTH_AMERICA', 'full_time', 0.0     # a series amateur, no family money
        s.season.am_support.pop(g.id, None)
        s.season.am_pos.pop(g.id, None)
        s.season.cash_blocked[g.id] = 8
        s._commit()
        plan(s, (2028, 1))
        s.advance_career('period', op_key='p')
        plan(s, (2028, 5))
        out = s.advance_career('period', op_key='q')                # week 5 is prepared, then the job decision
        self.assertEqual(out['weeks'], [])
        self.assertEqual(s.cursor['phase'], 'planned')
        return s, g, s.season.career.pending(('job',))[0]

    def test_taking_the_job(self):
        s, g, d = self.blocked()
        self.assertEqual(g.lifestyle, 'full_time')                    # nothing happened yet
        act(s, {'type': 'decide', 'decision': d['id'], 'answer': 'accept'}, 'job')
        self.assertEqual(g.lifestyle, 'part_time')                    # the pathway's own consequence
        self.assertEqual([r['gid'] for r in s.season.work_pathway[2028]], [g.id])
        self.assertEqual(len(s.advance_career('period', op_key='r')['weeks']), 4)
        s.close()

    def test_declining_keeps_full_time(self):
        s, g, d = self.blocked()
        act(s, {'type': 'decide', 'decision': d['id'], 'answer': 'decline'}, 'nojob')
        self.assertEqual(g.lifestyle, 'full_time')
        self.assertNotIn(g.id, [r['gid'] for r in s.season.work_pathway[2028]])
        self.assertEqual(len(s.advance_career('period', op_key='r')['weeks']), 4)
        s.close()

    def test_unsupported_paid_work_stops_with_a_handback(self):
        s = started()
        s.advance_career('next', op_key='a')
        g = golfer(s)
        g.status, g.tour, g.cash, g.backing = 'pro', 'MN_US_SUNBELT', 0.0, 0.0
        s._commit()
        out = s.advance_career('next', op_key='b')
        self.assertEqual(out['weeks'], [])
        d = [x for x in s.season.career.pending() if x['kind'] == 'unsupported']
        self.assertTrue(d and 'paid work' in d[0]['text'])
        act(s, {'type': 'decide', 'decision': d[0]['id'], 'answer': 'return_to_ai'}, 'ai')
        self.assertEqual(s.season.career.status, 'ended')
        self.assertEqual(len(s.advance(2)), 2)                         # the world continues under AI
        s.close()


class SeasonEnd(unittest.TestCase):
    def test_winter_stops_then_runs_once_after_handback(self):
        s = started()
        n = 0
        while True:
            out = s.advance_career('next', op_key=f'n{n}')
            n += 1
            stop = out['stop'] or {}
            pend = s.season.career.pending()
            if any(d['kind'] == 'season_end' for d in pend):
                break
            for d in pend:
                if d['kind'] == 'plan':
                    plan(s, d['payload']['block'])
                elif d['kind'] in ('coach_offer', 'caddie_offer', 'job'):
                    act(s, {'type': 'decide', 'decision': d['id'], 'answer': 'decline'}, f'd{d["id"]}')
            self.assertLess(n, 60)
        self.assertEqual(s.cursor, {'year': 2028, 'week': 52, 'phase': 'end'})
        self.assertNotIn(2029, s.season.juniors_added)                # the winter has not run
        d = next(x for x in s.season.career.pending() if x['kind'] == 'season_end')
        act(s, {'type': 'decide', 'decision': d['id'], 'answer': 'return_to_ai'}, 'ai')
        out = s.advance(1)                                            # the winter, once, then 2029 week 1
        self.assertIn(2029, s.season.juniors_added)
        juniors = s.season.juniors_added[2029]
        path = s.dir
        s.close()
        s = Session.open(path)                                        # reloaded: the winter is not repeated
        s.advance(1)
        self.assertEqual(s.season.juniors_added[2029], juniors)
        self.assertEqual(sum(1 for r in s.season.creations[2029].values() if r['path'] == 'junior'), juniors)
        s.close()


class Persistence(unittest.TestCase):
    def actions(self, s, reopen):
        steps = [lambda s: act(s, {'type': 'new_career'}, 'n'),
                 lambda s: s.advance_career('next', op_key='a'),
                 lambda s: plan(s, (2028, 1), {2: {'kind': 'train', 'category': 'physical'}}, key='p1'),
                 lambda s: s.advance_career('period', op_key='b')]
        for step in steps:
            step(s)
            if reopen:
                d = s.dir
                s.close()
                s = Session.open(d)
        return s

    def test_reload_between_parts_repeats_nothing_and_replays_deterministically(self):
        a = self.actions(Session.open(F.copy_of(F.first_boundary())), reopen=False)
        b = self.actions(Session.open(F.copy_of(F.first_boundary())), reopen=True)
        self.assertEqual(F.digest(a), F.digest(b))                   # 1 January and the block planning ran once
        self.assertEqual(a.cursor, {'year': 2028, 'week': 5, 'phase': 'week'})
        again = b.advance_career('period', op_key='b')                # an earlier operation key, resubmitted
        self.assertEqual(b.cursor, {'year': 2028, 'week': 5, 'phase': 'week'})
        self.assertEqual([w['completed'] for w in again['weeks']], [(2028, w) for w in (1, 2, 3, 4)])
        a.close()
        b.close()

    def test_stale_and_newer_format(self):
        s = started()
        old = s.cursor
        s.advance_career('next', op_key='a')
        with self.assertRaises(StaleCursor):
            s.career_action({'schema': CA.SCHEMA, 'type': 'end_control'}, expected=old, op_key='z')
        with self.assertRaisesRegex(CA.CareerError, 'Unsupported command format'):
            s.career_action({'schema': 99, 'type': 'end_control'}, op_key='zz')
        s.season.career.format = 99                                  # as a newer build would have written it
        s._commit()
        d = s.dir
        s.close()
        with self.assertRaises(UnsupportedCareer):
            Session.open(d)


class Privacy(unittest.TestCase):
    def test_no_hidden_potential_in_views(self):
        s = started()
        s.advance_career('next', op_key='a')
        g = golfer(s)
        blob = json.dumps([CA.view(s.season, s.cursor), CA.planner(s.season, s.cursor, 2028, 1)], default=str).lower()
        for word in ('potential', 'ceiling', 'peak_age', 'aging_rate'):
            self.assertNotIn(word, blob)
        self.assertNotIn(repr(round(g.potential, 2)), blob)
        s.close()


if __name__ == '__main__':
    unittest.main()
