"""Drawio-approved armour bureau; read-only by default, explicit --write only.

Only isolated definitions, seven donor availability gates and one focus dispatch.
No shared tech tree, unit definition or route/focus layout override.
"""
from pathlib import Path
from decimal import Decimal
import argparse,json
from hoi4_politics_blocks import load,parse
from generate_ordnance_design_bureau import block

ROOT=Path(__file__).resolve().parents[1]
SPEC_PATH=ROOT/'tools/design/armour_design_bureau/spec.json'
ORG='RUS_adb_organisation'
STEM='RUS_armour_design_bureau'
FOCUS='common/national_focus/00_RUS_future_foreign_policy_skeleton.txt'
DONORS='common/military_industrial_organization/organizations/RUS_organization.txt'

def render(spec):
    company_names={n['id']:n['name'] for n in json.loads((ROOT/'tools/design/RUS_stalin_mio_names.json').read_text(encoding='utf-8'))}
    byid={n['id']:n for n in spec['nodes']}
    loc={
      ORG:'陆军装甲设计总局','RUS_adb_initial_trait':'装甲车辆联合设计体系',
      'RUS_adb_repeat_remaining_tt':'§C这项特质还可以培养$RIGHT|Y0$次。§!',
      'RUS_adb_learning_tt':'§g当被分配为£industrial_manufacturer_icon §H制造商§!时，该§H军工机构§!将逐渐获得£research_speed_icon §H研究加成§!（分配到多条生产线时效果不会叠加）\n\n每周£research_speed_icon §H研究加成§!增长：[?RUS_adb_policy_research_gain|2W%]\n£research_speed_icon §H研究加成§!软上限：[?RUS_adb_policy_research_cap|2W%]\n获取£research_speed_icon §H研究加成§!所需的最低每日§H经费§!：[?daily_funds_requirement|2W]\n\n[GetRUSAdbLearningStatus]§!',
      'RUS_adb_research_cic_tt':'\n§g提高§H军工机构§!规模，也将提高通过研究获取的额外£civ_factory_output §H经济产能盈余§!，每有一级规模提高[?RUS_adb_cic_per_level|G0]。\n\n在该活动期间，获取的£civ_factory_output §H经济产能盈余§!总值：[?RUS_adb_total_campaign_cic|W0]§!',
      'RUS_adb_extreme_design':'极限设计',
      'RUS_adb_armour_battalions_tt':'§Y坦克、两栖坦克及其自行武器营：§!',
      'RUS_adb_all_terrain_tt':'§Y所有地形：§!',
      'RUS_adb_combat_width_delta_tt':'  $STAT_ARMY_COMBAT_WIDTH$$RIGHT|-=2$',
      'RUS_adb_terrain_attack_delta_tt':'  $STAT_ADJUSTER_ATTACK$$RIGHT|+=%1$',
      'RUS_adb_terrain_defence_delta_tt':'  $STAT_ADJUSTER_DEFENCE$$RIGHT|+=%1$',
      'RUS_adb_terrain_movement_delta_tt':'  $STAT_ADJUSTER_MOVEMENT$$RIGHT|+=%1$'
    }
    effects=[];traits=[]
    for n in spec['nodes']:
        key='RUS_adb_'+n['id'];count=n.get('repeat',1)
        loc[key]=n['name']
        if n.get('source'):loc[key]='整合'+company_names[n['id']]
        for rank in range(1,count+1):
            token=key if count==1 else key+'_'+str(rank)
            loc[token]=loc[key]
            b=f'token = {token}\nname = {token}\nicon = {n["icon"]}\nposition = {{ x = {n["x"]} y = {n["y"]} }}\n'
            if n.get('parents'):b+='all_parents = { '+' '.join('RUS_adb_'+p for p in n['parents'])+' }\n'
            if n.get('limit'):b+='limit_to_equipment_type = { '+' '.join(n['limit'])+' }\n'
            for field in ['equipment_bonus','production_bonus','organization_modifier']:
                if n.get(field):b+=block(field,'\n'.join(f'{k} = {v}' for k,v in n[field].items()))
            available=''
            if count>1:
                v=f'check_variable = {{ RUS_adb_{n["id"]}_rank = {rank-1} }}'
                if rank==count:v=f'NOT = {{ check_variable = {{ RUS_adb_{n["id"]}_rank < {rank-1} }} }}'
                b+=block('visible',v)
                available+=f'check_variable = {{ RUS_adb_{n["id"]}_rank = {rank-1} }}\n'
            if n.get('source'):
                available+=f'FROM = {{ hidden_trigger = {{ has_military_industrial_organization = {n["source"]} }} mio:{n["source"]} = {{ is_mio_available = yes }} }}\n'
            if n['id']=='guidance':available+='check_variable = { funds > 1000 tooltip = MIO_more_than_X_funds }\n'
            if available:b+=block('available',available)
            complete=''
            if n.get('source'):complete+=key.replace('RUS_adb_','RUS_adb_merge_')+' = yes\n'
            if n['id']=='chtz':complete+='set_variable = { RUS_adb_previous_funds = funds }\nRUS_adb_show_learning = yes\n'
            if n['id']=='platform':complete+='custom_effect_tooltip = RUS_manufacturer_research_no_reset_tt\n'
            if n['id']=='exchange':
                complete+='custom_effect_tooltip = INDUSTRIAL_ORG_TRAIT_TOOLTIP_ON_TECH_COMPLETED\nset_temp_variable = { RUS_adb_research_cic = { value = size multiply = 1000 } }\nFROM = { effect_tooltip = { add_cic = RUS_adb_research_cic } }\ncustom_effect_tooltip = RUS_adb_research_cic_tt\n'
            if count>1:
                complete+=f'set_variable = {{ RUS_adb_{n["id"]}_rank = {rank} }}\n'
                complete+=f'set_temp_variable = {{ RUS_adb_repeats_left = {count-rank} tooltip = RUS_adb_repeat_remaining_tt }}\n'
            if n['id']=='guidance':
                complete+='add_mio_funds = -1000\nsubtract_from_variable = { RUS_adb_previous_funds = 1000 }\nFROM = { show_ideas_tooltip = RUS_adb_extreme_design_1 }\nhidden_effect = { FROM = {\n'
                if rank>1:complete+=f'remove_ideas = RUS_adb_extreme_design_{rank-1}\n'
                complete+=f'add_ideas = RUS_adb_extreme_design_{rank}\n}} }}\n'
                complete+='custom_effect_tooltip = RUS_adb_armour_battalions_tt\n'
                complete+=f'set_temp_variable = {{ RUS_adb_width_delta = {n["unit_bonus"]["combat_width"]} tooltip = RUS_adb_combat_width_delta_tt }}\n'
                complete+=f'hidden_effect = {{ FROM = {{ set_technology = {{ RUS_adb_guidance_bonus_{rank} = 1 }} }} }}\n'
            if n['id']=='logistics':
                complete+='custom_effect_tooltip = RUS_adb_armour_battalions_tt\ncustom_effect_tooltip = RUS_adb_all_terrain_tt\n'
                for stat,value in n['terrain_bonus'].items():
                    complete+=f'set_temp_variable = {{ RUS_adb_terrain_delta = {value} tooltip = RUS_adb_terrain_{stat}_delta_tt }}\n'
                complete+=f'hidden_effect = {{ FROM = {{ set_technology = {{ RUS_adb_logistics_bonus_{rank} = 1 }} }} }}\n'
            if complete:b+=block('on_complete',complete)
            b+='ai_will_do = { factor = 1 }\n'
            traits.append(block('trait',b))
        if n.get('source'):
            old=n['source'];flag='RUS_adb_merged_'+n['id']
            effects.append(block('RUS_adb_merge_'+n['id'],f'''if = {{
 limit = {{ FROM = {{ has_military_industrial_organization = {old} NOT = {{ has_country_flag = {flag} }} }} }}
 FROM = {{
  mio:{old} = {{
   set_variable = {{ PREV.RUS_adb_transfer_size = size }}
   set_variable = {{ PREV.RUS_adb_transfer_funds = funds }}
   set_temp_variable = {{ RUS_adb_withdrawal = {{ value = funds multiply = -1 }} }}
   hidden_effect = {{ add_mio_funds = var:RUS_adb_withdrawal }}
  }}
  custom_effect_tooltip = USA_MIO_funds_and_level_merger_tt
  mio:{ORG} = {{
   add_mio_size = PREV.RUS_adb_transfer_size
   add_mio_funds = PREV.RUS_adb_transfer_funds
   add_to_variable = {{ RUS_adb_previous_funds = PREV.RUS_adb_transfer_funds }}
  }}
  set_country_flag = {flag}
  clear_variable = RUS_adb_transfer_size
  clear_variable = RUS_adb_transfer_funds
 }}
}}
custom_effect_tooltip = RUS_adb_{n['id']}_unavailable_tt'''))
            loc['RUS_adb_'+n['id']+'_unavailable_tt']='§Y[RUSStalinMioCompany_'+n['id']+']§!不再可用。'
    org=f'''name = {ORG}
icon = GFX_RUS_adb_organisation
allowed = {{ original_tag = RUS }}
visible = {{ FROM = {{ has_completed_focus = RUS_future_foreign_030 }} }}
available = {{ FROM = {{ has_completed_focus = RUS_future_foreign_030 }} }}
equipment_type = {{ {' '.join(spec['equipment'])} }}
research_categories = {{ mio_cat_tech_all_armor_and_modules mio_cat_tech_all_motorized_mechanized cat_armored_cars }}
research_bonus = 0
initial_trait = {{ name = RUS_adb_initial_trait }}
on_industrial_manufacturer_assigned = {{
 add_to_variable = {{ RUS_adb_manufacturers = 1 }}
 if = {{ limit = {{ is_mio_trait_completed = RUS_adb_chtz }} RUS_adb_show_learning = yes }}
}}
on_industrial_manufacturer_unassigned = {{
 subtract_from_variable = {{ RUS_adb_manufacturers = 1 }}
 if = {{ limit = {{ check_variable = {{ RUS_adb_manufacturers < 0 }} }} set_variable = {{ RUS_adb_manufacturers = 0 }} }}
}}
on_tech_research_cancelled = {{ RUS_adb_reset_research = yes }}
on_tech_research_completed = {{
 if = {{ limit = {{ is_mio_trait_completed = RUS_adb_exchange }} RUS_adb_research_income = yes }}
 if = {{ limit = {{ NOT = {{ is_mio_trait_completed = RUS_adb_platform }} }} RUS_adb_reset_research = yes }}
}}
'''+''.join(traits)
    effects.append(block('RUS_adb_unlock',f'''if = {{
 limit = {{ has_dlc_aat = yes has_military_industrial_organization = {ORG} }}
 show_mio_tooltip = {ORG}
 hidden_effect = {{ mio:{ORG} = {{
  if = {{
   limit = {{ NOT = {{ has_mio_flag = RUS_adb_initialized }} }}
   set_mio_flag = RUS_adb_initialized
   set_variable = {{ RUS_adb_previous_funds = funds }}
   set_variable = {{ max_research_speed = 0.55 }}
   set_variable = {{ weekly_research_speed_gain = 0.01 }}
   set_variable = {{ RUS_adb_cic_per_level = 1000 }}
  }}
 }} }}
}}'''))
    effects.append(block('RUS_adb_reset_research','hidden_effect = { set_mio_research_bonus = 0 }\ncustom_effect_tooltip = RUS_manufacturer_research_reset_tt'))
    effects.append(block('RUS_adb_show_learning','''set_temp_variable = { RUS_adb_policy_research_gain = weekly_research_speed_gain?0.01 }
set_temp_variable = { RUS_adb_policy_research_cap = max_research_speed?0.55 }
set_temp_variable = { daily_funds_requirement = 1.28 }
set_temp_variable = { daily_funds_gained = { value = RUS_adb_weekly_funds divide = 7 } }
custom_effect_tooltip = RUS_adb_learning_tt'''))
    effects.append(block('RUS_adb_research_income','''set_temp_variable = { RUS_adb_research_cic = { value = size multiply = 1000 } }
FROM = { add_cic = RUS_adb_research_cic }
add_to_variable = { RUS_adb_total_campaign_cic = RUS_adb_research_cic }
custom_effect_tooltip = RUS_adb_research_cic_tt'''))
    effects.append(block('RUS_adb_learning_weekly',f'''mio:{ORG} = {{
 if = {{
  limit = {{ is_mio_trait_completed = RUS_adb_chtz }}
  set_variable = {{ RUS_adb_weekly_funds = {{ value = funds subtract = RUS_adb_previous_funds clamp = {{ min = 0 max = 1000000 }} }} }}
  if = {{
   limit = {{
    check_variable = {{ RUS_adb_manufacturers > 0 }}
    NOT = {{ check_variable = {{ RUS_adb_weekly_funds < 8.96 }} }}
    check_variable = {{ research_bonus < max_research_speed?0.55 }}
   }}
   set_temp_variable = {{ RUS_adb_policy_research_gain = weekly_research_speed_gain?0.01 }}
   add_mio_research_bonus = RUS_adb_policy_research_gain
   if = {{
    limit = {{ check_variable = {{ research_bonus > max_research_speed?0.55 }} }}
    set_temp_variable = {{ RUS_adb_base_cap = {{ value = max_research_speed?0.55 subtract = modifier@military_industrial_organization_research_bonus }} }}
    set_mio_research_bonus = RUS_adb_base_cap
   }}
  }}
 }}
 set_variable = {{ RUS_adb_previous_funds = funds }}
}}'''))
    ideas=[];tech=[]
    for rank in range(1,11):
        name='RUS_adb_extreme_design_'+str(rank);loc[name]='$RUS_adb_extreme_design$'
        ideas.append(block(name,'allowed = { always = no }\nmodifier = { consumer_goods_expected_value = '+str(Decimal('.01')*rank)+' }'))
        for group in ['guidance','logistics']:
            name=f'RUS_adb_{group}_bonus_{rank}';loc[name]=('指导作战' if group=='guidance' else '联勤保障')+' '+str(rank)
            loc[name+'_desc']='装甲部队在联合设计与持续试验中积累经验，将新的成果用于战场。'
            stats='combat_width = '+str(byid['guidance']['unit_bonus']['combat_width']) if group=='guidance' else ''.join(block(t,'\n'.join(f'{k} = {v}' for k,v in byid['logistics']['terrain_bonus'].items())) for t in spec['terrains'])
            tech.append(block(name,'allow = { always = no }\n'+''.join(block(u,stats) for u in spec['units'])))
    local='''defined_text = {
 name = GetRUSAdbLearningStatus
 text = { trigger = { check_variable = { RUS_adb_manufacturers > 0 } NOT = { check_variable = { RUS_adb_weekly_funds < 8.96 } } } localization_key = RUS_MIO_Research_Gain_positive_tt }
 text = { localization_key = RUS_MIO_Research_Gain_negative_tt }
}
'''
    return {
     f'common/military_industrial_organization/organizations/{STEM}.txt':block(ORG,org),
     f'common/scripted_effects/{STEM}_effects.txt':''.join(effects),
     f'common/ideas/{STEM}_ideas.txt':block('ideas',block('hidden_ideas',''.join(ideas))),
     f'common/technologies/{STEM}_technologies.txt':block('technologies',''.join(tech)),
     f'common/on_actions/{STEM}_on_actions.txt':block('on_actions',block('on_weekly_RUS',f'effect = {{ if = {{ limit = {{ has_dlc_aat = yes has_military_industrial_organization = {ORG} has_completed_focus = RUS_future_foreign_030 }} RUS_adb_learning_weekly = yes }} }}')),
     f'common/scripted_localisation/{STEM}_localisation.txt':local,
     f'localisation/simp_chinese/{STEM}_l_simp_chinese.yml':'\ufeffl_simp_chinese:\n'+''.join(' '+k+':0 '+json.dumps(v,ensure_ascii=False)+'\n' for k,v in loc.items()),
     'interface/RUS_armour_design_bureau.gfx':'spriteTypes = {\n spriteType = { name = "GFX_RUS_adb_organisation" texturefile = "gfx/interface/ideas/RUS_adb_organisation.png" legacy_lazy_load = no }\n}\n'
    }

def adapters(spec):
    text=(ROOT/DONORS).read_text(encoding='utf-8-sig');edits=[]
    mapping={n['source']:n['id'] for n in spec['nodes'] if n.get('source')}
    for org in parse(text):
        if org.k not in mapping:continue
        flag='RUS_adb_merged_'+mapping[org.k];n=org.one('available')
        if flag not in n.raw():edits.append((n.ib,'\n\t\tFROM = { NOT = { has_country_flag = '+flag+' } }\n\t'))
    for at,s in sorted(edits,reverse=True):text=text[:at].rstrip()+s+text[at:]
    paths={DONORS:text}
    text=(ROOT/FOCUS).read_text(encoding='utf-8-sig');n=next(n for n in parse(text) if n.value('id')=='RUS_future_foreign_030').one('completion_reward')
    if 'RUS_adb_unlock' not in n.raw():text=text[:n.ib].rstrip()+'\n\t\tRUS_adb_unlock = yes\n\t'+text[n.ib:]
    paths[FOCUS]=text
    return paths

def main():
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');p.add_argument('--check',action='store_true');a=p.parse_args()
    spec=json.loads(SPEC_PATH.read_text(encoding='utf-8'));bad=[]
    for rel,text in (render(spec)|adapters(spec)).items():
        path=ROOT/rel
        if a.write:path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf-8',newline='\n')
        elif not path.exists() or path.read_text(encoding='utf-8')!=text:bad.append(rel)
    if bad:raise SystemExit('Stale armour bureau outputs: '+', '.join(bad))
    print('PASS: armour bureau (16 slots, 52 traits) '+('written' if a.write else 'matches (read-only)'))
if __name__=='__main__':main()
