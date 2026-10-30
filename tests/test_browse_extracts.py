"""History browsing shortcuts give exactly what reading the seasons gives: a profile's per-season extracts (career
decisions, ranking points, weekly rankings) kept with the history reading, and weeks at No. 1 counted once per
reading for every list that needs it (and again after the history changes).

Run from the project folder:  python -m unittest tests.test_browse_extracts -v
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
from golfsim.history_stats import board                               # noqa: E402
from golfsim.population import generate_world                         # noqa: E402
from golfsim.session import Session                                   # noqa: E402
import observer as O                                                  # noqa: E402
import observer_golf as OG                                            # noqa: E402
import observer_history as OH                                         # noqa: E402


class Extracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        s = Session.create(cls.tmp / 'w', seed=73, workers=1, world=generate_world(seed=73, scale=0.03))
        s.advance(2 * 52 + 2)
        s.close()
        cls.w = O.World(cls.tmp / 'w', workers=1)
        cls.w.reload()

    @classmethod
    def tearDownClass(cls):
        cls.w.close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_decisions_and_points_equal_the_season_files(self):
        w = self.w
        for y in w.a.years:
            d = w.a.year(y)
            people = sorted({t.get('gid') for t in d.get('transitions', [])} | set(list(d['careers'])[:200]))
            for pid in people:
                self.assertEqual(OH.decisions(w, pid, y), [t for t in d.get('transitions', []) if t.get('gid') == pid])
                want = None
                evs = d.get('events', [])
                if any(e.get('points') for e in evs):
                    want = []
                    for e in evs:
                        for k, site in enumerate(e.get('points') or []):
                            if str(pid) in site:
                                pos = next((p for g, p, _ in e['finish'][k] if g == pid), None)
                                want.append((y, e['week'], e['id'], pos, site[str(pid)]))
                    want.sort(key=lambda r: (r[1], r[2]))
                if getattr(w.a.index, 'has_points', False):
                    continue                                          # (the index answers it then)
                self.assertEqual(OG._archived_points(w, pid, y), want)
            self.assertEqual(OG._rankings(w, y)['ranking_points'], d.get('ranking_points') or {})

    def test_weeks_at_number_one_counted_once_per_reading(self):
        st = self.w.stats
        st.boards = {}
        calls = []
        real = st.a.weeks_at_number_one
        with mock.patch.object(st.a, 'weeks_at_number_one', side_effect=lambda: calls.append(1) or real()):
            short = board(st, 'weeks-at-number-one', n=100)[1]
            full = board(st, 'weeks-at-number-one', n=10 ** 6)[1]
        self.assertEqual(len(calls), 1)
        self.assertEqual(short, full[:100])
        self.assertEqual({r['person']: r['value'] for r in full}, real())
        st.extend(st.a)                                               # a new reading: counted again
        self.assertNotIn('_no1', st.boards)


if __name__ == '__main__':
    unittest.main()
