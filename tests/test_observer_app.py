"""The observer alpha: advances run as background jobs, one at a time, never twice for one request; pages
are drawn from the committed snapshot while a world advances; a stop keeps every completed week; a failure
or an observer that stops mid-advance leaves the world at its last committed week, and says so; worlds are
created, opened, copied (never changing the original) and exported as diagnostic packages; the current
season's editions read the same before and after the season is archived.

Run from the project folder:  python -m unittest discover -s tests -v
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import zipfile
from pathlib import Path
from unittest import mock
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
from golfsim import archive as A                                      # noqa: E402
from golfsim import session as SES                                    # noqa: E402
from golfsim.population import generate_world                         # noqa: E402
from golfsim.session import Session                                   # noqa: E402
import observer as O                                                  # noqa: E402
import observer_app as OA                                             # noqa: E402
import observer_jobs as J                                             # noqa: E402
import observer_worlds as WL                                          # noqa: E402

SCALE = 0.02


def small_create(cls, directory, seed=2027, workers=None, world=None, development=True, calendar=None):
    """Session.create with a small population (the observer creates whole worlds; tests need speed)."""
    return REAL_CREATE(cls, directory, seed=seed, workers=workers, development=development,
                       world=world or generate_world(seed=seed, scale=SCALE), calendar=calendar)


REAL_CREATE = Session.create.__func__


def files_digest(d):
    """{relative path: (size, mtime)} of every file (the original must not change)."""
    return {p.relative_to(d).as_posix(): (p.stat().st_size, p.stat().st_mtime_ns)
            for p in Path(d).rglob('*') if p.is_file()}


def form(w, weeks='1', op='k1'):
    c = w.live.cursor
    return {'weeks': [weeks], 'world': [w.live.world_id], 'year': [str(c['year'])], 'week': [str(c['week'])],
            'phase': [c['phase']], 'op': [op]}


class ObserverAppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.base = cls.tmp / 'base'                                    # 2027, week 41
        s = Session.create(cls.base, seed=11, workers=1, world=generate_world(seed=11, scale=SCALE))
        s.advance(40)
        s.close()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def app(self, name, worlds=('demo',)):
        lib = self.tmp / name
        lib.mkdir()
        for wname in worlds:
            shutil.copytree(self.base, lib / wname)
        app = OA.App(lib, workers=1)
        self.addCleanup(app.shutdown)
        return app, lib

    def opened(self, app, lib, name='demo'):
        app.renderer.call(app._install, lib / name, None)
        return app.world

    def draw(self, app, path='/'):
        """The page as the server draws it (job progress, one-time notices), on the renderer thread."""
        u = urlparse(path)
        return app.renderer.call(app.draw, u.path, parse_qs(u.query))

    def on_renderer(self, app, fn, *args):
        return app.renderer.call(fn, *args)

    # -- one advance per request, one at a time -------------------------------------------------------------
    def test_repeated_requests_advance_once(self):
        app, lib = self.app('repeat')
        w = self.opened(app, lib)
        f = form(w, '4', op='same-click')
        gate, real = threading.Event(), Session._step

        def slow(s):
            gate.wait(30)
            return real(s)
        with mock.patch.object(Session, '_step', slow):
            self.assertIsNone(app.renderer.call(app.advance, f))        # starts
            self.assertIsNone(app.renderer.call(app.advance, f))        # the same click again: the running job
            other = app.renderer.call(app.advance, form(w, '1', op='another'))
            self.assertEqual(other[0], 'warn')                          # a different request: one at a time
            gate.set()
            app.jobs.wait(120)
        self.assertEqual(app.job()['state'], 'done')
        self.draw(app)
        self.assertEqual(app.world.live.cursor, {'year': 2027, 'week': 45, 'phase': 'week'})
        gen = app.world.live.generation
        self.assertIsNone(app.renderer.call(app.advance, f))            # resubmitted after it finished
        app.jobs.wait(60)
        self.assertIn('Already applied', app.job()['message'])
        stale = app.renderer.call(app.advance, {**f, 'op': ['fresh']})    # drawn at week 41: refused
        app.jobs.wait(60)
        self.assertEqual(app.job()['state'], 'refused')
        self.draw(app)
        self.assertEqual((app.world.live.generation, app.world.live.cursor['week']), (gen, 45))
        self.assertIsNone(stale)

    def test_pages_show_the_committed_snapshot_while_advancing(self):
        app, lib = self.app('browse')
        w = self.opened(app, lib)
        before = self.draw(app, '/rankings')
        entered, gate, real = threading.Event(), threading.Event(), Session._step

        def slow(s):
            out = real(s)
            entered.set()
            gate.wait(30)
            return out
        with mock.patch.object(Session, '_step', slow):
            app.renderer.call(app.advance, form(w, '4', op='bg'))
            self.assertTrue(entered.wait(60))                           # a week has been played in memory
            during = self.draw(app, '/rankings')
            main = lambda html: html.split('<main>')[1].split('</main>')[0]
            self.assertEqual(main(during), main(before))                # the same committed snapshot
            self.assertIn('2027, week 41', during)
            self.assertIn('Stop simulation', during)
            for path in ('/', '/golfers', '/calendar', '/records', f'/golfer/{sorted(w.live.wr, key=w.live.wr.get)[0]}'):
                self.assertIn('</html>', self.draw(app, path))
            gate.set()
            app.jobs.wait(120)
        after = self.draw(app, '/')
        self.assertIn('2027, week 45', after)
        self.assertIn('4 weeks played and saved', after)               # the result, once

    def test_several_seasons_are_saved_one_by_one_and_can_be_stopped(self):
        """N seasons: the rest of this one, then whole seasons, each saved and published as it ends; the pages
        move on between seasons; Stop simulation keeps every completed week; the same form again advances
        nothing."""
        app, lib = self.app('seasons')
        w = self.opened(app, lib)                                       # 2027, week 41
        f = {**form(w, 'seasons', op='three'), 'seasons': ['3']}
        real, gate, entered = Session._step, threading.Event(), threading.Event()

        def step(s):
            c = s.state['cursor']
            if (c['year'], c['week']) == (2028, 5) and not entered.is_set():
                entered.set()
                gate.wait(60)
            return real(s)
        with mock.patch.object(Session, '_step', step):
            self.assertIsNone(app.renderer.call(app.advance, f))
            self.assertTrue(entered.wait(300))
            page = self.draw(app, '/')
            self.assertIn('2028, week 1', page)                         # the first season saved, shown
            self.assertIn('season 2 of 3', page)
            self.assertIn('Stop simulation', page)
            self.assertEqual(app.world.a.years, [2027])
            app.jobs.cancel(app.jobs.current.id)                        # Stop simulation, in the second season
            gate.set()
            app.jobs.wait(300)
        j = app.job()
        self.assertEqual(j['state'], 'stopped', j['message'])
        self.assertIn('2027 archived', j['message'])
        self.draw(app)
        self.assertEqual(app.world.live.cursor, {'year': 2028, 'week': 6, 'phase': 'week'})
        on_disk = json.loads((lib / 'demo' / 'CURRENT').read_text())['generation']
        self.assertEqual(on_disk, app.world.live.generation)
        app.renderer.call(app.advance, f)                               # the same form again
        app.jobs.wait(60)
        self.assertIn('Already applied', app.job()['message'])
        self.draw(app)
        self.assertEqual(app.world.live.cursor, {'year': 2028, 'week': 6, 'phase': 'week'})

    def test_two_seasons_to_the_end(self):
        app, lib = self.app('two')
        w = self.opened(app, lib)
        gen = w.live.generation
        app.renderer.call(app.advance, {**form(w, 'seasons', op='two'), 'seasons': ['2']})
        app.jobs.wait(600)
        j = app.job()
        self.assertEqual(j['state'], 'done', j['message'])
        self.assertEqual((j['done'], j['total']), (12 + 52, 12 + 52))
        self.assertIn('seasons 2027–2028 archived', j['message'])
        page = self.draw(app, '/')
        self.assertIn('2029, week 1', page)
        self.assertEqual(app.world.a.years, [2027, 2028])
        self.assertEqual(app.world.live.generation, gen + 2)            # one commit per season

    def test_stop_keeps_every_completed_week(self):
        app, lib = self.app('stop')
        w = self.opened(app, lib)
        real = Session._step

        def step(s):
            out = real(s)
            if s.state['weeks_played'] >= 42:                           # after the second week
                app.jobs.cancel(app.jobs.current.id)
            return out
        with mock.patch.object(Session, '_step', step):
            app.renderer.call(app.advance, form(w, 'season', op='season'))
            app.jobs.wait(120)
        j = app.job()
        self.assertEqual(j['state'], 'stopped')
        self.assertEqual(j['done'], 2)
        self.draw(app)
        self.assertEqual(app.world.live.cursor, {'year': 2027, 'week': 43, 'phase': 'week'})
        s = Session.open(lib / 'demo', workers=1)                       # what is on disk
        self.assertEqual(s.cursor, app.world.live.cursor)
        s.close()

    def test_a_failure_leaves_the_last_committed_week_and_is_reported(self):
        app, lib = self.app('fail')
        w = self.opened(app, lib)
        gen = w.live.generation
        real, calls = Session._step, []

        def step(s):
            calls.append(1)
            if len(calls) == 2:
                raise RuntimeError('injected failure in the second week')
            return real(s)
        with mock.patch.object(Session, '_step', step):
            app.renderer.call(app.advance, form(w, '4', op='fails'))
            app.jobs.wait(120)
        j = app.job()
        self.assertEqual(j['state'], 'failed')
        self.assertIn('injected failure', j['message'])
        self.assertIn('2027, week 41', j['message'])                   # where the world is
        page = self.draw(app, '/')
        self.assertIn('injected failure', page)
        self.assertIn('Report this problem', page)
        self.assertEqual((app.world.live.generation, app.world.live.cursor['week']), (gen, 41))
        self.assertIn('injected failure in the second week', (lib / 'demo' / J.LOG_FILE).read_text())
        self.assertFalse((lib / 'demo' / J.JOB_FILE).exists())
        app.renderer.call(app.advance, form(app.world, '1', op='after'))   # and it can go on
        app.jobs.wait(60)
        self.assertEqual(app.job()['state'], 'done')

    def test_a_season_saved_but_not_yet_published_is_reported_as_saved_and_recovers(self):
        """The owner's first Windows report: the season's end was committed, then publishing its history
        failed. The message must say the advance was saved (not "nothing was kept"), pages must keep
        working (showing the last published history, and saying so), and the history is published as
        soon as publishing works again -- nothing lost."""
        app, lib = self.app('unpublished')
        w = self.opened(app, lib)
        real = SES._publish_archive

        def broken(d, n):
            raise OSError(9, 'Bad file descriptor')
        with mock.patch.object(SES, '_publish_archive', broken):
            app.renderer.call(app.advance, form(w, 'season', op='season-end'))
            app.jobs.wait(300)
            j = app.job()
            self.assertEqual(j['state'], 'failed')
            self.assertIn('The advance was saved', j['message'])
            self.assertIn('2028, week 1', j['message'])
            self.assertNotIn('Nothing of this advance was kept', j['message'])
            page = self.draw(app, '/')
            self.assertNotIn('Something went wrong', page)
            self.assertIn('could not be published', page)
            self.assertIn('The advance was saved', page)               # the result banner, once
        self.assertIs(SES._publish_archive, real)
        page = self.draw(app, '/')                                      # publishing works again
        self.assertIn('2028, week 1', page)
        self.assertNotIn('could not be published', page)
        self.assertEqual(app.world.a.years, [2027])
        self.assertEqual(int(app.world.a.stamp[0]), app.world.live.history_generation)

    def test_an_observer_stopped_mid_advance_is_reported_and_nothing_half_written(self):
        lib = self.tmp / 'killed'
        lib.mkdir()
        shutil.copytree(self.base, lib / 'demo')
        script = f'''
import os, sys, time
sys.path.insert(0, {str(ROOT)!r}); sys.path.insert(0, {str(ROOT / "tools")!r})
import observer_app as OA
app = OA.App({str(lib)!r}, workers=1)
app.renderer.call(app._install, app.lib / 'demo', None)
w = app.world
c = w.live.cursor
app.renderer.call(app.advance, {{'weeks': ['4'], 'world': [w.live.world_id], 'year': [str(c['year'])],
                                 'week': [str(c['week'])], 'phase': [c['phase']], 'op': ['k']}})
while app.jobs.current.done < 2:
    time.sleep(0.05)
os._exit(9)                                   # the window closed: no cleanup at all
'''
        r = subprocess.run([sys.executable, '-c', script], timeout=300)
        self.assertEqual(r.returncode, 9)
        self.assertTrue((lib / 'demo' / J.JOB_FILE).exists())
        app = OA.App(lib, workers=1)
        self.addCleanup(app.shutdown)
        self.assertTrue(WL.inspect(lib / 'demo')['interrupted'])
        if os.name == 'posix':                                          # its lock names a dead process: not "busy"
            self.assertTrue((lib / 'demo' / 'lock').exists())
            self.assertFalse(WL.inspect(lib / 'demo')['busy'])
        self.assertIn('an advance did not finish', self.draw_library(app))
        self.assertIsNone(app.open({'name': ['demo']}))
        app.jobs.wait(120)
        self.assertIn('did not finish', app.job()['message'])
        page = self.draw(app, '/')
        self.assertIn('did not finish', page)
        self.assertEqual(app.world.live.cursor, {'year': 2027, 'week': 41, 'phase': 'week'})   # nothing kept
        self.assertFalse((lib / 'demo' / J.JOB_FILE).exists())
        self.assertFalse(list((lib / 'demo').glob('gen_*.tmp')))

    def draw_library(self, app):
        return self.draw(app, '/worlds')

    # -- the library -------------------------------------------------------------------------------------------
    def test_create_open_copy_and_other_engines(self):
        app, lib = self.app('library')
        with mock.patch.object(Session, 'create', classmethod(small_create)):
            self.assertIsNone(app.create({'name': ['fresh world'], 'seed': ['5']}))
            app.jobs.wait(300)
        self.assertEqual(app.job()['state'], 'done', app.job()['message'])
        self.assertEqual(app.world.label, 'fresh world')
        self.assertIn('2027, week 1', self.draw(app, '/'))
        self.assertEqual(app.create({'name': ['fresh world'], 'seed': ['5']})[0], 'err')   # never overwritten
        self.assertEqual(app.create({'name': ['../escape'], 'seed': ['5']})[0], 'err')
        self.assertEqual(app.create({'name': ['negative'], 'seed': ['-1']})[0], 'err')
        seeds = {re.search(r'name="seed"[^>]*value="(\d+)"', self.draw_library(app)).group(1) for _ in range(5)}
        self.assertGreater(len(seeds), 1)                               # a new seed suggested each time
        # copy: the original is not changed, the copy is the same committed world
        before = files_digest(lib / 'demo')
        self.assertIsNone(app.copy({'name': ['demo'], 'new_name': ['demo copy']}))
        app.jobs.wait(120)
        self.assertEqual(files_digest(lib / 'demo'), before)
        self.assertEqual(WL.inspect(lib / 'demo copy')['cursor'], WL.inspect(lib / 'demo')['cursor'])
        self.assertFalse((lib / 'demo copy' / 'lock').exists())
        # a world saved by another engine: never resumed in place
        other = lib / 'old engine'
        shutil.copytree(self.base, other)
        cur = json.loads((other / 'CURRENT').read_text())
        meta = json.loads((other / cur['dir'] / 'meta.json').read_text())
        meta['engine'], meta['commit'] = 'an-older-engine', '7334ffe'
        (other / cur['dir'] / 'meta.json').write_text(json.dumps(meta))
        os.utime(other / cur['dir'] / 'meta.json')
        info = WL.inspect(other)
        self.assertFalse(info['same_engine'] or info['can_resume'])
        self.assertIn('other engine', self.draw_library(app))
        self.assertEqual(app.open({'name': ['old engine']})[0], 'err')
        with self.assertRaises(ValueError):                             # the guard itself is untouched
            Session.open(other, workers=1)
        self.assertIsNone(app.copy({'name': ['old engine'], 'new_name': ['old engine continued'],
                                    'accept_engine': ['yes']}))
        app.jobs.wait(120)
        accepted = json.loads((lib / 'old engine continued' / WL.ENGINE_ACCEPTED).read_text())
        self.assertEqual(accepted['saved_by_commit'], '7334ffe')
        self.assertTrue(WL.inspect(lib / 'old engine continued')['can_resume'])
        self.assertIsNone(app.open({'name': ['old engine continued']}))
        app.jobs.wait(120)
        self.assertEqual(app.job()['state'], 'done', app.job()['message'])
        self.assertEqual(app.world.label, 'old engine continued')
        self.assertFalse((other / WL.ENGINE_ACCEPTED).exists())       # the original records nothing
        # read-only browsing of a world with no archived season yet
        self.assertIsNone(app.open({'name': ['demo']}, read_only=True))
        app.jobs.wait(60)
        self.assertTrue(app.world.read_only)
        self.assertNotIn('Advance week', self.draw(app, '/'))

    def test_diagnostic_package_is_complete_and_reopens(self):
        app, lib = self.app('export')
        s = Session.open(lib / 'demo', workers=1)
        s.advance(12)                                                   # 2027 archived: a manifest to package
        s.close()
        w = self.opened(app, lib)
        self.assertIsNone(app.export({'name': ['demo'], 'note': ['The leaderboard looked wrong'],
                                      'steps': ['Open week 3'], 'index': ['yes']}))
        app.jobs.wait(120)
        self.assertEqual(app.job()['state'], 'done', app.job()['message'])
        z = sorted((lib / WL.DIAGNOSTICS).glob('*.zip'))[-1]
        out = self.tmp / 'unpacked'
        with zipfile.ZipFile(z) as zf:
            names = set(zf.namelist())
            diag = json.loads(zf.read('DIAGNOSTIC.json'))
            issue = zf.read('ISSUE.md').decode()
            texts = [zf.read(n).decode('utf-8', 'replace') for n in names if n.endswith(('.json', '.md', '.log'))]
            zf.extractall(out)
        m = A.read_manifest(lib / 'demo' / 'archive')
        gen = json.loads((lib / 'demo' / 'CURRENT').read_text())['generation']
        required = {'CURRENT', f'gen_{gen:06d}/state.pkl.gz', f'gen_{gen:06d}/meta.json', 'archive/MANIFEST.json',
                    'archive/index.sqlite', J.LOG_FILE}
        required |= {f'archive/{f}' for k, f in m['files'].items() if k != 'years'}
        required |= {f'archive/{f}' for f in m['files']['years'].values()}
        self.assertLessEqual(required, names)
        self.assertNotIn('lock', names)
        self.assertEqual((diag['seed'], diag['cursor'], diag['generation']), (11, w.live.cursor, gen))
        self.assertEqual(diag['archived_seasons'], [2027])
        self.assertIn('The leaderboard looked wrong', issue)
        for t in texts:                                                 # no local folder names
            self.assertNotIn(str(self.tmp), t)
            self.assertNotIn(str(ROOT), t)
        for f in diag['files']:
            self.assertTrue((out / f['path']).exists(), f['path'])
        s = Session.open(out, workers=1)                                # the package is the world
        self.assertEqual(s.cursor, w.live.cursor)
        s.close()
        with A.Archive(out / 'archive') as a:
            self.assertEqual(a.years, [2027])
            self.assertIsNotNone(a.index)

    # -- one edition, before and after its season is archived ----------------------------------------------
    def test_current_season_editions_read_the_same_once_archived(self):
        app, lib = self.app('agree')
        w = self.opened(app, lib)
        lv = w.live
        eid = sorted(lv.editions, key=lambda e: -(lv.editions[e]['prestige'] or 0))[0]
        pid = O._winner(lv.editions[eid])
        before = {'edition': self.on_renderer(app, w.edition, eid), 'results': self.on_renderer(app, w.results, pid),
                  'page': self.draw(app, f'/event/{eid}')}
        self.assertEqual(before['edition']['source'], 'current season')
        self.assertIsNone(w.a)                                          # the first season: nothing archived yet
        app.renderer.call(app.advance, form(w, 'season', op='to-end'))
        app.jobs.wait(300)
        self.assertEqual(app.job()['state'], 'done', app.job()['message'])
        self.draw(app)
        w = app.world
        self.assertEqual(w.a.years, [2027])
        self.assertNotIn(eid, w.live.editions)                          # held by the archive now, once
        after = {'edition': self.on_renderer(app, w.edition, eid), 'results': self.on_renderer(app, w.results, pid),
                 'page': self.draw(app, f'/event/{eid}')}
        self.assertEqual(after['edition']['source'], 'archive')
        keys = ('person', 'site', 'pos', 'total', 'coach', 'caddie', 'route')
        rows = lambda e: sorted(tuple(r[k] for k in keys) for r in e['rows'])
        self.assertEqual(rows(after['edition']), rows(before['edition']))
        for k in ('id', 'series', 'year', 'week', 'name', 'tour', 'tier', 'category', 'playoff'):
            self.assertEqual(after['edition'][k], before['edition'][k], k)
        self.assertEqual([tuple(map(list, x['sites'])) for x in (after['edition'],)],
                         [tuple(map(list, x['sites'])) for x in (before['edition'],)])
        self.assertEqual(after['results'][:len(before['results'])], before['results'])   # no double counting
        cut = lambda p: re.search(r'<table[ >].*?</table>', p, re.S).group(0)    # the first table
        self.assertEqual(cut(after['page']), cut(before['page']))      # the leaderboard reads the same

    # -- over HTTP ----------------------------------------------------------------------------------------------
    def test_http_round_trip_and_quit(self):
        app, lib = self.app('http')
        httpd = OA.start_server(app, 0)
        base = f'http://127.0.0.1:{httpd.server_address[1]}'
        self.addCleanup(httpd.server_close)
        self.addCleanup(httpd.shutdown)
        get = lambda p: urlopen(base + p, timeout=60).read().decode()
        self.assertIn('World library', get('/'))                        # no world open: the library
        post = lambda p, d: urlopen(Request(base + p, data=urlencode(d, doseq=True).encode()), timeout=60).read().decode()
        post('/worlds/open', {'name': 'demo'})
        app.jobs.wait(120)
        page = get('/')
        self.assertIn('2027, week 41', page)
        f = dict(re.findall(r'<input type="hidden" name="(\w+)" value="([^"]*)">',
                            page.split('action="/advance">')[1].split('<button')[0]))
        f['weeks'] = '1'
        post('/advance', f)
        post('/advance', f)                                             # a double submit
        app.jobs.wait(120)
        status = json.loads(get('/api/status'))
        self.assertEqual(status['job']['state'], 'done')
        self.assertIn('2027, week 42', get('/'))
        post('/advance', f)                                             # the old form again, later
        app.jobs.wait(60)
        self.assertIn('2027, week 42', get('/'))
        for p in ('/golfers?nation=USA', '/calendar?status=played', '/records', '/export', '/job', '/worlds'):
            self.assertIn('</html>', get(p))
        forged = Request(base + '/advance', data=urlencode(f).encode(), headers={'Origin': 'https://example.com'})
        with self.assertRaises(Exception):                              # another web site cannot post here
            urlopen(forged, timeout=60)
        self.assertIn('2027, week 42', get('/'))
        post('/quit', {})
        self.assertTrue(app.quitting.wait(10))


if __name__ == '__main__':
    unittest.main()
