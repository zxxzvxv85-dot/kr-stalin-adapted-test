"""Execute real stage callbacks and decision awards; no HOI4 rendering claim."""
from pathlib import Path
import json,re,unittest
from collections import defaultdict
from doudizhu_script_model import ScriptModel,load_effects
from hoi4_politics_blocks import load,parse
from generate_military_decision_integration import ROOT,SPEC,IDEAS,FX,NEWFX,DM,CURRENT,REFRESH,ACTIVE,fields,easy_fields,reward_key,val,current
from generate_easy_mode_ideas import is_beneficial

SPEC_DATA=json.loads((ROOT/SPEC).read_text(encoding='utf-8'))
STAGES={k:parse(v)[0] for k,v in SPEC_DATA['stages'].items()}
REWARDS={k:parse(v)[0] for k,v in SPEC_DATA['rewards'].items()}
EFFECTS={}
for path in (FX,NEWFX,Path('common/scripted_effects/RUS_easy_mode_military_effects.txt')):
    EFFECTS.update(load_effects((ROOT/path).read_text(encoding='utf-8-sig')))
IDEA_DEFS={n.k:n for tree in load(ROOT/IDEAS) for cat in tree.v if isinstance(cat.v,list) for n in cat.v}
UNIFIED={n.k:n.v for root in load(ROOT/'common/dynamic_modifiers/RUS_fr_military_reform_dynamic_modifiers.txt') if root.k=='RUS_fr_unified_army_reform' for n in root.v if n.k not in ('icon','custom_modifier_tooltip')}

class Model(ScriptModel):
    def __init__(self,easy=False):
        super().__init__(EFFECTS);self.ideas=set();self.dynamic=set()
        if easy:self.flags.add('RUS_easy_mode_enabled')
    def number(self,value):
        return super().number(value.removeprefix('var:') if isinstance(value,str) else value)
    def check(self,nodes):
        if hasattr(nodes,'v'):nodes=nodes.v
        for n in nodes:
            if n.k=='has_idea':ok=n.v in self.ideas
            elif n.k=='has_dynamic_modifier':ok=n.value('modifier') in self.dynamic
            else:ok=super().check([n])
            if not ok:return False
        return True
    def add_idea(self,key):
        if key in self.ideas:return
        self.ideas.add(key)
        node=IDEA_DEFS.get(key)
        if node and node.one('on_add'):self.run(node.one('on_add').v)
    def remove_idea(self,key):
        if key not in self.ideas:return
        # Native on_remove may still observe has_idea. The stage-code guard
        # must work without relying on the engine deleting the old ID first.
        node=IDEA_DEFS.get(key)
        if node and node.one('on_remove'):self.run(node.one('on_remove').v)
        self.ideas.discard(key)
    def run(self,nodes):
        pending=[]
        native={'add_ideas','remove_ideas','swap_ideas','add_dynamic_modifier','remove_dynamic_modifier','force_update_dynamic_modifier','custom_effect_tooltip','effect_tooltip','every_army_leader'}
        for n in nodes:
            if n.k not in native:pending.append(n);continue
            if pending:super().run(pending);pending=[]
            if n.k=='add_ideas':self.add_idea(n.v)
            elif n.k=='remove_ideas':
                for key in ([n.v] if isinstance(n.v,str) else [x.k for x in n.v]):self.remove_idea(key)
            elif n.k=='swap_ideas':self.remove_idea(n.value('remove_idea'));self.add_idea(n.value('add_idea'))
            elif n.k=='add_dynamic_modifier':self.dynamic.add(n.value('modifier'))
            elif n.k=='remove_dynamic_modifier':self.dynamic.discard(n.value('modifier'))
            # Native tooltips are readonly; leader trait iteration is covered
            # by the retained military controller tests, not this scalar model.
        if pending:super().run(pending)

class Tests(unittest.TestCase):
    def test_all_stages_and_awards_preserve_original_normal_and_easy_totals(self):
        for easy in (False,True):
            for stage,baseline in STAGES.items():
                for key,reward in REWARDS.items():
                    with self.subTest(easy=easy,stage=stage,key=key):
                        m=Model(easy);m.add_idea(stage);m.call(reward_key(key))
                        expected=defaultdict(float)
                        for source in (baseline,reward):
                            for modifier,v in fields(source).items():expected[modifier]+=v+(easy_fields(source).get(modifier,0) if easy else 0)
                        for modifier,v in expected.items():self.assertAlmostEqual(m.vars[current(modifier)],v)
                        self.assertIn(CURRENT,m.dynamic);self.assertNotIn(ACTIVE,m.flags)
                        before=dict(m.vars);m.call(reward_key(key));m.call(REFRESH)
                        self.assertEqual(m.vars,before,'No duplicated decision reward on repeated execution or refresh')
                        if not reward.one('equipment_bonus'):self.assertNotIn(key,m.ideas)

    def test_stage_changes_keep_decision_awards_and_original_stage_differences(self):
        m=Model();first='RUS_fr_reform_disorganisation_4';m.add_idea(first)
        key='RUS_fr_military_democracy_trial_idea';m.call(reward_key(key))
        for level in (3,2,1,0):
            nxt=f'RUS_fr_reform_disorganisation_{level}'
            m.remove_idea(first);self.assertNotIn(CURRENT,m.dynamic)
            m.add_idea(nxt)
            for modifier,v in fields(STAGES[nxt]).items():
                self.assertAlmostEqual(m.vars[current(modifier)],v+fields(REWARDS[key]).get(modifier,0))
            first=nxt

    def test_mode_refresh_and_institutional_entry_points_do_not_reset_results(self):
        m=Model();m.add_idea('RUS_fr_reform_disorganisation_4')
        for name,raw in SPEC_DATA['apply'].items():
            original=parse(raw)[0]
            completed=[n.v for n in original.v if n.k=='set_country_flag']
            m.call(name)
            self.assertTrue(set(completed)<=m.flags)
        before=dict(m.vars);m.flags.add('RUS_easy_mode_enabled');m.call('RUS_easy_mode_refresh_military')
        # The original nested hidden recruitment correction was not doubled.
        m.call(reward_key('RUS_fr_mobilisation_base_correction'))
        self.assertEqual(m.vars[current('recruitable_population_factor')],0)
        m.flags.discard('RUS_easy_mode_enabled');m.call('RUS_easy_mode_refresh_military')
        for key,value in before.items():
            if key!=current('recruitable_population_factor'):self.assertEqual(m.vars[key],value)

    def test_final_stage_transfers_persistent_awards_once_and_drops_corrections(self):
        for before in (False,True):
            for key,reward in REWARDS.items():
                with self.subTest(before=before,key=key):
                    m=Model();m.add_idea('RUS_fr_reform_disorganisation_0')
                    if before:m.call(reward_key(key))
                    m.call('RUS_fr_initialise_unified_army_reform')
                    if not before:m.call(reward_key(key))
                    self.assertNotIn(CURRENT,m.dynamic)
                    self.assertIn('RUS_fr_unified_army_reform',m.dynamic)
                    base=Model();base.add_idea('RUS_fr_reform_disorganisation_0');base.call('RUS_fr_initialise_unified_army_reform')
                    for modifier,v in fields(reward).items():
                        if key.endswith('_correction'):continue
                        self.assertAlmostEqual(m.vars.get(UNIFIED[modifier],0)-base.vars.get(UNIFIED[modifier],0),v)
                    for modifier in fields(reward) if key.endswith('_correction') else ():
                        if modifier in UNIFIED:self.assertEqual(m.vars.get(UNIFIED[modifier],0),base.vars.get(UNIFIED[modifier],0))
                    saved=dict(m.vars);m.call('RUS_fr_initialise_unified_army_reform');m.call(reward_key(key))
                    self.assertEqual(saved,m.vars)

    def test_stage_equipment_and_callbacks_are_preserved_and_carriers_hidden(self):
        root=load(ROOT/IDEAS)[0];visible={n.k for n in root.one('country').v};hidden={n.k for n in root.one('hidden_ideas').v}
        self.assertFalse((STAGES.keys()|REWARDS.keys())&visible)
        self.assertTrue((STAGES.keys()|REWARDS.keys())<=hidden)
        for key,n in STAGES.items():
            self.assertEqual([x.norm() for x in n.children('equipment_bonus')],[x.norm() for x in IDEA_DEFS[key].children('equipment_bonus')])
            self.assertIsNone(IDEA_DEFS[key].one('modifier'))
        # Equipment-only corrections still execute through their hidden carrier.
        for key in ('RUS_fr_equipment_standardisation_correction','RUS_fr_armoured_production_correction'):
            self.assertEqual(REWARDS[key].one('equipment_bonus').norm(),IDEA_DEFS[key].one('equipment_bonus').norm())

if __name__=='__main__':unittest.main(verbosity=2)
