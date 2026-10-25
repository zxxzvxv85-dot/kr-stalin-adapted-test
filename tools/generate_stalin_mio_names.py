"""Event-gated MIO names and native literal introductions; preserve institutions/progress."""
from pathlib import Path
import argparse,json
from hoi4_politics_blocks import load,parse

ROOT=Path(__file__).resolve().parents[1]
SPEC=ROOT/'tools/design/RUS_stalin_mio_names.json'
TRAITS=ROOT/'tools/design/RUS_stalin_mio_trait_names.json'
REORGANIZATION=ROOT/'tools/design/RUS_stalin_mio_reorganization_20261025.json'
STEM='RUS_stalin_mio_names'
ENTRY='events/stalin_form_sov.txt'

def key(row):return 'RUS_stalin_mio_company_'+row['id']

def render():
    rows=json.loads(SPEC.read_text(encoding='utf-8'))
    reorganization=json.loads(REORGANIZATION.read_text(encoding='utf-8'))
    orgs={n.k:n for n in load(ROOT/'common/military_industrial_organization/organizations/RUS_organization.txt')}
    changes=[];preview_changes=[]
    for row in rows:
        for index,org in enumerate([row['org']]+row.get('related',[])):
            assert org in orgs
            change=f'\t\tif = {{\n\t\t\tlimit = {{ has_military_industrial_organization = {org} }}\n\t\t\tmio:{org} = {{ set_mio_name_key = {key(row)} }}\n\t\t}}\n'
            changes.append(change)
            # Show one native rename for a shared company; retain every real
            # instance mutation. Fall back when the main template is absent.
            preview_changes.append(change if index==0 else change.replace('if = {','else_if = {',1))
    effects='''RUS_stalin_apply_mio_names = {
 if = {
  limit = { has_dlc_aat = yes RUS_stalin_mio_names_active = yes }
'''+''.join(changes)+''' }
}
'''
    triggers='''RUS_stalin_mio_names_active = {
 tag = RUS
 has_country_flag = RUS_stalin_mio_reorganization_done
 OR = {
  has_country_flag = RUS_stalin_ml_promoted
  has_country_flag = RUS_stalin_communist_path
  has_country_leader = { character = RUS_iosif_stalin }
 }
}
'''
    # Normal daily maintenance also catches later vanilla industry/trait renames.
    on='''on_actions = {
 on_daily_RUS = { effect = { RUS_stalin_apply_mio_names = yes } }
}
'''
    cn={key(row):row['name'] for row in rows}
    fallback={key(row):'$'+orgs[row['org']].value('name')+'$' for row in rows}
    loc=[]
    for row in rows:
        if row['id'] not in ['toz','vpoz','bmz','obukhov','imz','okmo','uztm','chtz','putilovets','amo','tstz','naz']:continue
        old=orgs[row['org']].value('name')
        for prefix,new_key,old_key in [('Company',key(row),old)]:
            loc.append(f'''defined_text = {{
 name = RUSStalinMio{prefix}_{row['id']}
 text = {{ trigger = {{ FROM = {{ RUS_stalin_mio_names_active = yes }} }} localization_key = {new_key} }}
 text = {{ localization_key = {old_key} }}
}}
''')
    companies={row['id']:row for row in rows}
    named_traits={t.value('name') for org in orgs.values() for t in org.children('trait')}
    # Native trait lookup prefers TAG_name. Never override a shared KR title globally.
    for trait in json.loads(TRAITS.read_text(encoding='utf-8')):
        old='KR_MIO_Trait_'+trait['id']
        assert old in named_traits,old
        title='RUS_stalin_mio_trait_'+trait['id']
        prefixed='RUS_'+old
        helper='RUSStalinMioTrait_'+trait['id']
        cn[prefixed]='['+helper+']'
        cn[title]=trait['format'].format(company=companies[trait['company']]['name'])
        fallback[prefixed]='$'+old+'$'
        fallback[title]='$'+old+'$'
        loc.append(f'''defined_text = {{
 name = {helper}
 text = {{ trigger = {{ FROM = {{ RUS_stalin_mio_names_active = yes }} }} localization_key = {title} }}
 text = {{ localization_key = {old} }}
}}
''')
    paths={
        f'common/scripted_effects/{STEM}_effects.txt':effects,
        f'common/scripted_triggers/{STEM}_triggers.txt':triggers,
        f'common/on_actions/{STEM}_on_actions.txt':on,
        f'common/scripted_localisation/{STEM}_localisation.txt':''.join(loc),
    }
    effects_addition='''
RUS_stalin_queue_mio_reorganization = {
 if = {
  limit = {
   tag = RUS
   has_country_flag = RUS_stalin_ml_promoted
   NOT = { has_country_flag = RUS_stalin_mio_reorganization_scheduled }
   NOT = { has_country_flag = RUS_stalin_mio_reorganization_done }
  }
  set_country_flag = RUS_stalin_mio_reorganization_scheduled
  country_event = { id = RUS_stalin_mio_reorganization.0 days = 15 }
 }
}

RUS_stalin_complete_mio_reorganization = {
 if = {
  limit = {
   tag = RUS
   has_country_flag = RUS_stalin_ml_promoted
   has_country_flag = RUS_stalin_mio_reorganization_scheduled
   has_country_flag = RUS_stalin_mio_reorganization_shown
   has_socialist_government = yes
   NOT = { has_country_flag = RUS_stalin_mio_reorganization_done }
  }
  set_country_flag = RUS_stalin_mio_reorganization_done
  RUS_stalin_apply_mio_names = yes
 }
}
'''
    paths[f'common/scripted_effects/{STEM}_effects.txt']+=effects_addition
    report=reorganization['event'];event_loc={};events=['add_namespace = '+report['namespace']+'\n']
    assert report['delay_days']==15
    eligible='tag = RUS has_country_flag = RUS_stalin_ml_promoted has_country_flag = RUS_stalin_mio_reorganization_scheduled has_socialist_government = yes NOT = { has_country_flag = RUS_stalin_mio_reorganization_done }'
    # Recheck delayed delivery in executable effects rather than relying on
    # the trigger block of an explicitly scheduled visible event.
    events.append(f'''country_event = {{
 id = {report['namespace']}.0
 hidden = yes
 is_triggered_only = yes
 fire_only_once = yes
 immediate = {{
  if = {{ limit = {{ {eligible} }} country_event = {{ id = {report['namespace']}.1 }} }}
 }}
}}
''')
    event_id=report['namespace']+'.1'
    event_loc[event_id+'.t']=report['title']
    event_loc[event_id+'.d']='\n'.join(report['paragraphs'])
    option_name=event_id+'.a';event_loc[option_name]=report['option']
    # Preview only; the guarded mutation runs once after confirmation.
    preview='if = { limit = { has_dlc_aat = yes }\n'+''.join(preview_changes)+'}'
    reward='effect_tooltip = { '+preview+' }\n\t\thidden_effect = { RUS_stalin_complete_mio_reorganization = yes }'
    events.append(f'''country_event = {{
 id = {event_id}
 title = {event_id}.t
 desc = {event_id}.d
 picture = {report['picture']}
 is_triggered_only = yes
 fire_only_once = yes
 trigger = {{ {eligible} }}
 immediate = {{ if = {{ limit = {{ {eligible} }} set_country_flag = RUS_stalin_mio_reorganization_shown }} }}
 option = {{
  name = {option_name}
  {reward}
 }}
}}
''')
    paths['events/RUS_stalin_mio_reorganization_events.txt']='\n'.join(events)
    for lang in ('simp_chinese','english','russian'):
        paths[f'localisation/{lang}/RUS_stalin_mio_reorganization_l_{lang}.yml']='\ufeffl_'+lang+':\n'+''.join(' '+k+':0 '+json.dumps(v,ensure_ascii=False)+'\n' for k,v in event_loc.items())
    intro_loc={}
    for item in reorganization['introductions']:
        body_key='RUS_stalin_mio_intro_'+item['id']
        original='$'+item['old_body_key']+'$'
        assert item['original_format'].count(original)==1
        # Initial-trait descriptions do not expand bracket scripted loc in
        # game. Use KR's native $body_key$ prose references instead.
        intro_loc[item['localisation_key']]=item['original_format'].replace(original,'$'+body_key+'$')
        intro_loc[body_key]=item['introduction']
    paths['localisation/replace/zz_RUS_stalin_mio_introductions_l_simp_chinese.yml']='\ufeffl_simp_chinese:\n'+''.join(' '+k+':0 '+json.dumps(v,ensure_ascii=False)+'\n' for k,v in intro_loc.items())
    for lang,entries in [('simp_chinese',cn),('english',fallback),('russian',fallback)]:
        paths[f'localisation/{lang}/{STEM}_l_{lang}.yml']='\ufeffl_'+lang+':\n'+''.join(' '+k+':0 '+json.dumps(v,ensure_ascii=False)+'\n' for k,v in entries.items())
    text=(ROOT/ENTRY).read_text(encoding='utf-8-sig')
    event=next(n for n in parse(text) if n.value('id')=='stalin_form_sov.5')
    option=next(n for n in event.children('option') if n.value('name')=='stalin_form_sov.5.b')
    removals=[]
    for hidden in option.children('hidden_effect'):
        if hidden.value('RUS_stalin_apply_mio_names')=='yes':
            assert len(hidden.v)==1
            removals.append((hidden.a,hidden.b))
        for child in hidden.v:
            if child.k=='if' and 'set_mio_name_key = tstz_stalingrad' in child.raw():
                assert len(child.v)==2 and child.one('limit').value('has_dlc_aat')=='yes'
                removals.append((child.a,child.b))
    for start,end in sorted(removals,reverse=True):
        line_start=text.rfind('\n',0,start)+1;line_end=text.find('\n',end)
        assert not text[line_start:start].strip() and not text[end:line_end].strip()
        text=text[:line_start]+text[line_end+1:]
    event=next(n for n in parse(text) if n.value('id')=='stalin_form_sov.5')
    option=next(n for n in event.children('option') if n.value('name')=='stalin_form_sov.5.b')
    if 'RUS_stalin_queue_mio_reorganization' not in option.raw():
        text=text[:option.ib].rstrip()+'\n\t\thidden_effect = { RUS_stalin_queue_mio_reorganization = yes }\n\t'+text[option.ib:]
    paths[ENTRY]=text
    return paths

def main():
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');p.add_argument('--check',action='store_true');a=p.parse_args();bad=[]
    retired=ROOT/'common/scripted_localisation/RUS_stalin_mio_introductions.txt'
    if retired.exists():
        if a.write:
            assert all(n.k=='defined_text' and n.value('name').startswith('RUSStalinMioIntro_') for n in load(retired))
            retired.unlink()
        else:bad.append('retired introduction helpers still present')
    for rel,text in render().items():
        path=ROOT/rel
        if a.write:path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf-8',newline='\n')
        elif not path.exists() or path.read_text(encoding='utf-8')!=text:bad.append(rel)
    if bad:raise SystemExit('Stale MIO name outputs: '+', '.join(bad))
    print('PASS: 23 MIO names, two Sokol variants and 15 trait titles '+('written' if a.write else 'match (read-only)'))
if __name__=='__main__':main()
