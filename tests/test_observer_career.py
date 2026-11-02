"""Career mode in the observer (roadmap Phase B; docs/career/PHASE_AB_PLAN.md): the career routes, forms and pages
over golfsim's career commands, played over HTTP on the career fixture world (seed 11, scale 0.05) at its first
newcomer boundary. The pages only draw the committed snapshot and post commands; every rule lives in golfsim.

Run from the project folder:  python -m unittest tests.test_observer_career -v
"""
from __future__ import annotations

import re
import shutil
import sys
import threading
import unittest
from pathlib import Path
from unittest import mock
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'tests'))
import career_fixture as F                                             # noqa: E402
import observer_app as OA                                              # noqa: E402
from golfsim import career as CA                                       # noqa: E402
from golfsim.session import Session                                    # noqa: E402

POST_ROUTES = {'/career/start', '/career/plan', '/career/decide', '/career/end', '/career/advance', '/career/new'}


def fields(page, action):
    """The hidden fields of the first form on `page` that posts to `action`."""
    seg = page.split(f'action="{action}"')[1].split('</form>')[0]
    return dict(re.findall(r'<input type="hidden" name="(\w+)" value="([^"]*)">', seg))


def banners(page):
    return re.findall(r'class="banner (ok|warn|err)"[^>]*>(.*?)</div>', page, re.S)


class Server:
    """The observer on a copy of the fixture, served over HTTP on a free local port."""

    def __init__(self, case, src=None):
        self.lib = F.tmpdir('obs_career_')
        shutil.copytree(src or F.first_boundary(), self.lib / 'demo')
        self.app = OA.App(self.lib, workers=1)
        self.httpd = OA.start_server(self.app, 0)
        case.addCleanup(self.close)
        self.base = f'http://127.0.0.1:{self.httpd.server_address[1]}'
        self.post('/worlds/open', {'name': 'demo'})
        self.app.jobs.wait(120)

    def close(self):
        if self.httpd is None:
            return
        self.httpd.shutdown()
        self.httpd.server_close()
        self.app.shutdown()
        self.httpd = None

    def get(self, p):
        return urlopen(self.base + p, timeout=300).read().decode()

    def post(self, p, d):
        return urlopen(Request(self.base + p, data=urlencode(d, doseq=True).encode()), timeout=300).read().decode()

    def session(self):
        return self.app.world.session

    def job(self):
        self.app.jobs.wait(900)
        return self.app.job()


def start_and_reach_the_plan(t, srv):
    p = srv.get('/career')
    t.assertIn('Start the career', p)
    p = srv.post('/career/start', fields(p, '/career/start'))
    t.assertEqual(banners(p)[0][0], 'ok')
    f = fields(srv.get('/career'), '/career/advance')
    srv.post('/career/advance', dict(f, mode='next'))
    j = srv.job()
    t.assertEqual(j['state'], 'done')
    t.assertIn('0 weeks played', j['message'])
    t.assertIn('decision', j['message'])
    return srv.get('/career/plan?block=2028-1')


class ObserverCareer(unittest.TestCase):
    def test_a_four_week_slice_played_through_the_pages(self):
        """Start a career, reach the plan, have an ineligible choice refused with its reason, plan event / training /
        rest, play the period, resubmit the same form (nothing more happens), hand the golfer back."""
        srv = Server(self)
        pl = start_and_reach_the_plan(self, srv)
        ff = fields(pl, '/career/plan')
        events = re.findall(r'name="w1" value="event:([^"]+)"', pl)
        self.assertTrue(events)
        car = srv.session().season.career
        v0 = car.version
        bad = dict(ff, w1='event:2028:NO_SUCH_EVENT', f1='rest', w2='rest', w3='rest', w4='rest', selected='accept',
                   qualifying='skip')
        p = srv.post('/career/plan', bad)
        kind, text = banners(p)[0]
        self.assertEqual(kind, 'err')
        self.assertIn('not saved', text)
        self.assertEqual(srv.session().season.career.version, v0)        # nothing changed
        self.assertIn('action="/career/plan"', p)                        # still on the planner
        good = dict(ff, w1='event:' + events[0], f1='train:putting', w2='train', c2='long_game', w3='rest', w4='train',
                    c4='mental', selected='accept', qualifying='skip')
        p = srv.post('/career/plan', good)
        self.assertEqual(banners(p)[0][0], 'ok')
        gid = srv.session().season.career.golfer_id
        page = srv.get('/career')
        f = fields(page, '/career/advance')
        srv.post('/career/advance', dict(f, mode='period'))
        j = srv.job()
        self.assertEqual(j['state'], 'done')
        self.assertIn('4 weeks played', j['message'])
        self.assertEqual(srv.session().cursor, {'year': 2028, 'week': 5, 'phase': 'week'})
        se = srv.session().season
        entered = gid in se.event_routes[2028].get(events[0], {})
        fell_back = any(n['kind'] == 'entry' for n in se.career.notices)
        self.assertTrue(entered or fell_back)                            # the planned event, or its stated fallback
        self.assertGreaterEqual(se.activity_counts[2028][gid].get('train', 0), 2)   # weeks 2 and 4
        self.assertGreaterEqual(se.activity_counts[2028][gid].get('rest', 0), 1)    # week 3
        gen = srv.session().generation
        srv.post('/career/advance', dict(f, mode='period'))              # the same form again
        j = srv.job()
        self.assertIn('Already applied', j['message'])
        self.assertEqual(srv.session().generation, gen)
        srv.post('/career/advance', dict(f, mode='period', op='fresh'))  # a new click on the old page: stale
        j = srv.job()
        self.assertEqual(j['state'], 'refused')
        self.assertEqual(srv.session().cursor['week'], 5)
        e = fields(srv.get('/career'), '/career/end')
        p = srv.post('/career/end', e)
        self.assertEqual(banners(p)[0][0], 'warn')                       # confirmation required
        self.assertEqual(srv.session().season.career.status, 'active')
        p = srv.post('/career/end', dict(e, confirm='yes'))
        self.assertEqual(banners(p)[0][0], 'ok')
        self.assertIn('under AI control since', srv.get('/career'))

    def test_saved_and_reloaded_between_requests(self):
        srv = Server(self)
        pl = start_and_reach_the_plan(self, srv)
        ff = fields(pl, '/career/plan')
        srv.post('/career/plan', dict(ff, w1='rest', w2='rest', w3='train', c3='putting', w4='rest', selected='decline',
                                      qualifying='skip'))
        car = srv.session().season.career
        version, plans = car.version, dict(car.plans)
        lib = srv.lib
        srv.close()                                                      # the observer stops
        again = OA.App(lib, workers=1)                                   # and starts again on the same library
        self.addCleanup(again.shutdown)
        again.renderer.call(again._install, lib / 'demo', None)
        c2 = again.world.session.season.career
        self.assertEqual((c2.version, c2.plans), (version, plans))
        page = again.renderer.call(again.draw, '/career', {})
        self.assertIn('Train: Putting', page)

    def test_an_interrupted_advance_keeps_every_completed_week(self):
        srv = Server(self)
        pl = start_and_reach_the_plan(self, srv)
        ff = fields(pl, '/career/plan')
        srv.post('/career/plan', dict(ff, w1='rest', w2='rest', w3='rest', w4='rest', selected='accept',
                                      qualifying='skip'))
        gate, real = threading.Event(), Session._part_play
        played = []

        def slow(s):
            r = real(s)
            played.append(r['completed'])
            if len(played) == 2:
                srv.app.jobs.cancel(srv.app.job()['id'])                # stop requested during week 2
            return r
        f = fields(srv.get('/career'), '/career/advance')
        with mock.patch.object(Session, '_part_play', slow):
            srv.post('/career/advance', dict(f, mode='period'))
            j = srv.job()
        self.assertEqual(j['state'], 'stopped')
        self.assertIn('2 weeks played', j['message'])
        self.assertEqual(srv.session().cursor, {'year': 2028, 'week': 3, 'phase': 'week'})
        d = srv.lib / 'demo'
        s = Session.open(d)                                              # what is on disk: the two weeks, saved
        self.assertEqual(s.cursor, {'year': 2028, 'week': 3, 'phase': 'week'})
        s.close()

    def test_refusals(self):
        srv = Server(self)
        p = srv.get('/career')
        f = fields(p, '/career/start')
        p = srv.post('/career/start', dict(f, world='another-world'))  # a form from another world
        self.assertEqual(banners(p)[0][0], 'warn')
        self.assertIsNone(srv.session().season.career)
        p = srv.post('/career/start', f)
        self.assertEqual(banners(p)[0][0], 'ok')
        gid = srv.session().season.career.golfer_id
        p = srv.post('/career/start', dict(f, op='second'))              # a second career in the same world: refused
        self.assertEqual(banners(p)[0][0], 'err')
        self.assertEqual(srv.session().season.career.golfer_id, gid)
        p = srv.get('/career')
        d = fields(p, '/career/advance')
        p = srv.post('/career/decide', dict(d, decision='D999', answer='accept'))
        self.assertEqual(banners(p)[0][0], 'err')                        # no such decision: refused with a reason

    def test_pages_have_no_placeholder_controls_and_no_hidden_potential(self):
        srv = Server(self)
        pl = start_and_reach_the_plan(self, srv)
        g = srv.session().season.g[srv.session().season.career.golfer_id]
        for page in (srv.get('/career'), pl):
            for action in re.findall(r'<form method="post" action="([^"]+)"', page):   # every posted control
                self.assertIn(action, POST_ROUTES | {'/advance', '/cancel', '/shortlist'}, action)
            self.assertNotIn('href="#"', page)
            self.assertNotRegex(page, r'<(button|input|select)[^>]*\sdisabled')   # no dead controls
            self.assertNotIn(f'{g.potential:.1f}', page.replace('Potential is never shown', ''))
            self.assertNotIn('ceiling', page.lower())
        for href in re.findall(r'href="(/career[^"]*)"', srv.get('/career')):
            self.assertIn('</html>', srv.get(href.replace('&amp;', '&')))

    def test_views_change_nothing(self):
        s = Session.open(F.copy_of(F.first_boundary()))
        s.career_action({'schema': CA.SCHEMA, 'type': 'new_career'}, op_key='n')
        s.advance_career('next', op_key='a')
        before = F.digest(s), s.season.career.version, s.generation
        for _ in range(3):
            CA.view(s.season, s.cursor)
            CA.planner(s.season, s.cursor, 2028, 1)
            CA.planner(s.season, s.cursor, 2028, 5)
        self.assertEqual((F.digest(s), s.season.career.version, s.generation), before)
        s.close()


if __name__ == '__main__':
    unittest.main()
