"""The observer's profiles, statistics, shortlists and world controls (owner playtest roadmap, 29 October 2026):
statistics reconcile with the recorded results and the money actually paid; ratings show signed changes
against recorded snapshots and "unavailable" without one; ages are labelled approximate; honors come from
recorded wins; coach clients match current assignments; shortlists persist per world; removed worlds can be
restored and are deleted only deliberately; worlds start in a chosen year with a random or explicit seed.

Run from the project folder:  python -m unittest discover -s tests -v
"""
from __future__ import annotations

import json
import re
import shutil
import sys
import tempfile
import unittest
from collections import Counter, defaultdict
from pathlib import Path
from unittest import mock
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
from golfsim import population as POP                                 # noqa: E402
from golfsim.archive import Archive                                   # noqa: E402
from golfsim.population import generate_world                         # noqa: E402
from golfsim.ratings import ATTRIBUTE_KEYS                            # noqa: E402
from golfsim.session import Session                                   # noqa: E402
import observer as O                                                  # noqa: E402
import observer_app as OA                                             # noqa: E402
import observer_data as OD                                            # noqa: E402
import observer_stats as ST                                           # noqa: E402
import observer_worlds as WL                                          # noqa: E402

SCALE = 0.02


def files_digest(d):
    return {p.relative_to(d).as_posix(): (p.stat().st_size, p.stat().st_mtime_ns) for p in Path(d).rglob('*') if p.is_file()}


class ProfilesAndStatsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.base = cls.tmp / 'base'                                    # 2027 archived; 2028 at week 21
        s = Session.create(cls.base, seed=13, workers=1, world=generate_world(seed=13, scale=SCALE))
        s.advance(52 + 20)
        s.close()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def world(self, name):
        d = self.tmp / name
        shutil.copytree(self.base, d)
        w = O.World(d, workers=1)
        self.addCleanup(w.close)
        return d, w

    def built(self, w):
        db, building = w.statistics()
        if db is None:
            w._builder.wait(120)
            db, building = w.statistics()
        self.assertIsNotNone(db, building)
        return db

    def page(self, w, path):
        u = urlparse(path)
        return O.render(w, u.path, parse_qs(u.query))[1]

    # -- statistics ----------------------------------------------------------------------------------------
    def test_statistics_reconcile_with_results_and_money_paid(self):
        d, w = self.world('stats')
        db = self.built(w)
        # independent counts straight from the season files: every start once, qualifying apart
        want = defaultdict(Counter)
        with Archive(d / 'archive') as a:
            careers = a.year(2027)['careers']
            for e in a.year(2027)['events']:
                for site in e['finish']:
                    for gid, pos, _ in site:
                        c = want[gid]
                        if e['kind'] == 'qualifying':
                            c['qualifiers'] += 1
                            continue
                        c['starts'] += 1
                        c['wins'] += pos == 1
                        c['runner_ups'] += pos == 2
                        c['top10'] += pos is not None and pos <= 10
                        if e['cut_top'] and not e['match_play']:
                            c['cut_events'] += 1
                            c['cuts_made'] += pos is not None
        got = ST.query(db, [2027])
        for gid, c in want.items():
            for k in ('starts', 'wins', 'runner_ups', 'top10', 'cut_events', 'cuts_made', 'qualifiers'):
                self.assertEqual(got[gid][k], c[k], (gid, k))
            row = careers.get(gid) or careers.get(str(gid)) or {}
            self.assertAlmostEqual(got[gid]['prize'], row.get('prize', 0), delta=1)
        # every golfer-season with money reconciles, and its tours add up to the money paid
        n, ok = db.execute('SELECT COUNT(*), SUM(reconciled) FROM season_prize').fetchone()
        self.assertEqual(n, ok)
        for pid, paid in db.execute('SELECT person, prize FROM season_prize WHERE year = 2027 AND prize > 0'):
            tours = db.execute('SELECT SUM(prize) FROM agg WHERE person = ? AND year = 2027', (pid,)).fetchone()[0]
            self.assertAlmostEqual(tours, paid, delta=1)
        # a tour's figures are that tour's editions only; all tours add every start once
        tours = ST.tours_in(db)
        self.assertGreater(len(tours), 3)
        total = sum(r['starts'] for r in ST.query(db, [2027]).values())
        self.assertEqual(total, sum(sum(r['starts'] for r in ST.query(db, [2027], t).values()) for t in tours))
        # the current season so far: the snapshot's editions, partial and reconciled with its money
        live = w.live_statistics()
        self.assertTrue(all(live[1].values()))
        live_starts = sum(1 for e in w.live.editions.values() if e['kind'] != 'qualifying' for s in e['finish'] for _ in s)
        self.assertEqual(sum(a['starts'] for a in live[0].values()), live_starts)
        both = ST.query(db, [2027], None, live)
        self.assertEqual(sum(r['starts'] for r in both.values()), total + live_starts)

    def test_stats_pages_sort_filter_and_drill_down(self):
        d, w = self.world('pages')
        self.built(w)
        html = self.page(w, '/stats?year=2027&sort=wins')
        self.assertIn('Top 10', html)
        self.assertIn('Prize money', html)
        top = re.search(r'<td><a href="/golfer/(\d+)">', html).group(1)
        link = re.search(rf'href="(/golfer/{top}\?tab=results(?:&amp;|&)year=2027(?:&amp;|&)outcome=win)">(\d+)</a>', html)
        wins = int(link.group(2))
        res = self.page(w, link.group(1).replace('&amp;', '&'))
        self.assertIn(f'{wins} of ', res)                               # the drilldown lists exactly those wins
        money = self.page(w, '/money?year=2027')
        amounts = [int(x.replace(',', '')) for x in re.findall(r'<td class="n">\$([\d,]+)</td>', money)]
        self.assertEqual(amounts, sorted(amounts, reverse=True))         # largest first
        t = ST.tours_in(self.built(w))[0]
        self.assertIn('</table>', self.page(w, f'/stats?tour={t}&year=all&sort=prize'))
        self.assertIn('so far', self.page(w, '/stats?year=2028'))

    # -- profiles -------------------------------------------------------------------------------------------
    def test_ratings_ages_honors_and_season_rows(self):
        d, w = self.world('profile')
        self.built(w)
        lv = w.live
        pid = sorted(lv.wr, key=lv.wr.get)[0]
        g = w.session.season.g[pid]
        self.assertEqual(lv.people[pid]['ratings'][1:], tuple(round(g.attrs[k], 1) for k in ATTRIBUTE_KEYS))
        snaps = OD.rating_snapshots(w, pid)
        self.assertEqual(sorted(snaps), [2028])                         # the start of 2028 only: recorded with 2027
        html = self.page(w, f'/golfer/{pid}')
        self.assertIn(f'Age {2028 - g.born}*', html)                    # current age before the birth year
        self.assertLess(html.index('Age '), html.index('born '))
        self.assertIn('approximate', html)
        self.assertIn('unavailable', html)                              # no start-of-2027 snapshot: last season
        cur, base = lv.people[pid]['ratings'][0], snaps[2028][0]
        self.assertIn(f'{round(cur - base, 1):+.1f}', html)            # this season, signed, against the record
        self.assertIn(f'>2027</a></td><td class=n>{2027 - g.born}*</td>', html.replace('"', ''))   # linked season
        self.assertIn('so far', html)
        rows = OD.results(w, pid)
        wins = [r for r in rows if r['pos'] == 1 and not OD.is_qualifying(r)]
        honors = OD.honors(rows)
        self.assertEqual(sum(len(x[2]) for x in honors), len(wins))   # each win in one category
        for key, label, ws in honors:
            self.assertIn(label, html)

    def test_coach_clients_are_current_assignments(self):
        d, w = self.world('coach')
        lv = w.live
        coach = Counter(lv.coach_of.values()).most_common(1)[0][0]
        html = self.page(w, f'/golfer/{coach}?tab=coaching')
        clients = sorted(g for g, c in lv.coach_of.items() if c == coach)
        section = html.split('Current clients')[1].split('</table>')[0]
        self.assertEqual(sorted(int(x) for x in re.findall(r'/golfer/(\d+)', section)), clients)
        self.assertIn('All partnerships', html)                         # dated history kept apart
        self.assertIn('Season by season', html)

    def test_moments_show_their_venue(self):
        d, w = self.world('moments')
        html = self.page(w, '/moments')
        rows = re.findall(r'<tr>(.*?)</tr>', html)[1:]
        self.assertTrue(rows)
        for r in rows:
            self.assertTrue('/course/' in r or 'not applicable' in r, r)
        with Archive(d / 'archive') as a:
            m = a.moments()[0]
        self.assertIn(m['layout'].split(':')[1], html)

    def test_a_golfer_who_became_staff_keeps_one_identity(self):
        with Archive(self.base / 'archive') as a:
            both = [pid for pid, p in a.people.items() if 'golfer' in p and ('coach' in p or 'caddie' in p)]
        if not both:
            self.skipTest('no golfer became staff in this short world (checked on the 50-season copy)')
        d, w = self.world('roles')
        pid = both[0]
        html = self.page(w, f'/golfer/{pid}')
        self.assertIn('Playing career', html)
        self.assertTrue('Coaching' in html or 'Caddying' in html)

    # -- shortlists and world controls ----------------------------------------------------------------------
    def test_shortlists_persist_per_world_across_types(self):
        lib = self.tmp / 'short'
        lib.mkdir()
        shutil.copytree(self.base, lib / 'w')
        app = OA.App(lib, workers=1)
        self.addCleanup(app.shutdown)
        app.renderer.call(app._install, lib / 'w', None)
        w = app.world
        lv = w.live
        eid = next(iter(lv.editions))
        items = [('person', str(sorted(lv.wr, key=lv.wr.get)[0])), ('course', next(iter(lv.courses))),
                 ('nation', 'USA'), ('tour', 'PT_AMERICAS'), ('series', eid.split(':', 1)[1]), ('edition', eid)]
        for kind, ident in items:
            self.assertTrue(app.renderer.call(O.set_shortlist, w, kind, ident, True))
        page = app.renderer.call(app.draw, '/shortlist', {})
        for label in ('People', 'Courses', 'Nations', 'Tours', 'Tournaments', 'Editions'):
            self.assertIn(label, page)
        app.renderer.call(app.close)
        app2 = OA.App(lib, workers=1)                                   # reopened: still there
        self.addCleanup(app2.shutdown)
        app2.renderer.call(app2._install, lib / 'w', None)
        self.assertEqual(sorted((k, i) for k, i, _ in O.shortlist(app2.world)), sorted(items))
        app2.renderer.call(O.set_shortlist, app2.world, 'nation', 'USA', False)
        self.assertNotIn(('nation', 'USA'), [(k, i) for k, i, _ in O.shortlist(app2.world)])
        self.assertIn('Shortlisted', app2.renderer.call(app2.draw, f'/golfer/{items[0][1]}', {}))

    def test_removed_worlds_can_be_restored_and_are_deleted_only_deliberately(self):
        lib = self.tmp / 'trash'
        lib.mkdir()
        shutil.copytree(self.base, lib / 'keep')
        shutil.copytree(self.base, lib / 'open')
        before = files_digest(lib / 'keep')
        app = OA.App(lib, workers=1)
        self.addCleanup(app.shutdown)
        app.renderer.call(app._install, lib / 'open', None)
        self.assertEqual(app.remove({'name': ['keep']})[0], 'warn')      # not confirmed
        self.assertEqual(app.remove({'name': ['open'], 'confirm': ['yes']})[0], 'warn')   # the open world
        self.assertEqual(app.remove({'name': ['../keep'], 'confirm': ['yes']})[0], 'err')
        self.assertEqual(app.remove({'name': ['keep'], 'confirm': ['yes']})[0], 'ok')
        self.assertFalse((lib / 'keep').exists())
        self.assertNotIn('keep', [i['name'] for i in WL.list_worlds(lib)])
        (folder, name, _, _), = WL.trashed(lib)
        self.assertEqual(name, 'keep')
        self.assertIn('Removed worlds', app.renderer.call(app.draw, '/worlds', {}))
        self.assertEqual(app.purge({'folder': [folder], 'typed': ['wrong']})[0], 'err')   # deleted only deliberately
        self.assertEqual(app.restore({'folder': [folder]})[0], 'ok')
        after = files_digest(lib / 'keep')
        self.assertEqual({k: v for k, v in after.items() if k not in ('observer.log',)},
                         {k: v for k, v in before.items() if k not in ('observer.log',)})
        app.remove({'name': ['keep'], 'confirm': ['yes']})
        (folder, _, _, _), = WL.trashed(lib)
        self.assertEqual(app.purge({'folder': [folder], 'typed': ['keep']})[0], 'ok')
        self.assertEqual(WL.trashed(lib), [])
        self.assertTrue((lib / 'open').exists())

    def test_new_worlds_take_a_starting_year_and_a_random_or_explicit_seed(self):
        lib = self.tmp / 'years'
        lib.mkdir()
        app = OA.App(lib, workers=1)
        self.addCleanup(app.shutdown)
        real = POP.generate_world
        small = lambda year=2027, seed=2027, **k: real(year=year, seed=seed, scale=SCALE)
        with mock.patch.object(POP, 'generate_world', small):
            self.assertIsNone(app.create({'name': ['a'], 'start_year': ['2040'], 'seed': ['77']}))
            app.jobs.wait(300)
            self.assertIsNone(app.create({'name': ['b'], 'start_year': ['2040'], 'seed': ['77']}))
            app.jobs.wait(300)
            self.assertIsNone(app.create({'name': ['c'], 'start_year': ['2040'], 'seed': ['']}))
            app.jobs.wait(300)
            self.assertEqual(app.create({'name': ['d'], 'start_year': ['1700']})[0], 'err')
        info = {i['name']: i for i in WL.list_worlds(lib)}
        self.assertEqual((info['a']['seed'], info['a']['start_year'], info['a']['cursor']['year']), (77, 2040, 2040))
        self.assertEqual(info['c']['start_year'], 2040)
        self.assertIsNotNone(info['c']['seed'])                          # a random one, recorded
        self.assertEqual(json.loads((lib / 'a' / WL.WORLD_INFO).read_text())['seed'], 77)
        def golfers(n):
            s = Session.open(lib / n, workers=1)
            try:
                return [(g.name, g.born) for g in s.season.world.golfers[:50]]
            finally:
                s.close()
        self.assertEqual(golfers('a'), golfers('b'))                     # the same seed: the same world
        page = app.renderer.call(app.draw, '/worlds', {})
        self.assertIn('Starting year', page)
        self.assertIn('<td>2040</td>', page)


if __name__ == '__main__':
    unittest.main()
