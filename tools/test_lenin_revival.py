"""Execute imported route boundaries and check all 62 focuses against source.

The bounded interpreter does not emulate engine civil-war allocation or rendering.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import unittest
from doudizhu_script_model import ScriptModel
from hoi4_politics_blocks import load,parse,KR
from import_lenin_revival import ROOT,SOURCE,TRAIT,ACCEPTANCE,render_outputs,source_files

TREE=load(ROOT/'common/national_focus/00_RUS_lenin_revival_focus.txt')[0]
FOCUSES={n.value('id'):n for n in TREE.children('focus')}
EVENTS={n.value('id'):n for n in load(ROOT/'events/00_RUS_lenin_revival_events.txt') if n.k=='country_event'}
EFFECTS={n.k:n for n in load(ROOT/'common/scripted_effects/RUS_lenin_revival_effects.txt')}
EFFECTS['RUS_opening_finish_phase']=next(n for n in load(ROOT/'common/scripted_effects/RUS_savinkov_opening_effects.txt') if n.k=='RUS_opening_finish_phase')
TRIGGERS={n.k:n for n in load(ROOT/'common/scripted_triggers/RUS_lenin_revival_triggers.txt')}
DECISION=load(ROOT/'common/decisions/00_RUS_lenin_revival_decisions.txt')[0].v[0]
IDEAS={n.k:n for n in load(ROOT/'common/ideas/00_RUS_lenin_revival_ideas.txt')[0].one('country').v}

class Model(ScriptModel):
    def __init__(self):
        super().__init__(EFFECTS)
        self.original='RUS';self.government='national_populist';self.tree='RUS_savinkov_opening_tree'
        self.ideas=set();self.done=set();self.queue=[];self.seen=set();self.civilwar=False
        self.pp=0;self.stability=0;self.war_support=0;self.manpower=0;self.xp=0
        self.leader=None;self.leader_ideology=None;self.traits=[];self.leader_creations=0
        self.tree_loads=[];self.tech=[];self.equipment=0;self.rebel=None
        self.exists=True
    def check(self,nodes):
        if hasattr(nodes,'v'):nodes=nodes.v
        for n in nodes:
            if n.k=='original_tag':ok=self.original==n.v
            elif n.k=='has_government':ok=self.government==n.v
            elif n.k=='has_country_leader':ok=self.leader==n.value('name')
            elif n.k=='has_completed_focus':ok=n.v in self.done
            elif n.k=='exists':ok=self.exists==(n.v=='yes')
            elif n.k=='custom_trigger_tooltip':ok=self.check([x for x in n.v if x.k!='tooltip'])
            elif n.k=='any_country':
                if len(n.v)==1 and n.value('civilwar_target')=='ROOT':ok=self.civilwar
                else:ok=self.rebel is not None and self.rebel.check(n.v)
            elif n.k in TRIGGERS:ok=self.check(TRIGGERS[n.k])==(n.v=='yes')
            else:ok=super().check([n])
            if not ok:return False
        return True
    def run(self,nodes):
        native={'add_political_power','add_stability','add_war_support','add_manpower','army_experience',
            'add_ideas','remove_ideas','set_politics','load_focus_tree','mark_focus_tree_layout_dirty',
            'set_government_flags','set_party_name','create_country_leader','set_cosmetic_tag',
            'country_event','start_civil_war','add_tech_bonus','add_equipment_to_stockpile','add_popularity'}
        pending=[]
        for n in nodes:
            if n.k not in native:pending.append(n);continue
            if pending:super().run(pending);pending=[]
            k,v=n.k,n.v
            if k=='add_political_power':self.pp+=float(v)
            elif k=='add_stability':self.stability+=float(v)
            elif k=='add_war_support':self.war_support+=float(v)
            elif k=='add_manpower':self.manpower+=int(v)
            elif k=='army_experience':self.xp+=int(v)
            elif k in ('add_ideas','remove_ideas'):
                ids=[v] if isinstance(v,str) else [x.k for x in v]
                for key in ids:self.ideas.add(key) if k=='add_ideas' else self.ideas.discard(key)
            elif k=='set_politics':
                self.government=n.value('ruling_party')
                # Execute the real existing immediate government-change handler.
                self.call('RUS_opening_finish_phase')
            elif k=='load_focus_tree':self.tree=n.value('tree');self.tree_loads.append(self.tree)
            elif k=='create_country_leader':
                self.leader=n.value('name');self.leader_ideology=n.value('ideology')
                self.traits=[x.k for x in n.one('traits').v];self.leader_creations+=1
            elif k=='set_party_name':self.party=n.value('name')
            elif k=='set_cosmetic_tag':self.cosmetic=v
            elif k=='country_event':self.queue.append((n.value('id'),int(n.value('days'))))
            elif k=='start_civil_war':
                self.civilwar=True;self.war_size=float(n.value('size'))
                self.rebel=Model();self.rebel.government=n.value('ideology')
                # Deliberately copy flags to test the conservative inheritance case.
                self.rebel.flags=set(self.flags)
                self.rebel.run([x for x in v if x.k not in ('ideology','size')])
            elif k=='add_tech_bonus':self.tech.append(n.norm())
            elif k=='add_equipment_to_stockpile':self.equipment+=int(n.value('amount'))
            elif k in ('mark_focus_tree_layout_dirty','set_government_flags','add_popularity'):pass
            else:raise AssertionError(n.raw())
        if pending:super().run(pending)
    def event(self,eid,choice=0):
        e=EVENTS[eid]
        if eid in self.seen or not self.check(e.one('trigger')):return False
        self.seen.add(eid);self.run([n for n in e.children('option')[choice].v if n.k!='name']);return True
    def finish(self,key):
        focus=FOCUSES[key]
        if any(not any(x.v in self.done for x in p.v) for p in focus.children('prerequisite')):return False
        if focus.one('available') and not self.check(focus.one('available')):return False
        self.done.add(key);self.run(focus.one('completion_reward').v);return True

def entered():
    m=Model();m.flags.add('RUS_opening_active')
    m.ideas.update({'RUS_opening_disordered_industry','RUS_opening_unfinished_land_reform','unrelated_idea'})
    assert m.event('RUS_lenin_revival.1',1)
    return m

class LeninRevivalTests(unittest.TestCase):
    def test_opt_in_decline_and_opening_tree_cannot_overwrite_selected_route(self):
        m=Model();self.assertTrue(m.check(DECISION.one('allowed')));self.assertTrue(m.check(DECISION.one('available')))
        m.run(DECISION.one('complete_effect').v)
        self.assertEqual(m.queue,[('RUS_lenin_revival.1',1)])
        self.assertFalse(m.check(DECISION.one('available')))
        self.assertTrue(m.event('RUS_lenin_revival.1',0));self.assertEqual(m.tree,'RUS_savinkov_opening_tree')
        self.assertEqual(m.pp,25);self.assertFalse(m.event('RUS_lenin_revival.1',1))
        m=entered();self.assertEqual(m.tree,'RUS_lenin_revival_focus');self.assertNotIn('RUS_opening_active',m.flags)
        self.assertEqual(m.ideas,{'unrelated_idea'})
        self.assertTrue(m.finish('RUS_LR_return_to_the_urals'));self.assertTrue(m.finish('RUS_LR_proclaim_the_return'))
        self.assertEqual(m.tree,'RUS_lenin_revival_focus');self.assertNotIn('Russia_Focus',m.tree_loads)
        self.assertEqual(m.leader,'RUS_LR_vladimir_lenin');self.assertEqual(m.leader_ideology,'leninist_subtype')
        self.assertEqual(m.traits,[TRAIT]);m.call('RUS_LR_appoint_lenin');self.assertEqual(m.leader_creations,1)
        early=Model();self.assertTrue(early.event('RUS_lenin_revival.1',1))
        self.assertIn('RUS_opening_finished',early.flags,'Block queued opening initialization even before active is set')
        for original in ('GER','FRA'):
            other=Model();other.original=original;self.assertFalse(other.event('RUS_lenin_revival.1',1))
    def test_all_62_focus_rewards_war_defeat_gate_and_rebel_isolation(self):
        m=entered()
        self.assertFalse(m.event('RUS_lenin_revival.20'));self.assertFalse(m.event('RUS_lenin_revival.21'))
        self.assertFalse(m.event('RUS_lenin_revival.22'))
        order=sorted(FOCUSES,key=lambda k:(int(FOCUSES[k].value('y')),int(FOCUSES[k].value('x'))))
        for key in order:
            self.assertTrue(m.finish(key),key)
            if key=='RUS_LR_revolution_returns':
                self.assertIn(('RUS_lenin_revival.20',1),m.queue)
                self.assertTrue(m.event('RUS_lenin_revival.20'));self.assertEqual(m.war_size,.35)
                self.assertEqual(m.government,'communist');self.assertEqual(m.rebel.government,'radical_socialist')
                self.assertEqual(m.rebel.tree,'generic_focus');self.assertNotIn('RUS_LR_enabled',m.rebel.flags)
                self.assertFalse(m.rebel.event('RUS_lenin_revival.1',1))
                self.assertFalse(m.rebel.check(DECISION.one('visible')))
                m.rebel.call('RUS_LR_appoint_lenin');self.assertIsNone(m.rebel.leader)
            if key=='RUS_LR_sing_and_march':
                self.assertFalse(m.finish('RUS_LR_declare_sr_defeat'))
                self.assertFalse(m.event('RUS_lenin_revival.21'));m.civilwar=False
                self.assertFalse(m.finish('RUS_LR_declare_sr_defeat'),'Ending a war without defeating the surviving rebels is insufficient')
                self.assertFalse(m.event('RUS_lenin_revival.21'));m.rebel.exists=False
            if key=='RUS_LR_declare_sr_defeat':
                self.assertTrue(m.event('RUS_lenin_revival.21'));before=(m.pp,m.stability)
                self.assertFalse(m.event('RUS_lenin_revival.21'));self.assertEqual((m.pp,m.stability),before)
        self.assertEqual(len(m.done),62);self.assertTrue(m.event('RUS_lenin_revival.22'))
        self.assertEqual(m.leader_creations,1);self.assertEqual(m.tree,'RUS_lenin_revival_focus')
        self.assertNotIn('RUS_LR_wartime_economy',m.ideas);self.assertEqual(m.equipment,5000)
        self.assertEqual(len(m.tech),5)
    def test_original_focus_graph_numbers_and_descriptions_are_preserved(self):
        original=parse(source_files()['common/national_focus/00_RUS_lenin_revival_focus.txt'])[0]
        self.assertEqual(len(FOCUSES),62);self.assertEqual(TREE.value('default'),'no')
        self.assertEqual(TREE.one('country').value('factor'),'0')
        for old in original.children('focus'):
            key=old.value('id');new=FOCUSES[key]
            for field in ('icon','cost','x','y'):self.assertEqual(new.value(field),old.value(field),key)
            self.assertEqual([n.norm() for n in new.children('prerequisite')],[n.norm() for n in old.children('prerequisite')])
            reward=[n.norm() for n in new.one('completion_reward').v if n.k!='RUS_LR_appoint_lenin']
            self.assertEqual(reward,[n.norm() for n in old.one('completion_reward').v],key)
        self.assertEqual(len(IDEAS),14);self.assertEqual(len(EVENTS),4)
    def test_gwr_portrait_and_trait_reuse_exact_source_values(self):
        portrait=json.loads((SOURCE/'portrait_source.json').read_text(encoding='utf-8'))
        data=(ROOT/portrait['destination']).read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(),portrait['sha256'])
        from PIL import Image
        with Image.open(ROOT/portrait['destination']) as im:self.assertEqual(im.size,(156,210))
        old=parse((SOURCE/'trait_gwr_source.txt').read_text(encoding='utf-8'))[0]
        current=load(ROOT/'common/country_leader/RUS_lenin_revival_traits.txt')[0].one(TRAIT)
        expected={key:n.v for n in old.v for key in ACCEPTANCE.get(n.k,(n.k,))}
        self.assertEqual({n.k:n.v for n in current.v},expected)
        self.assertEqual(current.value('political_power_factor'),'0.1');self.assertEqual(current.value('war_support_factor'),'-0.05')
    def test_localisation_assets_and_supported_modifiers(self):
        outputs=render_outputs()
        for path,data in outputs.items():self.assertEqual((ROOT/path).read_bytes(),data,path)
        locale={}
        for lang in ('simp_chinese','english'):
            data=(ROOT/f'localisation/{lang}/00_RUS_lenin_revival_l_{lang}.yml').read_bytes()
            self.assertTrue(data.startswith(b'\xef\xbb\xbf'))
            entries=re.findall(r'^\s+([^:#\s]+):\d*\s*(".*")$',data.decode('utf-8-sig'),re.M)
            self.assertEqual(len(entries),len({k for k,v in entries}));locale[lang]=dict(entries)
            for key in [*FOCUSES,*IDEAS,'RUS_LR_vladimir_lenin',TRAIT]:self.assertIn(key,locale[lang])
            for key in FOCUSES:self.assertIn(key+'_desc',locale[lang])
            self.assertNotIn('无变化',data.decode('utf-8-sig'))
        self.assertEqual(locale['simp_chinese'].keys(),locale['english'].keys())
        sprites={}
        game=ROOT.parents[3]/'common/Hearts of Iron IV'
        for base in (game,KR,ROOT):
            for path in (base/'interface').rglob('*.gfx'):
                text=path.read_text(encoding='utf-8-sig',errors='replace')
                sprites.update({key:base for key in re.findall(r'name\s*=\s*"?(GFX_\w+)',text)})
        for data in outputs.values():
            try:text=data.decode('utf-8-sig')
            except UnicodeDecodeError:continue
            for key in re.findall(r'GFX_\w+',text):self.assertIn(key,sprites,key)
        modifiers=(game/'documentation/modifiers_documentation.md').read_text(encoding='utf-8-sig')
        native=set(re.findall(r'^## (\w+)\s*$',modifiers,re.M))|{'communist_drift'}
        # Building modifiers are generated by the engine from building IDs;
        # they are templates, not individual headings in its documentation.
        for path in (game/'common/buildings').glob('*.txt'):
            for root in load(path):
                if root.k=='buildings':native.update('production_speed_'+n.k+'_factor' for n in root.v)
        for idea in IDEAS.values():
            for modifier in idea.one('modifier').v:self.assertTrue(modifier.k in native,modifier.k)
        for forbidden in ('research_time_factor','communism_drift','recruit_character'):
            self.assertFalse(any(re.search(r'\b'+forbidden+r'\s*=',p.read_text(encoding='utf-8-sig')) for p in [ROOT/'common/ideas/00_RUS_lenin_revival_ideas.txt',ROOT/'common/scripted_effects/RUS_lenin_revival_effects.txt']))

if __name__=='__main__':unittest.main(verbosity=2)
