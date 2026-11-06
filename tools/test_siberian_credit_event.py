"""Execute shipped scheduling blocks, assert old rewards/dispatch preserved."""
import json,subprocess,unittest
from pathlib import Path
from hoi4_politics_blocks import parse,load
from generate_siberian_credit_event import ROOT,EVENT,ACTION,ID,NEXT,SCHEDULED,SEEN,FOLLOWUP,TITLE,BODY,OPTION,render_outputs

EVENTS={n.value('id'):n for n in load(ROOT/EVENT) if n.k=='country_event'}

class World:
 def __init__(self):self.flags=set();self.queue=[];self.stability=.5;self.day=0
 def check(self,nodes):
  for n in nodes:
   if n.k=='hidden_trigger':ok=self.check(n.v)
   elif n.k=='NOT':ok=not self.check(n.v)
   elif n.k=='has_country_flag':ok=n.v in self.flags
   else:raise AssertionError(n.raw())
   if not ok:return False
  return True
 def run(self,nodes):
  for n in nodes:
   if n.k=='if':
    if self.check(n.one('limit').v):self.run([x for x in n.v if x.k!='limit'])
   elif n.k=='hidden_effect':self.run(n.v)
   elif n.k=='set_country_flag':self.flags.add(n.v)
   elif n.k=='country_event':self.queue.append((n.value('id'),self.day+int(n.value('days','0'))))
   elif n.k=='add_stability':self.stability+=float(n.v)
   elif n.k=='name':pass
   else:raise AssertionError(n.raw())

class ChainTests(unittest.TestCase):
 def scheduler(self):return next(n for n in EVENTS['rus_stalin_white_revolt_events.1'].one('immediate').v if n.k=='if' and SCHEDULED in n.raw())
 def test_opening_plus_30_and_option_plus_30(self):
  w=World();w.day=17;w.run([self.scheduler()]);self.assertEqual(w.queue,[(ID,47)])
  w.day=47;w.run(EVENTS[ID].one('immediate').v);self.assertEqual(w.stability,.5);self.assertEqual(len(w.queue),1)
  # User may leave the popup open: follow-up counts from the actual click.
  w.day=52;w.run(EVENTS[ID].one('option').v);self.assertAlmostEqual(w.stability,.49);self.assertEqual(w.queue[-1],(NEXT,82))
 def test_duplicate_opening_and_followup(self):
  w=World();w.run([self.scheduler()]);w.run([self.scheduler()]);self.assertEqual(len(w.queue),1)
  w.run(EVENTS[ID].one('option').v);w.run(EVENTS[ID].one('option').v);self.assertEqual([x[0] for x in w.queue].count(NEXT),1)
 def test_manual_early_view_suppresses_natural_duplicate(self):
  w=World();w.run(EVENTS[ID].one('immediate').v);w.run([self.scheduler()]);self.assertEqual(w.queue,[])
 def test_old_direct_calls_removed_without_other_action_changes(self):
  before=subprocess.check_output(['git','show','3d3796d:'+ACTION]).decode('utf-8-sig')
  after=(ROOT/ACTION).read_bytes().decode('utf-8-sig')
  lines=[l for l in before.splitlines(True) if 'id = '+NEXT+' days = 60' not in l]
  self.assertEqual(after,''.join(lines));self.assertEqual(before.count('id = '+NEXT+' days = 60'),2)
 def test_all_old_events_and_opening_effects_preserved(self):
  old={n.value('id'):n for n in parse(subprocess.check_output(['git','show','3d3796d:'+EVENT]).decode('utf-8-sig')) if n.k=='country_event'}
  for key,a in old.items():
   b=EVENTS[key]
   if key!='rus_stalin_white_revolt_events.1':self.assertEqual(a.norm(),b.norm(),key);continue
   self.assertEqual([n.norm() for n in a.one('immediate').v],[n.norm() for n in b.one('immediate').v if not (n.k=='if' and SCHEDULED in n.raw())])
   self.assertEqual([n.norm() for n in a.v if n.k!='immediate'],[n.norm() for n in b.v if n.k!='immediate'])
  self.assertEqual(EVENTS[NEXT].one('option').value('add_war_support'),'0.05')
 def test_single_page_native_effect_and_localisations(self):
  e=EVENTS[ID];self.assertEqual(e.value('fire_only_once'),'yes');self.assertEqual(e.value('is_triggered_only'),'yes')
  self.assertEqual(e.one('trigger').value('has_socialist_government'),'yes');self.assertEqual(len(e.children('option')),1)
  self.assertEqual(e.one('option').value('add_stability'),'-0.01')
  for lang in ('simp_chinese','english','russian'):
   p=ROOT/f'localisation/{lang}/RUS_siberian_credit_l_{lang}.yml';self.assertTrue(p.read_bytes().startswith(b'\xef\xbb\xbf'))
   data={l.strip().split(':0 ',1)[0]:json.loads(l.strip().split(':0 ',1)[1]) for l in p.read_text(encoding='utf-8-sig').splitlines()[1:]}
   self.assertEqual(data,{ID+'.t':TITLE,ID+'.d':BODY,ID+'.a':OPTION})
  self.assertEqual(BODY.count('\n\n'),5);self.assertEqual(BODY.count('（斯拉夫粗口）'),3)
 def test_assets_and_generation(self):
  self.assertTrue((ROOT.parent/'1521695605/gfx/event_pictures/Europe/Russia/GFX_report_event_RUS_partisans1.png').is_file())
  self.assertIn('name = "GFX_report_event_RUS_partisans1"',(ROOT.parent/'1521695605/interface/kaiserreich/event_pictures.gfx').read_text(encoding='utf-8-sig'))
  for path,text in render_outputs().items():
   actual=(ROOT/path).read_bytes().decode('utf-8-sig') if path==ACTION else (ROOT/path).read_text(encoding='utf-8-sig')
   self.assertEqual(actual,text,path)

if __name__=='__main__':unittest.main()
