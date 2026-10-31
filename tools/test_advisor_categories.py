"""Native filter contracts and role-specific trait-preservation model."""
import unittest,random,subprocess,re
import generate_advisor_categories as g
from native_advisor_filters import strip_hooks,correct_identities,MARKER

def walk(ns):
 for n in ns:
  yield n
  if isinstance(n.v,list):yield from walk(n.v)
def norm(ns):return tuple((n.k,n.op,norm(n.v) if isinstance(n.v,list) else n.v) for n in ns if not n.k.startswith(g.GUARD))
class NativeFilters(unittest.TestCase):
 def test_generated_and_idempotent(self):
  data,count=g.outputs();self.assertGreaterEqual(count,48)
  for name,s in data.items():self.assertEqual((g.ROOT/name).read_bytes().decode('utf-8-sig') if name.startswith('history/') else (g.ROOT/name).read_text(encoding='utf-8-sig'),s,name)
  g.assets(False)
 def test_real_trait_definitions_unchanged(self):
  p=g.ROOT/'common/country_leader/RUS_native_advisor_filter_traits.txt'
  traits=g.load(p)[0].v;self.assertEqual(len(traits),9)
  for i,t in enumerate(traits,19):
   self.assertEqual(t.value('sprite'),str(i));self.assertEqual({n.k for n in t.v},{'sprite','random'})
 def test_native_ui_owns_filter(self):
  gui=(g.ROOT/'interface/command_character_view.gui').read_text(encoding='utf-8')
  self.assertIn('filter_grid',gui);self.assertIn('max_slots_horizontal = 10',gui)
  self.assertNotIn('RUS_advisor_faction_bar',gui)
  self.assertEqual(g.load(g.ROOT/'common/scripted_guis/RUS_advisor_faction_bar.txt')[0].v,[])
  self.assertNotIn('add_advisor_role',(g.ROOT/'common/scripted_effects/RUS_advisor_ui_refresh_effects.txt').read_text())
  self.assertNotIn('recruit_character',(g.ROOT/'common/scripted_effects/RUS_native_advisor_filter_effects.txt').read_text())
 def test_original_scripts_except_hooks_and_requested_identities(self):
  paths=subprocess.check_output(['git','-C',str(g.ROOT),'-c','core.safecrlf=false','diff','--name-only','HEAD']).decode().splitlines()
  # All existing runtime sources written by this generator preserve their AST,
  # after removing UI conditions/hooks and the two requested identity changes.
  for rel in paths:
   if not rel.endswith('.txt') or not rel.startswith(('common/characters/','common/scripted_effects/','events/')):continue
   if rel.endswith(('RUS_advisor_ui_refresh.txt','RUS_advisor_ui_refresh_effects.txt','RUS_native_advisor_filter_effects.txt')):continue
   old=subprocess.check_output(['git','-C',str(g.ROOT),'show','HEAD:'+rel]).decode('utf-8-sig')
   if g.ROOT.name.endswith('_local') and rel in ['common/scripted_effects/RUS_stalin_kamenev_bop_effects.txt','common/scripted_effects/RUS_stalin_relationship_scaled_advisor_tier_effects.txt','events/RUS events (Russia).txt','events/stalin_form_sov.txt']:continue
   old=correct_identities(strip_hooks(old),g)
   self.assertEqual(norm(g.parse(old)),norm(g.parse(strip_hooks((g.ROOT/rel).read_text(encoding='utf-8-sig')))),rel)
 def test_fixed_factions_and_other_traits(self):
  chars=g.load(g.ROOT/'common/characters/RUS characters.txt')[0]
  for char,wanted in [('RUS_lev_kamenev','KR_vst_left_kamenev'),('RUS_sergey_kirov','KR_bolshevik_kirov'),('RUS_grigory_zinovyev','KR_vst_left_zinovyev')]:
   c=chars.one(char)
   for role in c.children('advisor'):
    ts=[n.k for n in role.one('traits').v]
    identities=[t for t in ts if any(t.startswith(r[4]) for r in g.CATEGORIES)]
    self.assertEqual(identities,[wanted])
   self.assertTrue(any(not t.startswith('KR_vst_') for a in c.children('advisor') for t in [n.k for n in a.one('traits').v]))
 def test_bootstrap_and_dan_profession_not_used_as_faction(self):
  gate=g.load(g.ROOT/'common/scripted_triggers/RUS_advisor_faction_filter_triggers.txt')[0]
  self.assertEqual(gate.value('has_country_flag'),'RUS_ui_nf_new_game')
  history=(g.ROOT/'history/countries/RUS - Russia.txt').read_text(encoding='utf-8-sig')
  self.assertIn('set_country_flag = RUS_ui_nf_new_game',history)
  self.assertIn('RUS_ui_nf_sync_all = yes',history)
  helpers=g.load(g.ROOT/'common/scripted_effects/RUS_native_advisor_filter_effects.txt')
  dan=next(n for n in helpers if n.k=='RUS_ui_nf_order_RUS_fyodor_dan_second_in_command')
  selection=[n for n in dan.one('if').children('if') if n.one('set_temp_variable')]
  flags={n.v for part in selection for n in walk(part.one('limit').v) if n.k=='has_character_flag'}
  self.assertIn('RUS_ui_nf_second_in_command_KR_vst_right_dan',flags)
  self.assertFalse(any('menshevik_grandfather' in f or 'menshevik_doctor' in f for f in flags))
 def test_slot_specific_trait_preservation(self):
  nodes=g.load(g.ROOT/'common/scripted_effects/RUS_native_advisor_filter_effects.txt')
  rng=random.Random(31);cases=0
  for helper in [n for n in nodes if n.k.startswith('RUS_ui_nf_order_')]:
   slot=helper.one('if').one('limit').value('has_advisor_role')
   ids=list(dict.fromkeys(n.value('trait') for n in walk(helper.v) if n.k=='remove_trait' and not n.value('trait').startswith(MARKER)))
   for _ in range(12):
    real=[t for t in ids if rng.random()<.35];state=list(real);flags={'RUS_ui_nf_'+slot+'_'+t for t in real};variables={}
    if rng.random()<.5:
     row=rng.choice(g.CATEGORIES)[0];state.insert(0,MARKER+row);flags.add('RUS_ui_nf_marker_'+slot+'_'+row)
    def pred(n):
     if n.k=='has_advisor_role':return n.v==slot
     if n.k=='has_character_flag':return n.v in flags
     if n.k=='check_variable':return all(variables.get(c.k,0)==float(c.v) for c in n.v)
     if n.k=='NOT':return not any(pred(c) for c in n.v)
     if n.k=='OR':return any(pred(c) for c in n.v)
     return all(pred(c) for c in n.v)
    def run(ns):
     for n in ns:
      if n.k=='if':
       if pred(n.one('limit')):run([c for c in n.v if c.k!='limit'])
      elif n.k=='set_temp_variable':
       for c in n.v:variables[c.k]=float(c.v)
      elif n.k=='set_character_flag':flags.add(n.v)
      elif n.k=='clr_character_flag':flags.discard(n.v)
      elif n.k=='remove_trait':
       t=n.value('trait')
       if t in state:state.remove(t)
      elif n.k=='add_trait':
       t=n.value('trait')
       if t not in state:state.append(t)
      else:raise AssertionError(n.k)
    run(helper.v)
    self.assertCountEqual([t for t in state if not t.startswith(MARKER)],real)
    markers=[t for t in state if t.startswith(MARKER)]
    self.assertLessEqual(len(markers),1)
    if markers:self.assertEqual(state[0],markers[0])
    cases+=1
  self.assertGreater(cases,500)
if __name__=='__main__':unittest.main()
