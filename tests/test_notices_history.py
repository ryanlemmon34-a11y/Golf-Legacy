"""Field history (how each ordinary field closed, by edition) and notices of newly held places at period starts.

Run from the project folder:  python -m unittest tests.test_notices_history -v
"""
from __future__ import annotations

import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))
import career_fixture as F                                             # noqa: E402
from test_careertest2_fixes import Copy, act, started                 # noqa: E402
from golfsim import career as CA                                       # noqa: E402
from golfsim import decision_support as DS                             # noqa: E402
from golfsim import opportunities as O                                 # noqa: E402
from golfsim.session import Session                                    # noqa: E402


class FieldHistory(unittest.TestCase):
    def test_last_edition_as_history(self):
        with Copy() as s:
            se = s.season
            cut = se.field_cutoffs[2027]                                # recorded while 2027 was played
            self.assertTrue(cut)
            sid, rec = next((k, v) for k, v in sorted(cut.items()) if v['full'])
            self.assertGreaterEqual(rec['asked'], rec['admitted'] - rec['late_fills'])
            self.assertLessEqual(rec['admitted'], rec['capacity'])
            h = O.field_history(se, sid, 2028)
            self.assertEqual((h['year'], h['capacity'], h['asked'], h['full']), (2027, rec['capacity'], rec['asked'],
                                                                                  True))
            self.assertIn('History', h['note'])
            self.assertIsInstance(h['closed_at'], str)                  # the entry class the field closed at
            self.assertIsNone(O.field_history(se, sid, 2027))           # nothing before the first season
            self.assertIsNone(O.field_history(se, 'NO_SUCH_SERIES', 2028))
            for k in ('chance', 'probability'):
                self.assertNotIn(k, ' '.join(map(str, h.values())).lower())

    def test_the_week_comparison_carries_it_and_reads_change_nothing(self):
        with Copy() as s:
            g = started(s)
            se, c = s.season, s.season.career
            s.advance_career('next', op_key='a')
            before, state = F.digest(s), random.getstate()
            w = DS.week_compare(se, c, g, 2028, 1)
            self.assertTrue(all('last_edition' in p for p in w['play']))
            self.assertTrue(any(p['last_edition'] for p in w['play']))
            self.assertEqual((F.digest(s), random.getstate()), (before, state))


class SecuredNotices(unittest.TestCase):
    def test_a_newly_held_place_is_noticed_once(self):
        with Copy() as s:
            g = started(s)
            se = s.season
            se.ctx.results[('TOUR_MASTERS', 2027)] = {0: [(g.id, 1)]}  # (test set-up: a recorded Masters win)
            s._commit()
            s.advance_career('next', op_key='a')
            notes = [n for n in se.career.notices if n['kind'] == 'secured']
            self.assertTrue(notes)
            self.assertTrue(any('Tour Masters' in n['text'] for n in notes))
            self.assertTrue(all('recorded place, not an estimate' in n['text'] for n in notes))
            n0 = len(notes)
            for d in se.career.pending(CA.OFFER_KINDS):
                act(s, {'type': 'decide', 'decision': d['id'], 'answer': 'decline'}, f'o{d["id"]}')
            d0 = s.dir
            s.close()
            s2 = Session.open(d0)                                       # reloaded and asked again: no repeat
            s2.advance_career('next', op_key='b')
            s2.advance_career('next', op_key='c')
            notes2 = [n for n in s2.season.career.notices if n['kind'] == 'secured']
            self.assertEqual(len(notes2), n0)
            self.assertTrue(s2.season.career.secured_seen)
            s2.close()
            s.dir = d0

    def test_nothing_held_nothing_noticed(self):
        with Copy() as s:
            started(s)
            s.advance_career('next', op_key='a')
            self.assertFalse([n for n in s.season.career.notices if n['kind'] == 'secured'])


if __name__ == '__main__':
    unittest.main()
