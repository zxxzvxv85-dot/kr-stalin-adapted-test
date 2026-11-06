"""Execute shipped law dispatch and test isolation/boundaries; not engine QA."""
import copy, subprocess, unittest
from pathlib import Path
from PIL import Image
from hoi4_politics_blocks import parse, load
from generate_socialist_conscription import ROOT,KR,FOCI,VANILLA,STATS,IDEAS,FX,TR,TECH,KEYS,law,render_outputs

FXS={n.k:n for n in load(ROOT/FX)}
LAWS={n.k:n for n in load(ROOT/IDEAS)[0].one('mobilization_laws').v}
CONTEXT=load(ROOT/TR)[0]
ALL=set(LAWS)|set(VANILLA)

class Model:
 def __init__(self):
  self.tag='RUS';self.red=True;self.ger=True;self.surrender=0.;self.done=set();self.flags=set();self.ideas={'limited_conscription'};self.tech=set();self.pp=500;self.swaps=0;self.units=set()
 def check(self,nodes):
  for n in nodes:
   if n.k in ('hidden_trigger','custom_trigger_tooltip'):ok=self.check([x for x in n.v if x.k!='tooltip'])
   elif n.k=='OR':ok=any(self.check([x]) for x in n.v)
   elif n.k=='NOT':ok=not self.check(n.v)
   elif n.k=='RUS_sc_context':ok=self.check(CONTEXT.v)==(n.v=='yes')
   elif n.k=='original_tag':ok=self.tag==n.v
   elif n.k=='has_socialist_government':ok=self.red==(n.v=='yes')
   elif n.k=='country_exists':assert n.v=='GER';ok=self.ger
   elif n.k=='has_completed_focus':ok=n.v in self.done
   elif n.k=='has_country_flag':ok=n.v in self.flags
   elif n.k=='has_idea':ok=n.v in self.ideas
   elif n.k=='has_tech':ok=n.v in self.tech
   elif n.k=='always':ok=n.v=='yes'
   elif n.k=='surrender_progress':
    assert n.op=='>';ok=self.surrender>float(n.v)
   else:raise AssertionError(('condition',n.raw()))
   if not ok:return False
  return True
 def execute(self,nodes):
  matched=False
  for n in nodes:
   if n.k in ('if','else_if','else'):
    if n.k=='if':matched=False
    yes=not matched and (n.k=='else' or self.check(n.one('limit').v))
    if yes:self.execute([x for x in n.v if x.k!='limit']);matched=True
   elif n.k=='hidden_effect':self.execute(n.v)
   elif n.k=='effect_tooltip':pass
   elif n.k in FXS:self.execute(FXS[n.k].v)
   elif n.k=='add_ideas':
    current=self.ideas & ALL
    for old in current:
     if old in LAWS:self.execute(LAWS[old].one('on_remove').v)
    self.ideas-=ALL;self.ideas.add(n.v);self.swaps+=1
    if n.v in LAWS:self.execute(LAWS[n.v].one('on_add').v)
   elif n.k=='set_technology':
    for t in n.v:
     if t.k=='popup':continue
     if t.v=='1':self.tech.add(t.k)
     else:self.tech.discard(t.k)
   elif n.k=='set_country_flag':self.flags.add(n.v)
   elif n.k=='unlock_subunit':self.units.add(n.v)
   elif n.k in ('set_temp_variable','mobilisation_laws_on_add_effect'):pass # KR bookkeeping, unchanged
   else:raise AssertionError(('effect',n.raw()))
 def call(self,key='RUS_sc_refresh'):self.execute(FXS[key].v)
 def current(self):return next(iter(self.ideas & ALL))
 def manual(self,i):
  n=LAWS[law(i)]
  if self.current()==law(i) or not self.check(n.one('visible').v) or not self.check(n.one('available').v) or self.pp<150:return False
  self.pp-=150;self.execute(parse('add_ideas = '+law(i)));return True

class LawsTest(unittest.TestCase):
 def test_entry_and_each_focus_immediate(self):
  m=Model();m.call();self.assertEqual(m.current(),law(1));self.assertIn('militia',m.units)
  for i in (2,3,4):m.call('RUS_sc_focus_'+str(i));self.assertEqual(m.current(),law(i))
  self.assertEqual(m.pp,500)
 def test_completed_focus_catchup(self):
  for i,f in enumerate(FOCI,2):
   m=Model();m.done.add(f);m.call();self.assertEqual(m.current(),law(i))
 def test_strict_thresholds_and_priority(self):
  for ratio,want in ((0,4),(.2,4),(.20001,5),(.5,5),(.50001,6),(.99,6)):
   m=Model();m.done.update(FOCI);m.surrender=ratio;m.call();self.assertEqual(m.current(),law(want))
 def test_crisis_without_focus_and_focus_during_crisis(self):
  m=Model();m.surrender=.6;m.call();self.assertEqual(m.current(),law(6))
  m.call('RUS_sc_focus_3');self.assertEqual(m.current(),law(6))
  m.surrender=0;m.call();self.assertEqual(m.current(),law(3))
 def test_daily_refresh_no_repeat_charge_or_swap(self):
  m=Model();m.call();s=m.swaps
  for _ in range(30):m.call()
  self.assertEqual((m.pp,m.swaps),(500,s))
 def test_locked_manual_all_six(self):
  m=Model();m.call()
  for i in range(1,7):self.assertFalse(m.manual(i))
 def test_post_germany_manual_three_choices_and_no_overwrite(self):
  m=Model();m.ger=False;m.surrender=.9;m.call();self.assertEqual(m.current(),law(2))
  for i in (3,4,2):
   before=m.pp;self.assertTrue(m.manual(i));self.assertEqual(m.pp,before-150)
   for _ in range(3):m.call()
   self.assertEqual(m.current(),law(i))
  for i in (1,5,6):self.assertFalse(m.manual(i))
 def test_post_germany_emergency_released(self):
  m=Model();m.done.update(FOCI);m.surrender=.8;m.call();self.assertEqual(m.current(),law(6))
  m.ger=False;m.call();self.assertEqual(m.current(),law(4))
 def test_no_money_or_same_law_no_purchase(self):
  m=Model();m.ger=False;m.call();self.assertFalse(m.manual(2));m.pp=149;self.assertFalse(m.manual(3));self.assertEqual(m.pp,149)
 def test_country_and_government_isolation(self):
  for tag,red in (('GER',True),('FRA',True),('RUS',False)):
   m=Model();m.tag=tag;m.red=red;m.call();self.assertEqual(m.current(),'limited_conscription');self.assertFalse(m.tech)
   for n in LAWS.values():self.assertFalse(m.check(n.one('visible').v))
 def test_supply_reversible_and_foreign_tech_never_granted(self):
  m=Model();m.call('RUS_sc_focus_2');self.assertEqual(m.tech,{'RUS_sc_territorial_supply'})
  for _ in range(3):m.call()
  self.assertEqual(m.tech,{'RUS_sc_territorial_supply'})
  m.call('RUS_sc_focus_3');self.assertFalse(m.tech)
  m.ger=False;m.manual(2);self.assertTrue(m.tech);m.red=False;m.call();self.assertFalse(m.tech);self.assertEqual(m.current(),'limited_conscription')
 def test_native_laws_unchanged_except_russia_visibility(self):
  source=load(KR/'common/ideas/00 Laws.txt')[0];patched=load(ROOT/'common/ideas/00 Laws.txt')[0]
  for old,new in zip(source.v,patched.v):
   self.assertEqual(old.k,new.k)
   if old.k!='mobilization_laws':self.assertEqual(old.norm(),new.norm());continue
   for a,b in zip(old.v,new.v):
    if a.k not in VANILLA:self.assertEqual(a.norm(),b.norm());continue
    self.assertEqual(tuple(x.norm() for x in a.v),tuple(x.norm() for x in b.v if x.k!='visible'))
    m=Model();self.assertFalse(m.check(b.one('visible').v));m.tag='GER';self.assertTrue(m.check(b.one('visible').v));m.tag='RUS';m.red=False;self.assertTrue(m.check(b.one('visible').v))
 def test_exact_stats_costs_and_native_registration(self):
  for i in range(1,7):
   n=LAWS[law(i)];self.assertEqual(n.value('cost'),'150');self.assertEqual(int(n.value('level')),7-i)
   got={x.k:float(x.v) for x in n.one('modifier').v if x.k!='custom_modifier_tooltip'};self.assertEqual(got,STATS[i-1])
  self.assertEqual(STATS[2]['army_org_regain'],-.15)
  self.assertEqual([STATS[i]['war_stability_factor'] for i in (3,4,5)],[-.2,-.5,-.8])
  registered=(KR/'common/units/unit_modifiers/unit_modifiers.txt').read_text(encoding='utf-8-sig')
  for stats in STATS:
   for k in stats:
    if k.startswith('modifier_army_sub_unit_'):self.assertIn(k,registered)
  tech=load(ROOT/TECH)[0].one('RUS_sc_territorial_supply');self.assertEqual(tech.one('militia').value('supply_consumption'),'-0.15')
 def test_focus_rewards_preserved_except_added_hook(self):
  for path,ids in [('common/national_focus/RUS focus (Russia).txt',FOCI[:2]),('common/national_focus/00_RUS_future_foreign_policy_skeleton.txt',FOCI[2:])]:
   before=parse(subprocess.check_output(['git','show','f5b47fa:'+path]).decode('utf-8-sig'));after=load(ROOT/path)
   def focus(nodes,fid):return next(n for t in nodes for n in ([t] if t.k=='shared_focus' else t.children('focus')) if n.value('id')==fid)
   for fid in ids:
    a=focus(before,fid).one('completion_reward');b=focus(after,fid).one('completion_reward')
    self.assertEqual([n.norm() for n in a.v],[n.norm() for n in b.v if not n.k.startswith('RUS_sc_focus_')])
 def test_assets_and_generator_stability(self):
  for key in KEYS:
   im=Image.open(ROOT/'gfx/interface/ideas'/('RUS_sc_'+key+'.dds'));self.assertEqual(im.size,(64,64));self.assertEqual(im.convert('RGBA').getpixel((0,0))[3],0)
  for path,text in render_outputs().items():self.assertEqual((ROOT/path).read_text(encoding='utf-8-sig'),text,path)

if __name__=='__main__':unittest.main()
