"""The year's thirteen four-week periods stay fixed (W1-4, W5-8, ... W49-52) through interruptions: a decision
stopping play mid-period keeps the period, its committed plan and the weeks already played; the remaining weeks
resume after the answer; the period gets one full factual recap. Nothing a week does happens twice.

On the career fixture world (seed 11, scale 0.05).

Run from the project folder:  python -m unittest tests.test_period_cadence -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))
import career_fixture as F                                             # noqa: E402
from test_careertest2_fixes import Copy, act, started                 # noqa: E402
from golfsim import career as CA                                       # noqa: E402
from golfsim.session import Session                                    # noqa: E402

TRAIN = {'kind': 'train', 'category': 'putting'}


def run_period(s, interrupt_at=None, reload_at_stop=False):
    """Plan W1-4 (training) and play the period; with `interrupt_at`, a decision due that week (a job offer, test
    set-up) appears as the week before it is played, stopping play mid-period."""
    se = s.season
    s.advance_career('next', op_key='a')                               # 1 January
    for d in se.career.pending(CA.OFFER_KINDS):
        act(s, {'type': 'decide', 'decision': d['id'], 'answer': 'decline'}, f'o{d["id"]}')
    act(s, {'type': 'plan_block', 'block': [2028, 1], 'version': se.career.version,
            'weeks': {str(w): TRAIN for w in CA.open_weeks(s.cursor, 1)},
            'policy': {'selected': 'accept', 'qualifying': 'skip'}}, 'plan')
    real = Session._part_play
    stops = 0

    def play(self):
        week = self.state['cursor']['week']
        r = real(self)
        if interrupt_at is not None and week == interrupt_at - 1:
            self.season.career.job_offer(2028, interrupt_at, 4)
        return r
    with mock.patch.object(Session, '_part_play', play):
        for n in range(8):
            out = s.advance_career('period', op_key=f'n{n}')
            pend = s.season.career.pending(('job',))
            if pend:
                stops += 1
                if reload_at_stop:
                    d0 = s.dir
                    s.close()
                    s = Session.open(d0)
                for d in s.season.career.pending(('job',)):
                    act(s, {'type': 'decide', 'decision': d['id'], 'answer': 'decline'}, f'x{d["id"]}')
                continue
            if (s.cursor['year'], s.cursor['week']) > (2028, 4) or s.season.career.pending(('plan',)):
                break
    return s, stops


class Cadence(unittest.TestCase):
    def test_an_interruption_keeps_the_period(self):
        with Copy() as s:
            started(s)
            s, stops = run_period(s, interrupt_at=3, reload_at_stop=True)
            self.assertEqual(stops, 1)
            c = s.season.career
            self.assertIn((2028, 1), c.plans)                          # the period's plan, kept
            recaps = [r for r in CA.period_recaps(c) if (r['year'], r['start_week']) == (2028, 1)]
            self.assertEqual(len(recaps), 1)                           # one recap for the period
            r = recaps[0]
            self.assertTrue(r['complete'])
            self.assertEqual(r['recorded_weeks'], [1, 2, 3, 4])        # each week once
            self.assertEqual((r['start_week'], r['end_week']), (1, 4))
            gid = c.golfer_id
            self.assertEqual(s.season.activity_counts[2028][gid]['train'], 4)   # trained four times, not more
            s.advance_career('next', op_key='after')
            self.assertEqual(c.pending(('plan',))[0]['payload']['block'], [2028, 5])   # the next period: W5-8

    def test_the_interrupted_world_is_the_uninterrupted_one(self):
        with Copy() as a, Copy() as b:
            started(a)
            started(b)
            a, _ = run_period(a, interrupt_at=3, reload_at_stop=True)
            b, _ = run_period(b)
            # (the interrupted one recorded and declined an offer: the same world otherwise)
            self.assertEqual(F.digest(a), F.digest(b))
            ga, gb = a.season.g[a.season.career.golfer_id], b.season.g[b.season.career.golfer_id]
            self.assertEqual((round(ga.cash, 4), ga.attrs), (round(gb.cash, 4), gb.attrs))   # fees and training once

if __name__ == '__main__':
    unittest.main()
