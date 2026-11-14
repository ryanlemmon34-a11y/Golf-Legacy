"""Initial picker: real worlds, explicit guarded choices, no extra golfers or rerolls."""
import json
import re
import unittest
from html import unescape
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
from tests.test_observer_career import Server, fields, banners
import career_fixture as F
from golfsim import career as CA
import observer_career as UI

ROOT=Path(__file__).resolve().parents[1]

def candidate_forms(page):
    out=[]
    for segment in page.split('<form ')[1:]:
        if 'action="/career/start"' not in segment.split('>')[0]:
            continue
        body=segment.split('</form>')[0]
        out.append({k:unescape(v) for k,v in re.findall(r'<input type="hidden" name="(\w+)" value="([^"]*)">',body)})
    return out

class InitialPickerPresentation(unittest.TestCase):
    def test_fixture_profiles_readonly_and_no_automatic_choice(self):
        start=json.loads((ROOT/'docs/career/initial_selection_fixtures/start_view.json').read_text())
        w=SimpleNamespace(live=SimpleNamespace(career_start=start,cursor=start['cursor'],world_id='test'),read_only=False)
        html=UI.no_career(w)
        self.assertEqual([f['golfer'] for f in candidate_forms(html)],start['options'])
        self.assertIn('No golfer is chosen until',html)
        for key in ('peak_age','ceilings','aging_rate'):
            self.assertNotIn(key,html)
        w.read_only=True
        self.assertEqual(candidate_forms(UI.no_career(w)),[])
        self.assertIn('browsing only',UI.no_career(w))

class InitialPickerHTTP(unittest.TestCase):
    def test_refresh_reload_validation_and_explicit_choice(self):
        srv=Server(self)
        s=srv.session()
        ids_before=set(s.season.g)
        digest=F.digest(s)
        first=candidate_forms(srv.get('/career'))
        self.assertEqual(len(first),10)
        chosen=[f['golfer'] for f in first]
        self.assertEqual(chosen,[f['golfer'] for f in candidate_forms(srv.get('/career'))])
        self.assertEqual(digest,F.digest(s))
        self.assertIsNone(s.season.career)
        src=s.dir
        srv.close()
        srv=Server(self,src)
        again=candidate_forms(srv.get('/career'))
        self.assertEqual(chosen,[f['golfer'] for f in again])
        f=again[0]
        missing=dict(f);missing.pop('golfer')
        result=srv.post('/career/start',missing)
        self.assertEqual(banners(result)[0][0],'err')
        self.assertIsNone(srv.session().season.career)
        result=srv.post('/career/start',dict(f,golfer='999999999',op='invalid-golfer'))
        self.assertEqual(banners(result)[0][0],'err')
        self.assertIsNone(srv.session().season.career)
        result=srv.post('/career/start',f)
        self.assertEqual(banners(result)[0][0],'ok')
        self.assertEqual(srv.session().season.career.golfer_id,int(f['golfer']))
        generation=srv.session().generation
        srv.post('/career/start',f)
        self.assertEqual(srv.session().generation,generation)
        srv.post('/career/start',again[1])
        self.assertEqual(srv.session().season.career.golfer_id,int(f['golfer']))
        self.assertEqual(set(srv.session().season.g),ids_before)
        self.assertEqual(F.digest(srv.session()),digest)
        self.assertEqual(candidate_forms(srv.get('/career')),[])

    def test_new_career_job_stops_before_selecting_anyone(self):
        from golfsim.population import generate_world
        srv=Server(self)
        with mock.patch('golfsim.population.generate_world',side_effect=lambda **kw:generate_world(**kw,scale=.05)):
            srv.post('/career/new',{'name':'Choose me','seed':'11','start_year':'2027'})
            job=srv.job()
        self.assertEqual(job['state'],'done',job)
        self.assertIn('No golfer has been selected yet',job['message'])
        s=srv.session()
        self.assertEqual(s.cursor,{'year':2028,'week':1,'phase':'start'})
        self.assertIsNone(s.season.career)
        self.assertEqual(len(candidate_forms(srv.get('/career'))),10)
        self.assertIn('Choose your golfer',srv.get('/career'))
