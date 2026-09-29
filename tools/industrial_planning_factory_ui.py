"""Local factory board, native icon reuse and its three localisation catalogs."""
from __future__ import annotations

from industrial_planning_factory import (
    P, WIDTH, HEIGHT, HUB, COAL, IRON, ROCKS, COST, PROJECTS, CELLS,
    block, setv, add, cv, iff, render_economy,
)

LANGS = ('simp_chinese', 'english', 'russian')


def render_outputs():
    triggers, effects, actions = render_economy()
    loc = {lang: {} for lang in LANGS}

    def L(key, zh, en, ru=None):
        for lang, value in zip(LANGS, (zh, en, ru or en)):
            loc[lang][P+key] = value
        return P+key

    L('title', '国家计划委员会 · 工业规划沙盘', 'State Planning Commission · Factory Planning', 'Госплан · Планирование промышленности')
    L('open_tt', '§Y工业规划沙盘§!\n布置局部厂区、连接运输线，组织煤铁、电力、钢材与机械的连续生产。', '§YFactory planning§!\nLay out a local factory, connect its transport lines and organise continuous production.')
    L('test_category', '工业规划测试', 'Factory Planning Test')
    L('test_category_desc', '在新的工业基地上，勘探、运输与制造必须形成一个完整的生产体系。', 'Prospecting, transport and manufacturing must form a complete system in the new industrial base.')
    L('enable_gui', '启用工业规划沙盘（测试）', 'Enable Factory Planning (Test)')
    L('enable_gui_desc', '先在沙盘上检验我们的工业布局，再让未来的工业基地沿着规划发展。', 'Test an industrial layout on the planning board.')
    L('enable_gui_tt', '解锁独立入口并打开工业规划沙盘。布置完成后点击“开始生产”，启动 §Y1800§! 天连续生产。', 'Unlock the separate launcher and open the factory board. Select Start production when ready to begin the §Y1800§!-day programme.')
    L('summary', '[GetRUSIPPlanStatus]   |   交付目标 §Y500§! 机械   |   完成度 §G[?RUS_ip_score|0]%§!', '[GetRUSIPPlanStatus]  |  Target §Y500§! machines  |  §G[?RUS_ip_score|0]%§! complete')
    L('not_started', '§Y自由布置 · 尚未计时§!', '§YLayout phase · clock stopped§!')
    L('active', '剩余 §Y[?RUS_ip_days_left|0]§! 天', '§Y[?RUS_ip_days_left|0]§! days remaining')
    L('ended', '§Y本期生产已结束§!', '§YProduction concluded§!')
    L('board_title', '厂区布局   煤矿／铁矿须建在对应矿点', 'Factory layout · mines require matching deposits')
    L('board_note', '运输线须从 §YD6 调度站§! 逐格接通。设施与线路最高 §Y3§! 级。\n同一格可同时拥有设施和运输线；点击格子后在右侧建设。', 'Connect tile by tile to the §YD6 depot§!. Facilities and lines reach level §Y3§!.\nA tile can hold both a facility and a line. Select a tile to build on the right.')
    L('legend', '§Y◆§! 选中   §G●§! 接通   §R×§! 断线   §YⅡ§! 停机', '§Y◆§! selected   §G●§! connected   §R×§! disconnected   §YⅡ§! stopped')
    L('budget', '建设投资\n§Y[?RUS_ip_budget|1]§!', 'Investment\n§Y[?RUS_ip_budget|1]§!')
    for key, zh, en in [('coal', '煤炭库存', 'Coal stock'), ('iron', '铁矿库存', 'Iron stock'), ('steel', '钢材库存', 'Steel stock'), ('machines', '累计交付', 'Delivered')]:
        L(key, f'{zh}\n§Y[?RUS_ip_{key}|1]§!', f'{en}\n§Y[?RUS_ip_{key}|1]§!')
    L('power', '电力／满产需求\n§Y[?RUS_ip_power_total|1] / [?RUS_ip_power_demand|1]§!', 'Power / full demand\n§Y[?RUS_ip_power_total|1] / [?RUS_ip_power_demand|1]§!')
    L('budget_tt', '§Y建设投资§!\n初始：§Y40§!\n每交付 §Y1§! 单位机械，建设投资：§G+1.00§!\n拆除退还该设施或线路的实付投资。\n投资只用于本沙盘；没有固定拨款。', '§YConstruction investment§!\nInitial: §Y40§!\nEach delivered machine returns §G+1.00§! investment.\nDemolition refunds the actual investment paid.\nThis board has its own budget and no periodic grant.')
    L('stock_tt', '§Y厂区库存§!\n所有已接通设施共用原料。每日自动采矿、发电、炼钢、制造机械。\n缺料或缺电时按可用数量生产，不产生负库存。', '§YFactory stock§!\nConnected facilities share materials. Mining, power, steel and machinery run each day.\nShortages limit output to available inputs; stocks cannot become negative.')
    L('power_tt', '§Y电力§!\n电力当日生产、当日使用，不入库。先供炼钢，再供机械制造。\n满产需求按已接通且开机的设施计算；缺煤时电站也会减产。', '§YPower§!\nProduced and used daily; not stored. Steelworks draw power before machine works.\nDemand assumes full production at connected, enabled facilities. Coal shortages reduce generation.')
    L('selected', '地块 [GetRUSIPTile] · [GetRUSIPTerrain]', 'Tile [GetRUSIPTile] · [GetRUSIPTerrain]')
    L('detail', '设施：§Y[GetRUSIPType]§!  [?RUS_ip_sel_level|0] 级\n运输线：§Y[?RUS_ip_sel_rail|0]§! 级   接通能力：§Y[?RUS_ip_sel_route|0]§! 级\n有效生产等级：§G[?RUS_ip_sel_effective|0]§!\n[GetRUSIPSelectedStatus]', 'Facility: §Y[GetRUSIPType]§!  Lv [?RUS_ip_sel_level|0]\nLine: §Y[?RUS_ip_sel_rail|0]§!   Route capacity: §Y[?RUS_ip_sel_route|0]§!\nEffective production level: §G[?RUS_ip_sel_effective|0]§!\n[GetRUSIPSelectedStatus]')
    for key, zh, en in [('plain','工业用地','Industrial land'),('coal_site','煤矿点','Coal deposit'),('iron_site','铁矿点','Iron deposit'),('rock','岩壁 · 不可建设','Rock · no construction'),('hub','调度站','Depot')]:
        L('terrain_'+key,zh,en)
    L('rock_tile','岩壁','Rock')
    L('type_0','空地','Empty')
    for kind,(zh,en,_) in PROJECTS.items(): L(f'type_{kind}',zh,en)
    for key, zh, en in [
        ('hub','§G厂内运输网络的固定起点§!','§GFixed origin of the factory network§!'),
        ('empty','选择设施或铺设运输线。','Select a facility or place a line.'),
        ('rock','§R此处无法建设。§!','§RThis tile cannot be developed.§!'),
        ('paused','§Y设施已停机；线路仍可通行。§!','§YStopped; the line remains passable.§!'),
        ('offline','§R未接通调度站，无法生产。§!','§RDisconnected from the depot; no output.§!'),
        ('limited','§Y沿途线路限制产能，升级最薄弱路段。§!','§YThe route limits output; upgrade its weakest segments.§!'),
        ('ready','§G已接通；产量取决于原料与电力。§!','§GConnected; output depends on materials and power.§!'),
    ]: L('status_'+key,zh,en)
    L('forecast', '按当前布局折算／30天\n采煤：§G+[?RUS_ip_coal_month|1]§!   采铁：§G+[?RUS_ip_iron_month|1]§!\n炼钢：§G+[?RUS_ip_steel_month|1]§!   交付：§G+[?RUS_ip_machine_month|1]§!\n投资回流：§G+[?RUS_ip_investment_month|1]§!', 'Current daily rates × 30\nCoal: §G+[?RUS_ip_coal_month|1]§!  Iron: §G+[?RUS_ip_iron_month|1]§!\nSteel: §G+[?RUS_ip_steel_month|1]§!  Delivery: §G+[?RUS_ip_machine_month|1]§!\nInvestment return: §G+[?RUS_ip_investment_month|1]§!')
    L('forecast_tt','§Y产量速览§!\n当前下一日产量乘以 30，并非库存净变化或保证交付。库存耗尽、停机或改建会改变后续产量。\n可用电力、库存和接通能力每天及每次操作后重新计算。','§YProduction forecast§!\nNext-day output multiplied by 30, not net stock change or guaranteed deliveries. Depletion and layout changes affect later output.\nPower, stocks and network capacity refresh daily and after actions.')
    L('results','§Y本期结果§!\n累计交付：§G[?RUS_ip_machines|1]§!／500\n投资回流：§G+[?RUS_ip_earned|1]§!\n§Y生产已停止；可重新规划并开始下一次测试。§!','§YFinal results§!\nDelivered: §G[?RUS_ip_machines|1]§! / 500\nInvestment earned: §G+[?RUS_ip_earned|1]§!\n§YProduction stopped. Reset to try another layout.§!')
    L('bottleneck','当前瓶颈：[GetRUSIPBottleneck]','Bottleneck: [GetRUSIPBottleneck]')
    for number,zh,en in [(0,'§G当前产线正常§!','§GCurrent line is supplied§!'),(1,'§R煤炭不足§!','§RNot enough coal§!'),(2,'§R铁矿不足§!','§RNot enough iron§!'),(3,'§R电力不足§!','§RNot enough power§!'),(4,'§R钢材不足§!','§RNot enough steel§!'),(5,'§Y尚无接通的机械厂§!','§YNo connected machine works§!')]:
        L(f'bottleneck_{number}',zh,en)
    L('network','接通地块 §G[?RUS_ip_connected_count|0]§!   |   断线设施 §R[?RUS_ip_offline_count|0]§!','Connected tiles §G[?RUS_ip_connected_count|0]§!  |  Disconnected facilities §R[?RUS_ip_offline_count|0]§!')

    recipes={
        1:('每日煤炭产出：§G+0.30§!','Daily coal output: §G+0.30§!'),
        2:('每日铁矿产出：§G+0.30§!','Daily iron output: §G+0.30§!'),
        3:('每日煤炭消耗：§R-0.10§!\n每日电力供应：§G+0.60§!','Daily coal consumption: §R-0.10§!\nDaily power supply: §G+0.60§!'),
        4:('每日煤炭消耗：§R-0.20§!\n每日铁矿消耗：§R-0.20§!\n每日电力需求：§R+0.40§!\n每日钢材产出：§G+0.20§!','Daily coal consumption: §R-0.20§!\nDaily iron consumption: §R-0.20§!\nDaily power demand: §R+0.40§!\nDaily steel output: §G+0.20§!'),
        5:('每日钢材消耗：§R-0.40§!\n每日电力需求：§R+0.20§!\n每日机械交付：§G+0.20§!','Daily steel consumption: §R-0.40§!\nDaily power demand: §R+0.20§!\nDaily machinery delivery: §G+0.20§!'),
    }
    for kind,(zh,en,_) in PROJECTS.items():
        L(f'build_{kind}',zh,en)
        L(f'cost_{kind}',f'投资 §R-{COST[kind]}§! · 每级',f'§R-{COST[kind]}§! / level')
        site='对应矿点' if kind in (1,2) else '普通工业用地'
        site_en='a matching deposit' if kind in (1,2) else 'ordinary industrial land'
        L(f'build_{kind}_tt',f'§Y{zh}§!\n\n设施等级：§G+1§!\n建设投资：§R-{COST[kind]}§!\n\n§Y每级满产效果：§!\n{recipes[kind][0]}\n\n须位于{site}，最多 §Y3§! 级；不能覆盖其他设施。\n接通调度站后自动运行，沿途最低线路等级限制产能；缺料、缺电按比例减产。',f'§Y{en}§!\n\nFacility level: §G+1§!\nInvestment: §R-{COST[kind]}§!\n\n§YAt full production, per level:§!\n{recipes[kind][1]}\n\nRequires {site_en}; maximum level §Y3§!. Cannot replace another facility.\nConnect to the depot to operate. Weak route segments limit capacity; shortages limit output.')
    for key,zh,en in [('rail','厂内运输线','Transport line'),('remove','拆除设施','Remove plant'),('remove_rail','拆除线路','Remove line'),('switch','停机／开机','Stop / run'),('refresh','刷新产量','Refresh'),('start','开始生产','Start production'),('help','玩法介绍','How to play'),('back','返回厂区','Back to factory'),('restart','重新规划','Reset board'),('confirm_restart','确认重置','Confirm reset')]:L(key,zh,en)
    L('cost_rail','投资 §R-1§! · 每级','§R-1§! / level')
    L('rail_tt','§Y厂内运输线§!\n\n线路等级：§G+1§!\n建设投资：§R-1§!\n\n与上下左右的线路相连，须连通 §YD6 调度站§!。\n线路和设施可在同一格，最高 §Y3§! 级。有效产能取设施等级与最佳路线最薄弱等级中的较低值。\n这是沙盘内运输线。','§YFactory transport line§!\n\nLine level: §G+1§!\nInvestment: §R-1§!\n\nConnect through orthogonal neighbours to the §YD6 depot§!.\nShares tiles with facilities; maximum level §Y3§!. Effective capacity is limited by the weakest segment along the best route.')
    L('remove_tt','§Y拆除设施§!\n返还该设施实际支付的全部建设投资。\n保留运输线、库存和累计交付。调度站不能拆除。','§YRemove facility§!\nRefund all investment paid for this facility.\nKeep the line, stocks and deliveries. The depot cannot be removed.')
    L('remove_rail_tt','§Y拆除线路§!\n返还该线路实际支付的全部建设投资。\n保留设施；依赖此线路的设施可能断线。调度站不能拆除。','§YRemove line§!\nRefund all investment paid for this line.\nKeep its facility; downstream facilities may disconnect. The depot cannot be removed.')
    L('switch_tt','§Y停机／开机§!\n停机后该设施不生产、不消耗原料或电力；该格运输线仍然可用。','§YStop / run§!\nA stopped facility neither produces nor consumes materials or power. Its line still carries traffic.')
    L('refresh_tt','重新计算接通状态、产能和下一日产量。不会推进日期或结算生产。','Recalculate connectivity, capacity and next-day output without advancing time or producing goods.')
    L('start_tt','开始 §Y1800§! 天连续生产。设施按游戏日期自动运行，关闭窗口后也继续。\n目标：累计交付 §Y500§! 单位机械。期满停止生产并保留结果。','Begin §Y1800§! days of continuous production. Facilities run each game day, even with this window closed.\nGoal: deliver §Y500§! machines. Production stops at expiry and results remain visible.')
    L('restart_tt','§Y重新规划§!\n再次确认后清空本沙盘的设施、线路、库存、累计交付和计时，恢复初始投资。\n本沙盘独立计分，不发放真实工厂，不影响旧一五计划。','§YReset board§!\nConfirm again to clear this board, its stocks, deliveries and clock, and restore initial investment.\nThis independent prototype does not grant real factories or alter the old Five-Year Plan.')
    L('footnote','独立测试沙盘 · 机械为交付分数 · 生产随游戏日期推进','Independent test board · machinery counts as delivery score · production follows game time')
    L('help_title','工业规划沙盘 · 玩法介绍','Factory Planning · How to Play')
    help_zh=[
        '§Y一、先布置，再开工§!\n点击测试决议打开沙盘。初始建设投资 §Y40§!，煤 §Y6§!、铁 §Y4§!、钢 §Y2§!。先布置厂区，再点击“开始生产”：在 §Y1800§! 天内交付 §Y500§! 单位机械。时间随游戏日期推进，关闭窗口不会暂停。',
        '§Y二、固定矿点与生产链§!\n煤矿和铁矿须建在对应矿点。电站、钢铁厂和机械厂建在普通地块。岩壁不可建设。\n煤铁 → 电力与钢材 → 机械交付。电力当天使用，原料可入库；已接通设施共用库存。',
        '§Y三、运输线决定布局§!\n在设施所在格及途经格铺设运输线，逐格接到 §YD6 调度站§!。只连上下左右。\n设施和线路最高 §Y3§! 级。三级设施经过一级线路，最多按一级生产；可以升级薄弱路段，也可以另建较好的路线。',
        '§Y四、找出真正的瓶颈§!\n每级钢铁厂满产需煤 §R-0.20§!、铁 §R-0.20§!、电 §R+0.40§!，产钢 §G+0.20§!／日。每级机械厂需钢 §R-0.40§!、电 §R+0.20§!，交付机械 §G+0.20§!／日。\n先保证煤、电、钢足够，再扩机械厂。按钮悬浮提示列出每级效果。',
        '§Y五、扩产与重新布置§!\n每交付 §Y1§! 单位机械，投资回流 §G+1.00§!；积累后扩矿、扩产或升级线路。没有固定拨款。\n拆除退还实际投资，便于调整布局。停机可以节省原料和电力，线路仍然通行。采矿、发电、炼钢、机械按此顺序每日结算。',
        '§Y六、预估与期满§!\n产量速览显示下一日产量乘以 §Y30§!，不保证原料足够维持整月。库存耗尽后产量会改变；查看瓶颈与库存变化再调整。\n期满停止生产，保留交付量与完成度。两次点击重置后可以重玩。这是独立玩法测试，未接管旧一五计划，也不发放真实工厂。',
    ]
    help_en=[
        '§Y1. Plan, then start§!\nTake the test decision. Start with §Y40§! investment, §Y6§! coal, §Y4§! iron and §Y2§! steel. Arrange the factory, then Start production. Deliver §Y500§! machines in §Y1800§! game days. Closing this window does not pause production.',
        '§Y2. Deposits and production§!\nMines require matching deposits. Power stations, steelworks and machine works use ordinary tiles. Rocks cannot be developed.\nCoal and iron feed power and steel, then machinery. Power is used daily; materials can be stored. Connected facilities share stocks.',
        '§Y3. Lay out transport§!\nPlace lines under facilities and along a route to the §YD6 depot§!, using orthogonal neighbours.\nFacilities and lines reach level §Y3§!. A level-three plant on a level-one route produces at level one. Upgrade weak segments or build a better route.',
        '§Y4. Find the bottleneck§!\nA steelworks level uses §R0.20§! coal, §R0.20§! iron and §R0.40§! power to produce §G0.20§! steel daily. A machinery level uses §R0.40§! steel and §R0.20§! power to deliver §G0.20§! machines.\nSupply coal, power and steel before adding machinery. Hover actions for recipes.',
        '§Y5. Expand and rearrange§!\nEach delivered machine returns §G1.00§! investment. Expand mines, plants and lines with the proceeds. There are no periodic grants.\nDemolition refunds actual investment. Stopping plants saves resources; lines remain open. Daily order: mines, power, steel, machinery.',
        '§Y6. Forecasts and expiry§!\nThe forecast multiplies next-day output by §Y30§!; it does not guarantee a month of supply. Depleting stocks changes output.\nAt expiry production stops and results remain. Confirm a reset twice to replay. This independent prototype has no native factory rewards and does not replace the old Five-Year Plan.',
    ]
    for i,(zh,en) in enumerate(zip(help_zh,help_en)):L(f'help_{i}',zh,en)

    definitions=[]
    def defined(name,branches):
        definitions.append(block('defined_text',f'name = {name}\n'+''.join(block('text',(block('trigger',cond) if cond else '')+f'localization_key = {key}\n') for cond,key in branches)))
    defined('GetRUSIPPlanStatus',[('has_country_flag = RUS_ip_finished',P+'ended'),('has_country_flag = RUS_ip_started',P+'active'),('',P+'not_started')])
    defined('GetRUSIPType',[(cv('sel_type','=',k),P+f'type_{k}') for k in PROJECTS]+[('',P+'type_0')])
    defined('GetRUSIPTile',[(cv('selected','=',c['id']),L(f'tile_{c["id"]}',c['label'],c['label'])) for c in CELLS])
    def terrain(i):return 'hub' if i==HUB else 'rock' if i in ROCKS else 'coal_site' if i in COAL else 'iron_site' if i in IRON else 'plain'
    defined('GetRUSIPTerrain',[(cv('selected','=',c['id']),P+'terrain_'+terrain(c['id'])) for c in CELLS])
    defined('GetRUSIPSelectedStatus',[(cv('selected','=',HUB),P+'status_hub'),(block('OR',''.join(cv('selected','=',i) for i in sorted(ROCKS))),P+'status_rock'),(cv('sel_type','=',0),P+'status_empty'),(cv('sel_paused','=',1),P+'status_paused'),(cv('sel_route','=',0),P+'status_offline'),(cv('sel_route','<',P+'sel_level'),P+'status_limited'),('',P+'status_ready')])
    defined('GetRUSIPBottleneck',[(cv('bottleneck','=',i),P+f'bottleneck_{i}') for i in range(6)])
    for c in CELLS:
        i=c['id']
        defined(f'GetRUSIPType{i}',[(cv(f'n{i}_type','=',k),P+f'type_{k}') for k in PROJECTS]+[('',P+'type_0')])
        name={'hub':'调度站','rock':'岩壁','coal_site':'煤矿点','iron_site':'铁矿点','plain':'工业用地'}[terrain(i)]
        L(f'node_{i}_tt',f'§Y{c["label"]} · {name}§!\n设施：[GetRUSIPType{i}]，§Y[?RUS_ip_n{i}_level|0]§! 级\n线路等级：§Y[?RUS_ip_n{i}_rail|0]§!\n接通能力：§Y[?RUS_ip_n{i}_route|0]§!\n有效生产等级：§G[?RUS_ip_n{i}_effective|0]§!\n点击选择，在右侧建设或升级。',f'§Y{c["label"]} · $RUS_ip_terrain_{terrain(i)}$§!\n[GetRUSIPType{i}], level §Y[?RUS_ip_n{i}_level|0]§!\nLine: §Y[?RUS_ip_n{i}_rail|0]§!\nRoute: §Y[?RUS_ip_n{i}_route|0]§!\nEffective level: §G[?RUS_ip_n{i}_effective|0]§!\nSelect to build or upgrade on the right.')
        L(f'tile_levels_{i}',f'厂[?RUS_ip_n{i}_level|0] · 线[?RUS_ip_n{i}_rail|0]',f'P[?RUS_ip_n{i}_level|0] · L[?RUS_ip_n{i}_rail|0]')

    launchers=[]; launcher_scripts=[]
    for suffix,y,condition in [('',-121,'NOT = { GER_is_in_mitteleuropa = yes }'),('_above_mitteleuropa',-198,'GER_is_in_mitteleuropa = yes')]:
        launchers.append(block('containerWindowType',f'name = "RUS_industrial_planning_launcher{suffix}"\nposition = {{ x = -79 y = {y} }}\nsize = {{ width = 77 height = 77 }}\nbackground = {{ name = "Background" quadTextureSprite = "GFX_equipment_role_selector_tiled_window" }}\nbackground = {{ name = "Background" quadTextureSprite = "GFX_tiled_research_bg" }}\nbuttonType = {{ name = "ip_open" position = {{ x = 9 y = 7 }} scale = 1.8 quadTextureSprite = "GFX_decision_generic_industry" pdx_tooltip = "RUS_ip_open_tt" clicksound = click_ok }}\n'))
        launcher_scripts.append(block('RUS_industrial_planning_launcher'+suffix,f'context_type = player_context\nparent_window_name = raid_filter\nwindow_name = "RUS_industrial_planning_launcher{suffix}"\nai_enabled = {{ always = no }}\n'+block('visible','RUS_ip_available = yes\n'+condition)+block('effects','ip_open_click = { hidden_effect = { RUS_ip_toggle = yes } }')))
    widgets=[]; gt={}; geffects=[]; gfx=[]; cards=set()
    def visibility(name,condition='',page='board'):
        base='NOT = { has_country_flag = RUS_ip_help_open }\n' if page=='board' else 'has_country_flag = RUS_ip_help_open\n' if page=='help' else ''
        if base+condition:gt[name+'_visible']=base+condition
    def text(name,key,x,y,w,h=24,font='hoi_16mbs',center=False,condition='',page='board',tip=''):
        tooltip=f'pdx_tooltip = "{tip}" ' if tip else ''
        widgets.append(f'instantTextBoxType = {{ name = "{name}" position = {{ x = {x} y = {y} }} text = "{key}" font = "{font}" maxWidth = {w} maxHeight = {h} format = {"center" if center else "left"} fixedsize = yes {tooltip}alwaystransparent = {"no" if tip else "yes"} }}\n');visibility(name,condition,page)
    def icon(name,sprite,x,y,scale=1,condition='',page='board',tip=''):
        tooltip=f'pdx_tooltip = "{tip}" ' if tip else ''
        widgets.append(f'iconType = {{ name = "{name}" position = {{ x = {x} y = {y} }} spriteType = "{sprite}" scale = {scale} {tooltip}alwaystransparent = {"no" if tip else "yes"} }}\n');visibility(name,condition,page)
    def button(name,key,x,y,tip,action,enable='',sprite='GFX_RUS_ip_tab',condition='',page='board',scale=1):
        shortcut='shortcut = "ESCAPE" ' if name=='ip_close' else ''
        widgets.append(f'buttonType = {{ name = "{name}" position = {{ x = {x} y = {y} }} scale = {scale} quadTextureSprite = "{sprite}" buttonText = "{key}" buttonFont = "hoi_16mbs" pdx_tooltip = "{tip}" {shortcut}clicksound = click_default }}\n')
        if enable:gt[name+'_click_enabled']=enable
        visibility(name,condition,page)
        visible_condition=gt.get(name+'_visible','')
        guard='RUS_ip_available = yes\nhas_country_flag = RUS_ip_open\n'+visible_condition+(enable+'\n' if enable else '')
        geffects.append(block(name+'_click',block('hidden_effect',iff(guard,action))))
    def card(name,x,y,w,h,page='board'):
        cards.add((w,h));icon(name,f'GFX_RUS_ip_card_{w}x{h}',x,y,page=page)
    text('ip_title',P+'title',32,18,1204,32,'hoi_24header',True,page='all')
    text('ip_summary',P+'summary',36,57,1200,25,'hoi_20b',page='all')
    for index,(key,sprite,scale) in enumerate([('budget','funds',1.6),('coal','facility_1',1),('iron','facility_2',1),('steel','facility_4',1),('machines','facility_5',1),('power','facility_3',1)]):
        x=32+204*index
        card('ip_inventory_bg_'+key,x,97,196,66)
        tip=P+('budget_tt' if key=='budget' else 'power_tt' if key=='power' else 'stock_tt')
        icon('ip_inventory_icon_'+key,'GFX_RUS_ip_'+sprite,x+12,114,scale,tip=tip)
        text('ip_inventory_'+key,P+key,x+54,109,138,45,tip=tip)
    text('ip_board_title',P+'board_title',32,175,690,22)
    bx,by,step=32,207,84
    # Every background has its own page visibility, including the selection.
    for c in CELLS:
        i=c['id'];x,y=bx+c['x']*step,by+c['y']*step
        button(f'ip_cell_{i}','',x,y,P+f'node_{i}_tt',setv('selected',i)+'clr_country_flag = RUS_ip_restart_armed\nRUS_ip_refresh = yes\n',sprite='GFX_RUS_ip_tile')
        icon(f'ip_selection_{i}','GFX_RUS_ip_selected_tile',x,y,condition=cv('selected','=',i))
    # Lines join the centres, above tile backgrounds and behind plant icons.
    for c in CELLS:
        i=c['id'];x,y=bx+c['x']*step,by+c['y']*step
        for j in c['neighbors']:
            if j<=i:continue
            vertical=j-i==WIDTH
            icon(f'ip_link_{i}_{j}','GFX_RUS_ip_line_v' if vertical else 'GFX_RUS_ip_line_h',x+39,y+39,condition=cv(f'n{i}_rail','>',0)+cv(f'n{j}_rail','>',0))
    for c in CELLS:
        i=c['id'];x,y=bx+c['x']*step,by+c['y']*step
        text(f'ip_coordinate_{i}',P+f'tile_{i}',x+6,y+5,33,19,'hoi_16mbs',condition='')
        if i in ROCKS:
            text(f'ip_rock_{i}',P+'rock_tile',x+5,y+27,70,45,'hoi_16mbs',True)
        elif i==HUB:
            icon(f'ip_hub_icon_{i}','GFX_RUS_ip_hub',x+24,y+24,32/34)
            text(f'ip_hub_text_{i}',P+'terrain_hub',x+4,y+61,72,18,'hoi_16mbs',True)
        else:
            if i in COAL|IRON:
                kind=1 if i in COAL else 2
                icon(f'ip_deposit_{i}','GFX_RUS_ip_facility_'+str(kind),x+24,y+26,condition=cv(f'n{i}_type','=',0))
            for kind in PROJECTS:
                icon(f'ip_plant_{i}_{kind}','GFX_RUS_ip_facility_'+str(kind),x+24,y+26,condition=cv(f'n{i}_type','=',kind))
            text(f'ip_levels_{i}',P+f'tile_levels_{i}',x+3,y+61,74,18,'hoi_16mbs',True,condition=block('OR',cv(f'n{i}_type','>',0)+cv(f'n{i}_rail','>',0)))
        for key,label,cond in [
            ('on','§G●§!',cv(f'n{i}_route','>',0)),
            ('off','§R×§!',cv(f'n{i}_route','=',0)+cv(f'n{i}_type','>',0)),
            ('paused','§YⅡ§!',cv(f'n{i}_paused','=',1)),
        ]:text(f'ip_{key}_{i}',label,x+53,y+4,23,20,center=True,condition=cond)
    text('ip_legend',P+'legend',32,717,680,22)
    text('ip_board_note',P+'board_note',32,742,680,42)
    text('ip_selected',P+'selected',738,175,510,26,'hoi_20b')
    card('ip_detail_bg',738,207,510,116)
    text('ip_detail',P+'detail',754,221,480,94)
    for index,kind in enumerate([1,2,3,4,5,'rail']):
        x,y=738+(index%2)*246,340+(index//2)*68
        key=f'build_{kind}' if isinstance(kind,int) else 'rail'
        icon_key=f'facility_{kind}' if isinstance(kind,int) else 'line'
        button('ip_'+key,'',x,y,P+key+'_tt',f'RUS_ip_{key} = yes\n',f'RUS_ip_can_{key} = yes',sprite='GFX_RUS_ip_action')
        icon('ip_action_icon_'+key,'GFX_RUS_ip_'+icon_key,x+19,y+14)
        text('ip_action_title_'+key,P+key,x+55,y+8,170,22,center=True)
        text('ip_action_cost_'+key,P+f'cost_{kind}',x+52,y+33,177,20,'hoi_16mbs',True)
    for index,key in enumerate(['switch','remove','remove_rail','refresh']):
        button('ip_'+key,P+key,738+index*129,550,P+key+'_tt',f'RUS_ip_{key} = yes\n',f'RUS_ip_can_{key} = yes' if key!='refresh' else '')
    text('ip_forecast',P+'forecast',746,602,480,88,tip=P+'forecast_tt',condition='NOT = { has_country_flag = RUS_ip_finished }')
    text('ip_results',P+'results',746,602,480,88,condition='has_country_flag = RUS_ip_finished')
    text('ip_bottleneck',P+'bottleneck',746,698,500,26,condition='NOT = { has_country_flag = RUS_ip_finished }')
    text('ip_network',P+'network',746,738,500,25)
    button('ip_start',P+'start',32,801,P+'start_tt','RUS_ip_start = yes\n','RUS_ip_editing = yes',condition='NOT = { has_country_flag = RUS_ip_started }')
    button('ip_restart',P+'restart',175,801,P+'restart_tt','RUS_ip_arm_restart = yes\n',condition='NOT = { has_country_flag = RUS_ip_restart_armed }')
    button('ip_confirm_restart',P+'confirm_restart',175,801,P+'restart_tt','RUS_ip_confirm_restart = yes\n',condition='has_country_flag = RUS_ip_restart_armed')
    text('ip_footnote',P+'footnote',320,809,760,21,'hoi_16mbs')
    button('ip_help',P+'help',1125,801,'','RUS_ip_toggle_help = yes\n')
    button('ip_back',P+'back',575,801,'','RUS_ip_toggle_help = yes\n',page='help')
    text('ip_help_title',P+'help_title',80,114,1120,36,'hoi_24header',True,page='help')
    for i in range(6):text(f'ip_help_{i}',P+f'help_{i}',58+(594 if i>=3 else 0),181+(i%3)*194,570,173,page='help')
    button('ip_close','',1238,9,'CLOSE','RUS_ip_close_effect = yes\n',sprite='GFX_closebutton',page='all')
    frame='name = "RUS_industrial_planning_window"\nposition = { x = -640 y = -425 }\nsize = { width = 1280 height = 850 }\norientation = center\nmoveable = yes\nclick_to_front = yes\nshow_sound = menu_open_window\nhide_sound = menu_close_window\nbackground = { name = "frame" quadTextureSprite = "GFX_tiled_plain_bg" }\n'
    gui=block('guiTypes',''.join(launchers)+block('containerWindowType',frame+''.join(widgets)))
    script='context_type = player_context\nwindow_name = "RUS_industrial_planning_window"\ndirty = RUS_ip_dirty\nai_enabled = { always = no }\n'+block('visible','RUS_ip_available = yes\nhas_country_flag = RUS_ip_open\n')
    script+=block('triggers',''.join(block(k,v) for k,v in gt.items()))+block('effects',''.join(geffects))
    def tile_sprite(name,w,h,texture,border):
        gfx.append(block('corneredTileSpriteType',f'name = "GFX_RUS_ip_{name}"\nsize = {{ x = {w} y = {h} }}\ntextureFile = "{texture}"\nborderSize = {{ x = {border} y = {border} }}\ntilingCenter = yes\neffectFile = "gfx/FX/buttonstate_nodowneffect.lua"\n'))
    for w,h in sorted(cards):tile_sprite(f'card_{w}x{h}',w,h,'gfx/interface/tiles/tiled_research_bg.dds',32)
    tile_sprite('tile',80,80,'gfx/interface/tiles/tiled_plain_bg.dds',24)
    tile_sprite('selected_tile',80,80,'gfx/interface/tiles/tiled_research_bg.dds',24)
    tile_sprite('line_h',84,3,'gfx/interface/transp_white.dds',1)
    tile_sprite('line_v',3,84,'gfx/interface/transp_white.dds',1)
    sprites={f'facility_{k}':(f'gfx/interface/decisions/{asset}.dds',1) for k,(_,_,asset) in PROJECTS.items()}
    sprites.update(line=('gfx/interface/decisions/decision_generic_train.dds',1),funds=('gfx/texticons/bag_of_money.png',1),hub=('gfx/interface/abilitylist/ability_extra_supplies.dds',1),action=('gfx/interface/rus_intro_theme/continue.png',1),tab=('gfx/interface/rus_intro_theme/tab.png',2))
    for key,(path,frames) in sprites.items():gfx.append(block('spriteType',f'name = "GFX_RUS_ip_{key}"\ntexturefile = "{path}"\nnoOfFrames = {frames}\n'))
    header='# Generated by tools/generate_industrial_planning.py. Edit the renderer, then --write.\n'
    category=block(P+'test_category','icon = GFX_decision_category_generic_industry\nallowed = { original_tag = RUS }\nvisible = { is_ai = no NOT = { has_country_flag = RUS_ip_ui_unlocked } }\n')
    decisions=block(P+'test_category',block(P+'enable_gui','icon = GFX_decision_generic_industry\nfire_only_once = yes\ncost = 0\nvisible = { is_ai = no NOT = { has_country_flag = RUS_ip_ui_unlocked } }\navailable = { original_tag = RUS is_ai = no }\ncomplete_effect = { custom_effect_tooltip = RUS_ip_enable_gui_tt hidden_effect = { RUS_ip_enable_gui = yes } }\nai_will_do = { base = 0 }\n'))
    outputs={
        'common/scripted_triggers/RUS_industrial_planning_triggers.txt':header+'\n'.join(triggers),
        'common/decisions/categories/RUS_industrial_planning_categories.txt':header+category,
        'common/decisions/RUS_industrial_planning_decisions.txt':header+decisions,
        'common/scripted_effects/RUS_industrial_planning_effects.txt':header+'\n'.join(effects),
        'common/on_actions/RUS_industrial_planning_on_actions.txt':header+actions,
        'common/dynamic_modifiers/RUS_industrial_planning_modifiers.txt':header+'# Independent factory sandbox: no national economy modifiers.\n',
        'common/scripted_guis/RUS_industrial_planning.txt':header+block('scripted_gui',''.join(launcher_scripts)+block('RUS_industrial_planning_gui',script)),
        'common/scripted_localisation/RUS_industrial_planning_loc.txt':header+'\n'.join(definitions),
        'interface/RUS_industrial_planning.gui':header+gui,
        'interface/RUS_industrial_planning.gfx':header+block('spriteTypes',''.join(gfx)),
    }
    for lang,catalog in loc.items():outputs[f'localisation/{lang}/RUS_industrial_planning_l_{lang}.yml']='l_'+lang+':\n'+''.join(f' {key}:0 "{value.replace(chr(10),r"\n")}"\n' for key,value in catalog.items())
    return outputs
