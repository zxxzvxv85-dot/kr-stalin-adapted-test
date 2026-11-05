"""Opt-in Easter egg advisers; text-only, read-only by default.

Native references: KR RUS political adviser slots, available_political_advisor
and show_ideas_tooltip; native recruit_character; existing KR portrait template.
"""
import json
from pathlib import Path
from generation_io import cli

ROOT=Path(__file__).resolve().parents[1]
ADVISORS={
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
      'RUS_easter_eggs_category_desc':'特别来客与不同寻常的选择。',
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
        traits.append(block(trait,['random = no','sprite = 1',
            *[str(k)+' = '+str(v) for k,v in data['modifiers'].items()],
            *(['custom_modifier_tooltip = RUS_egg_guaranteed_minesweeper_tt'] if key=='larruping' else []),
            *(['custom_modifier_tooltip = RUS_egg_guaranteed_doudizhu_tt'] if key=='larruping' else []),
            *(['custom_modifier_tooltip = RUS_egg_mia_trait_tt'] if key=='mia' else []),
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
          'visible = { is_ai = no }','visible_when_empty = no']),
      'common/scripted_effects/RUS_easter_egg_advisor_effects.txt':''.join(effects),
      'interface/RUS_easter_egg_advisors.gfx':block('spriteTypes',sprites),
      'common/dynamic_modifiers/RUS_easter_egg_modifiers.txt':
          '# Tooltip only; actual reward is part of RUS_education_social_capacity.\n'+
          block('RUS_edu_mia_reward_preview',['research_speed_factor = 0.05']),
      'common/on_actions/RUS_easter_egg_on_actions.txt':block('on_actions',[
          'on_monthly = { effect = { RUS_egg_mia_monthly = yes } }']),
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
    for language in ('simp_chinese','english','russian'):
        outputs[f'localisation/{language}/RUS_easter_egg_advisors_l_{language}.yml']='l_'+language+':\n'+''.join(' '+k+':0 '+json.dumps(v,ensure_ascii=False)+'\n' for k,v in loc.items())
    return {rel:'\n'.join(line.rstrip() for line in text.split('\n')) for rel,text in outputs.items()}

if __name__=='__main__':cli(render_outputs,root=ROOT,description='Generate opt-in Easter egg advisers')
