"""Integrate the pinned user package. Default/--check are read-only; --write updates.

Source ZIP, GWR portrait and original trait are archived with SHA manifests.
No launcher descriptor, history replacement, external mod edit or image generation.
"""
from __future__ import annotations
import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
from zipfile import ZipFile
from hoi4_politics_blocks import parse

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'tools/design/RUS_lenin_revival_20261027'
TREE='RUS_lenin_revival_focus'
TRAIT='RUS_LR_vozhd_of_proletariat'
FILES=[
    'common/decisions/00_RUS_lenin_revival_decisions.txt',
    'common/decisions/categories/00_RUS_lenin_revival_categories.txt',
    'common/ideas/00_RUS_lenin_revival_ideas.txt',
    'common/national_focus/00_RUS_lenin_revival_focus.txt',
    'events/00_RUS_lenin_revival_events.txt',
    *[f'localisation/{lang}/00_RUS_lenin_revival_l_{lang}.yml' for lang in ('english','simp_chinese')]]
# User gameplay override; keep the archived GWR source unchanged. Negative
# cost reductions are benefits, so classification follows modifier meaning.
TRAIT_BENEFITS={
    'trade_laws_cost_factor':-1,'economy_cost_factor':-1,
    'war_stability_factor':1,'industrial_capacity_factory':1,
    'political_power_factor':1,'drift_defence_factor':1}
TRAIT_BENEFIT_MULTIPLIER=Decimal('5')
# Explicit final values appended after scaling the original six benefits.
TRAIT_ADDITIONS={'political_advisor_cost_factor':'-1','communist_drift':'0.25','compliance_gain':'0.25'}

def replace(text,old,new):
    assert text.count(old)==1,(old,text.count(old))
    return text.replace(old,new,1)

def edit_blocks(text,key,transform):
    nodes=parse(text)
    if key=='focus':nodes=nodes[0].children('focus')
    elif key=='country_event':nodes=[n for n in nodes if n.k==key]
    else:raise AssertionError(key)
    for n in reversed(nodes):text=text[:n.a]+transform(n)+text[n.b:]
    parse(text)
    return text

def source_files():
    manifest=json.loads((SOURCE/'source_manifest.json').read_text(encoding='utf-8'))
    archive=SOURCE/'source.zip'
    assert hashlib.sha256(archive.read_bytes()).hexdigest()==manifest['sha256']
    members={r['path']:r for r in manifest['members']}
    result={}
    with ZipFile(archive) as z:
        for name in FILES:
            member='RUS_Lenin_Revival/'+name;data=z.read(member)
            assert hashlib.sha256(data).hexdigest()==members[member]['sha256']
            result[name]=data.decode('utf-8-sig').replace('\r\n','\n')
    return result

def focus_text(text):
    text=replace(text,'id = '+TREE,'id = '+TREE+'\n\tdefault = no')
    def change(n):
        s=n.raw();key=n.value('id')
        if key=='RUS_LR_proclaim_the_return':
            s=replace(s,'set_politics = { ruling_party = communist elections_allowed = no }',
                'set_politics = { ruling_party = communist elections_allowed = no }\n\t\tRUS_LR_appoint_lenin = yes')
        if key=='RUS_LR_revolution_returns':
            s=replace(s,'completion_reward = {','available = { NOT = { any_country = { civilwar_target = ROOT } } }\n\tcompletion_reward = {')
        if key=='RUS_LR_declare_sr_defeat':
            s=replace(s,n.one('available').raw(),'available = { custom_trigger_tooltip = { tooltip = RUS_LR_sr_defeated_tt RUS_LR_sr_defeated = yes } }')
        return s
    return edit_blocks(text,'focus',change)

def event_text(text):
    def change(n):
        s=n.raw();eid=n.value('id')
        if eid=='RUS_lenin_revival.1':
            condition='original_tag = RUS NOT = { has_country_flag = RUS_LR_choice_resolved } NOT = { has_country_flag = RUS_LR_sr_rebel }'
            s=replace(s,'set_country_flag = RUS_LR_declined','set_country_flag = RUS_LR_declined\n\t\tset_country_flag = RUS_LR_choice_resolved')
            s=replace(s,'set_country_flag = RUS_LR_enabled\n\t\tload_focus_tree = { tree = RUS_lenin_revival_focus keep_completed = yes }',
                'hidden_effect = { RUS_LR_enter_route = yes }')
        else:
            condition='RUS_LR_is_active = yes'
            if eid.endswith('.20'):
                condition+=' has_government = communist NOT = { has_country_flag = RUS_LR_civil_war_started } NOT = { any_country = { civilwar_target = ROOT } }'
                s=replace(s,'start_civil_war = {','hidden_effect = { set_country_flag = RUS_LR_civil_war_started }\n\t\tstart_civil_war = {')
                s=replace(s,'ideology = social_democrat','ideology = radical_socialist')
                s=replace(s,'size = 0.35','size = 0.35\n\t\t\tset_country_flag = RUS_LR_sr_rebel\n\t\t\tclr_country_flag = RUS_LR_enabled\n\t\t\tload_focus_tree = { tree = generic_focus keep_completed = no }')
            elif eid.endswith('.21'):
                condition+=' RUS_LR_sr_defeated = yes NOT = { has_country_flag = RUS_LR_sr_defeat_seen }'
                s=replace(s,'add_political_power = 100','hidden_effect = { set_country_flag = RUS_LR_sr_defeat_seen }\n\t\tadd_political_power = 100')
            elif eid.endswith('.22'):
                condition+=' has_completed_focus = RUS_LR_economic_victory NOT = { has_country_flag = RUS_LR_economic_victory_seen }'
                s=replace(s,'add_political_power = 100','hidden_effect = { set_country_flag = RUS_LR_economic_victory_seen }\n\t\tadd_political_power = 100')
            else:raise AssertionError(eid)
        return replace(s,'is_triggered_only = yes','is_triggered_only = yes\n\tfire_only_once = yes\n\ttrigger = { '+condition+' }')
    return edit_blocks(text,'country_event',change)

def trait_text():
    meta=json.loads((SOURCE/'trait_source.json').read_text(encoding='utf-8'))
    raw=(SOURCE/'trait_gwr_source.txt').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==meta['trait_source_sha256']
    character=(SOURCE/'character_gwr_source.txt').read_bytes()
    assert hashlib.sha256(character).hexdigest()==meta['character_source_sha256']
    assert [n.k for n in parse(character.decode('utf-8'))[0].one('country_leader').one('traits').v]==[meta['trait']]
    trait=parse(raw.decode('utf-8'))[0]
    fields=[]
    found=set()
    for n in trait.v:
        if n.k=='random':fields.append(f'\t\t{n.k} = {n.v}')
        elif n.k in TRAIT_BENEFITS:
            value=Decimal(n.v)
            assert value*TRAIT_BENEFITS[n.k]>0,n.k
            scaled=format(value*TRAIT_BENEFIT_MULTIPLIER,'f')
            if '.' in scaled:scaled=scaled.rstrip('0').rstrip('.')
            fields.append(f'\t\t{n.k} = {scaled}');found.add(n.k)
        # All other source effects are the relation-cost, war-support and
        # ideology-acceptance penalties explicitly removed by the user.
    assert found==TRAIT_BENEFITS.keys()
    fields += [f'\t\t{key} = {value}' for key,value in TRAIT_ADDITIONS.items()]
    return 'leader_traits = {\n\t'+TRAIT+' = {\n'+'\n'.join(fields)+'\n\t}\n}\n'

def integration_effects():
    return '''# Generated by tools/import_lenin_revival.py --write
RUS_LR_enter_route = {
	if = {
		limit = { original_tag = RUS NOT = { has_country_flag = RUS_LR_enabled } NOT = { has_country_flag = RUS_LR_sr_rebel } }
		set_country_flag = RUS_LR_choice_made
		set_country_flag = RUS_LR_choice_resolved
		set_country_flag = RUS_LR_enabled
		# End the abandoned opening before the later government-change hook.
		# Otherwise it loads Russia_Focus over the explicitly chosen new tree.
		if = {
			limit = { has_country_flag = RUS_opening_active }
			clr_country_flag = RUS_opening_active
			remove_ideas = { RUS_opening_unfinished_land_reform RUS_opening_disordered_industry RUS_opening_resistance_wave RUS_opening_military_action }
		}
		# Also block a startup event queued before the player selected the egg.
		set_country_flag = RUS_opening_finished
		load_focus_tree = { tree = RUS_lenin_revival_focus keep_completed = yes }
		mark_focus_tree_layout_dirty = yes
	}
}

# Runtime leader creation, as used by KR and the existing GRU integration.
# History-only recruit_character cannot create this newly imported leader.
RUS_LR_appoint_lenin = {
	if = {
		limit = { hidden_trigger = { RUS_LR_is_active = yes has_government = communist NOT = { has_country_leader = { name = RUS_LR_vladimir_lenin ruling_only = yes } } } }
		create_country_leader = {
			name = RUS_LR_vladimir_lenin
			desc = RUS_LR_lenin_returned_desc
			picture = GFX_portrait_RUS_LR_vladimir_lenin
			ideology = leninist_subtype
			traits = { RUS_LR_vozhd_of_proletariat }
		}
		set_party_name = { ideology = communist name = RUS_LR_bolshevik_party long_name = RUS_LR_bolshevik_party_long }
		set_government_flags = yes
	}
}
'''

def render_outputs():
    texts=source_files()
    p='common/national_focus/00_RUS_lenin_revival_focus.txt';texts[p]=focus_text(texts[p])
    p='events/00_RUS_lenin_revival_events.txt';texts[p]=event_text(texts[p])
    p='common/ideas/00_RUS_lenin_revival_ideas.txt'
    # The package used obsolete research-time and vanilla ideology modifiers.
    texts[p]=texts[p].replace('communism_drift =','communist_drift =').replace('research_time_factor = -','research_speed_factor = ')
    p='common/decisions/00_RUS_lenin_revival_decisions.txt'
    texts[p]=texts[p].replace('NOT = { has_country_flag = RUS_LR_choice_made }','NOT = { has_country_flag = RUS_LR_choice_made } NOT = { has_country_flag = RUS_LR_sr_rebel }')
    texts[p]=replace(texts[p],'available = { NOT = { has_country_flag = RUS_LR_choice_made } NOT = { has_country_flag = RUS_LR_sr_rebel } }',
        'available = { hidden_trigger = { NOT = { has_country_flag = RUS_LR_choice_made } NOT = { has_country_flag = RUS_LR_sr_rebel } } }')
    p='common/decisions/categories/00_RUS_lenin_revival_categories.txt'
    texts[p]=replace(texts[p],'original_tag = RUS','original_tag = RUS\n\t\tNOT = { has_country_flag = RUS_LR_choice_resolved }\n\t\tNOT = { has_country_flag = RUS_LR_sr_rebel }')
    texts['common/scripted_effects/RUS_lenin_revival_effects.txt']=integration_effects()
    texts['common/scripted_triggers/RUS_lenin_revival_triggers.txt']='''RUS_LR_is_active = {
	original_tag = RUS
	has_country_flag = RUS_LR_enabled
	NOT = { has_country_flag = RUS_LR_sr_rebel }
}

RUS_LR_sr_defeated = {
	RUS_LR_is_active = yes
	has_country_flag = RUS_LR_civil_war_started
	NOT = { any_country = { civilwar_target = ROOT } }
	NOT = { any_country = { has_country_flag = RUS_LR_sr_rebel exists = yes } }
}
'''
    texts['common/country_leader/RUS_lenin_revival_traits.txt']=trait_text()
    trait_meta=json.loads((SOURCE/'trait_source.json').read_text(encoding='utf-8'))
    additions={
        'simp_chinese':{'RUS_LR_vladimir_lenin':'弗拉基米尔·伊里奇·列宁','RUS_LR_bolshevik_party':'俄共（布）','RUS_LR_bolshevik_party_long':'俄罗斯共产党（布尔什维克）','RUS_LR_sr_defeated_tt':'社会革命党叛军已被击败'},
        'english':{'RUS_LR_vladimir_lenin':'Vladimir Ilyich Lenin','RUS_LR_bolshevik_party':'RKP(b)','RUS_LR_bolshevik_party_long':'Russian Communist Party (Bolsheviks)','RUS_LR_sr_defeated_tt':'The Socialist-Revolutionary rebels have been defeated'}}
    for lang,entries in additions.items():
        p=f'localisation/{lang}/00_RUS_lenin_revival_l_{lang}.yml'
        entries[TRAIT]=trait_meta['localisation'][lang]
        texts[p]+='\n'+''.join(' '+k+':0 '+json.dumps(v,ensure_ascii=False)+'\n' for k,v in entries.items())
        if lang=='simp_chinese':texts[p]=texts[p].replace('是斯大林同志，他也回来了（无变化）','是斯大林同志，他也回来了。')
        else:texts[p]=texts[p].replace('(no change)','(retain the current route)')
    texts['interface/RUS_lenin_revival_portrait.gfx']='''spriteTypes = {
	spriteType = {
		name = "GFX_portrait_RUS_LR_vladimir_lenin"
		texturefile = "gfx/leaders/RUS/RUS_LR_vladimir_lenin.png"
	}
}
'''
    portrait=json.loads((SOURCE/'portrait_source.json').read_text(encoding='utf-8'))
    data=(SOURCE/'lenin_gwr_source.png').read_bytes()
    assert hashlib.sha256(data).hexdigest()==portrait['sha256']
    outputs={Path(p):text.encode('utf-8-sig' if p.endswith('.yml') else 'utf-8') for p,text in texts.items()}
    outputs[Path(portrait['destination'])]=data
    return outputs

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group();group.add_argument('--write',action='store_true');group.add_argument('--check',action='store_true')
    args=parser.parse_args();outputs=render_outputs()
    if args.write:
        for rel,data in outputs.items():
            dest=ROOT/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
        print(f'Wrote {len(outputs)} Lenin revival files; launcher metadata untouched.')
    else:
        stale=[str(p) for p,data in outputs.items() if not (ROOT/p).is_file() or (ROOT/p).read_bytes()!=data]
        if stale:raise SystemExit('Out of date: '+', '.join(stale))
        print(f'PASS: {len(outputs)} Lenin revival outputs match pinned sources (read-only).')

if __name__=='__main__':main()
