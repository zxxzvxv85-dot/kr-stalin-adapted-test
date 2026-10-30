"""Six international reports, with a two/three-part speech. Default is read-only."""
from pathlib import Path
from itertools import combinations
import json

ROOT=Path(__file__).resolve().parents[1]
SPEC=Path('tools/design/RUS_international_reports_20261029.json')
NS='RUS_international_reports'
P='RUS_int_report_'

def block(k,body):
    return k+' = {\n'+''.join('\t'+line+'\n' for line in body.splitlines())+'}\n'

def speech_parts(paragraphs):
    candidates=[]
    for count in (2,3):
        for cuts in combinations(range(1,len(paragraphs)),count-1):
            points=(0,*cuts,len(paragraphs))
            parts=[paragraphs[a:b] for a,b in zip(points,points[1:])]
            sizes=[len(''.join(p)) for p in parts]
            if all(800<=n<=1200 for n in sizes):candidates.append((max(sizes)-min(sizes),cuts,parts))
        if candidates:return min(candidates)[2]
    raise ValueError('Speech cannot fit 2/3 parts of 800–1200 characters at paragraph boundaries')

def outputs():
    spec=json.loads((ROOT/SPEC).read_text(encoding='utf8'))
    parts=speech_parts(spec['speech']['paragraphs'])
    actor='tag = RUS OR = { has_socialist_government = yes has_government = communist }'
    tr=block(P+'actor',actor+'\n')
    for key,tag,test in [
        ('italy','SRI','has_country_flag = SRI_italy_unified_flag'),
        ('spain','SWF','has_country_flag = SPA_aftermath_of_the_civil_war owns_state = 41'),
        ('south','FOP','owns_state = 278 NOT = { country_exists = ARG }')]:
        tr+=block(P+key+'_victory','has_country_flag = '+P+key+'_intervened\n'+tag+' = { exists = yes OR = { has_socialist_government = yes has_government = communist } '+test+' }')
    tr+=block(P+'america_started','has_global_flag = USA_civil_war_begun_flag\nNOT = { has_global_flag = USA_civil_war_over_flag }')
    effects=[]
    for key,idx in [('italy',1),('spain',3),('america',4),('south',8)]:
        test=P+key+('_started' if key=='america' else '_victory')
        effects.append(block('if','limit = { '+P+'actor = yes '+test+' = yes NOT = { has_country_flag = '+P+key+'_queued } }\nset_country_flag = '+P+key+'_queued\ncountry_event = { id = '+NS+'.'+str(idx)+' }'))
    fx=block(P+'check',''.join(effects))
    # New per-country participation markers survive the generic victory counter
    # clearing its old receiver flag after an earlier, partial peace conference.
    mark=''
    for key,test in [
        ('italy','FROM = { tag = SRI NOT = { has_country_flag = SRI_italy_unified_flag } }'),
        ('spain','FROM = { tag = SWF NOT = { has_country_flag = SPA_aftermath_of_the_civil_war } }'),
        ('south','FROM = { OR = { tag = FOP tag = CHL } } country_exists = ARG')]:
        mark+=block('if','limit = { '+test+' }\nset_country_flag = '+P+key+'_intervened')
    hook=block('on_actions',block('on_send_volunteers',block('effect',block('if','limit = { ROOT = { '+P+'actor = yes } FROM = { has_war = yes OR = { has_socialist_government = yes has_government = communist } } }\nROOT = {\n'+mark+'}\n')))+block('on_daily_RUS',block('effect',P+'check = yes')))
    loc={};events='add_namespace = '+NS+'\n\n'
    items=[(1,'italy',None),(2,'visit',None),(3,'spain',None),(4,'america',None)]+[(5+i,'speech',i) for i in range(len(parts))]+[(8,'south',None)]
    for idx,key,page in items:
        row=spec[key];eid=NS+'.'+str(idx)
        title=row['title']+(f'（{page+1}/{len(parts)}）' if page is not None else '')
        desc='\n\n'.join(parts[page] if page is not None else row['paragraphs'])
        if key=='visit':desc=desc.replace('斯大林格勒','[217.GetName]')
        loc[eid+'.t']=title;loc[eid+'.d']=desc
        body='id = '+eid+'\ntitle = '+eid+'.t\ndesc = '+eid+'.d\npicture = '+row['picture']+'\nis_triggered_only = yes\nfire_only_once = yes\ntrigger = { '+P+'actor = yes }\n'
        # Starting the report, rather than closing it, starts the exact 7-day visit delay.
        immediate='set_country_flag = '+P+key+('_page_'+str(page+1) if page is not None else '')+'_seen\n'
        if key=='italy':immediate+='if = { limit = { NOT = { has_country_flag = '+P+'visit_queued } } set_country_flag = '+P+'visit_queued country_event = { id = '+NS+'.2 days = 7 } }\n'
        body+=block('immediate',immediate)
        labels=['继续阅读。'] if page is not None and page<len(parts)-1 else row['options']
        for i,label in enumerate(labels):
            opt=eid+'.'+chr(97+i);loc[opt]=label
            reward=''
            next_id=5 if key=='america' and i==1 else idx+1 if page is not None and page<len(parts)-1 else None
            if next_id:
                reward=block('hidden_effect',block('if','limit = { '+P+'actor = yes NOT = { has_country_flag = '+P+'speech_'+str(next_id)+'_queued } }\nset_country_flag = '+P+'speech_'+str(next_id)+'_queued\ncountry_event = { id = '+NS+'.'+str(next_id)+' }'))
            body+=block('option','name = '+opt+'\n'+reward)
        events+=block('country_event',body)+'\n'
    result={
        'events/RUS_international_reports_events.txt':events.rstrip()+'\n',
        'common/scripted_triggers/RUS_international_reports_triggers.txt':tr,
        'common/scripted_effects/RUS_international_reports_effects.txt':fx,
        'common/on_actions/RUS_international_reports_on_actions.txt':hook}
    # Preserve the submitted Chinese prose on other UIs, matching the existing
    # football report's explicit untranslated-content fallback.
    for lang in ['simp_chinese','english','russian']:
        result[f'localisation/{lang}/RUS_international_reports_l_{lang}.yml']='l_'+lang+':\n'+''.join(' '+k+':0 '+json.dumps(v,ensure_ascii=False)+'\n' for k,v in loc.items())
    return result

if __name__=='__main__':
    from generation_io import cli
    cli(outputs,root=ROOT,description=__doc__,kr_dependency=False)
