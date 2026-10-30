"""The "no starts" explanation from the weekly evidence (roadmap v14): every contributing barrier and choice with
its weeks; a season with unaffordable or full-field weeks is never called voluntary; the season page shows the
week-by-week ledger for any archived season (older seasons included, from the weeks they recorded).

Named regression examples from the Test1 10.29 review (not to force either golfer into a tournament):
Kaito Ogawa's 2035 Challenger Japan season (28 unaffordable weeks, 2 full-field weeks, training, work and
declines) and Agustin Sanchez's full-time amateur season (11 unaffordable weeks, 41 with no suitable event).

Run from the project folder:  python -m unittest tests.test_access_ledger -v
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
from golfsim import access as ACC                                        # noqa: E402

OGAWA = {'could not afford any event': 28, 'shut out: every acceptable field full': 2, 'chose to work': 8,
         'chose to train': 10, 'declined the events on offer': 4}
SANCHEZ = {'could not afford any event': 11, 'no suitable event scheduled': 41}


class Ledger(unittest.TestCase):
    def test_mixed_barriers_and_choices_are_never_voluntary(self):
        kind, text = ACC.zero_start_summary(OGAWA, 0, 'full_time')
        self.assertEqual(kind, 'mixed')
        self.assertNotIn('chose not to play', text)
        for part in ('unaffordable 28', 'not admitted 2', 'declined 4', 'trained, rested or worked 18', 'out of 52'):
            self.assertIn(part, text)

    def test_barriers_only(self):
        kind, text = ACC.zero_start_summary(SANCHEZ)
        self.assertEqual(kind, 'barriers')
        self.assertIn('no suitable event 41', text)
        self.assertIn('unaffordable 11', text)

    def test_choices_only_and_part_timers(self):
        self.assertEqual(ACC.zero_start_summary({'chose to train': 52})[0], 'choices')
        kind, text = ACC.zero_start_summary({'chose to work': 30, 'chose to rest': 22}, 0, 'part_time')
        self.assertTrue(text.startswith('part-timer: chose not to play'))
        self.assertEqual(ACC.zero_start_summary({'injured': 40, 'chose to rest': 12})[0], 'injured')
        self.assertEqual(ACC.zero_start_summary({})[0], 'not recorded')

    def test_ledger_counts(self):
        lg = ACC.ledger({**OGAWA, 'played: first choice': 0})
        self.assertEqual((lg['weeks'], lg['barrier'], lg['choice'], lg['played']), (52, 30, 22, 0))
        self.assertEqual(lg['groups'], {'not admitted': 2, 'unaffordable': 28, 'declined': 4,
                                        'trained, rested or worked': 18})


class SeasonLedger(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from golfsim.population import generate_world
        from golfsim.session import Session
        cls.tmp = Path(tempfile.mkdtemp())
        s = Session.create(cls.tmp / 'w', seed=43, workers=1, world=generate_world(seed=43, scale=0.03))
        s.advance(53)
        s.close()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_the_season_explains_no_starts_from_its_weeks(self):
        from golfsim.session import Session
        s = Session.open(self.tmp / 'w', workers=1)
        self.addCleanup(s.close)
        se = s.season
        gid = next(g.id for g in se.active_golfers() if g.status == 'pro')
        se.week_access[2027][gid] = dict(OGAWA)
        row = {'injury_weeks': 0}
        text = se.zero_start_reason(gid, 2027, row)
        self.assertEqual(row['zero_start_kind'], 'mixed')
        self.assertNotIn('chose not to play', text)
        se.week_access[2027][gid] = dict(SANCHEZ)
        self.assertIn('kept out by barriers', se.zero_start_reason(gid, 2027, row))

    def test_every_season_page_shows_the_week_by_week_ledger(self):
        from golfsim.archive import Archive
        import observer as O
        with Archive(self.tmp / 'w' / 'archive') as a:
            careers = a.year(2027)['careers']
            for pid, r in careers.items():                                  # the weeks add up for everyone
                lg = ACC.ledger(r['access'])
                self.assertEqual(lg['played'] + lg['injured'] + lg['barrier'] + lg['choice'], lg['weeks'], pid)
                if r.get('events'):
                    self.assertGreater(lg['played'], 0, pid)
            pid = next(p for p, r in careers.items() if ACC.ledger(r['access'])['barrier'])
        w = O.World(self.tmp / 'w', workers=1)
        w.reload()
        self.addCleanup(w.close)
        page = O.render(w, f'/golfer/{pid}', {'tab': ['season'], 'year': ['2027']})[1]
        self.assertIn('The season week by week', page)
        self.assertIn('barrier:', page)

if __name__ == '__main__':
    unittest.main()
