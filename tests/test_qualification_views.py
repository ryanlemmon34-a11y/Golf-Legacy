"""Qualification evidence: this season's majors as they stand -- earned and conditional places (the majors' own
rules, as the engine applies them), places pending a list not yet published, places still to be decided by
qualifying, and projections labelled as information only that never take a qualifying attempt away; and the
standings-lock document generated from the calendar and card rules, kept in sync.

Run from the project folder:  python -m unittest tests.test_qualification_views -v
"""
from __future__ import annotations

import pickle
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
from golfsim import qualification as Q                                    # noqa: E402
from golfsim.population import generate_world                             # noqa: E402
from golfsim.season import Season                                         # noqa: E402
from golfsim.session import Session                                       # noqa: E402
import observer as O                                                      # noqa: E402
import observer_qual as OQ                                                # noqa: E402
import observer_spoilers as SP                                            # noqa: E402
import standings_calendar as SCAL                                         # noqa: E402


class Document(unittest.TestCase):
    def test_the_document_is_the_generators_output(self):
        self.assertEqual((ROOT / 'docs' / 'STANDINGS_AND_RIGHTS.md').read_text(), SCAL.doc(),
                         'regenerate: python tools/standings_calendar.py > docs/STANDINGS_AND_RIGHTS.md')

    def test_it_reads_the_calendar(self):
        mw = SCAL.money_weeks('v2')
        self.assertEqual(mw['PREMIER'][-1], max(w for w in mw['PREMIER']))
        self.assertIn(30, mw['PT_AMERICAS'])                              # the last major counts for Premier lists
        text = SCAL.doc()
        self.assertIn('| ASIA_QSCHOOL_FINAL — places 1-35: Asian Challenger Tour | 51 |', text)
        self.assertIn('| ASIA_QSCHOOL_FINAL — places 1-35: Asian Challenger Tour | 2 |', text)


class SeasonV2(unittest.TestCase):
    """A small reference-calendar season played to week 14, then on to local qualifying (week 17)."""

    @classmethod
    def setUpClass(cls):
        s = Season(generate_world(seed=61, scale=0.05), seed=61, development=True, workers=1, calendar='v2')
        s.start_year(2027)
        for wk in range(1, 15):
            s.advance_week(2027, wk)
        cls.st = OQ.standing(s, 2027, 15)
        cls.wr = dict(s.wr_pos)
        cls.engine = {m: Q.earned_exemptions(m, 2027, s.ctx.as_of(2027, 15)) for m in cls.st}
        for wk in range(15, 18):
            s.advance_week(2027, wk)
        cls.usa = pickle.loads(pickle.dumps(s.stage_log[(2027, 'USA_OPEN')]))
        s.close()

    def test_earned_places_match_the_engine(self):
        for m, (ex, pending) in self.engine.items():
            self.assertEqual(set(self.st[m]['earned']), set(ex), m)
            self.assertEqual({p['code'] for p in self.st[m]['pending']}, set(pending), m)

    def test_pending_cut_offs_have_their_weeks_and_projections_hold_no_place(self):
        usa = self.st['USA_OPEN']
        weeks = {p['code']: p['week'] for p in usa['pending']}
        self.assertEqual(weeks, {'U9': 20, 'U10': 24})
        for code, rows in usa['projected'].items():
            for gid, rank in rows:
                self.assertNotIn(gid, usa['earned'])
                self.assertEqual(self.wr[gid], rank)
                self.assertLessEqual(rank, 60)

    def test_a_projection_never_takes_an_attempt_away(self):
        projected = {g for rows in self.st['USA_OPEN']['projected'].values() for g, _ in rows}
        self.assertTrue(projected)
        able = set(self.usa['direct']) | set(self.usa['pool'])
        for g in projected:
            self.assertTrue(g in able or g in self.usa['exempt'], g)      # in qualifying, or exempt by a real place


class Pages(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        s = Session.create(cls.tmp / 'w', seed=67, workers=1, world=generate_world(seed=67, scale=0.04), calendar='v2')
        s.advance(16)
        s.close()
        cls.w = O.World(cls.tmp / 'w', workers=1)
        cls.w.reload()

    @classmethod
    def tearDownClass(cls):
        cls.w.close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def setUp(self):
        SP.set_hide(self.w, False)

    def page(self, major):
        return O.render(self.w, '/qualification', parse_qs(f'major={major}'))[1]

    def test_the_page_separates_earned_pending_and_projected(self):
        self.assertIsNotNone(self.w.live.qual)
        html = self.page('USA_OPEN')
        for h in ('Earned and conditional places, as of week 17', 'Still to be decided', 'Projected (for information only)'):
            self.assertIn(h, html)
        self.assertIn('A projection is not a place', html)
        self.assertIn('list published at the end of week 20', html)
        self.assertIn('<span class="tag">UQ</span>', html.split('Still to be decided')[1])   # final qualifying to come
        self.assertIn('Qualification ledger', html)

    def test_a_played_major_points_to_its_ledger(self):
        html = self.page('TOUR_MASTERS')
        self.assertIn('played', html)
        self.assertIn('Qualification ledger', html)

    def test_hide_results(self):
        SP.set_hide(self.w, True, 'season')
        html = self.page('USA_OPEN')
        self.assertIn('Hidden while results are hidden', html)
        self.assertIn('the rankings and places', html)                 # (the aggregate note)

    def test_the_standings_page(self):
        html = O.render(self.w, '/standings', {})[1]
        self.assertIn('Reference calendar', html)
        self.assertIn('Combined Premier list', html)


if __name__ == '__main__':
    unittest.main()
