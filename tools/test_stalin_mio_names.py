"""Execute rename gates and verify that only institution names can change."""
from pathlib import Path
import copy,json,re,subprocess
from hoi4_politics_blocks import load,parse
import generate_stalin_mio_names as build

R=build.ROOT
ROWS=json.loads(build.SPEC.read_text(encoding='utf-8'))
TRIGGER=load(R/'common/scripted_triggers/RUS_stalin_mio_names_triggers.txt')[0]
EFFECT=load(R/'common/scripted_effects/RUS_stalin_mio_names_effects.txt')[0]
MAPPING={org:build.key(row) for row in ROWS for org in [row['org']]+row.get('related',[])}

class World:
    def __init__(self,tag='RUS',flags=(),leader=False,dlc=True,missing=()):
        self.tag=tag;self.flags=set(flags);self.leader=leader;self.dlc=dlc
        self.mios={org:dict(name='original_'+org,size=22,funds=1357,traits=['a','b'],policies=['p'],tasks=['line1'],flags=['f']) for org in list(MAPPING)+['RUS_odb_organisation','foreign_test'] if org not in missing}
        self.current=None
    def cond(self,ns):
        def one(n):
            if n.k=='tag':return self.tag==n.v
            if n.k=='has_country_flag':return n.v in self.flags
            if n.k=='has_country_leader':assert n.value('character')=='RUS_iosif_stalin';return self.leader
            if n.k=='has_dlc_aat':return self.dlc
            if n.k=='has_military_industrial_organization':return n.v in self.mios
            if n.k=='RUS_stalin_mio_names_active':return self.cond(TRIGGER.v)
            if n.k=='OR':return any(one(x) for x in n.v)
            if n.k=='FROM':return self.cond(n.v)
            raise AssertionError(n.k)
        return all(one(n) for n in ns)
    def run(self,ns):
        for n in ns:
            if n.k=='if':
                if self.cond(n.one('limit').v):self.run([x for x in n.v if x.k!='limit'])
            elif n.k.startswith('mio:'):
                assert self.current is None;self.current=n.k[4:];self.run(n.v);self.current=None
            elif n.k=='set_mio_name_key':assert self.current;self.mios[self.current]['name']=n.v
            else:raise AssertionError(('rename effect must not mutate other game state',n.k))

def main():
    assert len(ROWS)==23 and len(MAPPING)==25
    cases=[('RUS',(),False,True,False),('RUS',('RUS_rename_industries',),False,True,False),('RUS',(),True,True,True),('RUS',('RUS_stalin_ml_promoted',),False,True,True),('RUS',('RUS_stalin_communist_path',),False,True,True),('FER',('RUS_stalin_communist_path',),True,True,False),('RSA',('RUS_stalin_ml_promoted',),True,True,False),('RUS',('RUS_stalin_ml_promoted',),True,False,False)]
    for tag,flags,leader,dlc,expected in cases:
        w=World(tag,flags,leader,dlc);before=copy.deepcopy(w.mios);w.run(EFFECT.v)
        assert {org for org in w.mios if w.mios[org]!=before[org]}==(set(MAPPING) if expected else set())
        for org,state in w.mios.items():
            assert {k:v for k,v in state.items() if k!='name'}=={k:v for k,v in before[org].items() if k!='name'}
            if expected and org in MAPPING:assert state['name']==MAPPING[org]
        once=copy.deepcopy(w.mios);w.run(EFFECT.v);assert w.mios==once
    w=World(flags=['RUS_stalin_ml_promoted'],missing=['RUS_bmz_organisation','RUS_sokol_production_organisation']);w.run(EFFECT.v)
    assert all(state['name']==MAPPING.get(org,'original_'+org) for org,state in w.mios.items())
    # Later KR renaming must not permanently replace the approved Stalin-era name.
    w.mios['RUS_chtz_organisation']['name']='chtz_improved';w.run(EFFECT.v)
    assert w.mios['RUS_chtz_organisation']['name']==MAPPING['RUS_chtz_organisation']
    # Original event is unchanged except one hidden native rename dispatch in5.b.
    baseline='f3c5524'
    old={n.value('id'):n for n in parse(subprocess.check_output(['git','show',baseline+':'+build.ENTRY]).decode('utf-8-sig')) if n.k=='country_event'}
    for event in [n for n in load(R/build.ENTRY) if n.k=='country_event']:
        original=old[event.value('id')]
        if event.value('id')!='stalin_form_sov.5':assert event.norm()==original.norm();continue
        assert [n.norm() for n in event.v if n.k!='option']==[n.norm() for n in original.v if n.k!='option']
        for a,b in zip(event.children('option'),original.children('option')):
            if a.value('name')!='stalin_form_sov.5.b':assert a.norm()==b.norm();continue
            assert [n.norm() for n in a.v[:-1]]==[n.norm() for n in b.v]
            assert a.v[-1].k=='hidden_effect' and a.v[-1].value('RUS_stalin_apply_mio_names')=='yes'
    cn=(R/'localisation/simp_chinese/RUS_stalin_mio_names_l_simp_chinese.yml').read_text(encoding='utf-8-sig')
    values={m[1]:json.loads(m[2]) for m in re.finditer(r'^ (\w+):0 (.+)$',cn,re.M)}
    for row in ROWS:assert values[build.key(row)]==row['name']
    # Execute the actual conditional labels in MIO scope (FROM is the owner).
    scripted={n.value('name'):n for n in load(R/'common/scripted_localisation/RUS_stalin_mio_names_localisation.txt')}
    traits=json.loads(build.TRAITS.read_text(encoding='utf-8'))
    assert len(traits)==15
    for tag,flags,leader,dlc,expected in cases:
        w=World(tag,flags,leader,dlc)
        # Localised titles do not require DLC; this condition describes country history.
        active=w.cond(TRIGGER.v)
        for trait in traits:
            old='KR_MIO_Trait_'+trait['id']
            helper='RUSStalinMioTrait_'+trait['id']
            text=next(t for t in scripted[helper].children('text') if not t.one('trigger') or w.cond(t.one('trigger').v))
            assert text.value('localization_key')==('RUS_stalin_mio_trait_'+trait['id'] if active else old)
            assert values['RUS_'+old]=='['+helper+']'
            assert old not in values # shared cross-country title is never replaced
            company=next(r for r in ROWS if r['id']==trait['company'])
            assert values['RUS_stalin_mio_trait_'+trait['id']]==trait['format'].format(company=company['name'])
    # Title changes must not alter trait definitions or modifiers in any original MIO.
    org_path='common/military_industrial_organization/organizations/RUS_organization.txt'
    original=parse(subprocess.check_output(['git','show',baseline+':'+org_path]).decode('utf-8-sig'))
    assert [n.norm() for n in load(R/org_path)]==[n.norm() for n in original]
    for rel in build.render():
        p=R/rel
        if p.suffix=='.yml':
            assert p.read_bytes().startswith(b'\xef\xbb\xbf')
            keys=re.findall(r'^ (\w+):',p.read_text(encoding='utf-8-sig'),re.M);assert len(keys)==len(set(keys))
        else:load(p)
    # Five merge labels and unavailable tooltips use the same conditional company names.
    odb=(R/'localisation/simp_chinese/RUS_ordnance_design_bureau_l_simp_chinese.yml').read_text(encoding='utf-8-sig')
    for key in ['toz','vpoz','bmz','obukhov','imz']:
        assert '[RUSStalinMioMerge_'+key+']' in odb and '[RUSStalinMioCompany_'+key+']' in odb
    print('PASS: 23 exact names + two Sokol variants; before/after/other-country/no-DLC gates, missing institutions, idempotence, preserved stats/tasks, event AST, five merge labels, 15 native trait titles, original MIO AST and BOM/keys. Runtime UI remains to be checked.')

if __name__=='__main__':main()
