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

资金初始 1000；每 30 天结算累计经营净额与 100 拨款，合计不足 25 时应急补足，上期补助单列。与农业、经济盈余、旧一五计划不兑换。

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
| budget_day/budget_net/last_budget/last_support | 当前 30 天周期与上期结果 |
| priority | −1 常规，0—35 指定地区 |
| capacity_*/reserved_*/free_* | 原生快照与分配台账 |
| mining_completed/resource_penalty | −30% 开采惩罚，每矿业竣工恢复 2 个百分点，15 次封顶 |
| edge_*_live/flow、地区供需、route_live | 当次刷新派生值 |
| preview_*/forecast_*/calc_*/region_*/cargo_* | 临时计算，不作永久账本 |
| sel_*/progress_frame/dirty | 显示缓存与界面更新 |

期满保存完工成果、发展度、资金与仓库/批次用于查看，但停止运行，清 paid 和原生占用。负资源修正与付费建设不参与简易模式额外发奖。

## 地图、图标与布局

地图以 KR provinces.bmp、definition.csv 与州历史为几何来源。先前内置 ImageGen 只增加纸纹与配色，固定源图、参照、完整提示词和来源在 assets/industrial_planning/。本轮未调用图像生成，未改几何或 120 张运行图片；只读检查比较 KR 输入、美术和输出哈希，不重画。

窗口 1760×1000，地图 1168×432 按 1.25 倍显示。保留上方地图、中部四项配套、下方八工程与进度的布局。顶部钱袋、仓储提示及独立账本页增加资金/仓库/在途/地区收支图标，统一约 32 像素，行内小图标缩小。图标来自已核对素材：KR 的 gfx/texticons/bag_of_money.png；原版 ability_extra_supplies.dds、decision_generic_train.dds、decision_hol_attract_foreign_investors.dds。通过独立 GFX_RUS_ip_* 引用，不覆盖共享美术。工程图标与红黑米白按钮沿用原有资源。

原生依据：游戏 documentation 下 dynamic_variables_documentation.md、effects_documentation.md、triggers_documentation.md；KR common/scripted_effects/00_wiki_scripted_effects.txt 的 state_population_k；原版 common/dynamic_modifiers/TAOG_dynamic_modifiers.txt 的资源成本与民工占用；KR common/decisions/01 KMT decisions.txt 的采矿、建筑、铁路；KR common/buildings/00_buildings.txt 的强化电网；KR interface/kaiserreich/gui_mitteleuropa.gui 的 iconType/pdx_tooltip。原生名称与效果由引擎及现有汉化显示。

## 验证边界

施工回归显式注入测试库存以独立验证原有建设规则；真实开局测试验证初始空仓。新增回归覆盖聚合、资金和材料守恒、生产上限、公平额度、发车/到货、断路、目的地失守、拥堵、取消防重、战时先后、预算周期和期满。不得把测试注入库存误写成免费起始奖励。

检查生成确定性、独立输出根、引用、编码、重复键与布局，另跑 RHoiScribe 相关文件、全项目和修复 dry-run。跨语言键、内部共有属性、defined_text 和未带上游的资产告警应按证据分类，不自动批量改历史问题；括号和未闭合块必须绿色。

静态模型及布局预览不等于实机验收。用户负责新开局验证原生占用缓存、日度处理、保存重载、真实建造、断线/失地/截止日、字体与点击热区。以 1920×1080、100% UI 缩放为布局目标，其他缩放仍待实测；本轮不启动游戏、不构建上传目录。
