"""Exercise the generated filter and phase guards, without claiming engine QA."""
import unittest
from itertools import product
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
  _,groups=decision_patch((ROOT/DECISIONS).read_text(encoding='utf8'))
  for rus,ai,red,communist,promoted,stalin in product([False,True],repeat=6):
   stage=rus and not ai and (red or communist) and not (promoted or stalin)
   for selected in [None,0,1,2,3,4]:
    s=dict(rus=rus,ai=ai,red=red,communist=communist,promoted=promoted,stalin=stalin,filter=selected)
    self.assertEqual(check(TR['RUS_rc_provisional_phase'],s),stage)
    for key,values in groups.items():
     self.assertEqual(check(TR['RUS_rc_show_'+key],s),not stage or selected in [None,0] or selected in values)

 def test_filter_is_read_only_and_overview_survives_empty_selection(self):
  cat=next(n for n in load(ROOT/DECISIONS) if n.k==CATEGORY)
  overview=cat.one('RUS_rc_overview')
  self.assertEqual(overview.value('cost'),'0')
  self.assertNotIn('RUS_rc_filter',overview.one('visible').raw())
  for n in cat.v:
   if n.one('days_mission_timeout'):self.assertNotIn('RUS_rc_show_',n.raw())
  gui=load(ROOT/'common/scripted_guis/RUS_provisional_industry_gui.txt')[0].one('RUS_rc_dashboard')
  for e in gui.one('effects').v:
   body=e.one('hidden_effect').one('if')
   self.assertEqual([x.k for x in body.v],['limit','set_variable'])
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
  s=(ROOT/DECISIONS).read_text(encoding='utf8');self.assertEqual(decision_patch(s)[0],s)
  self.assertEqual(render(),render())

if __name__=='__main__':unittest.main()
