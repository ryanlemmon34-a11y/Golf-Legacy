import copy,json,re,shutil,subprocess,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from observer_career_advice import committed_plan,render_advice

def fixtures():
    p={'block':[2030,1],'weeks':[{'week':1},{'week':2}],'policy':{'selected':'decline','qualifying':'skip'}}
    a={'block':[2030,1],'source':'coach','judge':'A & B','weeks':{
        '1':{'recommended':{'kind':'event','event_id':'2030:OPEN','fallback':{'kind':'train','category':'putting'}},'reasons':[{'code':'stakes','text':'Could earn a place'}],'alternatives':[{'choice':{'kind':'rest'},'for':[{'code':'load','text':'Reduce fatigue'}],'against':[{'code':'time','text':'Miss this event'}]}]},
        '2':{'recommended':{'kind':'train','category':'putting'},'reasons':[{'code':'room','text':'Uncertain room to improve'}],'alternatives':[]}},
       'policy':{'selected':'accept','qualifying':'enter'},'note':'No outcome guaranteed.'}
    return p,{'advice':a}

class CommittedAdvice(unittest.TestCase):
    def test_exact_backend_choices_and_no_saved_policy_change(self):
        p,v=fixtures();before=copy.deepcopy((p,v));out=committed_plan(p,v)
        self.assertEqual(out['advice']['weeks'][0]['choice'],v['advice']['weeks']['1']['recommended'])
        self.assertEqual(out['policy']['selected'],'decline');self.assertEqual((p,v),before)
        h=render_advice(out);self.assertIn('Compare alternatives',h);self.assertIn('Miss this event',h);self.assertIn('A &amp; B',h)
    def test_missing_mismatched_and_partial_never_use_heuristic(self):
        p,v=fixtures()
        self.assertIsNone(committed_plan(p,{})['advice'])
        v['advice']['block']=[2030,5];self.assertIsNone(committed_plan(p,v)['advice'])
        p,v=fixtures();del v['advice']['weeks']['2'];self.assertIsNone(committed_plan(p,v)['advice'])
    def test_self_assessment_label(self):
        p,v=fixtures();v['advice'].update(source='self',judge=None)
        h=render_advice(committed_plan(p,v));self.assertIn('Your planning assessment',h);self.assertIn('Apply suggested plan',h)
    @unittest.skipUnless(shutil.which('node'),'Node not installed')
    def test_atomic_editable_form_application(self):
        p,v=fixtures();script=re.search(r'<script>(.*?)</script>',render_advice(committed_plan(p,v)),re.S).group(1)
        harness="""
const assert=require('assert'); let click;
const radios=['w1:event','w1:rest','w2:train','w2:rest','selected:accept','selected:decline','qualifying:enter','qualifying:skip'].map(x=>{let [name,value]=x.split(':');return {name,value,checked:false,disabled:false}});
const selects={e1:{value:'',options:[{value:'2030:OPEN'}]},f1:{value:'rest',options:[{value:'rest'},{value:'train:putting'}]},c2:{value:'physical',options:[{value:'physical'},{value:'putting'}]}};
const status={};const form={querySelectorAll:()=>radios,elements:{namedItem:n=>selects[n]}};
global.document={querySelector:()=>form,getElementById:id=>id==='accept-coach-advice'?{addEventListener:(e,f)=>click=f}:status};
"""
        verify="""
click();assert.equal(selects.e1.value,'2030:OPEN');assert.equal(selects.c2.value,'putting');assert.ok(status.textContent.includes('Nothing has been saved'));
const first=JSON.stringify([radios,selects]);click();assert.equal(JSON.stringify([radios,selects]),first);
radios.forEach(x=>x.checked=false);selects.e1.value='';selects.c2.options=[];const stale=JSON.stringify([radios,selects]);click();assert.equal(JSON.stringify([radios,selects]),stale);
"""
        subprocess.run(['node','-e',harness+script+verify],check=True,capture_output=True,text=True)
    def test_http_helper_uses_actual_form_not_script_selector(self):
        from tests.test_observer_career import fields
        page='''<script>document.querySelector('form[action="/career/plan"]')</script><form action="/career/plan"><input type="hidden" name="version" value="4"></form>'''
        self.assertEqual(fields(page,'/career/plan'),{'version':'4'})
