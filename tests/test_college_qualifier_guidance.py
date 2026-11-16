"""v3 college qualifiers in the entry outlook and the coach's advice (golfsim/entry_outlook.college_qualifier,
golfsim/career_advice.py): a place the rules give now (`assured_by_rules`) or give unless the golfer qualifies in an
earlier qualifier first (`unless_qualified_earlier`, a future assumption, never a promise), counted in the advice's
load; no change to field rules, admission, random draws or defaults.

The reproduction (HAL / Claude audit of 6ad8d9d): world seed 23, scale 0.05, calendar v3; a fresh career at 1 January
2028 (a US college golfer); advice applied for periods 1 and 5; in period 9-12 the advice suggested an ordinary event in
week 12, the week of COLLEGE_QUALIFIER_3 (which the rules enter every not-yet-qualified US college golfer in), and week 9
next to three qualifier weeks.

Run from the project folder:  python -m unittest tests.test_college_qualifier_guidance -v
"""
from __future__ import annotations

import pickle
import shutil
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))
import career_fixture as F                                             # noqa: E402
from golfsim import career as CA                                       # noqa: E402
from golfsim import career_advice as AD                                # noqa: E402
from golfsim import entry_outlook as EO                                # noqa: E402
from golfsim.population import generate_world                          # noqa: E402
from golfsim.session import Session                                    # noqa: E402

_BASE = {}
_DIRS = []


def base(calendar='v3'):
    """A session directory at 1 January 2028 (seed 23, scale 0.05), built once per calendar and copied."""
    if calendar not in _BASE:
        d = F.tmpdir('cq_base_') / 'w'
        _DIRS.append(d.parent)
        s = Session.create(d, seed=23, world=generate_world(year=2027, seed=23, scale=0.05), workers=1,
                           calendar=calendar)
        s.advance(52)
        s.close()
        _BASE[calendar] = d
    d = F.tmpdir('cq_') / 'w'
    _DIRS.append(d.parent)
    shutil.copytree(_BASE[calendar], d)
    return Session.open(d)


def tearDownModule():
    for d in _DIRS:
        shutil.rmtree(d, ignore_errors=True)


def act(s, body, key):
    return s.career_action(dict({'schema': CA.SCHEMA}, **body), op_key=key)


def to_period_9(s):
    """The reproduction: a fresh career, the advice applied as given for periods 1 and 5, stopping at period 9's plan."""
    act(s, {'type': 'new_career'}, 'new')
    c = s.season.career
    for i in range(3):
        s.advance_career('next', op_key=f'a{i}')
        for d in c.pending(CA.OFFER_KINDS):
            act(s, {'type': 'decide', 'decision': d['id'], 'answer': 'decline'}, f'o{d["id"]}')
        v = CA.view(s.season, s.cursor)
        a = v['advice']
        if a['block'] == [2028, 9]:
            return v
        act(s, {'type': 'plan_block', 'block': a['block'], 'version': c.version,
                'weeks': {w: x['recommended'] for w, x in a['weeks'].items()}, 'policy': a['policy']}, f'p{i}')
    raise AssertionError('period 9 not reached')


def q(n):
    return f'2028:COLLEGE_QUALIFIER_{n}'


def outlook(se, g, n, week):
    return EO.outlook(se, g, 2028, week, {'event_id': q(n), 'rule': 'field chosen by the event\'s rules'}, held={})


def qweek(se, n):
    return next(e.week for e in se.cal.editions(2028) if e.event_id == q(n))


class Reproduction(unittest.TestCase):
    def test_seed23_period_9_to_12(self):
        s = base()
        try:
            v = to_period_9(s)
            se, c = s.season, s.season.career
            g = se.g[c.golfer_id]
            self.assertIn(g.tour, se.US_COLLEGE)
            st = {r['event_id']: r['entry_outlook']['status'] for x in v['week_compare'].values() for r in x['play']}
            self.assertEqual((st[q(1)], st[q(2)], st[q(3)]),
                             ('assured_by_rules', 'unless_qualified_earlier', 'unless_qualified_earlier'))
            a = v['advice']
            qweeks = {int(w) for w, x in v['week_compare'].items()
                      for r in x['play'] if r['event_id'].split(':')[1].startswith('COLLEGE_QUALIFIER')}
            self.assertEqual(qweeks, {10, 11, 12})
            rec = {int(w): x for w, x in a['weeks'].items()}
            for w in qweeks:                                    # no ordinary event suggested in a qualifier week
                self.assertNotEqual(rec[w]['recommended']['kind'], 'event', w)
                self.assertEqual(rec[w]['reasons'][0]['code'], 'committed')
            self.assertIn('the rules enter you and the suggested policy accepts it', rec[10]['reasons'][0]['text'])
            for w in (11, 12):
                self.assertIn('unless you qualify in an earlier qualifier first', rec[w]['reasons'][0]['text'])
                self.assertIn('not certain', rec[w]['reasons'][0]['text'])
            # nothing suggested beside them beyond the load: only the rules' own entries can fill a window
            events = {w for w, x in rec.items() if x['recommended']['kind'] == 'event'}
            for start in range(6, 13):
                win = [x for x in events | qweeks if start <= x < start + AD.WINDOW]
                self.assertLessEqual(len([x for x in win if x in events]) + len([x for x in win if x in qweeks]),
                                     max(AD.MAX_RECENT, len([x for x in win if x in qweeks])))
            self.assertNotIn(9, events)                          # week 9 sits next to weeks 10-12
            self.assertEqual(a['policy']['selected'], 'accept')
            self.assertIn('alone can exceed it', a['note'])
        finally:
            s.close()


class Cases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = base()
        cls.se = cls.s.season
        cls.se.year = 2028
        us = [g for g in cls.se.active_golfers() if g.tour in cls.se.US_COLLEGE]
        cls.us = us
        cls.other = next(g for g in cls.se.active_golfers() if g.tour not in cls.se.US_COLLEGE)

    @classmethod
    def tearDownClass(cls):
        cls.s.close()

    def test_before_any_qualifier_first_assured_later_contingent(self):
        g = self.us[0]
        self.assertEqual(outlook(self.se, g, 1, qweek(self.se, 1))['status'], 'assured_by_rules')
        for n, pending in ((2, '1'), (3, '1, 2'), (4, '1, 2, 3')):
            r = outlook(self.se, g, n, qweek(self.se, n))
            self.assertEqual(r['status'], 'unless_qualified_earlier')
            self.assertIn(f'{pending} come', r['reason'])
            self.assertNotIn('assured', (r['reason'] + r['uncertainty']).lower())
            self.assertIn('policy', r['uncertainty'])

    def test_not_us_college_or_retired(self):
        r = outlook(self.se, self.other, 1, qweek(self.se, 1))
        self.assertEqual(r['status'], 'not_eligible')
        g = self.us[1]
        life = g.lifestyle
        g.lifestyle = 'retired'
        try:
            self.assertEqual(outlook(self.se, g, 1, qweek(self.se, 1))['status'], 'not_eligible')
        finally:
            g.lifestyle = life
        tour = g.tour
        g.tour = self.other.tour                                       # (left US college golf)
        try:
            self.assertEqual(outlook(self.se, g, 1, qweek(self.se, 1))['status'], 'not_eligible')
        finally:
            g.tour = tour

    def test_injured_that_week(self):
        g = self.us[2]
        w = qweek(self.se, 1)
        saved = self.se.injured.get(g.id)
        self.se.injured[g.id] = (self.se.abs_week(2028, w) + 1,) + tuple(saved[1:] if saved else ())
        try:
            self.assertEqual(outlook(self.se, g, 1, w)['status'], 'injured')
        finally:
            if saved is None:
                del self.se.injured[g.id]
            else:
                self.se.injured[g.id] = saved

    def test_read_only_no_draws_and_same_for_any_golfer(self):
        before = pickle.dumps((self.se.results, self.se.injured, self.se.rng.getstate()
                               if hasattr(self.se, 'rng') else None, F.digest(self.s)))
        first = [[outlook(self.se, g, n, qweek(self.se, n)) for n in (1, 2, 3, 4)] for g in self.us]
        again = [[outlook(self.se, g, n, qweek(self.se, n)) for n in (1, 2, 3, 4)] for g in self.us]
        self.assertEqual(first, again)
        self.assertEqual(pickle.dumps((self.se.results, self.se.injured, self.se.rng.getstate()
                                       if hasattr(self.se, 'rng') else None, F.digest(self.s))), before)
        # the outlook reads no career: the same for a golfer whoever controls them (none here; one below)
        self.assertIsNone(self.se.career)
        g = self.us[0]
        plain = [outlook(self.se, g, n, qweek(self.se, n)) for n in (1, 2)]
        self.se.career = CA.Career(g.id, 2028, 1, {'rule': 'test'})
        try:
            self.assertEqual([outlook(self.se, g, n, qweek(self.se, n)) for n in (1, 2)], plain)
        finally:
            self.se.career = None


class AfterQualifierOne(unittest.TestCase):
    """Played through qualifier 1 (all AI): its qualifiers are no longer entered; the others are assured for qualifier
    2 and contingent for 3 and 4."""

    def test_already_qualified_and_next_assured(self):
        s = base()
        try:
            se = s.season
            w1 = qweek(se, 1)
            s.advance(w1 - s.cursor['week'] + 1)
            self.assertIn(q(1), se.results)
            done = se.college_qualified(2028, 1)
            self.assertTrue(done)
            gq = se.g[next(iter(done))]
            r = outlook(se, gq, 2, qweek(se, 2))
            self.assertEqual(r['status'], 'not_eligible')
            self.assertIn('Already qualified', r['reason'])
            g = next(x for x in se.active_golfers() if x.tour in se.US_COLLEGE and x.id not in done
                     and CA.injured_until(se, x.id, 2028, qweek(se, 2)) is None)
            self.assertEqual(outlook(se, g, 2, qweek(se, 2))['status'], 'assured_by_rules')
            self.assertEqual(outlook(se, g, 3, qweek(se, 3))['status'], 'unless_qualified_earlier')
            self.assertEqual(outlook(se, g, 4, qweek(se, 4))['status'], 'unless_qualified_earlier')
        finally:
            s.close()


class Policy(unittest.TestCase):
    """The place needs the period policy to accept rule-selected places (the engine's rule, unchanged): with 'decline'
    the career golfer is not in the qualifier's field; with 'accept' they are."""

    def field_with(self, selected):
        s = base()
        try:
            v = to_period_9(s)
            c = s.season.career
            a = v['advice']
            act(s, {'type': 'plan_block', 'block': a['block'], 'version': c.version,
                    'weeks': {w: x['recommended'] for w, x in a['weeks'].items()},
                    'policy': dict(a['policy'], selected=selected)}, 'pp')
            while (s.cursor['year'], s.cursor['week']) <= (2028, 10):
                s.advance_career('next', op_key=f'n{s.cursor["week"]}')
                for d in c.pending(CA.OFFER_KINDS):
                    act(s, {'type': 'decide', 'decision': d['id'], 'answer': 'decline'}, f'o{d["id"]}')
                if c.pending(('plan',)):
                    break
            res = s.season.results.get(q(1))
            return c.golfer_id in {gid for site in res.finish for gid, _, _ in site}
        finally:
            s.close()

    def test_accept_plays_decline_does_not(self):
        self.assertTrue(self.field_with('accept'))
        self.assertFalse(self.field_with('decline'))


class Legacy(unittest.TestCase):
    def test_v2_unchanged(self):
        s = base('v2')
        try:
            se = s.season
            se.year = 2028
            self.assertFalse(se.cal.spec.college_qualifiers)
            g = next(x for x in se.active_golfers() if x.tour == 'CO_US_D1')
            ed = next(e for e in se.cal.editions(2028) if e.series.category == 'college_postseason')
            sid = ed.series.series_id
            self.assertIsNone(EO.college_qualifier(se, g, sid, 2028, ed.week))
            self.assertIsNone(EO.college_qualifier(se, g, 'COLLEGE_QUALIFIER_1', 2028, ed.week))
            r = EO.outlook(se, g, 2028, ed.week, {'event_id': ed.event_id, 'rule': 'x'}, held={})
            self.assertEqual(r['status'], 'rule_selected')
        finally:
            s.close()


if __name__ == '__main__':
    unittest.main()
