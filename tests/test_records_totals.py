"""Lowest tournament totals per layout: recorded from real completed stroke-play events, linked to the
golfer and the edition, kept through a save, a publication and a reload, and reconstructible from the
archive's evidence.

Run from the project folder:  python -m unittest discover -s tests -v
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from golfsim import archive as A                                      # noqa: E402
from golfsim.population import generate_world                         # noqa: E402
from golfsim.session import Session                                   # noqa: E402
import reconstruct_totals as RT                                       # noqa: E402


class TournamentTotalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.d = cls.tmp / 'world'
        s = Session.create(cls.d, seed=21, workers=1, world=generate_world(seed=21, scale=0.05))
        s.advance(52)                                                  # a season: saved, published
        cls.live = s.season.records.to_dict()
        s.close()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_totals_come_from_completed_stroke_play_events_and_link_to_them(self):
        with A.Archive(self.d / 'archive') as a:
            evidence = defaultdict(list)                               # (layout, holes) -> completed totals
            match_play = set()
            for y, e in a.events():
                if e['match_play']:
                    match_play.add(e['id'])
                    continue
                for site, (course, layout, _) in enumerate(e['sites']):
                    if e['rounds'] < 2:                                # one round is a round, not a total
                        continue
                    for gid, pos, total in e['finish'][site] if site < len(e['finish']) else ():
                        if total is not None:                          # every round played (a missed cut has none)
                            evidence[(f'{course}:{layout}', e['rounds'] * 18)].append((total, e['id'], gid, pos))
            recorded = 0
            for lid, r in a.records.items():
                self.assertEqual(r['totals_since'], 2027)
                for holes, m in r['lowest_totals'].items():
                    recorded += 1
                    holes = int(holes)
                    self.assertIn(holes, (36, 54, 72))
                    rows = evidence[(lid, holes)]
                    self.assertTrue(rows, (lid, holes))
                    best = min(t for t, *_ in rows)
                    first = next(row for row in rows if row[0] == best)  # the first to post it holds it
                    self.assertEqual((m['score'], m['event_id'], m['golfer_id']), first[:3], lid)
                    self.assertNotIn(m['event_id'], match_play)
                    self.assertEqual(m['to_par'], m['score'] - a.world['courses'][lid.split(':')[0]]['layouts']
                                     [lid.split(':')[1]]['par'] * holes // 18)
                    self.assertIn(m['golfer_id'], a.people)            # links: golfer and edition
            self.assertGreater(recorded, 50)
            self.assertEqual({lid for lid, r in a.records.items() if r['lowest_totals']},
                             {lid for lid, _ in evidence})             # every layout with a completed event

    def test_totals_survive_save_and_reload_and_match_the_reconstruction(self):
        s = Session.open(self.d, workers=1)                            # the saved world, reloaded
        self.assertEqual(s.season.records.to_dict(), self.live)
        s.close()
        with A.Archive(self.d / 'archive') as a:
            self.assertEqual({lid: r['lowest_totals'] for lid, r in a.records.items()},
                             json.loads(json.dumps({lid: r['lowest_totals'] for lid, r in self.live.items()})))
            rebuilt = RT.reconstruct(a)
        self.assertEqual(rebuilt['basis'], {'recorded': 1})            # every edition carries its format
        for lid, r in self.live.items():
            want = {int(h): (m['score'], m['event_id'], m['golfer_id']) for h, m in r['lowest_totals'].items()}
            got = {h: (m['score'], m['event_id'], m['golfer_id']) for h, m in rebuilt['layouts'].get(lid, {}).items()}
            self.assertEqual(got, want, lid)


if __name__ == '__main__':
    unittest.main()
