"""Deterministic, read-only-by-default Russian industrial planning prototype.

Map/assets have a separate builder. This renderer only returns relative text
paths and content. The exercise deliberately has no rewards in the real economy.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = 'RUS_ip_'
COST = {1:2, 2:2, 3:3, 4:4, 5:5}
TARGETS = [2,6,12,18,25]
LANGS = ('simp_chinese','english','russian')


def block(name, content):
    return name+' = {\n'+''.join('\t'+line+'\n' if line else '\n' for line in content.rstrip().splitlines())+'}\n'


def setv(key, value):return f'set_variable = {{ {P+key} = {value} }}\n'
def add(key, value):return f'add_to_variable = {{ {P+key} = {value} }}\n'
def sub(key, value):return f'subtract_from_variable = {{ {P+key} = {value} }}\n'
def cv(key, op, value):return f'check_variable = {{ {P+key} {op} {value} }}'
def at_least(key, value):return f'NOT = {{ {cv(key,"<",value)} }}'
def iff(condition, body):return block('if',block('limit',condition)+body)
def fx(name,body):return block(P+name,body)


def render_outputs():
    data=json.loads((ROOT/'tools/data/industrial_planning_map.json').read_text(encoding='utf-8'))
    cells=data['cells'];hub=data['hub'];n=len(cells)
    loc={lang:{} for lang in LANGS}
    def L(key,zh,en,ru=None):
        key=P+key
        for lang,text in zip(LANGS,(zh,en,ru or en)):loc[lang][key]=text
        return key
    L('title','国家计划委员会 · 工业蓝图','State Planning Commission · Industrial Blueprint','Госплан · Промышленный план')
    L('subtitle','俄罗斯工业布局沙盘  /  五轮规划与生产考核','Russian industrial planning exercise / Five production rounds','Промышленная карта России / Пять этапов')
    L('open_tt','§Y工业规划沙盘§!\n在俄罗斯地图上建设工业与铁路，完成五轮生产目标。独立演算，可随时关闭并继续。','§YIndustrial planning§!\nBuild industry and rail on the Russian map. Complete five production rounds. Closing preserves your exercise.')
    L('summary','第 §Y[?RUS_ip_round|0]§! / 5 轮   |   投资 §Y[?RUS_ip_budget|0]§!   |   累计机械 §G[?RUS_ip_machines|0]§!   |   考核 §Y[?RUS_ip_score|0]§! 分','Round §Y[?RUS_ip_round|0]§! / 5  |  Investment §Y[?RUS_ip_budget|0]§!  |  Machines §G[?RUS_ip_machines|0]§!  |  Score §Y[?RUS_ip_score|0]§!')
    L('stocks','库存    煤 [?RUS_ip_coal|0]    铁 [?RUS_ip_iron|0]    钢 [?RUS_ip_steel|0]\n本轮预计    钢 +[?RUS_ip_steel_output|0]    机械 +[?RUS_ip_machine_output|0]','Stocks    Coal [?RUS_ip_coal|0]    Iron [?RUS_ip_iron|0]    Steel [?RUS_ip_steel|0]\nForecast    Steel +[?RUS_ip_steel_output|0]    Machines +[?RUS_ip_machine_output|0]')
    L('network','接通地块 [?RUS_ip_connected_count|0] / '+str(n)+'    |    供电 [?RUS_ip_power_total|0] / 需求 [?RUS_ip_power_demand|0]    |    加工运力 [?RUS_ip_transport_total|0]','Connected [?RUS_ip_connected_count|0] / '+str(n)+'  |  Power [?RUS_ip_power_total|0] / demand [?RUS_ip_power_demand|0]  |  Processing transport [?RUS_ip_transport_total|0]')
    L('target','本轮目标：累计交付 §Y[?RUS_ip_target|0]§! 单位机械。预计结算后达到 §Y[?RUS_ip_next_machines|0]§!。\n达到目标获得 20 分；每轮后追加 18 投资，共五轮。','Target: §Y[?RUS_ip_target|0]§! cumulative machines. Forecast: §Y[?RUS_ip_next_machines|0]§!.\nMeet the target for 20 points. Next round grants 18 investment. Five rounds total.')
    L('instructions','点击地区编号 → 建设或升级 → 检查预测 → 结算本轮\n相邻地区的铁路接通莫斯科后投产；蓝色虚线为两处海运接驳。编号位置有引线对应地区。','Click district number → Build or upgrade → Review forecast → Resolve round\nConnect adjacent districts to Moscow. Blue dashed links represent maritime transfer. Callout lines locate compact western districts.')
    L('sandbox_note','本沙盘独立计分与投资，可重开练习；暂不改变国家工厂或一五计划正式奖励。','This exercise uses its own investment and score. It can be replayed and does not alter national factories or Five-Year Plan rewards.')
    L('legend','煤：煤矿   铁：铁矿   电：电站   钢：钢铁厂   机：机械厂   ★：莫斯科枢纽','C: coal  I: iron  P: power  S: steel  M: machinery  ★: Moscow hub')
    L('selected','[GetRUSIPDistrict]','[GetRUSIPDistrict]')
    L('detail','设施：[GetRUSIPSelectedType]  §Y[?RUS_ip_sel_level|0]§! 级\n铁路：§Y[?RUS_ip_sel_rail|0]§! 级    [GetRUSIPSelectedStatus]\n煤矿潜力：[GetRUSIPCoalPotential]\n铁矿潜力：[GetRUSIPIronPotential]\n\n经营资格以地区中心的控制权为准。\n设施与铁路分别建设，最高三级。','Facility: [GetRUSIPSelectedType]  level §Y[?RUS_ip_sel_level|0]§!\nRail: level §Y[?RUS_ip_sel_rail|0]§!  [GetRUSIPSelectedStatus]\nCoal potential: [GetRUSIPCoalPotential]\nIron potential: [GetRUSIPIronPotential]\n\nControl is checked at the named centre.\nFacility and rail each have three levels.')
    L('status_0','§g无铁路§!','§gNo rail§!');L('status_1','§R不在控制下§!','§RNot controlled§!');L('status_2','§R尚未连通§!','§RDisconnected§!');L('status_3','§G已接通枢纽§!','§GConnected§!')
    L('yes','§G有§!','§GYes§!');L('no','§g无§!','§gNo§!')
    names=[('空地','Empty','Пусто'),('煤矿','Coal mine','Угольная шахта'),('铁矿','Iron mine','Железный рудник'),('电站','Power station','Электростанция'),('钢铁厂','Steelworks','Металлургия'),('机械厂','Machinery works','Машиностроение')]
    short=['·','煤','铁','电','钢','机'];short_en=['·','C','I','P','S','M']
    for kind,(zh,en,ru) in enumerate(names):
        L(f'type_{kind}',zh,en,ru);L(f'short_{kind}',short[kind],short_en[kind])
    rates={1:('每级每轮生产 3 煤。需要煤矿潜力。','Each level produces 3 coal per round. Requires coal potential.'),2:('每级每轮生产 3 铁。需要铁矿潜力。','Each level produces 3 iron per round. Requires iron potential.'),3:('每级每轮消耗 1 煤，提供 6 电力。','Each level burns 1 coal for 6 power per round.'),4:('每级每轮最多生产 2 钢。每单位消耗 1 煤、1 铁、2 电力、1 运力。','Each level produces up to 2 steel. Each unit uses 1 coal, 1 iron, 2 power and 1 transport.'),5:('每级每轮最多生产 2 机械。每单位消耗 2 钢、1 电力、1 运力。','Each level produces up to 2 machines. Each unit uses 2 steel, 1 power and 1 transport.')}
    for kind in COST:
        L(f'build_{kind}',names[kind][0]+f'  {COST[kind]}',names[kind][1]+f'  {COST[kind]}')
        L(f'build_{kind}_tt',f'§Y建设或升级{names[kind][0]}§!\n消耗 {COST[kind]} 投资。{rates[kind][0]}\n须为空地或同类设施，且由俄罗斯拥有并控制。设施与铁路均最高三级。',f'§YBuild or upgrade {names[kind][1]}§!\nCost: {COST[kind]} investment. {rates[kind][1]}\nRequires an empty district or the same facility, owned and controlled by Russia. Maximum level 3.')
    L('rail','铁路  2','Rail  2','Ж/д  2');L('rail_tt','§Y建设或升级铁路§!\n消耗 2 投资。相邻有铁路的地块自动连通；连接莫斯科后，每级增加 2 加工运力。','§YBuild or upgrade rail§!\nCosts 2 investment. Adjacent rail connects automatically. Each level connected to Moscow adds 2 processing transport.')
    L('remove','拆除设施','Remove facility','Снести завод');L('remove_rail','拆除铁路','Remove rail','Снять ж/д')
    L('remove_tt','移除选中设施，返还本局在该设施上实际支付的投资。起始设施不产生退款。','Remove this facility and refund investment actually paid into it this exercise. Free starting facilities have no refund.')
    L('remove_rail_tt','移除选中地块的铁路，返还实际支付的投资。下游设施可能失去连接。','Remove this rail and refund investment actually paid. Downstream districts may lose their connection.')
    L('settle','结算本轮','Resolve round','Завершить этап');L('settle_tt','重新核对领土与铁路连接，按预测生产并消耗原料。\n本轮只结算一次；五轮结束后显示总成绩。','Recheck territorial control and rail connections, then consume inputs and resolve production.\nEach round resolves once; the exercise ends after five rounds.')
    L('refresh','刷新预测','Refresh forecast','Обновить прогноз');L('refresh_tt','重新核对领土、铁路和产量预测，不推进轮次、不结算生产。','Recheck territory, rail and output forecasts without advancing or producing.')
    L('restart','重新规划','New exercise','Новый план');L('restart_confirm','确认重新规划','Confirm restart','Подтвердить')
    L('restart_tt','重新开始五轮演算。第一次点击显示确认按钮；再次确认后，清空本沙盘的布局、库存与成绩。','Start a new five-round exercise. Click once to reveal confirmation; confirm again to clear only this exercise layout, stocks and score.')
    L('finished','§Y五轮规划结束§!   累计机械：[?RUS_ip_machines|0]   考核：[?RUS_ip_score|0] / 100 分\n可继续查看地图，或点击“重新规划”再进行一局。','§YFive rounds complete§!   Machines: [?RUS_ip_machines|0]   Score: [?RUS_ip_score|0] / 100\nInspect the map or start another exercise.')
    L('bottlenecks','瓶颈：[GetRUSIPBottleneck]\n采矿 → 发电 → 炼钢 → 机械\n电力当轮使用，原料与成品留存。','Bottleneck: [GetRUSIPBottleneck]\nMining → Power → Steel → Machinery\nPower expires. Material stocks persist.')
    for key,zh,en in [('power','§R电力不足§!','§RPower shortage§!'),('coal','§R煤炭不足§!','§RCoal shortage§!'),('iron','§R铁矿不足§!','§RIron shortage§!'),('steel','§R钢材不足§!','§RSteel shortage§!'),('transport','§R加工运力不足§!','§RTransport shortage§!'),('clear','§G当前生产能力均可利用§!','§GAll connected production capacity can be used§!'),('idle','§g尚无接通的加工设施§!','§gNo connected processing facilities§!')]:L('bottleneck_'+key,zh,en)

    triggers=[fx('available','original_tag = RUS\nis_ai = no\n'),fx('editing','RUS_ip_available = yes\nhas_country_flag = RUS_ip_initialized\nhas_country_flag = RUS_ip_open\nNOT = { has_country_flag = RUS_ip_finished }\n')]
    for c in cells:
        i=c['id'];triggers.append(fx(f'owned_{i}',f'owns_state = {c["state"]}\ncontrols_state = {c["state"]}\n'))
    def eligible(i,kind):
        out=f'RUS_ip_owned_{i} = yes\n'+cv(f'n{i}_level','<',3)+'\n'+block('OR',cv(f'n{i}_type','=',0)+'\n'+cv(f'n{i}_type','=',kind))
        if kind in (1,2) and not cells[i]['coal' if kind==1 else 'iron']:out+='always = no\n'
        return out
    for kind,cost in COST.items():
        cond='RUS_ip_editing = yes\n'+at_least('budget',cost)+'\n'+block('OR',''.join(block('AND',cv('selected','=',c['id'])+'\n'+eligible(c['id'],kind)) for c in cells))
        triggers.append(fx(f'can_build_{kind}',cond))
    for name,cell_cond,money in [('rail',lambda i:cv(f'n{i}_rail','<',3),2),('remove',lambda i:cv(f'n{i}_level','>',0),0),('remove_rail',lambda i:cv(f'n{i}_rail','>',0),0)]:
        cond='RUS_ip_editing = yes\n'+at_least('budget',money)+'\n'+block('OR',''.join(block('AND',cv('selected','=',c['id'])+f'\nRUS_ip_owned_{c["id"]} = yes\n'+cell_cond(c['id'])) for c in cells))
        triggers.append(fx('can_'+name,cond))

    init='set_country_flag = RUS_ip_initialized\nclr_country_flag = RUS_ip_finished\nclr_country_flag = RUS_ip_restart_armed\n'
    for k,v in dict(round=1,budget=24,coal=6,iron=4,steel=2,machines=0,score=0,target=2,selected=hub).items():init+=setv(k,v)
    for c in cells:
        i=c['id'];kind=data['starter'].get(str(i),0)
        for k,v in dict(type=kind,level=int(kind>0),paid=0,rail=int(i in data['starter_rails']),rail_paid=0).items():init+=setv(f'n{i}_{k}',v)
    effects=[fx('initialize',init+'RUS_ip_refresh = yes\n')]
    effects.append(fx('open_effect',iff('RUS_ip_available = yes',iff('NOT = { has_country_flag = RUS_ip_initialized }','RUS_ip_initialize = yes\n')+'set_country_flag = RUS_ip_open\nclr_country_flag = RUS_ip_restart_armed\nRUS_ip_refresh = yes\n')))
    effects.append(fx('close_effect','clr_country_flag = RUS_ip_open\nclr_country_flag = RUS_ip_restart_armed\n'+add('dirty',1)))
    effects.append(fx('toggle',iff('RUS_ip_available = yes',iff('has_country_flag = RUS_ip_open','RUS_ip_close_effect = yes\n')+block('else','RUS_ip_open_effect = yes\n'))))

    # Reachability is recomputed only on interaction. No daily/global polling.
    refresh=''
    for c in cells:
        i=c['id'];refresh+=setv(f'n{i}_connected',0)+setv(f'n{i}_status',1)+iff(f'RUS_ip_owned_{i} = yes',setv(f'n{i}_status',0)+iff(cv(f'n{i}_rail','>',0),setv(f'n{i}_status',2)))
    refresh+=iff(f'RUS_ip_owned_{hub} = yes\n'+cv(f'n{hub}_rail','>',0),setv(f'n{hub}_connected',1))
    refresh+=setv('changed',1)+setv('iterations',0)
    flood=''
    for c in cells:
        i=c['id'];neighbors=block('OR','\n'.join(cv(f'n{j}_connected','=',1) for j in c['neighbors']))
        cond=f'RUS_ip_owned_{i} = yes\n'+cv(f'n{i}_rail','>',0)+'\n'+cv(f'n{i}_connected','=',0)+'\n'+neighbors
        flood+=iff(cond,setv(f'n{i}_connected',1)+setv('changed',1))
    refresh+=block('while_loop_effect',block('limit',cv('changed','=',1)+'\n'+cv('iterations','<',n))+setv('changed',0)+flood+add('iterations',1))
    for k in ['connected_count','coal_capacity','iron_capacity','power_capacity','steel_capacity','machine_capacity','transport_total']:refresh+=setv(k,0)
    for c in cells:
        i=c['id'];body=setv(f'n{i}_status',3)+add('connected_count',1)+add('transport_total',P+f'n{i}_rail')+add('transport_total',P+f'n{i}_rail')
        for kind,key,mult in [(1,'coal_capacity',3),(2,'iron_capacity',3),(3,'power_capacity',1),(4,'steel_capacity',2),(5,'machine_capacity',2)]:
            body+=iff(cv(f'n{i}_type','=',kind),''.join(add(key,P+f'n{i}_level') for _ in range(mult)))
        refresh+=iff(cv(f'n{i}_connected','=',1),body)
    refresh+='RUS_ip_forecast = yes\nRUS_ip_selection_cache = yes\n'+add('dirty',1)
    effects.append(fx('refresh',refresh))

    forecast=setv('next_coal',P+'coal')+add('next_coal',P+'coal_capacity')+setv('next_iron',P+'iron')+add('next_iron',P+'iron_capacity')+setv('next_steel',P+'steel')+setv('next_machines',P+'machines')
    forecast+=setv('power_total',0)+setv('power_left',0)+setv('transport_left',P+'transport_total')+setv('power_runs',0)+setv('steel_output',0)+setv('machine_output',0)+setv('bottleneck',0)
    forecast+=block('while_loop_effect',block('limit',cv('power_runs','<',P+'power_capacity')+'\n'+at_least('next_coal',1))+sub('next_coal',1)+add('power_total',6)+add('power_runs',1))
    forecast+=setv('power_left',P+'power_total')+setv('power_demand',P+'steel_capacity')+add('power_demand',P+'steel_capacity')+add('power_demand',P+'machine_capacity')
    forecast+=block('while_loop_effect',block('limit','\n'.join([cv('steel_output','<',P+'steel_capacity'),at_least('next_coal',1),at_least('next_iron',1),at_least('power_left',2),at_least('transport_left',1)]))+sub('next_coal',1)+sub('next_iron',1)+sub('power_left',2)+sub('transport_left',1)+add('next_steel',1)+add('steel_output',1))
    forecast+=block('while_loop_effect',block('limit','\n'.join([cv('machine_output','<',P+'machine_capacity'),at_least('next_steel',2),at_least('power_left',1),at_least('transport_left',1)]))+sub('next_steel',2)+sub('power_left',1)+sub('transport_left',1)+add('next_machines',1)+add('machine_output',1))
    # Show the first actionable shortage. Full requirements remain in tooltips.
    shortage=block('OR',cv('steel_output','<',P+'steel_capacity')+'\n'+cv('machine_output','<',P+'machine_capacity'))
    tests=[(1,cv('transport_left','<',1)),(2,cv('power_left','<',1)),(3,cv('next_coal','<',1)+'\n'+cv('steel_output','<',P+'steel_capacity')),(4,cv('next_iron','<',1)+'\n'+cv('steel_output','<',P+'steel_capacity')),(5,cv('next_steel','<',2)+'\n'+cv('machine_output','<',P+'machine_capacity'))]
    branch=''
    for index,(value,condition) in enumerate(tests):branch+=block('if' if index==0 else 'else_if',block('limit',condition)+setv('bottleneck',value))
    # Steel needs two units of power even when one remains.
    branch+=block('else',setv('bottleneck',2))
    forecast+=iff(shortage,branch)+iff(cv('steel_capacity','=',0)+'\n'+cv('machine_capacity','=',0),setv('bottleneck',6))
    effects.append(fx('forecast',forecast))
    cache=''
    for c in cells:
        i=c['id'];body=''.join(setv('sel_'+k,P+f'n{i}_{k}') for k in ['type','level','rail','status'])+setv('sel_coal',c['coal'])+setv('sel_iron',c['iron'])
        cache+=iff(cv('selected','=',i),body)
    effects.append(fx('selection_cache',cache))
    for kind,cost in COST.items():
        body=''
        for c in cells:
            i=c['id'];body+=iff(cv('selected','=',i)+'\n'+eligible(i,kind),setv(f'n{i}_type',kind)+add(f'n{i}_level',1)+add(f'n{i}_paid',cost)+sub('budget',cost))
        effects.append(fx(f'build_{kind}',iff(f'RUS_ip_can_build_{kind} = yes',body+'clr_country_flag = RUS_ip_restart_armed\nRUS_ip_refresh = yes\n')))
    for action in ['rail','remove','remove_rail']:
        body=''
        for c in cells:
            i=c['id']
            if action=='rail':change=add(f'n{i}_rail',1)+add(f'n{i}_rail_paid',2)+sub('budget',2)
            elif action=='remove':change=add('budget',P+f'n{i}_paid')+setv(f'n{i}_paid',0)+setv(f'n{i}_type',0)+setv(f'n{i}_level',0)
            else:change=add('budget',P+f'n{i}_rail_paid')+setv(f'n{i}_rail_paid',0)+setv(f'n{i}_rail',0)
            body+=iff(cv('selected','=',i)+f'\nRUS_ip_owned_{i} = yes',change)
        effects.append(fx(action,iff(f'RUS_ip_can_{action} = yes',body+'clr_country_flag = RUS_ip_restart_armed\nRUS_ip_refresh = yes\n')))
    settle='RUS_ip_refresh = yes\n'+''.join(setv(k,P+'next_'+k) for k in ['coal','iron','steel','machines'])
    settle+=iff(at_least('machines',P+'target'),add('score',20))
    settle+=iff(cv('round','<',5),add('round',1)+add('budget',18))+block('else','set_country_flag = RUS_ip_finished\n')
    for i,target in enumerate(TARGETS,1):settle+=iff(cv('round','=',i),setv('target',target))
    settle+='clr_country_flag = RUS_ip_restart_armed\nRUS_ip_refresh = yes\n'
    effects.append(fx('settle',iff('RUS_ip_editing = yes',settle)))
    effects.append(fx('arm_restart',iff('RUS_ip_available = yes\nhas_country_flag = RUS_ip_open','set_country_flag = RUS_ip_restart_armed\n'+add('dirty',1))))
    effects.append(fx('confirm_restart',iff('RUS_ip_available = yes\nhas_country_flag = RUS_ip_open\nhas_country_flag = RUS_ip_restart_armed','RUS_ip_initialize = yes\n')))

    defined=[]
    def defined_text(name,branches):
        defined.append(block('defined_text',f'name = {name}\n'+''.join(block('text',(block('trigger',cond) if cond else '')+f'localization_key = {key}\n') for cond,key in branches)))
    defined_text('GetRUSIPSelectedType',[(cv('sel_type','=',k),P+f'type_{k}') for k in range(1,6)]+[('',P+'type_0')])
    defined_text('GetRUSIPSelectedStatus',[(cv('sel_status','=',k),P+f'status_{k}') for k in range(1,4)]+[('',P+'status_0')])
    for key in ['coal','iron']:defined_text('GetRUSIP'+key.title()+'Potential',[(cv('sel_'+key,'=',1),P+'yes'),('',P+'no')])
    defined_text('GetRUSIPBottleneck',[(cv('bottleneck','=',i),P+'bottleneck_'+key) for i,key in enumerate(['transport','power','coal','iron','steel','idle'],1)]+[('',P+'bottleneck_clear')])
    for c in cells:
        i=c['id'];L(f'district_{i}',f'地块 {i+1:02} · $STATE_{c["state"]}$',f'District {i+1:02} · $STATE_{c["state"]}$')
        L(f'node_{i}',f'[GetRUSIPType{i}]  [?RUS_ip_n{i}_level|0]',f'[GetRUSIPType{i}]  [?RUS_ip_n{i}_level|0]')
        zh=f'§Y地块 {i+1:02} · $STATE_{c["state"]}$§!\n设施：[GetRUSIPType{i}]  [?RUS_ip_n{i}_level|0] 级\n铁路：[?RUS_ip_n{i}_rail|0] 级\n煤矿潜力：'+('有' if c['coal'] else '无')+'  /  铁矿潜力：'+('有' if c['iron'] else '无')
        en=f'§YDistrict {i+1:02} · $STATE_{c["state"]}$§!\nFacility: [GetRUSIPType{i}] level [?RUS_ip_n{i}_level|0]\nRail: level [?RUS_ip_n{i}_rail|0]\nCoal potential: {c["coal"]} / Iron potential: {c["iron"]}'
        L(f'node_{i}_tt',zh,en)
        defined_text(f'GetRUSIPType{i}',[(cv(f'n{i}_type','=',k),P+f'short_{k}') for k in range(1,6)]+[('',P+'short_0')])
    defined_text('GetRUSIPDistrict',[(cv('selected','=',c['id']),P+f'district_{c["id"]}') for c in cells]+[('',P+f'district_{hub}')])

    # Same raid-filter attachment as agriculture, one separate slot to its left.
    launchers=[];launcher_scripts=[]
    for suffix,y,condition in [('',-121,'NOT = { GER_is_in_mitteleuropa = yes }'),('_above_mitteleuropa',-198,'GER_is_in_mitteleuropa = yes')]:
        launchers.append(block('containerWindowType',f'name = "RUS_industrial_planning_launcher{suffix}"\nposition = {{ x = -79 y = {y} }}\nsize = {{ width = 77 height = 77 }}\nbackground = {{ name = "Background" quadTextureSprite = "GFX_equipment_role_selector_tiled_window" }}\nbackground = {{ name = "Background" quadTextureSprite = "GFX_tiled_research_bg" }}\nbuttonType = {{ name = "ip_open" position = {{ x = 9 y = 7 }} scale = 1.8 quadTextureSprite = "GFX_decision_generic_industry" pdx_tooltip = "RUS_ip_open_tt" clicksound = click_ok }}\n'))
        launcher_scripts.append(block('RUS_industrial_planning_launcher'+suffix,f'context_type = player_context\nparent_window_name = raid_filter\nwindow_name = "RUS_industrial_planning_launcher{suffix}"\nai_enabled = {{ always = no }}\n'+block('visible','RUS_ip_available = yes\n'+condition)+block('effects','ip_open_click = { hidden_effect = { RUS_ip_toggle = yes } }')))
    widgets=[];gt=[];ge=[]
    def horizontal(x,w=None):
        # Compact 1184 px window; the detail panel sits beside the 816 px map.
        return (x-108 if x>=960 else x, w-108 if w is not None and w>900 else w)
    def text(name,key,x,y,w,h=24,font='hoi_16mbs',center=False):
        x,w=horizontal(x,w)
        widgets.append(f'instantTextBoxType = {{ name = "{name}" position = {{ x = {x} y = {y} }} text = "{key}" font = "{font}" maxWidth = {w} maxHeight = {h} format = {"center" if center else "left"} fixedsize = yes alwaystransparent = yes }}\n')
    def button(name,key,x,y,tip,action,enable='',sprite='GFX_button_123x34'):
        x,_=horizontal(x)
        widgets.append(f'buttonType = {{ name = "{name}" position = {{ x = {x} y = {y} }} quadTextureSprite = "{sprite}" buttonText = "{key}" buttonFont = "hoi_16mbs" pdx_tooltip = "{tip}" clicksound = click_default }}\n')
        if enable:gt.append(block(name+'_click_enabled',enable))
        ge.append(block(name+'_click',block('hidden_effect',action)))
    def icon(name,sprite,x,y):widgets.append(f'iconType = {{ name = "{name}" position = {{ x = {x} y = {y} }} spriteType = "{sprite}" alwaystransparent = yes }}\n')
    text('ip_title',P+'title',24,12,1200,32,'hoi_24header',True)
    text('ip_subtitle',P+'subtitle',24,46,920,24)
    text('ip_summary',P+'summary',24,77,920,25,'hoi_20b')
    text('ip_network',P+'network',24,108,920,23)
    mx,my=20,140
    icon('ip_map','GFX_RUS_ip_map',mx,my)
    for edge in data['edge_sprites']:
        i,j=edge['a'],edge['b']
        icon(f'ip_link_{i}_{j}',f'GFX_RUS_ip_link_{i}_{j}',mx+edge['x'],my+edge['y'])
        gt.append(block(f'ip_link_{i}_{j}_visible',cv(f'n{i}_rail','>',0)+'\n'+cv(f'n{j}_rail','>',0)+f'\nRUS_ip_owned_{i} = yes\nRUS_ip_owned_{j} = yes'))
    for c in cells:
        i=c['id'];icon(f'ip_region_{i}',f'GFX_RUS_ip_region_{i}',mx+c['bbox'][0],my+c['bbox'][1])
        gt.append(block(f'ip_region_{i}_visible',cv('selected','=',i)))
    for c in cells:
        i=c['id'];x,y=mx+c['x']-20,my+c['y']-19
        button(f'ip_cell_{i}','',x,y,P+f'node_{i}_tt',iff('RUS_ip_available = yes\nhas_country_flag = RUS_ip_open',setv('selected',i)+'clr_country_flag = RUS_ip_restart_armed\nRUS_ip_refresh = yes\n'),sprite='GFX_RUS_ip_cell_button')
        for status,sprite,cond in [('selected','selected',cv('selected','=',i)),('connected','connected',cv(f'n{i}_connected','=',1)),('offline','offline',block('OR',cv(f'n{i}_status','=',1)+'\n'+block('AND',cv(f'n{i}_level','>',0)+'\n'+cv(f'n{i}_connected','=',0))))]:
            icon(f'ip_{status}_{i}','GFX_RUS_ip_'+sprite,x,y);gt.append(block(f'ip_{status}_{i}_visible',cond))
        text(f'ip_number_{i}',f'{i+1:02}',x+1,y+1,38,18,'hoi_16mbs',True)
        text(f'ip_node_{i}',P+f'node_{i}',x+1,y+18,38,20,'hoi_16mbs',True)
    text('ip_hub','★',mx+cells[hub]['x']-37,my+cells[hub]['y']-12,20,24,'hoi_20b')
    text('ip_legend',P+'legend',24,579,925,24)
    text('ip_target',P+'target',24,610,925,45)
    text('ip_instructions',P+'instructions',24,668,925,42)
    text('ip_selected',P+'selected',976,62,288,42,'hoi_20b')
    text('ip_detail',P+'detail',976,105,285,160)
    for kind,(x,y) in {1:(976,268),2:(1116,268),3:(976,309),4:(1116,309),5:(976,350)}.items():
        button(f'ip_build_{kind}',P+f'build_{kind}',x,y,P+f'build_{kind}_tt',f'RUS_ip_build_{kind} = yes',f'RUS_ip_can_build_{kind} = yes')
    button('ip_rail',P+'rail',1116,350,P+'rail_tt','RUS_ip_rail = yes','RUS_ip_can_rail = yes')
    button('ip_remove',P+'remove',976,392,P+'remove_tt','RUS_ip_remove = yes','RUS_ip_can_remove = yes')
    button('ip_remove_rail',P+'remove_rail',1116,392,P+'remove_rail_tt','RUS_ip_remove_rail = yes','RUS_ip_can_remove_rail = yes')
    text('ip_stocks',P+'stocks',976,443,285,55)
    text('ip_bottlenecks',P+'bottlenecks',976,504,285,66)
    button('ip_refresh',P+'refresh',976,578,P+'refresh_tt',iff('RUS_ip_available = yes\nhas_country_flag = RUS_ip_open','RUS_ip_refresh = yes\n'))
    button('ip_settle',P+'settle',1116,578,P+'settle_tt','RUS_ip_settle = yes','RUS_ip_editing = yes')
    button('ip_restart',P+'restart',976,620,P+'restart_tt','RUS_ip_arm_restart = yes')
    button('ip_restart_confirm',P+'restart_confirm',976,620,P+'restart_tt','RUS_ip_confirm_restart = yes')
    gt.extend([block('ip_restart_visible','NOT = { has_country_flag = RUS_ip_restart_armed }'),block('ip_restart_confirm_visible','has_country_flag = RUS_ip_restart_armed')])
    text('ip_sandbox_note',P+'sandbox_note',976,663,285,53)
    # Result replaces the target line, leaving all map inspection controls usable.
    gt.append(block('ip_target_visible','NOT = { has_country_flag = RUS_ip_finished }'))
    text('ip_final',P+'finished',24,610,925,46)
    gt.append(block('ip_final_visible','has_country_flag = RUS_ip_finished'))
    widgets.append('buttonType = { name = "ip_close" position = { x = 1138 y = 9 } spriteType = "GFX_closebutton" pdx_tooltip = "CLOSE" shortcut = "ESCAPE" clicksound = click_close }\n')
    ge.append(block('ip_close_click','hidden_effect = { RUS_ip_close_effect = yes }'))
    frame='name = "RUS_industrial_planning_window"\nposition = { x = -592 y = -363 }\nsize = { width = 1184 height = 726 }\norientation = center\nmoveable = yes\nclick_to_front = yes\nshow_sound = menu_open_window\nhide_sound = menu_close_window\nbackground = { name = "frame" quadTextureSprite = "GFX_tiled_plain_bg" }\n'
    frame+=block('containerWindowType','name = "ip_details_bg"\nposition = { x = 852 y = 49 }\nsize = { width = 316 height = 668 }\nbackground = { name = "detail" quadTextureSprite = "GFX_tiled_research_bg" }\n')
    gui=block('guiTypes',''.join(launchers)+block('containerWindowType',frame+''.join(widgets)))
    script='context_type = player_context\nwindow_name = "RUS_industrial_planning_window"\ndirty = RUS_ip_dirty\nai_enabled = { always = no }\n'+block('visible','RUS_ip_available = yes\nhas_country_flag = RUS_ip_open')+block('triggers',''.join(gt))+block('effects',''.join(ge))
    gfx=[]
    for name in ['map','selected','offline','connected','cell_button']+[f'region_{c["id"]}' for c in cells]+[f'link_{e["a"]}_{e["b"]}' for e in data['edge_sprites']]:
        gfx.append(block('spriteType',f'name = "GFX_RUS_ip_{name}"\ntexturefile = "gfx/interface/RUS_industrial_planning/{name}.png"\n'+('noOfFrames = 3\n' if name=='cell_button' else '')+'transparencecheck = yes\n'))
    header='# Generated by tools/generate_industrial_planning.py. Edit the renderer, then --write.\n'
    outputs={'common/scripted_triggers/RUS_industrial_planning_triggers.txt':header+'\n'.join(triggers),
             'common/scripted_effects/RUS_industrial_planning_effects.txt':header+'\n'.join(effects),
             'common/scripted_guis/RUS_industrial_planning.txt':header+block('scripted_gui',''.join(launcher_scripts)+block('RUS_industrial_planning_gui',script)),
             'common/scripted_localisation/RUS_industrial_planning_loc.txt':header+'\n'.join(defined),
             'interface/RUS_industrial_planning.gui':header+gui,
             'interface/RUS_industrial_planning.gfx':header+block('spriteTypes',''.join(gfx))}
    for lang,catalog in loc.items():outputs[f'localisation/{lang}/RUS_industrial_planning_l_{lang}.yml']='l_'+lang+':\n'+''.join(f' {key}:0 "{value.replace(chr(10),r"\n")}"\n' for key,value in catalog.items())
    return outputs


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group();mode.add_argument('--check',action='store_true');mode.add_argument('--write',action='store_true')
    parser.add_argument('--output-root',type=Path);args=parser.parse_args()
    if args.check and args.output_root:parser.error('--check cannot write --output-root')
    out=(args.output_root or ROOT).resolve();outputs=render_outputs();assert outputs==render_outputs(),'Non-deterministic output'
    differences=[]
    for rel,text in outputs.items():
        target=(out/rel).resolve();assert target.is_relative_to(out)
        data=text.encode('utf-8-sig' if rel.endswith('.yml') else 'utf-8')
        actual=target.read_bytes().replace(b'\r\n',b'\n') if target.is_file() else None
        if data!=actual:
            differences.append(rel)
            if args.write or args.output_root:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    print(f'{"Generated" if args.write or args.output_root else "Checked"} {len(outputs)} files; {len(differences)} differences.')
    if differences and not (args.write or args.output_root):raise SystemExit('\n'.join(differences))


if __name__=='__main__':main()
