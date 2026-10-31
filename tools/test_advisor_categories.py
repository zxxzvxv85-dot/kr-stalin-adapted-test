"""Faction filtering contracts. Does not substitute for native UI testing."""
import unittest
from generate_advisor_categories import ROOT, KR, CATEGORIES, FLAG, GUARD, outputs, load, assets

def walk(nodes):
 for n in nodes:
  yield n
  if isinstance(n.v,list):yield from walk(n.v)
def evaluate(n,flags,traits,tag='RUS',social=True,ai=False):
 if n.k=='RUS_ui_use_faction_advisor_filters':return tag=='RUS' and social and not ai
 if n.k=='has_country_flag':return n.v in flags
 if n.k=='has_trait':return n.v in traits
 if n.k=='original_tag':return n.v==tag
 if n.k=='has_socialist_government':return social
 if n.k=='is_ai':return ai
 vals=[evaluate(c,flags,traits,tag,social,ai) for c in n.v]
 if n.k=='OR':return any(vals)
 if n.k=='NOT':return not any(vals)
 return all(vals)
class AdvisorFactionFilter(unittest.TestCase):
 def test_membership_and_bypass(self):
  root=next(n for n in load(ROOT/'common/scripted_triggers/RUS_advisor_faction_filter_triggers.txt') if n.k.startswith(GUARD+'_'))
  self.assertFalse(any(n.k=='has_trait' and n.v.endswith('_bop') for n in walk(root.v)))
  examples=[]
  for row in CATEGORIES:
   branch=next(n for n in root.one('OR').children('AND') if n.value('has_country_flag')==FLAG+row[0])
   examples.append((row[0],next(n.v for n in walk(branch.v) if n.k=='has_trait')))
  for selected,_ in examples:
   flags={FLAG+selected}
   for group,member in examples:
    self.assertEqual(evaluate(root,flags,{member}),selected==group)
    self.assertTrue(evaluate(root,set(),{member}))
    self.assertTrue(evaluate(root,flags,{member},tag='GER'))
    self.assertTrue(evaluate(root,flags,{member},social=False))
    self.assertTrue(evaluate(root,flags,{member},ai=True))
   self.assertFalse(evaluate(root,flags,set()))
  self.assertTrue(evaluate(root,{FLAG+examples[0][0]},{examples[0][1]}))
  self.assertFalse(evaluate(root,{FLAG+examples[0][0]},{examples[1][1]}))
 def test_original_character_graph_preserved(self):
  import subprocess
  from generate_advisor_categories import parse
  baseline='8b9da52' if ROOT.name.endswith('_test') else '3c72da2'
  old=subprocess.check_output(['git','-C',str(ROOT),'show',baseline+':common/characters/RUS characters.txt']).decode('utf-8-sig')
  def normalized(nodes):
   return tuple((n.k,n.op,normalized(n.v) if isinstance(n.v,list) else n.v) for n in nodes if not n.k.startswith(GUARD))
  self.assertEqual(normalized(parse(old)),normalized(load(ROOT/'common/characters/RUS characters.txt')))
 def test_live_government_switch(self):
  roots=load(ROOT/'common/scripted_triggers/RUS_advisor_faction_filter_triggers.txt')
  gate=next(n for n in roots if n.k=='RUS_ui_use_faction_advisor_filters')
  self.assertEqual(gate.value('original_tag'),'RUS');self.assertEqual(gate.value('is_ai'),'no')
  governments={n.v for n in gate.one('OR').children('has_government')}
  self.assertEqual(governments,{'totalist','communist','syndicalist','radical_socialist'})
  self.assertEqual([g in governments for g in ['national_populist','radical_socialist','communist','paternal_autocrat']],[False,True,True,False])
  self.assertFalse(any(n.k in ('has_country_flag','has_socialist_government') for n in walk(gate.v)))
  gui=load(ROOT/'common/scripted_guis/RUS_advisor_faction_bar.txt')[0].v[0]
  self.assertEqual(gui.one('visible').value('RUS_ui_use_faction_advisor_filters'),'yes')
 def test_clicks_only_write_ui_flags(self):
  gui=load(ROOT/'common/scripted_guis/RUS_advisor_faction_bar.txt')[0].v[0]
  self.assertEqual(gui.value('parent_window_name'),'"command_character_view_window"')
  effects=gui.one('effects');self.assertEqual(len(effects.v),11)
  for button in effects.v:
   for n in walk(button.v):
    self.assertIn(n.k,{'if','else','limit','has_country_flag','set_country_flag','clr_country_flag'})
    if n.k.endswith('country_flag'):self.assertTrue(n.v.startswith(FLAG))
  self.assertEqual(len(effects.one('all_click').v),9)
 def test_single_row_native_geometry(self):
  current=(ROOT/'interface/command_character_view.gui').read_text(encoding='utf-8').split('\n',1)[1]
  self.assertEqual(current,(KR/'interface/command_character_view.gui').read_text(encoding='utf-8-sig'))
  bar=load(ROOT/'interface/RUS_advisor_faction_bar.gui')[0].v[0]
  self.assertEqual(bar.one('position').value('y'),'43')
  self.assertEqual(bar.one('size').value('height'),'50')
  buttons=[b for b in bar.children('buttonType') if not b.value('name').startswith('"cover_')]
  self.assertEqual(len(buttons),10)
  for b in buttons:self.assertLessEqual(int(b.one('position').value('x'))+45,500)
  for name in ('cover_lower','cover_upper'):
   b=next(b for b in bar.children('buttonType') if b.value('name')=='"'+name+'"')
   self.assertEqual((b.one('size').value('x'),b.one('size').value('y')),('500','50'))
  self.assertNotIn('name = "GFX_idea_traits_strip"',(ROOT/'interface/zz_RUS_advisor_categories.gfx').read_text())
 def test_generated_outputs_and_guards(self):
  data,count=outputs();self.assertGreater(count,100)
  for name,text in data.items():
   self.assertEqual((ROOT/name).read_text(encoding='utf-8-sig'),text,name)
   if name.endswith('.yml'):self.assertTrue((ROOT/name).read_bytes().startswith(b'\xef\xbb\xbf'))
  triggers=load(ROOT/'common/scripted_triggers/RUS_advisor_faction_filter_triggers.txt')
  definitions={n.k for n in triggers}
  for name,text in data.items():
   self.assertNotIn('$CHARACTER$',text)
   self.assertNotIn('CHARACTER =',text)
   if name.startswith(('common/characters/','common/scripted_effects/','events/')):
    for n in walk(load(ROOT/name)):
     if n.k.startswith(GUARD):
      self.assertEqual(n.v,'yes')
      self.assertIn(n.k,definitions)
  for c in load(ROOT/'common/characters/RUS characters.txt')[0].v:
   for n in c.children('advisor'):
    visible=n.one('visible')
    if visible:
     guards=[v for v in visible.v if v.k.startswith(GUARD)]
     self.assertEqual(len(guards),1)
     self.assertGreater(len(visible.v),1)
     self.assertEqual(guards[0].k,GUARD+'_'+c.k)
  assets(False)
if __name__=='__main__':unittest.main()
