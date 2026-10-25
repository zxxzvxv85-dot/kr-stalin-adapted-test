"""Additional poster campaigns requested on 2026-10-24. Pure authoring data."""

MILITARY_GATE = 'has_country_flag = RUS_fr_basic_reform_completed'
FINAL_STRUGGLE_GATE = 'has_completed_focus = RUS_future_foreign_062'
VICTORY_GATE = 'has_completed_focus = RUS_future_foreign_005'
AGRICULTURE_GATE = 'has_country_flag = RUS_nat_enabled NOT = { has_country_flag = RUS_nat_system_closed }'

# National campaign modifiers apply only during the activity, with a cost.
# State rewards last a fixed period and only apply while the state remains
# owned and controlled by socialist Russia. They never grant factories outright.
STATE_REWARDS = {
 'city_defence': ('城市防卫动员', {'local_org_regain':.20, 'state_production_speed_buildings_factor':.05}),
 'industrial_training': ('工业建设宣传', {'local_building_slots_factor':.10, 'state_production_speed_buildings_factor':.05}),
 'electrification': ('电气化建设动员', {'state_production_speed_buildings_factor':.10, 'local_resources_factor':.05}),
 'reconstruction': ('解放地区重建', {'state_production_speed_buildings_factor':.15, 'local_building_slots_factor':.05}),
}
CATEGORY_ICONS = {
 1:'GFX_decision_generic_military', 2:'GFX_decision_generic_industry',
 3:'GFX_decision_generic_civil_support', 4:'GFX_RUS_edu_basic_texticon',
 5:'GFX_decision_generic_police_action', 6:'GFX_decision_peace_dove',
}

# id, slogan, display category, parallel kind, days, PP, basic/higher, heat/30d,
# source poster, temporary national modifiers.
NEW_ROWS = [
 ('defend_leningrad','保卫列宁格勒！',1,'military',60,35,1,0,4,'C15',{'army_defence_factor':.05,'production_speed_bunker_factor':.10,'stability_factor':.01}),
 ('defend_moscow','保卫莫斯科！',1,'military',60,35,1,0,4,'C49',{'army_defence_factor':.05,'production_speed_bunker_factor':.10,'stability_factor':.01}),
 ('march_west','向西进军！',1,'military',60,40,0,1,5,'C64',{'army_attack_factor':.05,'planning_speed':.10,'political_power_factor':.025}),
 ('defend_october','十月革命的成果，绝不放弃！',1,'military',90,35,1,0,4,'C40',{'war_support_factor':.075,'stability_factor':.025}),
 ('dnieper_water','饮到亲爱的第聂伯河水！',1,'military',90,40,1,1,3,'C51',{'army_morale_factor':.05,'stability_factor':.025}),
 ('await_victory','等待我们胜利归来！',1,'military',90,30,1,0,2,'V03',{'experience_loss_factor':-.05,'stability_factor':.025}),
 ('advanced_theory','在先进理论指引下发挥先锋作用！',4,'higher',120,45,1,2,1,'C57',{'research_speed_factor':.025,'political_power_factor':.025}),
 ('cultural_enemies','打击文化革命的敌人！',4,'culture',90,30,1,1,3,'C56',{'resistance_growth_on_our_occupied_states':-.10,'political_power_factor':.025}),
 ('mothers_literacy','孩子不识字是母亲的耻辱',4,'basic',120,30,4,0,-.5,'WOM10',{'monthly_population':.05,'stability_factor':.015}),
 ('children_workers','让儿童融入劳动者的生活',4,'basic',120,30,4,1,0,'EDU03',{'monthly_population':.05,'political_power_cost':-.025}),
 ('ten_days','每个人都应了解震撼世界的十天！',4,'culture',90,25,1,1,2,'EDU04',{'drift_defence_factor':.10,'political_power_factor':.025}),
 ('book_fair','大家都到书市来！',4,'culture',90,25,2,1,1,'EDU07',{'stability_weekly':.0005,'research_speed_factor':.01,'political_power_cost':-.025}),
 ('grain_delivery','按时完成国家粮食交售计划！',3,'culture',90,30,1,0,2,'AGR10',{'stability_factor':.025,'political_power_cost':-.025}),
 ('end_kitchen_slavery','打倒厨房奴役，建设新生活！',3,'culture',120,35,2,1,1,'WOM03',{'consumer_goods_factor':-.025,'industrial_capacity_factory':.015}),
 ('soviet_elections','无产阶级队伍，参加苏维埃选举！',3,'culture',90,25,1,0,2,'CIV01',{'political_advisor_cost_factor':-.10,'political_power_factor':.025}),
 ('protect_children','宗教是毒药，保护儿童！',3,'basic',90,25,3,0,1,'ANT02',{'drift_defence_factor':.10,'research_speed_factor':.01}),
 ('lenin_banner','在列宁的旗帜下前进！',3,'culture',90,30,1,0,3,'CIV06',{'mobilization_speed':.10,'political_power_factor':.025}),
 ('labour_productivity','提高劳动生产率！',2,'technical',90,35,1,2,2,'IND04',{'production_factory_max_efficiency_factor':.025,'industrial_capacity_factory':.025}),
 ('socialist_industry','建设社会主义工业！',2,'technical',120,45,1,2,2,'IND03',{'conversion_cost_civ_to_mil_factor':-.10,'industrial_capacity_factory':.025}),
 ('lenin_electrification','列宁与电气化！',2,'technical',120,45,1,2,1,'IND11',{'production_speed_rail_way_factor':.10,'production_speed_infrastructure_factor':.10,'industrial_capacity_factory':.015}),
 ('tractors_nurseries','拖拉机与托儿所！',2,'technical',120,35,2,1,1,'AGR03',{'equipment_conversion_speed':.05,'consumer_goods_factor':-.015,'stability_factor':.015}),
 ('agricultural_statistics','社会主义农业建设的数据',2,'technical',120,35,1,2,0,'AGR02',{'production_lack_of_resource_penalty_factor':-.05,'research_speed_factor':.015}),
 ('complete_collectivisation','把集体化进行到底！',2,'technical',120,40,2,1,3,'AGR04',{'consumer_goods_factor':-.025,'political_power_factor':.025}),
 ('harvest_battle','为丰收而斗争！',2,'technical',90,30,2,1,2,'AGR06',{'supply_consumption_factor':-.025,'stability_factor':.025}),
 ('vigilance','敌人狡诈，提高警惕！',5,'culture',90,25,1,0,1,'C85',{'enemy_operative_detection_chance_factor':.10,'resistance_growth_on_our_occupied_states':-.05,'stability_factor':.01}),
 ('production_vices','打击危害生产的恶习！',5,'culture',90,30,1,1,-1,'EDU18',{'production_lack_of_resource_penalty_factor':-.05,'industrial_capacity_factory':.025}),
 ('public_property','无情打击侵吞公共财产者',5,'culture',90,30,1,0,1,'EDU22',{'political_advisor_cost_factor':-.10,'political_power_cost':-.05}),
 ('false_shock_workers','打击假突击手！',5,'technical',90,30,1,1,-1,'EDU23',{'production_factory_max_efficiency_factor':.025,'production_factory_efficiency_gain_factor':.025,'industrial_capacity_factory':.015}),
 ('motherland_calls','祖国母亲在召唤！',1,'military',90,35,1,0,3,'R01',{'mobilization_speed':.10,'conscription_factor':.05,'stability_factor':.01}),
 ('volunteer_enlistment','你报名参军了吗？',1,'military',90,30,1,0,2,'R02',{'training_time_army_factor':-.10,'political_power_factor':.025}),
 ('red_banner_oath','红旗之下的庄严誓言！',1,'military',90,30,1,0,2,'R04',{'experience_loss_factor':-.10,'army_morale_factor':.025,'stability_factor':.015}),
 ('women_frontline','一切为了胜利，苏联妇女支援前线！',1,'military',90,35,1,1,2,'C11',{'conversion_cost_civ_to_mil_factor':-.15,'industrial_capacity_dockyard':.05,'industrial_capacity_factory':.025}),
 ('people_and_army','人民与军队不可战胜！',1,'military',90,35,1,0,3,'C14',{'supply_consumption_factor':-.05,'army_org_factor':.025,'stability_factor':.01}),
 ('honour_freedom','为了祖国、荣誉与自由！',1,'military',90,35,1,0,3,'C27',{'max_planning_factor':.05,'army_defence_factor':.025,'political_power_factor':.025}),
 ('ukrainian_liberators','光荣属于乌克兰的解放者',6,'culture',120,40,1,1,1,'V01',{'resistance_growth_on_our_occupied_states':-.10,'stability_factor':.025}),
 ('beloved_motherland','光荣属于我们亲爱的祖国',6,'culture',120,35,1,1,1,'V04',{'production_speed_infrastructure_factor':.05,'stability_factor':.025,'war_support_factor':.025}),
 ('long_live_peace','和平万岁！',6,'culture',120,35,1,2,-1,'CIV16',{'conversion_cost_mil_to_civ_factor':-.15,'consumer_goods_factor':-.025,'stability_factor':.025}),
]

def additional_activities():
    keys=('id','name','category','kind','days','cost','basic','higher','heat','poster','modifiers')
    rows=[dict(zip(keys,row)) for row in NEW_ROWS]
    for i,a in enumerate(rows):
        if i<6:a.update(gate=FINAL_STRUGGLE_GATE,wartime=True)
        elif a['category']==1:a['gate']=MILITARY_GATE
        elif a['category']==6:a['gate']=VICTORY_GATE
    by_id={a['id']:a for a in rows}
    for aid,state,preset,days in [
        ('defend_leningrad',195,'city_defence',180),('defend_moscow',219,'city_defence',180),
        ('socialist_industry',219,'industrial_training',365),
        ('lenin_electrification',195,'electrification',365),('ukrainian_liberators',202,'reconstruction',365),
    ]:by_id[aid]['state_reward']={'state':state,'preset':preset,'days':days}
    by_id['dnieper_water']['timed_reward']={'idea':'RUS_edu_dnieper_offensive','name':'第聂伯河攻势',
        'target':'UKR','attack':.05,'days':30}
    for aid,bonus in [('grain_delivery','wheat'),('tractors_nurseries','repair'),('agricultural_statistics','technical'),('harvest_battle','rye')]:
        by_id[aid]['agriculture_reward']=bonus
    return rows
