# 构成主义国家建设界面

- 美术源：用户指定构成主义图，经内置 ImageGen 编辑。模型名称未由工具返回；完整提示词见 `prompt.txt`，尺寸和验证记录见 `asset_manifest.json`。
- `backplate.png` 是无字底图。游戏中文字与数值来自原生文本框和本地化，不能烘焙进图片。成品窗 504×620，底图 492×615。
- 运行时源：`tools/national_plan_dashboard.py`，由 `tools/generate_national_plan.py --write` 统一生成。仅挂接已有 `RUS_np_context` 的经济项目分类，不改变项目国策门槛、计分或奖励。
- 常驻六项：资源、冻结、日增、在建/名额、列车、计划干线等级。中央读取正式一五分数，启动前读取待计入分数；下方阶段格读取既有阶段。点击标题展开原有账目、组织效率和预备分数。
- 四块产业图案负责类型筛选，六个下方按钮负责地区筛选。两种筛选取交集；再次点击取消该维度，中央复位全部。保留独立账本管理决议，确保空筛选结果不会使整个分类消失。
- 动画参照本机 `3011069378/interface/tht_sov_ui.gfx` 的原生 `frameAnimatedSpriteType`。五张24帧序列，8fps。中心有工程即转动，四个区域按所选地区的在建数显示电网、炉口、运输与旋轮动效。动画不驱动工程结算，无额外每日钩子；统计附加在原刷新接口。
- 动态环、脉冲和运输标记为代码原生 UI 图形；ImageGen 底图原件保留。`build_constructivist_dashboard.py --write` 只导出底图尺寸和动画/交互图层。
- 成品预览：运行 `python -B tools/preview_constructivist_dashboard.py`，生成 `output/constructivist_dashboard_20261112/finished_native.png`、`animated_preview.gif` 与 `interactive.html`。预览数据仅为示例，不来自游戏存档。PNG/GIF使用已安装汉化字库；HTML为独立交互演示。
- 自动浏览器拒绝打开本地 file URL，未绕过。HTML交互仅以离线 Node DOM 模型检查；原生尺寸排版已目视检查，游戏内布局、点击即时刷新、动画播放仍需重启游戏实测。
- RHoi整项目legacy验证300秒超时；定向GUI/GFX/本地化检查通过，脚本GUI仅有已核对存在的刷新helper索引诊断。项目结构扫描通过，修复试运行无红项、未写入。
- 仅测试版开发目录；未同步上传目录、适配版或 Steam。
