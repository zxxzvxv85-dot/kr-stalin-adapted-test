"""Execute the focus's native exile subset; this is not an HOI4 engine test."""
from copy import deepcopy
from pathlib import Path
import hashlib
import json
import re
import unittest
from hoi4_politics_blocks import R,KR,load
from test_red_germany_integration import world,condition,TRIGGERS

PATH=R/'common/scripted_effects/RUS_german_exile_effects.txt'
EFFECT=load(PATH)[0]
LEADER='GER_willi_munzenberg'

def country(original,exists=True,government='communist'):
    return dict(original=original,exists=exists,government=government,flags=set(),exile_host=None,
        capitulated=False,characters=set(),popularities={},leader=None)

class Model:
    def __init__(self,host='RUS'):
        self.host=host
        self.countries={host:country('RUS'),'GRU':country('GRU',False,'social_democrat'),'GER':country('GER',True,'social_conservative')}
        self.countries['GER']['characters'].add(LEADER)
        self.states={64:dict(germany=True,owner='GER',cores={'GER'}),219:dict(germany=False,owner=host,cores={'RUS'})}
        self.dead=False;self.exile_calls=0;self.previews=0
    def check(self,nodes,tag,previous=None):
        def one(n):
            k,v=n.k,n.v;c=self.countries[tag]
            if k in ('AND','hidden_trigger'):return self.check(v,tag,previous)
            if k=='OR':return any(one(x) for x in v)
            if k=='NOT':return not self.check(v,tag,previous)
            if k in self.countries:return self.check(v,k,tag)
            if k=='original_tag':return c['original']==v
            if k=='country_exists':return self.countries.get(v,{}).get('exists',False)
            if k=='exists':return c['exists']==(v=='yes')
            if k=='has_socialist_government':return (c['government'] in ('communist','totalist','syndicalist','radical_socialist'))==(v=='yes')
            if k=='has_capitulated':return c['capitulated']==(v=='yes')
            if k=='is_government_in_exile':return bool(c['exile_host'])==(v=='yes')
            if k=='has_country_flag':return v in c['flags']
            if k=='has_character':return v in c['characters']
            if k=='has_country_leader':
                assert n.value('ruling_only')=='yes'
                return c['leader']==n.value('character')
            if k==LEADER:return self.check(v,tag,previous)
            if k=='is_dead':return self.dead==(v=='yes')
            if k=='any_country_with_original_tag':return any(self.check(v,t,tag) for t,x in self.countries.items() if x['original']==c['original'])
            raise AssertionError(n.raw())
        return all(one(n) for n in nodes)
    def run(self,nodes,tag=None,previous=None):
        tag=tag or self.host;matched=False
        for n in nodes:
            k,v=n.k,n.v;c=self.countries[tag]
            if k in ('if','else_if','else'):
                if k=='if':matched=False
                if not matched and (k=='else' or self.check(n.one('limit').v,tag,previous)):
                    self.run([x for x in v if x.k!='limit'],tag,previous);matched=True
                continue
            matched=False
            if k in self.countries:self.run(v,k,tag)
            elif k=='hidden_effect':self.run(v,tag,previous)
            elif k=='effect_tooltip':self.previews+=1
            elif k=='every_state':
                limit=n.one('limit');assert len(limit.v)==1 and limit.value('is_germany')=='yes'
                assert len(v)==2 and n.value('add_core_of')=='GRU'
                for state in self.states.values():
                    if state['germany']:state['cores'].add('GRU')
            elif k=='set_country_flag':c['flags'].add(v)
            elif k=='set_cosmetic_tag':c['cosmetic']=v
            elif k=='set_politics':c['government']=n.value('ruling_party');c['elections']=n.value('elections_allowed')
            elif k=='set_party_name':c['party']=n.value('name')
            elif k=='set_popularities':c['popularities']={x.k:float(x.v) for x in v}
            elif k=='set_government_flags':c['government_flags_refreshed']=True
            elif k=='become_exiled_in':
                assert n.value('target')=='PREV'
                c['exile_host']=previous;c['exists']=True;c['legitimacy']=int(n.value('legitimacy'));self.exile_calls+=1
            elif k==LEADER:
                owner=next(t for t,x in self.countries.items() if LEADER in x['characters'])
                assert [x.k for x in v]==['set_nationality','add_country_leader_role']
                assert n.value('set_nationality')=='PREV'
                self.countries[owner]['characters'].remove(LEADER);c['characters'].add(LEADER)
                role=n.one('add_country_leader_role');assert role.value('promote_leader')=='yes'
                c['leader']=LEADER;c['leader_ideology']=role.one('country_leader').value('ideology')
            elif k=='create_country_leader':c['leader']=n.value('name');c['leader_ideology']=n.value('ideology')
            else:raise AssertionError(n.raw())
    def finish_focus(self):
        focus=next(n for n in load(R/'common/national_focus/00_RUS_future_foreign_policy_skeleton.txt') if n.value('id')=='RUS_future_foreign_034')
        reward=focus.one('completion_reward')
        assert len(reward.v)==1 and reward.value(EFFECT.k)=='yes'
        self.run(EFFECT.v)

class GermanExileTests(unittest.TestCase):
    def test_original_focus_fields_remain_identical(self):
        focus=next(n for n in load(R/'common/national_focus/00_RUS_future_foreign_policy_skeleton.txt') if n.value('id')=='RUS_future_foreign_034')
        def content(nodes):
            return [[n.k,n.op,content(n.v) if isinstance(n.v,list) else n.v] for n in nodes
                if n.k not in ('x','y','relative_position_id','offset','uncomplete_national_focus')]
        baseline=json.loads((R/'tools/test_support/foreign_policy_baseline.json').read_text(encoding='utf-8'))['focuses']['RUS_future_foreign_034']
        fields=content([n for n in focus.v if n.k!='completion_reward'])
        self.assertEqual(hashlib.sha256(json.dumps(fields,ensure_ascii=False).encode()).hexdigest(),baseline['content_sha256'])
        self.assertEqual((int(focus.value('x')),int(focus.value('y'))),(baseline['x'],baseline['y']))
    def test_landless_socialist_exile_in_actual_russian_host_once(self):
        for host in ('RUS','D04'):
            for government in ('communist','totalist','syndicalist','radical_socialist'):
                m=Model(host);m.countries[host]['government']=government;before=deepcopy(m.countries[host]);m.finish_focus()
                c=m.countries['GRU']
                self.assertEqual(c['government'],'communist');self.assertEqual(c['exile_host'],host)
                self.assertEqual(c['cosmetic'],'GRU_red_germany');self.assertEqual(c['legitimacy'],25)
                self.assertEqual(c['leader'],LEADER);self.assertEqual(c['leader_ideology'],'marxism_leninism_subtype')
                self.assertEqual(sum(c['popularities'].values()),100);self.assertEqual(c['popularities']['communist'],55)
                self.assertNotIn('GRU_red_germany_established',c['flags']);self.assertNotIn('GRU_reconstruction_ongoing',c['flags'])
                self.assertEqual(m.countries[host],before);self.assertEqual(m.previews,1);self.assertEqual(m.exile_calls,1)
                self.assertEqual(m.states[64]['owner'],'GER');self.assertIn('GRU',m.states[64]['cores'])
                self.assertEqual(m.states[219],dict(germany=False,owner=host,cores={'RUS'}))
                snapshot=deepcopy(m.countries);m.finish_focus();self.assertEqual(m.countries,snapshot);self.assertEqual(m.exile_calls,1)
    def test_existing_and_annexed_reconstruction_or_exile_are_untouched(self):
        for target,dynamic in [('GRU',False),('D07',True)]:
            for status in ('exists','reconstructed','exiled'):
                m=Model()
                if dynamic:m.countries[target]=country('GRU',False,'market_liberal')
                c=m.countries[target]
                if status=='exists':c['exists']=True
                if status=='reconstructed':c['flags'].add('GRU_red_germany_established')
                if status=='exiled':c['exile_host']='FRA'
                snapshot=deepcopy((m.countries,m.states));m.finish_focus();self.assertEqual(snapshot,(m.countries,m.states));self.assertEqual(m.exile_calls,0)
    def test_host_eligibility_and_leader_absence_or_death(self):
        for blocked in ('wrong_tag','not_socialist','capitulated'):
            m=Model()
            if blocked=='wrong_tag':m.countries[m.host]['original']='GER'
            if blocked=='not_socialist':m.countries[m.host]['government']='social_democrat'
            if blocked=='capitulated':m.countries[m.host]['capitulated']=True
            snapshot=deepcopy(m.countries);m.finish_focus();self.assertEqual(snapshot,m.countries)
        for unavailable in ('absent','dead','ruling'):
            m=Model();m.dead=unavailable=='dead'
            if unavailable=='absent':m.countries['GER']['characters'].clear()
            if unavailable=='ruling':m.countries['GER']['leader']=LEADER
            before=deepcopy(m.countries['GER'])
            m.finish_focus();self.assertEqual(m.countries['GRU']['leader'],'RUS_german_exile_council');self.assertEqual(m.exile_calls,1)
            self.assertEqual(m.countries['GER'],before)
    def test_exile_does_not_enter_postwar_reconstruction(self):
        w=world();w['countries']['GRU']['exile_host']='RUS'
        self.assertFalse(condition(TRIGGERS['GRU_can_become_red_germany'].v,w,'GRU'))
        w['countries']['GRU']['exile_host']=None
        self.assertTrue(condition(TRIGGERS['GRU_can_become_red_germany'].v,w,'GRU'))
    def test_native_references_and_localised_fallback(self):
        game=R.parents[3]/'common/Hearts of Iron IV'
        triggers=(game/'documentation/triggers_documentation.md').read_text(encoding='utf-8-sig')
        effects=(game/'documentation/effects_documentation.md').read_text(encoding='utf-8-sig')
        for key in ('any_country_with_original_tag','is_government_in_exile'):self.assertIn('## '+key,triggers)
        for key in ('become_exiled_in','set_nationality','add_country_leader_role'):self.assertIn('## '+key,effects)
        kr=(KR/'common/on_actions/on_actions_China.txt').read_text(encoding='utf-8-sig')
        self.assertIn('CHI = { become_exiled_in = { target = FRA legitimacy = 10 } }',kr)
        self.assertIn('GFX_portrait_unknown',(KR/'interface/_leader_portraits.gfx').read_text(encoding='utf-8-sig'))
        for lang in ('simp_chinese','english','russian'):
            data=(R/f'localisation/{lang}/RUS_german_exile_l_{lang}.yml').read_bytes()
            self.assertTrue(data.startswith(b'\xef\xbb\xbf'));self.assertEqual(len(re.findall(r'^ RUS_german_exile_council:',data.decode('utf-8-sig'),re.M)),1)

if __name__=='__main__':unittest.main(verbosity=2)
