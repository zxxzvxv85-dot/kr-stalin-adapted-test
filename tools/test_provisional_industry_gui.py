"""Exercise the generated filter and phase guards, without claiming engine QA."""
import unittest
from itertools import product
from national_plan import restore
from PIL import Image
from hoi4_politics_blocks import load, parse
from generate_provisional_industry_gui import ROOT, CATEGORY, DECISIONS, ZONES, ART, decision_patch, render

TR={n.k:n.v for n in load(ROOT/'common/scripted_triggers/RUS_provisional_industry_triggers.txt')}
def check(nodes,state):
 def one(n):
  if n.k in TR:return check(TR[n.k],state)==(n.v=='yes')
  if n.k=='OR':return any(one(x) for x in n.v)
  if n.k=='NOT':return not any(one(x) for x in n.v)
  if n.k=='original_tag':return state['rus']
  if n.k=='is_ai':return state['ai']==(n.v=='yes')
  if n.k=='has_socialist_government':return state['red']==(n.v=='yes')
  if n.k=='has_government':return state['communist']
  if n.k=='has_country_flag':return state['promoted']
  if n.k=='has_country_leader':return state['stalin']
  if n.k=='has_variable':return state['filter'] is not None
  if n.k=='check_variable':return state['filter']==int(n.v[0].v)
  raise AssertionError(n.k)
 return all(one(n) for n in nodes)

class Tests(unittest.TestCase):
 def test_phase_and_filter_boundaries(self):
  _,groups=decision_patch(restore((ROOT/DECISIONS).read_text(encoding='utf8')))
  for rus,ai,red,communist,promoted,stalin in product([False,True],repeat=6):
   stage=rus and not ai and (red or communist) and not (promoted or stalin)
   for selected in [None,0,1,2,3,4]:
    s=dict(rus=rus,ai=ai,red=red,communist=communist,promoted=promoted,stalin=stalin,filter=selected)
    self.assertEqual(check(TR['RUS_rc_provisional_phase'],s),stage)
    for key,values in groups.items():
     self.assertEqual(check(TR['RUS_rc_show_'+key],s),not stage or selected in [None,0] or selected in values)

 def test_filter_is_read_only_and_overview_survives_empty_selection(self):
  cat=next(n for n in parse(restore((ROOT/DECISIONS).read_text(encoding='utf-8-sig'))) if n.k==CATEGORY)
  overview=cat.one('RUS_rc_overview')
  self.assertEqual(overview.value('cost'),'0')
  self.assertNotIn('RUS_rc_filter',overview.one('visible').raw())
  for n in cat.v:
   if n.one('days_mission_timeout'):self.assertNotIn('RUS_rc_show_',n.raw())
  gui=load(ROOT/'common/scripted_guis/RUS_provisional_industry_gui.txt')[0].one('RUS_rc_dashboard')
  for e in gui.one('effects').v:
   body=e.one('hidden_effect').one('if')
   self.assertEqual([x.k for x in body.v],['limit','set_variable','RUS_rc_refresh'])
   self.assertEqual(body.one('set_variable').v[0].k,'RUS_rc_filter')

 def test_assets_hits_and_language_bindings(self):
  plate=Image.open(ROOT/ART/'plate.png').convert('RGBA')
  for name,_,x,y,w,h in ZONES:
   im=Image.open(ROOT/ART/(name+'.png')).convert('RGBA')
   self.assertEqual(im.size,(w,h));self.assertGreater(im.getchannel('A').getextrema()[1],0)
   self.assertLessEqual(x+w,plate.width);self.assertLessEqual(y+h,plate.height)
   # Every opaque button pixel must exactly reconstruct the underlying art.
   bg=plate.crop((x,y,x+w,y+h))
   for a,b in zip(im.get_flattened_data(),bg.get_flattened_data()):
    if a[3]:self.assertEqual(a[:3],b[:3])
  for language in ['english','simp_chinese','russian']:
   data=(ROOT/f'localisation/{language}/RUS_provisional_industry_l_{language}.yml').read_bytes()
   self.assertTrue(data.startswith(b'\xef\xbb\xbf'))
   for name,*_ in ZONES:self.assertIn(('RUS_rc_'+name+'_tt:').encode(),data)

 def test_generation_is_idempotent(self):
  s=restore((ROOT/DECISIONS).read_text(encoding='utf8'));self.assertEqual(decision_patch(s)[0],s)
  self.assertEqual(render(),render())

 def test_gameplay_is_unchanged_except_ui_completion_flag(self):
  import subprocess,re
  before=subprocess.check_output(['git','-C',str(ROOT),'show','HEAD:'+DECISIONS]).decode('utf-8-sig')
  before=restore(before)
  after=restore((ROOT/DECISIONS).read_text(encoding='utf-8-sig'))
  def strip(s):return re.sub(r'(?ms)^[ \t]*# RUS_RECOVERY_LEDGER_BEGIN\n.*?^[ \t]*# RUS_RECOVERY_LEDGER_END[ \t]*\n','',s).replace('RUS_rc_refresh = yes','')
  self.assertEqual([n.norm() for n in parse(strip(before))],[n.norm() for n in parse(strip(after))])
  for rel,text in render().items():self.assertEqual((ROOT/rel).read_text(encoding='utf-8-sig'),text,rel)

 def test_engine_timer_statistics_and_crisis_boundaries(self):
  sg=load(ROOT/'common/scripted_guis/RUS_provisional_industry_gui.txt')[0].one('RUS_rc_dashboard')
  self.assertIsNone(sg.one('triggers').one('_'))
  self.assertNotIn('RUS_rc_blueprint_view',sg.raw())
  calc=load(ROOT/'common/scripted_effects/RUS_provisional_industry_effects.txt')[0].one('if')
  calc.v=[n for n in calc.v if n.k!='limit']
  cat=next(n for n in parse(restore((ROOT/DECISIONS).read_text(encoding='utf-8-sig'))) if n.k==CATEGORY)
  ids=[n.k for n in cat.v if n.one('days_remove') and n.one('remove_effect')]
  self.assertEqual(len(ids),46)
  for crisis in range(7):
   for pattern in range(7):
    timers={k:(-1 if pattern==0 else 0 if pattern==1 else (i+1)*2 if pattern in (2,4,6) else 5 if pattern==3 and i%3==0 else 0) for i,k in enumerate(ids)}
    flags={'RUS_rc_finished_'+k for i,k in enumerate(ids) if i%4==0};v={}
    if pattern in (4,6):flags|={'RUS_rc_settled_'+k for i,k in enumerate(ids) if i%2==0}
    if pattern in (5,6):flags|={'RUS_rc_running_'+k for i,k in enumerate(ids) if i%3==0}
    def value(k):
     try:return float(k)
     except ValueError:return timers.get(k.split('@',1)[1],0) if k.startswith('days_decision_timeout@') else v.get(k,0)
    def pred(n):
     if n.k=='OR':return any(pred(c) for c in n.v)
     if n.k=='NOT':return not any(pred(c) for c in n.v)
     if n.k=='has_idea':return n.v=='RUS_black_monday_'+str(crisis)
     if n.k=='has_country_flag':return n.v in flags
     if n.k=='check_variable':
      c=n.v[0];a,b=value(c.k),value(c.v);return a>b if c.op=='>' else a<b if c.op=='<' else a==b
     return all(pred(c) for c in n.v)
    def run(ns):
     for n in ns:
      if n.k=='if':
       if pred(n.one('limit')):run([x for x in n.v if x.k!='limit'])
      elif n.k in ('set_variable','add_to_variable'):
       c=n.v[0];v[c.k]=(v.get(c.k,0) if n.k=='add_to_variable' else 0)+value(c.v)
      else:raise AssertionError(n.k)
    run(calc.v);active_ids=[k for k in ids if 'RUS_rc_settled_'+k not in flags and (timers[k]>0 or 'RUS_rc_running_'+k in flags)];positive=[timers[k] for k in active_ids if timers[k]>0]
    self.assertEqual(v['RUS_rc_active'],len(active_ids));self.assertEqual(v['RUS_rc_done'],sum('RUS_rc_finished_'+k in flags for k in ids))
    self.assertEqual(v['RUS_rc_next_days'],min(positive,default=0))
    self.assertEqual(v['RUS_rc_recovery_frame'],7-crisis)
    self.assertEqual(v['RUS_rc_scene_frame'],1 if crisis>=5 else 2 if crisis>=3 else 3)
    for key,*_ in ZONES:
     self.assertEqual(v['RUS_rc_frame_'+key],2 if v['RUS_rc_active_'+key]>0 else 3 if v['RUS_rc_done_'+key]>0 else v['RUS_rc_scene_frame'])

 def test_dynamic_sprite_frames_match_click_overlays(self):
  import numpy as np
  scene=Image.open(ROOT/ART/'dynamic/scene.png').convert('RGBA')
  self.assertEqual(scene.size,(492*3,394))
  for name,_,x,y,w,h in ZONES:
   sprite=Image.open(ROOT/ART/'dynamic'/(name+'.png')).convert('RGBA')
   self.assertEqual(sprite.size,(w*3,h))
   for frame in range(3):
    actual=np.array(sprite.crop((frame*w,0,(frame+1)*w,h)));expected=np.array(scene.crop((frame*492+x,y,frame*492+x+w,y+h)))
    mask=actual[:,:,3]>0;self.assertTrue(np.array_equal(actual[:,:,:3][mask],expected[:,:,:3][mask]))

if __name__=='__main__':unittest.main()
