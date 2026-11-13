"""User-authored Red Army decree; generated alongside the domestic focus tree."""
import json
from pathlib import Path

EVENT_ID = 'RUS_red_army_decree.1'
FLAG = 'RUS_red_army_decree_awarded'
PICTURE = 'GFX_report_event_RUS_red_army_decree'
TEXT = '''[?global.date.GetDateStringNoHourLong]

旧军队曾是资产阶级对劳动者实行阶级压迫的工具。随着政权转归劳动阶级和被剥削阶级，建立一支新军队已成为必要。这支军队应当成为当前社会主义政权的支柱，成为在不久的将来以全民武装代替常备军的基础，并为即将在欧洲到来的社会主义革命提供支持。

一

鉴于上述情况，人民委员会决定：按照以下原则，组建一支名为“工农红军”的新军队。

（1）工农红军由劳动群众中觉悟最高、最有组织性的人员组成。

（2）凡年满十八岁的俄罗斯社会主义联邦共和国公民，均可加入红军。凡愿意献出自己的力量和生命，以保卫革命的成果、政权和社会主义的人，皆可参加红军。

加入红军，须取得部队委员会，或拥护社会主义政权纲领的民主社会团体、党组织和工会组织的推荐，或至少取得上述组织中两名成员的推荐。

整支部队集体加入时，须由全体成员相互担保，并进行记名表决。

二

（1）工农红军军人的全部给养由国家供给，此外每月领取五十卢布。

（2）红军士兵家庭中，原先依靠其供养且无劳动能力的成员，应依照地方政权机关的决定，按照当地的消费标准，获得一切必需的生活资料。

三

工农红军的最高领导机关为军事委员会。对军队的直接领导与管理，集中于军事委员会及其下设的特别全俄委员会。'''

def focus_reward():
    return ['if = {',
            ' limit = { hidden_trigger = { NOT = { has_country_flag = RUS_red_army_decree_queued } } }',
            ' hidden_effect = { set_country_flag = RUS_red_army_decree_queued }',
            ' country_event = { id = '+EVENT_ID+' days = 3 }',
            '}']

def outputs():
    # Skeleton reviewed from RHoiScribe generate_event_batch; KR uses add_namespace.
    event=f'''add_namespace = RUS_red_army_decree

country_event = {{
 id = {EVENT_ID}
 title = {EVENT_ID}.t
 desc = {EVENT_ID}.d
 picture = {PICTURE}
 is_triggered_only = yes
 fire_only_once = yes
 option = {{
  name = {EVENT_ID}.a
  effect_tooltip = {{ add_stability = 0.05 }}
  hidden_effect = {{
   if = {{
    limit = {{ NOT = {{ has_country_flag = {FLAG} }} }}
    set_country_flag = {FLAG}
    add_stability = 0.05
   }}
  }}
 }}
}}
'''
    gfx=f'''spriteTypes = {{
 spriteType = {{
  name = "{PICTURE}"
  texturefile = "gfx/event_pictures/RUS_red_army_decree.png"
 }}
}}
'''
    loc={EVENT_ID+'.t':'人民委员会关于组建工农红军的法令',
         EVENT_ID+'.d':TEXT, EVENT_ID+'.a':'起来，不愿做奴隶的人们！'}
    result={Path('events/RUS_red_army_decree.txt'):event.encode('utf8'),
            Path('interface/RUS_red_army_decree.gfx'):gfx.encode('utf8')}
    for lang in ('simp_chinese','english','russian'):
        # Keep the authored text as fallback rather than exposing raw keys.
        text='l_'+lang+':\n'+''.join(' '+k+':0 '+json.dumps(v,ensure_ascii=False)+'\n' for k,v in loc.items())
        result[Path(f'localisation/{lang}/RUS_red_army_decree_l_{lang}.yml')]=text.encode('utf-8-sig')
    return result
