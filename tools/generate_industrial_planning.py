"""Render independent industrial construction. Read-only unless --write.

The map builder and economy renderer are separate; the original Five-Year Plan
is deliberately neither an input nor an output of this prototype.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from industrial_planning_economy import P, PROJECTS, CATEGORIES, block, setv, add, cv, iff, rail_spec, render_economy
from industrial_planning_supply_ui import SUPPLY_ICONS, localisation as supply_localisation, widgets as supply_widgets
from industrial_planning_rail import map_pick, native_reward

ROOT = Path(__file__).resolve().parents[1]
LANGS = ('simp_chinese', 'english', 'russian')
ICONS = {1:'decision_coal', 2:'decision_steel', 3:'decision_generic_electricity',
         4:'decision_generic_factory', 5:'decision_generic_industry', 6:'decision_generic_train',
         7:'decision_generic_construction', 8:'decision_SOV_the_workers_dictatorship', 9:'ITA_urban',10:'decision_generic_train'}
ICON_SCALE = {8: .5, 9: 32/85}  # Reused KR assets fitted to a 32px icon box.


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
    L('open_tt','§Y工业建设§!\n在俄罗斯地图上安排工程，按游戏日期建设真实工厂、资源与交通设施。','§YIndustrial construction§!\nPlan real factories, resources and transport on the Russian map. Construction follows game time.')
    L('summary','[GetRUSIPPlanStatus]   |   已完成 §G[?RUS_ip_completed|0]§! 项工程','[GetRUSIPPlanStatus]  |  §G[?RUS_ip_completed|0]§! projects completed')
    L('not_started','§Y计划尚未启动§!','§YProgramme not started§!')
    L('active','剩余 §Y[?RUS_ip_days_left|0]§! 天','§Y[?RUS_ip_days_left|0]§! days remaining')
    L('ended','§Y本期建设计划已结束§!','§YConstruction programme concluded§!')
    L('network','接通莫斯科 [?RUS_ip_connected_count|0] / 36 区   |   全国供电满足率 [?RUS_ip_energy_percent|0]%   |   施工 [?RUS_ip_running|0] / 排队 [?RUS_ip_queued|0]','Linked to Moscow [?RUS_ip_connected_count|0] / 36  |  Power [?RUS_ip_energy_percent|0]%  |  Working [?RUS_ip_running|0] / queued [?RUS_ip_queued|0]')
    L('capacity','可用民工 §Y[?RUS_ip_free_civs|0]§!   |   物资入库占用：钢 [?RUS_ip_reserved_steel|1] / 煤 [?RUS_ip_reserved_coal|1]','Available civs §Y[?RUS_ip_free_civs|0]§!  |  Stock production: ST [?RUS_ip_reserved_steel|1] / CO [?RUS_ip_reserved_coal|1]')
    L('footnote','每区可同时安排一项工程。已竣工的工厂与资源保留在地图上。','One queued project per district. Completed buildings and resources remain on the world map.')
    L('selected','[GetRUSIPDistrict]','[GetRUSIPDistrict]')
    L('detail','基础设施 [?RUS_ip_sel_infra|0]   民工 [?RUS_ip_sel_civs|0]   军工 [?RUS_ip_sel_mil|0]\n煤 [?RUS_ip_sel_coal|0]   钢 [?RUS_ip_sel_steel|0]   电网 [?RUS_ip_sel_grid|0]\n铁路 [?RUS_ip_sel_rail|0] 级   [GetRUSIPConnection]\n当地运力 [?RUS_ip_sel_freight|1]','Infrastructure [?RUS_ip_sel_infra|0]  Civs [?RUS_ip_sel_civs|0]  Arms [?RUS_ip_sel_mil|0]\nCoal [?RUS_ip_sel_coal|0]  Steel [?RUS_ip_sel_steel|0]  Grid [?RUS_ip_sel_grid|0]\nRail level [?RUS_ip_sel_rail|0]  [GetRUSIPConnection]\nLocal freight [?RUS_ip_sel_freight|1]')
    L('connected','§G接通莫斯科§!','§GConnected§!'); L('disconnected','§R尚未接通§!','§RDisconnected§!')
    L('project','[GetRUSIPSelectedType]  ·  [GetRUSIPSelectedStatus]','[GetRUSIPSelectedType] · [GetRUSIPSelectedStatus]')
    L('progress','进度 [?RUS_ip_sel_percent|0]%   [GetRUSIPEstimate]\n当前速度：每日 [?RUS_ip_sel_speed|2] 工作量','Progress [?RUS_ip_sel_percent|0]%  [GetRUSIPEstimate]\nDaily work: [?RUS_ip_sel_speed|2]')
    L('eta','约 [?RUS_ip_sel_eta|0] 天','About [?RUS_ip_sel_eta|0] days'); L('eta_unknown','工期暂无法估计','Duration unavailable')
    L('commitments','全国调拨\n施工占用民工 [?RUS_ip_reserved_civs|0]；暂停、取消或竣工释放。\n钢 [?RUS_ip_reserved_steel|1] / 煤 [?RUS_ip_reserved_coal|1] 为生产仓储物资时的原生资源占用，每日调整；自动仓储与经营会在无施工时继续。','National commitments\nConstruction reserves [?RUS_ip_reserved_civs|0] civs until pause, cancellation or completion.\nST [?RUS_ip_reserved_steel|1] / CO [?RUS_ip_reserved_coal|1] is native flow booked for warehouse production, updated daily even when no construction is queued.')
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
    statuses=[(0,'空闲','Idle'),(1,'§G施工中§!','§GBuilding§!'),(2,'§R建设条件不符§!','§RSite unavailable§!'),(3,'§Y已暂停§!','§YPaused§!'),(4,'§R铁路未接通§!','§RRail disconnected§!'),(5,'§R等待民工§!','§RAwaiting civs§!'),(6,'§Y等待物资到货§!','§YAwaiting materials§!')]
    for k,zh,en in statuses: L(f'status_{k}',zh,en)
    for k,s in PROJECTS.items():
        L(f'type_{k}',s['zh'],s['en']); L(f'build_{k}',s['zh'],s['en'])
        requirement={1:'须有煤矿潜力；扩建上限：§Y3§! 次。',2:'须有铁矿潜力；扩建上限：§Y3§! 次。',3:'中心州须有强化电网建设空间。',4:'地区发展度要求：§Y20§!\n中心州须有民用工厂槽位，并接通莫斯科。',5:'地区发展度要求：§Y35§!\n中心州须有军用工厂槽位，并接通莫斯科。',6:'中心州须有基础设施空间；内陆需相邻已接通地区作为铁路起点。',7:'本区建设上限：§Y3§! 次。',8:'本区培训上限：§Y3§! 次；培训收益随发展度提高，重复培训收益递减。',9:'中心州须为普通地区类型，且尚未达到“$twelve$”。\n已用满建筑槽位仍可扩建；不适用于特殊港口、海岛和荒地。',10:'两端须由本国拥有并控制，并存在可施工的国内陆路。\n使用终点地区的工程队列、仓库与配套。开工后两端和目标等级固定。\n费用与工作量随地图距离和目标等级增加；不代表实际逐省长度。'}[k]
        requirement_en={1:'Requires coal deposits; expansion limit: §Y3§!.',2:'Requires iron deposits; expansion limit: §Y3§!.',3:'The central state needs a power grid slot.',4:'Required development: §Y20§!\nThe central state needs a civilian factory slot and a connection to Moscow.',5:'Required development: §Y35§!\nThe central state needs an arms factory slot and a connection to Moscow.',6:'The central state needs infrastructure space; inland rail starts at a connected domestic neighbour.',7:'District construction limit: §Y3§!.',8:'District training limit: §Y3§!; higher development improves training, repeated courses yield less.',9:'The central state must have an ordinary category below $twelve$.\nCan expand with all slots occupied; special ports, islands and wastelands are excluded.',10:'Own and control both endpoints, with a buildable domestic land path.\nUses the destination queue, stocks and capacities. Endpoints and level lock on acceptance.\nCost and work scale with map distance and target level, not the exact provincial route.'}[k]
        extra_zh={3:'\n地区供电容量：§G+8.0§!',7:'\n工业劳动力容量基础值：§G+2.0§!\n地区运输容量基础值：§G+1.0§!',8:'\n培训劳动力：§G+[?RUS_ip_forecast_8_training_gain|1]§!'}.get(k,'')
        extra_en={3:'\nLocal power capacity: §G+8.0§!',7:'\nBase industrial labour capacity: §G+2.0§!\nBase local freight capacity: §G+1.0§!',8:'\nTrained labour: §G+[?RUS_ip_forecast_8_training_gain|1]§!'}.get(k,'')
        category_zh='\n中心州类型：§Y[GetRUSIPCategory]§! → §Y[GetRUSIPNextCategory]§!' if k==9 else ''
        category_en='\nCentral state: §Y[GetRUSIPCategory]§! → §Y[GetRUSIPNextCategory]§!' if k==9 else ''
        if k==10:
            category_zh='\n§Y[GetRUSIPRailFrom]§! → §Y[GetRUSIPRailTo]§!\n目标铁路等级：§Y[?RUS_ip_rail_level|0]§!'
            category_en='\n§Y[GetRUSIPRailFrom]§! → §Y[GetRUSIPRailTo]§!\nTarget rail level: §Y[?RUS_ip_rail_level|0]§!'
        L(f'build_{k}_tt',f'§Y{s["zh"]}§!{category_zh}\n\n§Y竣工后获得：§!\n地区发展度：§G+[?RUS_ip_forecast_{k}_gain|1]§!{extra_zh}',f'§Y{s["en"]}§!{category_en}\n\n§YOn completion:§!\nDistrict development: §G+[?RUS_ip_forecast_{k}_gain|1]§!{extra_en}')
        def consumption(value):
            return f'§R-{value*.1:.2f}§!' if value else '§Y0.00§!'
        L(f'build_{k}_cost_tt','\n'.join([
            '\n§Y开工与施工：§!',f'计划资金：§R-[?RUS_ip_forecast_{k}_cost|1]§!',
            f'$MODIFIER_CIVILIAN_FACTORY_USE$：§R+{s["civs"]}§!',
            f'每日钢消耗：{consumption(s["steel"])}',f'每日煤消耗：{consumption(s["coal"])}',
            f'工业劳动力需求：§R+{s["workers"]:g}§!',f'地区电力需求：§R+{s["power"]:g}§!',f'基础运输负荷：§R+{s["freight"]:g}§!',
            '在途货物另占运力；缺料按供给比例施工，无料等待。',requirement,'同类工程的发展度收益递减。',
            f'供料充足时约 §Y[?RUS_ip_forecast_{k}_days|0]§! 天；瓶颈：[GetRUSIPForecast{k}]。','估计不含待料与排队。']),
            '\n'.join(['\n§YConstruction:§!',f'Programme funds: §R-[?RUS_ip_forecast_{k}_cost|1]§!',
            f'$MODIFIER_CIVILIAN_FACTORY_USE$: §R+{s["civs"]}§!',
            f'Daily steel consumption: {consumption(s["steel"])}',f'Daily coal consumption: {consumption(s["coal"])}',
            f'Industrial labour demand: §R+{s["workers"]:g}§!',f'Local power demand: §R+{s["power"]:g}§!',f'Base freight load: §R+{s["freight"]:g}§!',
            'Cargo adds freight load; shortages slow or halt work.',requirement_en,'Repeated projects yield less development.',
            f'Supplied estimate: §Y[?RUS_ip_forecast_{k}_days|0]§! days. [GetRUSIPForecast{k}].','Excludes waiting for materials and capacity.']))
        if k==10:
            for catalog in loc.values():
                for suffix in ('tt','cost_tt'):
                    key=P+f'build_10_{suffix}'
                    for metric in ('cost','days','gain'):catalog[key]=catalog[key].replace('RUS_ip_forecast_10_'+metric,'RUS_ip_rail_'+metric)
        # KR's scripted GUI tooltips explicitly bind [!<button>_click] to pdx_tooltip.
        # Keeping this wrapper separate from build_*_tt avoids recursive expansion.
        L(f'build_{k}_hover',f'[!ip_build_{k}_click]',f'[!ip_build_{k}_click]')
        L(f'estimate_{k}',f'资金 [?RUS_ip_forecast_{k}_cost|0] · [?RUS_ip_forecast_{k}_days|0] 天',f'[?RUS_ip_forecast_{k}_cost|0] funds · [?RUS_ip_forecast_{k}_days|0]d')
        L(f'cost_{k}',f'资金 [?RUS_ip_forecast_{k}_cost|0] · 民工 {s["civs"]}',f'[?RUS_ip_forecast_{k}_cost|0] funds · {s["civs"]} CIV')
    for key,zh,en in [('start','启动建设计划','Start programme'),('refresh','刷新状态','Refresh'),('help','玩法介绍','How to play'),('back','返回地图','Back to map'),('pause','暂停／继续','Pause / resume'),('cancel','取消工程','Cancel project'),('confirm_cancel','确认取消','Confirm cancel')]: L(key,zh,en)
    L('start_tt','开始本期 1800 天建设计划，仅能启动一次。每完成一项煤矿或铁矿工程，恢复 2 个百分点的战略资源获取效率，累计 15 项后清除下述惩罚；建设期结束时清除剩余惩罚。','Begin this independent 1800-day programme once. Each completed coal or iron mine restores 2 percentage points of extraction efficiency; 15 mines clear the penalty. Any remaining penalty ends with the programme.')
    L('refresh_tt','重新核对领土、铁路与施工状态，不推进时间。全国可用建设物资每日更新。','Recheck territory, rail and work without advancing time. National capacity updates daily.')
    L('pause_tt','暂停或恢复选中工程；暂停释放民工、停止施工耗料并保留进度。地区工业与仓库仍照常经营。','Pause or resume. Releases project civs and stops its material use; local industry and warehousing continue.')
    L('cancel_tt','确认取消后清空施工进度并释放民工，退还未完工部分所对应开工费的 75%。当前可退 [?RUS_ip_sel_refund|1] 资金；已消耗物资不退。','Confirm to release civs and discard progress. Refunds 75% of the uncompleted share of the upfront cost: [?RUS_ip_sel_refund|1] now. Consumed materials are not refunded.')
    L('help_title','工业建设 · 玩法介绍','Industrial construction · How to play')
    help_zh=[
        '§Y一、启动与选址§!\n先执行“启用工业建设界面（测试）”决议，再在窗口点击“启动建设计划”，开始独立的 1800 天建设期。圆点代表经济区，工程落在所示中心州；每区同时一项，可跨区并行。关闭窗口后工程继续。',
        '§Y二、真实建设与资源链§!\n启动时战略资源获取效率 −30%，每竣工一项煤矿或铁矿恢复 2 个百分点，15 项清除。煤矿产煤、铁矿产钢；电网降低工厂能耗，钢铁厂增加民工与钢，机械军工厂增加军工。具体收益见按钮原生提示。',
        '§Y三、资金与仓储§!\n初始资金 §Y1000§!，开工扣费，施工占用民工并每日耗煤钢。每 30 天按实际收支结算，无固定拨款、无保底。余额可为负：每欠 §R100§!，稳定度 §R−5%§!、建造速度 §R−10%§!，最多 §R−50%§!／§R−75%§!，还款后减轻。负债时不能开新工程，现有工程继续。',
        '§Y四、经济区与扩建§!\n统计全经济区本国拥有且控制的州，建筑落在中心州。发展度 §Y0—100§!；钢铁厂要求 §Y20§!，机械厂 §Y35§!。公共设施与培训改善劳动力。地区扩建消耗资金、民工与物资，竣工提升中心州类型一级，基础建筑槽位 §G+1§!，最高为“$twelve$”。',
        '§Y五、自动物流与规划§!\n本地先供料；超过 21 天储备的余料发往莫斯科，总仓向缺料区补至 14 天。在途货物沿固定规划路线运输，拥堵延迟、断路暂停。可指定一个优先地区。电网与相邻余电支援仍保留，调电占运力；重工业必须接通莫斯科。仓库无料时，配套工程也会等待。',
        '§Y六、战时与期满§!\n和平先供本区工业，开战后优先供给在建工程。计时与账本照常运行；取消或期满退回剩余开工费的 §Y75%§!。期满清除施工占用、开采与本期负债惩罚，保留完工资产并封存账本。在“仓储与预算”查看明细。本原型尚未接管旧一五计划。',
    ]
    help_en=[
        '§Y1. Start and choose a site§!\nFirst take Enable Industrial Construction GUI (Test), then Start programme in this window for an independent 1800-day period. Work is delivered to the selected central state. One queued project per district, several districts at once. Closing the window does not stop work.',
        '§Y2. Real assets and supply chains§!\nStarting applies -30% extraction efficiency. Each completed coal or iron mine restores 2 percentage points; 15 clear it. Coal mines add coal, iron mines add steel; grids lower energy needs, steelworks add civs and steel, machine works add arms factories. See native reward tooltips.',
        '§Y3. Funds and stock§!\nStart with 1000 funds. Projects cost funds, reserve civs and consume coal/steel. Settle actual operations every 30 days, with no funding or minimum. Debt can grow below zero: per 100 owed, stability -5%, construction -10%, capped at -50%/-75%. Repayment reduces penalties. Debt blocks new orders, not existing work.',
        '§Y4. Regions and expansion§!\nAggregate owned and controlled member states; deliver buildings to the centre. Development 0–100; steelworks require 20, machinery 35. Public facilities and training improve labour. Expansion consumes funds, civs and materials, raises the central state category once and adds one base slot, up to $twelve$.',
        '§Y5. Automatic freight and planning§!\nUse local stocks first. Export beyond 21 days to Moscow; the hub supplies up to 14 days. Fixed routes carry finite cargo; congestion delays and route cuts pause it. Select one priority district. Power sharing uses freight. Heavy industry needs Moscow access. No materials means no work.',
        '§Y6. War and conclusion§!\nPeace favours industry; war favours current construction. Accounts and time continue. Cancellation or expiry refunds 75% of unused upfront cost. Expiry releases commitments, extraction and programme debt penalties; assets remain and accounts freeze. The old Five-Year Plan is separate.',
    ]
    for idx,(zh,en) in enumerate(zip(help_zh,help_en)): L(f'help_{idx}',zh,en)
    definitions=[]
    def defined(name,branches):
        definitions.append(block('defined_text',f'name = {name}\n'+''.join(block('text',(block('trigger',c) if c else '')+f'localization_key = {k}\n') for c,k in branches)))
    supply_localisation(L,defined,data)
    L('rail_unselected','未选定','Not selected')
    L('rail_choose','选择铁路线路','Choose route')
    L('rail_clear','清除线路','Clear route')
    L('rail_level_button','目标：[?RUS_ip_rail_level|0] 级','Level [?RUS_ip_rail_level|0]')
    L('rail_queue','加入修建队列','Queue railway')
    L('rail_choose_tt','点击后，在地图上依次点击起点经济区和终点经济区。两次选点完成后，悬浮“加入修建队列”查看费用与原生成果。','Click, then select the origin and destination districts on the map. Hover Queue railway to review costs and native results.')
    L('rail_level_tt','点击切换目标铁路等级：§Y1—5§!。更高等级增加费用与工作量；完工修建至该等级，不降低已有的更高等级铁路。','Cycle target rail level §Y1–5§!. Higher levels cost more and take longer. Existing higher-level track is not downgraded.')
    L('rail_pick_start','§Y请在地图上点击起点地区。§!','§YClick the origin district on the map.§!')
    L('rail_pick_end','§Y请在地图上点击另一地区作为终点。§!','§YClick another district as the destination.§!')
    L('rail_ready','资金：§R-[?RUS_ip_rail_cost|1]§!  |  民工占用：§R+3§!  |  预计 [?RUS_ip_rail_days|0] 天','Funds: §R-[?RUS_ip_rail_cost|1]§! | Civs reserved: §R+3§! | ~[?RUS_ip_rail_days|0] days')
    L('rail_invalid','§R两端必须由本国拥有并控制，且存在可施工的国内陆路。§!','§ROwn and control both ends, with a buildable domestic land path.§!')
    L('rail_prompt','点击“选择铁路线路”，再依次点选地图上的两个经济区。','Choose route, then click two districts on the map.')
    L('rail_summary','铁路：§Y[GetRUSIPRailFrom]§! → §Y[GetRUSIPRailTo]§!\n[GetRUSIPRailPrompt]','Rail: §Y[GetRUSIPRailFrom]§! → §Y[GetRUSIPRailTo]§!\n[GetRUSIPRailPrompt]')
    L('rail_origin_marker','§Y起§!','§YFrom§!')
    L('rail_destination_marker','§G终§!','§GTo§!')
    L('rail_queue_detail','施工线路：§Y[GetRUSIPQueuedRailFrom]§! → §Y[GetRUSIPQueuedRailTo]§! · [?RUS_ip_sel_rail_level|0] 级','Building: §Y[GetRUSIPQueuedRailFrom]§! → §Y[GetRUSIPQueuedRailTo]§! · level [?RUS_ip_sel_rail_level|0]')
    for side in ('from','to'):
        defined('GetRUSIPQueuedRail'+side.title(),[(cv('sel_rail_'+side+'_state','=',c['state']),P+f'district_{c["id"]}') for c in cells]+[('',P+'rail_unselected')])
    for side in ('from','to'):
        defined('GetRUSIPRail'+side.title(),[(cv('rail_'+side,'=',c['id']),P+f'district_{c["id"]}') for c in cells]+[('',P+'rail_unselected')])
    defined('GetRUSIPRailPrompt',[(cv('rail_pick','=',1),P+'rail_pick_start'),(cv('rail_pick','=',2),P+'rail_pick_end'),
            ('RUS_ip_rail_path_valid = yes',P+'rail_ready'),(cv('rail_to','>',-1),P+'rail_invalid'),('',P+'rail_prompt')])
    L('category_special','特殊地区（不可扩建）','Special category (unavailable)')
    L('category_max','已达最高等级','Maximum category reached')
    defined('GetRUSIPCategory',[(cv('sel_category','=',level),category) for level,category in enumerate(CATEGORIES,1)]+[('',P+'category_special')])
    defined('GetRUSIPNextCategory',[(cv('sel_category','=',level),CATEGORIES[level]) for level in range(1,len(CATEGORIES))]+[(cv('sel_category','=',12),P+'category_max'),('',P+'category_special')])
    metrics=[('development','发展度','Development','[?RUS_ip_sel_development|1] / 100'),
             ('workers','工业劳动力 · 供给／需求','Labour · supply / need','[?RUS_ip_sel_workers|1] / [?RUS_ip_sel_workers_need|1]'),
             ('power','地区电力 · 可用／需求','Power · available / need','[?RUS_ip_sel_power|1] / [?RUS_ip_sel_power_need|1]'),
             ('freight','运输负荷 · 使用／容量','Freight · load / capacity','[?RUS_ip_sel_freight_used|1] / [?RUS_ip_sel_freight|1]')]
    tips={
        'development':('由经济区初始人口、加权基础设施和每州工厂密度决定，后续由工程积累。发展度提高施工速度与培训效果、降低开工费并提高经营收入；钢铁厂要求 20，机械军工厂要求 35。同类重复建设收益递减。','Seeded once from regional population, weighted infrastructure and industry per state. Improves work, training and income while reducing upfront costs. Steelworks need 20, machinery 35. Repeated projects yield less development.'),
        'workers':('工业劳动力容量点数，不扣征兵人力。现有民工、军工、矿业与施工共同占用；短缺会拖慢工程。建设公共设施、安排培训或提高发展度可缓解。公共设施 [?RUS_ip_sel_urban|0]/3，培训 [?RUS_ip_sel_training|0]/3。','Programme labour points, not recruitable manpower. Existing industry, mines and current work consume capacity. Public facilities, training and development improve it.'),
        'power':('用于本建设计划的地区供电能力，不改写全国原生电力市场。基础设施、煤炭条件与电网提供能力；工厂和施工增加需求。当前调入 [?RUS_ip_sel_power_import|1]、调出 [?RUS_ip_sel_power_export|1]。调拨只走陆上相邻可用联系，每点电力消耗两端各 0.5 运力；不能转手重复输出，也不跨海输电。','Programme power capacity. Infrastructure, coal and grids support it; factories and work consume it. Imports [?RUS_ip_sel_power_import|1], exports [?RUS_ip_sel_power_export|1]. Land neighbours only; each transferred point uses 0.5 freight at both endpoints. Imports cannot be re-exported.'),
        'freight':('基础设施、铁路与公共设施增加容量；未接通莫斯科时容量为 60%。工厂、矿业、施工、在途物资和调电占用运力。货物沿途各区都计入负荷；拥堵时到货延迟，最低按正常速度的 5% 运输。新发车保留 10% 容量的应急通道，避免配套工程永远缺料。','Infrastructure, rail and facilities add capacity; disconnected regions retain 60%. Industry, work, power and cargo along the whole route use freight. Congestion slows arrivals, down to 5% speed. New dispatches retain a 10% emergency allowance to avoid supply deadlock.')}
    for key,zh,en,val in metrics:
        L('metric_'+key,zh+'\n§Y'+val+'§!',en+'\n§Y'+val+'§!')
        L('metric_'+key+'_tt','§Y'+zh+'§!\n'+tips[key][0],'§Y'+en+'§!\n'+tips[key][1])
    for k,zh,en in [(0,'§G配套充足§!','§GSufficient capacity§!'),(1,'§R用工不足：安排培训或公共设施§!','§RLabour: train workers§!'),(2,'§R供电不足：建设电网或邻区调拨§!','§RPower: grid or neighbour support§!'),(3,'§R运输拥挤：完善交通或就近选址§!','§RFreight: improve transport§!'),(4,'§R仓储供料不足：查看仓储与预算§!','§RMaterials: see Supply / budget§!')]:
        L(f'bottleneck_{k}',zh,en)
    L('bottleneck','地区瓶颈：[GetRUSIPBottleneck]','Regional bottleneck: [GetRUSIPBottleneck]')
    L('idle_bottleneck','选择工程，悬浮查看工期与瓶颈预测。','Hover over a project for its work estimate and bottleneck.')
    L('site_summary','[GetRUSIPDistrict]  |  基建 [?RUS_ip_sel_infra|0] · 民工 [?RUS_ip_sel_civs|0] · 军工 [?RUS_ip_sel_mil|0]  |  [GetRUSIPConnection]','[GetRUSIPDistrict]  |  Infra [?RUS_ip_sel_infra|0] · Civs [?RUS_ip_sel_civs|0] · Arms [?RUS_ip_sel_mil|0]  |  [GetRUSIPConnection]')
    L('progress_compact','[GetRUSIPSelectedType] · [GetRUSIPSelectedStatus]  |  [?RUS_ip_sel_percent|0]% · [GetRUSIPEstimate]','[GetRUSIPSelectedType] · [GetRUSIPSelectedStatus]  |  [?RUS_ip_sel_percent|0]% · [GetRUSIPEstimate]')
    defined('GetRUSIPBottleneck',[(cv('sel_project','=',0),P+'idle_bottleneck')]+[(cv('sel_bottleneck','=',k),P+f'bottleneck_{k}') for k in range(5)])
    for kind in PROJECTS: defined(f'GetRUSIPForecast{kind}',[(cv('rail_bottleneck' if kind==10 else f'forecast_{kind}_bottleneck','=',k),P+f'bottleneck_{k}') for k in range(4)])
    defined('GetRUSIPPlanStatus',[('has_country_flag = RUS_ip_active',P+'active'),('has_country_flag = RUS_ip_ended',P+'ended'),('',P+'not_started')])
    defined('GetRUSIPSelectedType',[(cv('sel_project','=',k),P+f'type_{k}') for k in PROJECTS]+[('',P+'type_0')])
    defined('GetRUSIPSelectedStatus',[(cv('sel_status','=',k),P+f'status_{k}') for k,_,_ in statuses]+[('',P+'status_0')])
    defined('GetRUSIPEstimate',[(cv('sel_speed','>',0),P+'eta'),('',P+'eta_unknown')])
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
    widgets=[]; gt={}; geffects=[]; card_sizes=set()
    def visibility(name,condition='',page='board'):
        base='NOT = { has_country_flag = RUS_ip_help_open }\nNOT = { has_country_flag = RUS_ip_supply_open }\n' if page=='board' else f'has_country_flag = RUS_ip_{page}_open\n' if page in ('help','supply') else ''
        if base+condition: gt[name+'_visible']=base+condition
    def text(name,key,x,y,w,h=24,font='hoi_16mbs',center=False,condition='',page='board',tip=''):
        tooltip=f'pdx_tooltip = "{tip}" ' if tip else ''
        widgets.append(f'instantTextBoxType = {{ name = "{name}" position = {{ x = {x} y = {y} }} text = "{key}" font = "{font}" maxWidth = {w} maxHeight = {h} format = {"center" if center else "left"} fixedsize = yes {tooltip}alwaystransparent = {"no" if tip else "yes"} }}\n'); visibility(name,condition,page)
    def icon(name,sprite,x,y,scale=1,condition='',page='board',tip=''):
        tooltip=f'pdx_tooltip = "{tip}" ' if tip else ''
        widgets.append(f'iconType = {{ name = "{name}" position = {{ x = {x} y = {y} }} spriteType = "{sprite}" scale = {scale} {tooltip}alwaystransparent = {"no" if tip else "yes"} }}\n'); visibility(name,condition,page)
    def button(name,key,x,y,tip,action,enable='',sprite='GFX_RUS_ip_tab',condition='',page='board',preview='',scale=1):
        tooltip=f'pdx_tooltip = "{tip}" ' if tip else ''
        shortcut='shortcut = "ESCAPE" ' if name=='ip_close' else ''
        widgets.append(f'buttonType = {{ name = "{name}" position = {{ x = {x} y = {y} }} scale = {scale} quadTextureSprite = "{sprite}" buttonText = "{key}" buttonFont = "hoi_16mbs" {tooltip}{shortcut}clicksound = click_default }}\n')
        if enable: gt[name+'_click_enabled']=enable
        visibility(name,condition,page); geffects.append(block(name+'_click',preview+block('hidden_effect',action)))
    def background(name,x,y,w,h,page='board'):
        # Nested window backgrounds leaked across pages in-game. Use a visible
        # icon with a native nine-slice sprite, as KR's UPC_party_ban_bg does.
        card_sizes.add((w,h))
        icon(name,f'GFX_RUS_ip_card_{w}x{h}',x,y,page=page)
    text('ip_title',P+'title',24,16,1712,32,'hoi_24header',True,page='all')
    text('ip_summary',P+'summary',60,56,810,27,'hoi_20b',page='all')
    text('ip_budget_projection',P+'budget_projection',60,80,810,24,tip=P+'funds_hover',condition='has_country_flag = RUS_ip_active',page='all')
    text('ip_capacity',P+'capacity',940,80,760,24,tip=P+'commitments')
    debt_preview='custom_effect_tooltip = RUS_ip_funds_tt\n'+iff('has_country_flag = RUS_ip_active\n'+cv('funds','<',0),block('effect_tooltip','add_dynamic_modifier = { modifier = RUS_ip_plan_debt }\n'))
    button('ip_funds_icon','',900,56,P+'funds_hover','RUS_ip_toggle_supply = yes',sprite='GFX_RUS_ip_funds',scale=SUPPLY_ICONS['funds'][1],page='all',preview=debt_preview)
    text('ip_funds',P+'funds_summary',944,57,750,27,tip=P+'funds_hover',page='all')
    text('ip_rail_summary',P+'rail_summary',180,116,710,48,tip=P+'rail_choose_tt')
    button('ip_rail_choose',P+'rail_choose',930,120,P+'rail_choose_tt','RUS_ip_rail_choose = yes')
    button('ip_rail_level',P+'rail_level_button',1065,120,P+'rail_level_tt','RUS_ip_rail_cycle_level = yes')
    button('ip_rail_clear',P+'rail_clear',1335,120,P+'rail_choose_tt','RUS_ip_rail_clear = yes')
    mx,my,zoom=150,98,1.25
    # Clip the atlas' non-geographic northern padding in the GUI. The viewport
    # has no background; the inner icon owns page visibility, as in KR's intro.
    # Keep all map coordinates and the registered source art unchanged.
    map_cut=round(data.get('northern_map_limit_y',0)*zoom)
    widgets.append(block('containerWindowType',f'name = "ip_map_viewport"\nposition = {{ x = {mx} y = {my+map_cut} }}\nsize = {{ width = {round(data["width"]*zoom)} height = {round(data["height"]*zoom)-map_cut} }}\nclipping = yes\n'+f'iconType = {{ name = "ip_map" position = {{ x = 0 y = {-map_cut} }} spriteType = "GFX_RUS_ip_map" scale = {zoom} alwaystransparent = yes }}\n'))
    visibility('ip_map')
    for e in data['edge_sprites']:
        a,b=e['a'],e['b']; icon(f'ip_link_{a}_{b}',f'GFX_RUS_ip_link_{a}_{b}',mx+round(e['x']*zoom),my+round(e['y']*zoom),zoom,condition=cv(f'edge_{a}_{b}_live','=',1))
    for c in cells:
        i=c['id']; icon(f'ip_region_{i}',f'GFX_RUS_ip_region_{i}',mx+round(c['bbox'][0]*zoom),my+round(c['bbox'][1]*zoom),zoom,condition=cv('selected','=',i))
    for c in cells:
        i=c['id']; x,y=mx+round((c['x']-13)*zoom),my+round((c['y']-13)*zoom)
        action=iff('RUS_ip_available = yes\nhas_country_flag = RUS_ip_open',setv('selected',i)+map_pick(c)+'clr_country_flag = RUS_ip_cancel_armed\nRUS_ip_refresh = yes\n')
        button(f'ip_cell_{i}','',x,y,P+f'node_{i}_tt',action,sprite='GFX_RUS_ip_cell_button',scale=zoom)
        icon(f'ip_selected_{i}','GFX_RUS_ip_selected',x,y,zoom,condition=cv('selected','=',i))
        icon(f'ip_offline_{i}','GFX_RUS_ip_offline',x,y,zoom,condition=cv(f'n{i}_project','>',0)+cv(f'n{i}_running','=',0))
        text(f'ip_number_{i}',f'{i+1:02}',x+1,y+6,30,20,center=True,condition=cv(f'n{i}_project','=',0)+cv(f'n{i}_last_kind','=',0))
        for k in PROJECTS:
            cond=block('OR',cv(f'n{i}_project','=',k)+block('AND',cv(f'n{i}_project','=',0)+cv(f'n{i}_last_kind','=',k)))
            icon(f'ip_facility_{i}_{k}',f'GFX_RUS_ip_facility_{k}',x+4,y+4,.78*ICON_SCALE.get(k,1),cond)
        text(f'ip_rail_origin_{i}',P+'rail_origin_marker',x-4,y-17,40,20,center=True,condition=cv('rail_from','=',i))
        text(f'ip_rail_destination_{i}',P+'rail_destination_marker',x-4,y-17,40,20,center=True,condition=cv('rail_to','=',i))
    text('ip_network',P+'network',410,600,1040,24,center=True)
    text('ip_selected',P+'site_summary',220,646,1320,28,'hoi_20b',True,tip=P+'detail')
    for idx,(key,_,_,_) in enumerate(metrics):
        x=218+332*idx
        background('ip_metric_bg_'+key,x,679,326,64)
        icon('ip_metric_icon_'+key,'GFX_RUS_ip_metric_'+key,x+14,695,1.05*(.5 if key=='workers' else 1),tip=P+'metric_'+key+'_tt')
        text('ip_metric_'+key,P+'metric_'+key,x+60,692,258,44,tip=P+'metric_'+key+'_tt')
    icon('ip_stock_icon','GFX_RUS_ip_warehouse',374,748,.64,tip=P+'warehouse_tt')
    text('ip_stock',P+'stock_ribbon',409,746,1135,24,tip=P+'warehouse_tt')
    for k in PROJECTS:
        if k==10:
            preview='custom_effect_tooltip = RUS_ip_build_10_tt\n'
            preview+=block('effect_tooltip',iff('RUS_ip_rail_path_valid = yes',native_reward('rail_from_state','rail_to_state','rail_level')))
            preview+='custom_effect_tooltip = RUS_ip_build_10_cost_tt\n'
            button('ip_build_10',P+'rail_queue',1200,120,P+'build_10_hover','RUS_ip_build_10 = yes','RUS_ip_can_build_10 = yes',preview=preview)
            continue
        x,y=374+257*((k-1)%4),776+66*((k-1)//4)
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
            if payout: preview_rewards.append(iff(cv('selected','=',c['id']),payout))
        preview=f'custom_effect_tooltip = {P}build_{k}_tt\n'
        if preview_rewards: preview+=block('effect_tooltip',''.join(preview_rewards))
        if k==9:
            preview+=iff(cv('sel_category','>',0)+cv('sel_category','<',12),'custom_effect_tooltip = increase_state_category_by_one_level_tt\n')
        preview+=f'custom_effect_tooltip = {P}build_{k}_cost_tt\n'
        if k==9:
            # Compact expansion action beside the selected state, above the
            # existing eight-project grid; never overlap its progress row.
            button('ip_build_9',P+'build_9',1566,644,P+'build_9_hover','RUS_ip_build_9 = yes','RUS_ip_can_build_9 = yes',preview=preview)
            icon('ip_build_icon_9','GFX_RUS_ip_facility_9',1535,648,.85*ICON_SCALE[9])
            continue
        button(f'ip_build_{k}','',x,y,P+f'build_{k}_hover',f'RUS_ip_build_{k} = yes',f'RUS_ip_can_build_{k} = yes',preview=preview,sprite='GFX_RUS_ip_action')
        icon(f'ip_build_icon_{k}',f'GFX_RUS_ip_facility_{k}',x+24,y+15,ICON_SCALE.get(k,1))
        text(f'ip_build_label_{k}',P+f'build_{k}',x+65,y+10,150,22,center=True)
        text(f'ip_build_estimate_{k}',P+f'estimate_{k}',x+65,y+33,150,22,center=True,condition=cv('sel_project','=',0))
        text(f'ip_build_cost_{k}',P+f'cost_{k}',x+65,y+33,150,22,center=True,condition=cv('sel_project','>',0))
    text('ip_progress',P+'progress_compact',550,910,810,24)
    text('ip_rail_queue_detail',P+'rail_queue_detail',550,929,1080,19,condition=cv('sel_project','=',10))
    icon('ip_progressbar','GFX_RUS_ip_progress',242,911)
    button('ip_pause',P+'pause',525,948,P+'pause_tt','RUS_ip_pause = yes','RUS_ip_editing = yes\n'+cv('sel_project','>',0))
    button('ip_cancel',P+'cancel',662,948,P+'cancel_tt','set_country_flag = RUS_ip_cancel_armed\n'+add('dirty',1),cv('sel_project','>',0),condition='NOT = { has_country_flag = RUS_ip_cancel_armed }')
    button('ip_cancel_confirm',P+'confirm_cancel',662,948,P+'cancel_tt','RUS_ip_cancel = yes',condition='has_country_flag = RUS_ip_cancel_armed')
    button('ip_refresh',P+'refresh',799,948,P+'refresh_tt','RUS_ip_refresh = yes')
    button('ip_supply',P+'supply',936,948,'','RUS_ip_toggle_supply = yes')
    button('ip_help',P+'help',1073,948,'','RUS_ip_toggle_help = yes',page='board')
    button('ip_back',P+'back',818,948,'','RUS_ip_toggle_help = yes',page='help')
    button('ip_start',P+'start',388,948,'','RUS_ip_start = yes',condition='NOT = { has_country_flag = RUS_ip_started }',
           preview='custom_effect_tooltip = RUS_ip_start_tt\neffect_tooltip = { add_dynamic_modifier = { modifier = RUS_ip_extraction_bottleneck } }\n')
    text('ip_help_title',P+'help_title',160,140,1440,36,'hoi_24header',True,page='help')
    for idx in range(6): text(f'ip_help_{idx}',P+f'help_{idx}',170+(730 if idx>=3 else 0),215+190*(idx%3),660,170,page='help')
    text('ip_extraction',P+'extraction',170,837,1400,24,page='help')
    supply_widgets(text,icon,button,background)
    button('ip_close','',1714,9,'CLOSE','RUS_ip_close_effect = yes',sprite='GFX_closebutton',page='all')
    frame='name = "RUS_industrial_planning_window"\nposition = { x = -880 y = -500 }\nsize = { width = 1760 height = 1000 }\norientation = center\nmoveable = yes\nclick_to_front = yes\nshow_sound = menu_open_window\nhide_sound = menu_close_window\nbackground = { name = "frame" quadTextureSprite = "GFX_tiled_plain_bg" }\n'
    gui=block('guiTypes',''.join(launchers)+block('containerWindowType',frame+''.join(widgets)))
    script='context_type = player_context\nwindow_name = "RUS_industrial_planning_window"\ndirty = RUS_ip_dirty\nai_enabled = { always = no }\n'+block('visible','RUS_ip_available = yes\nhas_country_flag = RUS_ip_open')
    script+=block('triggers',''.join(block(k,v) for k,v in gt.items()))+block('properties','ip_progressbar = { frame = RUS_ip_progress_frame }\n')+block('effects',''.join(geffects))
    gfx=[]
    for w,h in sorted(card_sizes):
        gfx.append(block('corneredTileSpriteType',f'name = "GFX_RUS_ip_card_{w}x{h}"\nsize = {{ x = {w} y = {h} }}\ntextureFile = "gfx/interface/tiles/tiled_research_bg.dds"\nborderSize = {{ x = 32 y = 32 }}\ntilingCenter = yes\neffectFile = "gfx/FX/buttonstate_nodowneffect.lua"\nalwaystransparent = yes\n'))
    for name in ['map','selected','offline','connected','cell_button','progress']+[f'region_{c["id"]}' for c in cells]+[f'link_{e["a"]}_{e["b"]}' for e in data['edge_sprites']]:
        frames={'cell_button':3,'progress':21}.get(name,1)
        gfx.append(block('spriteType',f'name = "GFX_RUS_ip_{name}"\ntexturefile = "gfx/interface/RUS_industrial_planning/{name}.png"\nnoOfFrames = {frames}\ntransparencecheck = yes\n'))
    for k,asset in ICONS.items():
        path={8:'gfx/interface/ideas/generic_syndicalist_worker.png',9:'gfx/interface/goals/ITA_urban.png'}.get(k,f'gfx/interface/decisions/{asset}.dds')
        gfx.append(block('spriteType',f'name = "GFX_RUS_ip_facility_{k}"\ntexturefile = "{path}"\n'))
    for key,(path,_) in SUPPLY_ICONS.items():
        gfx.append(block('spriteType',f'name = "GFX_RUS_ip_{key}"\ntexturefile = "{path}"\n'))
    for key,asset in [('development',ICONS[7]),('workers',ICONS[8]),('power',ICONS[3]),('freight',ICONS[6])]:
        path='gfx/interface/ideas/generic_syndicalist_worker.png' if key=='workers' else f'gfx/interface/decisions/{asset}.dds'
        gfx.append(block('spriteType',f'name = "GFX_RUS_ip_metric_{key}"\ntexturefile = "{path}"\n'))
    gfx.append(block('spriteType','name = "GFX_RUS_ip_action"\ntexturefile = "gfx/interface/rus_intro_theme/continue.png"\n'))
    gfx.append(block('spriteType','name = "GFX_RUS_ip_tab"\ntexturefile = "gfx/interface/rus_intro_theme/tab.png"\nnoOfFrames = 2\n'))
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
