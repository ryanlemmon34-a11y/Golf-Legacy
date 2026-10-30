"""Peak Overall and the Stats page's Overall column (roadmap v14).

Peaks: the base Overall (no form or staff effect) is noted when the world begins, just before every lasting injury
and at every season's end before and after aging -- the only times ratings can fall -- so the highest value is
exact from then on; an equal value (to one decimal, as shown) keeps its first date; noting draws nothing at
random, so the world plays out exactly as it would without it. The profile shows the peak with its date, age and
coverage ("Recorded Peak Overall" when the records do not cover the whole career). The Stats page sorts the
whole result set by Overall in either direction: the current rating (last recorded for retired golfers), or for
a past season its recorded start-of-season rating, missing where none was recorded.

Run from the project folder:  python -m unittest tests.test_peak_overall -v
"""
from __future__ import annotations

import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
from golfsim.population import generate_world                            # noqa: E402
from golfsim.season import Season                                         # noqa: E402
from golfsim.session import Session                                       # noqa: E402
import observer as O                                                      # noqa: E402
import observer_data as OD                                                # noqa: E402


class G:
    def __init__(self, gid, overall, lifestyle='full_time'):
        self.id, self.overall, self.lifestyle = gid, overall, lifestyle


def noter(golfers):
    se = Season.__new__(Season)
    se.peak_overall = {}
    se.active_golfers = lambda: [g for g in golfers if g.lifestyle != 'retired']
    return se


class Noting(unittest.TestCase):
    def test_rising_declining_and_tied_peaks(self):
        rise, fall, tie, gone = G(1, 60.0), G(2, 80.0), G(3, 70.0), G(4, 50.0, 'retired')
        se = noter([rise, fall, tie, gone])
        se.note_peaks(2027, 0)
        rise.overall, fall.overall, tie.overall = 64.0, 78.0, 70.04      # 70.04 shows as 70.0: a tie
        se.note_peaks(2027, 52)
        rise.overall, fall.overall, tie.overall = 66.5, 75.0, 70.06      # 70.06 shows as 70.1: higher
        se.note_peaks(2028, 52)
        self.assertEqual(se.peak_overall[1], (66.5, 2028, 52))
        self.assertEqual(se.peak_overall[2], (80.0, 2027, 0))
        self.assertEqual(se.peak_overall[3], (70.06, 2028, 52))
        self.assertNotIn(4, se.peak_overall)                               # retired golfers are not noted again
        tie2 = G(5, 70.0)
        se2 = noter([tie2])
        se2.note_peaks(2027, 0)
        tie2.overall = 70.0
        se2.note_peaks(2030, 52)
        self.assertEqual(se2.peak_overall[5], (70.0, 2027, 0))              # reached again: the first date is kept

    def test_an_injured_golfer_is_noted_before_the_damage(self):
        g = G(7, 72.0)
        se = noter([])
        se.note_peaks(2031, 18, (g,))
        g.overall = 69.0                                                   # lasting damage
        se.note_peaks(2031, 52, (g,))
        self.assertEqual(se.peak_overall[7], (72.0, 2031, 18))


class World(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        s = Session.create(cls.tmp / 'w', seed=53, workers=1, world=generate_world(seed=53, scale=0.03))
        s.advance(52 + 10)
        cls.peaks = dict(s.season.peak_overall)
        cls.overall = {g.id: g.overall for g in s.season.world.golfers}
        cls.retired = {g.id for g in s.season.world.golfers if g.lifestyle == 'retired'}
        s.close()
        cls.w = O.World(cls.tmp / 'w', workers=1)
        cls.w.reload()
        if cls.w.statistics()[0] is None:
            cls.w._builder.wait(300)

    @classmethod
    def tearDownClass(cls):
        cls.w.close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def page(self, path):
        u = urlparse(path)
        return O.render(self.w, u.path, parse_qs(u.query))[1]

    def test_the_peak_is_at_least_every_recorded_rating_and_survives_reloading(self):
        from golfsim.archive import Archive
        with Archive(self.tmp / 'w' / 'archive') as a:
            careers = a.year(2027)['careers']
            keys = a.world['rating_keys']
        i = keys.index('overall')
        for gid, row in careers.items():
            gid = int(gid)
            self.assertIn('peak', row, gid)
            if row.get('ratings'):                                         # start of 2028, after aging
                self.assertGreaterEqual(round(self.peaks[gid][0], 1), round(row['ratings'][i], 1), gid)
                self.assertGreaterEqual(round(row['peak'][0], 1), round(row['ratings'][i], 1), gid)
        for gid in list(self.peaks)[:60]:                                  # the shown peak: noted values and now
            if gid not in self.retired:
                pk = OD.recorded_peak(self.w, gid)
                self.assertGreaterEqual(pk['value'], round(self.overall[gid], 1), gid)
                self.assertGreaterEqual(pk['value'], round(self.peaks[gid][0], 1), gid)
        s = Session.open(self.tmp / 'w', workers=1)
        try:
            self.assertEqual(dict(s.season.peak_overall), self.peaks)       # unchanged after reload
        finally:
            s.close()

    def test_noting_peaks_changes_nothing_else(self):
        def run(note):
            tmp = Path(tempfile.mkdtemp())
            self.addCleanup(shutil.rmtree, tmp, True)
            with mock.patch.object(Season, 'note_peaks', note):
                s = Session.create(tmp / 'w', seed=59, workers=1, world=generate_world(seed=59, scale=0.02))
                s.advance(52 + 4)
            se = s.season
            out = ({eid: (r.finish, r.scores, r.prizes) for eid, r in se.results.items()},
                   {g.id: (dict(g.attrs), g.lifestyle, g.status) for g in se.world.golfers},
                   {k: v for k, v in se.injured.items()})
            s.close()
            return out
        self.assertEqual(run(Season.note_peaks), run(lambda self, *a, **k: None))

    def test_profile_shows_the_peak_its_date_age_and_coverage(self):
        gid = next(g for g, (v, y, wk) in self.peaks.items() if g not in self.retired and y == 2027 and wk == 0)
        body = self.page(f'/golfer/{gid}')
        m = re.search(r'<p>(Recorded Peak Overall|Peak Overall) <strong>([\d.]+)</strong> · first recorded at ([^<]*)</p>', body)
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), 'Recorded Peak Overall')              # an initial golfer: career began earlier
        self.assertEqual(float(m.group(2)), round(self.peaks[gid][0], 1))
        self.assertIn('the start of 2027', m.group(3))
        self.assertIn('age ', m.group(3))
        self.assertIn('career began before the world’s records', body)
        self.assertIn('no form, staff or play effects', body)
        arrived = [g for g in self.peaks if not self.w.a.people.get(g, {}).get('initial')
                   and g in self.w.a.people]
        if arrived:                                                        # arrived after the world began: complete
            pk = OD.recorded_peak(self.w, arrived[0])
            self.assertTrue(pk['complete'])
            self.assertIn('<p>Peak Overall <strong>', self.page(f'/golfer/{arrived[0]}'))

    def test_stats_sorts_the_whole_set_by_overall_both_ways(self):
        def column(body):
            return [float(v) if v[:1].isdigit() else None
                    for v in re.findall(r'<tr><td class="n">\d+</td><td>.*?</td><td>.*?</td><td class="n">([^<]*)', body)]
        down = self.page('/stats?sort=overall')
        self.assertIn('aria-sort="descending">Overall ▼', down)
        vals = column(down)
        live = [p['ratings'][0] for pid, p in self.w.live.people.items() if p.get('ratings')]
        self.assertEqual(vals[0], max(live))                               # the top of every row, not of one page
        self.assertEqual(vals, sorted(vals, reverse=True))
        up = self.page('/stats?sort=overall&dir=asc')
        self.assertIn('aria-sort="ascending">Overall ▲', up)
        vals_up = [v for v in column(up) if v is not None]
        self.assertEqual(vals_up, sorted(vals_up))
        n = int(re.search(r'([\d,]+) golfers', up).group(1).replace(',', ''))
        if n > O.PAGE_SIZE:                                                # the last page holds the highest
            pages = (n + O.PAGE_SIZE - 1) // O.PAGE_SIZE
            last = [v for v in column(self.page(f'/stats?sort=overall&dir=asc&page={pages}')) if v is not None]
            self.assertEqual(max(last), max(live))
        past = self.page('/stats?sort=overall&year=2027')                  # no start-of-2027 rating: missing
        self.assertIn('Overall (start of 2027)', past)
        self.assertTrue(all(v is None for v in column(past)))
        self.assertNotIn(f'{max(live):.1f}<', past)                        # today's rating is never put in the past
        if 2028 in self.w.a.years:
            self.assertIn('Overall (start of 2028)', self.page('/stats?sort=overall&year=2028'))

    def test_retired_golfers_show_their_last_recorded_overall(self):
        out, label, note = O.overall_column(self.w, self.w.statistics()[0], 'all', None, list(self.retired)[:20])
        for pid, (v, kind, when) in out.items():
            self.assertEqual(kind, 'last')
        self.assertIn('last recorded', note)


class Fixtures(unittest.TestCase):
    """recorded_peak from recorded ratings only, with fixtures for missing history and partial coverage."""

    def world(self, rows, live=None, peak_since=None, first_year=2027, initial=False, cursor=(2031, 10)):
        people = {9: {'name': 'X', 'country': 'USA', 'born': 2000, 'initial': initial, **(live or {})}}
        live_view = SimpleNamespace(people=people, cursor={'year': cursor[0], 'week': cursor[1]},
                                    peak_since=peak_since, first_year=first_year)
        a = SimpleNamespace(people={9: {'initial': initial}}, world={'rating_keys': ['overall', 'x']},
                            years=[r[0] for r in rows] or [first_year], index=None,
                            playing_career=lambda pid: rows)
        return SimpleNamespace(live=live_view, a=a)

    def test_only_a_current_rating(self):
        w = self.world([], live={'ratings': (71.0, 1.0)})
        w.a = None
        pk = OD.recorded_peak(w, 9)
        self.assertEqual((pk['value'], pk['source'], pk['complete']), (71.0, 'current', False))
        self.assertIn('only the current rating is recorded', O.peak_line(w, 9, {'born': 2000}))

    def test_snapshots_from_an_older_engine(self):
        rows = [(2028, {'ratings': [74.2, 1]}), (2029, {'ratings': [76.0, 1]}), (2030, {'ratings': [75.1, 1]})]
        w = self.world(rows, live={'ratings': (74.0, 1.0)})
        pk = OD.recorded_peak(w, 9)
        self.assertEqual((pk['value'], pk['year'], pk['week'], pk['source']), (76.0, 2030, 0, 'start of season'))
        line = O.peak_line(w, 9, {'born': 2000})
        self.assertIn('Recorded Peak Overall <strong>76.0</strong>', line)
        self.assertIn('start-of-season ratings only', line)
        self.assertIn('age 30*', line)

    def test_noting_from_an_upgrade_is_partial(self):
        rows = [(2028, {'ratings': [74.2, 1]}), (2029, {'ratings': [76.0, 1]}),
                (2030, {'ratings': [75.1, 1], 'peak': [76.3, 2030, 18]})]
        w = self.world(rows, live={'ratings': (75.0, 1.0), 'peak': (76.3, 2030, 18)}, peak_since=2030)
        pk = OD.recorded_peak(w, 9)
        self.assertEqual((pk['value'], pk['year'], pk['week'], pk['since'], pk['complete']), (76.3, 2030, 18, 2030, False))
        line = O.peak_line(w, 9, {'born': 2000})
        self.assertIn('noted since 2030', line)
        self.assertIn('start-of-season ratings from 2029', line)

    def test_a_tie_keeps_the_earliest_record(self):
        rows = [(2028, {'ratings': [76.0, 1], 'peak': [76.04, 2028, 52]}), (2029, {'ratings': [75.0, 1], 'peak': [76.04, 2028, 52]})]
        w = self.world(rows, live={'ratings': (76.0, 1.0), 'peak': (76.04, 2028, 52)}, peak_since=2028, first_year=2028)
        pk = OD.recorded_peak(w, 9)
        self.assertEqual((pk['year'], pk['week']), (2028, 52))             # not the start of 2029, not now
        self.assertTrue(pk['complete'])

    def test_a_retired_golfer(self):
        rows = [(2028, {'ratings': [70.0, 1], 'peak': [71.2, 2028, 52]}),
                (2029, {'ratings': [68.0, 1], 'peak': [71.2, 2028, 52]})]
        w = self.world(rows, live={'lifestyle': 'retired', 'peak': (71.2, 2028, 52)}, peak_since=2027, first_year=2027)
        pk = OD.recorded_peak(w, 9)
        self.assertEqual((pk['value'], pk['source'], pk['complete']), (71.2, 'noted', True))
        self.assertIn('Peak Overall <strong>71.2</strong> · first recorded at the end of the 2028 season',
                      O.peak_line(w, 9, {'born': 2000}))


if __name__ == '__main__':
    unittest.main()
