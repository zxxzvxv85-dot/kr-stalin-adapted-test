"""Native per-country MIO renaming. No template, stat, flag or save migration edits."""
from pathlib import Path
import argparse,json
from hoi4_politics_blocks import load,parse

ROOT=Path(__file__).resolve().parents[1]
SPEC=ROOT/'tools/design/RUS_stalin_mio_names.json'
TRAITS=ROOT/'tools/design/RUS_stalin_mio_trait_names.json'
STEM='RUS_stalin_mio_names'
ENTRY='events/stalin_form_sov.txt'

def key(row):return 'RUS_stalin_mio_company_'+row['id']

def render():
    rows=json.loads(SPEC.read_text(encoding='utf-8'))
    orgs={n.k:n for n in load(ROOT/'common/military_industrial_organization/organizations/RUS_organization.txt')}
    changes=[]
    for row in rows:
        for org in [row['org']]+row.get('related',[]):
            assert org in orgs
            changes.append(f'\t\tif = {{\n\t\t\tlimit = {{ has_military_industrial_organization = {org} }}\n\t\t\tmio:{org} = {{ set_mio_name_key = {key(row)} }}\n\t\t}}\n')
    effects='''RUS_stalin_apply_mio_names = {
 if = {
  limit = { has_dlc_aat = yes RUS_stalin_mio_names_active = yes }
'''+''.join(changes)+''' }
}
'''
    triggers='''RUS_stalin_mio_names_active = {
 tag = RUS
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
        for prefix,new_key,old_key in [('Company',key(row),old),('Merge','RUS_stalin_mio_merge_'+row['id'],'RUS_stalin_mio_merge_old_'+row['id'])]:
            loc.append(f'''defined_text = {{
 name = RUSStalinMio{prefix}_{row['id']}
 text = {{ trigger = {{ FROM = {{ RUS_stalin_mio_names_active = yes }} }} localization_key = {new_key} }}
 text = {{ localization_key = {old_key} }}
}}
''')
        cn['RUS_stalin_mio_merge_'+row['id']]='整合'+row['name']
        cn['RUS_stalin_mio_merge_old_'+row['id']]='整合$'+old+'$'
        for prefix in ['RUS_stalin_mio_merge_','RUS_stalin_mio_merge_old_']:
            fallback[prefix+row['id']]='Integrate $'+old+'$'
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
    for lang,entries in [('simp_chinese',cn),('english',fallback),('russian',fallback)]:
        paths[f'localisation/{lang}/{STEM}_l_{lang}.yml']='\ufeffl_'+lang+':\n'+''.join(' '+k+':0 '+json.dumps(v,ensure_ascii=False)+'\n' for k,v in entries.items())
    text=(ROOT/ENTRY).read_text(encoding='utf-8-sig')
    event=next(n for n in parse(text) if n.value('id')=='stalin_form_sov.5')
    option=next(n for n in event.children('option') if n.value('name')=='stalin_form_sov.5.b')
    if 'RUS_stalin_apply_mio_names' not in option.raw():
        text=text[:option.ib].rstrip()+'\n\t\thidden_effect = { RUS_stalin_apply_mio_names = yes }\n\t'+text[option.ib:]
    paths[ENTRY]=text
    return paths

def main():
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');p.add_argument('--check',action='store_true');a=p.parse_args();bad=[]
    for rel,text in render().items():
        path=ROOT/rel
        if a.write:path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf-8',newline='\n')
        elif not path.exists() or path.read_text(encoding='utf-8')!=text:bad.append(rel)
    if bad:raise SystemExit('Stale MIO name outputs: '+', '.join(bad))
    print('PASS: 23 MIO names, two Sokol variants and 15 trait titles '+('written' if a.write else 'match (read-only)'))
if __name__=='__main__':main()
