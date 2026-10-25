"""Education balance and focus authoring source; importing never writes files."""
from __future__ import annotations

KINDS = {'basic': '基础教育', 'higher': '高等教育', 'technical': '职业技术', 'culture': '文化与社会动员', 'military':'国防动员'}
POSTER_CATEGORIES = {
 1: ('军事与保卫', (1, 2, 4, 13)),
 2: ('经济与生产', (3, 7, 8)),
 3: ('社会与群体', (5, 10, 11)),
 4: ('文教与思想', (9, 12)),
 5: ('国家与生活', (14, 15)),
 6: ('胜利与纪念', (6,)),
}
POSTER_PREFIX_CATEGORY = {'EDU':4,'WOM':3,'YTH':3,'IND':2}
HEAT_ECONOMIC_MODIFIERS = {'production_factory_start_efficiency_factor','production_factory_efficiency_gain_factor'}
HEAT_WEEKLY_STABILITY_THRESHOLD = 75
HEAT_WEEKLY_STABILITY_MAX_LOSS = .01
EDUCATION_GAIN_CAPS = {'basic':4, 'higher':2}
HEAT_QUALITY_CURVATURE = 4
HEAT_STABILITY_PRESSURE = .08
HEAT_POLITICAL_PRESSURE = .15
# id, slogan, category, duration, PP, total base/higher gain, enthusiasm per 30 days, poster code, temporary modifiers
ROWS = [
 ('literacy','知识打破奴隶的锁链！','basic',90,25,4,0,0,'EDU02',{'research_speed_factor':.01}),
 ('schools','让每一个村庄都有学校！','basic',120,40,4,0,-.5,'EDU01',{'monthly_population':.05,'stability_factor':.015,'consumer_goods_factor':.05}),
 ('night_school','工农群众，拿起书本！','basic',90,30,4,1,.5,'EDU66',{'equipment_conversion_speed':.10,'industrial_capacity_factory':.025}),
 ('teachers','为人民培养人民教师！','basic',120,40,4,2,0,'WOM16',{'political_advisor_cost_factor':-.10,'political_power_cost':-.025}),
 ('university','工农群众，走进大学！','higher',120,45,1,2,.5,'EDU42',{'research_speed_factor':.015,'consumer_goods_factor':.05}),
 ('science','科学必须服务于人民！','higher',180,55,0,2,0,'EDU56',{'research_speed_factor':.015,'local_resources_factor':.05}),
 ('pedagogy','培养建设新社会的师资！','higher',120,45,3,2,0,'EDU68',{'political_advisor_cost_factor':-.10,'political_power_factor':.025}),
 ('technical','掌握技术，建设社会主义！','technical',90,35,1,2,1,'EDU30',{'equipment_conversion_speed':.10,'industrial_capacity_factory':.02}),
 ('agriculture','把科学带到田野！','technical',90,30,2,1,1,'YTH03',{'industrial_capacity_factory':.025}),
 ('reading','让书籍走进千家万户！','culture',90,20,.5,.5,2,'EDU13',{'stability_weekly':.0005,'political_power_factor':.025}),
 ('outreach','把文化带到田野和车间！','culture',90,25,.5,0,3,'EDU44',{'resistance_growth_on_our_occupied_states':-.05,'stability_factor':.015}),
 ('construction','用劳动建设我们的新生活！','culture',90,25,0,0,4,'IND07',{'production_speed_rail_way_factor':.10,'production_speed_supply_node_factor':.05,'industrial_capacity_factory':.025}),
 ('mentoring','老工人，扶青年一把！','technical',90,30,1,2,1,'YTH06',{'equipment_conversion_speed':.10,'production_factory_max_efficiency_factor':.025,'industrial_capacity_factory':.015}),
 ('library','让每个工人俱乐部都有图书室！','culture',120,30,2,1,1,'EDU07',{'political_advisor_cost_factor':-.05,'research_speed_factor':.01}),
]
ACTIVITIES = [dict(zip(('id','name','kind','days','cost','basic','higher','heat','poster','modifiers'), row)) for row in ROWS]
for activity in ACTIVITIES:
    prefix = ''.join(c for c in activity['poster'] if c.isalpha())
    activity['category'] = POSTER_PREFIX_CATEGORY[prefix]
from education_poster_expansion import additional_activities
ACTIVITIES += additional_activities()
# The decision modifier applies each benefit and its explicit cost together.
# Costs are separate authoring data so they cannot silently replace a benefit.
CAMPAIGN_COSTS = {
 'literacy':{'production_speed_buildings_factor':-.05},
 'schools':{}, 'night_school':{'production_factory_efficiency_gain_factor':-.075},
 'teachers':{'production_speed_buildings_factor':-.075}, 'university':{},
 'science':{'political_power_cost':.05}, 'pedagogy':{'industrial_capacity_factory':-.05},
 'technical':{'political_power_cost':.05}, 'agriculture':{'consumer_goods_factor':.005},
 'reading':{'political_power_cost':.025}, 'outreach':{'consumer_goods_factor':.005},
 'construction':{'consumer_goods_factor':.05}, 'mentoring':{'political_power_cost':.05},
 'library':{'political_power_cost':.025},
 'defend_leningrad':{'industrial_capacity_factory':-.075}, 'defend_moscow':{'industrial_capacity_factory':-.075},
 'march_west':{'supply_consumption_factor':.025}, 'defend_october':{'political_power_cost':.05},
 'dnieper_water':{'supply_consumption_factor':.025}, 'await_victory':{'political_power_cost':.025},
 'advanced_theory':{'consumer_goods_factor':.05}, 'cultural_enemies':{'stability_factor':-.05},
 'mothers_literacy':{'political_power_cost':.025}, 'children_workers':{'production_speed_buildings_factor':-.05},
 'ten_days':{'industrial_capacity_factory':-.05}, 'book_fair':{'consumer_goods_factor':.005},
 'grain_delivery':{'consumer_goods_factor':.05}, 'end_kitchen_slavery':{'production_speed_buildings_factor':-.05},
 'soviet_elections':{'industrial_capacity_factory':-.05}, 'protect_children':{'stability_factor':-.05},
 'lenin_banner':{'stability_factor':-.05}, 'labour_productivity':{'political_power_cost':.05},
 'socialist_industry':{'consumer_goods_factor':.05}, 'lenin_electrification':{'production_lack_of_resource_penalty_factor':.025},
 'tractors_nurseries':{'production_speed_buildings_factor':-.05}, 'agricultural_statistics':{'political_power_cost':.025},
 'complete_collectivisation':{'stability_factor':-.075}, 'harvest_battle':{'industrial_capacity_factory':-.05},
 'vigilance':{'political_power_cost':.05}, 'production_vices':{'political_power_cost':.025},
 'public_property':{'stability_factor':-.05}, 'false_shock_workers':{'political_power_cost':.05},
 'motherland_calls':{'industrial_capacity_factory':-.02}, 'volunteer_enlistment':{'consumer_goods_factor':.05},
 'red_banner_oath':{'training_time_army_factor':.025}, 'women_frontline':{'consumer_goods_factor':.05},
 'people_and_army':{'political_power_cost':.05}, 'honour_freedom':{'supply_consumption_factor':.025},
 'ukrainian_liberators':{'political_power_cost':.05}, 'beloved_motherland':{'consumer_goods_factor':.005},
 'long_live_peace':{'training_time_army_factor':.05},
}
assert set(CAMPAIGN_COSTS)=={a['id'] for a in ACTIVITIES}
for activity in ACTIVITIES:
    costs=CAMPAIGN_COSTS[activity['id']]
    assert not set(costs)&set(activity['modifiers']),activity['id']
    activity['modifiers'].update(costs)
    if activity['id'] in ('red_banner_oath','people_and_army'):
        activity['modifiers']['experience_gain_army_factor']=.05
    if activity['id']=='honour_freedom':activity['modifiers']['command_power_gain_mult']=.10
CONTROLS = [
 dict(id='listen',name='听取群众的声音！',kind='control',days=30,cost=20,basic=0,higher=0,heat=10,modifiers={'political_power_cost':-.025}),
 dict(id='restore_order',name='让课堂与车间恢复秩序！',kind='control',days=30,cost=20,basic=0,higher=0,heat=-12,modifiers={'political_power_cost':-.025}),
]
# Scale only beneficial native modifiers while a decision is running. The
# independent permanent table, education gains and completion extras are not inputs.
LOWER_IS_BETTER = {
 'political_power_cost','consumer_goods_factor','political_advisor_cost_factor',
 'resistance_growth_on_our_occupied_states','conversion_cost_civ_to_mil_factor',
 'conversion_cost_mil_to_civ_factor','production_lack_of_resource_penalty_factor',
 'supply_consumption_factor','experience_loss_factor','training_time_army_factor',
}
TEMPORARY_BENEFIT_MULTIPLIERS = {
 'industrial_capacity_factory':4, 'industrial_capacity_dockyard':4,
 'production_factory_start_efficiency_factor':4,
 'production_factory_efficiency_gain_factor':4,
 'production_factory_max_efficiency_factor':4,
 'political_power_cost':4, 'political_power_factor':3,
 'stability_factor':2.5, 'stability_weekly':5, 'war_support_factor':2.5,
 'political_advisor_cost_factor':2.5, 'consumer_goods_factor':2.5,
 'conversion_cost_civ_to_mil_factor':2.5, 'conversion_cost_mil_to_civ_factor':2.5,
 'production_speed_rail_way_factor':2.5, 'production_speed_infrastructure_factor':2.5,
 'production_speed_bunker_factor':2.5, 'equipment_conversion_speed':2.5,
 'training_time_army_factor':2.5, 'resistance_growth_on_our_occupied_states':2.5,
}
for activity in ACTIVITIES+CONTROLS:
    activity['base_temporary_modifiers']=dict(activity['modifiers'])
    for modifier,value in activity['base_temporary_modifiers'].items():
        if (-value if modifier in LOWER_IS_BETTER else value)<=0:continue
        factor=TEMPORARY_BENEFIT_MULTIPLIERS.get(modifier,3)
        if modifier=='research_speed_factor':factor=5 if value<=.01 else 2.5
        activity['modifiers'][modifier]=round(value*factor,12)
from education_permanent_rewards import PERMANENT_REWARDS
for activity in ACTIVITIES+CONTROLS:
    # Keep published permanent awards, without converting the new costs or
    # additional temporary effects into permanent changes.
    activity['permanent_modifiers']=dict(PERMANENT_REWARDS.get(activity['id'],{}))
POOL_CAPS = {'industrial_capacity_factory':.10,'stability_factor':.15,'political_power_cost':-.2,'political_power_factor':.10,'research_speed_factor':.05}
# lower endpoint, upper endpoint, weight of basic education (remaining weight = higher)
BODY = {
 'research_speed_factor':(-.10,.15,.25),
 'production_factory_start_efficiency_factor':(-.15,.10,.75),
 'production_factory_efficiency_gain_factor':(-.20,.125,.60),
 'political_power_factor':(-.10,0,.50),
 'global_building_slots_factor':(-.20,.10,.80),
 'production_speed_buildings_factor':(-.05,0,.70),
 'consumer_goods_factor':(.15,0,.70),
 'conscription_factor':(-.15,.10,.85),
}

def education_focuses():
    rows = [
      ('205','共产主义教育理念',[],['custom_effect_tooltip = RUS_edu_unlock_basic_tt','hidden_effect = { RUS_education_initialize = yes }'],
       '革命打开了通往新社会的大门，却不能凭一道命令扫除旧时代留下的无知。识字班、乡村学校与工人夜校必须成为公共事业，让劳动群众能够理解自己的权利，掌握建设共和国的知识。'),
      ('210','对文化革命',['has_completed_focus = RUS_future_domestic_205'],['custom_effect_tooltip = RUS_edu_unlock_culture_tt','hidden_effect = { set_country_flag = RUS_edu_culture_open RUS_education_refresh = yes }'],
       '学校之外，报刊、俱乐部、图书室和剧场也应当向劳动群众敞开。文化事业的扩大不能只靠热烈的口号，还需要教师、教材和能够容纳新学员的课堂。'),
      ('212','专业技能培训',['has_completed_focus = RUS_future_domestic_205'],['custom_effect_tooltip = RUS_edu_unlock_technical_tt','hidden_effect = { set_country_flag = RUS_edu_technical_open RUS_education_refresh = yes }'],
       '机器不会因为主人的更换而自行运转，土地也不会仅凭热情提高产量。将工厂里的经验、农庄中的实践与学校的教学结合起来，才能使劳动者真正掌握现代生产。'),
      ('218','理论指导优先',gate(3,30,0),['custom_effect_tooltip = RUS_edu_theory_tt','hidden_effect = { set_country_flag = RUS_edu_theory RUS_education_refresh = yes }'],
       '零散经验能够解决眼前的问题，却不足以解释复杂的社会与自然。我们应当扶持系统研究，使高等学校和研究机关成为新社会的知识源泉。'),
      ('221','实践价值导向',gate(3,30,0),['custom_effect_tooltip = RUS_edu_practice_tt','hidden_effect = { set_country_flag = RUS_edu_practice RUS_education_refresh = yes }'],
       '教育首先应当使人能够在自己的生活和劳动中有所作为。课堂必须回答村庄与车间提出的问题，让识字、算术和实际技能扎根于群众日常的经验。'),
      ('224','集中宣传供给',gate(6,45,15),['custom_effect_tooltip = RUS_edu_central_tt','hidden_effect = { set_country_flag = RUS_edu_central RUS_education_refresh = yes }'],
       '各地分散编写的教材与宣传品难免质量不一。集中组织印刷、发行与讲习，可以使有限的纸张和师资送到更需要它们的地方，也让共和国的声音传得更远。'),
      ('226','鼓励业余创作',gate(6,45,15),['custom_effect_tooltip = RUS_edu_amateur_tt','hidden_effect = { set_country_flag = RUS_edu_amateur RUS_education_refresh = yes }'],
       '工人俱乐部的剧本、乡村读书会的刊物和青年人的画作，不应只等待上级批准才获得生命。让群众参与知识与文化的创造，教育才能成为他们自己的事业。'),
      ('229','"现在"',gate(9,60,25),['custom_effect_tooltip = RUS_edu_now_tt','add_timed_idea = { idea = RUS_education_present_drive days = 180 }','hidden_effect = { add_to_variable = { RUS_basic_education_level = 8 } add_to_variable = { RUS_higher_education_level = 3 } add_to_variable = { RUS_education_enthusiasm = 10 } RUS_education_refresh = yes }'],
       '共和国不能永远等待一个遥远而完美的明天。将已经积累的师资、技术与组织力量投入当前的建设，让教育的成果尽早走进车间与田野。'),
      ('231','“将来”',gate(9,60,25),['custom_effect_tooltip = RUS_edu_future_tt','hidden_effect = { set_country_flag = RUS_edu_future RUS_education_refresh = yes }'],
       '今日播下的种子未必能由今日的人收获。我们仍须为后来的劳动者留下更完备的大学、实验室和研究传统，让共和国不因眼前的需要而耗尽长远的力量。'),
    ]
    result={i:dict(name=n,cost=5,mode='manual',available=a,reward=r,description=d) for i,n,a,r,d in rows}
    from pathlib import Path
    import json
    source=json.loads((Path(__file__).parent/'design/RUS_education_focus_update_20261024.json').read_text(encoding='utf-8'))
    for suffix,spec in source['focuses'].items():
        if suffix not in result:
            result[suffix]=dict(name=spec['name'],cost=5,mode='manual',available=[],reward=[])
        assert result[suffix]['name']==spec['name']
        result[suffix]['description']=spec['description']
    result['224']['reward'].append('custom_effect_tooltip = RUS_edu_repeat_campaign_tt')
    result['226']['reward'] += ['custom_effect_tooltip = RUS_edu_half_cost_tt',
        'effect_tooltip = { add_timed_idea = { idea = RUS_education_mass_hesitation days = 180 } }',
        'custom_effect_tooltip = RUS_edu_mass_transition_tt',
        'effect_tooltip = { add_timed_idea = { idea = RUS_education_mass_enthusiasm days = 360 } }',
        'hidden_effect = { RUS_education_start_mass_campaign = yes }']
    result['233']['reward'].append('add_research_slot = 1')
    result['234']['reward'] += ['custom_effect_tooltip = RUS_edu_era_cost_tt',
        'hidden_effect = { set_country_flag = RUS_edu_era RUS_education_refresh = yes }']
    return result

def gate(count,basic,higher):
    rows=[f'NOT = {{ check_variable = {{ RUS_education_completed_activities < {count} }} }}', f'NOT = {{ check_variable = {{ RUS_basic_education_level < {basic} }} }}']
    if higher: rows.append(f'NOT = {{ check_variable = {{ RUS_higher_education_level < {higher} }} }}')
    return rows
