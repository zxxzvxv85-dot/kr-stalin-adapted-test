"""Opt-in Easter egg advisers; text-only, read-only by default.

Native references: KR RUS political adviser slots, available_political_advisor
and show_ideas_tooltip; native recruit_character; existing KR portrait template.
"""
import json
from pathlib import Path
from generation_io import cli

ROOT=Path(__file__).resolve().parents[1]
ADVISORS={
 'hongying':dict(name='今日红缨在手',trait='远视极权自动化未来平权主义',
     modifiers={'consumer_goods_factor':-1,'political_power_factor':2,
                'production_speed_buildings_factor':5},desc=(
     '背景：红缨的意识形态恐怕是近年来最值得研究的话题，他通常不被认为是正经的或是传统的革命者，如果说他是左派，他对自由意志的无限制打压会显得他像个保皇派，如果说他是右派，那么他对布尔什维克的政策又十分的推崇。'
     '\n\n一个倾向于平等的极权主义者——或许这么说可能会比较合适，他还认为只要让AI哲人王掌管一切经济事务，所有事情都会变得好起来。'
     '\n\n在组内，他也更倾向于快乐一些，虽然有时负面情绪会溢出来，但这微不足道。'
     '\n\n要喜剧，不要悲剧，为了让所有事物都走向Happy End。'
     '\n\n为了世界上所有美好而战——这人是个米卫兵')),
 'suyi':dict(name='Suyi',trait='概率学博士',modifiers={},desc=(
     '背景：Suyi的mod制作历程可谓成效显著，仅用数周时间，便凭借独具风格的文案撰写和策划运营，完成了从普通群友到核心组员的跨越式转变——这一转变并非偶然，既源于其在文案撰写和策划运营方面的持续积累，也与其温和稳重的做事风格密切相关。'
     '\n\n尽管Suyi在群内仍习惯以“季伯常”自居，但其工作热情仍感染着每一位组员。'
     '\n\n“有理想的人，生活总是火热的。”')),
 'xin':dict(name='心',trait='自刎归天',modifiers={'org_loss_at_low_org_factor':-1},desc=(
     '背景：某种意义上来讲，牢心可能是制作组成分最复杂的人，在作为群友的早年生活中，他有时跳出来发表一些长篇大论，有时又会在长时间内陷入沉寂；不仅如此，牢心的还乐于在mod群里搬花样繁多的史，从科幻FPS对局到神笔历史小故事应有尽有，他自己美其名曰分享美食。尽管他的史经常0个人在意，但他依然乐此不疲。'
     '\n\n作为制作组新加入的成员之一，曾经的他对mod制作望而却步。直到某一天他下载了那个震撼的多么多么的多么mod——承蒙多么多么mod组的伟力，他被让KR红俄再次伟大的理想所感召，完成了从见证别人做mod到自己参与做mod的转变。为了达成这个伟大理想，无论付出何种代价都在所不惜，哪怕让群聊燃烧，让飞书陨落........')),
 'mia':dict(name='米娅',trait='最强菜花蛇',modifiers={},desc=(
     '背景：米娅，一个简简单单的假名，浓缩了相当多的意义——友人称之为爱称，敌人则认为是撒旦般可憎的代名词。她向来被冠以许多称号，却都不能够充分的代表她。只有一件事情能够为多数人所肯定——她肯定任职着相当重要的位置，同larruping一般使用奶蛙作为代表图案，更是为这一事情提供了证据。'
     '\n\n米娅在何时何地进行过活动，也许连她的友人也无法得知。大多数时候，递交给米娅的文件都会在第二天以批注完毕的形式交付回来，这无疑为她增添了些许神秘色彩。随着奶蛙图案和过夜出现的批注文件越来越多，米娅也逐渐浮现在人们的视野中，可她究竟是谁？性别为何？这些问题仍留在黑暗之中。'
     '\n\n随着米娅的出现越来越突然，间隔也越来越久，不少人都认为她正在执行一个从所未有的任务，而更多的人只认为她已经死去，只留下米娅这个代称。不管怎么样，米娅都将在大众心里留下符号，不管是以什么样的色彩。')),
 'su_beichen':dict(name='苏北辰',trait='制作组最锋利的剑',
     modifiers={'army_attack_factor':.20,'combat_width_factor':-.20,
                'supply_consumption_factor':-.20,'army_org_factor':.20},desc=(
     '背景：该如何形容苏北辰，这位制作组最锋利的剑？他向来被冠以许多称号：愤怒者——只要被某些事情气红温就会产出优质文案；整活运动的实际领导者；毫无骨气的享乐主义者，沉迷于战争雷霆；组长larruping最早、最忠实的追随者。总而言之，他是个极端的人，对于所爱之物，他痛快地耍起；对于所恨之事，他放肆地耍起。'
     '\n\n事实上，关于苏北辰的种种神秘事迹很大程度上要归功于他的神人言论，或是那些和他一同加入制作组的组员。苏北辰从哪里来，0个人知道，直到组长的适配版震撼发布，他迷恋上了mod——他走上了做mod的道路，也走向了做mod的极端：经过很久攻击社革、攻击社革、攻击社革的道路，最终一步步走向了制作组。他摇身一变，从一名评论区鬣狗变成了一名制作组组员。他们将不惜一切代价，用鲜血铸就一条KR共产主义复兴之路。')),
 'larruping':dict(name='larruping',trait='赌徒',modifiers={},desc=(
     '背景：该如何形容larruping，这位制作组的组长？他向来被冠以许多称号：反动派，因为他mod里越来越弱的俄罗斯和苏联；享乐主义者、沉迷斗地主的赌徒和好色之徒，自以为肩负着某种伟大使命，还喜欢发唐得没边的奶蛙表情包。总而言之，他是个整活的人，对于所爱之物，他不离不弃地整活；对于所恨之事，他深恶痛绝地整活。'
     '\n\n'
     '事实上，关于larruping的种种神话很大程度上要归功于他的mod，或是那些受他启发的狂热玩家。larruping在遥远的东方长大成人，正是在那里，他迷恋上了做mod——他走上了做mod的道路，也走向了逻辑的极端：经过多年整活主义和bug的洗礼，最终一步步成立了多么多么的制作组。他摇身一变，从一名为爱发电的玩家变成了一位制作组的领导人。mod发布后，许多人随他加入了制作组——这是一个为KR布尔什维克拨乱反正的组织，他们将不惜一切代价，铸就一条KR共产主义的复兴之路。')),
}

def block(key,lines):return key+' = {\n'+''.join('\t'+s+'\n' for s in lines)+'}\n'
def token(key):return 'RUS_egg_'+key

def render_outputs():
    characters=[];traits=[];decisions=[];effects=[];sprites=[]
    loc={
      'RUS_easter_eggs_category':'彩蛋',
      'RUS_easter_eggs_category_desc':'特别来客与不同寻常的选择。\n\n[ROOT.GetRUSEggSuyiCurrentPP]',
      'RUS_egg_guaranteed_minesweeper_tt':'扫雷小游戏无论胜负，均按成功结算。',
      'RUS_egg_guaranteed_doudizhu_tt':'每局斗地主必定获得§G四张2和大小王§!。',
      'RUS_egg_mia_trait_tt':'每月土改分数：§G+100§!（土改启用后）\n任命期间，每完成一次教育改革决议，“教育改革”永久追加科研速度：§G+5.00%§!。',
      'RUS_edu_mia_reward_preview':'教育改革',
    }
    for key,data in ADVISORS.items():
        ident=token(key);idea=ident+'_advisor';flag=ident+'_unlocked';trait=ident+'_trait'
        characters.append(block(ident,[
            'name = '+ident,
            'portraits = { civilian = { small = GFX_portrait_'+ident+'_small } }',
            block('advisor',[
                'slot = political_advisor','idea_token = '+idea,'desc = '+idea+'_desc',
                'visible = { has_country_flag = '+flag+' }',
                'available = { hidden_trigger = { has_country_flag = '+flag+' } not_already_hired_except_as = political_advisor }',
                'traits = { '+trait+' }','cost = 0','can_be_fired = yes','ai_will_do = { base = 0 }']).strip()]))
        if key=='suyi':
            characters[-1]=characters[-1].replace('cost = 0',
                'on_add = { hidden_effect = { RUS_egg_suyi_appoint = yes } }\n\ton_remove = { hidden_effect = { clr_country_flag = RUS_egg_suyi_active remove_dynamic_modifier = { modifier = RUS_egg_suyi_daily_pp } force_update_dynamic_modifier = yes } }\n\tcost = 0')
        traits.append(block(trait,['random = no','sprite = 1',
            *[str(k)+' = '+str(v) for k,v in data['modifiers'].items()],
            *(['custom_modifier_tooltip = RUS_egg_guaranteed_minesweeper_tt'] if key=='larruping' else []),
            *(['custom_modifier_tooltip = RUS_egg_guaranteed_doudizhu_tt'] if key=='larruping' else []),
            *(['custom_modifier_tooltip = RUS_egg_mia_trait_tt'] if key=='mia' else []),
            *(['custom_modifier_tooltip = RUS_egg_suyi_trait_tt'] if key=='suyi' else []),
            'ai_will_do = { factor = 0 }']))
        effects.append(block(ident+'_unlock',[
            'if = { limit = { original_tag = RUS is_ai = no NOT = { has_country_flag = '+flag+' } }',
            'set_country_flag = '+flag,
            'if = { limit = { NOT = { has_character = '+ident+' } } recruit_character = '+ident+' }','}']))
        decisions.append(block(ident+'_recruit',[
            'icon = generic_political_discourse','allowed = { original_tag = RUS }',
            'visible = { is_ai = no NOT = { has_country_flag = '+flag+' } }',
            'available = { hidden_trigger = { NOT = { has_country_flag = '+flag+' } } }',
            'on_map_mode = decision_view_only','cost = 0','fire_only_once = yes',
            'complete_effect = { custom_effect_tooltip = available_political_advisor show_ideas_tooltip = '+idea+' hidden_effect = { '+ident+'_unlock = yes } }',
            'ai_will_do = { factor = 0 }']))
        sprites.append(block('spriteType',[
            'name = "GFX_portrait_'+ident+'_small"',
            'texturefile = "gfx/interface/advisors/RUS/RUS_'+key+'.png"']))
        loc[ident]=data['name'];loc[idea]=data['name'];loc[trait]=data['trait']
        loc[idea+'_desc']=data.get('desc','来自制作组的彩蛋顾问。')
        if data.get('desc'):
            # Match KR's RUS_alisa_berkova_advisor_desc biography styling.
            loc[idea+'_desc']='§Y背景：§!§L'+data['desc'].removeprefix('背景：')+'§!'
        loc[ident+'_recruit']='邀请'+data['name']
        loc[ident+'_recruit_desc']='解锁彩蛋顾问'+data['name']+'。解锁后可在政治顾问栏任命。'
    outputs={
      'common/characters/RUS_easter_egg_advisors.txt':block('characters',characters),
      'common/country_leader/RUS_easter_egg_advisor_traits.txt':block('leader_traits',traits),
      'common/decisions/RUS_easter_egg_advisors.txt':block('RUS_easter_eggs_category',decisions),
      'common/decisions/categories/RUS_easter_egg_categories.txt':block('RUS_easter_eggs_category',[
          'icon = generic_communism','priority = 120','allowed = { original_tag = RUS }',
          'visible = { is_ai = no }','visible_when_empty = yes']),
      'common/scripted_effects/RUS_easter_egg_advisor_effects.txt':''.join(effects),
      'interface/RUS_easter_egg_advisors.gfx':block('spriteTypes',sprites),
      'common/dynamic_modifiers/RUS_easter_egg_modifiers.txt':
          '# Mia preview only; her actual reward is in RUS_education_social_capacity.\n# Suyi below is the live, variable-valued country modifier (no spirit icon).\n'+
          block('RUS_edu_mia_reward_preview',['research_speed_factor = 0.05'])+
          block('RUS_egg_suyi_daily_pp',['enable = { original_tag = RUS is_ai = no has_country_flag = RUS_egg_suyi_active }',
              'political_power_gain = RUS_egg_suyi_pp']),
      'common/on_actions/RUS_easter_egg_on_actions.txt':block('on_actions',[
          'on_monthly = { effect = { RUS_egg_mia_monthly = yes } }',
          'on_daily_RUS = { effect = { RUS_egg_suyi_daily = yes } }']),
    }
    outputs['common/scripted_effects/RUS_easter_egg_advisor_effects.txt']+='''
RUS_egg_mia_education_completed = {
    if = {
        limit = { has_idea = RUS_egg_mia_advisor is_ai = no original_tag = RUS }
        add_to_variable = { RUS_edu_mia_permanent_research = 0.05 }
    }
}
RUS_egg_mia_monthly = {
    if = {
        limit = { has_idea = RUS_egg_mia_advisor is_ai = no original_tag = RUS }
        set_variable = { RUS_agri_score_award = 100 }
        RUS_agri_credit_score = yes
    }
}
'''
    outputs['common/scripted_effects/RUS_easter_egg_advisor_effects.txt']+='''
# Country-local persistent draw: appointing again on the same day reuses it.
RUS_egg_suyi_roll = {
    if = {
        limit = { original_tag = RUS is_ai = no OR = { NOT = { has_country_flag = RUS_egg_suyi_rolled } check_variable = { RUS_egg_suyi_roll_day < global.num_days } } }
        randomize_variable = { var = RUS_egg_suyi_pp distribution = uniform min = -30 max = 30 }
        multiply_variable = { RUS_egg_suyi_pp = 100 }
        round_variable = RUS_egg_suyi_pp
        divide_variable = { RUS_egg_suyi_pp = 100 }
        clamp_variable = { var = RUS_egg_suyi_pp min = -30 max = 30 }
        set_variable = { RUS_egg_suyi_roll_day = global.num_days }
        set_country_flag = RUS_egg_suyi_rolled
    }
}
RUS_egg_suyi_appoint = {
    if = {
        limit = { original_tag = RUS is_ai = no has_country_flag = RUS_egg_suyi_unlocked }
        set_country_flag = RUS_egg_suyi_active
        RUS_egg_suyi_roll = yes
        if = { limit = { NOT = { has_dynamic_modifier = RUS_egg_suyi_daily_pp } } add_dynamic_modifier = { modifier = RUS_egg_suyi_daily_pp } }
        force_update_dynamic_modifier = yes
    }
}
RUS_egg_suyi_daily = {
    if = {
        limit = { original_tag = RUS is_ai = no has_idea = RUS_egg_suyi_advisor }
        RUS_egg_suyi_appoint = yes
    }
    else = {
        clr_country_flag = RUS_egg_suyi_active
        if = { limit = { has_dynamic_modifier = RUS_egg_suyi_daily_pp } remove_dynamic_modifier = { modifier = RUS_egg_suyi_daily_pp } force_update_dynamic_modifier = yes }
    }
}
'''
    outputs['common/scripted_localisation/RUS_easter_egg_advisors_loc.txt']=block('defined_text',[
        'name = GetRUSEggSuyiCurrentPP',
        'text = { trigger = { has_idea = RUS_egg_suyi_advisor has_country_flag = RUS_egg_suyi_rolled } localization_key = RUS_egg_suyi_pp_today }',
        'text = { trigger = { has_country_flag = RUS_egg_suyi_unlocked } localization_key = RUS_egg_suyi_pp_range }',
        'text = { localization_key = RUS_egg_suyi_pp_hidden }'])
    loc.update({
        'RUS_egg_suyi_daily_pp':'概率学博士',
        'RUS_egg_suyi_trait_tt':'$MODIFIER_POLITICAL_POWER_GAIN$：§Y-30.00至+30.00§!（每日随机刷新）',
        'RUS_egg_suyi_pp_today':'§YSuyi§!\n$MODIFIER_POLITICAL_POWER_GAIN$：[?ROOT.RUS_egg_suyi_pp|+=2]\n每日随机刷新：§Y-30.00至+30.00§!。',
        'RUS_egg_suyi_pp_hidden':'',
        'RUS_egg_suyi_pp_range':'§YSuyi§!\n$MODIFIER_POLITICAL_POWER_GAIN$：§Y-30.00至+30.00§!（每日随机刷新）',
    })
    for language in ('simp_chinese','english','russian'):
        outputs[f'localisation/{language}/RUS_easter_egg_advisors_l_{language}.yml']='l_'+language+':\n'+''.join(' '+k+':0 '+json.dumps(v,ensure_ascii=False)+'\n' for k,v in loc.items())
    return {rel:'\n'.join(line.rstrip() for line in text.split('\n')) for rel,text in outputs.items()}

if __name__=='__main__':cli(render_outputs,root=ROOT,description='Generate opt-in Easter egg advisers')
