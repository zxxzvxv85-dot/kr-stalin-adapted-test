"""Independent local factory simulation; forecasts never commit production."""
from __future__ import annotations

P='RUS_ip_'
WIDTH,HEIGHT,HUB=8,6,43
COAL={9,17,33}; IRON={14,22,38}; ROCKS={11,12,27,28}
COST={1:3,2:3,3:5,4:6,5:8}
PROJECTS={
    1:('煤矿','Coal mine','decision_coal'),
    2:('铁矿','Iron mine','decision_steel'),
    3:('电站','Power station','decision_generic_electricity'),
    4:('钢铁厂','Steelworks','decision_generic_factory'),
    5:('机械厂','Machine works','decision_generic_industry'),
}
CELLS=tuple(dict(id=i,x=i%WIDTH,y=i//WIDTH,label=f'{chr(65+i%WIDTH)}{i//WIDTH+1}',
    coal=i in COAL,iron=i in IRON,rock=i in ROCKS,
    neighbors=tuple(j for j in (i-1,i+1,i-WIDTH,i+WIDTH)
        if 0<=j<WIDTH*HEIGHT and abs(j%WIDTH-i%WIDTH)+abs(j//WIDTH-i//WIDTH)==1))
    for i in range(WIDTH*HEIGHT))

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
    if i==HUB or i in ROCKS or kind==1 and i not in COAL or kind==2 and i not in IRON:
        return 'always = no\n'
    if kind not in (1,2) and i in COAL|IRON:return 'always = no\n'
    return block('OR',cv(f'n{i}_type','=',0)+cv(f'n{i}_type','=',kind))+cv(f'n{i}_level','<',3)

def render_economy():
    triggers=[fx('available','original_tag = RUS\nis_ai = no\nhas_country_flag = RUS_ip_ui_unlocked\n'),
        fx('editing','RUS_ip_available = yes\nhas_country_flag = RUS_ip_factory_initialized\nhas_country_flag = RUS_ip_open\nNOT = { has_country_flag = RUS_ip_finished }\n')]
    effects=[]
    for kind,cost in COST.items():
        sites=''.join(block('AND',cv('selected','=',c['id'])+eligible(c['id'],kind)) for c in CELLS)
        triggers.append(fx(f'can_build_{kind}','RUS_ip_editing = yes\n'+ge('budget',cost)+block('OR',sites)))
    for action in ('rail','remove','remove_rail','switch'):
        sites=[]
        for c in CELLS:
            i=c['id']
            if i==HUB or c['rock']:continue
            cond=cv('selected','=',i)
            cond+=cv(f'n{i}_rail','<',3) if action=='rail' else cv(f'n{i}_rail','>',0) if action=='remove_rail' else cv(f'n{i}_type','>',0)
            sites.append(block('AND',cond))
        triggers.append(fx('can_'+action,'RUS_ip_editing = yes\n'+(ge('budget',1) if action=='rail' else '')+block('OR',''.join(sites))))
    init='set_country_flag = RUS_ip_factory_initialized\n'
    for flag in ('started','active','finished','help_open','restart_armed'):init+=f'clr_country_flag = RUS_ip_{flag}\n'
    for key,value in dict(selected=HUB,budget=40,coal=6,iron=4,steel=2,machines=0,days_left=1800,elapsed=0,spent=0,refunded=0,earned=0,score=0).items():init+=setv(key,value)
    for c in CELLS:
        for key in ('type','level','rail','paid','rail_paid','paused','route','effective'):
            init+=setv(f'n{c["id"]}_{key}',3 if c['id']==HUB and key=='rail' else 0)
    effects.append(fx('initialize',init+'RUS_ip_refresh = yes\n'))
    effects.append(fx('open_effect',iff('RUS_ip_available = yes\n',iff('NOT = { has_country_flag = RUS_ip_factory_initialized }\n','RUS_ip_initialize = yes\n')+'set_country_flag = RUS_ip_open\nclr_country_flag = RUS_ip_help_open\nclr_country_flag = RUS_ip_restart_armed\nRUS_ip_refresh = yes\n')))
    effects.append(fx('enable_gui',iff('original_tag = RUS\nis_ai = no\n','set_country_flag = RUS_ip_ui_unlocked\nRUS_ip_open_effect = yes\n')))
    effects.append(fx('close_effect','clr_country_flag = RUS_ip_open\nclr_country_flag = RUS_ip_help_open\nclr_country_flag = RUS_ip_restart_armed\n'))
    effects.append(fx('toggle',iff('RUS_ip_available = yes\n',iff('has_country_flag = RUS_ip_open\n','RUS_ip_close_effect = yes\n')+block('else','RUS_ip_open_effect = yes\n'))))
    effects.append(fx('toggle_help',iff('RUS_ip_available = yes\nhas_country_flag = RUS_ip_open\n',iff('has_country_flag = RUS_ip_help_open\n','clr_country_flag = RUS_ip_help_open\n')+block('else','set_country_flag = RUS_ip_help_open\n')+'clr_country_flag = RUS_ip_restart_armed\n'+add('dirty',1))))
    effects.append(fx('start',iff('RUS_ip_editing = yes\nNOT = { has_country_flag = RUS_ip_started }\n','set_country_flag = RUS_ip_started\nset_country_flag = RUS_ip_active\nRUS_ip_refresh = yes\n')))

    # Widest path: all segments must support the desired facility grade.
    # Cycles without a route to the hub remain disconnected.
    refresh=''.join(setv(f'n{c["id"]}_route',0) for c in CELLS)+setv(f'n{HUB}_route',3)+setv('changed',1)+setv('iterations',0)
    flood=''
    for c in CELLS:
        i=c['id']
        if i==HUB or c['rock']:continue
        body=''
        for j in c['neighbors']:
            body+=iff(cv(f'n{j}_route','>',P+f'n{i}_route'),setv('candidate',P+f'n{i}_rail')+minimum('candidate',P+f'n{j}_route')+iff(cv('candidate','>',P+f'n{i}_route'),setv(f'n{i}_route',P+'candidate')+setv('changed',1)))
        flood+=iff(cv(f'n{i}_rail','>',P+f'n{i}_route'),body)
    refresh+=block('while_loop_effect',block('limit',cv('changed','=',1)+cv('iterations','<',len(CELLS)))+setv('changed',0)+flood+add('iterations',1))
    for key in ('connected_count','offline_count','coal_capacity','iron_capacity','power_capacity','steel_capacity','machine_capacity'):refresh+=setv(key,0)
    for c in CELLS:
        i=c['id']
        refresh+=setv(f'n{i}_effective',0)+iff(cv(f'n{i}_route','>',0),add('connected_count',1))
        refresh+=iff(cv(f'n{i}_type','>',0)+cv(f'n{i}_route','=',0),add('offline_count',1))
        body=setv(f'n{i}_effective',P+f'n{i}_level')+minimum(f'n{i}_effective',P+f'n{i}_route')
        for kind,key in ((1,'coal'),(2,'iron'),(3,'power'),(4,'steel'),(5,'machine')):body+=iff(cv(f'n{i}_type','=',kind),add(key+'_capacity',P+f'n{i}_effective'))
        refresh+=iff(cv(f'n{i}_type','>',0)+cv(f'n{i}_paused','=',0),body)
    effects.append(fx('refresh',refresh+'RUS_ip_forecast = yes\nRUS_ip_selection_cache = yes\n'+add('dirty',1)))

    forecast=''.join(setv('next_'+key,P+key) for key in ('coal','iron','steel','machines'))
    for key in ('coal','iron'):forecast+=setv(key+'_output',P+key+'_capacity')+mul(key+'_output',.3)+add('next_'+key,P+key+'_output')
    forecast+=setv('fuel',P+'power_capacity')+mul('fuel',.1)+minimum('fuel',P+'next_coal')+sub('next_coal',P+'fuel')
    forecast+=setv('power_total',P+'fuel')+mul('power_total',6)+setv('power_left',P+'power_total')
    forecast+=setv('steel_rate',P+'steel_capacity')+mul('steel_rate',.2)+setv('steel_output',P+'steel_rate')
    forecast+=minimum('steel_output',P+'next_coal')+minimum('steel_output',P+'next_iron')+setv('temp_power',P+'power_left')+div('temp_power',2)+minimum('steel_output',P+'temp_power')
    forecast+=sub('next_coal',P+'steel_output')+sub('next_iron',P+'steel_output')+add('next_steel',P+'steel_output')+setv('temp_power',P+'steel_output')+mul('temp_power',2)+sub('power_left',P+'temp_power')+clamp('power_left',0,100000)
    forecast+=setv('machine_rate',P+'machine_capacity')+mul('machine_rate',.2)+setv('machine_output',P+'machine_rate')
    forecast+=setv('temp_steel',P+'next_steel')+div('temp_steel',2)+minimum('machine_output',P+'temp_steel')+minimum('machine_output',P+'power_left')
    forecast+=setv('temp_steel',P+'machine_output')+mul('temp_steel',2)+sub('next_steel',P+'temp_steel')+sub('power_left',P+'machine_output')+add('next_machines',P+'machine_output')
    forecast+=setv('investment_output',P+'machine_output')+mul('investment_output',1)
    forecast+=setv('power_demand',P+'steel_rate')+mul('power_demand',2)+add('power_demand',P+'machine_rate')
    for key in ('coal','iron','steel','machines'):forecast+=clamp('next_'+key,0,100000)
    for key in ('coal','iron','steel','machine','investment'):forecast+=setv(key+'_month',P+key+'_output')+mul(key+'_month',30)
    forecast+=setv('bottleneck',0)
    shortage=block('OR',cv('steel_output','<',P+'steel_rate')+cv('machine_output','<',P+'machine_rate'))
    checks=[(1,cv('next_coal','<',.001)),(2,cv('next_iron','<',.001)+cv('steel_output','<',P+'steel_rate')),(3,cv('power_left','<',.001)),(4,cv('next_steel','<',.001))]
    branches=''.join(block('if' if i==0 else 'else_if',block('limit',cond)+setv('bottleneck',number)) for i,(number,cond) in enumerate(checks))
    forecast+=iff(shortage,branches)+iff(cv('machine_capacity','=',0),setv('bottleneck',5))
    forecast+=setv('score',P+'machines')+div('score',5)+clamp('score',0,100)
    effects.append(fx('forecast',forecast))
    cache=''
    for c in CELLS:
        i=c['id'];cache+=iff(cv('selected','=',i),''.join(setv('sel_'+k,P+f'n{i}_{k}') for k in ('type','level','rail','route','effective','paused')))
    effects.append(fx('selection_cache',cache))
    for kind,cost in COST.items():
        body=''
        for c in CELLS:
            i=c['id'];body+=iff(cv('selected','=',i)+eligible(i,kind),setv(f'n{i}_type',kind)+add(f'n{i}_level',1)+add(f'n{i}_paid',cost)+sub('budget',cost)+add('spent',cost))
        effects.append(fx(f'build_{kind}',iff(f'RUS_ip_can_build_{kind} = yes\n',body+'clr_country_flag = RUS_ip_restart_armed\nRUS_ip_refresh = yes\n')))
    for action in ('rail','remove','remove_rail','switch'):
        body=''
        for c in CELLS:
            i=c['id']
            if i==HUB or c['rock']:continue
            if action=='rail':change=add(f'n{i}_rail',1)+add(f'n{i}_rail_paid',1)+sub('budget',1)+add('spent',1)
            elif action=='remove':change=add('budget',P+f'n{i}_paid')+add('refunded',P+f'n{i}_paid')+''.join(setv(f'n{i}_{key}',0) for key in ('paid','type','level','paused'))
            elif action=='remove_rail':change=add('budget',P+f'n{i}_rail_paid')+add('refunded',P+f'n{i}_rail_paid')+setv(f'n{i}_rail_paid',0)+setv(f'n{i}_rail',0)
            else:change=iff(cv(f'n{i}_paused','=',0),setv(f'n{i}_paused',1))+block('else',setv(f'n{i}_paused',0))
            body+=iff(cv('selected','=',i),change)
        effects.append(fx(action,iff(f'RUS_ip_can_{action} = yes\n',body+'clr_country_flag = RUS_ip_restart_armed\nRUS_ip_refresh = yes\n')))
    day='RUS_ip_refresh = yes\n'+''.join(setv(key,P+'next_'+key) for key in ('coal','iron','steel','machines'))
    day+=add('budget',P+'investment_output')+add('earned',P+'investment_output')+sub('days_left',1)+add('elapsed',1)
    day+=iff(cv('days_left','=',0),'clr_country_flag = RUS_ip_active\nset_country_flag = RUS_ip_finished\n')+'RUS_ip_refresh = yes\n'
    effects.append(fx('daily',iff('RUS_ip_available = yes\nhas_country_flag = RUS_ip_factory_initialized\nhas_country_flag = RUS_ip_active\n'+cv('days_left','>',0),day)))
    effects.append(fx('arm_restart',iff('RUS_ip_available = yes\nhas_country_flag = RUS_ip_open\n','set_country_flag = RUS_ip_restart_armed\n'+add('dirty',1))))
    effects.append(fx('confirm_restart',iff('RUS_ip_available = yes\nhas_country_flag = RUS_ip_open\nhas_country_flag = RUS_ip_restart_armed\n','RUS_ip_initialize = yes\n')))
    actions=block('on_actions',block('on_daily',block('effect','RUS_ip_daily = yes\n'))+block('on_startup',block('effect',block('every_country',block('limit','original_tag = RUS\nhas_country_flag = RUS_ip_factory_initialized\n')+'RUS_ip_refresh = yes\n'))))
    return triggers,effects,actions
