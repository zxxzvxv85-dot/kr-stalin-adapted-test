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
# id, slogan, category, duration, PP, total base/higher gain, enthusiasm per 30 days, poster code, temporary modifiers
ROWS = [
 ('literacy','知识打破奴隶的锁链！','basic',90,25,5,0,0,'EDU02',{'research_speed_factor':.01}),
 ('schools','让每一个村庄都有学校！','basic',120,40,7,0,-.5,'EDU01',{'stability_factor':.025,'consumer_goods_factor':.01}),
 ('night_school','工农群众，拿起书本！','basic',90,30,4,1,.5,'EDU66',{'industrial_capacity_factory':.025}),
 ('teachers','为人民培养人民教师！','basic',120,40,4,2,0,'WOM16',{'political_power_cost':-.05}),
 ('university','工农群众，走进大学！','higher',120,45,1,6,.5,'EDU42',{'research_speed_factor':.025,'consumer_goods_factor':.01}),
 ('science','科学必须服务于人民！','higher',180,55,0,9,0,'EDU56',{'research_speed_factor':.025}),
 ('pedagogy','培养建设新社会的师资！','higher',120,45,3,5,0,'EDU68',{'political_power_factor':.025}),
 ('technical','掌握技术，建设社会主义！','technical',90,35,1,2,1,'EDU30',{'industrial_capacity_factory':.03}),
 ('agriculture','把科学带到田野！','technical',90,30,2,1,1,'YTH03',{'industrial_capacity_factory':.025}),
 ('reading','让书籍走进千家万户！','culture',90,20,.5,.5,2,'EDU13',{'political_power_factor':.05}),
 ('outreach','把文化带到田野和车间！','culture',90,25,.5,0,3,'EDU44',{'stability_factor':.025}),
 ('construction','用劳动建设我们的新生活！','culture',90,25,0,0,4,'IND07',{'industrial_capacity_factory':.05}),
 ('mentoring','老工人，扶青年一把！','technical',90,30,1,2,1,'YTH06',{'industrial_capacity_factory':.025,'political_power_cost':-.05}),
 ('library','让每个工人俱乐部都有图书室！','culture',120,30,2,1,1,'EDU07',{'research_speed_factor':.01,'stability_factor':.025}),
]
ACTIVITIES = [dict(zip(('id','name','kind','days','cost','basic','higher','heat','poster','modifiers'), row)) for row in ROWS]
for activity in ACTIVITIES:
    prefix = ''.join(c for c in activity['poster'] if c.isalpha())
    activity['category'] = POSTER_PREFIX_CATEGORY[prefix]
from education_poster_expansion import additional_activities
ACTIVITIES += additional_activities()
CONTROLS = [
 dict(id='listen',name='听取群众的声音！',kind='control',days=30,cost=20,basic=0,higher=0,heat=10,modifiers={'political_power_cost':-.025}),
 dict(id='restore_order',name='让课堂与车间恢复秩序！',kind='control',days=30,cost=20,basic=0,higher=0,heat=-12,modifiers={'political_power_cost':-.025}),
]
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
      ('229','"现在"',gate(10,60,25),['custom_effect_tooltip = RUS_edu_now_tt','add_timed_idea = { idea = RUS_education_present_drive days = 180 }','hidden_effect = { add_to_variable = { RUS_basic_education_level = 8 } add_to_variable = { RUS_higher_education_level = 3 } add_to_variable = { RUS_education_enthusiasm = 10 } RUS_education_refresh = yes }'],
       '共和国不能永远等待一个遥远而完美的明天。将已经积累的师资、技术与组织力量投入当前的建设，让教育的成果尽早走进车间与田野。'),
      ('231','“将来”',gate(10,60,25),['custom_effect_tooltip = RUS_edu_future_tt','hidden_effect = { set_country_flag = RUS_edu_future RUS_education_refresh = yes }'],
       '今日播下的种子未必能由今日的人收获。我们仍须为后来的劳动者留下更完备的大学、实验室和研究传统，让共和国不因眼前的需要而耗尽长远的力量。'),
    ]
    return {i:dict(name=n,cost=5,mode='manual',available=a,reward=r,description=d) for i,n,a,r,d in rows}

def gate(count,basic,higher):
    rows=[f'NOT = {{ check_variable = {{ RUS_education_completed_activities < {count} }} }}', f'NOT = {{ check_variable = {{ RUS_basic_education_level < {basic} }} }}']
    if higher: rows.append(f'NOT = {{ check_variable = {{ RUS_higher_education_level < {higher} }} }}')
    return rows
