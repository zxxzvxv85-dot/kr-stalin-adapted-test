"""Render independent industrial construction. Read-only unless --write.

The map builder and economy renderer are separate; the original Five-Year Plan
is deliberately neither an input nor an output of this prototype.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from industrial_planning_economy import P, PROJECTS, block, setv, add, cv, iff, rail_spec, render_economy

ROOT = Path(__file__).resolve().parents[1]
LANGS = ('simp_chinese', 'english', 'russian')
ICONS = {1:'decision_coal', 2:'decision_steel', 3:'decision_generic_electricity',
         4:'decision_generic_factory', 5:'decision_generic_industry', 6:'decision_generic_train'}


def render_outputs():
    data = json.loads((ROOT/'tools/data/industrial_planning_map.json').read_text(encoding='utf-8'))
    cells, hub = data['cells'], data['hub']
    triggers, effects, actions, modifier, rewards = render_economy(data)
    loc = {lang:{} for lang in LANGS}
    def L(key, zh, en, ru=None):
        for lang, content in zip(LANGS, (zh, en, ru or en)): loc[lang][P+key] = content
        return P+key
    L('title','国家计划委员会 · 工业建设','State Planning Commission · Industrial Construction','Госплан · Промышленное строительство')
    L('subtitle','俄罗斯工业布局  /  1800 天建设计划','Russian industrial development / 1800-day programme')
    L('map_northern_limit','§gKR 地图北部边界§!','§gNorthern boundary of the KR map§!','§gСеверная граница карты KR§!')
    L('open_tt','§Y工业建设§!\n在俄罗斯地图上安排工程，按游戏日期建设真实工厂、资源与交通设施。','§YIndustrial construction§!\nPlan real factories, resources and transport on the Russian map. Construction follows game time.')
    L('summary','[GetRUSIPPlanStatus]   |   已完成 §G[?RUS_ip_completed|0]§! 项工程','[GetRUSIPPlanStatus]  |  §G[?RUS_ip_completed|0]§! projects completed')
    L('not_started','§Y计划尚未启动§!','§YProgramme not started§!')
    L('active','剩余 §Y[?RUS_ip_days_left|0]§! 天','§Y[?RUS_ip_days_left|0]§! days remaining')
    L('ended','§Y本期建设计划已结束§!','§YConstruction programme concluded§!')
    L('network','接通莫斯科 [?RUS_ip_connected_count|0] / 36 区   |   全国供电满足率 [?RUS_ip_energy_percent|0]%   |   施工 [?RUS_ip_running|0] / 排队 [?RUS_ip_queued|0]','Linked to Moscow [?RUS_ip_connected_count|0] / 36  |  Power [?RUS_ip_energy_percent|0]%  |  Working [?RUS_ip_running|0] / queued [?RUS_ip_queued|0]')
    L('capacity','可用于新工程：民工 §Y[?RUS_ip_free_civs|0]§!   钢 §Y[?RUS_ip_free_steel|0]§!   煤 §Y[?RUS_ip_free_coal|0]§!','Available: civs §Y[?RUS_ip_free_civs|0]§!  steel §Y[?RUS_ip_free_steel|0]§!  coal §Y[?RUS_ip_free_coal|0]§!')
    L('footnote','每区可同时安排一项工程。已竣工的工厂与资源保留在地图上。','One queued project per district. Completed buildings and resources remain on the world map.')
    L('selected','[GetRUSIPDistrict]','[GetRUSIPDistrict]')
    L('detail','基础设施 [?RUS_ip_sel_infra|0]   民工 [?RUS_ip_sel_civs|0]   军工 [?RUS_ip_sel_mil|0]\n煤 [?RUS_ip_sel_coal|0]   钢 [?RUS_ip_sel_steel|0]   电网 [?RUS_ip_sel_grid|0]\n铁路 [?RUS_ip_sel_rail|0] 级   [GetRUSIPConnection]\n当地运力 [?RUS_ip_sel_freight|1]','Infrastructure [?RUS_ip_sel_infra|0]  Civs [?RUS_ip_sel_civs|0]  Arms [?RUS_ip_sel_mil|0]\nCoal [?RUS_ip_sel_coal|0]  Steel [?RUS_ip_sel_steel|0]  Grid [?RUS_ip_sel_grid|0]\nRail level [?RUS_ip_sel_rail|0]  [GetRUSIPConnection]\nLocal freight [?RUS_ip_sel_freight|1]')
    L('connected','§G接通莫斯科§!','§GConnected§!'); L('disconnected','§R尚未接通§!','§RDisconnected§!')
    L('project','[GetRUSIPSelectedType]  ·  [GetRUSIPSelectedStatus]','[GetRUSIPSelectedType] · [GetRUSIPSelectedStatus]')
    L('progress','进度 [?RUS_ip_sel_percent|0]%   [GetRUSIPEstimate]\n当前速度：每日 [?RUS_ip_sel_speed|2] 工作量','Progress [?RUS_ip_sel_percent|0]%  [GetRUSIPEstimate]\nDaily work: [?RUS_ip_sel_speed|2]')
    L('eta','约 [?RUS_ip_sel_eta|0] 天','About [?RUS_ip_sel_eta|0] days'); L('eta_unknown','工期暂无法估计','Duration unavailable')
    L('commitments','施工占用（全国）\n民工 [?RUS_ip_reserved_civs|0]   钢 [?RUS_ip_reserved_steel|0]   煤 [?RUS_ip_reserved_coal|0]\n暂停、取消或竣工后释放。','Construction commitments\nCivs [?RUS_ip_reserved_civs|0]  Steel [?RUS_ip_reserved_steel|0]  Coal [?RUS_ip_reserved_coal|0]\nReleased on pause, cancellation or completion.')
    L('construction_commitment','工业建设物资调拨','Industrial construction commitments')
    L('construction_commitment_desc','建设队伍与材料由国家计划委员会统一调拨。','The planning commission coordinates construction teams and material deliveries.')
    L('extraction_bottleneck','落后的资源开采体系','Outdated Resource Extraction')
    L('extraction_bottleneck_desc','老旧设备、粗放的开采方式与薄弱的勘探体系，阻碍着地下财富转化为工业原料。矿区扩建与开采整顿将逐步缓解这一困境。','Obsolete equipment, wasteful methods and weak prospecting prevent mineral wealth from reaching industry. Mine development and modernisation will gradually ease these problems.')
    L('extraction','[GetRUSIPExtractionStatus]','[GetRUSIPExtractionStatus]')
    L('extraction_active','战略资源获取效率惩罚 §R[?RUS_ip_resource_penalty_percent|0]%§!   |   矿业恢复目标 [?RUS_ip_mining_completed|0] / 15','Resource extraction penalty §R[?RUS_ip_resource_penalty_percent|0]%§!  |  Mine recovery [?RUS_ip_mining_completed|0] / 15')
    L('extraction_pending','开采整顿将在启动建设计划后开始。','Extraction reform begins when the programme starts.')
    L('extraction_clear','§G已消除资源开采惩罚。§!','§GExtraction penalty cleared.§!')
    L('test_category','工业建设测试','Industrial Construction Test')
    L('test_category_desc','国家计划委员会正在试行新的地区工业建设与资源调配方式。','The planning commission is testing a new approach to regional construction and resource allocation.')
    L('enable_gui','启用工业建设界面（测试）','Enable Industrial Construction GUI (Test)')
    L('enable_gui_desc','以各地区实际的工业条件为基础，筹划矿业、能源、交通与制造业建设。','Plan mining, energy, transport and manufacturing around the actual conditions of each region.')
    L('enable_gui_tt','启用地图上的工业建设入口并打开界面。建设期将在窗口内点击“启动建设计划”后开始。','Unlock the industrial map button and open the window. The programme begins only after selecting Start programme inside it.')
    L('type_0','待安排','No project')
    statuses=[(0,'空闲','Idle'),(1,'§G施工中§!','§GBuilding§!'),(2,'§R建设条件不符§!','§RSite unavailable§!'),(3,'§Y已暂停§!','§YPaused§!'),(4,'§R铁路未接通§!','§RRail disconnected§!'),(5,'§R等待工厂或物资§!','§RAwaiting capacity§!')]
    for k,zh,en in statuses: L(f'status_{k}',zh,en)
    for k,s in PROJECTS.items():
        L(f'type_{k}',s['zh'],s['en']); L(f'build_{k}',s['zh'],{1:'Coal',2:'Iron',3:'Grid',4:'Steel',5:'Machinery',6:'Transport'}[k])
        requirement={1:'须有煤矿潜力，最多扩建三次。',2:'须有铁矿潜力，最多扩建三次。',3:'须有强化电网建设空间。',4:'须有民工槽位并接通莫斯科；缺电会减速。',5:'须有军工槽位并接通莫斯科；缺电会减速。',6:'须有基础设施空间；内陆地区需相邻已接通地区作为铁路起点。'}[k]
        L(f'build_{k}_tt',f'§Y{s["zh"]}§!\n施工期间占用 {s["civs"]} 座民工、{s["steel"]} 钢、{s["coal"]} 煤。\n基础工作量 {s["days"]}；所需当地运力 {s["freight"]}。\n{requirement}\n工程完成时获得：',f'§Y{s["en"]}§!\nReserves {s["civs"]} civilian factories, {s["steel"]} steel and {s["coal"]} coal.\nBase work {s["days"]}; freight demand {s["freight"]}.\nRequires an owned, controlled eligible site and an empty queue.\nOn completion:')
    for key,zh,en in [('start','启动建设计划','Start programme'),('refresh','刷新状态','Refresh'),('help','玩法介绍','How to play'),('back','返回地图','Back to map'),('pause','暂停／继续','Pause / resume'),('cancel','取消工程','Cancel project'),('confirm_cancel','确认取消','Confirm cancel')]: L(key,zh,en)
    L('start_tt','开始本期 1800 天建设计划，仅能启动一次。每完成一项煤矿或铁矿工程，恢复 2 个百分点的战略资源获取效率，累计 15 项后清除下述惩罚；建设期结束时清除剩余惩罚。','Begin this independent 1800-day programme once. Each completed coal or iron mine restores 2 percentage points of extraction efficiency; 15 mines clear the penalty. Any remaining penalty ends with the programme.')
    L('refresh_tt','重新核对领土、铁路与施工状态，不推进时间。全国可用建设物资每日更新。','Recheck territory, rail and work without advancing time. National capacity updates daily.')
    L('pause_tt','暂停或恢复选中工程；暂停时释放占用的工厂和物资，保留进度。','Pause or resume. Paused work releases commitments and preserves progress.')
    L('cancel_tt','再次确认后取消选中工程，清空施工进度并释放占用。已建成设施不受影响。','Confirm to discard this project progress and release commitments. Completed facilities remain.')
    L('help_title','工业建设 · 玩法介绍','Industrial construction · How to play')
    help_zh=[
        '§Y一、启动与选址§!\n先执行“启用工业建设界面（测试）”决议，再在窗口点击“启动建设计划”，开始独立的 1800 天建设期。圆点代表经济区，工程落在所示中心州；每区同时一项，可跨区并行。关闭窗口后工程继续。',
        '§Y二、真实建设与资源链§!\n启动时战略资源获取效率 −30%，每竣工一项煤矿或铁矿恢复 2 个百分点，15 项清除。煤矿产煤、铁矿产钢；电网降低工厂能耗，钢铁厂增加民工与钢，机械军工厂增加军工。具体收益见按钮原生提示。',
        '§Y三、持续占用§!\n施工持续占用真实民工与煤钢资源。缺少领土、槽位、物资或铁路条件时工程暂停。暂停、取消、完工均释放占用。国家可用物资每日核对；短缺时按地区编号依次保障施工。可手动暂停工程来调整优先级。',
        '§Y四、工期与瓶颈§!\n每日基础进度 = 1 + 基础设施 × 0.12 + 民工数量（最多 20）× 0.025 + 相关资源（最多 40）× 0.005，再乘运力与供电系数。煤矿、电网参考煤，其余参考钢。全国缺电使钢铁与机械工程减速，最低保留 25% 速度。',
        '§Y五、铁路与运输§!\n读取实际铁路是否接通莫斯科。当地运力 = 1 + 基础设施 + 铁路等级，未接通时仅为四分之一；运力不足进一步拖慢工程。钢铁与机械工程必须接通。交通建设增加基础设施并从相邻已接通的国内地区铺设一级铁路。两处海运接驳需要两端港口和至少 10 艘运输船。',
        '§Y六、竣工与期限§!\n每天自动推进一次，完工后增加真实建筑或资源；每区两类矿业各可扩建三次。建设期结束时停止未完成工程、释放占用并清除剩余开采惩罚，保留竣工成果。本窗口独立运行，暂不改变旧一五计划任务、分数与结算奖励。',
    ]
    help_en=[
        '§Y1. Start and choose a site§!\nFirst take Enable Industrial Construction GUI (Test), then Start programme in this window for an independent 1800-day period. Work is delivered to the selected central state. One queued project per district, several districts at once. Closing the window does not stop work.',
        '§Y2. Real assets and supply chains§!\nStarting applies -30% extraction efficiency. Each completed coal or iron mine restores 2 percentage points; 15 clear it. Coal mines add coal, iron mines add steel; grids lower energy needs, steelworks add civs and steel, machine works add arms factories. See native reward tooltips.',
        '§Y3. Commitments§!\nWork reserves real civilian factories, coal and steel. Invalid sites and shortages pause work. Pausing, cancelling or finishing releases commitments. Capacity updates daily; lower district numbers have priority during shortages. Pause projects to adjust priority.',
        '§Y4. Speed and bottlenecks§!\nBase daily work = 1 + infrastructure x 0.12 + civilian factories (cap 20) x 0.025 + resources (cap 40) x 0.005, multiplied by freight and power factors. Coal mines and grids use coal; others use steel. Low national power slows steel and machine works to a minimum of 25%.',
        '§Y5. Rail and transport§!\nUses real rail connections to Moscow. Freight = 1 + infrastructure + rail level, quartered if disconnected. Steel/machine works require connection. Transport adds infrastructure and a level-1 railway from a connected domestic neighbour. Maritime links require ports at both ends and at least 10 convoys.',
        '§Y6. Completion and deadline§!\nProgress advances once per day, delivering real buildings or resources. Each mine type allows three expansions. The deadline cancels unfinished work and releases commitments; completed assets remain. The original Five-Year Plan mission, score and rewards are unchanged.',
    ]
    for idx,(zh,en) in enumerate(zip(help_zh,help_en)): L(f'help_{idx}',zh,en)
    definitions=[]
    def defined(name,branches):
        definitions.append(block('defined_text',f'name = {name}\n'+''.join(block('text',(block('trigger',c) if c else '')+f'localization_key = {k}\n') for c,k in branches)))
    defined('GetRUSIPPlanStatus',[('has_country_flag = RUS_ip_active',P+'active'),('has_country_flag = RUS_ip_ended',P+'ended'),('',P+'not_started')])
    defined('GetRUSIPSelectedType',[(cv('sel_project','=',k),P+f'type_{k}') for k in PROJECTS]+[('',P+'type_0')])
    defined('GetRUSIPSelectedStatus',[(cv('sel_status','=',k),P+f'status_{k}') for k,_,_ in statuses]+[('',P+'status_0')])
    defined('GetRUSIPEstimate',[(cv('sel_running','=',1),P+'eta'),('',P+'eta_unknown')])
    defined('GetRUSIPConnection',[(cv('sel_connected','=',1),P+'connected'),('',P+'disconnected')])
    defined('GetRUSIPExtractionStatus',[('NOT = { has_country_flag = RUS_ip_started }',P+'extraction_pending'),(cv('resource_penalty','<',0),P+'extraction_active'),('',P+'extraction_clear')])
    for c in cells:
        i,state=c['id'],c['state']
        L(f'district_{i}',f'地区 {i+1:02} · [{state}.GetName]',f'District {i+1:02} · [{state}.GetName]')
        L(f'node_{i}_tt',f'§Y[{state}.GetName]§!\n工程：[GetRUSIPProject{i}]\n进度 [?RUS_ip_n{i}_percent|0]%\n基础设施 [?RUS_ip_n{i}_infra|0]  民工 [?RUS_ip_n{i}_civs|0]  军工 [?RUS_ip_n{i}_mil|0]\n煤矿潜力：'+('有' if c['coal'] else '无')+'  铁矿潜力：'+('有' if c['iron'] else '无'),f'§Y[{state}.GetName]§!\nProject: [GetRUSIPProject{i}]\nProgress [?RUS_ip_n{i}_percent|0]%\nInfrastructure [?RUS_ip_n{i}_infra|0]  Civs [?RUS_ip_n{i}_civs|0]  Arms [?RUS_ip_n{i}_mil|0]')
        defined(f'GetRUSIPProject{i}',[(cv(f'n{i}_project','=',k),P+f'type_{k}') for k in PROJECTS]+[('',P+'type_0')])
    defined('GetRUSIPDistrict',[(cv('selected','=',c['id']),P+f'district_{c["id"]}') for c in cells]+[('',P+f'district_{hub}')])
    launchers=[]; launcher_scripts=[]
    for suffix,y,condition in [('',-121,'NOT = { GER_is_in_mitteleuropa = yes }'),('_above_mitteleuropa',-198,'GER_is_in_mitteleuropa = yes')]:
        launchers.append(block('containerWindowType',f'name = "RUS_industrial_planning_launcher{suffix}"\nposition = {{ x = -79 y = {y} }}\nsize = {{ width = 77 height = 77 }}\nbackground = {{ name = "Background" quadTextureSprite = "GFX_equipment_role_selector_tiled_window" }}\nbackground = {{ name = "Background" quadTextureSprite = "GFX_tiled_research_bg" }}\nbuttonType = {{ name = "ip_open" position = {{ x = 9 y = 7 }} scale = 1.8 quadTextureSprite = "GFX_decision_generic_industry" pdx_tooltip = "RUS_ip_open_tt" clicksound = click_ok }}\n'))
        launcher_scripts.append(block('RUS_industrial_planning_launcher'+suffix,f'context_type = player_context\nparent_window_name = raid_filter\nwindow_name = "RUS_industrial_planning_launcher{suffix}"\nai_enabled = {{ always = no }}\n'+block('visible','RUS_ip_available = yes\n'+condition)+block('effects','ip_open_click = { hidden_effect = { RUS_ip_toggle = yes } }')))
    widgets=[]; gt={}; geffects=[]
    def visibility(name,condition='',page='board'):
        base='NOT = { has_country_flag = RUS_ip_help_open }\n' if page=='board' else 'has_country_flag = RUS_ip_help_open\n' if page=='help' else ''
        if base+condition: gt[name+'_visible']=base+condition
    def text(name,key,x,y,w,h=24,font='hoi_16mbs',center=False,condition='',page='board'):
        widgets.append(f'instantTextBoxType = {{ name = "{name}" position = {{ x = {x} y = {y} }} text = "{key}" font = "{font}" maxWidth = {w} maxHeight = {h} format = {"center" if center else "left"} fixedsize = yes alwaystransparent = yes }}\n'); visibility(name,condition,page)
    def icon(name,sprite,x,y,scale=1,condition='',page='board'):
        widgets.append(f'iconType = {{ name = "{name}" position = {{ x = {x} y = {y} }} spriteType = "{sprite}" scale = {scale} alwaystransparent = yes }}\n'); visibility(name,condition,page)
    def button(name,key,x,y,tip,action,enable='',sprite='GFX_button_123x34',condition='',page='board',preview=''):
        tooltip=f'pdx_tooltip = "{tip}" ' if tip else ''
        shortcut='shortcut = "ESCAPE" ' if name=='ip_close' else ''
        widgets.append(f'buttonType = {{ name = "{name}" position = {{ x = {x} y = {y} }} quadTextureSprite = "{sprite}" buttonText = "{key}" buttonFont = "hoi_16mbs" {tooltip}{shortcut}clicksound = click_default }}\n')
        if enable: gt[name+'_click_enabled']=enable
        visibility(name,condition,page); geffects.append(block(name+'_click',preview+block('hidden_effect',action)))
    text('ip_title',P+'title',24,12,1488,32,'hoi_24header',True,page='all')
    text('ip_subtitle',P+'subtitle',24,48,1120,page='all')
    text('ip_summary',P+'summary',24,79,1150,27,'hoi_20b',page='all')
    text('ip_network',P+'network',24,112,1160)
    mx,my=20,144; icon('ip_map','GFX_RUS_ip_map',mx,my)
    if data.get('northern_map_limit_y'):
        text('ip_map_northern_limit',P+'map_northern_limit',mx+284,my+16,600,24,center=True)
    for e in data['edge_sprites']:
        a,b=e['a'],e['b']; icon(f'ip_link_{a}_{b}',f'GFX_RUS_ip_link_{a}_{b}',mx+e['x'],my+e['y'],condition=cv(f'n{a}_connected','=',1)+cv(f'n{b}_connected','=',1))
    for c in cells:
        i=c['id']; icon(f'ip_region_{i}',f'GFX_RUS_ip_region_{i}',mx+c['bbox'][0],my+c['bbox'][1],condition=cv('selected','=',i))
    for c in cells:
        i=c['id']; x,y=mx+c['x']-13,my+c['y']-13
        action=iff('RUS_ip_available = yes\nhas_country_flag = RUS_ip_open',setv('selected',i)+'clr_country_flag = RUS_ip_cancel_armed\nRUS_ip_refresh = yes\n')
        button(f'ip_cell_{i}','',x,y,P+f'node_{i}_tt',action,sprite='GFX_RUS_ip_cell_button')
        icon(f'ip_selected_{i}','GFX_RUS_ip_selected',x,y,condition=cv('selected','=',i))
        icon(f'ip_offline_{i}','GFX_RUS_ip_offline',x,y,condition=cv(f'n{i}_project','>',0)+cv(f'n{i}_running','=',0))
        text(f'ip_number_{i}',f'{i+1:02}',x+1,y+4,24,20,center=True,condition=cv(f'n{i}_project','=',0)+cv(f'n{i}_last_kind','=',0))
        for k in PROJECTS:
            cond=block('OR',cv(f'n{i}_project','=',k)+block('AND',cv(f'n{i}_project','=',0)+cv(f'n{i}_last_kind','=',k)))
            icon(f'ip_facility_{i}_{k}',f'GFX_RUS_ip_facility_{k}',x+3,y+3,.625,cond)
    text('ip_capacity',P+'capacity',24,599,1150,27,'hoi_20b')
    text('ip_extraction',P+'extraction',24,638,1150)
    text('ip_footnote',P+'footnote',24,684,1000)
    button('ip_help',P+'help',1064,680,'','RUS_ip_toggle_help = yes',page='board')
    button('ip_back',P+'back',24,680,'','RUS_ip_toggle_help = yes',page='help')
    widgets.append(block('containerWindowType','name = "ip_details_bg"\nposition = { x = 1204 y = 50 }\nsize = { width = 316 height = 667 }\nbackground = { name = "detail" quadTextureSprite = "GFX_tiled_research_bg" }\n')); visibility('ip_details_bg')
    text('ip_selected',P+'selected',1220,65,284,42,'hoi_20b')
    text('ip_detail',P+'detail',1220,113,288,85)
    text('ip_project',P+'project',1220,207,285,26)
    icon('ip_progressbar','GFX_RUS_ip_progress',1220,239)
    text('ip_progress',P+'progress',1220,260,285,42)
    for k in PROJECTS:
        x,y=1220+(144 if k%2==0 else 0),312+41*((k-1)//2)
        preview_rewards=[]
        for c in cells:
            payout=rewards[c['id'],k]
            if k==6 and c['id']!=hub and c['id'] not in {b for a,b in data['sea_edges']}:
                # Before queueing, preview the same first valid neighbour that
                # build_6 will store. effect_tooltip never executes construction.
                branches=''
                for j in c['neighbors']:
                    if sorted((c['id'],j)) in data['sea_edges']: continue
                    cond=cv(f'n{j}_connected','=',1)+f'RUS_ip_owned_{j} = yes\n'+block('can_build_railway',rail_spec(cells[j]['state'],c['state']))
                    branches+=block('if' if not branches else 'else_if',block('limit',cond)+block('build_railway','level = 1\n'+rail_spec(cells[j]['state'],c['state'])))
                payout+=iff(cv(f'n{c["id"]}_project','=',0),branches)
            preview_rewards.append(iff(cv('selected','=',c['id']),payout))
        preview=f'custom_effect_tooltip = {P}build_{k}_tt\n'+block('effect_tooltip',''.join(preview_rewards))
        button(f'ip_build_{k}','',x,y,'',f'RUS_ip_build_{k} = yes',f'RUS_ip_can_build_{k} = yes',preview=preview)
        icon(f'ip_build_icon_{k}',f'GFX_RUS_ip_facility_{k}',x+6,y+5,.75)
        text(f'ip_build_label_{k}',P+f'build_{k}',x+32,y+8,86,20,center=True)
    button('ip_pause',P+'pause',1220,443,P+'pause_tt','RUS_ip_pause = yes','RUS_ip_editing = yes\n'+cv('sel_project','>',0))
    button('ip_cancel',P+'cancel',1364,443,P+'cancel_tt','set_country_flag = RUS_ip_cancel_armed\n'+add('dirty',1),cv('sel_project','>',0),condition='NOT = { has_country_flag = RUS_ip_cancel_armed }')
    button('ip_cancel_confirm',P+'confirm_cancel',1364,443,P+'cancel_tt','RUS_ip_cancel = yes',condition='has_country_flag = RUS_ip_cancel_armed')
    text('ip_commitments',P+'commitments',1220,493,284,75)
    button('ip_refresh',P+'refresh',1220,588,P+'refresh_tt','RUS_ip_refresh = yes')
    button('ip_start',P+'start',1364,588,'','RUS_ip_start = yes',condition='NOT = { has_country_flag = RUS_ip_started }',
           preview='custom_effect_tooltip = RUS_ip_start_tt\neffect_tooltip = { add_dynamic_modifier = { modifier = RUS_ip_extraction_bottleneck } }\n')
    text('ip_help_title',P+'help_title',44,135,1440,36,'hoi_24header',page='help')
    for idx in range(6): text(f'ip_help_{idx}',P+f'help_{idx}',44+(728 if idx>=3 else 0),191+154*(idx%3),686,146,page='help')
    button('ip_close','',1490,9,'CLOSE','RUS_ip_close_effect = yes',sprite='GFX_closebutton',page='all')
    frame='name = "RUS_industrial_planning_window"\nposition = { x = -768 y = -363 }\nsize = { width = 1536 height = 726 }\norientation = center\nmoveable = yes\nclick_to_front = yes\nshow_sound = menu_open_window\nhide_sound = menu_close_window\nbackground = { name = "frame" quadTextureSprite = "GFX_tiled_plain_bg" }\n'
    gui=block('guiTypes',''.join(launchers)+block('containerWindowType',frame+''.join(widgets)))
    script='context_type = player_context\nwindow_name = "RUS_industrial_planning_window"\ndirty = RUS_ip_dirty\nai_enabled = { always = no }\n'+block('visible','RUS_ip_available = yes\nhas_country_flag = RUS_ip_open')
    script+=block('triggers',''.join(block(k,v) for k,v in gt.items()))+block('properties','ip_progressbar = { frame = RUS_ip_progress_frame }\n')+block('effects',''.join(geffects))
    gfx=[]
    for name in ['map','selected','offline','connected','cell_button','progress']+[f'region_{c["id"]}' for c in cells]+[f'link_{e["a"]}_{e["b"]}' for e in data['edge_sprites']]:
        frames={'cell_button':3,'progress':21}.get(name,1)
        gfx.append(block('spriteType',f'name = "GFX_RUS_ip_{name}"\ntexturefile = "gfx/interface/RUS_industrial_planning/{name}.png"\nnoOfFrames = {frames}\ntransparencecheck = yes\n'))
    for k,asset in ICONS.items(): gfx.append(block('spriteType',f'name = "GFX_RUS_ip_facility_{k}"\ntexturefile = "gfx/interface/decisions/{asset}.dds"\n'))
    header='# Generated by tools/generate_industrial_planning.py. Edit the renderer, then --write.\n'
    category=block(P+'test_category','icon = GFX_decision_category_generic_industry\nallowed = { original_tag = RUS }\nvisible = { is_ai = no NOT = { has_country_flag = RUS_ip_ui_unlocked } }\n')
    decisions=block(P+'test_category',block(P+'enable_gui','icon = GFX_decision_generic_industry\nfire_only_once = yes\ncost = 0\nvisible = { is_ai = no NOT = { has_country_flag = RUS_ip_ui_unlocked } }\navailable = { original_tag = RUS is_ai = no }\ncomplete_effect = { custom_effect_tooltip = RUS_ip_enable_gui_tt hidden_effect = { RUS_ip_enable_gui = yes } }\nai_will_do = { base = 0 }\n'))
    outputs={'common/scripted_triggers/RUS_industrial_planning_triggers.txt':header+'\n'.join(triggers),
             'common/decisions/categories/RUS_industrial_planning_categories.txt':header+category,
             'common/decisions/RUS_industrial_planning_decisions.txt':header+decisions,
             'common/scripted_effects/RUS_industrial_planning_effects.txt':header+'\n'.join(effects),
             'common/on_actions/RUS_industrial_planning_on_actions.txt':header+actions,
             'common/dynamic_modifiers/RUS_industrial_planning_modifiers.txt':header+modifier,
             'common/scripted_guis/RUS_industrial_planning.txt':header+block('scripted_gui',''.join(launcher_scripts)+block('RUS_industrial_planning_gui',script)),
             'common/scripted_localisation/RUS_industrial_planning_loc.txt':header+'\n'.join(definitions),
             'interface/RUS_industrial_planning.gui':header+gui,'interface/RUS_industrial_planning.gfx':header+block('spriteTypes',''.join(gfx))}
    for lang,catalog in loc.items(): outputs[f'localisation/{lang}/RUS_industrial_planning_l_{lang}.yml']='l_'+lang+':\n'+''.join(f' {key}:0 "{value.replace(chr(10),r"\n")}"\n' for key,value in catalog.items())
    return outputs


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group();mode.add_argument('--check',action='store_true');mode.add_argument('--write',action='store_true')
    parser.add_argument('--output-root',type=Path);args=parser.parse_args()
    if args.check and args.output_root: parser.error('--check cannot write --output-root')
    out=(args.output_root or ROOT).resolve();outputs=render_outputs();assert outputs==render_outputs(),'Non-deterministic output'
    differences=[]
    for rel,content in outputs.items():
        target=(out/rel).resolve();assert target.is_relative_to(out)
        encoded=content.encode('utf-8-sig' if rel.endswith('.yml') else 'utf-8')
        actual=target.read_bytes().replace(b'\r\n',b'\n') if target.is_file() else None
        if encoded!=actual:
            differences.append(rel)
            if args.write or args.output_root: target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(encoded)
    print(f'{"Generated" if args.write or args.output_root else "Checked"} {len(outputs)} files; {len(differences)} differences.')
    if differences and not (args.write or args.output_root): raise SystemExit('\n'.join(differences))


if __name__=='__main__': main()
