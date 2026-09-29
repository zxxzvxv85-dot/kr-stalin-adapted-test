# 独立工业规划沙盘维护说明

当前实现：2026-09-29，局部 8×6 厂区、1800 天连续生产。旧的 36 经济区地图、地区资金与物流系统已退出当前生成入口。

## 唯一生成入口

```powershell
python tools/generate_industrial_planning.py --check
python tools/generate_industrial_planning.py --write
```

默认只检查，不写文件。支持 `--output-root <临时目录>` 独立复现 13 份输出，三语本地化使用 UTF-8 BOM。不得直接改生成后的脚本、GUI 或本地化。

- `tools/industrial_planning_factory.py`：格子定义、建设限制、连接与产能、每日配方、投资退款、计时与重置。
- `tools/industrial_planning_factory_ui.py`：GUI/GFX、三语文本、动态名称、入口与帮助页。
- `tools/test_factory_planning.py`：运行生成后的 Clausewitz 脚本，含独立图论判定与守恒检查。
- `tools/test_industrial_planning.py`：统一验证保留的入口，调用以上测试。
- `tools/test_factory_layout.py`：引用、三语 BOM/键、字体与资源、按钮绑定、分页残框和沙盘隔离。
- `tools/preview_industrial_planning.py`：读取实际 GUI 与本地素材做布局预览，只写 `output/industrial_planning/`，不是游戏截图。
- 玩家说明：根目录 `工业建设GUI玩法说明.md`。

## 输出与边界

仍生成 `RUS_industrial_planning` 对应的 triggers、effects、scripted_gui、on_actions、scripted_localisation、decisions/category、GUI/GFX 和三语本地化，共 13 份。动态修正文件保留生成声明但没有修正定义。

没有国家工厂/人力/资源占用、领土与铁路调用、债务惩罚，也没有旧一五计划的奖励或入口调用。新游戏是验收基线，不迁移此前地区经营原型的存档。保留测试决议解锁和 raid_filter 侧边独立入口，并保留中欧同盟时的入口避让。

此前 `industrial_planning_economy.py`、`industrial_planning_regions.py`、`industrial_planning_supply.py`、`industrial_planning_supply_ui.py`、`industrial_planning_rail.py`、`build_industrial_planning_map.py` 与旧地图数据、美术仍作为历史参考留在开发目录；当前入口不导入或引用它们。旧 supply/rail 专用测试仅适用于旧实现，不再由当前验证入口调用。正常开发不要运行旧地图的写入命令。需要查回旧实现时可参考提交 `4439a62`；最初五轮原型为 `a0914ea`。当前没有恢复轮数。

## 状态与算法

国家变量前缀 `RUS_ip_`；新初始化标识 `RUS_ip_factory_initialized`。`ui_unlocked` 控制入口、`open` 控制窗口、`started/active/finished` 控制阶段、`help_open` 控制分页。按钮在显示和实际执行两侧都检查窗口、页面及可操作状态。

格子固定 48 个，内部从 0 编号；显示 A1—H6，D6 为编号 43 的调度站，煤矿 9/17/33、铁矿 14/22/38、岩壁 11/12/27/28。设施类型 1—5 依次为煤矿、铁矿、电站、钢铁厂、机械厂，0 为空地。

每格持久变量：type、level、rail、paid、rail_paid、paused。route/effective 是可重算缓存。设施和线路上限三级，调度站自带三级线路，不可拆改。费用 3/3/5/6/8，线路每级 1。

网络采用带上限的单调松弛，最多 48 遍。每格 `route` 是通往调度站的所有正交路径中“最弱线路等级”的最大值。只有孤立环路不能凭空接通。`effective=min(level,route)`，停机时为零。每类产能为相应设施有效等级之和，不模拟共享路段总拥堵。

`refresh` 重算网络、产能、纯预测、选择缓存与 dirty。预测拷贝煤铁钢机械库存到 next_*，按采矿→发电→炼钢→机械顺序计算：采矿每级 +0.3/日，电站每级最多耗煤 0.1、供电 0.6；每单位钢耗煤 1、铁 1、电 2，每级最多钢 0.2/日；每单位机械耗钢 2、电 1，每级最多机械 0.2/日。浮点极小的剩余电力钳制到非负，短缺判定阈值 0.001。

`daily` 仅对已解锁、初始化且 active 的人类俄罗斯运行。先计算，再一次写回 next_*；每交付一机械回流一投资，计时减一，随后刷新下一日产量。第 1800 次结算后停止，避免多结算一天；达到 500 交付只改变完成度，不提前停止。`on_startup` 仅刷新已初始化国家，不发放资金或推进生产。

初始投资 40，煤6、铁4、钢2；初始布置不计时。预算守恒：`budget = 40 + earned - spent + refunded`，`earned = machines`。拆除退还实付，立即清零已付字段。显式二次确认重置才恢复开局；重复打开、解锁、帮助或刷新不重置预算。

## 界面与提示参考

窗口 1280×850，棋盘 8×6、每格 80×80、步长 84。没有俄罗斯地图纹理或 STATE 名称。资金、资源、设施及线路图标复用已安装 KR/原版素材，不新增生成图。

- KR `interface/core.gfx`：确认 `hoi_16mbs`、`hoi_20b` 等真实字体与数值颜色。
- KR `common/scripted_effects/00_useful_scripted_effects.txt`：`while_loop_effect` 用法。
- KR UPC 党派背景的 iconType + corneredTileSpriteType：独立控制卡片显隐，避免嵌套窗口背景跨页泄漏。
- 原版 `interface/core_bare_minimum.gfx`：`gfx/interface/transp_white.dds` 原生线段材质。
- KR 简中 `KR_common/st manager l_simp_chinese.yml` 与地区管理 GUI：显式 pdx_tooltip 绑定写法。当前奖励全是自定义沙盘值，所以直接使用彩色自定义提示，没有虚构原生工厂效果。

所有卡片、选中底框和连线都随页面显隐；厂区动作在帮助页不能穿透执行。线段在背景之上、设施图标之下，描绘相邻格子的真实运输连接。主界面“30天”是下一日产率折算，不是未来整月模拟。

## 验证与预览

```powershell
python tools/test_industrial_planning.py
python tools/test_factory_layout.py
python tools/generate_industrial_planning.py --check
python tools/preview_industrial_planning.py
python tools/preview_industrial_planning.py --idle
python tools/preview_industrial_planning.py --help-page
python tools/preview_industrial_planning.py --finished
python tools/validate.py --group industry
```

检查实际生成脚本，而不是仅检查源代码含某段字符串。网络用独立优先队列算法比较 80 组图；60 组配方输入检查物资/电力守恒；完整 1800 天合法扩建案例不注入资金，交付约664.7机械。生命周期覆盖隐藏页面、关闭窗口、重复开始/初始化、AI/他国、保存数据、期满及退款。

执行相关 RHoiScribe 文件与项目检查及 `repair_hoi4_project(dry_run=true)`，区分上游自定义效果索引误报；不应用全项目通用格式修复。最后做独立生成复现、BOM/重复键和 Git 空白检查。运行时仍由用户新开局验证，不自动启动游戏；本任务不构建上传目录。
