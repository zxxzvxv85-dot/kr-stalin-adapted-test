"""Drawio-approved ordnance MIO. Default/check is read-only; --write renders scripts.

Source artwork and original drawio are archived beside the JSON specification.
Does not rewrite shared technology trees or any legacy focus-tree conditions.
"""
from pathlib import Path
from decimal import Decimal
import argparse, json, sys

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT/'tools/design/ordnance_design_bureau/spec.json'
ORG = 'RUS_odb_organisation'
STEM = 'RUS_ordnance_design_bureau'

def block(key, body):
    return key+' = {\n'+''.join((' '+s if s.strip() else '')+'\n' for s in body.strip().splitlines())+'}\n'

def render(spec):
    loc = dict(spec['localisation'])
    effects = []
    traits = []
    for node in spec['nodes']:
        key = 'RUS_odb_'+node['id']
        count = node.get('repeat', 1)
        for rank in range(1, count+1):
            token = key if count == 1 else f'{key}_{rank}'
            loc[token] = node['name']
            b = f'token = {token}\nname = {token}\nicon = {node["icon"]}\nposition = {{ x = {node["x"]} y = {node["y"]} }}\n'
            if node.get('parents'):
                b += 'all_parents = { '+' '.join('RUS_odb_'+x for x in node['parents'])+' }\n'
            if node.get('exclusive'):
                b += 'mutually_exclusive = { RUS_odb_'+node['exclusive']+' }\n'
            if node.get('limit'):
                b += 'limit_to_equipment_type = { '+' '.join(node['limit'])+' }\n'
            for field in ['equipment_bonus','production_bonus','organization_modifier']:
                if node.get(field):
                    b += block(field, '\n'.join(f'{k} = {v}' for k,v in node[field].items()))
            visible, available = '', ''
            if count > 1:
                # One visible slot, exactly like KR TSTZ's finite repeat traits.
                visible += f'check_variable = {{ RUS_odb_{node["id"]}_rank = {rank-1} }}\n' if rank < count else f'NOT = {{ check_variable = {{ RUS_odb_{node["id"]}_rank < {rank-1} }} }}\n'
                available += f'check_variable = {{ RUS_odb_{node["id"]}_rank = {rank-1} }}\n'
            if node.get('source'):
                available += f'FROM = {{ mio:{node["source"]} = {{ is_mio_available = yes }} }}\n'
            if node['id']=='investment':
                available += 'check_variable = { funds > 1000 tooltip = MIO_more_than_X_funds }\n'
            if visible: b += block('visible',visible)
            if available: b += block('available',available)
            complete = node.get('on_complete','')
            if node.get('source'):
                complete += f'RUS_odb_merge_{node["id"]} = yes\n'
            if count > 1:
                # Also guards scripts invoking on_complete twice; normal clicking costs one point.
                complete += f'set_variable = {{ RUS_odb_{node["id"]}_rank = {rank} }}\n'
                complete += f'set_temp_variable = {{ RUS_odb_repeats_left = {count-rank} tooltip = RUS_odb_repeat_remaining_tt }}\n'
                if node['id']=='medals':
                    complete += f'FROM = {{ set_variable = {{ RUS_odb_medal_rank = {rank} }} }}\n'
                    complete += 'custom_effect_tooltip = RUS_odb_medal_upgrade_tt\n'
                    for modifier in ['army_attack_factor','army_defence_factor','army_org_factor','breakthrough_factor']:
                        complete += f'set_temp_variable = {{ RUS_medal_modifier_tt = 0.005 tooltip = {modifier}_tooltip }}\n'
                if node['id']=='investment':
                    complete += 'add_mio_funds = -1000\n'
                    complete += 'subtract_from_variable = { RUS_odb_previous_funds = 1000 }\n'
                    complete += 'FROM = { show_ideas_tooltip = RUS_odb_investment_1 }\n'
                    complete += 'hidden_effect = { FROM = {\n'
                    if rank>1: complete += f' remove_ideas = RUS_odb_investment_{rank-1}\n'
                    complete += f' add_ideas = RUS_odb_investment_{rank}\n}} }}\n'
                    if rank==count:
                        complete += 'FROM = { set_technology = { RUS_odb_unlock_modern_high_velocity_cannon = 1 RUS_odb_unlock_modern_heavy_cannon = 1 } }\n'
                if node['id']=='expansion':
                    complete += 'FROM = { show_ideas_tooltip = RUS_odb_expansion_1 }\n'
                    complete += 'hidden_effect = { FROM = {\n'
                    if rank>1: complete += f' remove_ideas = RUS_odb_expansion_{rank-1}\n'
                    complete += f' add_ideas = RUS_odb_expansion_{rank}\n}} }}\n'
            if complete: b += block('on_complete',complete)
            b += 'ai_will_do = { factor = 1 }\n'
            traits.append(block('trait',b))
        if node.get('source'):
            factory = node['source']
            flag = 'RUS_odb_merged_'+node['id']
            # MIO -> owner -> donor -> owner -> recipient. Persistent snapshots avoid
            # implicit ROOT/FROM variables and do not run completion effects on donor traits.
            fx = f'''if = {{
 limit = {{ FROM = {{ NOT = {{ has_country_flag = {flag} }} }} }}
 FROM = {{
  mio:{factory} = {{
    set_variable = {{ PREV.RUS_odb_transfer_size = size }}
   set_variable = {{ PREV.RUS_odb_transfer_funds = funds }}
   set_temp_variable = {{ RUS_odb_withdrawal = {{ value = funds multiply = -1 }} }}
   hidden_effect = {{ add_mio_funds = var:RUS_odb_withdrawal }}
  }}
  custom_effect_tooltip = USA_MIO_funds_and_level_merger_tt
  mio:{ORG} = {{
   add_mio_size = PREV.RUS_odb_transfer_size
   add_mio_funds = PREV.RUS_odb_transfer_funds
   add_to_variable = {{ RUS_odb_previous_funds = PREV.RUS_odb_transfer_funds }}
  }}
  set_country_flag = {flag}
  clear_variable = RUS_odb_transfer_size
  clear_variable = RUS_odb_transfer_funds
 }}
}}
custom_effect_tooltip = RUS_odb_transfer_tt
'''
            if node['id']=='toz':
                fx += '''FROM = {
 # Existing variables and the ten-day automatic mission are deliberately untouched.
 if = { limit = { NOT = { has_variable = TOZ_Divisions } } set_variable = { TOZ_Divisions = 4 } }
 if = { limit = { NOT = { has_variable = TOZ_Required_Funds } } set_variable = { TOZ_Required_Funds = 500 } }
 if = { limit = { NOT = { has_variable = RUS_odb_medal_rank } } set_variable = { RUS_odb_medal_rank = 0 } }
 if = {
  limit = { mio:RUS_toz_organisation = { NOT = { has_mio_flag = TOZ_Medal_Decision_Taken } } }
  activate_targeted_decision = { target = THIS decision = RUS_TOZ_Medals }
  activate_targeted_decision = { target = THIS decision = RUS_TOZ_Medals_automatic }
 }
}
custom_effect_tooltip = RUS_odb_medals_inherited_tt
'''
            # Company name keys differ from organization tokens in upstream KR.
            company={'toz':'toz','vpoz':'vpoz','imz':'imz','bmz':'bmz','obukhov':'obukhov_non_socrus'}[node['id']]
            loc[f'RUS_odb_{node["id"]}_unavailable_tt']=f'§Y${company}$§!不再可用。'
            fx=fx.replace('custom_effect_tooltip = RUS_odb_transfer_tt',f'custom_effect_tooltip = RUS_odb_{node["id"]}_unavailable_tt')
            if node['id']=='toz':
                fx=fx.replace('custom_effect_tooltip = RUS_odb_medals_inherited_tt','''FROM = {
 unlock_decision_tooltip = { decision = RUS_TOZ_Medals show_effect_tooltip = no }
 unlock_decision_tooltip = { decision = RUS_TOZ_Medals_automatic show_effect_tooltip = no }
 effect_tooltip = { RUS_odb_hand_out_medals = yes }
}''')
            effects.append(block('RUS_odb_merge_'+node['id'],fx))

    org = f'''name = {ORG}
icon = GFX_RUS_odb_organisation
allowed = {{ original_tag = RUS }}
visible = {{ FROM = {{ has_completed_focus = RUS_future_foreign_030 }} }}
available = {{ FROM = {{ has_completed_focus = RUS_future_foreign_030 }} }}
equipment_type = {{ {' '.join(spec['equipment'])} }}
research_categories = {{ infantry_weapons support_tech night_vision cat_special_forces_generic mio_cat_all_artillery_equipment train_tech }}
research_bonus = 0
on_industrial_manufacturer_assigned = {{
 add_to_variable = {{ RUS_odb_manufacturers = 1 }}
 if = {{ limit = {{ is_mio_trait_completed = RUS_odb_modular }} RUS_odb_show_learning = yes }}
}}
on_industrial_manufacturer_unassigned = {{ subtract_from_variable = {{ RUS_odb_manufacturers = 1 }} }}
on_tech_research_cancelled = {{ RUS_odb_reset_research = yes }}
on_tech_research_completed = {{
 if = {{ limit = {{ NOT = {{ is_mio_trait_completed = RUS_odb_bmz }} }} RUS_odb_reset_research = yes }}
}}
initial_trait = {{ name = RUS_odb_initial_trait }}
'''+''.join(traits)

    effects.append(block('RUS_odb_unlock',f'''if = {{
 limit = {{ has_dlc_aat = yes }}
 show_mio_tooltip = {ORG}
 hidden_effect = {{
  mio:{ORG} = {{
   if = {{
    limit = {{ NOT = {{ has_mio_flag = RUS_odb_initialized }} }}
    set_mio_flag = RUS_odb_initialized
    set_variable = {{ RUS_odb_medals_rank = 0 }}
    set_variable = {{ RUS_odb_optimization_rank = 0 }}
    set_variable = {{ RUS_odb_investment_rank = 0 }}
    set_variable = {{ RUS_odb_expansion_rank = 0 }}
    set_variable = {{ RUS_odb_manufacturers = 0 }}
    set_variable = {{ RUS_odb_previous_funds = funds }}
   }}
  }}
 }}
}}'''))
    effects.append(block('RUS_odb_reset_research','''hidden_effect = { set_mio_research_bonus = 0 }
custom_effect_tooltip = RUS_manufacturer_research_reset_tt'''))
    effects.append(block('RUS_odb_show_learning','''set_temp_variable = { weekly_research_speed_gain = 0.06 }
set_temp_variable = { max_research_speed = 1.25 }
set_temp_variable = { daily_funds_requirement = 1.28 }
set_temp_variable = { daily_funds_gained = { value = RUS_odb_weekly_funds divide = 7 } }
custom_effect_tooltip = RUS_odb_learning_tt'''))
    effects.append(block('RUS_odb_learning_weekly', f'''mio:{ORG} = {{
 if = {{
  limit = {{ is_mio_trait_completed = RUS_odb_modular }}
  set_variable = {{ RUS_odb_weekly_funds = {{ value = funds subtract = RUS_odb_previous_funds clamp = {{ min = 0 max = 1000000 }} }} }}
  if = {{
   limit = {{
    check_variable = {{ RUS_odb_manufacturers > 0 }}
    NOT = {{ check_variable = {{ RUS_odb_weekly_funds < 8.96 }} }}
    check_variable = {{ research_bonus < 1.25 }}
   }}
   add_mio_research_bonus = 0.06
   if = {{
    limit = {{ check_variable = {{ research_bonus > 1.25 }} }}
    # Clamp the final bonus including the infantry bureau's organization modifier.
    set_temp_variable = {{ RUS_odb_base_cap = {{ value = 1.25 subtract = modifier@military_industrial_organization_research_bonus }} }}
    set_mio_research_bonus = RUS_odb_base_cap
   }}
  }}
  set_variable = {{ RUS_odb_previous_funds = funds }}
 }}
}}'''))
    effects.append(block('RUS_odb_daily',f'''mio:{ORG} = {{
 if = {{
  limit = {{ is_mio_trait_completed = RUS_odb_obukhov }}
  add_to_variable = {{ RUS_odb_funding_days = 1 }}
  if = {{
   limit = {{ NOT = {{ check_variable = {{ RUS_odb_funding_days < 30 }} }} }}
   set_variable = {{ RUS_odb_funding_days = 0 }}
   PREV = {{
    random_military_industrial_organization = {{
     limit = {{ is_mio_available = yes is_mio_assigned_to_task = yes }}
     set_temp_variable_to_random = {{ var = RUS_odb_grant min = 100 max = 300 integer = yes }}
     add_mio_funds = var:RUS_odb_grant
     if = {{
      limit = {{ is_military_industrial_organization = {ORG} }}
      add_to_variable = {{ RUS_odb_previous_funds = RUS_odb_grant }}
     }}
    }}
   }}
  }}
 }}
}}'''))
    effects.append(block('RUS_odb_pay_medal_funds',f'''set_temp_variable = {{ funds_change = {{ value = TOZ_Required_Funds?500 multiply = -1 }} }}
if = {{
 limit = {{ has_country_flag = RUS_odb_merged_toz }}
 mio:{ORG} = {{
  add_mio_funds = var:funds_change
  add_to_variable = {{ RUS_odb_previous_funds = funds_change }}
 }}
}}
else = {{ mio:RUS_toz_organisation = {{ add_mio_funds = var:funds_change }} }}'''))
    # No change to existing medals: a rank is stamped when each NEW award is made.
    effects.append(block('RUS_odb_hand_out_medals','''custom_effect_tooltip = toz_give_medals_tt
set_temp_variable = { RUS_odb_medal_value = { value = RUS_odb_medal_rank multiply = 0.005 add = 0.1 } }
set_temp_variable = { RUS_medal_modifier_tt = RUS_odb_medal_value tooltip = army_attack_factor_tooltip }
set_temp_variable = { RUS_medal_modifier_tt = RUS_odb_medal_value tooltip = army_defence_factor_tooltip }
set_temp_variable = { RUS_medal_modifier_tt = RUS_odb_medal_value tooltip = army_org_factor_tooltip }
set_temp_variable = { RUS_medal_modifier_tt = RUS_odb_medal_value tooltip = breakthrough_factor_tooltip }
custom_effect_tooltip = RUS_TOZ_Org_reset_tt
for_loop_effect = {
 start = 0
 end = TOZ_Divisions
 compare = less_than
 random_country_division = {
  limit = { unit_organization > 0.02 }
  add_history_entry = { key = RUS_TOZ_Medal_Award subject = "RUS_TOZ_Medal_Award" allow = yes }
  meta_effect = {
   text = { add_unit_medal_to_latest_entry = { unit_medals = RUS_odb_medal_[RANK] } }
   RANK = "[?RUS_odb_medal_rank|0]"
  }
  set_unit_organization = 0.01
 }
}
add_to_variable = { RUS_TOZ_total_medals = TOZ_Divisions }'''))
    trig = block('RUS_odb_has_medal_funds',f'''OR = {{
 AND = {{
  has_country_flag = RUS_odb_merged_toz
  mio:{ORG} = {{ NOT = {{ check_variable = {{ funds < ROOT.TOZ_Required_Funds?500 }} }} }}
 }}
 AND = {{
  NOT = {{ has_country_flag = RUS_odb_merged_toz }}
  mio:RUS_toz_organisation = {{ NOT = {{ check_variable = {{ funds < ROOT.TOZ_Required_Funds?500 }} }} }}
 }}
}}''')
    ideas = [block('RUS_odb_heavy_research','''allowed = { always = no }
research_bonus = { artillery = 0.15 }
modifier = { special_project_speed_factor = 0.15 }''')]
    for group,n,mod,step in [('investment',10,'consumer_goods_expected_value',Decimal('0.01')),('expansion',5,'global_building_slots',Decimal(1))]:
        for rank in range(1,n+1):
            key=f'RUS_odb_{group}_{rank}'
            ideas.append(block(key,f'allowed = {{ always = no }}\nmodifier = {{ {mod} = {step*rank} }}'))
            loc[key] = '加大投资' if group=='investment' else '扩建火炮制造厂'
    medals=[]
    for rank in range(11):
        value=Decimal('0.10')+Decimal('0.005')*rank
        medals.append(block(f'RUS_odb_medal_{rank}',f'''available = {{ always = no }}
frame = 4
icon = "GFX_medal_icon_default"
cost = 15
unit_modifiers = {{ army_attack_factor = {value} army_defence_factor = {value} army_org_factor = {value} breakthrough_factor = {value} }}
officer_xp = 100'''))
        loc[f'RUS_odb_medal_{rank}']='图拉军功勋章'
        loc[f'RUS_odb_medal_{rank}_desc']='由陆军兵器设计总局颁发，表彰作战中的勇气与集体荣誉。'
    on = block('on_actions',block('on_weekly_RUS','effect = { if = { limit = { has_dlc_aat = yes has_completed_focus = RUS_future_foreign_030 } RUS_odb_learning_weekly = yes } }')+block('on_daily_RUS','effect = { if = { limit = { has_dlc_aat = yes has_completed_focus = RUS_future_foreign_030 } RUS_odb_daily = yes } }'))
    paths={
        f'common/military_industrial_organization/organizations/{STEM}.txt':block(ORG,org),
        f'common/scripted_effects/{STEM}_effects.txt':''.join(effects),
        f'common/scripted_triggers/{STEM}_triggers.txt':trig,
        f'common/ideas/{STEM}_ideas.txt':block('ideas',block('hidden_ideas',''.join(ideas))),
        f'common/unit_medals/{STEM}_medals.txt':block('unit_medals',''.join(medals)),
        f'common/on_actions/{STEM}_on_actions.txt':on,
        f'common/scripted_localisation/{STEM}_localisation.txt':'''define_text = {
 name = GetRUSOdbMedalManufacturer
 text = { trigger = { has_country_flag = RUS_odb_merged_toz } localization_key = RUS_odb_organisation }
 text = { localization_key = toz }
}
define_text = {
 name = GetRUSOdbLearningStatus
 text = {
  trigger = { check_variable = { RUS_odb_manufacturers > 0 } NOT = { check_variable = { RUS_odb_weekly_funds < 8.96 } } }
  localization_key = RUS_MIO_Research_Gain_positive_tt
 }
 text = { localization_key = RUS_MIO_Research_Gain_negative_tt }
}
''',
        f'localisation/simp_chinese/{STEM}_l_simp_chinese.yml':'\ufeffl_simp_chinese:\n'+''.join(' '+k+':0 '+json.dumps(v,ensure_ascii=False)+'\n' for k,v in loc.items()),
    }
    return paths

def patch_legacy_effects(text):
    """Called by the opening generator too: it reconstructs this file from KR."""
    from hoi4_politics_blocks import parse
    n=next(n for n in parse(text) if n.k=='RUS_TOZ_Hand_Out_Medals')
    if 'RUS_odb_hand_out_medals' not in n.raw():
        original=''.join(('\t'+line if line.strip() else '')+'\n' for line in n.inner().strip('\n').splitlines())
        replacement=n.k+' = {\n\tif = {\n\t\tlimit = { has_country_flag = RUS_odb_merged_toz }\n\t\tRUS_odb_hand_out_medals = yes\n\t}\n\telse = {\n'+original+'\t}\n}\n'
        text=text[:n.a]+replacement+text[n.b:]
    return text

def adapters(spec):
    from hoi4_politics_blocks import parse
    paths={}
    rel='common/military_industrial_organization/organizations/RUS_organization.txt'
    text=(ROOT/rel).read_text(encoding='utf-8-sig');changes=[]
    by_source={n['source']:n['id'] for n in spec['nodes'] if n.get('source')}
    for n in parse(text):
        if n.k not in by_source:continue
        available=n.one('available');flag='RUS_odb_merged_'+by_source[n.k]
        raw=available.raw()
        if flag not in raw:
            raw=raw.rstrip().removesuffix('}').rstrip()+'\n\t\tFROM = { NOT = { has_country_flag = '+flag+' } }\n\t}'
        raw='\n'.join(line.rstrip() for line in raw.splitlines())
        if raw!=available.raw():changes.append((available.a,available.b,raw))
    for a,b,s in sorted(changes,reverse=True):text=text[:a]+s+text[b:]
    paths[rel]=text
    rel='common/scripted_effects/RUS effects (Russia).txt'
    paths[rel]=patch_legacy_effects((ROOT/rel).read_text(encoding='utf-8-sig'))
    rel='common/decisions/RUS decisions (Russia).txt'
    text=(ROOT/rel).read_text(encoding='utf-8-sig');changes=[]
    def walk(nodes):
        for n in nodes:
            yield n
            if isinstance(n.v,list):yield from walk(n.v)
    for cat in parse(text):
        for n in cat.v if isinstance(cat.v,list) else []:
            if n.k not in ['RUS_TOZ_Medals','RUS_TOZ_Medals_automatic_mission']:continue
            raw=n.raw()
            # Replace only the two old checks and two old payments. Preserve mission timers.
            for x in reversed(list(walk(parse(raw)))):
                if x.k=='mio:RUS_toz_organisation' and 'funds < ROOT.TOZ_Required_Funds?500' in x.raw():
                    raw=raw[:x.a]+'RUS_odb_has_medal_funds = yes'+raw[x.b:]
            import re
            raw=re.sub(r'set_temp_variable\s*=\s*\{ funds_change = TOZ_Required_Funds\?500 \}\s*multiply_temp_variable\s*=\s*\{ funds_change = -1 \}\s*mio:RUS_toz_organisation\s*=\s*\{ add_mio_funds = var:funds_change \}', 'RUS_odb_pay_medal_funds = yes',raw)
            raw=raw.replace('custom_cost_text = RUS_TOZ_Funds_Medals_Requirement','custom_cost_text = RUS_odb_medal_funds_cost')
            if raw!=n.raw():changes.append((n.a,n.b,raw))
    for a,b,s in sorted(changes,reverse=True):text=text[:a]+s+text[b:]
    paths[rel]=text
    rel='common/national_focus/00_RUS_future_foreign_policy_skeleton.txt'
    text=(ROOT/rel).read_text(encoding='utf-8-sig')
    n=next(n for n in parse(text) if n.value('id')=='RUS_future_foreign_030')
    reward=n.one('completion_reward')
    if 'RUS_odb_unlock' not in reward.raw():
        text=text[:reward.ib].rstrip()+'\n\t\tRUS_odb_unlock = yes\n\t'+text[reward.ib:]
    else:
        raw='\n'.join(line.rstrip() for line in reward.raw().splitlines())
        text=text[:reward.a]+raw+text[reward.b:]
    paths[rel]=text
    return paths

def main():
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');p.add_argument('--check',action='store_true');a=p.parse_args()
    spec=json.loads(SPEC_PATH.read_text(encoding='utf-8'))
    expected=render(spec)|adapters(spec);bad=[]
    for rel,s in expected.items():
        path=ROOT/rel;data=s.encode('utf-8')
        if a.write:
            path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        elif not path.exists() or path.read_text(encoding='utf-8')!=s:bad.append(rel)
    if bad:raise SystemExit('Generated files differ: '+', '.join(bad))
    print(f'Ordnance MIO: {len(expected)} generated files '+('written' if a.write else 'match (read-only)'))
if __name__=='__main__':main()
