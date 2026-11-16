"""Coach's advice for the period (golfsim/career_advice.py; docs/career/COACH_ADVICE.md): play / train / rest per open
week from the planner's evidence by fixed rules; read only; the suggestion is a valid plan the engine accepts.

On the career fixture world (seed 11, scale 0.05); each test on its own temporary copy.

Run from the project folder:  python -m unittest tests.test_career_advice -v
"""
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))
import career_fixture as F                                             # noqa: E402
from test_careertest2_fixes import Copy, act, started                  # noqa: E402
from golfsim import career as CA                                       # noqa: E402
from golfsim import career_advice as AD                                # noqa: E402


def at_first_period(s):
    g = started(s)
    s.advance_career('next', op_key='a')
    for d in s.season.career.pending(CA.OFFER_KINDS):
        act(s, {'type': 'decide', 'decision': d['id'], 'answer': 'decline'}, f'o{d["id"]}')
    return g


def event_row(eid, tour, status='open_last_time', cost=100.0, stakes=0, fit=None, selected=False, why=''):
    return {'event_id': eid, 'name': eid, 'eligible': True, 'why': why, 'cost': None if selected else cost, 'tour': tour,
            **({'selected_field': True} if selected else {}),
            'opportunities': [{'status': 'needs_result', 'target': {'label': 'Test Major', 'year': 2028}}] * stakes,
            'course_fit': fit, 'entry_outlook': {'status': status, 'label': status, 'reason': 'test'}}


class Advice(unittest.TestCase):
    def test_read_only_deterministic_and_valid_as_a_plan(self):
        with Copy() as s:
            at_first_period(s)
            before = F.digest(s)
            v1 = CA.view(s.season, s.cursor)
            v2 = CA.view(s.season, s.cursor)
            self.assertEqual(v1['advice'], v2['advice'])
            self.assertEqual(F.digest(s), before)
            a = v1['advice']
            self.assertEqual(sorted(a['weeks']), sorted(v1['week_compare']))
            for w, x in a['weeks'].items():
                self.assertIn(x['recommended']['kind'], ('event', 'train', 'rest'))
                self.assertTrue(x['reasons'])
                self.assertTrue(all({'code', 'text'} <= set(r) for r in x['reasons']))
                for alt in x['alternatives']:
                    self.assertNotEqual(alt['choice']['kind'], x['recommended']['kind'])
                    self.assertTrue(alt['for'] and alt['against'])
            text = str(a).lower()
            for h in ('ceiling', 'potential', '%_chance', 'probability'):
                self.assertNotIn(h, text)
            r = act(s, {'type': 'plan_block', 'block': a['block'], 'version': s.season.career.version,
                        'weeks': {w: x['recommended'] for w, x in a['weeks'].items()}, 'policy': a['policy']}, 'p')
            self.assertTrue(r.get('ok', True))
            plan = s.season.career.plan_for(*a['block'])
            self.assertEqual({str(k): v['kind'] for k, v in plan['weeks'].items() if str(k) in a['weeks']},
                             {w: x['recommended']['kind'] for w, x in a['weeks'].items()})

    def synthetic(self, s, rows, load=None, fatigue=0.0, recaps=()):
        se, c = s.season, s.season.career
        g = se.g[c.golfer_id]
        real = CA.view(se, s.cursor)['week_compare']
        w0 = min(int(w) for w in real)
        comp = {}
        for w in real:
            x = copy.deepcopy(real[w])
            x['play'] = rows.get(int(w), [])
            if load:
                x['load'].update(load)
            comp[w] = x
        saved = (se.fatigue.get(g.id, 0.0), getattr(c, 'weekly_recaps', {}))
        se.fatigue[g.id] = fatigue
        c.weekly_recaps = {(2028, w): {'golfer_id': g.id, 'activity': 'play'} for w in recaps}
        try:
            return AD.advise(se, c, g, s.cursor, comp), g, w0
        finally:
            se.fatigue[g.id], c.weekly_recaps = saved

    def test_rules(self):
        with Copy() as s:
            g = at_first_period(s)
            from golfsim.calendar import TOUR_BY_KEY
            own = TOUR_BY_KEY[g.tour].name
            rows = {w: [event_row(f'2028:A{w}', 'Other Tour'), event_row(f'2028:B{w}', own, stakes=1)]
                    for w in range(1, 5)}
            a, _, w0 = self.synthetic(s, rows)
            first = a['weeks'][str(w0)]
            self.assertEqual(first['recommended']['event_id'], f'2028:B{w0}')     # stakes and own tour count
            self.assertEqual({r['code'] for r in first['reasons']} >= {'stakes', 'pathway', 'entry_outlook'}, True)
            self.assertEqual(sum(1 for x in a['weeks'].values() if x['recommended']['kind'] == 'event'),
                             min(AD.MAX_RECENT, len(a['weeks'])))                   # the load rule
            # behind last edition's cut-off: not suggested
            behind = {w: [event_row(f'2028:C{w}', own, status='behind_last_cutoff', stakes=1)] for w in range(1, 5)}
            a, _, _ = self.synthetic(s, behind)
            self.assertTrue(all(x['recommended']['kind'] != 'event' for x in a['weeks'].values()))
            # tired: rest first; injured: rest
            a, _, w0 = self.synthetic(s, rows, fatigue=0.35)
            self.assertEqual(a['weeks'][str(w0)]['recommended'], {'kind': 'rest'})
            self.assertEqual(a['weeks'][str(w0)]['reasons'][0]['code'], 'fatigue')
            a, _, w0 = self.synthetic(s, rows, load={'injured_until': [2028, 9]})
            self.assertTrue(all(x['recommended'] == {'kind': 'rest'} for x in a['weeks'].values()))
            # recorded play counts toward the load: two tournaments recorded in the stretch -> no more suggested
            a, _, w0 = self.synthetic(s, rows, recaps=(w0, w0 + 1))
            self.assertEqual([x['recommended']['kind'] for w, x in sorted(a['weeks'].items(), key=lambda t: int(t[0]))
                              if int(w) in (w0 + 2, w0 + 3)], ['train', 'train'])
            # unaffordable: never suggested
            pricey = {w: [event_row(f'2028:D{w}', own, cost=1e12, stakes=1)] for w in range(1, 5)}
            a, _, _ = self.synthetic(s, pricey)
            self.assertTrue(all(x['recommended']['kind'] != 'event' for x in a['weeks'].values()))

    def test_training_pick_uses_weakness_room_and_speciality(self):
        with Copy() as s:
            g = at_first_period(s)
            se, c = s.season, s.season.career
            wc = CA.view(se, s.cursor)['week_compare']
            first = wc[min(wc, key=int)]
            sc = {'categories': [{'category': t['category'], 'growth_room': {'label': 'little', 'uncertainty': 'wide'}}
                                 for t in first['train']]}
            weakest = next(t['category'] for t in first['train'] if t['weakest_rank'] == 1)
            cat, reasons, table = AD.train_pick(first, sc, None)
            self.assertEqual(cat, weakest)
            self.assertIn('visible_weakness', [r['code'] for r in reasons])
            second = next(t['category'] for t in first['train'] if t['weakest_rank'] == 2)
            for x in sc['categories']:                                      # room and a specialist coach for #2
                if x['category'] == second:
                    x['growth_room'] = {'label': 'considerable', 'uncertainty': 'moderate'}

            class Coach:
                speciality = second
            cat, reasons, _ = AD.train_pick(first, sc, Coach())
            self.assertEqual(cat, second)
            self.assertEqual({r['code'] for r in reasons}, {'visible_weakness', 'growth_room', 'coach_speciality'})


class ReviewFixes(unittest.TestCase):
    """HAL's review of 80fc9ff/6d0d31e: a long shot is described as one; held places and qualifying the policy enters
    count in the load; qualifying is recognised by the engine's own test, never by text."""

    synthetic = Advice.synthetic

    def test_long_shot_only_with_enough_else_and_said_so(self):
        with Copy() as s:
            g = at_first_period(s)
            from golfsim.calendar import TOUR_BY_KEY
            own = TOUR_BY_KEY[g.tour].name
            weak = {w: [event_row(f'2028:C{w}', own, status='behind_last_cutoff', stakes=1)] for w in range(1, 5)}
            a, _, _ = self.synthetic(s, weak)                                  # -3 + 2 + 1.5 = 0.5: not suggested
            self.assertTrue(all(x['recommended']['kind'] != 'event' for x in a['weeks'].values()))
            strong = {w: [event_row(f'2028:C{w}', own, status='behind_last_cutoff', stakes=1,
                                    fit={'points': 5.0})] for w in range(1, 5)}
            a, _, w0 = self.synthetic(s, strong)                               # + 2.5 course fit: 3.0
            x = a['weeks'][str(w0)]
            self.assertEqual(x['recommended']['kind'], 'event')
            self.assertEqual(x['reasons'][0]['code'], 'long_shot')
            self.assertIn('long shot', x['reasons'][0]['text'])

    def special(self, s, qualifier):
        from golfsim import career as CA
        se = s.season
        return next(ed for ed in se.cal.editions(2028) if se.is_special(ed.series)
                    and CA.entrant_decides(ed.series) == qualifier)

    def test_held_place_and_qualifying_count_in_the_load(self):
        with Copy() as s:
            g = at_first_period(s)
            from golfsim.calendar import TOUR_BY_KEY
            own = TOUR_BY_KEY[g.tour].name
            q = self.special(s, True)
            sel = self.special(s, False)
            rows = {w: [event_row(f'2028:B{w}', own, stakes=1)] for w in range(1, 5)}
            a0, _, w0 = self.synthetic(s, rows)
            held = event_row(sel.event_id, '', status='holds_place', selected=True)
            rows[w0] = rows[w0] + [held]
            a, _, _ = self.synthetic(s, rows)
            x = a['weeks'][str(w0)]
            self.assertNotEqual(x['recommended']['kind'], 'event')
            self.assertEqual(x['reasons'][0]['code'], 'committed')
            n0 = sum(1 for y in a0['weeks'].values() if y['recommended']['kind'] == 'event')
            n = sum(1 for y in a['weeks'].values() if y['recommended']['kind'] == 'event')
            self.assertEqual(n, n0 - 1)                                        # the held place used a load slot
            # qualifying recognised by the engine's test (needs a result there to be worth entering)
            qrow = event_row(q.event_id, '', status='rule_selected', selected=True, stakes=1)
            rows2 = {w: [event_row(f'2028:B{w}', own, stakes=1)] for w in range(1, 5)}
            rows2[w0] = rows2[w0] + [qrow]
            a, _, _ = self.synthetic(s, rows2)
            self.assertEqual(a['policy'], {'selected': 'accept', 'qualifying': 'enter'})
            self.assertEqual(a['weeks'][str(w0)]['reasons'][0]['code'], 'committed')
            # an event the word 'qualifying' in its rule text does not make one
            fake = event_row(sel.event_id, '', status='rule_selected', selected=True, stakes=1,
                             why='qualifying: entrants decide (your period policy)')
            rows3 = {w: [event_row(f'2028:B{w}', own, stakes=1)] for w in range(1, 5)}
            rows3[w0] = rows3[w0] + [fake]
            a, _, _ = self.synthetic(s, rows3)
            self.assertEqual(a['policy']['qualifying'], 'skip')
            x = a['weeks'][str(w0)]
            self.assertIn('possible_selection', [r['code'] for r in x['reasons']])   # said, not counted
            self.assertEqual(x['recommended']['kind'], 'event')


if __name__ == '__main__':
    unittest.main()
