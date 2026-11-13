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

# digests of the fixture world (all AI) after its first season, and after 12 more weeks advanced one committed week
# at a time, under the engine this integration build builds on: the realism test build 52870f5 (engine of 7e88aa2:
# dev-3 rules for new worlds, the long-irons table of rules 2026-11-16, standing-based seeded money), computed with
# the same procedure on 52870f5 itself (docs/career/INTEGRATION.md). The career branch's earlier reference, main
# 18a8e23 + the engine fix (4d9be6cb...2097 and 1ce30676...e7a), cannot hold here: the long-irons table changes play
# in every world, whatever its development rules (a dev-1 fixture gives 360fed3a...a165 on both 52870f5 and this
# build).
MAIN_SEASON1 = 'c6230d8ec521c39b53e8829585ddb3e59ff646e1f795b2e67130150dc233c25b'
MAIN_2028_W12 = '80ad8e6f1cbccef2a72a6e323de52bb675da401a455808cca11a0908df54b8a9'

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
        """Without a career the engine and session behave exactly as the engine this build builds on (the realism
        test build 52870f5, dev-3): the same world after a season and after twelve more weeks advanced one committed
        week at a time."""
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


class ParkedDefects(unittest.TestCase):
    """The three defects found in review of 8354ea0, each fixed and tested on its own."""

    def test_advance_one_week_returns_a_stopped_result_at_a_gate(self):
        s = started()
        g0 = s.generation
        r = s.advance_one_week(expected=s.cursor)                 # 1 January runs, then the plan gate stops
        self.assertIsNone(r['completed'])
        self.assertEqual(r['stop']['kind'], 'decision')
        self.assertEqual(r['cursor'], {'year': 2028, 'week': 1, 'phase': 'week'})
        self.assertGreater(s.generation, g0)                        # the decision the gate created is committed
        self.assertEqual(r['generation'], s.generation)
        g1 = s.generation
        r = s.advance_one_week(expected=s.cursor)                 # still stopped; nothing new, nothing committed
        self.assertIsNone(r['completed'])
        self.assertEqual(r['stop']['kind'], 'decision')
        self.assertEqual(s.generation, g1)
        self.assertEqual(s.advance(3, commit_every_week=True), [])   # the per-week API stops instead of failing
        self.assertEqual(s.cursor, {'year': 2028, 'week': 1, 'phase': 'week'})
        k = s.advance_one_week(expected=s.cursor, op_key='k')     # a keyed blocked request: recorded, replayable
        self.assertIsNone(k['completed'])
        self.assertEqual(s.advance_one_week(expected=s.cursor, op_key='k'), k)
        plan(s, (2028, 1))
        out = s.advance(2, commit_every_week=True)
        self.assertEqual([x['completed'] for x in out], [(2028, 1), (2028, 2)])
        s.close()

    def _handback(self, s):
        """End control with Season._plan_acts spied on; returns (the calls, the plans before)."""
        calls = []
        real = Season._plan_acts

        def spy(self, g, year, week0, weeks, *a, **k):
            r = real(self, g, year, week0, weeks, *a, **k)
            calls.append((g.id, year, list(weeks), list(r[0])))
            return r
        with mock.patch.object(Season, '_plan_acts', spy):
            act(s, {'type': 'end_control'}, f'end-{s.season.career.version}')
        return calls

    def _side_effects(self, s, gid):
        se = s.season
        coach, caddie = se.staff.coach(gid), se.staff.caddie(gid)
        return json.dumps([dict(se.block_flags[2028].get(gid, {})), se.stuck_blocks.get(gid), se.week_avail.get(gid),
                           coach.id if coach else None, caddie.id if caddie else None, golfer(s).lifestyle,
                           golfer(s).tour, round(golfer(s).cash, 6), sorted(se.plan_ev.get(2028, {}).keys())
                           if hasattr(se, 'plan_ev') else None], sort_keys=True, default=str)

    def test_handback_mid_block_hands_the_rest_of_the_block_to_the_ai(self):
        s = started()
        s.advance_career('next', op_key='a')
        human = {w: {'kind': 'train', 'category': 'putting'} for w in (1, 2, 3, 4)}
        plan(s, (2028, 1), human)
        s.advance(1)                                                # week 1 played as planned
        self.assertEqual(s.cursor, {'year': 2028, 'week': 2, 'phase': 'week'})
        gid = s.season.career.golfer_id
        self.assertEqual(s.season.plans[gid], {w: ('train', 'putting') for w in (1, 2, 3, 4)})
        before = self._side_effects(s, gid)
        calls = self._handback(s)
        self.assertEqual(len(calls), 1)                             # the AI planner ran once, for weeks 2-4 only
        cg, cy, weeks, acts = calls[0]
        self.assertEqual((cg, cy, weeks), (gid, 2028, [2, 3, 4]))
        plans = s.season.plans[gid]
        self.assertEqual(plans[1], ('train', 'putting'))           # the week already played is left alone
        self.assertEqual([plans[w][0] for w in (2, 3, 4)], acts)   # the AI's own plan, not the player's intents
        self.assertEqual(self._side_effects(s, gid), before)       # no staff, job, statistics or evidence change
        d = s.dir
        s.close()
        s = Session.open(d)                                         # saved with the handback
        self.assertEqual([s.season.plans[gid][w][0] for w in (2, 3, 4)], acts)
        out = s.advance(3)                                          # the AI plays the rest of the block
        self.assertEqual([x['completed'] for x in out], [(2028, 2), (2028, 3), (2028, 4)])
        s.close()

    def test_handback_in_a_prepared_week_keeps_that_week(self):
        s = started()
        s.advance_career('next', op_key='a')
        e1 = first_event(s, 1)
        plan(s, (2028, 1), {1: {'kind': 'event', 'event_id': e1['event_id'], 'fallback': {'kind': 'rest'}}})
        g = golfer(s)
        g.cash, g.backing = -1e7, 0.0                               # the planned trip becomes unaffordable
        s.season.am_support.pop(g.id, None)
        s._commit()
        s.advance_career('period', op_key='b')
        self.assertEqual(s.cursor['phase'], 'planned')              # week 1 prepared; the replan decision waits
        prepared = s.season.plans[g.id][1]
        calls = self._handback(s)
        self.assertEqual([c[2] for c in calls], [[2, 3, 4]])       # only the weeks not yet prepared
        self.assertEqual(s.season.plans[g.id][1], prepared)
        self.assertEqual(s.season.career.pending(), [])             # the open decision was closed by the handback
        self.assertEqual(s.advance(1)[0]['completed'], (2028, 1))
        s.close()

    def test_handback_at_a_block_start_leaves_planning_to_plan_block(self):
        s = started()
        s.advance_career('next', op_key='a')
        plan(s, (2028, 1))
        s.advance(4)
        self.assertEqual(s.cursor, {'year': 2028, 'week': 5, 'phase': 'week'})
        self.assertEqual(self._handback(s), [])                     # nothing to rebuild: week 5 plans its block
        s.close()

    def test_a_blocked_keyed_request_is_recorded_and_never_runs_later(self):
        s = started()
        s.advance_career('next', op_key='A')                        # the first gate creates the plan decision
        v = s.season.career.version
        g1 = s.generation
        played = s.state['weeks_played']
        b = s.advance_career('next', expected=s.cursor, op_key='B', expected_version=v)   # blocked by that decision
        self.assertEqual(b['weeks'], [])
        self.assertEqual(b['stop']['kind'], 'decision')
        self.assertGreater(s.generation, g1)                        # recorded although nothing changed
        self.assertEqual(s.season.career.version, v)
        plan(s, (2028, 1))                                          # the decision is answered; the cursor is unchanged
        self.assertEqual(s.cursor, {'year': 2028, 'week': 1, 'phase': 'week'})
        d = s.dir
        s.close()
        s = Session.open(d)                                         # durable across a reload
        again = s.advance_career('next', expected=s.cursor, op_key='B', expected_version=v)
        self.assertEqual(again, b)                                  # the recorded outcome, not a new advance
        self.assertEqual(s.state['weeks_played'], played)
        self.assertEqual(s.cursor, {'year': 2028, 'week': 1, 'phase': 'week'})
        with self.assertRaises(CA.StaleCareer):                     # a new request drawn before the plan: refused
            s.advance_career('next', expected=s.cursor, op_key='C', expected_version=v)
        self.assertEqual(s.state['weeks_played'], played)
        out = s.advance_career('period', expected=s.cursor, op_key='D', expected_version=s.season.career.version)
        self.assertEqual(len(out['weeks']), 4)
        s.close()


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
