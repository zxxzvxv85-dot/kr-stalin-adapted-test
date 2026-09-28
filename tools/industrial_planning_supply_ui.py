"""Labels and widgets for the programme's funds, stock and automatic transport."""
import re
from industrial_planning_economy import P, cv
from industrial_planning_supply import routes

# Existing KR/native assets, inspected at their source size. No generated image
# or replacement of shared sprites is needed. Each large icon fits a 32px box.
SUPPLY_ICONS = {
    'funds': ('gfx/texticons/bag_of_money.png', 1.6),
    'warehouse': ('gfx/interface/abilitylist/ability_extra_supplies.dds', 32/34),
    'transit': ('gfx/interface/decisions/decision_generic_train.dds', 32/33),
    'balance': ('gfx/interface/decisions/decision_hol_attract_foreign_investors.dds', 32/33),
}


def format_amounts(text):
    """Format programme quantities only; dates and underlying values stay intact.

    KR's RUS_change_projection_tt uses |=+1 for signed, coloured changes.
    Native building rewards remain in effect_tooltip, outside these custom rows.
    """
    deltas = {'next_settlement','projected_operating','projected_settlement',
              'budget_net','last_budget','funds_refunded',
              'sel_income_month','sel_mining_month','sel_refund','sel_net_month'}
    expenses = {'funds_spent','sel_paid','sel_upkeep_month'}
    demand = {'sel_need_steel','sel_need_coal','sel_base_steel','sel_base_coal','sel_project_steel','sel_project_coal'}
    balances = {'funds','next_balance'}
    stocks = {'debt','sel_members','sel_pop_k','sel_warehouse_cap',
              'sel_route_load','sel_route_capacity','sel_route_missing','sel_route_rail',
              'sel_delivery_load','sel_freight_used','sel_freight',
              *(f'{prefix}_{r}' for prefix in ('sel_stock','sel_view_in','sel_view_out','total_stock','total_transit') for r in ('steel','coal'))}
    known = deltas | expenses | demand | stocks | balances
    # Replace existing decoration of these exact values, never whole prose.
    text = re.sub(r'§[YGR](\[\?RUS_ip_(\w+)\|[^\]]+\])§!',
                  lambda m:m[1] if m[2] in known else m[0], text)
    def value(m):
        key,precision=m[1],m[2][-1]
        plain=f'[?RUS_ip_{key}|{precision}]'
        if key in deltas:return f'[?RUS_ip_{key}|=+{precision}]'
        if key in balances:return f'[?RUS_ip_{key}|+{precision}]'
        if key in expenses:return f'§R-{plain}§!'
        if key in demand:return f'§R{plain}§!'
        if key in stocks:return f'§Y{plain}§!'
        return m[0]
    return re.sub(r'\[\?RUS_ip_(\w+)\|([=+]*[012])\]',value,text)


def localisation(L, defined, data):
    cells=data['cells'];hub=data['hub']
    register=L
    def L(key,zh,en,ru=None):
        return register(key,format_amounts(zh),format_amounts(en),format_amounts(ru) if ru else None)
    L('funds_summary','计划资金 §Y[?RUS_ip_funds|1]§!  |  [GetRUSIPBudgetStatus]  |  [GetRUSIPPolicy]',
      'Funds §Y[?RUS_ip_funds|1]§!  |  [GetRUSIPBudgetStatus]  |  [GetRUSIPPolicy]')
    L('budget_status','[?RUS_ip_budget_next|0] 天后结算：预计 [?RUS_ip_next_settlement|+1]','[?RUS_ip_budget_next|0]d to settlement: est. [?RUS_ip_next_settlement|+1]')
    L('budget_frozen','账本封存','Account frozen')
    L('budget_pending','等待启动','Awaiting start')
    L('policy_peace','和平经营','Peacetime industry')
    L('policy_war','§Y战时优先施工§!','§YWartime construction priority§!')
    defined('GetRUSIPBudgetStatus',[('has_country_flag = RUS_ip_active',P+'budget_status'),('has_country_flag = RUS_ip_ended',P+'budget_frozen'),('',P+'budget_pending')])
    defined('GetRUSIPPolicy',[('has_war = yes',P+'policy_war'),('',P+'policy_peace')])
    L('budget_projection','当前方案 / 30 天资金变动：[?RUS_ip_projected_settlement|+1]  |  [GetRUSIPDebtStatus]',
      'Funds change / 30d: [?RUS_ip_projected_settlement|+1] | [GetRUSIPDebtStatus]')
    L('budget_projection_tt','§Y按当前方案预估§!\n30 天资金变动：[?RUS_ip_projected_settlement|+1]\n本期累计经营净额：[?RUS_ip_budget_net|+1]\n距结算：[?RUS_ip_budget_next|0] 天\n预计资金变动：[?RUS_ip_next_settlement|+1]\n预计结算后余额：[?RUS_ip_next_balance|1]\n\n每日及操作后刷新；不含未来开工、取消退款、竣工、供料与战局变化。最近一次结算包含本期已发生收支。',
      '§YCurrent-plan forecast§!\n30-day funds change: [?RUS_ip_projected_settlement|+1]\nAccrued operating net: [?RUS_ip_budget_net|+1]\n[?RUS_ip_budget_next|0] days to settlement\nExpected change: [?RUS_ip_next_settlement|+1]\nExpected balance: [?RUS_ip_next_balance|1]\n\nUpdates daily and after actions. Excludes future starts, refunds, completions, supply and war changes. The next settlement includes actual accruals.')
    L('budget_projection_pending','启动建设计划后显示资金预估。','Start the programme to see the funds forecast.')
    L('budget_projection_frozen','建设期已结束，账本封存，不再结算。','Programme ended; the account is frozen and no longer settles.')
    defined('GetRUSIPBudgetForecast',[('has_country_flag = RUS_ip_active',P+'budget_projection_tt'),('has_country_flag = RUS_ip_ended',P+'budget_projection_frozen'),('',P+'budget_projection_pending')])
    L('supply','仓储与预算','Supply / budget')
    L('supply_title','计划资金 · 仓储与调拨','Programme funds · Warehouses and freight')
    L('stock_ribbon','库存：钢 [?RUS_ip_sel_stock_steel|1] / 煤 [?RUS_ip_sel_stock_coal|1]  ·  日需求 [?RUS_ip_sel_need_steel|2] / [?RUS_ip_sel_need_coal|2]  |  [GetRUSIPArrival]  |  净收支 [?RUS_ip_sel_net_month|1] / 30 天',
      'Stock ST [?RUS_ip_sel_stock_steel|1] / CO [?RUS_ip_sel_stock_coal|1] · need [?RUS_ip_sel_need_steel|2] / [?RUS_ip_sel_need_coal|2] per day | [GetRUSIPArrival] | net [?RUS_ip_sel_net_month|1] / 30d')
    L('arrival_blocked','§R调拨线路中断§!','§RRoute interrupted§!')
    L('arrival_pending','最近到货约 [?RUS_ip_sel_arrival|1] 天','Next arrival ~[?RUS_ip_sel_arrival|1] days')
    L('arrival_none','暂无入境批次','No incoming batch')
    L('arrival_waiting','入境批次等待接收','Incoming batch awaiting reception')
    L('route_district','畅通时单程约 [?RUS_ip_sel_route_days|1] 天，拥堵会延长','Base journey ~[?RUS_ip_sel_route_days|1] days; congestion adds time')
    L('route_hub','总仓汇总全国批次；选择来源经济区可查看具体路线','Central warehouse aggregates batches; select a source district for its route')
    defined('GetRUSIPRouteDetail',[(cv('selected','=',hub),P+'route_hub'),('',P+'route_district')])
    for i,(path,_) in sorted(routes(data).items()):
        itinerary=' → '.join(f'[{cells[j]["state"]}.GetName]' for j in path)
        L(f'route_path_{i}',itinerary,itinerary)
    defined('GetRUSIPRoutePath',[(cv('selected','=',i),P+f'route_path_{i}') for i in range(len(cells))])
    defined('GetRUSIPRouteBottleneck',[(cv('sel_route_bottleneck','=',i),P+f'district_{i}') for i in range(len(cells))])
    gaps=[]
    for e in data['edge_sprites']:
        a,b=e['a'],e['b'];key=f'route_gap_{a}_{b}'
        L(key,f'[{cells[a]["state"]}.GetName] — [{cells[b]["state"]}.GetName]',f'[{cells[a]["state"]}.GetName] — [{cells[b]["state"]}.GetName]')
        gaps.append((cv('sel_route_gap','=',min(a,b)*len(cells)+max(a,b)),P+key))
    L('route_hub_lost','莫斯科总仓未由本国拥有并控制','Moscow warehouse is not owned and controlled')
    defined('GetRUSIPRouteGap',[(cv('sel_route_gap','=',-2),P+'route_hub_lost')]+gaps+[('',P+'route_hub_lost')])
    L('route_diagnosis_blocked','§R线路中断§!：[GetRUSIPRouteGap]\n先检查两端控制权与铁路连通；海运联系检查港口及运输船。',
      '§RRoute interrupted§!: [GetRUSIPRouteGap]\nCheck control and rail connections, or ports and convoys for sea links.')
    L('route_diagnosis_hub','总仓汇总多个方向；选择收货或发货经济区查看其线路瓶颈。',
      'The hub aggregates several routes; select a receiving or sending district to inspect its bottleneck.')
    L('route_diagnosis_busy','§R运输瓶颈§!：[GetRUSIPRouteBottleneck]\n负荷：[?RUS_ip_sel_route_load|1] / 容量：[?RUS_ip_sel_route_capacity|1]；运力缺口：[?RUS_ip_sel_route_missing|1]\n中心州铁路：[?RUS_ip_sel_route_rail|0] / §Y5§! 级。优先改善该区交通，或降低当地负荷。',
      '§RFreight bottleneck§!: [GetRUSIPRouteBottleneck]\nLoad: [?RUS_ip_sel_route_load|1] / capacity: [?RUS_ip_sel_route_capacity|1]; shortfall: [?RUS_ip_sel_route_missing|1]\nCentral-state rail: [?RUS_ip_sel_route_rail|0] / §Y5§!. Improve transport here or reduce local load.')
    L('route_diagnosis_clear','§G当前无运力瓶颈§!；按基础路程运输，继续升级铁路不会再缩短路程时间。',
      '§GNo freight bottleneck§!; normal journey time. Further rail upgrades will not shorten it.')
    defined('GetRUSIPRouteDiagnosis',[(cv('sel_route_live','=',0),P+'route_diagnosis_blocked'),(cv('selected','=',hub),P+'route_diagnosis_hub'),
            (cv('sel_route_bottleneck','>',-1),P+'route_diagnosis_busy'),('',P+'route_diagnosis_clear')])
    defined('GetRUSIPArrival',[(cv('sel_route_live','=',0),P+'arrival_blocked'),(cv('sel_arrival','>',0),P+'arrival_pending'),
                             (cv('sel_view_in_steel','>',0),P+'arrival_waiting'),(cv('sel_view_in_coal','>',0),P+'arrival_waiting'),('',P+'arrival_none')])
    L('plan_debt','计划建设负债','Programme Construction Debt')
    L('plan_debt_desc','工程账款积欠，公共开支难以维系。承建单位失去信心，生产与建设秩序也随之受到冲击。','Unpaid bills undermine public services and confidence among contractors, disrupting construction and economic order.')
    L('debt_active','§R负债§!：[?RUS_ip_debt|1]','§RDebt§!: [?RUS_ip_debt|1]')
    L('debt_clear','无负债','No debt')
    defined('GetRUSIPDebtStatus',[(cv('funds','<',0),P+'debt_active'),('',P+'debt_clear')])
    L('funds_hover','[!ip_funds_icon_click]','[!ip_funds_icon_click]')
    L('funds_tt','§Y计划资金§!\n初始资金：§Y1000§!；独立账户，不与经济盈余兑换。\n每 30 天按实际收支结算，无固定拨款、无保底。\n开工一次扣款；资金不足时不能新开工。\n\n[GetRUSIPBudgetForecast]\n\n[GetRUSIPDebtStatus]\n建设期内每欠 §R100§!，稳定度 §R−5%§!、建造速度 §R−10%§!；分别封顶 §R−50%§!、§R−75%§!。\n按实际欠款连续计算，还款后减轻；原生与本界面建设均受影响。本期结束时清除惩罚。',
      '§YProgramme funds§!\nStarting funds: §Y1000§!; separate from the existing surplus.\nActual accounts settle every 30 days, without grants or a minimum.\nPay upfront; insufficient funds block new orders.\n\n[GetRUSIPBudgetForecast]\n\n[GetRUSIPDebtStatus]\nDuring the programme, per §R100§! owed: stability §R−5%§!, construction §R−10%§!, capped at §R−50%§!/§R−75%§!.\nScales continuously and recedes with repayment. Affects native and GUI construction. Penalties end when this programme expires.')
    L('warehouse_tt','§Y地区仓库§!\n钢、煤分别存放，各有容量上限。原生资源每占用 1 点，生产日入库 0.25 单位；全国至多使用可调配资源的一半。施工和经营每日消耗仓库，出库与在途物资不能再次使用。库存不足会减速或等待。',
      '§YRegional warehouse§!\nSeparate steel/coal capacities. Booking one native resource point yields 0.25 warehouse units that day, using at most half the national available flow. Daily operation and construction consume stocks. Dispatched cargo cannot be spent twice.')
    L('transit_tt','§Y自动调拨§!\n地区保留 21 天需求量后向莫斯科运送余料，总仓向缺料地区补至 14 天需求量。每个方向、每种物资最多一批；沿固定规划路线逐日运输，拥堵减速、断路停运。途中物资不计入可用库存。',
      '§YAutomatic freight§!\nRegions export beyond a 21-day reserve to Moscow. The hub supplies up to 14 days of regional demand. One batch per direction and resource. Fixed planning routes, congestion delays and interruptions. Cargo in transit is unavailable.')
    L('balance_tt','§Y地区收支§!\n民工经营收入受发展度、仓储供料、用工与电力影响；矿业按实际入库量贡献收入。军工、公共设施、电网、铁路和基本公共服务产生维持费用。这里只核算本计划的贡献，不改变原生工厂产出。',
      '§YRegional balance§!\nCivilian income depends on development, materials, labour and power. Mining earns on actual production. Military industry, facilities, grids, rail and public services incur upkeep. These are programme contributions, not native factory output penalties.')
    cards={
        'funds':('统一计划资金\n§Y[?RUS_ip_funds|1]§!', 'Programme funds\n§Y[?RUS_ip_funds|1]§!'),
        'warehouse':('本区库存  钢 / 煤\n[?RUS_ip_sel_stock_steel|1] / [?RUS_ip_sel_stock_coal|1]', 'Local stock · ST / CO\n[?RUS_ip_sel_stock_steel|1] / [?RUS_ip_sel_stock_coal|1]'),
        'transit':('运抵本区  钢 / 煤\n[?RUS_ip_sel_view_in_steel|1] / [?RUS_ip_sel_view_in_coal|1]', 'Inbound · ST / CO\n[?RUS_ip_sel_view_in_steel|1] / [?RUS_ip_sel_view_in_coal|1]'),
        'balance':('本区净收支 / 30 天\n§Y[?RUS_ip_sel_net_month|1]§!', 'Local balance / 30 days\n§Y[?RUS_ip_sel_net_month|1]§!'),
    }
    for k,(zh,en) in cards.items():L('supply_card_'+k,zh,en)
    L('budget_ledger_projection','距下次结算：[?RUS_ip_budget_next|0] 天\n预计资金变动：[?RUS_ip_next_settlement|+1]　结算后余额：[?RUS_ip_next_balance|1]\n本期累计经营净额：[?RUS_ip_budget_net|+1]\n每 30 天资金变动：[?RUS_ip_projected_settlement|+1]',
      'Next settlement: [?RUS_ip_budget_next|0] days\nFunds change: [?RUS_ip_next_settlement|+1] · balance: [?RUS_ip_next_balance|1]\nAccrued operating net: [?RUS_ip_budget_net|+1]\nFunds change / 30d: [?RUS_ip_projected_settlement|+1]')
    defined('GetRUSIPLedgerForecast',[('has_country_flag = RUS_ip_active',P+'budget_ledger_projection'),('has_country_flag = RUS_ip_ended',P+'budget_projection_frozen'),('',P+'budget_projection_pending')])
    L('budget_ledger','§Y全国计划账本§!\n[GetRUSIPLedgerForecast]\n上期实际结算：[?RUS_ip_last_budget|1]\n累计开工支出：[?RUS_ip_funds_spent|1]　累计退款：[?RUS_ip_funds_refunded|1]\n全国钢库存：[?RUS_ip_total_stock_steel|1]　煤库存：[?RUS_ip_total_stock_coal|1]\n全国在途钢：[?RUS_ip_total_transit_steel|1]　在途煤：[?RUS_ip_total_transit_coal|1]\n[GetRUSIPDebtStatus]；悬浮顶部资金查看影响。',
      '§YNational account§!\n[GetRUSIPLedgerForecast]\nLast settlement: [?RUS_ip_last_budget|1]\nTotal spending: [?RUS_ip_funds_spent|1] · refunds: [?RUS_ip_funds_refunded|1]\nSteel stock: [?RUS_ip_total_stock_steel|1] · coal: [?RUS_ip_total_stock_coal|1]\nSteel in transit: [?RUS_ip_total_transit_steel|1] · coal: [?RUS_ip_total_transit_coal|1]\n[GetRUSIPDebtStatus]; hover funds for effects.')
    L('supply_local','§Y所选经济区§!\n控制州数：[?RUS_ip_sel_members|0]　人口：[?RUS_ip_sel_pop_k|0] 千\n单种物资仓容：[?RUS_ip_sel_warehouse_cap|1]　库存可用约 [?RUS_ip_sel_cover|1] 天\n工业每日需求：钢 [?RUS_ip_sel_base_steel|2] / 煤 [?RUS_ip_sel_base_coal|2]\n施工每日需求：钢 [?RUS_ip_sel_project_steel|2] / 煤 [?RUS_ip_sel_project_coal|2]\n民工经营收入：[?RUS_ip_sel_income_month|1] / 30 天\n矿业收入折算：[?RUS_ip_sel_mining_month|1] / 30 天（按当日入库）\n维持支出：[?RUS_ip_sel_upkeep_month|1] / 30 天\n本工程开工支出：[?RUS_ip_sel_paid|1]\n取消可退款：[?RUS_ip_sel_refund|1]',
      '§YSelected economic region§!\nStates: [?RUS_ip_sel_members|0] · population: [?RUS_ip_sel_pop_k|0] thousand\nStorage/resource: [?RUS_ip_sel_warehouse_cap|1] · cover: ~[?RUS_ip_sel_cover|1] days\nIndustrial daily demand: ST [?RUS_ip_sel_base_steel|2] / CO [?RUS_ip_sel_base_coal|2]\nConstruction daily demand: ST [?RUS_ip_sel_project_steel|2] / CO [?RUS_ip_sel_project_coal|2]\nCivilian income: [?RUS_ip_sel_income_month|1] / 30 days\nMining run rate: [?RUS_ip_sel_mining_month|1] / 30 days\nUpkeep: [?RUS_ip_sel_upkeep_month|1] / 30 days\nProject spending: [?RUS_ip_sel_paid|1]\nRefund on cancellation: [?RUS_ip_sel_refund|1]')
    L('supply_route','§Y调拨与线路§!\n往返路线：[GetRUSIPRoutePath]\n[GetRUSIPRouteDiagnosis]\n[GetRUSIPArrival]；[GetRUSIPRouteDetail]\n本区发运钢：[?RUS_ip_sel_view_out_steel|1]　煤：[?RUS_ip_sel_view_out_coal|1]\n在途货物运输负荷：[?RUS_ip_sel_delivery_load|1]\n本区总负荷：[?RUS_ip_sel_freight_used|1]　容量：[?RUS_ip_sel_freight|1]',
      '§YDispatch and route§!\nRoute: [GetRUSIPRoutePath]\n[GetRUSIPRouteDiagnosis]\n[GetRUSIPArrival]; [GetRUSIPRouteDetail]\nOutbound steel: [?RUS_ip_sel_view_out_steel|1] · coal: [?RUS_ip_sel_view_out_coal|1]\nCargo freight load: [?RUS_ip_sel_delivery_load|1]\nLocal total load: [?RUS_ip_sel_freight_used|1] · capacity: [?RUS_ip_sel_freight|1]')
    L('route_focus','查看问题地区','Inspect bottleneck')
    L('route_focus_tt','选中当前路线最拥堵的经济区；若线路中断，则选中首处中断联系的远端地区。显示的是经济区中心州，不是逐省铁路区段。',
      'Select the worst freight bottleneck, or the far side of the first interrupted link. Identifies a district centre, not a province-by-province railway segment.')
    L('supply_policy','§Y调度政策§!\n[GetRUSIPPolicy]；[GetRUSIPPriority]\n和平时先保障本区工业，再供应施工。开战后自动优先供应在建工程，资金、运输和 1800 天期限照常结算。\n可指定一个经济区优先调拨；其余按地区顺序自动安排。工厂不足时也优先保留该区施工。',
      '§YDispatch policy§!\n[GetRUSIPPolicy]; [GetRUSIPPriority]\nPeace: local industry first. War: queued construction first, with normal accounts, freight and programme clock.\nSelect one priority region; others follow district order. The priority also applies to civilian factory allocation.')
    L('priority','优先供给本区','Prioritise district')
    L('priority_selected','§G本区优先供给§!','§GThis district has priority§!')
    L('priority_other','本区采用常规调度','Normal dispatch for this district')
    defined('GetRUSIPPriority',[(cv('priority','=',P+'selected'),P+'priority_selected'),('',P+'priority_other')])
    L('priority_tt','再次点击可取消本区优先级。优先保障民工分配与总仓发车顺序，不立即到货、不产生免费物资，也不撤回已发出的货物。','Click again to remove priority. Changes civilian allocation and dispatch order; never creates materials, instant arrivals or recalls cargo.')
    L('supply_note','物资单位为本计划仓储单位。现有工厂照常参加原生生产；本页经营收支只计入计划资金。',
      'Warehouse units belong to this programme. Native industry keeps operating normally; this page records programme contributions only.')


def widgets(text, icon, button, background):
    text('ip_supply_title',P+'supply_title',160,125,1440,36,'hoi_24header',True,page='supply')
    text('ip_supply_selected',P+'site_summary',170,174,1420,28,'hoi_20b',True,page='supply')
    for idx,key in enumerate(SUPPLY_ICONS):
        x=170+360*idx
        background('ip_supply_bg_'+key,x,218,340,82,'supply')
        tip=P+('funds_hover' if key=='funds' else key+'_tt')
        icon('ip_supply_icon_'+key,'GFX_RUS_ip_'+key,x+18,242,SUPPLY_ICONS[key][1],page='supply',tip=tip)
        text('ip_supply_card_'+key,P+'supply_card_'+key,x+70,236,260,52,page='supply',tip=tip)
    text('ip_budget_ledger',P+'budget_ledger',180,335,660,230,page='supply')
    text('ip_supply_local',P+'supply_local',910,335,660,240,page='supply')
    text('ip_supply_route',P+'supply_route',180,574,660,254,page='supply')
    button('ip_route_focus',P+'route_focus',180,838,P+'route_focus_tt','RUS_ip_focus_route = yes','RUS_ip_available = yes\n'+cv('sel_route_focus','>',-1),page='supply')
    text('ip_supply_policy',P+'supply_policy',910,620,660,180,page='supply')
    button('ip_priority',P+'priority',910,810,P+'priority_tt','RUS_ip_prioritise = yes','RUS_ip_editing = yes',page='supply')
    text('ip_supply_note',P+'supply_note',180,883,1400,48,page='supply')
    button('ip_supply_back',P+'back',818,948,'','RUS_ip_toggle_supply = yes',page='supply')
