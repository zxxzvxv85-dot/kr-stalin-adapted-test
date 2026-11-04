"""Opt-in Easter egg advisers; text-only, read-only by default.

Native references: KR RUS political adviser slots, available_political_advisor
and show_ideas_tooltip; native recruit_character; existing KR portrait template.
"""
import json
from pathlib import Path
from generation_io import cli

ROOT=Path(__file__).resolve().parents[1]
ADVISORS={
 'su_beichen':dict(name='苏北辰',trait='制作组最锋利的剑',
     modifiers={'army_attack_factor':.20,'combat_width_factor':-.20,
                'supply_consumption_factor':-.20,'army_org_factor':.20}),
 'larruping':dict(name='larruping',trait='扫雷先驱',modifiers={},desc=(
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
    }
    for key,data in ADVISORS.items():
        ident=token(key);idea=ident+'_advisor';flag=ident+'_unlocked';trait=ident+'_trait'
        characters.append(block(ident,[
            'name = '+ident,
            'portraits = { civilian = { small = GFX_portrait_'+ident+'_small } }',
            block('advisor',[
                'slot = political_advisor','idea_token = '+idea,'desc = '+idea+'_desc',
                'visible = { has_country_flag = '+flag+' }',
                'available = { has_country_flag = '+flag+' not_already_hired_except_as = political_advisor }',
                'traits = { '+trait+' }','cost = 0','can_be_fired = yes','ai_will_do = { base = 0 }']).strip()]))
        traits.append(block(trait,['random = no','sprite = 1',
            *[str(k)+' = '+str(v) for k,v in data['modifiers'].items()],
            *(['custom_modifier_tooltip = RUS_egg_guaranteed_minesweeper_tt'] if key=='larruping' else []),
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
    }
    for language in ('simp_chinese','english','russian'):
        outputs[f'localisation/{language}/RUS_easter_egg_advisors_l_{language}.yml']='l_'+language+':\n'+''.join(' '+k+':0 '+json.dumps(v,ensure_ascii=False)+'\n' for k,v in loc.items())
    return {rel:'\n'.join(line.rstrip() for line in text.split('\n')) for rel,text in outputs.items()}

if __name__=='__main__':cli(render_outputs,root=ROOT,description='Generate opt-in Easter egg advisers')
