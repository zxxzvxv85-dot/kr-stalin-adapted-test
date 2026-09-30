"""Local factory board, native icon reuse and its three localisation catalogs."""
from __future__ import annotations
from pathlib import Path
import os
from PIL import Image
from industrial_planning_catalog import PLANTS, STOCKS, PRODUCTS, PRICES, TARGET, TERRAINS, DEPOSITS, NAMES, RESOURCE_ICONS, PRODUCT_ICONS, FREIGHT_KIND, allowed, region_plants, specialty, extra_stocks
from industrial_planning_factory_freight_ui import localise as freight_localise, widgets as freight_widgets
from industrial_planning_factory_assets import ASSET_DIR, COLOUR_SPRITES, LEVEL_COLOURS

from industrial_planning_factory import (
    P, WIDTH, HEIGHT, HUBS, REGIONS, COST, PROJECTS, CELLS,
    block, setv, add, cv, iff, render_economy,
)

LANGS = ('simp_chinese', 'english', 'russian')
TILE_SIZE,TILE_STEP=40,42
WINDOW_WIDTH,WINDOW_HEIGHT=1600,1040
BOARD_X,BOARD_Y=32,250
SIDEBAR_X=1056


def render_outputs():
    triggers, effects, actions = render_economy()
    loc = {lang: {} for lang in LANGS}

    def L(key, zh, en, ru=None):
        for lang, value in zip(LANGS, (zh, en, ru or en)):
            loc[lang][P+key] = value
        return P+key

    L('title','国家计划委员会 · 工业规划沙盘','State Planning Commission · Factory Planning','Госплан · Планирование промышленности')
    L('open_tt','§Y工业规划沙盘§!\n布置厂区、连接运输线，发展六区特色产业。','§YFactory planning§!\nBuild factories, connect transport and develop six regional industries.')
    L('test_category','工业规划测试','Factory Planning Test')
    L('test_category_desc','勘探、运输与制造共同构成新的工业体系。','Prospecting, transport and manufacturing form a new industrial system.')
    L('enable_gui','启用工业规划沙盘（测试）','Enable Factory Planning (Test)')
    L('enable_gui_desc','先在沙盘上检验工业布局，再让生产基地沿着规划发展。','Test an industrial layout on the planning board.')
    L('enable_gui_tt','解锁独立入口并打开沙盘；点击“开始生产”后运行 §Y1800§! 天。','Unlock the launcher. Start production to run the §Y1800§!-day programme.')
    L('summary',f'[GetRUSIPPlanStatus]   |   工业产值目标 §Y{TARGET}§!   |   完成度 §G[?RUS_ip_score|0]%§!',f'[GetRUSIPPlanStatus]  |  Value target §Y{TARGET}§!  |  §G[?RUS_ip_score|0]%§! complete')
    L('not_started','§Y自由布置 · 尚未计时§!','§YLayout phase · clock stopped§!')
    L('active','剩余 §Y[?RUS_ip_days_left|0]§! 天','§Y[?RUS_ip_days_left|0]§! days remaining')
    L('ended','§Y本期生产已结束§!','§YProduction concluded§!')
    L('board_note','[GetRUSIPRegionSummary]','[GetRUSIPRegionSummary]')
    L('legend','底色表示设施等级；矿点、配方与状态见悬浮提示。','Colour indicates level; hover for deposits, recipes and status.')
    for level in (1,2,3):L(f'grade_{level}',f'{level} 级',f'Level {level}')
    L('budget','建设投资\n§Y[?RUS_ip_budget|1]§!','Investment\n§Y[?RUS_ip_budget|1]§!')
    for key in ('coal','iron','steel'):
        zh,en=NAMES[key];L(key,f'本区{zh}\n§Y[?RUS_ip_{key}|1]§!',f'{en}\n§Y[?RUS_ip_{key}|1]§!')
    L('value','六区累计产值\n§Y[?RUS_ip_value|1]§!','Total delivered value\n§Y[?RUS_ip_value|1]§!')
    L('power','本区电力／需求\n§Y[?RUS_ip_power_total|1] / [?RUS_ip_power_demand|1]§!','Local power / need\n§Y[?RUS_ip_power_total|1] / [?RUS_ip_power_demand|1]§!')
    L('budget_tt','§Y建设投资§!\n初始共享投资：§Y40§!\n每交付 §Y1§! 产值，投资回流：§G+1.00§!\n产品按固定单价计价；拆除退还实付投资。无固定拨款。','§YInvestment§!\nShared initial funds: §Y40§!\nEach §Y1§! delivered value returns §G+1.00§! investment.\nFixed product prices; demolition refunds paid costs. No periodic grants.')
    L('stock_tt','§Y本区库存§!\n[GetRUSIPStocks]\n\n运输站可调拨库存；电力留在本区。缺料按比例减产。','§YLocal stocks§!\n[GetRUSIPStocks]\n\nFreight stations move inventory; power stays local. Shortages scale production.')
    delivery=[];delivery_en=[]
    for key in PRODUCTS:
        zh,en=NAMES[key];price=PRICES[key]
        delivery.append(f'{zh}：§Y[?RUS_ip_{key}|1]§! × 单价 §Y{price:g}§!')
        delivery_en.append(f'{en}: §Y[?RUS_ip_{key}|1]§! × §Y{price:g}§!')
    L('deliveries_tt','§Y六区累计交付§!\n'+'\n'.join(delivery)+'\n\n总产值：§G+[?RUS_ip_value|1]§!\n次日产率折算／30天：§G+[?RUS_ip_total_value_month|1]§!\n按实际产值回流投资，未售出原料不计价。','§YCombined deliveries§!\n'+'\n'.join(delivery_en)+'\n\nTotal value: §G+[?RUS_ip_value|1]§!\nNext-day rate × 30: §G+[?RUS_ip_total_value_month|1]§!\nOnly delivered products earn investment; raw stocks do not.')
    L('power_tt','§Y电力§!\n每日电力当日使用，不储存。\n炼油→发电→炼钢→铝与合金→特色制造→通用机械。\n炼油厂自备辅助动力；燃油电站可缓解缺煤。满产需求按已接通、开机设施计算。','§YPower§!\nProduced and used daily.\nRefining → power → steel → aluminium/alloys → regional products → generic machinery.\nRefineries provide their own auxiliary power. Demand assumes full connected capacity.')
    L('selected','[GetRUSIPRegion] · [GetRUSIPTile] · [GetRUSIPTerrain]','[GetRUSIPRegion] · [GetRUSIPTile] · [GetRUSIPTerrain]')
    L('detail','设施：§Y[GetRUSIPType]§!  [?RUS_ip_sel_level|0] 级\n运输线：§Y[?RUS_ip_sel_rail|0]§! 级   接通能力：§Y[?RUS_ip_sel_route|0]§! 级\n有效等级：§G[?RUS_ip_sel_effective|0]§!\n[GetRUSIPSelectedStatus]','Facility: §Y[GetRUSIPType]§!  Lv [?RUS_ip_sel_level|0]\nLine: §Y[?RUS_ip_sel_rail|0]§!  Route: §Y[?RUS_ip_sel_route|0]§!\nEffective level: §G[?RUS_ip_sel_effective|0]§!\n[GetRUSIPSelectedStatus]')
    terrains={0:'plain',1:'coal_site',2:'iron_site',3:'rock',4:'hub',5:'bauxite_site',6:'chromium_site',7:'tungsten_site',8:'oil_site'}
    for key,zh,en in [('plain','工业用地','Industrial land'),('rock','岩壁 · 不可建设','Rock · no construction'),('hub','调度站','Depot')]:L('terrain_'+key,zh,en)
    for key in TERRAINS.values():L('terrain_'+key+'_site',NAMES[key][0]+'矿点',NAMES[key][1]+' deposit')
    L('type_0','空地','Empty')
    for kind,p in PLANTS.items():L(f'type_{kind}',p['zh'],p['en'])
    for key,zh,en in [
        ('hub','§G厂内运输网络的固定起点§!','§GFixed origin of the network§!'),
        ('empty','选择设施或铺设运输线。','Select a facility or place a line.'),
        ('rock','§R此处无法建设。§!','§RNo construction here.§!'),
        ('paused','§Y设施已停机；线路仍可通行。§!','§YStopped; the line remains passable.§!'),
        ('offline','§R未接通调度站，无法生产。§!','§RDisconnected from depot; no output.§!'),
        ('limited','§Y沿途线路限制产能，升级最薄弱路段。§!','§YUpgrade the weakest route segments.§!'),
        ('transport','§G运输站已接通；在“跨区运输”中配置路线。§!','§GStation connected; configure it under Freight.§!'),
        ('ready','§G已接通；产量取决于原料与电力。§!','§GConnected; output depends on materials and power.§!'),
    ]:L('status_'+key,zh,en)
    L('forecast','次日产率折算／30天\n机械：§G+[?RUS_ip_machine_month|1]§!   [GetRUSIPProduct]：§G+[?RUS_ip_specialty_month|1]§!\n产值／投资回流：§G+[?RUS_ip_investment_month|1] / +[?RUS_ip_investment_month|1]§!','Next-day rates × 30\nMachinery: §G+[?RUS_ip_machine_month|1]§!  Regional: §G+[?RUS_ip_specialty_month|1]§!\nValue / return: §G+[?RUS_ip_investment_month|1] / +[?RUS_ip_investment_month|1]§!')
    L('forecast_tt','§Y产量速览§!\n下一日产量乘以30，并非保证整月交付；库存耗尽会改变产量。\n特色制造优先领取原料，随后供通用机械。停机可改变原料分配。','§YForecast§!\nNext-day rates × 30, not guaranteed monthly output. Depletion changes production.\nRegional manufacturers receive inputs before generic machinery. Stop plants to change allocation.')
    L('results',f'§Y本期结果§!\n累计产值：§G[?RUS_ip_value|1]§!／{TARGET}\n投资回流：§G+[?RUS_ip_earned|1]§!\n生产已停止，可重置再试。',f'§YFinal results§!\nValue: §G[?RUS_ip_value|1]§! / {TARGET}\nInvestment earned: §G+[?RUS_ip_earned|1]§!\nProduction stopped; reset to try again.')
    L('bottleneck','当前瓶颈：[GetRUSIPBottleneck]','Bottleneck: [GetRUSIPBottleneck]')
    bottlenecks={0:('§G当前产线正常§!','§GCurrent line is supplied§!'),1:('§R煤炭不足§!','§RCoal shortage§!'),2:('§R铁矿不足§!','§RIron shortage§!'),3:('§R电力不足§!','§RPower shortage§!'),4:('§R钢材不足§!','§RSteel shortage§!'),5:('§Y尚无接通的成品制造厂§!','§YNo connected final-product works§!')}
    for index,key in enumerate(STOCKS):
        if key not in ('coal','iron','steel'):bottlenecks[6+index]=(f'§R{NAMES[key][0]}不足§!',f'§R{NAMES[key][1]} shortage§!')
    for code,(zh,en) in bottlenecks.items():L(f'bottleneck_{code}',zh,en)
    L('network','接通 §G[?RUS_ip_connected_count|0]§! 格   |   断线 §R[?RUS_ip_offline_count|0]§! 座   |   运输站可跨区运货','Connected §G[?RUS_ip_connected_count|0]§!  |  Offline §R[?RUS_ip_offline_count|0]§!  |  Freight stations link regions')
    L('base_page','基础生产','Basic production');L('special_page','特色产业','Regional industry')
    L('base_page_active','§Y基础生产§!','§YBasic production§!');L('special_page_active','§Y特色产业§!','§YRegional industry§!')
    L('base_page_tab','[GetRUSIPBaseMenu]','[GetRUSIPBaseMenu]');L('special_page_tab','[GetRUSIPSpecialMenu]','[GetRUSIPSpecialMenu]')
    L('page_tt','切换建设目录，不影响已建设施的连续生产。','Change the build menu without stopping production.')
    for r in REGIONS:
        rid=r['id'];sp=specialty(rid);product=sp['output'];price=PRICES[product]
        deposits={'coal':r['coal'],'iron':r['iron'],**DEPOSITS[rid]}
        for key,zh,en in [(f'region_{rid}',r['zh'],r['en']),(f'region_{rid}_active','§Y'+r['zh']+'§!','§Y'+r['en']+'§!'),(f'region_{rid}_tab',f'[GetRUSIPRegionTab{rid}]',f'[GetRUSIPRegionTab{rid}]'),(f'product_{rid}',*NAMES[product])]:L(key,zh,en)
        L(f'region_{rid}_summary',f'§Y{r["zh"]}§! · 特色：{NAMES[product][0]} · 单价 §Y{price:g}§! · 地块 §Y{len(r["cells"])}§!',f'§Y{r["en"]}§! · {NAMES[product][1]} · Price §Y{price:g}§! · §Y{len(r["cells"])}§! tiles')
        zh='；'.join(f'{NAMES[k][0]} §Y{n}§!' for k,n in deposits.items());en='; '.join(f'{NAMES[k][1]} §Y{n}§!' for k,n in deposits.items())
        L(f'region_{rid}_tt',f'§Y{r["zh"]}§!\n矿点：{zh}\n岩壁：§Y{r["rocks"]}§!\n特色产品：{NAMES[product][0]}；单价：§Y{price:g}§!\n位置每次新计划随机；切图和读档不重抽。\n基本煤铁包含沙盘起步保障，其余矿种参考KR州组。\n切换地区时其他厂区继续生产。',f'§Y{r["en"]}§!\nDeposits: {en}\nRocks: §Y{r["rocks"]}§!\nSpecialty: {NAMES[product][1]}, price §Y{price:g}§!\nNew plans randomise positions; switching/reloading preserves them.\nBasic ore includes starter reserves; special ores follow KR catchments.')
        keys=('coal','iron','steel',*extra_stocks(rid))
        L(f'stocks_{rid}','\n'.join(f'{NAMES[k][0]}：§Y[?RUS_ip_{k}|1]§!' for k in keys),'\n'.join(f'{NAMES[k][1]}: §Y[?RUS_ip_{k}|1]§!' for k in keys))
    for key in STOCKS:
        L(f'stock_{key}',f'§Y[?RUS_ip_{key}|1]§!',f'§Y[?RUS_ip_{key}|1]§!')
        L(f'stock_{key}_tt',f'§Y{NAMES[key][0]}§!\n本区库存：§Y[?RUS_ip_{key}|1]§!\n供本区已接通、开机的设施使用；也可经运输站发往其他地区。不计入交付产值。',f'§Y{NAMES[key][1]}§!\nLocal stock: §Y[?RUS_ip_{key}|1]§!\nSupplies connected local plants and can be exported through freight stations. Not counted as delivered value.')
    for kind,p in PLANTS.items():
        zh,en=p['zh'],p['en'];rate=p['rate'];out=p['output']
        L(f'build_{kind}',zh,en);L(f'cost_{kind}',f'投资 §R-{p["cost"]}§! · 每级',f'§R-{p["cost"]}§! / level')
        if kind==FREIGHT_KIND:
            L(f'build_{kind}_tt','§Y跨区运输站§!\n\n设施等级：§G+1§!\n建设投资：§R-10§!\n单批运输上限／每级：§G+6§!\n\n每区最多一座，最高§Y3§!级；建在普通工业用地并接通调度站。两端较低有效等级限制批量。\n在“跨区运输”中选择目的区、货物和保留量，按日自动发运。每单位运费：§R-0.10§! 投资。无每日固定维护费。',
              '§YFreight station§!\n\nLevel: §G+1§!\nInvestment: §R-10§!\nBatch limit per level: §G+6§!\n\nOne per region, maximum level §Y3§!. Build on plain land and connect to depot; the lower endpoint level limits batches.\nConfigure destination, cargo and reserve under Freight. Automatic daily dispatch; fee §R-0.10§! per unit, no daily standing cost.')
            continue
        z=[];e=[]
        for key,ratio in p['inputs'].items():
            z.append(f'每日{NAMES[key][0]}消耗：§R-{ratio*rate:.2f}§!');e.append(f'Daily {NAMES[key][1]} use: §R-{ratio*rate:.2f}§!')
        if p['power']:z.append(f'每日电力需求：§R+{p["power"]*rate:.2f}§!');e.append(f'Daily power demand: §R+{p["power"]*rate:.2f}§!')
        outzh,outen=('电力','Power') if out=='power' else NAMES[out]
        z.append(f'每日{outzh}{"交付" if out in PRODUCTS else "产出"}：§G+{rate:.2f}§!');e.append(f'Daily {outen} output: §G+{rate:.2f}§!')
        if out in PRODUCTS:
            z.extend([f'产品单价：§Y{PRICES[out]:g}§!',f'每日产值／投资回流：§G+{rate*PRICES[out]:.2f}§!'])
            e.extend([f'Unit price: §Y{PRICES[out]:g}§!',f'Daily value / investment: §G+{rate*PRICES[out]:.2f}§!'])
        if kind==13:z.append('自备辅助动力，不占用本区电网。');e.append('Own auxiliary power; no grid demand.')
        site='对应矿点' if p['terrain'] else '普通工业用地';site_en='matching deposit' if p['terrain'] else 'plain industrial tile'
        special=f'\n仅限{REGIONS[p["region"]]["zh"]}。' if p['region'] is not None else ''
        special_en=f'\nOnly in {REGIONS[p["region"]]["en"]}.' if p['region'] is not None else ''
        L(f'build_{kind}_tt',f'§Y{zh}§!\n\n设施等级：§G+1§!\n建设投资：§R-{p["cost"]}§!\n\n§Y每级满产效果：§!\n'+'\n'.join(z)+f'\n\n须位于{site}，最高§Y3§!级。{special}\n接通调度站后运行，受沿途最低线路等级限制；缺料缺电按比例减产。',f'§Y{en}§!\n\nLevel: §G+1§!\nInvestment: §R-{p["cost"]}§!\n\n§YFull production per level:§!\n'+'\n'.join(e)+f'\n\nRequires {site_en}; maximum level §Y3§!.{special_en}\nConnect to depot; route grades, materials and power limit output.')
    for key,zh,en in [('rail','厂内运输线','Transport line'),('quick_rail','铺设线路','Lay line'),('switch','停机／开机','Stop / run'),('remove','拆除设施','Remove plant'),('remove_rail','拆除线路','Remove line'),('refresh','刷新产量','Refresh'),('start','开始生产','Start'),('restart','重新规划','Reset'),('confirm_restart','确认重置','Confirm reset'),('help','玩法介绍','How to play'),('back','返回厂区','Back')]:L(key,zh,en)
    L('cost_rail','投资 §R-1§! · 每级','§R-1§! / level')
    L('rail_tt','§Y厂内运输线§!\n线路等级：§G+1§!\n建设投资：§R-1§!\n逐格接到本区调度站，只连接上下左右。最多3级，与设施共用格子；最佳路线的最低等级限制产能。','§YTransport line§!\nLevel: §G+1§!\nInvestment: §R-1§!\nConnect orthogonally to the local depot. Maximum level 3; shares plant tiles. Weakest segment limits output.')
    L('remove_tt','返还设施全部实付投资；保留线路、库存和交付量。','Refund plant investment; keep lines, stocks and deliveries.')
    L('remove_rail_tt','返还线路全部实付投资；保留设施，依赖此线的设施可能断线。','Refund line investment; downstream plants may disconnect.')
    L('switch_tt','停机后不生产、不耗料、不耗电，线路仍能通行。','Stop production and input use; the line remains passable.')
    L('refresh_tt','重算线路、产能和次日产量，不推进日期、不发放收益。','Recalculate routes and forecast without production or income.')
    L('start_tt',f'开始1800天连续生产；目标工业产值§Y{TARGET}§!。关闭窗口仍运行，期满停止。',f'Start 1800 days of production; value target §Y{TARGET}§!. Runs while closed; stops at expiry.')
    L('restart_tt','再次确认后清空六区设施、线路、全部原料、成品交付、产值与计时，恢复40投资并重抽矿点；不影响旧一五计划。','Confirm twice to clear all boards, stocks, product deliveries, value and time; restore 40 investment and reroll deposits. The old plan is unaffected.')
    L('footnote','独立测试沙盘 · 产品按固定单价计入产值 · 随游戏日期生产','Independent sandbox · fixed product values · production follows game time')
    L('help_title','工业规划沙盘 · 玩法介绍','Factory Planning · How to Play')
    help_zh=[
        '§Y一、先布置，再开工§!\n六区共享初始投资§Y40§!，每区煤§Y6§!、铁§Y4§!、钢§Y2§!。先布置，再点击“开始生产”。目标是在§Y1800§!天内交付§Y500§!工业产值，关闭窗口仍生产。\n基础煤铁、电站、钢铁厂和机械厂可独立开局；特色产业可在积累投资后发展。',
        '§Y二、六区的不同选择§!\n莫斯科生产机床；彼得格勒生产航空部件；察里津生产拖拉机；西西伯利亚生产铁路装备；中西伯利亚生产发电设备；远东生产精密工具。\n铝、铬、钨和石油按KR州组分布；基础煤铁保留起步保障。矿点位置随机，切图和读档不重抽。',
        '§Y三、运输与建设§!\n设施格及途经格铺线，按上下左右接到本区调度站。设施和线路最高§Y3§!级，最薄弱路段限制产能。一级绿、二级蓝、三级金。\n“基础生产”可建运输站，每区一座；两端接通后在“跨区运输”选择目的地与货物，设置保留量并开启自动发运。每级单批6单位，每单位运费0.1。',
        '§Y四、按顺序组织加工§!\n采矿→炼油→发电→炼钢→铝与合金→特色制造→通用机械。炼油自备辅助动力，燃油电站可节省煤。\n特色制造先领取原料，可用停机按钮调整分配。物资可用运输站跨区调拨，电力仅在本区使用。缺料缺电按比例减产，电力不储存。',
        '§Y五、产品价值与回流§!\n单价：机械§Y1§!，拖拉机§Y1.5§!，机床§Y2§!，铁路装备§Y2.5§!，航空部件与发电设备§Y3§!，精密工具§Y4§!。\n实际交付×单价计入产值，同额回流投资。原料和中间品库存不计价。高级工厂更贵、配套更多；没有固定拨款。',
        '§Y六、预估、退款与期满§!\n产量速览是下一日产率×30，不保证库存能支撑整月。建设按钮显示每级配方和产值，顶部累计产值悬浮列出所有产品交付量。\n拆除退实付投资；期满保留结果，未到货物与该批运费退回，重置须再次确认。本沙盘独立，不发放真实工厂，不接管旧一五计划。',
    ]
    help_en=[
        '§Y1. Plan, then start§!\nShare §Y40§! investment; each region starts with §Y6§! coal, §Y4§! iron and §Y2§! steel. Target §Y500§! delivered value in §Y1800§! days. Production continues while closed.\nBasic coal, iron, power, steel and machinery provide an independent start.',
        '§Y2. Regional choices§!\nMoscow: machine tools. Petrograd: aircraft parts. Tsaritsyn: tractors. West Siberia: rail equipment. Central Siberia: generating equipment. Far East: precision tools.\nSpecial ores follow KR catchments; basic ores include starter reserves. Positions reroll only on a new plan.',
        '§Y3. Lines and construction§!\nConnect facility tiles orthogonally to the local depot. Plants and lines reach level §Y3§!; the weakest route limits production. Grades are green, blue and gold.\nBuild one freight station per region under Basic production. Connect both ends; select destination, cargo, reserve and enable dispatch under Freight. Batch size is 6 per effective level; fee is 0.1 per unit.',
        '§Y4. Processing order§!\nMines → refining → power → steel → aluminium/alloys → regional products → generic machinery. Refineries have their own auxiliary power. Fuel power saves coal.\nRegional products have input priority; stop plants to redirect inputs. Freight stations transfer stocks; power stays local. Shortages scale output.',
        '§Y5. Prices and investment§!\nPrices: machinery §Y1§!, tractors §Y1.5§!, machine tools §Y2§!, rail equipment §Y2.5§!, aircraft parts and generators §Y3§!, precision tools §Y4§!.\nDelivered quantity × price gives value and equal investment. Intermediate stocks do not earn income. Advanced chains cost more to build.',
        '§Y6. Forecasts and expiry§!\nForecasts show next-day rates × 30, not guaranteed monthly output. Hover build buttons for recipes and total value for product deliveries.\nDemolition refunds paid costs. Expiry preserves results and returns unfinished cargo and its fees; confirm reset twice. This sandbox grants no real factories and does not replace the old plan.',
    ]
    for i,(zh,en) in enumerate(zip(help_zh,help_en)):L(f'help_{i}',zh,en)

    definitions=[]
    def defined(name,branches):
        definitions.append(block('defined_text',f'name = {name}\n'+''.join(block('text',(block('trigger',cond) if cond else '')+f'localization_key = {key}\n') for cond,key in branches)))
    freight_localise(L,defined)
    defined('GetRUSIPBaseMenu',[(cv('build_page','=',0),P+'base_page_active'),('',P+'base_page')])
    defined('GetRUSIPSpecialMenu',[(cv('build_page','=',1),P+'special_page_active'),('',P+'special_page')])
    defined('GetRUSIPPlanStatus',[('has_country_flag = RUS_ip_finished',P+'ended'),('has_country_flag = RUS_ip_started',P+'active'),('',P+'not_started')])
    defined('GetRUSIPRegion',[(cv('region','=',r['id']),P+f'region_{r["id"]}') for r in REGIONS])
    defined('GetRUSIPRegionSummary',[(cv('region','=',r['id']),P+f'region_{r["id"]}_summary') for r in REGIONS])
    defined('GetRUSIPProduct',[(cv('region','=',r['id']),P+f'product_{r["id"]}') for r in REGIONS])
    defined('GetRUSIPStocks',[(cv('region','=',r['id']),P+f'stocks_{r["id"]}') for r in REGIONS])
    for r in REGIONS:
        rid=r['id'];defined(f'GetRUSIPRegionTab{rid}',[(cv('region','=',rid),P+f'region_{rid}_active'),('',P+f'region_{rid}')])
    defined('GetRUSIPType',[(cv('sel_type','=',k),P+f'type_{k}') for k in PROJECTS]+[('',P+'type_0')])
    defined('GetRUSIPTile',[(cv('selected','=',c['id']),L(f'tile_{c["id"]}',c['label'],c['label'])) for c in CELLS])
    defined('GetRUSIPTerrain',[(cv('sel_terrain','=',k),P+'terrain_'+name) for k,name in terrains.items()])
    defined('GetRUSIPSelectedStatus',[(cv('sel_terrain','=',4),P+'status_hub'),(cv('sel_terrain','=',3),P+'status_rock'),(cv('sel_type','=',0),P+'status_empty'),(cv('sel_paused','=',1),P+'status_paused'),(cv('sel_route','=',0),P+'status_offline'),(cv('sel_route','<',P+'sel_level'),P+'status_limited'),(cv('sel_type','=',FREIGHT_KIND),P+'status_transport'),('',P+'status_ready')])
    defined('GetRUSIPBottleneck',[(cv('bottleneck','=',i),P+f'bottleneck_{i}') for i in bottlenecks])
    for c in CELLS:
        i=c['id'];region=REGIONS[c['region']]
        defined(f'GetRUSIPType{i}',[(cv(f'n{i}_type','=',k),P+f'type_{k}') for k in region_plants(region['id'])]+[('',P+'type_0')])
        defined(f'GetRUSIPTerrain{i}',[(cv(f'n{i}_terrain','=',k),P+'terrain_'+name) for k,name in terrains.items()])
        L(f'node_{i}_tt',f'§Y{region["zh"]} · {c["label"]} · [GetRUSIPTerrain{i}]§!\n设施：[GetRUSIPType{i}]，§Y[?RUS_ip_n{i}_level|0]§! 级\n线路等级：§Y[?RUS_ip_n{i}_rail|0]§!\n接通能力：§Y[?RUS_ip_n{i}_route|0]§!\n有效等级：§G[?RUS_ip_n{i}_effective|0]§!\n点击选择，在右侧建设或升级。',f'§Y{region["en"]} · {c["label"]} · [GetRUSIPTerrain{i}]§!\n[GetRUSIPType{i}], level §Y[?RUS_ip_n{i}_level|0]§!\nLine: §Y[?RUS_ip_n{i}_rail|0]§!\nRoute: §Y[?RUS_ip_n{i}_route|0]§!\nEffective level: §G[?RUS_ip_n{i}_effective|0]§!\nSelect to build or upgrade on the right.')
        status=[(cv(f'n{i}_terrain','=',4),P+'status_hub'),(cv(f'n{i}_terrain','=',3),P+'status_rock'),(cv(f'n{i}_type','=',0),P+'status_empty'),(cv(f'n{i}_paused','=',1),P+'status_paused'),(cv(f'n{i}_route','=',0),P+'status_offline'),(cv(f'n{i}_route','<',P+f'n{i}_level'),P+'status_limited'),(cv(f'n{i}_type','=',FREIGHT_KIND),P+'status_transport'),('',P+'status_ready')]
        defined(f'GetRUSIPNodeStatus{i}',status)
        for catalog in loc.values():
            catalog[P+f'node_{i}_tt']+=f'\n[GetRUSIPNodeStatus{i}]'

    launchers=[]; launcher_scripts=[]
    for suffix,y,condition in [('',-121,'NOT = { GER_is_in_mitteleuropa = yes }'),('_above_mitteleuropa',-198,'GER_is_in_mitteleuropa = yes')]:
        launchers.append(block('containerWindowType',f'name = "RUS_industrial_planning_launcher{suffix}"\nposition = {{ x = -79 y = {y} }}\nsize = {{ width = 77 height = 77 }}\nbackground = {{ name = "Background" quadTextureSprite = "GFX_equipment_role_selector_tiled_window" }}\nbackground = {{ name = "Background" quadTextureSprite = "GFX_tiled_research_bg" }}\nbuttonType = {{ name = "ip_open" position = {{ x = 9 y = 7 }} scale = 1.8 quadTextureSprite = "GFX_decision_generic_industry" pdx_tooltip = "RUS_ip_open_tt" clicksound = click_ok }}\n'))
        launcher_scripts.append(block('RUS_industrial_planning_launcher'+suffix,f'context_type = player_context\nparent_window_name = raid_filter\nwindow_name = "RUS_industrial_planning_launcher{suffix}"\nai_enabled = {{ always = no }}\n'+block('visible','RUS_ip_available = yes\n'+condition)+block('effects','ip_open_click = { hidden_effect = { RUS_ip_toggle = yes } }')))
    # Normalize native textures to a 32px box without editing raster assets.
    root=Path(__file__).resolve().parents[1]
    roots=(root,Path(os.environ.get('HOI4_KR_ROOT',root.parent/'1521695605')),
           Path(os.environ.get('HOI4_GAME_ROOT',root.parents[3]/'common/Hearts of Iron IV')))
    icon_scales={}
    for name,path in {**{f'facility_{k}':p['icon'] for k,p in PLANTS.items()},**{f'resource_{k}':v for k,v in RESOURCE_ICONS.items()}}.items():
        source=next(root/path for root in roots if (root/path).is_file())
        with Image.open(source) as img:icon_scales['GFX_RUS_ip_'+name]=32/max(img.size)
    widgets=[]; gt={}; geffects=[]; gfx=[]; cards=set();board_region=''
    def visibility(name,condition='',page='board'):
        base='NOT = { has_country_flag = RUS_ip_help_open }\n' if page=='board' else 'has_country_flag = RUS_ip_help_open\n' if page=='help' else ''
        if page=='board':base+=board_region
        if base+condition:gt[name+'_visible']=base+condition
    def text(name,key,x,y,w,h=24,font='hoi_16mbs',center=False,condition='',page='board',tip=''):
        tooltip=f'pdx_tooltip = "{tip}" ' if tip else ''
        widgets.append(f'instantTextBoxType = {{ name = "{name}" position = {{ x = {x} y = {y} }} text = "{key}" font = "{font}" maxWidth = {w} maxHeight = {h} format = {"center" if center else "left"} fixedsize = yes {tooltip}alwaystransparent = {"no" if tip else "yes"} }}\n');visibility(name,condition,page)
    def icon(name,sprite,x,y,scale=1,condition='',page='board',tip=''):
        scale=round(scale*icon_scales.get(sprite,1),6)
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
    text('ip_title',P+'title',32,18,1536,32,'hoi_24header',True,page='all')
    text('ip_summary',P+'summary',36,57,1520,25,'hoi_20b',page='all')
    for index,(key,sprite,scale) in enumerate([('budget','funds',1.6),('coal','facility_1',1),('iron','facility_2',1),('steel','facility_4',1),('value','facility_5',1),('power','facility_3',1)]):
        x=32+260*index
        card('ip_inventory_bg_'+key,x,97,236,66)
        tip=P+('budget_tt' if key=='budget' else 'power_tt' if key=='power' else 'deliveries_tt' if key=='value' else 'stock_tt')
        icon('ip_inventory_icon_'+key,'GFX_RUS_ip_'+sprite,x+12,114,scale,tip=tip)
        text('ip_inventory_'+key,P+key,x+54,109,178,45,tip=tip)
    for r in REGIONS:
        rid=r['id']
        button(f'ip_region_{rid}',P+f'region_{rid}_tab',32+160*rid,170,P+f'region_{rid}_tt',f'RUS_ip_select_region_{rid} = yes\n',scale=1.13)
    bx,by,step=BOARD_X,BOARD_Y,TILE_STEP
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
                icon(f'ip_grade_{i}_{level}',f'GFX_RUS_ip_grade_{level}',x+2,y+2,condition=block('NOT',cv(f'n{i}_terrain','=',3))+cv(f'n{i}_level','=',level))
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
            for kind in region_plants(c['region']):
                if not PLANTS[kind]['terrain']:continue
                icon(f'ip_deposit_{i}_{kind}','GFX_RUS_ip_facility_'+str(kind),x+6,y+6,.875,condition=cv(f'n{i}_type','=',0)+cv(f'n{i}_terrain','=',PLANTS[kind]['terrain']))
            for kind in region_plants(c['region']):
                icon(f'ip_plant_{i}_{kind}','GFX_RUS_ip_facility_'+str(kind),x+6,y+6,.875,condition=cv(f'n{i}_type','=',kind))
    for r in REGIONS:
        board_region=cv('region','=',r['id'])
        for index,key in enumerate(extra_stocks(r['id'])):
            x=32+index*128
            icon(f'ip_extra_icon_{r["id"]}_{key}','GFX_RUS_ip_resource_'+key,x,217,.75,tip=P+f'stock_{key}_tt')
            text(f'ip_extra_stock_{r["id"]}_{key}',P+f'stock_{key}',x+30,219,60,22,tip=P+f'stock_{key}_tt')
    board_region=''
    for level in (1,2,3):
        x=32+(level-1)*80
        icon(f'ip_grade_legend_{level}',f'GFX_RUS_ip_legend_{level}',x,969,tip=P+'legend')
        text(f'ip_grade_label_{level}',P+f'grade_{level}',x+22,967,58,22)
    text('ip_selected',P+'selected',SIDEBAR_X,175,510,26,'hoi_20b')
    card('ip_detail_bg',SIDEBAR_X,207,510,128)
    text('ip_detail',P+'detail',SIDEBAR_X+16,221,480,106)
    button('ip_base_page',P+'base_page_tab',SIDEBAR_X,348,P+'page_tt','RUS_ip_build_page_0 = yes\n',condition='')
    button('ip_special_page',P+'special_page_tab',SIDEBAR_X+143,348,P+'page_tt','RUS_ip_build_page_1 = yes\n',condition='')
    button('ip_freight_page',P+'freight_page_tab',SIDEBAR_X+286,348,P+'freight_rules_tt','RUS_ip_build_page_2 = yes\n',condition='')
    def build_button(name,kind,index,condition):
        x,y=SIDEBAR_X+(index%2)*246,390+(index//2)*70
        key=f'build_{kind}' if isinstance(kind,int) else 'rail'
        icon_key=f'facility_{kind}' if isinstance(kind,int) else 'line'
        button(name,'',x,y,P+key+'_tt',f'RUS_ip_{key} = yes\n',f'RUS_ip_can_{key} = yes',sprite='GFX_RUS_ip_action',scale=.92,condition=condition)
        icon(name+'_icon','GFX_RUS_ip_'+icon_key,x+13,y+10,.875,condition=condition)
        text(name+'_title',P+key,x+45,y+5,155,21,center=True,condition=condition)
        text(name+'_cost',P+f'cost_{kind}',x+40,y+29,165,20,center=True,condition=condition)
    for index,kind in enumerate([1,2,3,4,5,'rail',FREIGHT_KIND]):build_button('ip_'+(f'build_{kind}' if isinstance(kind,int) else kind),kind,index,cv('build_page','=',0))
    for r in REGIONS:
        for index,kind in enumerate(k for k in region_plants(r['id']) if 5<k<FREIGHT_KIND):
            build_button(f'ip_r{r["id"]}_build_{kind}',kind,index,cv('build_page','=',1)+cv('region','=',r['id']))
    for index,key in enumerate(['quick_rail','switch','remove','remove_rail','refresh']):
        action='rail' if key=='quick_rail' else key
        button('ip_'+key,P+key,SIDEBAR_X+index*103,743,P+action+'_tt',f'RUS_ip_{action} = yes\n',f'RUS_ip_can_{action} = yes' if action!='refresh' else '',scale=.80,condition=cv('build_page','<',2))
    text('ip_forecast',P+'forecast',SIDEBAR_X+8,800,496,64,tip=P+'forecast_tt',condition=cv('build_page','<',2)+'NOT = { has_country_flag = RUS_ip_finished }')
    text('ip_results',P+'results',SIDEBAR_X+8,800,496,90,condition=cv('build_page','<',2)+'has_country_flag = RUS_ip_finished')
    text('ip_bottleneck',P+'bottleneck',SIDEBAR_X+8,870,500,23,condition=cv('build_page','<',2)+'NOT = { has_country_flag = RUS_ip_finished }')
    text('ip_network',P+'network',284,967,714,23,tip=P+'board_note')
    freight_widgets(text,icon,button,SIDEBAR_X)
    button('ip_start',P+'start',32,995,P+'start_tt','RUS_ip_start = yes\n','RUS_ip_editing = yes',condition='NOT = { has_country_flag = RUS_ip_started }')
    button('ip_restart',P+'restart',175,995,P+'restart_tt','RUS_ip_arm_restart = yes\n',condition='NOT = { has_country_flag = RUS_ip_restart_armed }')
    button('ip_confirm_restart',P+'confirm_restart',175,995,P+'restart_tt','RUS_ip_confirm_restart = yes\n',condition='has_country_flag = RUS_ip_restart_armed')
    text('ip_footnote',P+'footnote',320,1003,1050,21,'hoi_16mbs')
    button('ip_help',P+'help',1443,995,'','RUS_ip_toggle_help = yes\n')
    button('ip_back',P+'back',735,995,'','RUS_ip_toggle_help = yes\n',page='help')
    text('ip_help_title',P+'help_title',80,114,1440,36,'hoi_24header',True,page='help')
    for i in range(6):text(f'ip_help_{i}',P+f'help_{i}',58+(754 if i>=3 else 0),181+(i%3)*240,710,216,page='help')
    button('ip_close','',1558,9,'CLOSE','RUS_ip_close_effect = yes\n',sprite='GFX_closebutton',page='all')
    frame=f'name = "RUS_industrial_planning_window"\nposition = {{ x = {-WINDOW_WIDTH//2} y = {-WINDOW_HEIGHT//2} }}\nsize = {{ width = {WINDOW_WIDTH} height = {WINDOW_HEIGHT} }}\norientation = center\nmoveable = yes\nclick_to_front = yes\nshow_sound = menu_open_window\nhide_sound = menu_close_window\nbackground = {{ name = "frame" quadTextureSprite = "GFX_tiled_plain_bg" }}\n'
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
    sprites={f'facility_{k}':(p['icon'],1) for k,p in PLANTS.items()}
    sprites.update({f'resource_{k}':(path,1) for k,path in RESOURCE_ICONS.items()})
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
