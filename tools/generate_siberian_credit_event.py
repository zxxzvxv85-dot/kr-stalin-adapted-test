"""White-revolt opening -> 30d credit dispute -> option -> 30d Siberia report.

References: existing white-revolt events/on_actions and KR Russia event 107's
native stability loss + delayed country_event. Default is read-only.
"""
import argparse,json,re
from pathlib import Path
from hoi4_politics_blocks import parse
from generation_io import process_outputs

ROOT=Path(__file__).resolve().parents[1]
EVENT='events/RUS stalin white revolt events.txt'
ACTION='common/on_actions/on_actions_Russia.txt'
ID='rus_stalin_white_revolt_events.23'
NEXT='rus_stalin_white_revolt_events.18'
SCHEDULED='RUS_siberian_credit_scheduled'
SEEN='RUS_siberian_credit_seen'
FOLLOWUP='RUS_siberian_credit_followup_scheduled'
TITLE='谁的功劳？'
OPTION='新共和国还没站稳脚跟，又要开始内斗吗？'
BODY='''昨日清晨，克利缅特·伏罗希洛夫所属的“整合运动”“雪怪”游击部队、工农民兵部队和赤卫队打响了夺取西伯利亚政权第一枪，辅以左翼社会革命党的部分农村民兵，很快就夺取了首府上乌金斯克，由于整合运动部队仍然缺乏拥有足够的政府工作经验的人，他们便把当地的政府机构交给左翼社会革命党控制，但部队仍然听命于伏罗希洛夫等人。

今日，乌兰乌德（原上乌金斯克）政府宣布受中央政府管辖，在提交的关于夺权的声明中，乌兰乌德政府声称：夺取政权的过程是由左翼社会革命党领导的，伏罗希洛夫对当地左翼社会革命党的顺从为夺权提供了许多便利。

乌兰乌德一处原“整合运动”游击区所在村庄的一位老农民听闻乌兰乌德政府的声明后大发雷霆：

“简直就是放他（斯拉夫粗口）的（斯拉夫粗口）！尽管伏罗希洛夫同志的性格温和，就算先前有着深仇大恨，也会为了共同的利益暂时与他人同盟。凭我这近二十年和他相处的经验，他绝无可能会顺从于左翼社会革命党这群（斯拉夫粗口）的东西！”

“左翼社会革命党除了会放空话还会干什么？我第一次被分到田还是红军分的，后来内战结束我又失去了我的田地；这次第二次革命我得到的田竟然还是‘整合运动’分给我们的，而左翼社会革命党的所谓村社从头到尾我们都没有见到过，他们还有脸说他们是领导者！”

“在二十年前的革命，左翼社会革命党暴力夺取了列宁同志的生命，转投了反动势力的阵营；而到了如今，明明是“整合运动”率先揭竿而起，他们却声明是他们领导有力。这次这群蛀虫又要夺取革命的胜利果实吗！”'''

def render_outputs():
 text=(ROOT/EVENT).read_text(encoding='utf-8-sig')
 # Remove only our event before re-rendering, preserving all old event bodies.
 for n in reversed(parse(text)):
  if n.k=='country_event' and n.value('id')==ID:text=text[:n.a]+text[n.b:]
 opening=next(n for n in parse(text) if n.k=='country_event' and n.value('id')=='rus_stalin_white_revolt_events.1')
 immediate=opening.one('immediate')
 if SCHEDULED not in immediate.raw():
  addition=f'''\n\t\tif = {{
\t\t\tlimit = {{
\t\t\t\tNOT = {{ has_country_flag = {SCHEDULED} }}
\t\t\t\tNOT = {{ has_country_flag = {SEEN} }}
\t\t\t}}
\t\t\tset_country_flag = {SCHEDULED}
\t\t\tcountry_event = {{ id = {ID} days = 30 }}
\t\t}}
\t'''
  text=text[:immediate.ib].rstrip()+addition+text[immediate.ib:]
 new=f'''country_event = {{
    id = {ID}
    title = {ID}.t
    desc = {ID}.d
    picture = GFX_report_event_RUS_partisans1
    is_triggered_only = yes
    fire_only_once = yes
    trigger = {{ has_socialist_government = yes }}
    immediate = {{ set_country_flag = {SEEN} }}
    option = {{
        name = {ID}.a
        add_stability = -0.01
        if = {{
            limit = {{ hidden_trigger = {{ NOT = {{ has_country_flag = {FOLLOWUP} }} }} }}
            hidden_effect = {{ set_country_flag = {FOLLOWUP} }}
            country_event = {{ id = {NEXT} days = 30 }}
        }}
    }}
}}
'''
 out={EVENT:text.rstrip()+'\n\n'+new}
 # This legacy file contains mixed line endings. Preserve them byte-for-byte;
 # changing two dispatch lines must not reformat the entire Russian on_actions.
 actions=(ROOT/ACTION).read_bytes().decode('utf-8-sig')
 old=r'(?m)^[ \t]*country_event = \{ id = rus_stalin_white_revolt_events\.18 days = 60 \}\r?\n'
 actions,count=re.subn(old,'',actions)
 assert count in (0,2),f'Review changed old Siberia dispatch sites: {count}'
 out[ACTION]=actions
 loc={ID+'.t':TITLE,ID+'.d':BODY,ID+'.a':OPTION}
 for lang in ('simp_chinese','english','russian'):
  out[f'localisation/{lang}/RUS_siberian_credit_l_{lang}.yml']='l_'+lang+':\n'+''.join(' '+k+':0 '+json.dumps(v,ensure_ascii=False)+'\n' for k,v in loc.items())
 return out

def main():
 p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group();g.add_argument('--write',action='store_true');g.add_argument('--check',action='store_true');args=p.parse_args()
 out=render_outputs();actions=out.pop(ACTION);target=ROOT/ACTION
 changed=target.read_bytes()!=actions.encode('utf-8')
 status=process_outputs(out,ROOT,write=args.write)
 if changed:
  if args.write:target.write_bytes(actions.encode('utf-8'))
  print(('WROTE ' if args.write else 'DIFF ')+ACTION)
 return max(status,int(changed and not args.write))

if __name__=='__main__':raise SystemExit(main())
