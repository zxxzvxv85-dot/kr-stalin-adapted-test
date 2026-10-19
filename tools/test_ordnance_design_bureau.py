"""Actual-script regression model, not a substitute for engine verification."""
from pathlib import Path
from decimal import Decimal as D
import copy,json,re,subprocess
import xml.etree.ElementTree as ET
from hoi4_politics_blocks import load,parse,tokens
import generate_ordnance_design_bureau as build
R=build.ROOT
ORG=build.ORG
SPEC=json.loads(build.SPEC_PATH.read_text(encoding='utf-8'))
FX={n.k:n for n in load(R/'common/scripted_effects/RUS_ordnance_design_bureau_effects.txt')}
MIO=load(R/'common/military_industrial_organization/organizations/RUS_ordnance_design_bureau.txt')[0]
TRAITS={n.value('token'):n for n in MIO.children('trait')}
IDEAS={n.k:n for n in load(R/'common/ideas/RUS_ordnance_design_bureau_ideas.txt')[0].one('hidden_ideas').v}

class Model:
    def __init__(self):
        self.country={'vars':{'TOZ_Divisions':D(7),'TOZ_Required_Funds':D(350)},'flags':set(),'ideas':set(),'traits':set()}
        self.mios={m:{'vars':{'size':D(6),'funds':D(275),'research_bonus':D(0),'modifier@military_industrial_organization_research_bonus':D(0)},'flags':set(),'ideas':set(),'traits':set(),'active':True} for m in [ORG]+[n['source'] for n in SPEC['nodes'] if n.get('source')]}
        self.temps={};self.current=self.country;self.stack=[];self.awards=[];self.tech=set();self.decisions=[];self.day=0;self.grants=[]
        self.divisions=[D(1) for _ in range(20)]
        self.missions={'RUS_TOZ_Medals_automatic_mission':6}
        self.mios['RUS_toz_organisation']['flags'].add('TOZ_Medal_Decision_Taken')
    def obj(self,scope):
        if scope in ['FROM','ROOT']:return self.country
        if scope=='PREV':return self.stack[-1]
        raise AssertionError(scope)
    def value(self,v):
        if isinstance(v,list):
            ans=D(0)
            for n in v:
                x=self.value(n.v) if n.k!='clamp' else None
                if n.k=='value':ans=x
                elif n.k=='add':ans+=x
                elif n.k=='subtract':ans-=x
                elif n.k=='multiply':ans*=x
                elif n.k=='divide':ans/=x
                elif n.k=='clamp':ans=max(self.value(n.value('min')),min(self.value(n.value('max')),ans))
                else:raise AssertionError(n.k)
            return ans
        try:return D(v)
        except Exception:pass
        if v.startswith('var:'):v=v[4:]
        if '.' in v and v.split('.')[0] in ['ROOT','FROM','PREV']:
            s,v=v.split('.',1);o=self.current;self.current=self.obj(s);a=self.value(v);self.current=o;return a
        if '?' in v:
            key,default=v.split('?');return self.current['vars'].get(key,D(default))
        if v in self.temps:return self.temps[v]
        if v=='research_bonus':return self.current['vars'].get(v,D(0))+self.current['vars'].get('modifier@military_industrial_organization_research_bonus',D(0))
        return self.current['vars'].get(v,D(0))
    def scoped(self,o,fn):
        self.stack.append(self.current);old=self.current;self.current=o
        result=fn();self.current=old;self.stack.pop();return result
    def available(self,o):
        for n in SPEC['nodes']:
            if n.get('source') and self.mios[n['source']] is o:
                return 'RUS_odb_merged_'+n['id'] not in self.country['flags']
        return True
    def cond(self,nodes):
        def one(n):
            if n.k in ['FROM','PREV','ROOT']:return self.scoped(self.obj(n.k),lambda:self.cond(n.v))
            if n.k.startswith('mio:'):return self.scoped(self.mios[n.k[4:]],lambda:self.cond(n.v))
            if n.k in ['hidden_trigger','AND']:return self.cond(n.v)
            if n.k=='OR':return any(one(x) for x in n.v)
            if n.k=='NOT':return not self.cond(n.v)
            if n.k in ['has_country_flag','has_mio_flag']:return n.v in self.current['flags']
            if n.k=='has_variable':return n.v in self.current['vars']
            if n.k=='has_dlc_aat':return True
            if n.k=='is_mio_trait_completed':return n.v in self.current['traits']
            if n.k=='is_mio_available':return self.available(self.current)
            if n.k=='is_mio_assigned_to_task':return self.current['active']
            if n.k=='is_military_industrial_organization':return self.current is self.mios.get(n.v)
            if n.k=='check_variable':
                x=n.v[0];a,b=self.value(x.k),self.value(x.v)
                return a>b if x.op=='>' else a<b if x.op=='<' else a==b
            raise AssertionError(('condition',n.k))
        return all(one(n) for n in nodes)
    def run(self,nodes):
        matched=False
        for n in nodes:
            k,v=n.k,n.v
            if k in ['if','else_if','else']:
                if k=='if':matched=False
                if not matched and (k=='else' or self.cond(n.one('limit').v)):
                    self.run([x for x in v if x.k!='limit']);matched=True
            elif k in ['FROM','PREV','ROOT']:self.scoped(self.obj(k),lambda:self.run(v))
            elif k.startswith('mio:'):self.scoped(self.mios[k[4:]],lambda:self.run(v))
            elif k in ['hidden_effect']:self.run(v)
            elif k in FX:self.run(FX[k].v)
            elif k in ['effect_tooltip','custom_effect_tooltip','unlock_decision_tooltip','show_mio_tooltip','show_ideas_tooltip']:pass
            elif k in ['set_country_flag','set_mio_flag']:self.current['flags'].add(v)
            elif k in ['set_variable','set_temp_variable','add_to_variable','subtract_from_variable']:
                x=v[0];name=x.k;amount=self.value(x.v)
                target=self.current['vars']
                if name.split('.')[0] in ['ROOT','FROM','PREV']:
                    scope,name=name.split('.',1);target=self.obj(scope)['vars']
                if k=='set_temp_variable':target=self.temps
                if k=='add_to_variable':amount+=target.get(name,D(0))
                if k=='subtract_from_variable':amount=target.get(name,D(0))-amount
                target[name]=amount
            elif k=='clear_variable':self.current['vars'].pop(v,None)
            elif k in ['add_mio_funds','add_mio_size','add_mio_research_bonus','set_mio_research_bonus']:
                key={'add_mio_funds':'funds','add_mio_size':'size'}.get(k,'research_bonus')
                self.current['vars'][key]=max(D(0),(D(0) if k.startswith('set_') else self.current['vars'].get(key,D(0)))+self.value(v))
            elif k=='set_temp_variable_to_random':self.temps[n.value('var')]=self.value(n.value('min'))
            elif k=='random_military_industrial_organization':
                eligible=[o for o in self.mios.values() if self.scoped(o,lambda:self.cond(n.one('limit').v))]
                if eligible:
                    o=eligible[0];self.scoped(o,lambda:self.run([x for x in v if x.k!='limit']));self.grants.append(o)
            elif k in ['add_ideas','remove_ideas']:
                (self.current['ideas'].add if k=='add_ideas' else self.current['ideas'].discard)(v)
            elif k=='set_technology':self.tech.update(x.k for x in v)
            elif k=='activate_targeted_decision':self.decisions.append(n.value('decision'))
            elif k=='for_loop_effect':
                for _ in range(int(self.value(n.value('end')))):self.run([x for x in v if x.k not in ['start','end','compare']])
            elif k=='random_country_division':
                chosen=next((i for i,o in enumerate(self.divisions) if o>D('.02')),None)
                if chosen is not None:
                    self.divisions[chosen]=D('.01');self.awards.append(int(self.country['vars']['RUS_odb_medal_rank']))
            else:raise AssertionError(('effect',k))
    def fx(self,key,mio=None):
        if mio:self.scoped(self.mios[mio],lambda:self.run(FX[key].v))
        else:self.run(FX[key].v)
    def buy(self,key):
        t=TRAITS[key];o=self.mios[ORG]
        if key in o['traits']:return False
        if any(p not in o['traits'] for p in tokens(t.one('all_parents'))):return False
        if any(p in o['traits'] for p in tokens(t.one('mutually_exclusive'))):return False
        if t.one('available') and not self.scoped(o,lambda:self.cond(t.one('available').v)):return False
        o['traits'].add(key)
        if t.one('on_complete'):self.scoped(o,lambda:self.run(t.one('on_complete').v))
        return True

def main():
    w=Model();w.fx('RUS_odb_unlock');o=w.mios[ORG]
    o['vars']['RUS_odb_investment_rank']=D(3);w.fx('RUS_odb_unlock');assert o['vars']['RUS_odb_investment_rank']==3
    # Full levels/funds transfer exactly once, without any donor trait completions.
    for node in [n for n in SPEC['nodes'] if n.get('source')]:
        w=Model();before=copy.deepcopy((w.country['vars'],w.missions,w.decisions))
        w.fx('RUS_odb_merge_'+node['id'],ORG)
        assert w.mios[ORG]['vars']['size']==12 and w.mios[ORG]['vars']['funds']==550
        assert w.mios[node['source']]['vars']['funds']==0 and not w.available(w.mios[node['source']])
        w.fx('RUS_odb_merge_'+node['id'],ORG)
        assert w.mios[ORG]['vars']['size']==12 and w.mios[ORG]['vars']['funds']==550
        if node['id']=='toz':
            assert w.country['vars']['TOZ_Divisions']==7 and w.country['vars']['TOZ_Required_Funds']==350
            assert (w.missions,w.decisions)==before[1:]
            for rank in range(11):
                w.awards=[];w.divisions=[D(1)]*20;w.country['vars']['RUS_odb_medal_rank']=D(rank)
                w.fx('RUS_odb_hand_out_medals');assert len(w.awards)==7 and set(w.awards)=={rank}
    # Untouched and missing donor medal settings both work without changing timers.
    w=Model();w.country['vars'].clear();w.mios['RUS_toz_organisation']['flags'].clear()
    w.fx('RUS_odb_merge_toz',ORG)
    assert w.country['vars']['TOZ_Divisions']==4 and w.country['vars']['TOZ_Required_Funds']==500
    assert set(w.decisions)=={'RUS_TOZ_Medals','RUS_TOZ_Medals_automatic'}
    # Manual/automatic share the very same payer, before and after merger.
    for merged in [False,True]:
        w=Model();w.mios[ORG]['vars']['funds']=D(1000);w.mios['RUS_toz_organisation']['vars']['funds']=D(1000)
        if merged:w.country['flags'].add('RUS_odb_merged_toz')
        w.fx('RUS_odb_pay_medal_funds')
        assert w.mios[ORG if merged else 'RUS_toz_organisation']['vars']['funds']==650
        assert w.mios['RUS_toz_organisation' if merged else ORG]['vars']['funds']==1000
    # All incoming parents, not merely one, and the two terminal branches are exclusive.
    w=Model();w.mios[ORG]['traits']={'RUS_odb_imz'}
    assert not w.buy('RUS_odb_production');w.mios[ORG]['traits'].add('RUS_odb_modular');assert w.buy('RUS_odb_production')
    for chosen,other in [('land','cannon_research'),('cannon_research','land'),('testing','production'),('production','testing')]:
        w=Model();w.mios[ORG]['traits'].update({'RUS_odb_barrels','RUS_odb_toz','RUS_odb_imz','RUS_odb_modular'})
        assert w.buy('RUS_odb_'+chosen);assert not w.buy('RUS_odb_'+other)
    # Repeat spending at exactly 1000 is forbidden; >1000, ten purchases, no eleventh.
    w=Model();o=w.mios[ORG];o['traits'].add('RUS_odb_cannon_research')
    o['vars']['funds']=D(1000);assert not w.buy('RUS_odb_investment_1')
    o['vars']['funds']=D(10001)
    assert not w.buy('RUS_odb_investment_2')
    for rank in range(1,11):
        assert w.buy(f'RUS_odb_investment_{rank}')
        assert len(w.country['ideas'])==1 and f'RUS_odb_investment_{rank}' in w.country['ideas']
        assert bool(w.tech)==(rank==10)
    assert o['vars']['funds']==1 and len(w.tech)==2 and not w.buy('RUS_odb_investment_10')
    for group,total,parent in [('expansion',5,'land'),('optimization',10,'production'),('medals',10,'testing')]:
        w=Model();o=w.mios[ORG];o['traits'].add('RUS_odb_'+parent)
        for rank in range(1,total+1):assert w.buy(f'RUS_odb_{group}_{rank}')
        assert o['vars']['RUS_odb_'+group+'_rank']==total
        visible=[k for k,t in TRAITS.items() if k.startswith('RUS_odb_'+group+'_') and (not t.one('visible') or w.scoped(o,lambda:w.cond(t.one('visible').v)))]
        assert visible==[f'RUS_odb_{group}_{total}']
    # Weekly rate is 6%, 1.28 daily funds boundary, no multi-line multiplication, final cap125%.
    for funds,lines,gain in [('8.95',1,False),('8.96',1,True),('8.96',9,True),('8.96',0,False)]:
        w=Model();o=w.mios[ORG];o['traits'].add('RUS_odb_modular');o['vars'].update({'funds':D(funds),'RUS_odb_previous_funds':D(0),'RUS_odb_manufacturers':D(lines)})
        w.fx('RUS_odb_learning_weekly');assert o['vars']['research_bonus']==(D('.06') if gain else D(0))
    w=Model();o=w.mios[ORG];o['traits'].add('RUS_odb_modular');o['vars'].update({'funds':D(0),'RUS_odb_previous_funds':D(0),'RUS_odb_manufacturers':D(1),'modifier@military_industrial_organization_research_bonus':D('.10')})
    for _ in range(30):o['vars']['funds']+=D(10);w.fx('RUS_odb_learning_weekly')
    assert o['vars']['research_bonus']+D('.10')==D('1.25')
    o['traits'].add('RUS_odb_bmz');w.scoped(o,lambda:w.run(MIO.one('on_tech_research_completed').v));assert o['vars']['research_bonus']==D('1.15')
    w.scoped(o,lambda:w.run(MIO.one('on_tech_research_cancelled').v));assert o['vars']['research_bonus']==0
    # Extend the original policy allowlists only; effects, cost defaults and other MIOs stay native.
    policy_path='common/military_industrial_organization/policies/RUS_policies.txt'
    original={n.k:n for n in load(build.KR/policy_path)}
    policies={n.k:n for n in load(R/policy_path)}
    rd=['RUS_mio_policy_RD_Cap','RUS_mio_policy_RD_Growth']
    assert original.keys()==policies.keys()
    for key,p in policies.items():
        b=original[key]
        if key not in rd:assert p.norm()==b.norm();continue
        assert [n.norm() for n in p.v if n.k!='allowed']==[n.norm() for n in b.v if n.k!='allowed']
        assert [n.norm() for n in p.one('allowed').one('OR').v[:-1]]==[n.norm() for n in b.one('allowed').one('OR').v]
        assert p.one('allowed').one('OR').v[-1].v==ORG
        w=Model()
        assert w.scoped(w.mios[ORG],lambda:w.cond(p.one('allowed').v))
        assert w.scoped(w.mios['RUS_vpoz_organisation'],lambda:w.cond(p.one('allowed').v))
        assert not w.scoped(w.mios['RUS_toz_organisation'],lambda:w.cond(p.one('allowed').v))
    for policy,gain,cap in [(None,D('.06'),D('1.25')),(rd[0],D('.06'),D('1.50')),(rd[1],D('.07'),D('1.25'))]:
        w=Model();w.fx('RUS_odb_unlock');o=w.mios[ORG]
        if policy:w.scoped(o,lambda:w.run(policies[policy].one('on_add').v))
        # Attaching before the modular trait and repeated initialization must not erase the policy.
        w.fx('RUS_odb_unlock');o['traits'].add('RUS_odb_modular')
        o['vars'].update({'funds':D(0),'RUS_odb_previous_funds':D(0),'RUS_odb_manufacturers':D(1),'modifier@military_industrial_organization_research_bonus':D('.10')})
        w.fx('RUS_odb_show_learning',ORG)
        assert w.temps['RUS_odb_policy_research_gain']==gain and w.temps['RUS_odb_policy_research_cap']==cap
        o['vars']['funds']+=10;w.fx('RUS_odb_learning_weekly');assert o['vars']['research_bonus']==gain
        for _ in range(30):o['vars']['funds']+=10;w.fx('RUS_odb_learning_weekly')
        assert o['vars']['research_bonus']+D('.10')==cap
        w.fx('RUS_odb_reset_research',ORG)
        assert o['vars']['weekly_research_speed_gain']==gain and o['vars']['max_research_speed']==cap
        if policy:
            w.scoped(o,lambda:w.run(policies[policy].one('on_remove').v))
            assert o['vars']['max_research_speed']==D('1.25') and o['vars']['weekly_research_speed_gain']==D('.06')
            other=rd[1] if policy==rd[0] else rd[0]
            w.scoped(o,lambda:w.run(policies[other].one('on_add').v))
            w.scoped(o,lambda:w.run(policies[other].one('on_remove').v))
            assert o['vars']['max_research_speed']==D('1.25') and o['vars']['weekly_research_speed_gain']==D('.06')
    # Exactly once per30days, only actively assigned, and not an artificial weekly learning gain.
    w=Model();o=w.mios[ORG];o['traits'].add('RUS_odb_obukhov')
    for _ in range(29):w.fx('RUS_odb_daily')
    assert not w.grants
    w.fx('RUS_odb_daily');assert len(w.grants)==1 and o['vars']['RUS_odb_previous_funds']==100
    for obj in w.mios.values():obj['active']=False
    for _ in range(30):w.fx('RUS_odb_daily')
    assert len(w.grants)==1
    # Shared tech files stay absent; exact restored stats, dedicated IDs, no chassis or folder override.
    assert not (R/'common/technologies/artillery.txt').exists()
    tech=load(R/'common/technologies/RUS_odb_modern_cannons_unlock.txt')[0]
    assert len(tech.v)==2 and all(n.one('allow').value('always')=='no' and not n.one('folder') for n in tech.v)
    old=parse(subprocess.check_output(['git','show','bbd773d:common/units/equipment/modules/zzz_RUS_modern_cannons.txt']).decode())[0]
    new=load(R/'common/units/equipment/modules/RUS_odb_modern_cannons.txt')[0]
    for a,b in zip(old.v,new.v):assert a.one('add_stats').norm()==b.one('add_stats').norm() and b.value('category')=='tank_medium_main_armament'
    # No unrelated legacy traits, conditions, focus rewards or missions were changed.
    source='common/military_industrial_organization/organizations/RUS_organization.txt'
    old={n.k:n for n in parse(subprocess.check_output(['git','show','ea65495ad19b87083fc4a7324242dbafc24be97b:'+source]).decode('utf-8-sig'))}
    for n in load(R/source):
        b=old[n.k]
        if n.k in [x.get('source') for x in SPEC['nodes']]:
            assert [x.norm() for x in n.v if x.k!='available']==[x.norm() for x in b.v if x.k!='available']
            assert [x.norm() for x in n.one('available').v[:-1]]==[x.norm() for x in b.one('available').v]
        else:assert n.norm()==b.norm()
    positions={(n['x'],n['y']) for n in SPEC['nodes']};assert len(positions)==17
    assert max(x for x,y in positions)==6 and max(y for x,y in positions)==4
    cells={n['cell']:n['id'] for n in SPEC['nodes']}
    drawn=set()
    for edge in ET.parse(R/'tools/design/ordnance_design_bureau/陆军兵器设计总局.drawio').iter('mxCell'):
        style=edge.get('style','')
        if 'endArrow=classic' in style and 'startArrow=classic' in style:
            drawn.add(frozenset(cells[edge.get(k).rsplit('-',1)[1]] for k in ['source','target']))
    scripted={frozenset((n['id'],n['exclusive'])) for n in SPEC['nodes'] if n.get('exclusive')}
    assert drawn==scripted and len(scripted)==2
    def ancestors(key):
        n=next(n for n in SPEC['nodes'] if n['id']==key)
        return set(n.get('parents',[]))|set().union(*(ancestors(k) for k in n.get('parents',[])))
    for n in SPEC['nodes']:
        if n.get('exclusive'):assert n['exclusive'] not in ancestors(n['id'])
    for rel in build.render(SPEC):
        p=R/rel
        if p.suffix=='.yml':
            assert p.read_bytes().startswith(b'\xef\xbb\xbf')
            keys=re.findall(r'^\s+(\w+):',p.read_text(encoding='utf-8-sig'),re.M);assert len(keys)==len(set(keys))
        else:load(p)
    assert len(TRAITS)==48
    print('PASS: ordnance MIO script model — five idempotent transfers, medal7/count/cost/timer inheritance, all-parent gates, exclusion, finite repeats, investment boundaries, weekly cap/reset, 30day grants, isolated technologies, preserved donor trees and 7x5 bounds. Engine testing is still required.')

if __name__=='__main__':main()
