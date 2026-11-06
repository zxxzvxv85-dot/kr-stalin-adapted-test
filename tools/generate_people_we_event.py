"""1936-03-08 protest report, source-owned and read-only unless --write.

References: KR RUS events' native add_popularity; existing dated Russian
flavour on_daily_RUS windows; KR Russian protest event photograph.
"""
import json
from pathlib import Path
from generation_io import cli

ROOT=Path(__file__).resolve().parents[1]
ID='RUS_people_we.1'
FLAG='RUS_people_we_reported'
PICTURE='GFX_report_event_RUS_protest'
TITLE='人们，我们'
OPTION='“时间啊，向前！”'
BODY='''据《今日评论》报道，彼得格勒内部爆发了大规模的学生抗议和工会抗议。

前议员之女、“俄罗斯学生联合会”的主席奥尔佳·达尼洛夫娜·特里波列娃领导了本次学生抗议活动，学生团体对萨文科夫的独裁行径表达出了愤怒。警察出动后，“俄罗斯学生联合大会”内部“俄罗斯学生自治团”的主要人员之一索尼娅·米哈伊里芙娜以及其他学生领袖与参加抗议的部分学生均已被逮捕，并被送往城外的废弃工业区关押。

年轻的激进组织“无缚者同盟”领导者、工会领袖安东·舍斯托夫领导了本次因黑色星期一而起的工会罢工，诉求是改善远东地区工人的处境、按时发放工人工资、提供贫困家庭必要的生存物资、取消官员特权等，同时“无缚者同盟”成员意图刺杀萨文科夫，但被学生抗议影响导致刺杀失败。警察出动后，参与工会抗议的主要领导者与参与刺杀萨文科夫的人员均已被逮捕，并被一同送往城外的废弃工业区关押。

目前，奥尔佳·特里波列娃和娜塔莉亚·罗斯托娃正试图采用各种渠道释放被关押的学生与工会成员。

在为此案件举行的听证会上，被称为“卓雅”的证人在发言的最后突然大喊：“历史的车轮不可被倒转，暴君们终被人民推翻！”后被警察强行带离现场，但被其他学生救走。'''

def render_outputs():
 out={
 'events/RUS_people_we_events.txt':f'''add_namespace = RUS_people_we

country_event = {{
    id = {ID}
    title = {ID}.t
    desc = {ID}.d
    picture = {PICTURE}
    is_triggered_only = yes
    fire_only_once = yes
    trigger = {{ tag = RUS }}
    immediate = {{ set_country_flag = {FLAG} }}
    option = {{
        name = {ID}.a
        add_popularity = {{ ideology = national_populist popularity = -0.01 }}
    }}
}}
''',
 'common/on_actions/RUS_people_we_on_actions.txt':f'''on_actions = {{
    on_daily_RUS = {{
        effect = {{
            if = {{
                limit = {{
                    date > 1936.3.7
                    date < 1936.3.9
                    NOT = {{ has_country_flag = {FLAG} }}
                }}
                set_country_flag = {FLAG}
                country_event = {ID}
            }}
        }}
    }}
}}
'''}
 loc={ID+'.t':TITLE,ID+'.d':BODY,ID+'.a':OPTION}
 # Same Chinese text fallback in all three supported localisation namespaces.
 for lang in ('simp_chinese','english','russian'):
  out[f'localisation/{lang}/RUS_people_we_l_{lang}.yml']='l_'+lang+':\n'+''.join(' '+k+':0 '+json.dumps(v,ensure_ascii=False)+'\n' for k,v in loc.items())
 return out

if __name__=='__main__':cli(render_outputs,root=ROOT)
