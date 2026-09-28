# 独立工业建设 GUI：维护入口

更新：2026-09-28。完整玩家规则、公式、费用、图表和策略说明见 [工业建设GUI玩法说明](../工业建设GUI玩法说明.md)。本文件记录生成来源与结算边界。

仅开发测试版，独立于旧一五计划，不接入、不删除旧任务、积分或结算奖励，按用户要求不生成上传目录。以新开局为测试基线；本轮不回填旧原型存档的资金、仓库或发展度。

## 维护来源

| 用途 | 维护源 |
| --- | --- |
| 生命周期、真实建造、资格、原生占用与每日入口 | industrial_planning_economy.py |
| 地区发展、用工、电力、运力、余电调拨、工期与递减收益 | industrial_planning_regions.py |
| 多州汇总、计划资金、有限仓库、路线、批次与收支 | industrial_planning_supply.py |
| 资金/仓储/物流图标、账本页及文本 | industrial_planning_supply_ui.py |
| 总生成入口、主界面、帮助、原生效果提示、本地化与测试决议 | generate_industrial_planning.py |
| KR 几何与图形 | build_industrial_planning_map.py、data/industrial_planning_map.json |
| 执行真实生成脚本的回归 | test_industrial_planning.py，也调用 test_industrial_planning_supply.py |
| 实际 GUI 坐标布局预览 | preview_industrial_planning.py，只写 output/industrial_planning/ |

总入口返回“相对路径 → 内容”，导入不写盘，默认只读检查；普通文本生成不重画地图。输出仍为 13 份：effects、triggers、scripted_gui、scripted_localisation、on_actions、dynamic_modifiers、decisions、category、GUI、GFX 和三语本地化。中文、英文完整，俄语部分文本以英文回退，全部本地化保持 UTF-8 BOM。

~~~powershell
python -B tools/generate_industrial_planning.py --check
python -B tools/build_industrial_planning_map.py --check
python -B tools/test_industrial_planning.py
python -B tools/validate.py

# 修改维护源后显式写出；不生成上传目录。
python -B tools/generate_industrial_planning.py --write
python -B tools/generate_industrial_planning.py --output-root C:/Temp/industrial-preview
python -B tools/preview_industrial_planning.py
python -B tools/preview_industrial_planning.py --idle
python -B tools/preview_industrial_planning.py --supply-page
python -B tools/preview_industrial_planning.py --help-page
python -B tools/preview_industrial_planning.py --finished
~~~

## 作用域与统计

全部计划变量保存于原始 RUS 国家作用域，前缀 RUS_ip_。州作用域只读取原生数据或接受竣工成果。人类玩家只能操作本国 RUS；转国后原 RUS 的已启动计划继续处理，AI 不主动启动或排队。

36 区共 104 个州。aggregate() 仅累计同时拥有且控制的成员州；人口与工业规模加权计算基础设施。发展度由该快照一次播种，刷新或领土变化不重置。原生竣工、槽位、铁路等级和主要资格仍以命名中心州为准。

开工检查真实民工额度、资金、中心州资格、队列空闲和发展度。原料不再按项目直接重复占用国家资源：可先排队等待仓库供料。民工分配优先指定地区再按编号；原料生产最多使用全国可调配资源一半，地区之间按申请量同比例分配。

## 日度与刷新顺序

on_daily 调用 RUS_ip_daily，只对已启动且 active 的原始 RUS 生效：

1. 读取原生可用民工/钢/煤，加回自身上次占用，形成当日容量快照。
2. 刷新原生统计、分配民工、地区供需、线路、到货预估和速度。
3. 处理仓库及目的地失守损失；按资源和仓容生产当日库存，记原生资源占用。
4. 既有批次推进路程并按空间到货；重算运力。
5. 发出新批次，依次处理指定优先区、战时未完工区和其他编号；重算含新货流的供需。
6. 按供料比例消耗仓库，累计经营净额，必要时结算 30 天账本。
7. 运行项目增加工作量；符合完工条件则先清队列与 paid，再发一次原生成果和发展收益。
8. 期限减一天；最后一天允许正常竣工，其余项目退款、清队列与原生占用，清剩余开采惩罚。
9. 刷新界面与额度显示。

refresh / supply_refresh 仅重算派生值及原生修正，不生产、发车、到货、领料、积累利润或推进时间。开关窗口、帮助、账本、选择地区、载入均不调用日度结算。按钮实际操作在 hidden_effect，原生竣工预览使用 effect_tooltip，不能提前发奖。

取消先刷新退款，再返还“未完工比例 × 实付资金 × 75%”，随即清除 paid/refund 防重。暂停保留 paid/work，释放民工并停止本项目耗料，地区仓储和既有工业仍经营。

## 资金、物资与原生占用

资金初始 1000；每 30 天只结算累计经营净额，已删除固定拨款与不足 25 的补足。funds 与 last_budget 允许负值，不加非负夹取。与农业、经济盈余、旧一五计划不兑换。

cargo_totals 只刷新预估：projected_operating/projected_settlement 为各区当前 net_month 合计；next_settlement 使用 budget_net 加当前日净额乘 budget_next，next_balance 为余额加该预估。显示与实际结算都没有拨款/补助/下限。以上变量不写账本、不推进预算日；未启动和结束不宣称将来会结算。

refresh_debt 将负余额转为欠款；active 时 stability_factor = max(−0.50, −debt×0.0005)，production_speed_buildings_factor = max(−0.75, −debt×0.001)，以 RUS_ip_plan_debt 动态修正施加，刷新覆盖数值而不累加。refresh 在计算施工速度前更新 debt_speed_factor = 1 + debt_construction，live 和 forecast 均在配套下限后乘一次。余额恢复至零或期满后移除动态修正。新开工仍要求 funds >= cost；既有工程可以继续。退款后即时刷新惩罚，期满封存负余额但不留下永远无法偿还的测试修正。

- 资金：funds = 1000 − funds_spent + funds_refunded + funds_settled。
- 每种材料：produced = 所有 stock + 所有 in/out 批次 + consumed + lost。

每点原生资源生产额度生成 0.25 仓储单位，记录 produced/booked；出库扣源仓进入批次，到货仅将批次移入仓库，消费才计 consumed。目的地失守损失计 lost，反复刷新不得再扣。后来失地造成仓容缩小可暂时超容，停止新生产，不额外删除合法库存。

和平先供应工业、战时先供应施工，各用途按钢煤共同满足率消耗。经营收入还受用工和电力限制；矿业收入仅按当天实际入库数量计入一次，mining_month 是当日水平的 30 天折算。完整公式集中在玩家说明中，维护时应与生成源码一起更新。

civilian_factory_use 只占用施工民工；country_resource_cost_steel/coal 只占用当日入库生产的资源，用 force_update_dynamic_modifier 更新。不改写原生工厂产出，不扣征兵人力。无工程时仍可生产库存，不能因为 running==0 就移除整个占用修正。原生缓存与面板即时刷新仍需游戏确认。

## 路线与规划约束

routes() 按 KR 邻接与固定地图距离计算莫斯科至各区的规划路径，指定海运终点经对应港口。运行时逐段核对原生连接；断路保留同一批次，不自动换路，不声称 GUI 直线就是逐省铁路。

本地保留 21 天需求后出口，总仓补给至 14 天需求并保留 7 天自用；这两个阈值避免正常货物往返空转。每区每种材料各一个进货与出货槽。全部在途量/14 计入沿途每区，最低运输满足率决定路程推进，最小速度 5%；新发车保留当地运力 10% 的应急通道，避免交通配套永久拿不到材料，但仍计入实际拥堵。

先计在途运输负荷，再安排相邻余电。余电不得转售，每点占两端各 0.5 运力，不跨海。交通工程固定开工铁路起点；失去起点暂停，内陆完工修一级接驳铁路，莫斯科与海运终点只加基础设施。铺轨寻路限制国内控制区域。

## 状态索引

| 状态（均有 RUS_ip_ 前缀） | 生命周期 |
| --- | --- |
| ui_unlocked / economy_initialized | 免费测试决议与一次性初始化 |
| started / active / ended / days_left | 一次性 1800 天周期 |
| open / help_open / supply_open / cancel_armed | 窗口、互斥页面、取消确认 |
| n*_project/work/required/paused/anchor/paid | 地区项目、进度、固定铁路起点、实付费用 |
| n*_development/trained/urban/training/done_*/mine_* | 完工积累，刷新不重置 |
| n*_stock_*/in_*/out_*/in_work_*/out_work_* | 库存、在途数量、剩余路程 |
| booked_*/produced_*/consumed_*/lost_* | 当日生产占用与物资总账 |
| funds/funds_spent/funds_refunded/funds_settled | 资金余额和累计流水 |
| budget_day/budget_net/last_budget | 当前 30 天周期与上期实际净额，无固定拨款与保底 |
| debt/debt_stability/debt_construction/debt_speed_factor | 欠款与派生惩罚，不单独扣款；归零或期满清除惩罚 |
| n*_category/sel_category | 每次刷新读取中心州 KR 普通类型等级；特殊类型为 0 |
| priority | −1 常规，0—35 指定地区 |
| capacity_*/reserved_*/free_* | 原生快照与分配台账 |
| mining_completed/resource_penalty | −30% 开采惩罚，每矿业竣工恢复 2 个百分点，15 次封顶 |
| edge_*_live/flow、地区供需、route_live | 当次刷新派生值 |
| preview_*/forecast_*/calc_*/region_*/cargo_* | 临时计算，不作永久账本 |
| sel_*/progress_frame/dirty | 显示缓存与界面更新 |

期满保存完工成果、发展度、资金与仓库/批次用于查看，但停止运行，清 paid、原生占用及本期负债惩罚。负资源修正与付费建设不参与简易模式额外发奖。

## 地区扩建

PROJECTS[9] 沿用全部付费施工、资源消耗、民工占用、暂停、取消、截止和一地区一队列逻辑。基础 180 工作量、150 资金价、3 民工，每日钢 0.30/煤 0.20，地区用工 3/电力 2/运力 1，发展收益基础 3。费用与重复发展收益仍使用公共公式。

site_9 不要求空槽位，要求中心州属于 KR one 至 eleven；不改变 special ports/islands/wasteland 限制，也不对 twelve 额外加槽。完工在中心州用 if/else_if 将当时原生类型只提升一级，不对其他成员州施工；外部效果先升级时不会降级或连升多级。已经变成最大/特殊类别时队列暂停并允许取消。参考 KR common/scripted_effects/00_useful_scripted_effects.txt 的 increase_state_category_by_one_level，但刻意不复制其 else 的无限额外槽位分支。类型与槽位来自 KR common/state_category/state_categories.txt；名称参考 KR CN 的 00 Map State Categories 汉化。

原生 set_state_category 通过 effect_tooltip 展示，额外槽位说明复用 KR increase_state_category_by_one_level_tt；前后类型用已定义的原生类别本地化。预览与实际奖励分离，不提前改变州。按钮位于 x1566/y644，和八工程网格、进度条错开，复用 KR ITA_urban 建筑图标并缩放至 32 像素。

## 铁路选线与瓶颈提示

`industrial_planning_rail.py` 生成 PROJECTS[10]：点击选线按钮后 rail_pick 从 1（起点）转为 2（终点），完成后归零。地图动作使用 if/else_if，防止同一次点击选中两端。候选端点保存经济区编号、原生州 ID 和地图坐标；开工复制到 n*_rail_from_state/to_state/level，终点承担唯一队列、仓库、施工供需与进度。新的候选线不改已经接受的订单；正反两端重复队列禁用。

等级范围 1—5，基础 90 工作量、120 资金、3 民工、每日钢 0.30/煤 0.20、用工 3/电力 1/基础运输 2；价格与工作量另乘 `level × (1 + (abs(dx)+abs(dy))/200)`。坐标距离只作预算估算，不能当成实际省份路径长度。发展收益基础 2，配套工程能力下限 0.65。forecast 临时选取终点调用公共地区预测，然后恢复原选择，避免候选线预测覆盖普通项目。每日施工重新检查两端所有权/控制权与 can_build_railway，国内通路禁用负权重国家；无共享工厂槽位要求。

原生 `build_railway` 的变量州端点依据原版 `common/scripted_effects/SOV_scripted_effects.txt:8304`；固定 `level` 分支只在竣工奖励和 `effect_tooltip` 中调用。候选与已排队两端分别显示，地图以“起/终”标记候选。顶部工具栏使用裁切后地图上方空位，全部随地图页显隐；已排队线路显示在进度条下方。

用户指定参考的“日共重置：内容拓展”（只读目录 `3254004005`）中，`common/decisions/RGCZ_mod_sov.txt:165/189/214` 调用三组一键队列效果，实现在 `common/scripted_effects/RGCZ_SOV_effects.txt:258/312/463`。其基建、民工、军工用 `add_building_construction` + `instant_build=no` 确实进入原版队列；检查该模组铁路效果只找到 `build_railway`，未找到铁路加入原版队列的实现。因此本铁路按用户已选方案使用 GUI 付费计时，不能把参考模组的一般建筑队列当成“铁路原版排队已证实”，也不能断言所有一键原版队列都做不到。

`cargo_routes/cargo_prepare` 为每区缓存固定总仓路径、第一段断线、最小到达倍率对应地区及该区运力/负载/缺口/铁路等级。账本列出完整地区路线；`focus_route` 只跳转瓶颈或首个断线远端，不推进时间、不花费物资。总仓汇总多路批次，不伪造单一瓶颈。此提示不读取省份铁路路径或整段最低等级；玩家仍需原版铁路地图核对具体修哪一段。人工新铁路不修改固定仓储 Dijkstra 路由。

`test_industrial_planning_rail.py` 执行生成的实际按钮及效果，检查两次点击、相同端点、改选、等级、锁定线路、保存重载、正反重复、施工缺料/失地/断路、满槽可建、付款退款/期满/单次原生奖励。模型只近似原生铁路连通，不替代引擎寻路验收。`preview_industrial_planning.py --railway` 展示一条在建线路和另一条候选线路并存的布局。

## 地图、图标与布局

地图以 KR provinces.bmp、definition.csv 与州历史为几何来源。先前内置 ImageGen 只增加纸纹与配色，固定源图、参照、完整提示词和来源在 assets/industrial_planning/。本轮未调用图像生成，未改几何或 120 张运行图片；只读检查比较 KR 输入、美术和输出哈希，不重画。

窗口 1760×1000，地图 1168×432 按 1.25 倍显示。保留上方地图、中部四项配套、下方八工程与进度的布局。顶部钱袋、仓储提示及独立账本页增加资金/仓库/在途/地区收支图标，统一约 32 像素，行内小图标缩小。图标来自已核对素材：KR 的 gfx/texticons/bag_of_money.png；原版 ability_extra_supplies.dds、decision_generic_train.dds、decision_hol_attract_foreign_investors.dds。通过独立 GFX_RUS_ip_* 引用，不覆盖共享美术。工程图标与红黑米白按钮沿用原有资源。

原生依据：游戏 documentation 下 dynamic_variables_documentation.md、effects_documentation.md、triggers_documentation.md；KR common/scripted_effects/00_wiki_scripted_effects.txt 的 state_population_k；原版 common/dynamic_modifiers/TAOG_dynamic_modifiers.txt 的资源成本与民工占用；KR common/decisions/01 KMT decisions.txt 的采矿、建筑、铁路；KR common/buildings/00_buildings.txt 的强化电网；KR interface/kaiserreich/gui_mitteleuropa.gui 的 iconType/pdx_tooltip。原生名称与效果由引擎及现有汉化显示。

## 验证边界

页面卡片背景必须使用受 `_visible` 控制的 `iconType`，通过专用 `corneredTileSpriteType` 复用原版九宫格边框。不能给嵌套 `containerWindowType` 写页面 `_visible` 来隐藏背景：实机出现过地图页与仓储页互相残留四个空框。参考 KR 的 `interface/kaiserreich/gui_china.gfx` 中 `GFX_party_banned_overlay` 与 `gui_china.gui` / `01 chinese scripted guis.txt` 中 `UPC_party_ban_bg`。布局预览会拒绝该错误结构，但不替代引擎验收。

地图用无背景、`clipping=yes` 的固定视口裁去顶端 `northern_map_limit_y` 非地理斜纹区；`ip_map` 图标自己受页面显隐控制。嵌套图标引用参考 KR 开局介绍的 `country_intro_page_indicator_box`。删去边界标签，不重画底图或改地区坐标，保留登记美术与 120 张贴图哈希。

工程悬浮提示显式绑定 `pdx_tooltip` → `RUS_ip_build_*_hover` → `[!ip_build_*_click]`，参考 KR 的 `st manager l_english.yml`、对应简中汉化和 `00_st_state_transfer.txt`。先显示自定义完工收益，再用 `effect_tooltip` 预览实际原生奖励，最后显示成本与工期；真实开工操作仍在 `hidden_effect` 内。公共设施、培训不伪造原生建筑。标签和图标保持鼠标穿透，避免遮挡整个按钮热区；本地化外层键与内层说明分离，禁止循环展开。

自定义数字格式参考 KR RUS_change_projection_tt 的 |=+1（带符号和正负颜色）。成本为红色负数，占用/需求为红色正数，库存/门槛为黄色；民工占用名称复用原生 MODIFIER_CIVILIAN_FACTORY_USE。funds/next_balance 用 |+1 随余额变色，禁止外层黄色覆盖负债红色。日期不修改。钱袋使用可点击按钮，funds_hover 绑定其 click；资金说明后用 effect_tooltip 展示实际债务动态修正，点击只切换账本。preview_industrial_planning.py --supply-page --debt 可检查示例负余额布局；并非实际存档或原生提示渲染。

施工回归显式注入测试库存以独立验证原有建设规则；真实开局测试验证初始空仓。新增回归覆盖聚合、资金和材料守恒、生产上限、公平额度、发车/到货、断路、目的地失守、拥堵、取消防重、战时先后、预算周期和期满。不得把测试注入库存误写成免费起始奖励。

检查生成确定性、独立输出根、引用、编码、重复键与布局，另跑 RHoiScribe 相关文件、全项目和修复 dry-run。跨语言键、内部共有属性、defined_text 和未带上游的资产告警应按证据分类，不自动批量改历史问题；括号和未闭合块必须绿色。

静态模型及布局预览不等于实机验收。用户负责新开局验证原生占用缓存、日度处理、保存重载、真实建造、断线/失地/截止日、字体与点击热区。以 1920×1080、100% UI 缩放为布局目标，其他缩放仍待实测；本轮不启动游戏、不构建上传目录。
