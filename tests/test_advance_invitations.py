"""Advance invitations (calendar v4; golfsim/invitations.py, docs/career/ADVANCE_INVITATIONS.md).

World: seed 23, scale 0.05, calendar v4, all AI through 2027 (built once, copied per test). The career golfer of that
world (a fresh career at 1 January 2028) is a US college amateur invited to the USA national amateur championship.

Run from the project folder:  python -m unittest tests.test_advance_invitations -v
"""
from __future__ import annotations

import copy
import pickle
import shutil
import sys
import unittest
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))
import career_fixture as F                                             # noqa: E402
from golfsim import career as CA                                       # noqa: E402
from golfsim import entry_outlook as EO                                # noqa: E402
from golfsim import invitations as INV                                 # noqa: E402
from golfsim import schedule as SCH                                    # noqa: E402
from golfsim.population import generate_world                          # noqa: E402
from golfsim.session import Session                                    # noqa: E402

_BASE = {}
_DIRS = []


def base(calendar='v4', weeks=52):
    key = (calendar, weeks)
    if key not in _BASE:
        d = F.tmpdir('inv_base_') / 'w'
        _DIRS.append(d.parent)
        s = Session.create(d, seed=23, world=generate_world(year=2027, seed=23, scale=0.05), workers=1,
                           calendar=calendar)
        s.advance(weeks)
        s.close()
        _BASE[key] = d
    d = F.tmpdir('inv_') / 'w'
    _DIRS.append(d.parent)
    shutil.copytree(_BASE[key], d)
    return Session.open(d)


def tearDownModule():
    for d in _DIRS:
        shutil.rmtree(d, ignore_errors=True)


def act(s, body, key):
    return s.career_action(dict({'schema': CA.SCHEMA}, **body), op_key=key)


def career_until(s, stop, answer=None, log=None):
    """A fresh career, the coach's advice applied as given each period, offers from the staff market declined; runs
    until stop(s) is true. Invitation decisions: answered with `answer(d)` when it returns an option, else left
    open (they then block at their deadline)."""
    act(s, {'type': 'new_career'}, 'new')
    c = s.season.career
    for i in range(400):
        if stop(s):
            return c
        s.advance_career('next', op_key=f'a{i}')
        for d in c.pending(CA.OFFER_KINDS):
            act(s, {'type': 'decide', 'decision': d['id'], 'answer': 'decline'}, f'o{d["id"]}')
        for d in c.pending(('invitation',)):
            if log is not None:
                log.append((tuple((s.cursor['year'], s.cursor['week'])), copy.deepcopy(d)))
            a = answer(d) if answer else None
            if a is not None:
                act(s, {'type': 'decide', 'decision': d['id'], 'answer': a}, f'i{d["id"]}')
        if s.cursor['phase'] == 'week':
            v = CA.view(s.season, s.cursor)
            a = v.get('advice')
            if a and c.plan_for(*a['block']) is None:
                act(s, {'type': 'plan_block', 'block': a['block'], 'version': c.version,
                        'weeks': {w: x['recommended'] for w, x in a['weeks'].items()}, 'policy': a['policy']},
                    f'p{i}')
    raise AssertionError('not reached')


def at(y, w):
    return lambda s: (s.cursor['year'], s.cursor['week']) >= (y, w) and s.cursor['phase'] == 'week'


USA = '2028:NATIONAL_AMATEUR_USA'


class Spec(unittest.TestCase):
    def test_v4_new_worlds_only(self):
        self.assertEqual(SCH.NEW_WORLD, 'v4')
        self.assertTrue(SCH.V4.advance_invitations)
        for v in ('v1', 'v2', 'v3'):
            self.assertFalse(SCH.SPECS[v].advance_invitations)


class Lifecycle(unittest.TestCase):
    """All AI, through 2028 week 34."""

    @classmethod
    def setUpClass(cls):
        cls.s = base(weeks=52 + 34)
        cls.se = cls.s.season
        cls.led = cls.se.invitations

    @classmethod
    def tearDownClass(cls):
        cls.s.close()

    def test_advance_notice_by_event_type_and_rollover(self):
        n = 0
        for rec in self.led.values():
            lead = INV.LEAD[rec['category']]
            e = self.se.abs_week(rec['year'], rec['week'])
            self.assertEqual(self.se.abs_week(*rec['offer_at']), e - lead)
            self.assertEqual(self.se.abs_week(*rec['deadline']), e - lead + INV.RESPOND)
            self.assertNotEqual(rec['series_id'], 'USA_AMATEUR')            # qualifying + exemptions: unchanged
            n += 1
        self.assertGreater(n, 40)
        early = [r for r in self.led.values() if r['year'] == 2028 and r['week'] <= INV.LEAD[r['category']]]
        self.assertTrue(early)
        self.assertEqual([(r['event_id'], r['offer_at']) for r in early
                          if not (r['offer_at'][0] == 2027 and r['offer_at'][1] >= 46)], [])   # the December before
        self.assertEqual([r['event_id'] for r in early if not r.get('played')], [])

    def test_answers_and_promotions_at_the_deadline(self):
        for rec in self.led.values():
            if tuple(rec['deadline']) > (2028, 34):
                continue
            for e in rec['entries']:
                self.assertNotEqual(e['status'], 'offered', rec['event_id'])
                self.assertEqual(e['answered_at'], rec['deadline'])
            taken = [e for e in rec['entries'] if e['status'] in INV.TAKEN or e.get('status_before') in INV.TAKEN]
            self.assertLessEqual(len(taken), rec['field'])
            promoted = [e for e in rec['entries'] if 'promoted' in (e['status'], e.get('status_before'))]
            lost = [e for e in rec['entries'] if e['role'] == 'invited' and e['status'] in ('declined', 'expired')]
            self.assertLessEqual(len(promoted), len(lost))

    def test_fields_come_from_the_ledger_only_vacancy_replacements(self):
        for rec in self.led.values():
            if not rec.get('played'):
                continue
            res = self.se.results.get(rec['event_id'])
            entered = {e['golfer_id'] for e in rec['entries'] if e['status'] == 'entered'}
            played = {gid for site in res.finish for gid, _, _ in site} if res else set()
            self.assertEqual(played, entered, rec['event_id'])
            late = [e for e in rec['entries'] if e.get('late')]
            withdrawn = [e for e in rec['entries'] if e['status'] == 'withdrawn']
            self.assertLessEqual(len(late), len(withdrawn), rec['event_id'])    # only genuine vacancies
            for e in late:
                self.assertEqual(e['role'], 'alternate')
                self.assertEqual(e['status_before'], 'standby')

    def test_no_golfer_twice_on_the_same_days(self):
        """Never in two fields on overlapping days, never twice in one field (two events on different days of one week
        is the calendar's day-level rule, unchanged)."""
        days = defaultdict(list)
        for eid, r in self.se.results.items():
            if r.year != 2028:
                continue
            s = self.se.cal.by_id[eid.split(':', 1)[1]]
            ids = [gid for site in r.finish for gid, _, _ in site]
            self.assertEqual(len(ids), len(set(ids)), eid)
            for gid in ids:
                days[(r.week, gid)].append(set(s.day_set))
        for k, sets in days.items():
            for i in range(len(sets)):
                for j in range(i + 1, len(sets)):
                    self.assertFalse(sets[i] & sets[j], k)

    def test_late_replacement_needs_a_withdrawal_in_that_event(self):
        for rec in self.led.values():
            logs = rec['log']
            for k, x in enumerate(logs):
                if x['event'] == 'late_replacement':
                    self.assertTrue(any(y['event'] == 'withdrawn' for y in logs[:k]), rec['event_id'])

    def test_step_is_idempotent(self):
        se = pickle.loads(pickle.dumps(self.se))
        before = pickle.dumps(se.invitations)
        INV.step(se, 2028, 34)                                              # (already run this week)
        self.assertEqual(pickle.dumps(se.invitations), before)


class Parity(unittest.TestCase):
    """The same state and the same answer give the same lifecycle whether the golfer is the player's or an AI's: the
    player answering what the rule answers (or the explicit 'auto' setting) gives the AI's ledger and the same world."""

    def test_matched_answers(self):
        s = base(weeks=52 + 25)                          # the USA national amateur's offers sent in week 25
        try:
            se = s.season
            self.assertIn(USA, se.invitations)
            rec = se.invitations[USA]
            R = tuple(rec['deadline'])
            s.advance(R[1] - s.cursor['week'])          # up to the deadline week (not yet played)
            self.assertEqual((s.cursor['year'], s.cursor['week']), R)
            ai = pickle.loads(pickle.dumps(se))
            ai.prepare_week(*R)
            INV.step(ai, *R)
            picks = [e for e in ai.invitations[USA]['entries'] if e['by'] == 'ai'][:6]
            self.assertTrue(any(e['status'] == 'accepted' for e in picks))
            for e in picks:
                gid = e['golfer_id']
                ans = {'accepted': 'accept', 'standby': 'standby', 'declined': 'decline'}.get(e['status'])
                if ans is None:
                    continue
                for policy in ('ask', 'auto'):
                    pl = pickle.loads(pickle.dumps(se))
                    pl.prepare_week(*R)
                    c = CA.Career(gid, *R, {'rule': 'test'})
                    c.invitation_policy = policy
                    if policy == 'ask':
                        c.invitation_answers = {USA: ans}
                    pl.career = c
                    INV.step(pl, *R)
                    strip = lambda led: {k: [dict(x, by=None) for x in r['entries']] for k, r in led.items()}
                    self.assertEqual(strip(pl.invitations), strip(ai.invitations), (gid, policy))
                    mine = next(x for x in pl.invitations[USA]['entries'] if x['golfer_id'] == gid)
                    self.assertEqual(mine['by'], 'player' if policy == 'ask' else 'auto')
        finally:
            s.close()


class Career(unittest.TestCase):
    """The player's side: offer shown with cost, place, dates and conflicts; nothing blocks before the deadline; the
    deadline does; answers survive save and load; a decline spends nothing."""

    def test_offer_deadline_save_load_and_accept(self):
        s = base()
        log = []
        try:
            c = career_until(s, at(2028, 27), answer=None, log=log)
            d = next(d for _, d in log if d['payload']['event_id'] == USA)
            first_seen = next(when for when, x in log if x['id'] == d['id'])
            p = d['payload']
            rec = s.season.invitations[USA]
            self.assertEqual(first_seen, (rec['offer_at'][0], rec['offer_at'][1] + 1))   # shown the week after
            self.assertEqual(p['deadline'], rec['deadline'])
            self.assertEqual(p['event_week'], [2028, rec['week']])
            for k in ('cost_estimate', 'city', 'country', 'days', 'conflicts', 'group', 'role', 'order'):
                self.assertIn(k, p)
            self.assertGreater(p['cost_estimate'], 0)
            # not due before the deadline; due at it
            self.assertEqual(len([x for x in log if x[1]['id'] == d['id']]), 2)       # offer week + 1, deadline - 1
            self.assertIn(d['id'], [x['id'] for x in c.due(*rec['deadline'])])
            # repeat gates: one decision
            for _ in range(3):
                CA.gate(s.season, s.cursor)
            self.assertEqual(len([x for x in c.decisions.values() if x['key'] == ('invitation', USA)]), 1)
            # save and load, then answer
            dirp = s.dir
            s._commit()
            s.close()
            s = Session.open(dirp)
            c = s.season.career
            self.assertEqual(c.pending(('invitation',))[0]['id'], d['id'])
            act(s, {'type': 'decide', 'decision': d['id'], 'answer': 'accept'}, 'yes')
            self.assertEqual(c.invitation_answers[USA], 'accept')
            with self.assertRaises(CA.CareerError):                   # answered once
                act(s, {'type': 'decide', 'decision': d['id'], 'answer': 'decline'}, 'again')
            v = CA.view(s.season, s.cursor)
            row = next(x for x in v['entries'] if x['event_id'] == USA)
            self.assertEqual(row['status'], 'offered')                 # applied at the deadline, not before
            s.advance_career('next', op_key='go')
            e = next(x for x in s.season.invitations[USA]['entries'] if x['golfer_id'] == c.golfer_id)
            self.assertEqual((e['status'], e['by']), ('accepted', 'player'))
        finally:
            s.close()

    def test_decline_spends_nothing(self):
        s = base()
        try:
            c = career_until(s, at(2028, 30), answer=lambda d: 'decline')
            g = s.season.g[c.golfer_id]
            e = next(x for x in s.season.invitations[USA]['entries'] if x['golfer_id'] == g.id)
            self.assertEqual((e['status'], e['by']), ('declined', 'player'))
            res = s.season.results[USA]
            self.assertNotIn(g.id, {gid for site in res.finish for gid, _, _ in site})
            v = CA.view(s.season, s.cursor)
            row = next(x for x in v['entries'] if x['event_id'] == USA)
            self.assertEqual((row['status'], row['cost_estimate']), ('declined', None))
            rc = c.weekly_recaps.get((2028, s.season.invitations[USA]['week']), {})
            self.assertNotIn(USA, [x['id'] for x in rc.get('events', [])])
        finally:
            s.close()

    def test_auto_setting_needs_no_decision(self):
        s = base()
        log = []
        try:
            act(s, {'type': 'new_career'}, 'n0')
            act(s, {'type': 'invitation_policy', 'value': 'auto'}, 'auto')
            c = s.season.career
            for i in range(400):
                if at(2028, 30)(s):
                    break
                if i == 399:
                    raise AssertionError('not reached')
                s.advance_career('next', op_key=f'b{i}')
                for d in c.pending(CA.OFFER_KINDS):
                    act(s, {'type': 'decide', 'decision': d['id'], 'answer': 'decline'}, f'o{d["id"]}')
                log += [d for d in c.pending(('invitation',))]
                if s.cursor['phase'] == 'week':
                    a = CA.view(s.season, s.cursor).get('advice')
                    if a and c.plan_for(*a['block']) is None:
                        act(s, {'type': 'plan_block', 'block': a['block'], 'version': c.version,
                                'weeks': {w: x['recommended'] for w, x in a['weeks'].items()},
                                'policy': a['policy']}, f'p{i}')
            self.assertEqual(log, [])
            e = next(x for x in s.season.invitations[USA]['entries'] if x['golfer_id'] == c.golfer_id)
            self.assertEqual(e['by'], 'auto')
            self.assertTrue(any(n.get('key') == ('invitation_auto', USA) for n in c.notices))
        finally:
            s.close()


class ReadModels(unittest.TestCase):
    def test_outlook_route_and_read_only(self):
        s = base(weeks=52 + 27)                          # past its deadline (week 27)
        try:
            se = s.season
            se.year = 2028
            rec = se.invitations[USA]
            inv = next(e for e in rec['entries'] if e['status'] == 'accepted')
            g = se.g[inv['golfer_id']]
            s_ = se.cal.by_id['NATIONAL_AMATEUR_USA']
            before = (F.digest(s), pickle.dumps(se.invitations))
            r = EO.invitation(se, g, USA, s_)
            self.assertEqual(r['status'], 'accepted')
            out = next(e for e in se.active_golfers() if e.id not in {x['golfer_id'] for x in rec['entries']})
            self.assertEqual(EO.invitation(se, out, USA, s_)['status'], 'not_invited')
            later = next(e for e in se.cal.editions(2028) if INV.applies(se, e.series) and e.event_id not in
                         se.invitations)
            self.assertEqual(EO.invitation(se, g, later.event_id, later.series)['status'], 'invitations_later')
            self.assertEqual(EO.route(se, {'event_id': USA, 'rule': 'x'}), 'invitation')
            self.assertEqual(EO.route(se, {'event_id': '2028:USA_AMATEUR', 'rule': 'x'}), 'earned')
            self.assertEqual(EO.route(se, {'event_id': '2028:USA_AMATEUR_QUALIFYING', 'rule': 'x'}), 'qualifier')
            self.assertEqual((F.digest(s), pickle.dumps(se.invitations)), before)
        finally:
            s.close()


class EventWeekChecks(unittest.TestCase):
    """The event week's checks and the late places, on the USA national amateur (120 accepted, 30 on stand-by after
    its deadline): a withdrawal for a real reason opens exactly one late place; no withdrawal, no late place."""

    @classmethod
    def setUpClass(cls):
        s = base(weeks=52 + 28)                          # cursor: 2028 week 29 (the event week), not yet played
        cls.blob = pickle.dumps(s.season)
        cls.cursor = dict(s.cursor)
        s.close()

    def fresh(self):
        se = pickle.loads(self.blob)
        rec = se.invitations[USA]
        se.prepare_week(2028, rec['week'])
        se.year = 2028
        return se, rec

    def run_field(self, se, rec, busy=None):
        ed = next(e for e in se.cal.editions(2028) if e.event_id == USA)
        return INV.event_field(se, ed, 2028, rec['week'], busy or defaultdict(set))

    def test_no_withdrawal_no_late_place(self):
        se, rec = self.fresh()
        accepted = [e['golfer_id'] for e in rec['entries'] if e['status'] in INV.TAKEN]
        healthy = all(gid not in se.injured for gid in accepted)
        take = self.run_field(se, rec)
        if healthy:
            withdrawn = [e for e in rec['entries'] if e['status'] == 'withdrawn']
            late = [e for e in rec['entries'] if e.get('late')]
            self.assertEqual(len(late), len(withdrawn))
            self.assertEqual(len(take), len(accepted) - len(withdrawn) + len(late))
            self.assertTrue(all(e['status'] == 'unused' for e in rec['entries']
                                if e['role'] == 'alternate' and e['status'] not in ('entered', 'declined', 'expired')))

    def test_injury_cost_and_clash_withdraw_and_replace_one_for_one(self):
        se, rec = self.fresh()
        acc = [e for e in rec['entries'] if e['status'] in INV.TAKEN]
        a, b, c3 = acc[0]['golfer_id'], acc[1]['golfer_id'], acc[2]['golfer_id']
        se.injured[a] = (se.abs_week(2028, rec['week']) + 3, 'back', 3)
        real = se.spendable
        se.spendable = lambda g, y: -1e9 if g.id == b else real(g, y)
        busy = defaultdict(set)
        busy[c3] = set(rec['days'])
        standby = [e['golfer_id'] for e in rec['entries'] if e['status'] == 'standby']
        take = self.run_field(se, rec, busy)
        why = {e['golfer_id']: e['reason'] for e in rec['entries'] if e['status'] == 'withdrawn'}
        self.assertEqual(why[a], 'injured')
        self.assertEqual(why[b], 'cannot afford the trip now')
        self.assertEqual(why[c3], 'already playing another event those days')
        self.assertIn(rec['series_id'], se.declined[2028][b])
        late = [e['golfer_id'] for e in rec['entries'] if e.get('late')]
        self.assertEqual(len(late), len(why))                            # one late place per withdrawal
        self.assertEqual(late, [gid for gid in standby if gid in late])   # in alternate order
        self.assertTrue(set(late) <= set(take) and not ({a, b, c3} & set(take)))
        self.assertEqual(len(take), len(set(take)))

    def test_rule_declines_injured_or_clashing(self):
        se, rec = self.fresh()
        e = next(x for x in rec['entries'] if x['status'] in INV.TAKEN)
        g = se.g[e['golfer_id']]
        probe = dict(e, status='offered', role='invited')
        se.injured[g.id] = (se.abs_week(rec['year'], rec['week']) + 1, 'wrist', 2)
        self.assertEqual(INV.rule_answer(se, g, rec, probe, 2028), ('decline', 'injured past the event'))
        del se.injured[g.id]
        other = next(r for r in se.invitations.values() if r is not rec and (r['year'], r['week']) ==
                     (rec['year'], rec['week']) and set(r['days']) & set(rec['days']))   # another field those days
        other['entries'].append({'golfer_id': g.id, 'role': 'invited', 'order': 999, 'status': 'accepted',
                                 'answered_at': None, 'by': 'ai', 'reason': None})   # (test set-up: a place held)
        ans, why = INV.rule_answer(se, g, rec, probe, 2028)
        self.assertEqual(ans, 'decline')
        self.assertIn('same days', why)
        self.assertEqual(INV.conflicts(se, g.id, rec)[0]['event_id'], other['event_id'])

    def test_player_without_an_answer_expires(self):
        s = base(weeks=52 + 26)                          # cursor: week 27, the deadline
        try:
            se = s.season
            rec = se.invitations[USA]
            gid = rec['entries'][0]['golfer_id']
            se.prepare_week(2028, 27)
            se.career = CA.Career(gid, 2028, 27, {'rule': 'test'})
            INV.step(se, 2028, 27)
            e = rec['entries'][0]
            self.assertEqual((e['status'], e['reason']), ('expired', 'no answer by the deadline'))
            self.assertTrue(any(x['status'] == 'promoted' for x in rec['entries']))   # its place passed on
        finally:
            s.close()


V4_2028_W26 = '5f21081a7ff6526ab3ea2a929d671ccc891fcc7ba0848315db5804e61f632cc2'   # first v4 golden (2026-11-16)


class Golden(unittest.TestCase):
    """An all-AI v4 world is reproducible (seed 11, scale 0.05, through 2028 week 25: the same frame as the v3 golden
    in tests/test_college_qualifiers.py, which stays unchanged); two runs agree."""

    def test_v4_golden_and_replay(self):
        import tempfile
        digests = []
        for _ in range(2):
            d = Path(tempfile.mkdtemp(prefix='inv_golden_', dir=F.os.environ.get('TMPDIR'))) / 'w'
            _DIRS.append(d.parent)
            s = Session.create(d, seed=11, world=generate_world(year=2027, seed=11, scale=0.05), workers=1,
                               calendar='v4')
            s.advance(52 + 25)
            digests.append(F.digest(s))
            s.close()
        self.assertEqual(digests[0], digests[1])
        self.assertEqual(digests[0], V4_2028_W26)


if __name__ == '__main__':
    unittest.main()
