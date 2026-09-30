# 国家农业独立窗口

2026-09-26 起，国家农业经营从决议分类迁至独立窗口。国家农业解锁且未永久关闭时，俄罗斯玩家可通过地图右下方农业按钮打开；按钮使用 KR 中欧同盟的 `raid_filter` 挂接位置，贴齐右侧功能按钮列，位于袭击筛选标题上方并留出 6 像素间距。中欧同盟入口同时显示时，农业入口改放其上方；两个互斥入口复用相同开关效果，不保存额外位置变量。窗口居中、可拖动，右上角或 Esc 关闭，不暂停季度经营、不取消订单。

## 内容及状态

- 左侧保留农业生产、农机生产、库存与贸易、季度报告四页，以及国内／国外订单浏览。
- 右侧季度援助包含原六项支援；农业建设包含原七项国内项目。经营指南和关闭系统也在窗口内，共 15 项原农业分类操作。
- 土改分数严格大于 200 才显示永久关闭系统按钮。它沿用原关闭效果，包括工厂释放、停止日常和季度逻辑、保留既有改革成果。
- 三项面向外国的农业援助仍属“输出革命”外交内容，由原外交目标及资格管理；它们不是国家农业分类中的国内经营项目。
- `RUS_nat_window_open` 只控制窗口显示；`RUS_nat_admin_page` 只控制右侧页签，0 为季度援助，1 为农业建设。左侧沿用 `RUS_nat_page`。这些状态不参与产量、成本、评分和奖励。
- 可见性共用 `RUS_nat_window_available`，要求俄罗斯原始标签、玩家、已解锁及启用国家农业、系统未关闭。国家变为 AI 或不符合条件时窗口与入口隐藏。

## 生成来源

统一入口：

```powershell
node tools/generate_national_agriculture.cjs --check
node tools/generate_national_agriculture.cjs --write
```

`build_agriculture_card_gui.py` 先生成原有卡片文本，再调用纯函数 `agriculture_standalone_window.render_window` 包装窗口、追加右侧操作和快捷入口，随后由订单浏览器生成阶段继续完善订单页。普通生成不重画素材。

独立窗口读取以下三个文件中首个农业分类的操作定义，直接复用 `visible`、`available`、`cost`、`custom_cost_trigger`、`complete_effect`，不另抄一套平衡数值：

- `common/decisions/RUS_national_agriculture_decisions.txt`
- `common/decisions/RUS_agri_development_decisions.txt`
- `common/decisions/RUS_national_agriculture_shutdown_decision.txt`

这些定义保留为维护源，原农业决议分类隐藏。新增操作时必须同步审查按钮布局及数量；生成器遇到尚未支持的原生决议计时器会失败，不能悄悄省略计时逻辑。

按钮用 `[!按钮名_click_enabled]` 展示可行动条件，用 `[!按钮名_click]` 展示原生效果。政治点费用由 GUI 显式扣除一次；真正执行置于 `hidden_effect` 内，并再次检查资格、余额及原有冷却。`effect_tooltip` 仅展示，不额外执行奖励。积分支出及奖励仍由原 `complete_effect` 结算，简易模式也沿用原分支。

主要运行文件为 `interface/RUS_national_agriculture.gui`、`common/scripted_guis/RUS_national_agriculture.txt`，以及对应的 `*_launcher.gui/txt`、`*_window_effects.txt`、`*_window_triggers.txt`。窗口新增文本在三语 `RUS_agriculture_window_l_*.yml` 中；通过生成器维护 UTF-8 BOM。

参考已安装 KR 的 `common/scripted_guis/germany_mitteleuropa.txt`、`interface/kaiserreich/gui_mitteleuropa.gui` 和 `common/scripted_effects/MIT effects (Mitteleuropa).txt`。窗口背景、按钮、关闭图标使用 KR／原版现有精灵，不替换全局界面资源。

## 拆军工与农机产线

“拆1军工”位于农机页底部，停产与全部产能按钮之间。拆除本国拥有并控制的地图内军工后，永久增加 1 条专用产线，并通过原有分配效果立即投入；新线仍按 30% 效率加权并入。终身上限 5 条，不从地图外工厂或失去控制的地区取得免费额度。

`RUS_nat_factories` 是当前投入的总产线，`RUS_nat_base_civilian_factories` 是拆军工获得的永久专用额度。`RUS_nat_civilian_use = max(总产线 - 专用额度, 0)` 才是动态修正实际占用的普通民工；用 `RUS_nat_reserve_factories` 统一重算并刷新。可增派量只加上尚未投入的专用额度，不能重复提供已经开工的产线。

停产将总产线和民工占用归零，但保留永久额度；“全部产能”可以重新投入。此前已经记入的拆除额度同样经正常分配使用，无需再次拆厂。日产量、效率增长、库存上限、国内补机顺序和累计自产规则沿用原算法，不另发一次性农机奖励。系统永久关闭时同时清空实际占用变量。

## 验证与预览

```powershell
python -B tools/validate.py --group agriculture interface
python -B tools/preview_agriculture_window.py --admin-page 0 --card-page 1
python -B tools/preview_agriculture_window.py --admin-page 1 --card-page 3
```

预览读取实际 GUI 位置和原生纹理，以一份已完成土改的模拟状态展示窗口，保存在 `output/national-agriculture/`。它不模拟游戏的字体描边、悬停及原生容器行为，不能充当实机截图。

游戏内抽查由用户执行：

1. 农业未解锁时无入口；解锁后不打开决议栏即可打开窗口。检查与中欧同盟按钮、不同分辨率及 UI 缩放的相对位置。
2. 四页、右侧两个页签及订单滚动正常；拖动窗口后文字、图标和点击区域一起移动。
3. 支援费用和每季四次上限、建设积分和项目上限正确；反复点击不能重复发奖。普通／简易模式均抽查一次。
4. 关闭再打开后方案、库存、订单、报告和所选页保留；季度切换仍正常结算和提醒。
5. 土改分数 200 时无关闭按钮，超过 200 后可永久关闭；执行后入口消失，已占用工厂释放，后续不再季度操作。

以上运行时项目不由静态检查替代；本次迁移未增加旧存档专用修复逻辑。

拆军工回归由 `test_agriculture_factory_conversion.cjs` 执行真实 GUI 动作与生产脚本，覆盖零空闲民工、普通／简易状态、5 次上限、真实建筑扣除、专用／普通产能混用、损失民工、停产／恢复、仓库已满和已有转换额度。夹具只建模这些场景涉及的建筑及占用行为，不模拟引擎的状态选择动画或完整工业系统。
