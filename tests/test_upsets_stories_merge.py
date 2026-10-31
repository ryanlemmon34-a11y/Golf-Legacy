"""Biggest Upsets meets tournament stories: each upset row links to its edition's story (the Story tab of the
edition page, observer_stories.story_href). Built on the Biggest Upsets page fixture (a stats store from
recorded editions; no world, nothing simulated).

Run from the project folder:  python -m unittest tests.test_upsets_stories_merge -v
"""
from __future__ import annotations

import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'tests'))
import test_upsets as TU                                              # noqa: E402  (the page fixture)


class UpsetRowsLinkToStories(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import observer_stats as ST
        cls.tmp = Path(tempfile.mkdtemp())
        cls.store = ST.StatsStore(cls.tmp / 's.sqlite')
        for y, evs in TU.season_events().items():
            cls.store.put(y, str(y), {}, {}, {}, {}, upsets=ST.upset_rows(evs, y))
        people = {g: {'name': f'Golfer {g}', 'country': 'USA', 'born': 2010, 'golfer': {'status': 'pro'}}
                  for g in range(1, 7)}
        cls.w = TU.FakeWorld(cls.store.db, people)

    @classmethod
    def tearDownClass(cls):
        cls.store.close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_each_ranked_row_links_to_its_story(self):
        import observer_stories as STORY
        import observer_upsets as OU
        html = OU.page(self.w, {})[1]
        rows, _ = OU.rows_for(self.w)
        ranked = [r['event_id'] for r in rows if r['p'] is not None]
        self.assertTrue(ranked)
        body = html.split('<tbody>', 1)[1].split('</tbody>', 1)[0]
        trs = body.split('</tr>')[:-1]
        self.assertEqual(len(trs), len(ranked))
        for eid in ranked:
            href = STORY.story_href(eid)                               # /event/<id>?view=story
            self.assertEqual(href, f'/event/{eid.replace(":", "%3A")}?view=story')
            row = next(t for t in trs if f'href="/event/{eid.replace(":", "%3A")}"' in t)
            self.assertIn(f'href="{href}"', row)                       # the story, in the same row as the edition
        self.assertEqual(len(re.findall(r'\?view=story"', body)), len(ranked))

    def test_no_link_without_an_edition(self):
        import observer_upsets as OU
        self.assertEqual(OU.story_link({'event_id': None}), '')
        self.assertIn('?view=story', OU.story_link({'event_id': '2031:REGIONAL_C'}))


if __name__ == '__main__':
    unittest.main()
