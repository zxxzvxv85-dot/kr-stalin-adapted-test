"""Execute actual armour scripts with the existing MIO model; no engine UI claim."""
from pathlib import Path
from decimal import Decimal as D
import copy,json,re,subprocess,xml.etree.ElementTree as ET
from hoi4_politics_blocks import load,parse,tokens
import generate_armour_design_bureau as build
import test_ordnance_design_bureau as model

R=build.ROOT;ORG=build.ORG
SPEC=json.loads(build.SPEC_PATH.read_text(encoding='utf-8'))
MIO=load(R/f'common/military_industrial_organization/organizations/{build.STEM}.txt')[0]
FX={n.k:n for n in load(R/f'common/scripted_effects/{build.STEM}_effects.txt')}
TRAITS={n.value('token'):n for n in MIO.children('trait')}
model.FX=FX;model.ORG=ORG;model.SPEC=SPEC;model.TRAITS=TRAITS

class World(model.Model):
    def __init__(self):
        self.country={'vars':{},'flags':set(),'ideas':set(),'traits':set()}
        self.mios={m:{'vars':{'size':D(6),'funds':D(275),'research_bonus':D(0),'modifier@military_industrial_organization_research_bonus':D(0)},'flags':set(),'ideas':set(),'traits':set(),'active':True} for m in [ORG]+[n['source'] for n in SPEC['nodes'] if n.get('source')]}
        self.temps={};self.current=self.country;self.stack=[];self.tech=set();self.cic=D(0);self.grants=[]
    def cond(self,nodes):
        return all((n.v in self.mios if n.k=='has_military_industrial_organization' else super(World,self).cond([n])) for n in nodes)
    def run(self,nodes):
        if any(n.k=='add_cic' for n in nodes):
            for n in nodes:
                if n.k=='add_cic':assert self.current is self.country;self.cic+=self.value(n.v)
                else:super().run([n])
        else:super().run(nodes)
    def available(self,o):
        for n in SPEC['nodes']:
            if n.get('source') and self.mios.get(n['source']) is o:return 'RUS_adb_merged_'+n['id'] not in self.country['flags']
        return True

def main():
    assert len(SPEC['nodes'])==16 and len(TRAITS)==52
    assert len({(n['x'],n['y']) for n in SPEC['nodes']})==16
    assert max(n['x'] for n in SPEC['nodes'])==6 and max(n['y'] for n in SPEC['nodes'])==4
    tag_text='\n'.join(p.read_text(encoding='utf-8-sig') for base in [R.parents[3]/'common/Hearts of Iron IV',R.parent/'1521695605',R] for p in (base/'common/technology_tags').glob('*.txt'))
    for category in tokens(MIO.one('research_categories')):assert re.search(r'\b'+re.escape(category)+r'\b',tag_text),category
    # Actual drawio edges, including the unbound geometric TSTZ -> process arrow.
    cells={n['cell']:n['id'] for n in SPEC['nodes']};edges=set()
    for c in ET.parse(R/'tools/design/armour_design_bureau/陆军装甲设计总局.drawio').iter('mxCell'):
        if not c.get('edge'):continue
        if c.get('source'):edges.add((cells[c.get('source').rsplit('-',1)[-1]],cells[c.get('target').rsplit('-',1)[-1]]))
        else:
            points={p.get('as'):(float(p.get('x')),float(p.get('y'))) for p in c.findall('./mxGeometry/mxPoint')}
            assert points=={'sourcePoint':(859.5,500.0),'targetPoint':(859.5,680.0)}
            edges.add(('tstz','process'))
    assert edges=={(p,n['id']) for n in SPEC['nodes'] for p in n.get('parents',[])}
    w=World();w.fx('RUS_adb_unlock');o=w.mios[ORG]
    o['vars']['weekly_research_speed_gain']=D('.02');w.fx('RUS_adb_unlock');assert o['vars']['weekly_research_speed_gain']==D('.02')
    assert not World().buy('RUS_adb_naz')
    for n in [n for n in SPEC['nodes'] if n.get('source')]:
        w=World();w.fx('RUS_adb_merge_'+n['id'],ORG);o=w.mios[ORG]
        assert o['vars']['size']==12 and o['vars']['funds']==550
        assert w.mios[n['source']]['vars']['funds']==0 and not w.available(w.mios[n['source']])
        once=copy.deepcopy((w.mios,w.country));w.fx('RUS_adb_merge_'+n['id'],ORG);assert once==(w.mios,w.country)
        w=World();del w.mios[n['source']];w.fx('RUS_adb_merge_'+n['id'],ORG);assert w.mios[ORG]['vars']['size']==6
    for n in SPEC['nodes']:
        if len(n.get('parents',[]))<2:continue
        w=World();o=w.mios[ORG];o['traits'].add('RUS_adb_'+n['parents'][0]);assert not w.buy('RUS_adb_'+n['id']+('_1' if n.get('repeat') else ''))
    w=World();w.fx('RUS_adb_unlock');o=w.mios[ORG]
    # Entire approved tree can be bought topologically; all four repeats stop after ten.
    for n in SPEC['nodes']:
        if n['id']=='guidance':o['vars']['funds']=D(1000);assert not w.buy('RUS_adb_guidance_1');o['vars']['funds']=D(10001)
        if n.get('repeat'):
            assert not w.buy('RUS_adb_'+n['id']+'_2')
            for rank in range(1,11):assert w.buy('RUS_adb_'+n['id']+'_'+str(rank))
            assert not w.buy('RUS_adb_'+n['id']+'_10')
            visible=[t for t in TRAITS.values() if t.value('token').startswith('RUS_adb_'+n['id']+'_') and w.scoped(o,lambda:w.cond(t.one('visible').v))]
            assert len(visible)==1 and visible[0].value('token').endswith('_10')
        else:assert w.buy('RUS_adb_'+n['id'])
    assert o['vars']['funds']==1 and len(w.tech)==20 and w.country['ideas']=={'RUS_adb_extreme_design_10'}
    # Previewed CIC is not paid at trait purchase; each completed research pays once.
    assert w.cic==0
    o['vars']['size']=D(23);o['vars']['research_bonus']=D('.4')
    w.scoped(o,lambda:w.run(MIO.one('on_tech_research_completed').v));assert w.cic==23000 and o['vars']['research_bonus']==D('.4')
    o['vars']['size']=D(24);w.scoped(o,lambda:w.run(MIO.one('on_tech_research_completed').v));assert w.cic==47000
    w.scoped(o,lambda:w.run(MIO.one('on_tech_research_cancelled').v));assert w.cic==47000 and o['vars']['research_bonus']==0
    w=World();o=w.mios[ORG];o['traits'].add('RUS_adb_chtz');o['vars']['research_bonus']=D('.3')
    w.scoped(o,lambda:w.run(MIO.one('on_tech_research_completed').v));assert w.cic==0 and o['vars']['research_bonus']==0
    for funds,lines,gain in [('8.95',1,False),('8.96',1,True),('8.96',7,True),('8.96',0,False)]:
        w=World();w.fx('RUS_adb_unlock');o=w.mios[ORG];o['traits'].add('RUS_adb_chtz');o['vars'].update({'funds':D(funds),'RUS_adb_previous_funds':D(0),'RUS_adb_manufacturers':D(lines)})
        w.fx('RUS_adb_learning_weekly');assert o['vars']['research_bonus']==(D('.01') if gain else 0)
    policies={n.k:n for n in load(R/'common/military_industrial_organization/policies/RUS_policies.txt')}
    for policy,gain,cap in [(None,D('.01'),D('.55')),('RUS_mio_policy_RD_Cap',D('.01'),D('.80')),('RUS_mio_policy_RD_Growth',D('.02'),D('.55'))]:
        w=World();w.fx('RUS_adb_unlock');o=w.mios[ORG];o['traits'].add('RUS_adb_chtz');o['vars']['RUS_adb_manufacturers']=D(1)
        if policy:
            assert w.scoped(o,lambda:w.cond(policies[policy].one('allowed').v));w.scoped(o,lambda:w.run(policies[policy].one('on_add').v))
        w.fx('RUS_adb_unlock');w.fx('RUS_adb_show_learning',ORG);assert w.temps['RUS_adb_policy_research_gain']==gain and w.temps['RUS_adb_policy_research_cap']==cap
        for _ in range(90):o['vars']['funds']+=10;w.fx('RUS_adb_learning_weekly')
        assert o['vars']['research_bonus']==cap
    # Expenses and transfers change the baseline; they never buy production learning.
    w=World();w.fx('RUS_adb_unlock');o=w.mios[ORG];o['traits'].add('RUS_adb_chtz');o['vars']['RUS_adb_manufacturers']=D(1)
    w.fx('RUS_adb_merge_amo',ORG);w.fx('RUS_adb_learning_weekly');assert o['vars']['research_bonus']==0
    o['traits'].update({'RUS_adb_exchange','RUS_adb_joint'});o['vars'].update({'funds':D(1010),'RUS_adb_previous_funds':D(1001)})
    assert w.buy('RUS_adb_guidance_1');w.fx('RUS_adb_learning_weekly');assert o['vars']['research_bonus']==D('.01')
    # The other bureau's Obukhov grant is income, not production learning.
    w=World();w.fx('RUS_adb_unlock');o=w.mios[ORG];o['traits'].add('RUS_adb_chtz');o['vars']['RUS_adb_manufacturers']=D(1)
    for m in w.mios.values():m['active']=False
    o['active']=True
    w.mios['RUS_odb_organisation']=copy.deepcopy(o);w.mios['RUS_odb_organisation']['active']=False
    w.mios['RUS_odb_organisation']['traits']={'RUS_odb_obukhov'}
    w.mios['RUS_odb_organisation']['vars']['RUS_odb_funding_days']=D(29)
    odb={n.k:n for n in load(R/'common/scripted_effects/RUS_ordnance_design_bureau_effects.txt')}
    w.run(odb['RUS_odb_daily'].v);assert len(w.grants)==1
    assert o['vars']['funds']==o['vars']['RUS_adb_previous_funds']==375
    w.fx('RUS_adb_learning_weekly');assert o['vars']['research_bonus']==0
    # Original MIOs and all focus nodes/rewards: precisely the seven gates and one call.
    original={n.k:n for n in parse(subprocess.check_output(['git','show','4bbcbda:'+build.DONORS]).decode('utf-8-sig'))}
    donors={n['source']:n['id'] for n in SPEC['nodes'] if n.get('source')}
    for n in load(R/build.DONORS):
        b=original[n.k]
        if n.k not in donors:assert n.norm()==b.norm();continue
        assert [x.norm() for x in n.v if x.k!='available']==[x.norm() for x in b.v if x.k!='available']
        assert [x.norm() for x in n.one('available').v[:-1]]==[x.norm() for x in b.one('available').v]
        assert n.one('available').v[-1].one('NOT').value('has_country_flag')=='RUS_adb_merged_'+donors[n.k]
    old=parse(subprocess.check_output(['git','show','4bbcbda:'+build.FOCUS]).decode('utf-8-sig'))
    for a,b in zip(load(R/build.FOCUS),old):
        if a.value('id')!='RUS_future_foreign_030':assert a.norm()==b.norm();continue
        assert [n.norm() for n in a.v if n.k!='completion_reward']==[n.norm() for n in b.v if n.k!='completion_reward']
        assert [n.norm() for n in a.one('completion_reward').v[:-1]]==[n.norm() for n in b.one('completion_reward').v]
        assert a.one('completion_reward').v[-1].k=='RUS_adb_unlock'
    tech=load(R/f'common/technologies/{build.STEM}_technologies.txt')[0]
    assert len(tech.v)==20
    for t in tech.v:
        assert not t.one('folder') and t.one('allow').value('always')=='no'
        units={n.k:n for n in t.v if n.k!='allow'};assert set(units)==set(SPEC['units'])
        for unit in units.values():
            if 'guidance' in t.k:assert unit.value('combat_width')=='-0.05'
            else:
                assert {n.k for n in unit.v}==set(SPEC['terrains'])
                assert all(n.value('attack')==n.value('defence')==n.value('movement')=='0.01' for n in unit.v)
    assert not any('mechanized' in u or 'armored_car' in u for u in SPEC['units'])
    # Use existing combat battalions only; support companies with zero width stay out.
    files={}
    for base in [R.parents[3]/'common/Hearts of Iron IV',R.parent/'1521695605',R]:
        for p in (base/'common/units').glob('*.txt'):files[p.name]=p
    units={u.k:u for p in files.values() for root in load(p) if root.k=='sub_units' for u in root.v}
    for key in SPEC['units']:
        assert D(units[key].value('combat_width'))>D('.5'),key
        assert 'category_all_armor' in tokens(units[key].one('categories')),key
    for key in ['reactive','guidance','logistics','process']:
        selected=[t for t in TRAITS.values() if t.value('token').startswith('RUS_adb_'+key+'_')]
        assert len(selected)==10
    assert TRAITS['RUS_adb_process_1'].one('equipment_bonus').value('hardness')=='-0.02'
    for rel in build.render(SPEC):
        p=R/rel
        if p.suffix=='.yml':
            assert p.read_bytes().startswith(b'\xef\xbb\xbf');keys=re.findall(r'^ (\w+):',p.read_text(encoding='utf-8-sig'),re.M);assert len(keys)==len(set(keys))
        else:load(p)
    print('PASS: armour actual-script model, seven one-time transfers, drawio AND edges, four finite repeats, 1000 boundary, research payout/reset/cap/policies, 20 isolated technologies, donor/focus AST and 7x5 bounds. Engine UI remains untested.')
if __name__=='__main__':main()
