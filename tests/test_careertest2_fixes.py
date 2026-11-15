"""CareerTest2 fixes: coach offers hold a place in the coach's book; truthful entry reasons recorded when the field is
decided; contextual labels for same-named events and qualifying targets.

On the career fixture world (seed 11, scale 0.05). Each test works on its own copy in a temporary folder that is
removed afterwards (career_fixture.copy_of); nothing generated is kept.

Run from the project folder:  python -m unittest tests.test_careertest2_fixes -v
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
from golfsim import event_labels as EL                                 # noqa: E402
from golfsim import staff as ST                                        # noqa: E402
from golfsim.calendar import WorldCalendar                             # noqa: E402
from golfsim.season import Season                                      # noqa: E402
from golfsim.session import Session                                    # noqa: E402

REST = {'kind': 'rest'}


class Copy:
    """A session on a fresh copy of the fixture's first boundary, removed when done."""

    def __enter__(self):
        self.s = Session.open(F.copy_of(F.first_boundary()))
        return self.s

    def __exit__(self, *exc):
        d = self.s.dir
        self.s.close()
        shutil.rmtree(Path(d).parent, ignore_errors=True)


def act(s, body, key, **kw):
    return s.career_action(dict({'schema': CA.SCHEMA}, **body), op_key=key, **kw)


def started(s):
    act(s, {'type': 'new_career'}, 'new')
    return s.season.g[s.season.career.golfer_id]


def free_coach(st, share_room=True):
    """An active coach with room for two more students (and share room), by id."""
    for c in sorted(st.coaches.values(), key=lambda c: c.id):
        n = sum(1 for x in st.coach_of.values() if x == c.id)
        sh = sum(1 for gid, x in st.coach_of.items() if x == c.id and st.deal.get(gid) == 'share')
        if c.status == 'active' and c.capacity >= 4 and n + 2 <= c.capacity and (not share_room or sh + 1 < c.capacity // 3):
            return c
    raise AssertionError('no coach with room')


def fill(season, c, upto, skip):
    """Give coach `c` AI fee students until they have `upto` (test set-up)."""
    st = season.staff
    for g in sorted(season.world.golfers, key=lambda g: g.id):
        if sum(1 for x in st.coach_of.values() if x == c.id) >= upto:
            return
        if g.id != skip and g.lifestyle != 'retired' and g.status in ('pro', 'amateur') and g.id not in st.coach_of:
            st.assign_coach(season, g, c, 'fee', (2028, 1), 'golfer', 'test set-up')


def students(st, c):
    return sum(1 for x in st.coach_of.values() if x == c.id)


def popular_coach(st):
    """The best-known active coach with share room (the one the market's golfers ask first)."""
    for c in sorted(st.coaches.values(), key=lambda c: (-c.reputation, c.id)):
        sh = sum(1 for gid, x in st.coach_of.items() if x == c.id and st.deal.get(gid) == 'share')
        if c.status == 'active' and c.capacity >= 4 and sh + 1 < c.capacity // 3:
            return c
    raise AssertionError('no coach')


class CoachReservation(unittest.TestCase):
    def test_without_the_reservation_the_market_fills_the_offered_place(self):
        # the CareerTest2 defect, reproduced: the offer held nothing and the AI market filled the coach's book
        with Copy() as s:
            g = started(s)
            se, st = s.season, s.season.staff
            c = popular_coach(st)
            fill(se, c, c.capacity - 1, g.id)
            d = se.career.staff_offer(se, 'coach', c, g, 'test offer', (2028, 1), 'share')
            s._commit()
            with mock.patch.object(ST, 'offer_reservations', return_value={}):
                s.advance_career('next', op_key='a')
            self.assertEqual(students(st, c), c.capacity)
            r = act(s, {'type': 'decide', 'decision': d['id'], 'answer': 'accept'}, 'acc')
            self.assertIn('book is now full', r['reason'])

    def test_an_open_offer_holds_its_place_through_the_market(self):
        with Copy() as s:
            g = started(s)
            se, st = s.season, s.season.staff
            c = popular_coach(st)
            fill(se, c, c.capacity - 1, g.id)                      # one place left: the offer's
            d = se.career.staff_offer(se, 'coach', c, g, 'test offer', (2028, 1), 'share')
            self.assertEqual(ST.offer_reservations(se), {c.id: (1, 1)})
            s._commit()
            s.advance_career('next', op_key='a')                   # 1 January: the whole staff market runs
            self.assertLessEqual(students(st, c), c.capacity - 1)  # nobody took the held place
            r = act(s, {'type': 'decide', 'decision': d['id'], 'answer': 'accept'}, 'acc')
            self.assertTrue(r['ok'], r)
            self.assertIs(st.coach(g.id), c)
            self.assertLessEqual(students(st, c), c.capacity)      # never overbooked
            self.assertEqual(ST.offer_reservations(se), {})       # consumed by the acceptance
            with self.assertRaises(CA.CareerError):               # never accepted twice
                act(s, {'type': 'decide', 'decision': d['id'], 'answer': 'accept'}, 'acc2')

    def test_the_market_counts_the_place_as_taken(self):
        # the market's own book: the offer made inside the market (approach) holds the place for the rest of it
        with Copy() as s:
            g = started(s)
            se, st = s.season, s.season.staff
            c = free_coach(st)
            students_, shares = {c.id: 1}, {c.id: 0}
            ok = ST.approach(se, c, g, 'scouted', (2028, 1), __import__('random').Random(1), students_, shares)
            self.assertFalse(ok)                                   # the player answers later
            self.assertEqual((students_[c.id], shares[c.id]), (2, 1))
            ST.approach(se, c, g, 'scouted again', (2028, 1), __import__('random').Random(1), students_, shares)
            self.assertEqual((students_[c.id], shares[c.id]), (2, 1))   # one offer, one place

    def test_share_quota_and_releases(self):
        with Copy() as s:
            g = started(s)
            se, st = s.season, s.season.staff
            c = free_coach(st)
            d = se.career.staff_offer(se, 'coach', c, g, 'test offer', (2028, 1), 'share')
            self.assertEqual(ST.offer_reservations(se)[c.id], (1, 1))
            act(s, {'type': 'decide', 'decision': d['id'], 'answer': 'decline'}, 'dec')
            self.assertEqual(ST.offer_reservations(se), {})       # released on decline
            d2 = se.career.staff_offer(se, 'coach', c, g, 'again', (2028, 2), 'fee')
            self.assertEqual(ST.offer_reservations(se)[c.id], (1, 0))   # a fee offer holds no share place
            c.status = 'retired'
            self.assertEqual(ST.offer_reservations(se), {})       # the coach stopped working: nothing held
            c.status = 'active'
            st.assign_coach(se, g, c, 'fee', (2028, 2), 'golfer', 'test set-up')
            self.assertEqual(ST.offer_reservations(se), {})       # already their coach: not counted twice
            self.assertEqual(d2['status'], 'pending')

    def test_a_failed_acceptance_keeps_the_old_coach_and_says_why(self):
        with Copy() as s:
            g = started(s)
            se, st = s.season, s.season.staff
            old = free_coach(st)
            st.assign_coach(se, g, old, 'fee', (2028, 1), 'golfer', 'test set-up')
            c = next(x for x in sorted(st.coaches.values(), key=lambda x: x.id)
                     if x.status == 'active' and x is not old)
            d = se.career.staff_offer(se, 'coach', c, g, 'test offer', (2028, 1), 'share')
            d['payload'].pop('reserved')                           # an offer an earlier build made (no place held)
            fill(se, c, c.capacity, g.id)
            r = act(s, {'type': 'decide', 'decision': d['id'], 'answer': 'accept'}, 'acc')
            self.assertFalse(r['ok'])
            self.assertIn('book is now full', r['reason'])
            self.assertIn('earlier build', r['reason'])
            self.assertIs(st.coach(g.id), old)                     # nothing ended
            self.assertEqual(d['status'], 'withdrawn')

    def test_all_ai_worlds_have_no_reservations(self):
        with Copy() as s:
            self.assertIsNone(s.season.career)
            self.assertEqual(ST.offer_reservations(s.season), {})


class EntryReasons(unittest.TestCase):
    def plan_eligible(self, s, g):
        """Rest until a planning period with an eligible ordinary event; plan it. Returns (year, week, event id)."""
        se = s.season
        for n in range(30):
            out = s.advance_career('next', op_key=f'n{n}')
            for d in se.career.pending(CA.OFFER_KINDS):
                act(s, {'type': 'decide', 'decision': d['id'], 'answer': 'decline'}, f'o{d["id"]}')
            for d in se.career.pending(('plan',)):
                y, w0 = d['payload']['block']
                pl = CA.planner(se, s.cursor, y, w0)
                weeks = {str(w['week']): REST for w in pl['weeks']}
                pick = None
                for w in pl['weeks']:
                    for e in w['events']:
                        sid = e['event_id'].split(':', 1)[1]
                        if e['eligible'] and not se.is_special(se.cal.by_id[sid]) and pick is None:
                            pick = (y, w['week'], e['event_id'])
                if pick:
                    weeks[str(pick[1])] = {'kind': 'event', 'event_id': pick[2], 'fallback': {'kind': 'rest'}}
                act(s, {'type': 'plan_block', 'block': [y, w0], 'version': se.career.version, 'weeks': weeks,
                        'policy': {'selected': 'accept', 'qualifying': 'skip'}}, f'p{y}{w0}')
                if pick:
                    return pick
        raise AssertionError('no eligible ordinary event')

    def test_a_planned_entry_is_recorded_as_decided(self):
        with Copy() as s:
            g = started(s)
            y, w, eid = self.plan_eligible(s, g)
            while (s.cursor['year'], s.cursor['week']) <= (y, w):
                s.advance_career('next', op_key=f'g{s.cursor["week"]}')
                for d in s.season.career.pending(('plan',)):
                    b = d['payload']['block']
                    act(s, {'type': 'plan_block', 'block': b, 'version': s.season.career.version,
                            'weeks': {str(x): REST for x in CA.open_weeks(s.cursor, b[1])},
                            'policy': {'selected': 'accept', 'qualifying': 'skip'}}, f'q{b}')
            e = CA.week_entry(s.season, s.season.career, y, w)
            self.assertTrue(e['recorded'])
            self.assertEqual(e['event'], eid)
            self.assertIn(e['code'], ('entered', 'school_lineup', 'field_full', 'quota'))
            self.assertEqual(e['text'], CA.ENTRY_TEXT[e['code']])
            self.assertTrue(1 <= e['position'] <= e['applicants'])
            self.assertGreater(e['capacity'], 0)
            if e['code'] == 'entered':
                self.assertEqual(e['entered']['event'], eid)
            rec = s.season.career.weekly_recaps[(y, w)]
            self.assertEqual(rec['entry']['code'], e['code'])     # kept with the week's recap

    def test_entry_codes(self):
        self.assertEqual(Season.entry_code(True, True, 50, 10), 'entered')
        self.assertEqual(Season.entry_code(False, True, 3, 10), 'school_lineup')   # the lineup, not capacity
        self.assertEqual(Season.entry_code(False, False, 3, 10), 'quota')
        self.assertEqual(Season.entry_code(False, False, 11, 10), 'field_full')

    def test_why_a_planned_entry_could_not_stand(self):
        with Copy() as s:
            g = started(s)
            se = s.season
            y, w, eid = self.plan_eligible(s, g)
            ed = next(e for e in se.cal.editions(y) if e.event_id == eid)
            other = next(e for e in se.cal.editions(y) if e.week == w and e.event_id != eid)
            cases = [
                ({'evs': [], 'days': frozenset()}, None, 'not_eligible'),
                ({'evs': [ed], 'days': frozenset(ed.series.day_set)}, None, 'clash'),
                ({'evs': [ed], 'days': frozenset(), 'money': 0.0}, None, 'cost'),
                ({'evs': [ed], 'days': frozenset()}, (other.event_id, 'selected'), 'superseded'),
            ]
            for kw, entered, code in cases:
                se.career.entry_evidence = {}
                se._week_entered.clear()
                if entered:
                    se._week_entered[g.id] = entered
                se._career_entry(se.career, g, y, w, [], {}, kw['evs'], kw['days'], kw.get('money'))
                e = CA.week_entry(se, se.career, y, w)
                self.assertEqual(e['code'], code)
                self.assertEqual(e['text'], CA.ENTRY_TEXT[code])
                self.assertIsNone(e['position'])                   # no entry order was decided
                if code == 'superseded':
                    self.assertEqual(e['by'], other.event_id)
            se._week_entered.clear()

    def test_a_declined_rule_selected_place_is_the_players_policy(self):
        with Copy() as s:
            g = started(s)
            se = s.season
            s.advance_career('next', op_key='a')
            y0, w0 = s.cursor['year'], s.cursor['week']
            act(s, {'type': 'plan_block', 'block': [y0, 1], 'version': se.career.version,
                    'weeks': {str(x): REST for x in CA.open_weeks(s.cursor, 1)},
                    'policy': {'selected': 'decline', 'qualifying': 'skip'}}, 'p')
            ser = next(x for x in se.cal.series if x.category == 'elite_amateur')
            se.year, se.week = y0, w0
            from collections import defaultdict
            self.assertFalse(se.available(g.id, ser, defaultdict(set)))
            e = CA.week_entry(se, se.career, y0, w0)
            self.assertEqual(e['declined'], [ser.series_id])
            self.assertIsNone(e['position'])                       # no hypothetical selection rank

    def test_older_weeks_speak_only_from_the_seasons_log(self):
        with Copy() as s:
            g = started(s)
            se = s.season
            se.access_log[2028][g.id].append((7, 'not selected for the college lineup', '2028:CO_US_D1_05', None))
            se.access_log[2028][g.id].append((8, 'shut out: every acceptable field full', '2028:AM_X', None))
            e7 = CA.week_entry(se, se.career, 2028, 7)
            self.assertEqual((e7['recorded'], e7['code'], e7['position']), (False, 'school_lineup', None))
            self.assertEqual(e7['text'], "not selected for your school's college lineup")
            e8 = CA.week_entry(se, se.career, 2028, 8)
            self.assertEqual((e8['code'], e8['capacity']), ('field_full', None))
            e9 = CA.week_entry(se, se.career, 2028, 9)
            self.assertEqual((e9['recorded'], e9['code'], e9['access']), (False, None, None))


class Labels(unittest.TestCase):
    def test_same_named_events_are_told_apart_and_ids_are_kept(self):
        for v in ('v1', 'v2'):
            cal = WorldCalendar(seed=11, version=v)
            by = {s.series_id: s for s in cal.series}
            self.assertEqual(by['NATIONAL_AMATEUR_USA'].name, by['USA_AMATEUR'].name)   # names (history) unchanged
            nat, am = EL.label(cal, 'NATIONAL_AMATEUR_USA'), EL.label(cal, 'USA_AMATEUR')
            self.assertNotEqual(nat, am)
            self.assertIn(f'week {by["NATIONAL_AMATEUR_USA"].week}', nat)
            self.assertIn('week 33', am)
            labels = [EL.label(cal, s.series_id) for s in cal.series]
            self.assertEqual(len(labels), len(set(labels)))       # every label in the calendar is unique
            self.assertEqual(EL.label(cal, 'USA_OPEN'), by['USA_OPEN'].name)   # unique names stay as they are

    def test_the_usa_amateur_qualifier_feeds_the_usa_amateur(self):
        for seed in (11, 120401):
            cal = WorldCalendar(seed=seed, version='v2')
            by = {s.series_id: s for s in cal.series}
            t = EL.target(cal, 'USA_AMATEUR_QUALIFYING')
            self.assertEqual((t['id'], t['week']), ('USA_AMATEUR', 33))
            self.assertLess(by['USA_AMATEUR_QUALIFYING'].week, t['week'])            # before its target
            self.assertNotEqual(t['id'], 'NATIONAL_AMATEUR_USA')
            self.assertIn('match play', t['label'])
            for sid in [s.series_id for s in cal.series]:
                x = EL.target(cal, sid)
                if x is not None:
                    self.assertLess(by[sid].week, x['week'], sid)  # every qualifier comes before what it feeds
            self.assertIsNone(EL.target(cal, 'NATIONAL_AMATEUR_USA'))


if __name__ == '__main__':
    unittest.main()
