"""Execute rename gates and verify that only institution names can change."""
from pathlib import Path
import copy,json,re,subprocess
from hoi4_politics_blocks import load,parse
import generate_stalin_mio_names as build

R=build.ROOT
ROWS=json.loads(build.SPEC.read_text(encoding='utf-8'))
TRIGGER=load(R/'common/scripted_triggers/RUS_stalin_mio_names_triggers.txt')[0]
EFFECT=load(R/'common/scripted_effects/RUS_stalin_mio_names_effects.txt')[0]
EFFECTS={n.k:n for n in load(R/'common/scripted_effects/RUS_stalin_mio_names_effects.txt')}
EVENTS={n.value('id'):n for n in load(R/'events/RUS_stalin_mio_reorganization_events.txt') if n.k=='country_event'}
DONE='RUS_stalin_mio_reorganization_done'
MAPPING={org:build.key(row) for row in ROWS for org in [row['org']]+row.get('related',[])}

class World:
    def __init__(self,tag='RUS',flags=(),leader=False,dlc=True,missing=()):
        self.tag=tag;self.flags=set(flags);self.leader=leader;self.dlc=dlc
        self.mios={org:dict(name='original_'+org,size=22,funds=1357,traits=['a','b'],policies=['p'],tasks=['line1'],flags=['f']) for org in list(MAPPING)+['RUS_odb_organisation','foreign_test'] if org not in missing}
        self.current=None
        self.socialist=True;self.day=0;self.queue=[];self.popups=[];self.fired=set()
    def cond(self,ns):
        def one(n):
            if n.k=='tag':return self.tag==n.v
            if n.k=='has_country_flag':return n.v in self.flags
            if n.k=='has_socialist_government':return self.socialist==(n.v=='yes')
            if n.k=='has_country_leader':assert n.value('character')=='RUS_iosif_stalin';return self.leader
            if n.k=='has_dlc_aat':return self.dlc
            if n.k=='has_military_industrial_organization':return n.v in self.mios
            if n.k=='RUS_stalin_mio_names_active':return self.cond(TRIGGER.v)
            if n.k=='OR':return any(one(x) for x in n.v)
            if n.k=='NOT':return not any(one(x) for x in n.v)
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
            elif n.k=='set_country_flag':self.flags.add(n.v)
            elif n.k=='country_event':self.queue.append((self.day+int(n.value('days','0')),n.value('id')))
            elif n.k=='hidden_effect':self.run(n.v)
            elif n.k in ('name','effect_tooltip'):pass
            elif n.k in EFFECTS:self.run(EFFECTS[n.k].v)
            else:raise AssertionError(('rename effect must not mutate other game state',n.k))
    def advance(self,days=0):
        for _ in range(days+1):
            while due:=[(day,key) for day,key in self.queue if day<=self.day]:
                self.queue=[(day,key) for day,key in self.queue if day>self.day]
                for day,key in due:
                    event=EVENTS[key]
                    if key in self.fired:continue
                    self.fired.add(key)
                    # Deliberately do not simulate trigger filtering on a
                    # forced call: production guards must be actual effects.
                    if event.one('immediate'):self.run(event.one('immediate').v)
                    if event.value('hidden')!='yes':self.popups.append(key)
            if _<days:self.day+=1
    def confirm(self):
        key=self.popups.pop(0);self.run(EVENTS[key].one('option').v);self.advance()

def main():
    assert len(ROWS)==23 and len(MAPPING)==25
    cases=[('RUS',(),False,True,False),('RUS',('RUS_rename_industries',),False,True,False),('RUS',(),True,True,False),('RUS',('RUS_stalin_ml_promoted',),False,True,False),('RUS',('RUS_stalin_communist_path',),False,True,False),('RUS',(DONE,),True,True,True),('RUS',(DONE,'RUS_stalin_ml_promoted'),False,True,True),('RUS',(DONE,'RUS_stalin_communist_path'),False,True,True),('FER',(DONE,'RUS_stalin_communist_path'),True,True,False),('RSA',(DONE,'RUS_stalin_ml_promoted'),True,True,False),('RUS',(DONE,'RUS_stalin_ml_promoted'),True,False,False)]
    for tag,flags,leader,dlc,expected in cases:
        w=World(tag,flags,leader,dlc);before=copy.deepcopy(w.mios);w.run(EFFECT.v)
        assert {org for org in w.mios if w.mios[org]!=before[org]}==(set(MAPPING) if expected else set())
        for org,state in w.mios.items():
            assert {k:v for k,v in state.items() if k!='name'}=={k:v for k,v in before[org].items() if k!='name'}
            if expected and org in MAPPING:assert state['name']==MAPPING[org]
        once=copy.deepcopy(w.mios);w.run(EFFECT.v);assert w.mios==once
    w=World(flags=[DONE,'RUS_stalin_ml_promoted'],missing=['RUS_bmz_organisation','RUS_sokol_production_organisation']);w.run(EFFECT.v)
    assert all(state['name']==MAPPING.get(org,'original_'+org) for org,state in w.mios.items())
    # Later KR renaming must not permanently replace the approved Stalin-era name.
    w.mios['RUS_chtz_organisation']['name']='chtz_improved';w.run(EFFECT.v)
    assert w.mios['RUS_chtz_organisation']['name']==MAPPING['RUS_chtz_organisation']
    # Original event only replaces the immediate MIO rename with scheduling;
    # the legacy single-factory name call moves into the same later report.
    baseline='f3c5524'
    old={n.value('id'):n for n in parse(subprocess.check_output(['git','show',baseline+':'+build.ENTRY]).decode('utf-8-sig')) if n.k=='country_event'}
    for event in [n for n in load(R/build.ENTRY) if n.k=='country_event']:
        original=old[event.value('id')]
        if event.value('id')!='stalin_form_sov.5':assert event.norm()==original.norm();continue
        assert [n.norm() for n in event.v if n.k!='option']==[n.norm() for n in original.v if n.k!='option']
        for a,b in zip(event.children('option'),original.children('option')):
            if a.value('name')!='stalin_form_sov.5.b':assert a.norm()==b.norm();continue
            def without_legacy_tstz(n):
                if n.k=='if' and 'set_mio_name_key = tstz_stalingrad' in n.raw():return None
                if not isinstance(n.v,list):return n.norm()
                return (n.k,n.op,tuple(value for child in n.v if (value:=without_legacy_tstz(child)) is not None))
            assert [n.norm() for n in a.v[:-1]]==[without_legacy_tstz(n) for n in b.v]
            assert a.v[-1].k=='hidden_effect' and a.v[-1].value('RUS_stalin_queue_mio_reorganization')=='yes'
            assert 'set_mio_name_key' not in a.raw() and 'RUS_stalin_apply_mio_names' not in a.raw()
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
    armour=json.loads((R/'tools/design/armour_design_bureau/spec.json').read_text(encoding='utf-8'))
    donors={x['source']:x['id'] for x in armour['nodes'] if x.get('source')}
    for a,b in zip(load(R/org_path),original):
        if a.k not in donors:assert a.norm()==b.norm();continue
        assert [n.norm() for n in a.v if n.k!='available']==[n.norm() for n in b.v if n.k!='available']
        assert [n.norm() for n in a.one('available').v[:-1]]==[n.norm() for n in b.one('available').v]
        assert a.one('available').v[-1].one('NOT').value('has_country_flag')=='RUS_adb_merged_'+donors[a.k]
    for rel in build.render():
        p=R/rel
        if p.suffix=='.yml':
            assert p.read_bytes().startswith(b'\xef\xbb\xbf')
            keys=re.findall(r'^ (\w+):',p.read_text(encoding='utf-8-sig'),re.M);assert len(keys)==len(set(keys))
        else:load(p)
    # Scheduling is anchored to the real accession option, never a daily save
    # migration. Opening/reading the report must not apply the approved names.
    for dlc in (False,True):
        w=World(flags=['RUS_stalin_ml_promoted'],leader=True,dlc=dlc)
        original=copy.deepcopy(w.mios)
        w.run(EFFECTS['RUS_stalin_queue_mio_reorganization'].v)
        assert w.queue==[(15,'RUS_stalin_mio_reorganization.0')]
        w.run(EFFECTS['RUS_stalin_queue_mio_reorganization'].v);assert len(w.queue)==1
        w.run(EFFECTS['RUS_stalin_complete_mio_reorganization'].v);assert DONE not in w.flags
        w.advance(14);assert not w.popups and w.mios==original
        w.advance(1);assert w.popups==['RUS_stalin_mio_reorganization.1'] and w.mios==original
        assert 'RUS_stalin_mio_reorganization_shown' in w.flags
        w.confirm();assert not w.popups and DONE in w.flags
        for org,state in w.mios.items():
            assert {k:v for k,v in state.items() if k!='name'}=={k:v for k,v in original[org].items() if k!='name'}
            assert state['name']==(MAPPING[org] if dlc and org in MAPPING else original[org]['name'])
        once=copy.deepcopy(w.mios);w.run(EVENTS['RUS_stalin_mio_reorganization.1'].one('option').v)
        w.run(EFFECTS['RUS_stalin_queue_mio_reorganization'].v);assert w.mios==once and not w.queue
        w.advance(60);assert not w.popups
    for tag,flags in [('FER',['RUS_stalin_ml_promoted']),('RUS',[]),('RUS',[DONE,'RUS_stalin_ml_promoted'])]:
        w=World(tag=tag,flags=flags,leader=True);w.run(EFFECTS['RUS_stalin_queue_mio_reorganization'].v);assert not w.queue
    w=World(flags=['RUS_stalin_ml_promoted'],leader=True);w.run(EFFECTS['RUS_stalin_queue_mio_reorganization'].v)
    w.socialist=False;w.advance(15);assert not w.popups and DONE not in w.flags
    # Every possible instance remains covered, but each company is displayed
    # once. The first available Sokol variant supplies its native preview.
    preview=EVENTS['RUS_stalin_mio_reorganization.1'].one('option').one('effect_tooltip')
    # The scoped checks are nested under the DLC condition.
    preview_mios={scope.k[4:]:scope.value('set_mio_name_key') for outer in preview.v for inner in outer.v if inner.k in ('if','else_if') for scope in inner.v if scope.k.startswith('mio:')}
    assert preview_mios==MAPPING
    def visible_previews(nodes,w):
        result=[];selected=False
        for n in nodes:
            if n.k in ('if','else_if'):
                if n.k=='if':selected=False
                if not selected and w.cond(n.one('limit').v):
                    selected=True
                    result+=visible_previews([x for x in n.v if x.k!='limit'],w)
            elif n.k.startswith('mio:'):
                result.append((n.k[4:],n.value('set_mio_name_key')))
            else:raise AssertionError(n.k)
        return result
    sokol=ROWS[0];assert sokol['id']=='sokol'
    variants=[sokol['org']]+sokol['related']
    for missing in [[],variants[:1],variants[:2],variants]:
        for dlc in (False,True):
            w=World(dlc=dlc,missing=missing)
            visible=visible_previews(preview.v,w)
            expected=[(next(org for org in [r['org']]+r.get('related',[]) if org in w.mios),build.key(r)) for r in ROWS if any(org in w.mios for org in [r['org']]+r.get('related',[]))] if dlc else []
            assert visible==expected
            assert len({label for org,label in visible})==len(visible)
    reorganization=json.loads(build.REORGANIZATION.read_text(encoding='utf-8'))
    assert len(reorganization['introductions'])==22
    assert sum(len(item['organizations']) for item in reorganization['introductions'])==24
    intro_text=(R/'localisation/replace/zz_RUS_stalin_mio_introductions_l_simp_chinese.yml').read_text(encoding='utf-8-sig')
    intro_values={m[1]:json.loads(m[2]) for m in re.finditer(r'^ (\w+):0 (.+)$',intro_text,re.M)}
    assert not (R/'common/scripted_localisation/RUS_stalin_mio_introductions.txt').exists()
    for item in reorganization['introductions']:
        key=item['localisation_key'];body_key='RUS_stalin_mio_intro_'+item['id']
        assert intro_values[key]==item['original_format'].replace('$'+item['old_body_key']+'$','$'+body_key+'$')
        assert intro_values['RUS_stalin_mio_intro_'+item['id']]==item['introduction']
        assert item['old_body_key'] not in intro_values
    assert '[RUSStalinMioIntro_' not in intro_text
    from extract_rus_mio_introductions import extract
    extracted={r['id']:r for r in extract()}
    for item in reorganization['introductions']:
        for org in item['organizations']:
            assert extracted[org]['introduction']==item['introduction'],org
    assert '（当前没有介绍正文。）' not in intro_text
    report=reorganization['event'];assert set(EVENTS)=={'RUS_stalin_mio_reorganization.0','RUS_stalin_mio_reorganization.1'}
    for lang in ('simp_chinese','english','russian'):
        text=(R/f'localisation/{lang}/RUS_stalin_mio_reorganization_l_{lang}.yml').read_text(encoding='utf-8-sig')
        labels={k:json.loads(v) for k,v in re.findall(r'^ ([\w.]+):0 (.+)$',text,re.M)}
        assert len(labels)==3
        assert labels['RUS_stalin_mio_reorganization.1.d']=='\n'.join(report['paragraphs'])
        assert labels['RUS_stalin_mio_reorganization.1.t']==report['title']
        assert labels['RUS_stalin_mio_reorganization.1.a']==report['option']
        assert '继续阅读' not in text and 'page_' not in text
    from hoi4_bitmap_fonts import measure
    assert measure('hoi4_typewriter22',report['title'])<=551
    assert measure(report['layout']['font'],report['option'])<=512
    # In-game evidence: trait titles leave scripted loc raw, whereas effect bodies expand it.
    # Both bureaus unlock after Stalin; keep all twelve titles literal, same approved source.
    companies={r['id']:r['name'] for r in ROWS}
    for prefix,stem in [('odb','ordnance'),('adb','armour')]:
        text=(R/f'localisation/simp_chinese/RUS_{stem}_design_bureau_l_simp_chinese.yml').read_text(encoding='utf-8-sig')
        labels={m[1]:json.loads(m[2]) for m in re.finditer(r'^ (\w+):0 (.+)$',text,re.M)}
        spec=json.loads((R/f'tools/design/{stem}_design_bureau/spec.json').read_text(encoding='utf-8'))
        for n in [n for n in spec['nodes'] if n.get('source')]:
            assert labels[f'RUS_{prefix}_'+n['id']]=='整合'+companies[n['id']]
            assert '[RUSStalinMioCompany_'+n['id']+']' in labels[f'RUS_{prefix}_'+n['id']+'_unavailable_tt']
        assert '[RUSStalinMioMerge_' not in text
    print('PASS: 15-day accession schedule; single full-text report; confirmation-only rename/22 introductions for 24 MIOs; 23 names + two Sokol variants, preserved institutions/progress/traits, native previews, country/DLC/duplicate gates and BOM/keys. Runtime UI remains to be checked.')

if __name__=='__main__':main()
