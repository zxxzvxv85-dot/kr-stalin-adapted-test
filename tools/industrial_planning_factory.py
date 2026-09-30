"""Independent local factory simulation; forecasts never commit production."""
from __future__ import annotations
import json
import re
from pathlib import Path
from industrial_planning_catalog import (PLANTS, STOCKS, PRODUCTS, STORED, PRICES, TARGET, TERRAINS, DEPOSITS, PROCESS_ORDER, allowed, region_plants, specialty)

P='RUS_ip_'
WIDTH,HEIGHT=23,14
REGIONS=json.loads((Path(__file__).parent/'data/industrial_planning_factory_regions.json').read_text(encoding='utf-8'))['regions']
CELLS=[]
for region in REGIONS:
    coords={}
    region['cells']=[]
    for y,row in enumerate(region['rows']):
        for x,char in enumerate(row):
            if char!='#':continue
            i=len(CELLS);coords[x,y]=i;region['cells'].append(i)
            CELLS.append(dict(id=i,x=x,y=y,label=f'{chr(65+x)}{y+1}',region=region['id']))
    for i in region['cells']:
        c=CELLS[i];x,y=c['x'],c['y']
        c['neighbors']=tuple(coords[p] for p in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)) if p in coords)
    region['hub']=coords[tuple(region['hub'])]
    for key in ('starter','protected'):region[key]=tuple(coords[tuple(p)] for p in region[key])
CELLS=tuple(CELLS)
HUBS={r['hub'] for r in REGIONS}
HUB=REGIONS[0]['hub']

def cell_id(label,region=0):
    """Human coordinates are for details/tooltips, never labels on the board."""
    return next(c['id'] for c in CELLS if c['region']==region and c['label']==label)
COST={k:p['cost'] for k,p in PLANTS.items()}
PROJECTS={k:(p['zh'],p['en'],p['icon']) for k,p in PLANTS.items()}

def block(name,body):return name+' = {\n'+''.join('\t'+line+'\n' if line else '\n' for line in body.rstrip().splitlines())+'}\n'
def variable(cmd,k,v):return f'{cmd} = {{ {P}{k} = {v} }}\n'
def setv(k,v):return variable('set_variable',k,v)
def add(k,v):return variable('add_to_variable',k,v)
def sub(k,v):return variable('subtract_from_variable',k,v)
def mul(k,v):return variable('multiply_variable',k,v)
def div(k,v):return variable('divide_variable',k,v)
def cv(k,op,v):return f'check_variable = {{ {P}{k} {op} {v} }}\n'
def ge(k,v):return block('NOT',cv(k,'<',v))
def iff(cond,body):return block('if',block('limit',cond)+body)
def fx(k,body):return block(P+k,body)
def clamp(k,lo,hi):return f'clamp_variable = {{ var = {P}{k} min = {lo} max = {hi} }}\n'
def minimum(k,v):return iff(cv(k,'>',v),setv(k,v))

def eligible(i,kind):
    if i in HUBS or not allowed(kind,CELLS[i]['region']):return 'always = no\n'
    return (cv('region','=',CELLS[i]['region'])+cv(f'n{i}_terrain','=',PLANTS[kind]['terrain'])
        +block('OR',cv(f'n{i}_type','=',0)+cv(f'n{i}_type','=',kind))+cv(f'n{i}_level','<',3))

def geology(region):
    """Exact local quotas, random positions, and an obstacle-proof backbone."""
    a,b=region['starter'][-2:]
    result=block('random_list',block('1',setv(f'n{a}_terrain',1)+setv(f'n{b}_terrain',2))
        +block('1',setv(f'n{a}_terrain',2)+setv(f'n{b}_terrain',1)))
    for terrain,key in ((3,'rocks'), *TERRAINS.items()):
        options=''
        for i in region['cells']:
            if i in region['starter'] or terrain==3 and i in region['protected']:continue
            # Native KR uses random_list modifier factor=0 to exclude entries.
            options+=block('1',block('modifier','factor = 0\n'+block('NOT',cv(f'n{i}_terrain','=',0)))+setv(f'n{i}_terrain',terrain))
        count=(region[key] if key in ('coal','iron','rocks') else DEPOSITS[region['id']].get(key,0))-(1 if terrain in (1,2) else 0)
        if count<=0:continue
        result+=setv('roll_remaining',count)+block('while_loop_effect',block('limit',cv('roll_remaining','>',0))
            +block('random_list',options)+sub('roll_remaining',1))
    return result

def render_economy():
    triggers=[fx('available','original_tag = RUS\nis_ai = no\nhas_country_flag = RUS_ip_ui_unlocked\n'),
        fx('editing','RUS_ip_available = yes\nhas_country_flag = RUS_ip_factory_initialized\nhas_country_flag = RUS_ip_open\nNOT = { has_country_flag = RUS_ip_finished }\n')]
    effects=[]
    for kind,cost in COST.items():
        sites=''.join(block('AND',cv('selected','=',c['id'])+eligible(c['id'],kind)) for c in CELLS if c['id'] not in HUBS and allowed(kind,c['region']))
        triggers.append(fx(f'can_build_{kind}','RUS_ip_editing = yes\n'+ge('budget',cost)+block('OR',sites)))
    for action in ('rail','remove','remove_rail','switch'):
        sites=[]
        for c in CELLS:
            i=c['id']
            if i in HUBS:continue
            cond=cv('selected','=',i)+cv('region','=',c['region'])+block('NOT',cv(f'n{i}_terrain','=',3))
            cond+=cv(f'n{i}_rail','<',3) if action=='rail' else cv(f'n{i}_rail','>',0) if action=='remove_rail' else cv(f'n{i}_type','>',0)
            sites.append(block('AND',cond))
        triggers.append(fx('can_'+action,'RUS_ip_editing = yes\n'+(ge('budget',1) if action=='rail' else '')+block('OR',''.join(sites))))
    init='set_country_flag = RUS_ip_factory_initialized\n'
    for flag in ('started','active','finished','help_open','restart_armed'):init+=f'clr_country_flag = RUS_ip_{flag}\n'
    for key,value in dict(region=0,selected=HUB,budget=40,value=0,machines=0,build_page=0,days_left=1800,elapsed=0,spent=0,refunded=0,earned=0,score=0).items():init+=setv(key,value)
    for c in CELLS:
        for key in ('type','level','rail','paid','rail_paid','paused','route','effective'):
            init+=setv(f'n{c["id"]}_{key}',3 if c['id'] in HUBS and key=='rail' else 0)
        init+=setv(f'n{c["id"]}_terrain',4 if c['id'] in HUBS else 0)
    for r in REGIONS:
        rid=r['id']
        for key in STORED:init+=setv(f'r{rid}_{key}',dict(coal=6,iron=4,steel=2).get(key,0))
        init+=setv(f'r{rid}_selected',r['hub'])
        effects.append(fx(f'r{rid}_geology',geology(r)))
        init+=f'RUS_ip_r{rid}_geology = yes\n'
        effects.append(fx(f'select_region_{rid}',iff('RUS_ip_available = yes\nhas_country_flag = RUS_ip_open\nNOT = { has_country_flag = RUS_ip_help_open }\n',
            setv('region',rid)+setv('selected',P+f'r{rid}_selected')+'clr_country_flag = RUS_ip_restart_armed\nRUS_ip_refresh = yes\n')))
    effects.append(fx('initialize',init+'RUS_ip_refresh = yes\n'))
    effects.append(fx('open_effect',iff('RUS_ip_available = yes\n',iff('NOT = { has_country_flag = RUS_ip_factory_initialized }\n','RUS_ip_initialize = yes\n')+'set_country_flag = RUS_ip_open\nclr_country_flag = RUS_ip_help_open\nclr_country_flag = RUS_ip_restart_armed\nRUS_ip_refresh = yes\n')))
    effects.append(fx('enable_gui',iff('original_tag = RUS\nis_ai = no\n','set_country_flag = RUS_ip_ui_unlocked\nRUS_ip_open_effect = yes\n')))
    effects.append(fx('close_effect','clr_country_flag = RUS_ip_open\nclr_country_flag = RUS_ip_help_open\nclr_country_flag = RUS_ip_restart_armed\n'))
    effects.append(fx('toggle',iff('RUS_ip_available = yes\n',iff('has_country_flag = RUS_ip_open\n','RUS_ip_close_effect = yes\n')+block('else','RUS_ip_open_effect = yes\n'))))
    effects.append(fx('toggle_help',iff('RUS_ip_available = yes\nhas_country_flag = RUS_ip_open\n',iff('has_country_flag = RUS_ip_help_open\n','clr_country_flag = RUS_ip_help_open\n')+block('else','set_country_flag = RUS_ip_help_open\n')+'clr_country_flag = RUS_ip_restart_armed\n'+add('dirty',1))))
    for page in (0,1):effects.append(fx(f'build_page_{page}',iff('RUS_ip_available = yes\nhas_country_flag = RUS_ip_open\nNOT = { has_country_flag = RUS_ip_help_open }\n',setv('build_page',page)+add('dirty',1))))
    effects.append(fx('start',iff('RUS_ip_editing = yes\nNOT = { has_country_flag = RUS_ip_started }\n','set_country_flag = RUS_ip_started\nset_country_flag = RUS_ip_active\nRUS_ip_refresh = yes\n')))

    # Widest path: all segments must support the desired facility grade.
    # Cycles without a route to the hub remain disconnected.
    refresh=''.join(setv(f'n{c["id"]}_route',3 if c['id'] in HUBS else 0) for c in CELLS)+setv('changed',1)+setv('iterations',0)
    flood=''
    for c in CELLS:
        i=c['id']
        if i in HUBS:continue
        body=''
        for j in c['neighbors']:
            body+=iff(cv(f'n{j}_route','>',P+f'n{i}_route'),setv('candidate',P+f'n{i}_rail')+minimum('candidate',P+f'n{j}_route')+iff(cv('candidate','>',P+f'n{i}_route'),setv(f'n{i}_route',P+'candidate')+setv('changed',1)))
        flood+=iff(block('NOT',cv(f'n{i}_terrain','=',3))+cv(f'n{i}_rail','>',P+f'n{i}_route'),body)
    refresh+=block('while_loop_effect',block('limit',cv('changed','=',1)+cv('iterations','<',len(CELLS)))+setv('changed',0)+flood+add('iterations',1))
    for r in REGIONS:
        for key in ('connected_count','offline_count',*(p['key']+'_capacity' for p in PLANTS.values())):refresh+=setv(f'r{r["id"]}_{key}',0)
    for c in CELLS:
        i=c['id'];rp=f'r{c["region"]}_'
        refresh+=setv(f'n{i}_effective',0)+iff(cv(f'n{i}_route','>',0),add(rp+'connected_count',1))
        refresh+=iff(cv(f'n{i}_type','>',0)+cv(f'n{i}_route','=',0),add(rp+'offline_count',1))
        body=setv(f'n{i}_effective',P+f'n{i}_level')+minimum(f'n{i}_effective',P+f'n{i}_route')
        for kind in region_plants(c['region']):body+=iff(cv(f'n{i}_type','=',kind),add(rp+PLANTS[kind]['key']+'_capacity',P+f'n{i}_effective'))
        refresh+=iff(block('NOT',cv(f'n{i}_terrain','=',3))+cv(f'n{i}_type','>',0)+cv(f'n{i}_paused','=',0),body)
    effects.append(fx('refresh',refresh+'RUS_ip_forecast = yes\nRUS_ip_selection_cache = yes\n'+add('dirty',1)))

    # Regional forecasts operate only on next_* scratch stocks. No production
    # or budget mutation occurs until the single daily commit below.
    for r in REGIONS:
        rid=r['id']
        forecast=''.join(setv('next_'+key,P+key) for key in STORED)
        forecast+=''.join(setv(k,0) for k in ('power_total','power_left','power_demand','bottleneck','investment_output','specialty_output'))
        for p in PLANTS.values():forecast+=setv(p['key']+'_output',0)
        for kind in PROCESS_ORDER:
            if not allowed(kind,rid):continue
            p=PLANTS[kind];key=p['key'];out=key+'_output';rate=key+'_rate'
            forecast+=setv(rate,P+key+'_capacity')+mul(rate,p['rate'])+setv(out,P+rate)+setv('constraint',0)
            inputs={**p['inputs']}
            if p['power']:inputs['power']=p['power']
            for resource,ratio in inputs.items():
                source='power_left' if resource=='power' else 'next_'+resource
                code=3 if resource=='power' else {'coal':1,'iron':2,'steel':4}.get(resource,6+STOCKS.index(resource))
                forecast+=setv('available_amount',P+source)+div('available_amount',ratio)
                forecast+=iff(cv(out,'>',P+'available_amount'),setv(out,P+'available_amount')+setv('constraint',code))
            forecast+=clamp(out,0,100000)
            forecast+=setv('shortfall',P+rate)+sub('shortfall',P+out)
            forecast+=iff(cv('shortfall','>',.0001)+cv('bottleneck','=',0),setv('bottleneck',P+'constraint'))
            for resource,ratio in inputs.items():
                target='power_left' if resource=='power' else 'next_'+resource
                forecast+=setv('consumed',P+out)+mul('consumed',ratio)+sub(target,P+'consumed')+clamp(target,0,100000)
            if p['power']:
                forecast+=setv('full_power',P+rate)+mul('full_power',p['power'])+add('power_demand',P+'full_power')
            if p['output']=='power':forecast+=add('power_total',P+out)+add('power_left',P+out)
            else:forecast+=add('next_'+p['output'],P+out)
            if p['output'] in PRODUCTS:
                forecast+=setv('output_value',P+out)+mul('output_value',PRICES[p['output']])+add('investment_output',P+'output_value')+add('next_value',P+'output_value')
                if p['region'] is not None:forecast+=setv('specialty_output',P+out)
        forecast+=iff(cv('machine_capacity','=',0)+cv(specialty(rid)['key']+'_capacity','=',0),setv('bottleneck',5))
        for key in STORED:forecast+=clamp('next_'+key,0,1000000)
        for key in ('coal','iron','steel','machine','specialty','investment'):
            forecast+=setv(key+'_month',P+key+'_output')+mul(key+'_month',30)
        regional=re.sub(r'\bRUS_ip_(\w+)',lambda m:P+f'r{rid}_'+m[1],forecast)
        effects.append(fx(f'r{rid}_forecast',regional))
    aggregate=''.join(setv(k,0) for k in (*PRODUCTS,'value','next_value','investment_output','total_machine_output'))
    for r in REGIONS:
        rid=r['id'];aggregate+=f'RUS_ip_r{rid}_forecast = yes\n'
        for k in (*PRODUCTS,'value','next_value','investment_output'):aggregate+=add(k,P+f'r{rid}_{k}')
        aggregate+=add('total_machine_output',P+f'r{rid}_machine_output')
    aggregate+=setv('total_machine_month',P+'total_machine_output')+mul('total_machine_month',30)
    aggregate+=setv('total_value_month',P+'investment_output')+mul('total_value_month',30)
    aggregate+=setv('score',P+'value')+div('score',TARGET/100)+clamp('score',0,100)
    effects.append(fx('forecast',aggregate))
    cache=''
    display=(*STOCKS,'connected_count','offline_count','power_total','power_left','power_demand','bottleneck',
        *(p['key']+'_capacity' for p in PLANTS.values()),
        'coal_month','iron_month','steel_month','machine_month','specialty_month','investment_month')
    for r in REGIONS:
        rid=r['id'];cache+=iff(cv('region','=',rid),''.join(setv(k,P+f'r{rid}_{k}') for k in display))
    for c in CELLS:
        i=c['id'];cache+=iff(cv('selected','=',i)+cv('region','=',c['region']),
            ''.join(setv('sel_'+k,P+f'n{i}_{k}') for k in ('type','level','rail','route','effective','paused','terrain'))
            +setv(f'r{c["region"]}_selected',i))
    effects.append(fx('selection_cache',cache))
    for kind,cost in COST.items():
        body=''
        for c in CELLS:
            i=c['id']
            if i in HUBS or not allowed(kind,c['region']):continue
            body+=iff(cv('selected','=',i)+eligible(i,kind),setv(f'n{i}_type',kind)+add(f'n{i}_level',1)+add(f'n{i}_paid',cost)+sub('budget',cost)+add('spent',cost))
        effects.append(fx(f'build_{kind}',iff(f'RUS_ip_can_build_{kind} = yes\n',body+'clr_country_flag = RUS_ip_restart_armed\nRUS_ip_refresh = yes\n')))
    for action in ('rail','remove','remove_rail','switch'):
        body=''
        for c in CELLS:
            i=c['id']
            if i in HUBS:continue
            if action=='rail':change=add(f'n{i}_rail',1)+add(f'n{i}_rail_paid',1)+sub('budget',1)+add('spent',1)
            elif action=='remove':change=add('budget',P+f'n{i}_paid')+add('refunded',P+f'n{i}_paid')+''.join(setv(f'n{i}_{key}',0) for key in ('paid','type','level','paused'))
            elif action=='remove_rail':change=add('budget',P+f'n{i}_rail_paid')+add('refunded',P+f'n{i}_rail_paid')+setv(f'n{i}_rail_paid',0)+setv(f'n{i}_rail',0)
            else:change=iff(cv(f'n{i}_paused','=',0),setv(f'n{i}_paused',1))+block('else',setv(f'n{i}_paused',0))
            body+=iff(cv('selected','=',i)+cv('region','=',c['region']),change)
        effects.append(fx(action,iff(f'RUS_ip_can_{action} = yes\n',body+'clr_country_flag = RUS_ip_restart_armed\nRUS_ip_refresh = yes\n')))
    day='RUS_ip_refresh = yes\n'
    for r in REGIONS:
        for key in STORED:day+=setv(f'r{r["id"]}_{key}',P+f'r{r["id"]}_next_{key}')
    day+=add('budget',P+'investment_output')+add('earned',P+'investment_output')+sub('days_left',1)+add('elapsed',1)
    day+=iff(cv('days_left','=',0),'clr_country_flag = RUS_ip_active\nset_country_flag = RUS_ip_finished\n')+'RUS_ip_refresh = yes\n'
    effects.append(fx('daily',iff('RUS_ip_available = yes\nhas_country_flag = RUS_ip_factory_initialized\nhas_country_flag = RUS_ip_active\n'+cv('days_left','>',0),day)))
    effects.append(fx('arm_restart',iff('RUS_ip_available = yes\nhas_country_flag = RUS_ip_open\n','set_country_flag = RUS_ip_restart_armed\n'+add('dirty',1))))
    effects.append(fx('confirm_restart',iff('RUS_ip_available = yes\nhas_country_flag = RUS_ip_open\nhas_country_flag = RUS_ip_restart_armed\n','RUS_ip_initialize = yes\n')))
    actions=block('on_actions',block('on_daily',block('effect','RUS_ip_daily = yes\n'))+block('on_startup',block('effect',block('every_country',block('limit','original_tag = RUS\nhas_country_flag = RUS_ip_factory_initialized\n')+'RUS_ip_refresh = yes\n'))))
    return triggers,effects,actions
