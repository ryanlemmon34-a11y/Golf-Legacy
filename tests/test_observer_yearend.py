"""Year-end pages use committed facts and real guarded HTTP decisions, not client-side simulation."""
import json
import re
import unittest
from html import unescape
from pathlib import Path
from types import SimpleNamespace
from tests.test_observer_career import Server, fields, banners
from tests.test_career_year_end import review_fixture
from golfsim import career as CA
import observer_career as UI
import observer_career_yearend as YE

ROOT = Path(__file__).resolve().parents[1]

def answer_form(page, answer):
    for part in page.split('<form ')[1:]:
        if 'action="/career/decide"' not in part.split('>')[0]:
            continue
        body=part.split('</form>')[0]
        values={k:unescape(v) for k,v in re.findall(r'<input type="hidden" name="(\w+)" value="([^"]*)">',body)}
        if values.get('answer') == answer:
            return values
    raise AssertionError('answer not rendered: '+answer)

class AnnualPresentation(unittest.TestCase):
    def test_all_committed_stage_fixtures_render_valid_options(self):
        for path in sorted((ROOT/'docs/career/year_end_fixtures').glob('*.json')):
            if 'planner' in path.name:
                continue
            ye=json.loads(path.read_text())
            w=SimpleNamespace(live=SimpleNamespace(cursor={'year':ye['year'],'week':52,'phase':'end'},world_id='test'))
            v={'year_end':ye,'version':ye['version']}
            html=YE.panel(w,v)
            self.assertIn('Season transition',html)
            for d in ye['decisions']:
                for choice in d['choices']:
                    self.assertEqual(answer_form(html,choice['key'])['decision'],d['id'])
            if ye['stage']=='choose_newcomer':
                self.assertEqual(html.count('<article class="newcomer-card">'),len(ye['candidates']))
                self.assertIn('list is fixed',html)
            for forbidden in ('peak_age','ceilings','aging_rate'):
                self.assertNotIn(forbidden,html)

    def test_null_review_data_does_not_become_zero(self):
        ye=json.loads((ROOT/'docs/career/year_end_fixtures/1_season_review.json').read_text())
        ye['review']['income']=None
        ye['review']['complete']=False
        html=YE.review_html(ye['review'])
        self.assertIn('Not recorded',html)
        self.assertIn('Partial record',html)
        self.assertIn('Not profit or net earnings',html)
        self.assertEqual(UI.plan_command({'block':'2029-1','w1':'work'},lambda f,k:f.get(k))['weeks']['1'],{'kind':'work'})

    def test_paid_work_control_uses_engine_availability_and_wage(self):
        week={'week':1,'current':{'kind':'work'},'events':[],'selected':[],'injured_until':None,
              'work':{'available':True,'wage':900,'why':''},'money':0}
        v={'status':'active','golfer':{'fatigue':0,'injured_until':None},'plannable':[[2029,1]],'readiness':{}}
        p={'weeks':[week],'version':1,'policy':None}
        w=SimpleNamespace(live=SimpleNamespace(career=v,career_planner={(2029,1):p},
                         cursor={'year':2029,'week':1,'phase':'week'},world_id='test'))
        _,html=UI.plan_page(w,{'block':['2029-1']})
        self.assertIn('value="work" checked',html)
        self.assertIn('Weekly wage: $900',html)
        week['work']['available']=False
        self.assertNotIn('value="work"',UI.plan_page(w,{'block':['2029-1']})[1])

    def test_new_golfer_never_inherits_previous_players_rating_delta(self):
        old={'year':2028,'weeks':[{'golfer_id':1}]}
        new={'year':2029,'weeks':[{'golfer_id':2}]}
        self.assertEqual(UI.current_recaps({'golfer':{'id':2},'recaps':[old,new]}),[new])
        self.assertEqual(UI.current_recaps({'golfer':{'id':2},'recaps':[old]}),[])

class AnnualHTTP(unittest.TestCase):
    def advance(self,srv):
        page=srv.get('/career')
        srv.post('/career/advance',dict(fields(page,'/career/advance'),mode='next'))
        job=srv.job()
        self.assertNotEqual(job['state'],'failed',job)

    def test_keep_actual_golfer_through_winter_via_forms(self):
        srv=Server(self,review_fixture())
        gid=srv.session().season.career.golfer_id
        page=srv.get('/career')
        self.assertIn('Your season. Your next chapter.',page)
        f=answer_form(page,'keep')
        bad=srv.post('/career/decide',dict(f,answer='not-an-option',op='invalid-winter'))
        self.assertEqual(banners(bad)[0][0],'err')
        self.assertEqual(srv.session().season.winter_parts_done(2028),0)
        self.assertEqual(banners(srv.post('/career/decide',f))[0][0],'ok')
        generation=srv.session().generation
        srv.post('/career/decide',f)
        self.assertEqual(srv.session().generation,generation)
        for _ in range(10):
            view=CA.view(srv.session().season,srv.session().cursor)
            ye=view['year_end']
            if not ye:
                break
            for d in ye['decisions']:
                # The fixture's first legal option preserves the current path/staff/home.
                page=srv.get('/career')
                result=srv.post('/career/decide',answer_form(page,d['choices'][0]['key']))
                self.assertEqual(banners(result)[0][0],'ok')
            self.advance(srv)
        else:
            self.fail('did not reach next season')
        self.assertEqual(srv.session().cursor['year'],2029)
        self.assertEqual(srv.session().season.career.golfer_id,gid)
        self.assertEqual(srv.session().season.career.status,'active')
        self.assertIn('Plan weeks 1–4 of 2029',srv.get('/career'))
        page=srv.get('/career/plan?block=2029-1')
        plan=fields(page,'/career/plan')
        result=srv.post('/career/plan',dict(plan,w1='rest',w2='rest',w3='rest',w4='rest',selected='decline',qualifying='skip'))
        self.assertEqual(banners(result)[0][0],'ok')
        page=srv.get('/career')
        srv.post('/career/advance',dict(fields(page,'/career/advance'),mode='period'))
        srv.job()
        self.assertEqual(srv.session().cursor['year'],2029)
        self.assertGreater(srv.session().cursor['week'],1)

    def test_switch_stable_candidates_reload_and_choose_via_forms(self):
        srv=Server(self,review_fixture())
        original=srv.session().season.career.golfer_id
        self.assertEqual(banners(srv.post('/career/decide',answer_form(srv.get('/career'),'switch')))[0][0],'ok')
        self.assertIn('Choosing your next golfer',srv.get('/career'))
        self.advance(srv)
        ye=CA.view(srv.session().season,srv.session().cursor)['year_end']
        self.assertEqual(ye['stage'],'choose_newcomer')
        ids=[c['id'] for c in ye['candidates']]
        self.assertEqual(len(ids),10)
        self.assertEqual(len(set(ids)),10)
        path=srv.session().dir
        srv.close()
        srv=Server(self,path)
        ye2=CA.view(srv.session().season,srv.session().cursor)['year_end']
        self.assertEqual(ids,[c['id'] for c in ye2['candidates']])
        page=srv.get('/career')
        f=answer_form(page,str(ids[0]))
        invalid=srv.post('/career/decide',dict(f,answer=str(original),op='bad-candidate'))
        self.assertEqual(banners(invalid)[0][0],'err')
        self.assertEqual(banners(srv.post('/career/decide',f))[0][0],'ok')
        c=srv.session().season.career
        self.assertEqual(c.golfer_id,ids[0])
        self.assertFalse(c.controls(original))
        self.assertEqual(len(c.stints),2)
        self.assertIn('Your golfers',srv.get('/career'))
        self.advance(srv)
        self.assertEqual(srv.session().cursor['year'],2029)
