"""Major places and money: every place records the money it was decided on (what the golfer could draw, what
was set aside, what remained, the trip's cost and who paid), and the qualification ledger shows it; places
decided before this was kept say "not recorded".

Run from the project folder:  python -m unittest tests.test_major_funding -v
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
from golfsim.population import generate_world                         # noqa: E402
from golfsim.session import Session                                   # noqa: E402
import observer as O                                                  # noqa: E402


class MoneyFacts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        s = Session.create(cls.tmp / 'w', seed=91, workers=1, world=generate_world(seed=91, scale=0.03))
        s.advance(22)                                                   # the reference calendar's first two majors
        cls.rights = {m: {g: dict(r) for g, r in book.items()} for m, book in s.season.major_rights[2027].items()}
        s.close()
        cls.w = O.World(cls.tmp / 'w', workers=1)
        cls.w.reload()

    @classmethod
    def tearDownClass(cls):
        cls.w.close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_every_decided_place_records_its_money(self):
        self.assertEqual(sorted(self.rights), ['PREMIER_TOUR_CHAMPIONSHIP', 'TOUR_MASTERS'])
        for major, book in self.rights.items():
            for gid, r in book.items():
                if r['result'].startswith('withdrawn') or r['result'].startswith('expired'):
                    continue                                            # (decided by injury, retirement, status)
                m = r.get('money')
                self.assertIsNotNone(m, (major, gid, r['result']))
                self.assertLessEqual(abs(m['funds'] - m['set_aside'] - m['spendable']), 1)   # (each rounded)
                self.assertGreater(m['trip'], 0)
                self.assertIn(m['paid_by'], ('golfer', 'organizer', 'school', 'club'))
                if r['result'] == 'declined: could not pay the trip':
                    self.assertLess(m['spendable'], m['trip'])          # the reason, in numbers

    def test_the_ledger_page_shows_it(self):
        html = O.render(self.w, '/qualification', parse_qs('major=TOUR_MASTERS&year=2027'))[1]
        self.assertIn('Money when the field was set', html)
        self.assertIn('could draw $', html)
        self.assertIn('paid by the golfer', html)

    def test_older_places_say_not_recorded(self):
        import observer_history as OH
        self.assertIn('not recorded', OH._place_money(O, {'result': 'entered'}))


if __name__ == '__main__':
    unittest.main()
