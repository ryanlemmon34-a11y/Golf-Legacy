"""GOAT Lab and cohorts in archive-only browsing: golfers who retired seasons ago keep the Recorded Peak their
profile shows -- its value and its contribution to a custom score -- with or without a live world, and the batch
peak helper agrees with the profile's for every golfer.

Run from the project folder:  python -m unittest tests.test_goat_peaks -v
"""
from __future__ import annotations

import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlencode

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
from golfsim.population import generate_world                         # noqa: E402
from golfsim.session import Session                                   # noqa: E402
import observer as O                                                  # noqa: E402
import observer_goat as G                                             # noqa: E402


class ArchiveOnlyPeaks(unittest.TestCase):
    """Golfers who retired seasons ago keep the Recorded Peak their profile shows -- in the GOAT Lab (its value and
    its contribution to a score) and in cohorts -- with or without a live world (Peak once read only the last
    archived season and the live snapshot)."""

    @classmethod
    def setUpClass(cls):
        import observer_data as OD
        cls.tmp = Path(tempfile.mkdtemp())
        s = Session.create(cls.tmp / 'w', seed=59, workers=1, world=generate_world(seed=59, scale=0.02))
        s.advance(4 * 52 + 2)                                           # four archived seasons
        s.close()
        cls.live = O.World(cls.tmp / 'w', workers=1)
        cls.live.reload()
        cls.arch = O.World(cls.tmp / 'w' / 'archive', workers=1)        # the archive alone: no live snapshot
        if cls.arch.statistics()[0] is None:                           # (the Lab reads the statistics store)
            cls.arch._builder.wait(300)
        a = cls.arch.a
        cls.first, cls.last = a.years[0], a.years[-1]
        # retired golfers with a recorded peak who played the first season, grouped by the last season they
        # played; the earliest such retirement is taken (the most archived seasons after it). Which golfers
        # retire, and when, is a draw of the simulation: this world need not have anyone who stopped right
        # after the first season, so the cohort is chosen, not assumed.
        by_last = {}
        for pid in a.people:
            rows = OD.career_rows(cls.arch, pid)
            if (rows and rows[0][0] == cls.first and any(r.get('peak') for _, r in rows)
                    and ((cls.arch.person(pid) or {}).get('golfer') or {}).get('lifestyle') == 'retired'):
                by_last.setdefault(rows[-1][0], []).append(pid)
        cls.gone = min(by_last, default=None)                           # the last season they played
        cls.retired = by_last.get(cls.gone, [])

    @classmethod
    def tearDownClass(cls):
        cls.arch.close()
        cls.live.close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_a_retired_golfers_peak_survives_later_seasons(self):
        import observer_cohort as OC
        import observer_data as OD
        self.assertIsNone(self.arch.live)
        self.assertGreaterEqual(self.last - self.first, 3)              # several archived seasons
        self.assertTrue(self.retired)
        self.assertLess(self.gone, self.last)                           # archived seasons after they retired:
        for pid in self.retired:                                        # none of them has a row in those
            self.assertEqual(OD.career_rows(self.arch, pid)[-1][0], self.gone)
        vals, missing = G.careers(self.arch, '')
        fol = OC.follow(self.arch, self.retired, self.first)
        for pid in self.retired:
            pk = OD.recorded_peak(self.arch, pid)                       # the profile's
            self.assertIsNotNone(pk, pid)
            if pid in vals:
                self.assertEqual(vals[pid]['peak'], pk['value'])        # the GOAT Lab
                self.assertNotIn('peak', missing[pid])
            self.assertEqual(fol[pid]['peak'], (pk['value'], pk['year'], pk['week']))   # cohorts
            self.assertEqual(OD.recorded_peak(self.live, pid)['value'], pk['value'])   # the same with a live world
        self.assertTrue(any(pid in vals for pid in self.retired))

    def test_the_peak_counts_in_a_custom_score_without_a_live_world(self):
        import observer_data as OD
        q = {f'w_{k}': '0' for k in G.COMPONENTS}
        q.update({'w_peak': '2', 'tour': '', 'status': 'retired'})
        vals, _ = G.careers(self.arch, '')
        order = sorted((p for p, v in vals.items()
                        if ((self.arch.person(p) or {}).get('golfer') or {}).get('lifestyle') == 'retired'),
                       key=lambda p: (-round(2 * (vals[p]['peak'] or 0), 6), -vals[p]['majors'], -vals[p]['wins'], p))
        for pid in [p for p in self.retired if p in vals][:5]:
            value = OD.recorded_peak(self.arch, pid)['value']
            page = order.index(pid) // O.PAGE_SIZE + 1
            html = O.render(self.arch, '/goat', parse_qs(urlencode({**q, 'page': page}), keep_blank_values=True))[1]
            row = re.search(rf'<a href="/golfer/{pid}">.*?</tr>', html, re.S).group(0)
            self.assertIn(f'<strong>{2 * value:,.1f}</strong>', row)    # the score: 2 x the peak
            self.assertIn(f'{value:,.1f}<br><span class="muted">+{2 * value:,.1f}</span>', row)
            self.assertNotIn('missing', row)

    def test_every_golfer_matches_the_profile_helper(self):
        import observer_data as OD
        for w in (self.arch, self.live):
            pids = list(w.a.people)[:400]
            got = OD.recorded_peaks(w, pids)
            for pid in pids:
                pk = OD.recorded_peak(w, pid)
                self.assertEqual(got[pid], (pk['value'], pk['year'], pk['week']) if pk else None, pid)


if __name__ == '__main__':
    unittest.main()
