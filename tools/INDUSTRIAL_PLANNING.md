# 独立工业建设 GUI 原型

2026-09-28 按用户最新要求先单独开发，不承接或删除旧一五计划，不构建上传目录。人类 RUS 先执行免费的、仅能执行一次的“启用工业建设界面（测试）”决议，才显示农业左侧的工业入口并打开窗口。解锁和打开不启动计时，也不施加惩罚；点击窗口内“启动建设计划”才开始独立的 1800 天建设期。只有每日钩子推进工作量和期限，刷新、打开、帮助页与载入均不推进时间。

## 建设规则

取消旧原型的五轮、虚拟投资、库存、手动结算和反复重开。保留煤铁资源链、供电、铁路连通、运力瓶颈及地区工业条件，以原生经济数据和建筑承载。每区一项在建工程，可跨区并行；完工后可以继续安排工程。

| 工程 | 基础工作量 | 占用民工 | 钢 | 煤 | 所需当地运力 | 完工产能 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 煤矿 | 120 | 2 | 2 | 0 | 1 | 中心州原生煤 +4，每区最多三次 |
| 铁矿 | 120 | 2 | 2 | 1 | 1 | 中心州原生钢 +4，每区最多三次 |
| 强化电网 | 180 | 3 | 4 | 2 | 1 | 原生 energy_infrastructure +1 |
| 钢铁厂 | 240 | 4 | 4 | 4 | 2 | 民工 +1，原生钢 +2 |
| 机械军工厂 | 300 | 5 | 6 | 2 | 3 | 军工 +1 |
| 交通建设 | 120 | 2 | 2 | 1 | 1 | 基础设施 +1；内陆地区由相邻已连通国内地区铺设一级铁路 |

这是付费建设等级，不发额外政治点、计划分数或最终奖励，未接入简易模式的奖励后处理。钢四没有独立铁矿石库存，矿业与炼钢均计入原生钢资源。电网使用 KR“强化电网”建筑的降低工厂能耗效果。工程遵守实际建筑上限和槽位，不增加免费共享槽位。

启动时获得“落后的资源开采体系”：战略资源获取效率 **−30%**，作用于煤炭及其他国内战略资源。使用原生国家修正 `local_resources_factor`，不是名称相似但无原生定义的 `resource_gain_efficiency`。每完成一项煤矿或铁矿恢复 **2 个百分点**，累计 15 项清除；计数封顶 15，不转为额外正面加成。暂停、取消、打开或刷新均不恢复效率。1800 天结束清除剩余惩罚。先施加惩罚再读取初始施工额度，避免使用惩罚生效前的供应量。负面修正不参与简易模式翻倍。

每日基础工作量为：

`1 + 中心州基础设施 × 0.12 + min(中心州民工, 20) × 0.025 + min(相关资源, 40) × 0.005`

煤矿、电网参考当地煤，其余参考当地钢。再乘以下系数：

- 当地运力为 `1 + 基础设施 + 本州最高铁路等级`，未接通莫斯科时为四分之一。速度乘 `clamp(当地运力 / 所需运力, 0.1, 1)`。
- 钢铁、机械工程必须接通莫斯科，并乘 `0.25 + 全国 energy_ratio × 0.75`。采矿、电网、交通在缺电时仍可修复瓶颈。
- 使用原生 has_railway_level / has_railway_connection。此原型不模拟逐段列车调度、线路距离或海运封锁。

鄂霍次克—堪察加、哈巴罗夫斯克—北萨哈林保留两条海运接驳：锚点接通莫斯科、两端拥有并控制港口、至少 10 艘运输船。海运端点和莫斯科的交通工程只提高基础设施；不跨海画铁路。内陆工程开工时固定铁路起点，起点失守或断线会暂停，不能在完工时改换起点。铺轨优先权非本国为负值，仅在本国控制区寻路。

## 占用与状态生命周期

`RUS_ip_construction_commitment` 动态修正使用原生 civilian_factory_use、country_resource_cost_steel、country_resource_cost_coal。施工持续占用工厂与资源，不破坏基础资源。每日重分配额度；不足时按地区编号依次保障工程，其他项目保留进度等待。可手动暂停来改变物资使用顺序。

初始化和每日边界读取 num_of_civilian_factories_available_for_projects、resource@*，加回自身上次占用得到额度上限。界面操作只重分配同一份额度，不能通过连续点击重复使用尚未更新的原生经济缓存。写回占用后使用 force_update_dynamic_modifier；不移除其他系统修正。原生工厂/资源面板即时刷新仍须实机确认。

每天复核拥有权、控制权、槽位及必要铁路条件，失效则暂停并释放占用。暂停保留进度，取消需第二次确认且丢弃该工程进度。完工先清空项目状态，再添加原生建筑/资源，防止重复发奖。第 1800 个日度步进允许当日竣工，随后清除其他队列、释放占用；既有成果保留，不能重启期限。

转国不复制工程；原 RUS 已开工项目继续每日处理并最终释放占用，AI 不能主动启动或操作。旧沙盘免费起始设施和虚拟库存不转换成原生产能。

国家旗标均为 RUS_ip_：ui_unlocked 是测试决议开关；economy_initialized 防止重复初始化；started/active/ended 控制期限；open/help_open/cancel_armed 控制界面。n0_* 至 n35_* 保存工程、工作量、暂停、固定铁路起点、矿业扩建次数。capacity_*/free_*/reserved_* 为占用台账，days_left/completed 为独立期限和竣工数，mining_completed/resource_penalty 保存恢复进度与可重算的负修正，sel_*/progress_frame/dirty 为界面缓存。

## 地图与界面

从 KR 真实州界和资源生成 36 个不规则经济区，覆盖开局 RUS/TRM 的 104 个州。工程落在命名中心州，采矿潜力参考整个经济区原始煤/钢矿分布。临时失去领土后仍可查看。

窗口 1536×726，地图 1168×432，圆点 26×26。地图保持原比例，标记避让不改变边界；固定 816×432 采样生成邻接，扩大显示不会改变接壤。圆点显示编号、当前工程图标或最近竣工类型；实际建筑数量在详情与悬浮提示中。六类工程复用原生煤、钢、电力、工厂、工业、列车图标。右侧显示当地数据、工程进度、预计时间；规则收进单独“玩法介绍”按钮。Esc/关闭保留工程。

地图以已安装 KR 的 provinces.bmp、definition.csv 与州历史为唯一几何来源；不混入现实国家轮廓或现代国界。内置 ImageGen 只为固定参照增加印刷纸纹与配色，2062×763 源图缩放到原有 1168×432 画布。36 区、中心州、点击位置、选区和运输关系继续由 KR 数据确定。KR 地图北缘之外显示斜线边栏，并由本地化标签注明“KR 地图北部边界”，不把裁切范围画成海面。

最终源图、几何参考、完整提示词和来源说明保存于 tools/assets/industrial_planning/。构建先核对重建的 KR 参考图是否逐像素一致，再打包固定源图；KR 地理更新导致图形变化时会停止，要求核对重绘。只读检查验证 KR 与美术哈希，不重画、不调用生成服务。放弃的现实地理草案仅留在 output/，不参与维护构建或游戏载入。

地区名称用 `[州ID.GetName]`，避免嵌套 `$STATE_*$` 原样显示。原生完工收益放入 effect_tooltip，实际点击只在 hidden_effect 中排队，不提前发奖。中文完整，俄语除标题外暂用英文回退。

## 维护来源与验证

| 用途 | 维护源 / 输出 |
| --- | --- |
| 地理及图形 | build_industrial_planning_map.py → 地图 JSON、地图、连线、标记、21 帧进度条 |
| 地图美术 | assets/industrial_planning/atlas_source.png；prompt.txt 与 README.md 记录实际提示及来源，构建只打包固定源图 |
| 规则 | industrial_planning_economy.py → scripted_effects、scripted_triggers、on_actions、dynamic_modifiers |
| 界面、测试入口及文本 | generate_industrial_planning.py → 决议/分类、scripted_guis、scripted_localisation、GUI、GFX、三语文本；总计 13 份运行文件 |
| 回归 | test_industrial_planning.py 执行实际生成脚本，模拟原生经济缓存、资源、建筑和领土 |
| 预览 | preview_industrial_planning.py 读取真实 GUI 坐标、图标、文本及示例施工状态，只写 output/ |

生成器返回相对路径及内容，默认只读检查，不在导入时执行测试、不重画图片。地图 JSON 固定 KR 依赖、美术源和图片 SHA-256，依赖更新会报告差异。中文及其他语言保持 UTF-8 BOM。

```powershell
python -B tools/build_industrial_planning_map.py --check
python -B tools/generate_industrial_planning.py --check
python -B tools/validate.py --group industry interface

# 显式修改后的生成顺序；不生成上传目录。
python -B tools/build_industrial_planning_map.py --write
python -B tools/generate_industrial_planning.py --write
python -B tools/generate_industrial_planning.py --output-root C:/Temp/industrial-preview
python -B tools/preview_industrial_planning.py
python -B tools/preview_industrial_planning.py --help-page
python -B tools/preview_industrial_planning.py --finished
```

依据：已安装游戏 documentation/dynamic_variables_documentation.md、effects_documentation.md、triggers_documentation.md；原版 common/dynamic_modifiers/TAOG_dynamic_modifiers.txt 的资源成本与民工占用；KR common/decisions/01 KMT decisions.txt 的原生采矿、建造、铁路效果；KR common/buildings/00_buildings.txt 的强化电网；KR 中文 country_resource_cost_coal 与原版 energy_infrastructure 名称。

回归覆盖测试决议开关、−30% 惩罚与十五次恢复/封顶、占用守恒、快速连续点击、日度施工、资源不足、断线/失地/槽位满、固定铁路起点、供电运力、暂停/取消释放、完工一次、期限清理、存档状态、转国/AI、旧计划隔离、地理及本地化。布局预览不是游戏截图。实机由用户确认入口、缩放、原生提示、煤炭与其他资源效率、每日进度、实际占用/释放、实际建筑、保存重载和截止日。
