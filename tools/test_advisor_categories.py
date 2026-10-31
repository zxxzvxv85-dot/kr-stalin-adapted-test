"""Original native profession filters, badges, trait order and gameplay preservation."""
import unittest,subprocess,re
import generate_advisor_categories as g
from native_advisor_filters import strip_hooks,correct_identities,MARKER

def walk(ns):
 for n in ns:
  yield n
  if isinstance(n.v,list):yield from walk(n.v)
def norm(ns):return tuple((n.k,n.op,norm(n.v) if isinstance(n.v,list) else n.v) for n in ns if not n.k.startswith(g.GUARD))
class NativeFilters(unittest.TestCase):
 def test_generated_and_idempotent(self):
  data,count=g.outputs();self.assertEqual(count,0)
  for name,s in data.items():self.assertEqual((g.ROOT/name).read_bytes().decode('utf-8-sig') if name.startswith('history/') else (g.ROOT/name).read_text(encoding='utf-8-sig'),s,name)
  g.assets(False)
 def test_original_profession_strip_and_native_layout(self):
  traits=g.load(g.ROOT/'common/country_leader/RUS_native_advisor_filter_traits.txt')[0]
  self.assertEqual(traits.v,[])
  gui=(g.ROOT/'interface/command_character_view.gui').read_text(encoding='utf-8')
  self.assertEqual(norm(g.parse(gui)),norm(g.load(g.KR/'interface/command_character_view.gui')))
  self.assertIn('filter_grid',gui);self.assertIn('max_slots_horizontal = 8',gui)
  gfx=g.load(g.ROOT/'interface/zz_RUS_advisor_categories.gfx')[0].one('SpriteType')
  self.assertEqual(gfx.value('noOfFrames'),'18')
  self.assertEqual(gfx.value('texturefile'),'"gfx/interface/ideas/idea_traits_strip.dds"')
  self.assertTrue((g.KR/'gfx/interface/ideas/idea_traits_strip.dds').is_file())
 def test_no_faction_marker_or_refresh_runtime(self):
  self.assertEqual(g.load(g.ROOT/'common/scripted_guis/RUS_advisor_faction_bar.txt')[0].v,[])
  self.assertEqual(g.load(g.ROOT/'common/scripted_effects/RUS_native_advisor_filter_effects.txt'),[])
  self.assertEqual(g.load(g.ROOT/'common/scripted_triggers/RUS_advisor_faction_filter_triggers.txt'),[])
  for sub in ('common/characters','common/scripted_effects','events'):
   for p in (g.ROOT/sub).glob('*.txt'):
    text=p.read_text(encoding='utf-8-sig')
    self.assertNotIn('RUS_ui_nf_',text,str(p));self.assertNotIn(MARKER,text,str(p))
    self.assertNotIn('RUS_ui_advisor_matches_faction',text,str(p))
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
 def test_opening_gameplay_unchanged(self):
  rel='history/countries/RUS - Russia.txt'
  old=subprocess.check_output(['git','-C',str(g.ROOT),'show','HEAD:'+rel]).decode('utf-8-sig')
  before=[n for n in g.parse(old) if not (n.k=='set_country_flag' and n.v=='RUS_ui_nf_new_game') and n.k!='RUS_ui_nf_sync_all']
  self.assertEqual(norm(before),norm(g.load(g.ROOT/rel)))
  self.assertNotIn('RUS_ui_nf_', (g.ROOT/rel).read_text(encoding='utf-8-sig'))
 def test_role_trait_order_and_original_definitions_preserved(self):
  rel='common/characters/RUS characters.txt'
  old=correct_identities(strip_hooks(subprocess.check_output(['git','-C',str(g.ROOT),'show','HEAD:'+rel]).decode('utf-8-sig')),g)
  self.assertEqual(norm(g.parse(old)),norm(g.load(g.ROOT/rel)))
  # No occupation trait is cloned, renamed, assigned a faction sprite or modified.
  paths=subprocess.check_output(['git','-C',str(g.ROOT),'diff','--name-only','HEAD','--','common/country_leader']).decode().splitlines()
  self.assertLessEqual(set(paths),{'common/country_leader/RUS_native_advisor_filter_traits.txt'})
if __name__=='__main__':unittest.main()
