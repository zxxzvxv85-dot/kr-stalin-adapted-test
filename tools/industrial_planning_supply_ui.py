"""Labels and widgets for the programme's funds, stock and automatic transport."""
from industrial_planning_economy import P, cv

# Existing KR/native assets, inspected at their source size. No generated image
# or replacement of shared sprites is needed. Each large icon fits a 32px box.
SUPPLY_ICONS = {
    'funds': ('gfx/texticons/bag_of_money.png', 1.6),
    'warehouse': ('gfx/interface/abilitylist/ability_extra_supplies.dds', 32/34),
    'transit': ('gfx/interface/decisions/decision_generic_train.dds', 32/33),
    'balance': ('gfx/interface/decisions/decision_hol_attract_foreign_investors.dds', 32/33),
}


def localisation(L, defined, hub):
    L('funds_summary','计划资金 §Y[?RUS_ip_funds|1]§!  |  [GetRUSIPBudgetStatus]  |  [GetRUSIPPolicy]',
      'Funds §Y[?RUS_ip_funds|1]§!  |  [GetRUSIPBudgetStatus]  |  [GetRUSIPPolicy]')
    L('budget_status','[?RUS_ip_budget_next|0] 天后结算：预计 [?RUS_ip_next_settlement|+1]','[?RUS_ip_budget_next|0]d to settlement: est. [?RUS_ip_next_settlement|+1]')
    L('budget_frozen','账本封存','Account frozen')
    L('budget_pending','等待启动','Awaiting start')
    L('policy_peace','和平经营','Peacetime industry')
    L('policy_war','§Y战时优先施工§!','§YWartime construction priority§!')
    defined('GetRUSIPBudgetStatus',[('has_country_flag = RUS_ip_active',P+'budget_status'),('has_country_flag = RUS_ip_ended',P+'budget_frozen'),('',P+'budget_pending')])
    defined('GetRUSIPPolicy',[('has_war = yes',P+'policy_war'),('',P+'policy_peace')])
    L('budget_projection','当前方案 / 30 天：经营 [?RUS_ip_projected_operating|+1]  |  含拨款及补助后 [?RUS_ip_projected_settlement|+1]',
      'Current plan / 30d: operating [?RUS_ip_projected_operating|+1] | with funding [?RUS_ip_projected_settlement|+1]')
    L('budget_projection_tt','§Y按当前方案预估§!\n30 天经营净额：[?RUS_ip_projected_operating|+1]\n固定拨款：§G+100.0§!\n预计应急补助：[?RUS_ip_projected_support|+1]\n30 天合计资金变动：[?RUS_ip_projected_settlement|+1]\n\n§Y最近一次结算§!\n本期已累计经营净额：[?RUS_ip_budget_net|+1]\n距结算还有 [?RUS_ip_budget_next|0] 天，按当前经营状态延续计算：\n预计资金变动：[?RUS_ip_next_settlement|+1]，其中补助 [?RUS_ip_next_support|+1]\n预计结算后余额：§Y[?RUS_ip_next_balance|1]§!\n\n每日及操作后刷新；不含未来开工、取消退款、竣工、供料与战局变化。30 天数值是当前方案的经营折算，最近一次结算另计本期已经发生的收支。',
      '§YCurrent-plan forecast§!\n30-day operating balance: [?RUS_ip_projected_operating|+1]\nAppropriation: §G+100.0§!\nEmergency support: [?RUS_ip_projected_support|+1]\n30-day funds change: [?RUS_ip_projected_settlement|+1]\n\n§YNext settlement§!\nAccrued operating balance: [?RUS_ip_budget_net|+1]\n[?RUS_ip_budget_next|0] days remaining at the current operating rate:\nFunds change: [?RUS_ip_next_settlement|+1], including support [?RUS_ip_next_support|+1]\nExpected balance: §Y[?RUS_ip_next_balance|1]§!\n\nUpdates daily and after actions. Excludes future starts, refunds, completions, supply and war changes. The 30-day figure is a run rate; the next settlement includes actual accruals.')
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
    defined('GetRUSIPArrival',[(cv('sel_route_live','=',0),P+'arrival_blocked'),(cv('sel_arrival','>',0),P+'arrival_pending'),
                             (cv('sel_view_in_steel','>',0),P+'arrival_waiting'),(cv('sel_view_in_coal','>',0),P+'arrival_waiting'),('',P+'arrival_none')])
    L('funds_tt','§Y计划资金§!\n独立建设账户，初始 1000；不与原有经济盈余互换。开工一次扣款，发展度越低费用越高。每 30 天结算经营收支并拨款 100；当合计低于 25 时补足至 25。\n\n[GetRUSIPBudgetForecast]',
      '§YProgramme funds§!\nSeparate account, starting at 1000. Upfront costs are higher in less developed regions. Every 30 days: operating balance + 100 appropriation, with emergency support to ensure at least 25 net. No exchange with the existing economy surplus.\n\n[GetRUSIPBudgetForecast]')
    L('warehouse_tt','§Y地区仓库§!\n钢、煤分别存放，各有容量上限。原生资源每占用 1 点，生产日入库 0.25 单位；全国至多使用可调配资源的一半。施工和经营每日消耗仓库，出库与在途物资不能再次使用。库存不足会减速或等待。',
      '§YRegional warehouse§!\nSeparate steel/coal capacities. Booking one native resource point yields 0.25 warehouse units that day, using at most half the national available flow. Daily operation and construction consume stocks. Dispatched cargo cannot be spent twice.')
    L('transit_tt','§Y自动调拨§!\n地区保留 21 天需求量后向莫斯科运送余料，总仓向缺料地区补至 14 天需求量。每个方向、每种物资最多一批；沿固定规划路线逐日运输，拥堵减速、断路停运。途中物资不计入可用库存。',
      '§YAutomatic freight§!\nRegions export beyond a 21-day reserve to Moscow. The hub supplies up to 14 days of regional demand. One batch per direction and resource. Fixed planning routes, congestion delays and interruptions. Cargo in transit is unavailable.')
    L('balance_tt','§Y地区收支§!\n民工经营收入受发展度、仓储供料、用工与电力影响；矿业按实际入库量贡献收入。军工、公共设施、电网、铁路和基本公共服务产生维持费用。这里只核算本计划的贡献，不改变原生工厂产出。',
      '§YRegional balance§!\nCivilian income depends on development, materials, labour and power. Mining earns on actual production. Military industry, facilities, grids, rail and public services incur upkeep. These are programme contributions, not native factory output penalties.')
    cards={
        'funds':('统一计划资金\n§Y[?RUS_ip_funds|1]§!', 'Programme funds\n§Y[?RUS_ip_funds|1]§!'),
        'warehouse':('本区库存  钢 / 煤\n§Y[?RUS_ip_sel_stock_steel|1] / [?RUS_ip_sel_stock_coal|1]§!', 'Local stock · ST / CO\n§Y[?RUS_ip_sel_stock_steel|1] / [?RUS_ip_sel_stock_coal|1]§!'),
        'transit':('运抵本区  钢 / 煤\n§Y[?RUS_ip_sel_view_in_steel|1] / [?RUS_ip_sel_view_in_coal|1]§!', 'Inbound · ST / CO\n§Y[?RUS_ip_sel_view_in_steel|1] / [?RUS_ip_sel_view_in_coal|1]§!'),
        'balance':('本区净收支 / 30 天\n§Y[?RUS_ip_sel_net_month|1]§!', 'Local balance / 30 days\n§Y[?RUS_ip_sel_net_month|1]§!'),
    }
    for k,(zh,en) in cards.items():L('supply_card_'+k,zh,en)
    L('budget_ledger_projection','距下次结算：[?RUS_ip_budget_next|0] 天；预计资金变动 [?RUS_ip_next_settlement|+1]\n预计结算后余额：[?RUS_ip_next_balance|1]\n本期已累计经营净额：[?RUS_ip_budget_net|+1]\n当前方案 / 30 天：经营 [?RUS_ip_projected_operating|+1]；合计 [?RUS_ip_projected_settlement|+1]\n合计包括固定拨款 100、预计应急补助 [?RUS_ip_projected_support|1]',
      'Next settlement: [?RUS_ip_budget_next|0] days; funds change [?RUS_ip_next_settlement|+1]\nExpected balance: [?RUS_ip_next_balance|1]\nAccrued operating net: [?RUS_ip_budget_net|+1]\nCurrent plan / 30d: operating [?RUS_ip_projected_operating|+1]; total [?RUS_ip_projected_settlement|+1]\nIncludes 100 appropriation, [?RUS_ip_projected_support|1] support')
    defined('GetRUSIPLedgerForecast',[('has_country_flag = RUS_ip_active',P+'budget_ledger_projection'),('has_country_flag = RUS_ip_ended',P+'budget_projection_frozen'),('',P+'budget_projection_pending')])
    L('budget_ledger','§Y全国计划账本§!\n[GetRUSIPLedgerForecast]\n上期实际入账：[?RUS_ip_last_budget|1]，其中应急补助 [?RUS_ip_last_support|1]\n累计开工扣款：[?RUS_ip_funds_spent|1]；取消与期满退款：[?RUS_ip_funds_refunded|1]\n全国库存：钢 [?RUS_ip_total_stock_steel|1] / 煤 [?RUS_ip_total_stock_coal|1]\n全国在途：钢 [?RUS_ip_total_transit_steel|1] / 煤 [?RUS_ip_total_transit_coal|1]',
      '§YNational account§!\n[GetRUSIPLedgerForecast]\nLast settlement: [?RUS_ip_last_budget|1], emergency aid [?RUS_ip_last_support|1]\nSpent: [?RUS_ip_funds_spent|1]; refunded: [?RUS_ip_funds_refunded|1]\nStock: steel [?RUS_ip_total_stock_steel|1] / coal [?RUS_ip_total_stock_coal|1]\nTransit: steel [?RUS_ip_total_transit_steel|1] / coal [?RUS_ip_total_transit_coal|1]')
    L('supply_local','§Y所选经济区§!\n统计 [?RUS_ip_sel_members|0] 个本国控制的州，人口 [?RUS_ip_sel_pop_k|0] 千\n每种物资仓容 [?RUS_ip_sel_warehouse_cap|1]；库存可用约 [?RUS_ip_sel_cover|1] 天\n工业日需求：钢 [?RUS_ip_sel_base_steel|2] / 煤 [?RUS_ip_sel_base_coal|2]\n施工日需求：钢 [?RUS_ip_sel_project_steel|2] / 煤 [?RUS_ip_sel_project_coal|2]\n民工经营收入 [?RUS_ip_sel_income_month|1] / 30 天\n矿业收入折算 [?RUS_ip_sel_mining_month|1] / 30 天（按当日入库）\n维持支出 [?RUS_ip_sel_upkeep_month|1] / 30 天\n本工程已付款 [?RUS_ip_sel_paid|1]；现在取消可退 [?RUS_ip_sel_refund|1]',
      '§YSelected economic region§!\n[?RUS_ip_sel_members|0] owned/controlled states, [?RUS_ip_sel_pop_k|0] thousand people\nCapacity per resource [?RUS_ip_sel_warehouse_cap|1]; cover ~[?RUS_ip_sel_cover|1] days\nIndustry/day: ST [?RUS_ip_sel_base_steel|2] / CO [?RUS_ip_sel_base_coal|2]\nConstruction/day: ST [?RUS_ip_sel_project_steel|2] / CO [?RUS_ip_sel_project_coal|2]\nCivilian income [?RUS_ip_sel_income_month|1] / 30 days\nMining run rate [?RUS_ip_sel_mining_month|1] / 30 days\nUpkeep [?RUS_ip_sel_upkeep_month|1] / 30 days\nProject paid [?RUS_ip_sel_paid|1]; refund now [?RUS_ip_sel_refund|1]')
    L('supply_route','§Y调拨与线路§!\n[GetRUSIPArrival]\n[GetRUSIPRouteDetail]\n从本区发出：钢 [?RUS_ip_sel_view_out_steel|1] / 煤 [?RUS_ip_sel_view_out_coal|1]\n本区在途货物占用运力 [?RUS_ip_sel_delivery_load|1]\n全部负荷 [?RUS_ip_sel_freight_used|1] / 容量 [?RUS_ip_sel_freight|1]\n目的地失守会损失对应库存与入境批次；中途断路只暂停运输。',
      '§YDispatch and route§!\n[GetRUSIPArrival]\n[GetRUSIPRouteDetail]\nOutbound: ST [?RUS_ip_sel_view_out_steel|1] / CO [?RUS_ip_sel_view_out_coal|1]\nCargo freight load [?RUS_ip_sel_delivery_load|1]\nTotal load [?RUS_ip_sel_freight_used|1] / [?RUS_ip_sel_freight|1]\nLost destinations lose stocks and incoming batches; route cuts only pause transit.')
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
        icon('ip_supply_icon_'+key,'GFX_RUS_ip_'+key,x+18,242,SUPPLY_ICONS[key][1],page='supply',tip=P+key+'_tt')
        text('ip_supply_card_'+key,P+'supply_card_'+key,x+70,236,260,52,page='supply',tip=P+key+'_tt')
    text('ip_budget_ledger',P+'budget_ledger',180,335,660,230,page='supply')
    text('ip_supply_local',P+'supply_local',910,335,660,240,page='supply')
    text('ip_supply_route',P+'supply_route',180,604,660,210,page='supply')
    text('ip_supply_policy',P+'supply_policy',910,620,660,180,page='supply')
    button('ip_priority',P+'priority',910,810,P+'priority_tt','RUS_ip_prioritise = yes','RUS_ip_editing = yes',page='supply')
    text('ip_supply_note',P+'supply_note',180,883,1400,48,page='supply')
    button('ip_supply_back',P+'back',818,948,'','RUS_ip_toggle_supply = yes',page='supply')
