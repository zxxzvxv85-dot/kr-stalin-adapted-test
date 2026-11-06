"""Opening spirit handoff only; no agriculture progress is completed/reset."""
import copy,subprocess,unittest
from pathlib import Path
from hoi4_politics_blocks import load,parse
import rework_savinkov_opening as build

ROOT=Path(__file__).resolve().parents[1]
PATH='common/scripted_effects/RUS_savinkov_opening_effects.txt'
KEY='RUS_opening_finish_phase'
OLD='RUS_opening_unfinished_land_reform'
NEW='RUS_pre_maximalist_land_reform'
FX={n.k:n for n in load(ROOT/PATH)}

class State:
 def __init__(self):
  self.tag='RUS';self.socialist=False;self.gov='national_populist';self.ideas={OLD};self.flags={'RUS_opening_active'};self.loads=[]
  self.progress={'RUS_maximalist_land_reform_score':37.5,'RUS_nat_reform_score':12,'RUS_nat_installed':500,'RUS_nat_machine_stock':72}
  self.swaps=0
 def check(self,nodes):
  for n in nodes:
   if n.k=='NOT':ok=not self.check(n.v)
   elif n.k=='original_tag':ok=self.tag==n.v
   elif n.k=='has_socialist_government':ok=self.socialist==(n.v=='yes')
   elif n.k=='has_idea':ok=n.v in self.ideas
   elif n.k=='has_country_flag':ok=n.v in self.flags
   elif n.k=='has_government':ok=self.gov==n.v
   else:raise AssertionError(n.raw())
   if not ok:return False
  return True
 def run(self,nodes):
  for n in nodes:
   if n.k=='if':
    if self.check(n.one('limit').v):self.run([x for x in n.v if x.k!='limit'])
   elif n.k=='swap_ideas':self.ideas.discard(n.value('remove_idea'));self.ideas.add(n.value('add_idea'));self.swaps+=1
   elif n.k=='clr_country_flag':self.flags.discard(n.v)
   elif n.k=='set_country_flag':self.flags.add(n.v)
   elif n.k=='load_focus_tree':self.loads.append((n.value('tree'),n.value('keep_completed')))
   elif n.k=='mark_focus_tree_layout_dirty':pass
   else:raise AssertionError(n.raw()) # Progress writes/helpers fail closed.
 def refresh(self):self.run(FX[KEY].v)

class HandoffTests(unittest.TestCase):
 def test_savinkov_unchanged(self):
  s=State();before=copy.deepcopy(s.__dict__);s.refresh();self.assertEqual(s.__dict__,before)
 def test_socialist_transition_and_idempotency(self):
  s=State();s.socialist=True;s.gov='radical_socialist';p=s.progress.copy();s.refresh();s.refresh()
  self.assertEqual(s.ideas,{NEW});self.assertEqual(s.swaps,1);self.assertEqual(s.progress,p);self.assertEqual(s.loads,[('Russia_Focus','yes')])
 def test_already_finished_opening_still_hands_over(self):
  s=State();s.gov='authoritarian_democrat';s.refresh();self.assertIn(OLD,s.ideas)
  s.gov='communist';s.socialist=True;s.refresh();self.assertEqual(s.ideas,{NEW});self.assertEqual(len(s.loads),1)
 def test_foreign_country_no_handoff(self):
  s=State();s.tag='FRA';s.flags.clear();s.gov='syndicalist';s.socialist=True;before=copy.deepcopy(s.__dict__);s.refresh();self.assertEqual(s.__dict__,before)
 def test_no_unfinished_idea_does_not_grant_or_downgrade(self):
  s=State();s.gov='communist';s.socialist=True;s.ideas={'RUS_nat_land_reform_stage_4'};s.refresh();self.assertEqual(s.ideas,{'RUS_nat_land_reform_stage_4'});self.assertEqual(s.swaps,0)
 def test_real_old_spirit_is_pre_reform_not_positive_final(self):
  ideas=load(ROOT/'common/ideas/RUS stalin maximalist land reform ideas.txt')[0].one('country')
  n=ideas.one(NEW);mods={x.k:float(x.v) for x in n.one('modifier').v if x.k!='custom_modifier_tooltip'}
  self.assertEqual(mods,{'stability_factor':-.2,'political_power_factor':-.2,'consumer_goods_expected_value':.2})
  self.assertNotIn('RUS_maximalist_land_reform_stage_5',FX[KEY].raw())
 def test_old_phase_logic_preserved_and_source_matches(self):
  old={n.k:n for n in parse(subprocess.check_output(['git','show','3659291:'+PATH]).decode('utf-8-sig'))}
  for k,n in old.items():
   if k!=KEY:self.assertEqual(n.norm(),FX[k].norm(),k)
   else:self.assertEqual([x.norm() for x in n.v],[x.norm() for x in FX[k].v[1:]])
  self.assertEqual((ROOT/PATH).read_text(encoding='utf-8-sig'),build.render_effects()+'\n'+build.startup_effect())

if __name__=='__main__':unittest.main()
