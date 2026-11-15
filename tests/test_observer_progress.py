import copy
import unittest
from types import SimpleNamespace as N
from unittest.mock import patch
from tests.test_observer_career import Server,fields,banners
import observer_career as UI
from observer_career_progress import opportunities,goals,staff_search,timeline

class ProgressPresentation(unittest.TestCase):
    def test_exact_rule_and_status_no_invented_admission(self):
        row={'event':{'id':'2030:Q','series_id':'Q','label':'Qualifier','week':10,'year':2030},
             'condition':{'text':'Top 39 across the allocated heats'},'target':{'id':'2030:C','series_id':'C','label':'Championship','week':22,'year':2030},
             'status':'needs_result','route':{'label':'College qualifying'},'restrictions':['Already qualified golfers cannot enter again']}
        before=copy.deepcopy(row);html=opportunities([row])
        self.assertIn('Top 39',html);self.assertIn('week 22 of 2030',html)
        self.assertIn('Result required',html);self.assertNotIn('Already qualified</span>',html)
        self.assertEqual(row,before)
    def test_market_choice_has_real_yes_no_forms(self):
        v={'pending':[{'id':'D1','kind':'market_choice','text':'Look for a coach?','deadline':[2030,1],'options':['yes','no']}], 'resolved':[],'version':1}
        with patch.object(UI,'hidden',return_value=''):
            html=UI.decisions_card(N(),v)
        self.assertIn('>Yes</button>',html);self.assertIn('>No</button>',html)
        self.assertEqual(html.count('action="/career/decide"'),2)
    def test_readonly_has_no_goal_or_staff_writes(self):
        v={'status':'active','date':[2030,1],'goals':[],'staff_policy':{}}
        w=N(read_only=True)
        self.assertNotIn('<form',goals(w,v));self.assertEqual(staff_search(w,v),'')

class ProgressHTTP(unittest.TestCase):
    def test_goal_staff_commands_idempotence_and_invalid_fields(self):
        srv=Server(self)
        page=srv.get('/career')
        page=srv.post('/career/start',fields(page,'/career/start'))
        f=fields(page,'/career/set_goal')
        bad=srv.post('/career/set_goal',dict(f,kind='world_rank',top='bad',by_year='2028'))
        self.assertIn('Nothing was changed',bad)
        request=dict(f,kind='world_rank',top='50',by_year='2028')
        page=srv.post('/career/set_goal',request)
        self.assertIn('Goal saved',page)
        count=len(srv.session().season.career.goals)
        srv.post('/career/set_goal',request)
        self.assertEqual(len(srv.session().season.career.goals),count)
        page=srv.get('/career')
        page=srv.post('/career/staff_policy',dict(fields(page,'/career/staff_policy'),seek_coach='ask',seek_caddie='no'))
        self.assertEqual(srv.session().season.career.staff_policy['seek_coach'],'ask')
        page=srv.post('/career/drop_goal',fields(page,'/career/drop_goal'))
        self.assertIn('Goal dropped',page)
        self.assertEqual(srv.session().season.career.goals[-1]['status'],'dropped')


class CalendarSupport(unittest.TestCase):
    def test_v3_is_supported_without_bypassing_engine_guard(self):
        import observer_worlds as WL
        info={'format_ok':True,'same_engine':True,'calendar':'v3'}
        self.assertEqual(WL.unsupported(info),[])
        info['same_engine']=False
        self.assertTrue(any('earlier engine' in x for x in WL.unsupported(info)))
        info.update(same_engine=True,calendar='v1')
        self.assertEqual(WL.unsupported(info),['the classic calendar (v1)'])

class V3WorldHTTP(unittest.TestCase):
    def test_new_world_v3_reopens_without_guard_bypass(self):
        from golfsim.population import generate_world
        import observer_worlds as WL
        srv=Server(self)
        with patch('golfsim.population.generate_world',side_effect=lambda **kw:generate_world(**kw,scale=.05)):
            srv.post('/worlds/create',{'name':'v3-check','seed':'11','start_year':'2027'})
            result=srv.job()
        self.assertEqual(result['state'],'done',result)
        info=WL.inspect(srv.lib/'v3-check')
        self.assertEqual(info['calendar'],'v3')
        self.assertTrue(info['can_resume'],info)
        srv.post('/worlds/close',{})
        srv.post('/worlds/open',{'name':'v3-check'})
        result=srv.job()
        self.assertEqual(result['state'],'done',result)
        self.assertFalse(srv.app.world.read_only)
