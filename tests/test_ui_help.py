"""Context-help mappings and deterministic, accessible HTML contracts."""
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import observer_help as H
from golfsim.ratings import ATTRIBUTES


class Elements(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.tags = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


class HelpTests(unittest.TestCase):
    def test_attributes_and_headings(self):
        for key, label, _, description in ATTRIBUTES:
            self.assertIn("Rating: 0–100.", H.description_for(key))
            self.assertNotEqual(description, H.description_for(key))
            self.assertEqual(H.description_for(key), H.description_for(label))
        for label in ('GIR', 'SG/rd (engine)', 'Putts/GIR', 'Prestige', 'Overall', 'Physical', 'Technical', 'Mental'):
            self.assertTrue(H.description_for(label), label)
        self.assertEqual(H.help_for('Unrecognized'), '')
        self.assertEqual(H.description_for('  gir '), H.description_for('GIR'))
        self.assertEqual(H.help_for('<strong>GIR</strong>'), '')

    def test_causal_descriptions_and_outcome_distinction(self):
        # Mechanics verified in engine.Player/play_hole, season fatigue/injury/rest,
        # and staff fee/partnership functions; labels alone are not explanations.
        mechanics = {
            'power': 'physical reach', 'stamina': 'target number of events',
            'recovery_rate': 'weeks off', 'injury_resistance': 'no direct effect',
            'driving_accuracy': 'sideways spread', 'long_irons': 'effective yards',
            'mid_irons': 'contact-error floor', 'wedges': 'contact errors',
            'ball_flight': 'firm greens', 'chipping': 'failed chips',
            'bunker': 'fairway bunker', 'recovery_play': 'escape from trees',
            'short_putting': 'eight feet', 'lag_putting': 'follow-up putts',
            'green_reading': 'slope', 'striking_consistency': 'mishit risk',
            'putting_consistency': 'short-putt lapses', 'composure': 'pressure',
            'resilience': 'fade faster', 'management': 'judgement errors',
            'focus': 'mental errors',
        }
        self.assertEqual(set(mechanics), {key for key, *_ in ATTRIBUTES})
        for key, phrase in mechanics.items():
            self.assertIn(phrase, H.description_for(key))
        for key in ('scoring', 'distance', 'fairways', 'gir', 'scrambling', 'sand',
                    'putts_round', 'putts_gir', 'birdies', 'bogeys', 'sg_total'):
            self.assertIn('recorded outcome, not a shot-control rating', H.TEXT[key])
        self.assertIn('sponsor income', H.TEXT['prestige_golfer'])
        self.assertIn('fees', H.TEXT['prestige_staff'])
        self.assertIn('ranking points', H.TEXT['prestige_event'])
        self.assertIn('does not change the layout', H.TEXT['prestige_course'])
        self.assertIn('does not increase the worldwide total', H.TEXT['prestige_nation'])
        # Do not confuse a result statistic with the similarly named skill.
        self.assertNotEqual(H.description_for('Fairways'), H.description_for('Driving Accuracy'))
        self.assertIn('Qualifying stages', H.TEXT['starts'])
        self.assertIn('before costs', H.TEXT['prize'])

    def test_escape_and_native_fallback(self):
        text = 'A "quote" & <script>alert(1)</script>'
        html = H.help_trigger('<GIR>', text)
        self.assertNotIn('<script>', html)
        self.assertNotIn('<GIR>', html)
        button = Elements(html).tags[0]
        self.assertEqual(button[0], 'button')
        self.assertEqual(button[1]['title'], text)
        self.assertIn(text, button[1]['aria-label'])
        self.assertEqual(button[1]['type'], 'button')
        self.assertNotIn('tabindex', button[1])  # native keyboard focus

    def test_deterministic_and_sort_separation(self):
        first = H.help_for('GIR')
        H.help_for('Prestige')
        self.assertEqual(first, H.help_for('GIR'))
        attrs = Elements(first).tags[0][1]
        self.assertNotIn('id', attrs)
        self.assertNotIn('href', attrs)
        self.assertEqual(H.help_for('Prestige', 'prestige_staff'), H.help_trigger('Prestige', H.TEXT['prestige_staff']))
        self.assertIn('event.stopPropagation()', H.HELP_JS)
        self.assertIn('event.preventDefault()', H.HELP_JS)

    def test_popover_interaction_contract(self):
        for fragment in ("'focus'", "'mouseenter'", "'Escape'", "'click'", "'blur'",
                         "'aria-describedby'", 'document.body.appendChild(tip)',
                         'getBoundingClientRect()', "button.setAttribute('title', '')"):
            self.assertIn(fragment, H.HELP_JS)
        self.assertIn('position:fixed', H.HELP_CSS)
        self.assertIn(':focus-visible', H.HELP_CSS)
        self.assertIn('if (active) active.removeAttribute', H.HELP_JS)


class HelpIntegrationTests(unittest.TestCase):
    def test_table_help_is_separate_from_sort_and_keeps_values(self):
        import observer as O
        for heads in (None, {0: ('/golfers?sort=reputation', 'descending')}):
            html = O.table(['Prestige', 'GIR'], [['82.5', '71.3%']], heads=heads,
                           help_keys={0: 'prestige_golfer'})
            self.assertIn('<td>82.5</td><td>71.3%</td>', html)
            self.assertIn('sponsor income', html)
            import re
            # Help is a sibling, never nested inside another interactive control.
            self.assertNotRegex(html, r'<(?:a|button)[^>]*>[^<]*<button')
            self.assertEqual(html.count('class="context-help"'), 2)
            self.assertIn('scope="col"', html)

    def test_all_attribute_numbers_remain_beside_descriptions(self):
        from types import SimpleNamespace as NS
        from unittest.mock import patch
        import observer as O
        values = [70.0] + [float(40 + i) for i in range(len(ATTRIBUTES))]
        w = NS(a=None, live=NS(people={1: {'ratings': values}}, cursor={'year': 2030}))
        with patch.object(O.OD, 'rating_snapshots', return_value={}), patch.object(O, 'peak_line', return_value=''):
            body = O._ratings(w, 1, {'golfer': {}})
        self.assertEqual(body.count('class="context-help"'), len(ATTRIBUTES) + 1)
        for value in values:
            self.assertIn(f'<strong>{value:.1f}</strong>', body)
        self.assertIn('physical reach', body)
        self.assertIn('unavailable', body)

    def test_staff_and_aggression_describe_the_correct_mechanics(self):
        from types import SimpleNamespace as NS
        import observer as O
        staff = O._staff_card({'reputation': 72.5}, 'coach')
        self.assertIn('fees', staff)
        self.assertIn('<dd>72.5 ', staff)
        body = O.OH.aggression_section(NS(live=None), 1, {'golfer': {'aggression': 61}})
        self.assertIn('biases choices toward risk', body)
        self.assertIn('<b>61</b> / 100', body)


class HelpBehaviorTests(unittest.TestCase):
    def test_script_focus_hover_dismissal_and_viewport(self):
        import json
        import shutil
        import subprocess
        if not shutil.which('node'):
            self.skipTest('Node is required for the non-browser DOM event harness')
        harness = r'''
const assert = require('assert');
const handlers = {}, win = {}, timers = new Map(); let timerID=0, popup;
class El {
 constructor(text,rect){this.dataset={help:text,helpLabel:'About rating'};this.attrs={title:text};this.style={};this.listeners={};this.hidden=true;this.rect=rect;this.hover=false;}
 setAttribute(k,v){this.attrs[k]=v;}
 removeAttribute(k){delete this.attrs[k];}
 addEventListener(k,fn){this.listeners[k]=fn;}
 getBoundingClientRect(){return this.rect || {width:Math.min(352,parseFloat(this.style.maxWidth)||352),height:Math.min(140,parseFloat(this.style.maxHeight)||140)};}
 matches(){return this.hover;}
 contains(x){return x===this;}
 closest(s){return s==='.context-help'&&this!==popup?this:null;}
 emit(k){let e={target:this,key:k==='keydown'?'Enter':undefined,preventDefault(){this.prevented=true;},stopPropagation(){this.stopped=true;}};this.listeners[k]?.(e);return e;}
}
const first=new El('Driving accuracy changes dispersion.',{left:700,right:722,top:500,bottom:522});
const second=new El('GIR is a recorded outcome.',{left:10,right:32,top:10,bottom:32});
const document={readyState:'complete',activeElement:null,documentElement:{clientWidth:800},
 querySelector(){return null;},querySelectorAll(){return [first,second];},getElementById(){return null;},
 createElement(){popup=new El();return popup;},body:{appendChild(x){assert.strictEqual(x,popup);}},
 addEventListener(k,fn){handlers[k]=fn;}};
const window={innerHeight:600,addEventListener(k,fn){win[k]=fn;}};
const setTimeout=(fn)=>{timers.set(++timerID,fn);return timerID;};
const clearTimeout=(id)=>timers.delete(id);
const flush=()=>{for(const fn of [...timers.values()])fn();timers.clear();};
__SCRIPT__
document.activeElement=first; first.emit('focus');
assert.strictEqual(popup.hidden,false);assert.strictEqual(popup.textContent,first.dataset.help);
assert.strictEqual(first.attrs['aria-describedby'],popup.id);assert.strictEqual(first.attrs.title,'');
assert(parseFloat(popup.style.left)>=8);assert(parseFloat(popup.style.left)+popup.getBoundingClientRect().width<=792);
assert(parseFloat(popup.style.top)+popup.getBoundingClientRect().height<first.rect.top);
handlers.keydown({key:'Escape'});assert.strictEqual(popup.hidden,true);assert(!first.attrs['aria-describedby']);
second.emit('mouseenter');assert.strictEqual(popup.hidden,false);assert.strictEqual(popup.textContent,second.dataset.help);
const click=second.emit('click');assert(click.prevented&&click.stopped);
document.activeElement=null;second.emit('blur');flush();assert.strictEqual(popup.hidden,true);
first.emit('mouseenter');handlers.scroll({target:document});assert.strictEqual(popup.hidden,true);
second.emit('mouseenter');handlers.click({target:{closest:()=>null}});assert.strictEqual(popup.hidden,true);
console.log('hover/focus/Escape/blur/click/scroll/viewport checks passed');
'''
        script=harness.replace('__SCRIPT__', H.HELP_JS)
        result=subprocess.run(['node','-e',script],capture_output=True,text=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('checks passed',result.stdout)


if __name__ == '__main__':
    unittest.main()
