"""Local factory board, native icon reuse and its three localisation catalogs."""
from __future__ import annotations
from industrial_planning_factory_assets import ASSET_DIR, COLOUR_SPRITES, LEVEL_COLOURS

from industrial_planning_factory import (
    P, WIDTH, HEIGHT, HUBS, REGIONS, COST, PROJECTS, CELLS,
    block, setv, add, cv, iff, render_economy,
)

LANGS = ('simp_chinese', 'english', 'russian')
TILE_SIZE,TILE_STEP=40,42


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
    L('board_note', '[GetRUSIPRegionSummary]\n各区库存、电力独立；共用建设投资、交付目标与计时。', '[GetRUSIPRegionSummary]\nLocal stocks and power; shared investment, deliveries and clock.')
    L('legend', '格子底色表示设施等级，详细信息见悬浮提示。', 'Tile colour shows facility level. Hover for details.')
    for level in (1,2,3):L(f'grade_{level}',f'{level} 级',f'Level {level}')
    L('budget', '建设投资\n§Y[?RUS_ip_budget|1]§!', 'Investment\n§Y[?RUS_ip_budget|1]§!')
    for key, zh, en in [('coal', '本区煤炭', 'Local coal'), ('iron', '本区铁矿', 'Local iron'), ('steel', '本区钢材', 'Local steel'), ('machines', '六区累计交付', 'Total delivered')]:
        L(key, f'{zh}\n§Y[?RUS_ip_{key}|1]§!', f'{en}\n§Y[?RUS_ip_{key}|1]§!')
    L('power', '本区电力／需求\n§Y[?RUS_ip_power_total|1] / [?RUS_ip_power_demand|1]§!', 'Local power / need\n§Y[?RUS_ip_power_total|1] / [?RUS_ip_power_demand|1]§!')
    L('budget_tt', '§Y建设投资§!\n六区共享初始投资：§Y40§!\n每交付 §Y1§! 单位机械，建设投资：§G+1.00§!\n拆除退还该设施或线路的实付投资。\n投资只用于本沙盘；没有固定拨款。', '§YConstruction investment§!\nShared initial investment: §Y40§!\nEach delivered machine returns §G+1.00§! investment.\nDemolition refunds the actual investment paid.\nThis board has its own budget and no periodic grant.')
    L('stock_tt', '§Y[GetRUSIPRegion] · 本区库存§!\n本区已接通设施共用原料，每区初始煤 §Y6§!、铁 §Y4§!、钢 §Y2§!。每日自动生产，缺料、缺电限产。\n各区之间不自动调拨原料或电力；切换地图不重置库存。', '§Y[GetRUSIPRegion] · Local stocks§!\nConnected local facilities share stocks. Each region starts with §Y6§! coal, §Y4§! iron and §Y2§! steel. Shortages limit daily output.\nMaterials and power do not transfer between regions. Changing maps preserves stocks.')
    L('deliveries_tt','§Y六区累计交付§!\n六个厂区同时生产，机械交付合并计分。\n当前六区日产率折算／30天：§G+[?RUS_ip_total_machine_month|1]§!\n每单位机械回流 §G+1.00§! 共享投资；目标 §Y500§!。','§YCombined deliveries§!\nAll six regions operate simultaneously and contribute to the same score.\nCombined next-day rate × 30: §G+[?RUS_ip_total_machine_month|1]§!\nEach machine returns §G+1.00§! shared investment. Target: §Y500§!.')
    L('power_tt', '§Y电力§!\n电力当日生产、当日使用，不入库。先供炼钢，再供机械制造。\n满产需求按已接通且开机的设施计算；缺煤时电站也会减产。', '§YPower§!\nProduced and used daily; not stored. Steelworks draw power before machine works.\nDemand assumes full production at connected, enabled facilities. Coal shortages reduce generation.')
    L('selected', '[GetRUSIPRegion] · [GetRUSIPTile] · [GetRUSIPTerrain]', '[GetRUSIPRegion] · [GetRUSIPTile] · [GetRUSIPTerrain]')
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
    L('forecast', '本区当前产量折算／30天\n采煤：§G+[?RUS_ip_coal_month|1]§!   采铁：§G+[?RUS_ip_iron_month|1]§!\n炼钢：§G+[?RUS_ip_steel_month|1]§!   交付：§G+[?RUS_ip_machine_month|1]§!\n投资回流：§G+[?RUS_ip_investment_month|1]§!', 'Local daily rates × 30\nCoal: §G+[?RUS_ip_coal_month|1]§!  Iron: §G+[?RUS_ip_iron_month|1]§!\nSteel: §G+[?RUS_ip_steel_month|1]§!  Delivery: §G+[?RUS_ip_machine_month|1]§!\nInvestment return: §G+[?RUS_ip_investment_month|1]§!')
    L('forecast_tt','§Y产量速览§!\n当前下一日产量乘以 30，并非库存净变化或保证交付。库存耗尽、停机或改建会改变后续产量。\n可用电力、库存和接通能力每天及每次操作后重新计算。','§YProduction forecast§!\nNext-day output multiplied by 30, not net stock change or guaranteed deliveries. Depletion and layout changes affect later output.\nPower, stocks and network capacity refresh daily and after actions.')
    L('results','§Y本期结果§!\n累计交付：§G[?RUS_ip_machines|1]§!／500\n投资回流：§G+[?RUS_ip_earned|1]§!\n§Y生产已停止；可重新规划并开始下一次测试。§!','§YFinal results§!\nDelivered: §G[?RUS_ip_machines|1]§! / 500\nInvestment earned: §G+[?RUS_ip_earned|1]§!\n§YProduction stopped. Reset to try another layout.§!')
    L('bottleneck','当前瓶颈：[GetRUSIPBottleneck]','Bottleneck: [GetRUSIPBottleneck]')
    for number,zh,en in [(0,'§G当前产线正常§!','§GCurrent line is supplied§!'),(1,'§R煤炭不足§!','§RNot enough coal§!'),(2,'§R铁矿不足§!','§RNot enough iron§!'),(3,'§R电力不足§!','§RNot enough power§!'),(4,'§R钢材不足§!','§RNot enough steel§!'),(5,'§Y尚无接通的机械厂§!','§YNo connected machine works§!')]:
        L(f'bottleneck_{number}',zh,en)
    L('network','接通地块 §G[?RUS_ip_connected_count|0]§!   |   断线设施 §R[?RUS_ip_offline_count|0]§!','Connected tiles §G[?RUS_ip_connected_count|0]§!  |  Disconnected facilities §R[?RUS_ip_offline_count|0]§!')
    profiles=[
        ('煤铁适中，紧凑的工业腹地。','Moderate coal and iron in a compact industrial hinterland.'),
        ('煤铁稀少，可用空间紧凑，适合精简产线。','Sparse deposits and limited space favour compact production.'),
        ('煤少铁略多，厂区沿纵向展开。','Little coal, slightly more iron, and a narrow north–south footprint.'),
        ('煤铁丰富，铁矿更多，适合扩大钢铁产能。','Rich in both ores, with more iron deposits for steel expansion.'),
        ('煤铁丰富且较均衡，建设空间最大。','Abundant, balanced ores with the largest building area.'),
        ('铁多煤少，岩壁较多，煤炭是扩产约束。','Iron-rich, coal-poor and rocky; coal constrains expansion.'),
    ]
    for r,(zh,en) in zip(REGIONS,profiles):
        rid=r['id'];coal,iron,rocks=r['coal'],r['iron'],r['rocks']
        L(f'region_{rid}',r['zh'],r['en'])
        L(f'region_{rid}_active','§Y'+r['zh']+'§!','§Y'+r['en']+'§!')
        L(f'region_{rid}_tab',f'[GetRUSIPRegionTab{rid}]',f'[GetRUSIPRegionTab{rid}]')
        L(f'region_{rid}_summary',f'§Y{r["zh"]}§! · 煤点 §Y{coal}§! · 铁点 §Y{iron}§! · 岩壁 §Y{rocks}§! · 用地 §Y{len(r["cells"])}§!',f'§Y{r["en"]}§! · Coal §Y{coal}§! · Iron §Y{iron}§! · Rocks §Y{rocks}§! · Tiles §Y{len(r["cells"])}§!')
        extra='\n少量矿点为沙盘起步储备。' if rid in (1,2) else ''
        extra_en='\nSmall deposits are sandbox starting reserves.' if rid in (1,2) else ''
        L(f'region_{rid}_tt',f'§Y{r["zh"]}§!\n{zh}\n煤点：§Y{coal}§!；铁点：§Y{iron}§!；岩壁：§Y{rocks}§!。\n新计划随机分布，当前存档内保持不变。{extra}\n点击切换；其他地区继续自动生产。',f'§Y{r["en"]}§!\n{en}\nCoal: §Y{coal}§!; iron: §Y{iron}§!; rocks: §Y{rocks}§!.\nRandom positions per new plan, saved thereafter.{extra_en}\nSwitch maps; other regions keep producing.')

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
    L('rail_tt','§Y厂内运输线§!\n\n线路等级：§G+1§!\n建设投资：§R-1§!\n\n与上下左右的线路相连，须连通 §Y本区调度站§!。\n线路和设施可在同一格，最高 §Y3§! 级。有效产能取设施等级与最佳路线最薄弱等级中的较低值。\n这是沙盘内运输线。','§YFactory transport line§!\n\nLine level: §G+1§!\nInvestment: §R-1§!\n\nConnect through orthogonal neighbours to the §Ylocal depot§!.\nShares tiles with facilities; maximum level §Y3§!. Effective capacity is limited by the weakest segment along the best route.')
    L('remove_tt','§Y拆除设施§!\n返还该设施实际支付的全部建设投资。\n保留运输线、库存和累计交付。调度站不能拆除。','§YRemove facility§!\nRefund all investment paid for this facility.\nKeep the line, stocks and deliveries. The depot cannot be removed.')
    L('remove_rail_tt','§Y拆除线路§!\n返还该线路实际支付的全部建设投资。\n保留设施；依赖此线路的设施可能断线。调度站不能拆除。','§YRemove line§!\nRefund all investment paid for this line.\nKeep its facility; downstream facilities may disconnect. The depot cannot be removed.')
    L('switch_tt','§Y停机／开机§!\n停机后该设施不生产、不消耗原料或电力；该格运输线仍然可用。','§YStop / run§!\nA stopped facility neither produces nor consumes materials or power. Its line still carries traffic.')
    L('refresh_tt','重新计算接通状态、产能和下一日产量。不会推进日期或结算生产。','Recalculate connectivity, capacity and next-day output without advancing time or producing goods.')
    L('start_tt','开始 §Y1800§! 天连续生产。设施按游戏日期自动运行，关闭窗口后也继续。\n目标：累计交付 §Y500§! 单位机械。期满停止生产并保留结果。','Begin §Y1800§! days of continuous production. Facilities run each game day, even with this window closed.\nGoal: deliver §Y500§! machines. Production stops at expiry and results remain visible.')
    L('restart_tt','§Y重新规划§!\n再次确认后清空六区设施、线路、库存、交付与计时，恢复初始投资，并重新随机生成全部六张地图的矿点和岩壁。\n本沙盘独立计分，不发放真实工厂，不影响旧一五计划。','§YReset board§!\nConfirm again to clear all six boards, stocks, deliveries and clock; restore investment and randomise all deposits and rocks.\nThis independent prototype does not grant real factories or alter the old Five-Year Plan.')
    L('footnote','独立测试沙盘 · 机械为交付分数 · 生产随游戏日期推进','Independent test board · machinery counts as delivery score · production follows game time')
    L('help_title','工业规划沙盘 · 玩法介绍','Factory Planning · How to Play')
    help_zh=[
        '§Y一、先布置，再开工§!\n点击测试决议打开沙盘。六区共享投资 §Y40§!，每区煤 §Y6§!、铁 §Y4§!、钢 §Y2§!。先选地区布置厂区，再点击“开始生产”：在 §Y1800§! 天内交付 §Y500§! 单位机械。时间随游戏日期推进，关闭窗口不会暂停。',
        '§Y二、六区禀赋与随机矿点§!\n三大城、西西伯利亚、中西伯利亚与远东，轮廓参考 KR。每区矿点数量不同，新计划随机位置，切图和读档不重抽。城市贫矿区保留少量起步矿点。\n矿山须建在对应矿点；其他设施用普通地块。一级绿、二级蓝、三级金；深灰岩壁不可建。详情和线路等级见悬浮提示。',
        '§Y三、运输线决定布局§!\n在设施所在格及途经格铺设运输线，逐格接到 §Y本区调度站§!。只连上下左右。\n设施和线路最高 §Y3§! 级。三级设施经过一级线路，最多按一级生产；可以升级薄弱路段，也可以另建较好的路线。',
        '§Y四、找出真正的瓶颈§!\n每级钢铁厂满产需煤 §R-0.20§!、铁 §R-0.20§!、电 §R+0.40§!，产钢 §G+0.20§!／日。每级机械厂需钢 §R-0.40§!、电 §R+0.20§!，交付机械 §G+0.20§!／日。\n先保证煤、电、钢足够，再扩机械厂。各区分别计算煤铁、电力和钢材，不跨区调拨；六区同时生产，交付合并计分。',
        '§Y五、扩产与重新布置§!\n每交付 §Y1§! 单位机械，投资回流 §G+1.00§!；积累后扩矿、扩产或升级线路。没有固定拨款。\n拆除退还实际投资，便于调整布局。停机可以节省原料和电力，线路仍然通行。采矿、发电、炼钢、机械按此顺序每日结算。',
        '§Y六、预估与期满§!\n产量速览显示下一日产量乘以 §Y30§!，不保证原料足够维持整月。库存耗尽后产量会改变；查看瓶颈与库存变化再调整。\n期满停止生产，保留交付量与完成度。重置须再次确认，将重抽六区矿点与岩壁。这是独立玩法测试，未接管旧一五计划，也不发放真实工厂。',
    ]
    help_en=[
        '§Y1. Plan, then start§!\nTake the test decision. Share §Y40§! investment; each region starts with §Y6§! coal, §Y4§! iron and §Y2§! steel. Arrange the factory, then Start production. Deliver §Y500§! machines in §Y1800§! game days. Closing this window does not pause production.',
        '§Y2. Six regional endowments§!\nThree cities, West Siberia, Central Siberia and the Far East use KR-inspired outlines. Each has different deposit quotas, randomised once per new plan. Switching and reloading preserve them. Poor cities retain starter deposits.\nMines need deposits; other plants use plain tiles. Levels are green, blue and gold; dark rocks cannot be developed. Hover for line grades and details.',
        '§Y3. Lay out transport§!\nPlace lines under facilities and along a route to the §Ylocal depot§!, using orthogonal neighbours.\nFacilities and lines reach level §Y3§!. A level-three plant on a level-one route produces at level one. Upgrade weak segments or build a better route.',
        '§Y4. Find the bottleneck§!\nA steelworks level uses §R0.20§! coal, §R0.20§! iron and §R0.40§! power to produce §G0.20§! steel daily. A machinery level uses §R0.40§! steel and §R0.20§! power to deliver §G0.20§! machines.\nBalance each region separately: stocks and power do not cross regions. All six factories run together; deliveries add to the shared score.',
        '§Y5. Expand and rearrange§!\nEach delivered machine returns §G1.00§! investment. Expand mines, plants and lines with the proceeds. There are no periodic grants.\nDemolition refunds actual investment. Stopping plants saves resources; lines remain open. Daily order: mines, power, steel, machinery.',
        '§Y6. Forecasts and expiry§!\nThe forecast multiplies next-day output by §Y30§!; it does not guarantee a month of supply. Depleting stocks changes output.\nAt expiry production stops and results remain. Confirm a reset twice to replay. This independent prototype has no native factory rewards and does not replace the old Five-Year Plan.',
    ]
    for i,(zh,en) in enumerate(zip(help_zh,help_en)):L(f'help_{i}',zh,en)

    definitions=[]
    def defined(name,branches):
        definitions.append(block('defined_text',f'name = {name}\n'+''.join(block('text',(block('trigger',cond) if cond else '')+f'localization_key = {key}\n') for cond,key in branches)))
    defined('GetRUSIPPlanStatus',[('has_country_flag = RUS_ip_finished',P+'ended'),('has_country_flag = RUS_ip_started',P+'active'),('',P+'not_started')])
    defined('GetRUSIPRegion',[(cv('region','=',r['id']),P+f'region_{r["id"]}') for r in REGIONS])
    defined('GetRUSIPRegionSummary',[(cv('region','=',r['id']),P+f'region_{r["id"]}_summary') for r in REGIONS])
    for r in REGIONS:
        rid=r['id'];defined(f'GetRUSIPRegionTab{rid}',[(cv('region','=',rid),P+f'region_{rid}_active'),('',P+f'region_{rid}')])
    defined('GetRUSIPType',[(cv('sel_type','=',k),P+f'type_{k}') for k in PROJECTS]+[('',P+'type_0')])
    defined('GetRUSIPTile',[(cv('selected','=',c['id']),L(f'tile_{c["id"]}',c['label'],c['label'])) for c in CELLS])
    terrains={0:'plain',1:'coal_site',2:'iron_site',3:'rock',4:'hub'}
    defined('GetRUSIPTerrain',[(cv('sel_terrain','=',k),P+'terrain_'+name) for k,name in terrains.items()])
    defined('GetRUSIPSelectedStatus',[(cv('sel_terrain','=',4),P+'status_hub'),(cv('sel_terrain','=',3),P+'status_rock'),(cv('sel_type','=',0),P+'status_empty'),(cv('sel_paused','=',1),P+'status_paused'),(cv('sel_route','=',0),P+'status_offline'),(cv('sel_route','<',P+'sel_level'),P+'status_limited'),('',P+'status_ready')])
    defined('GetRUSIPBottleneck',[(cv('bottleneck','=',i),P+f'bottleneck_{i}') for i in range(6)])
    for c in CELLS:
        i=c['id'];region=REGIONS[c['region']]
        defined(f'GetRUSIPType{i}',[(cv(f'n{i}_type','=',k),P+f'type_{k}') for k in PROJECTS]+[('',P+'type_0')])
        defined(f'GetRUSIPTerrain{i}',[(cv(f'n{i}_terrain','=',k),P+'terrain_'+name) for k,name in terrains.items()])
        L(f'node_{i}_tt',f'§Y{region["zh"]} · {c["label"]} · [GetRUSIPTerrain{i}]§!\n设施：[GetRUSIPType{i}]，§Y[?RUS_ip_n{i}_level|0]§! 级\n线路等级：§Y[?RUS_ip_n{i}_rail|0]§!\n接通能力：§Y[?RUS_ip_n{i}_route|0]§!\n有效生产等级：§G[?RUS_ip_n{i}_effective|0]§!\n点击选择，在右侧建设或升级。',f'§Y{region["en"]} · {c["label"]} · [GetRUSIPTerrain{i}]§!\n[GetRUSIPType{i}], level §Y[?RUS_ip_n{i}_level|0]§!\nLine: §Y[?RUS_ip_n{i}_rail|0]§!\nRoute: §Y[?RUS_ip_n{i}_route|0]§!\nEffective level: §G[?RUS_ip_n{i}_effective|0]§!\nSelect to build or upgrade on the right.')
        status=[(cv(f'n{i}_terrain','=',4),P+'status_hub'),(cv(f'n{i}_terrain','=',3),P+'status_rock'),(cv(f'n{i}_type','=',0),P+'status_empty'),(cv(f'n{i}_paused','=',1),P+'status_paused'),(cv(f'n{i}_route','=',0),P+'status_offline'),(cv(f'n{i}_route','<',P+f'n{i}_level'),P+'status_limited'),('',P+'status_ready')]
        defined(f'GetRUSIPNodeStatus{i}',status)
        for catalog in loc.values():
            catalog[P+f'node_{i}_tt']+=f'\n[GetRUSIPNodeStatus{i}]'

    launchers=[]; launcher_scripts=[]
    for suffix,y,condition in [('',-121,'NOT = { GER_is_in_mitteleuropa = yes }'),('_above_mitteleuropa',-198,'GER_is_in_mitteleuropa = yes')]:
        launchers.append(block('containerWindowType',f'name = "RUS_industrial_planning_launcher{suffix}"\nposition = {{ x = -79 y = {y} }}\nsize = {{ width = 77 height = 77 }}\nbackground = {{ name = "Background" quadTextureSprite = "GFX_equipment_role_selector_tiled_window" }}\nbackground = {{ name = "Background" quadTextureSprite = "GFX_tiled_research_bg" }}\nbuttonType = {{ name = "ip_open" position = {{ x = 9 y = 7 }} scale = 1.8 quadTextureSprite = "GFX_decision_generic_industry" pdx_tooltip = "RUS_ip_open_tt" clicksound = click_ok }}\n'))
        launcher_scripts.append(block('RUS_industrial_planning_launcher'+suffix,f'context_type = player_context\nparent_window_name = raid_filter\nwindow_name = "RUS_industrial_planning_launcher{suffix}"\nai_enabled = {{ always = no }}\n'+block('visible','RUS_ip_available = yes\n'+condition)+block('effects','ip_open_click = { hidden_effect = { RUS_ip_toggle = yes } }')))
    widgets=[]; gt={}; geffects=[]; gfx=[]; cards=set();board_region=''
    def visibility(name,condition='',page='board'):
        base='NOT = { has_country_flag = RUS_ip_help_open }\n' if page=='board' else 'has_country_flag = RUS_ip_help_open\n' if page=='help' else ''
        if page=='board':base+=board_region
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
        tip=P+('budget_tt' if key=='budget' else 'power_tt' if key=='power' else 'deliveries_tt' if key=='machines' else 'stock_tt')
        icon('ip_inventory_icon_'+key,'GFX_RUS_ip_'+sprite,x+12,114,scale,tip=tip)
        text('ip_inventory_'+key,P+key,x+54,109,138,45,tip=tip)
    for r in REGIONS:
        rid=r['id']
        button(f'ip_region_{rid}',P+f'region_{rid}_tab',32+112*rid,170,P+f'region_{rid}_tt',f'RUS_ip_select_region_{rid} = yes\n',scale=.88)
    bx,by,step=32,207,TILE_STEP
    def position(c):
        r=REGIONS[c['region']]
        return bx+(WIDTH-r['width'])*step//2+c['x']*step,by+(HEIGHT-r['height'])*step//2+c['y']*step
    # Every background has its own page visibility, including the selection.
    for c in CELLS:
        i=c['id'];x,y=position(c);board_region=cv('region','=',c['region'])
        button(f'ip_cell_{i}','',x,y,P+f'node_{i}_tt',setv('selected',i)+'clr_country_flag = RUS_ip_restart_armed\nRUS_ip_refresh = yes\n',sprite='GFX_RUS_ip_tile')
        for edge,dx,dy,sprite in [('top',0,0,'selection_h'),('bottom',0,38,'selection_h'),('left',0,0,'selection_v'),('right',38,0,'selection_v')]:
            icon(f'ip_selection_{i}_{edge}','GFX_RUS_ip_'+sprite,x+dx,y+dy,condition=cv('selected','=',i))
        if i in HUBS:icon(f'ip_hub_fill_{i}','GFX_RUS_ip_hub_fill',x+2,y+2)
        else:
            icon(f'ip_rock_fill_{i}','GFX_RUS_ip_rock_fill',x+2,y+2,condition=cv(f'n{i}_terrain','=',3))
            for level in LEVEL_COLOURS:
                icon(f'ip_grade_{i}_{level}',f'GFX_RUS_ip_grade_{level}',x+2,y+2,condition=cv(f'n{i}_terrain','<',3)+cv(f'n{i}_level','=',level))
    # Lines join the centres, above tile backgrounds and behind plant icons.
    for c in CELLS:
        i=c['id'];x,y=position(c);board_region=cv('region','=',c['region'])
        for j in c['neighbors']:
            if j<=i:continue
            vertical=CELLS[j]['y']!=c['y']
            icon(f'ip_link_{i}_{j}','GFX_RUS_ip_line_v' if vertical else 'GFX_RUS_ip_line_h',x+19,y+19,condition=cv(f'n{i}_rail','>',0)+cv(f'n{j}_rail','>',0))
    for c in CELLS:
        i=c['id'];x,y=position(c);board_region=cv('region','=',c['region'])
        if i in HUBS:
            icon(f'ip_hub_icon_{i}','GFX_RUS_ip_hub',x+6,y+6,28/34)
        else:
            for kind in (1,2):
                icon(f'ip_deposit_{i}_{kind}','GFX_RUS_ip_facility_'+str(kind),x+6,y+6,.875,condition=cv(f'n{i}_type','=',0)+cv(f'n{i}_terrain','=',kind))
            for kind in PROJECTS:
                icon(f'ip_plant_{i}_{kind}','GFX_RUS_ip_facility_'+str(kind),x+6,y+6,.875,condition=cv(f'n{i}_type','=',kind))
    board_region=''
    for level in (1,2,3):
        x=32+(level-1)*80
        icon(f'ip_grade_legend_{level}',f'GFX_RUS_ip_legend_{level}',x,719)
        text(f'ip_grade_label_{level}',P+f'grade_{level}',x+22,717,58,22)
    text('ip_legend',P+'legend',284,717,440,22)
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
    tile_sprite('tile',TILE_SIZE,TILE_SIZE,'gfx/interface/tiles/tiled_plain_bg.dds',8)
    tile_sprite('line_h',TILE_STEP,2,'gfx/interface/transp_white.dds',1)
    tile_sprite('line_v',2,TILE_STEP,'gfx/interface/transp_white.dds',1)
    # Fixed-size texture sprites, including dedicated 16px legend swatches.
    # Do not restore texture-free progressbartype: it failed in the game.
    for key in COLOUR_SPRITES:
        gfx.append(block('spriteType',f'name = "GFX_RUS_ip_{key}"\ntexturefile = "{ASSET_DIR}/{key}.png"\nnoOfFrames = 1\n'))
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
