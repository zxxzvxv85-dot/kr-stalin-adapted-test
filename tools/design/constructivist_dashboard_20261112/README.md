# 构成主义国家建设界面

- 美术源：用户指定构成主义图，经内置 ImageGen 编辑。模型名称未由工具返回；完整提示词见 `prompt.txt`，尺寸和验证记录见 `asset_manifest.json`。
- `backplate.png` 是无字底图。游戏中文字与数值来自原生文本框和本地化，不能烘焙进图片。成品窗 504×620，底图 492×615。
- 运行时源：`tools/national_plan_dashboard.py`，由 `tools/generate_national_plan.py --write` 统一生成。仅挂接已有 `RUS_np_context` 的经济项目分类，不改变项目国策门槛、计分或奖励。
- 常驻六项：资源、冻结、日增、在建/名额、列车、计划干线等级。中央读取正式一五分数，启动前读取待计入分数；下方阶段格读取既有阶段。点击标题展开原有账目、组织效率和预备分数。
- 四块产业图案负责类型筛选，六个下方按钮负责地区筛选。两种筛选取交集；再次点击取消该维度，中央复位全部。保留独立账本管理决议，确保空筛选结果不会使整个分类消失。
- 动画改为单个有纹理的中央传动盘：内置 ImageGen 完整源图见 `motion_v2/rotor_source.png`，224×224运行贴图；原生 `spriteType.animation` 连续旋转，每圈24秒。有在建工程才旋转，无工程显示同款静止轮面。中央分数面与标牌保留在前景固定层，移除原五组简陋叠层动画。原生参考为游戏 `interface/nationalfocusview.gfx`、`frontendmainview.gfx` 及 `gfx/FX/sprite_animation.fxh` 的normal透明混合。
- 中央总览点击区三个状态完全透明，不再出现矩形悬浮或按下边框；点击与提示保留。`build_constructivist_dashboard.py --write` 只进行图像尺寸、透明遮罩及固定前景包装，不改绘生成源图。
- 成品预览：运行 `python -B tools/preview_constructivist_dashboard.py`，生成 `output/constructivist_dashboard_20261112/finished_native.png`、`animated_preview.gif` 与 `interactive.html`。预览数据仅为示例，不来自游戏存档。PNG/GIF使用已安装汉化字库；HTML为独立交互演示。
- 自动浏览器拒绝打开本地 file URL，未绕过。HTML交互仅以离线 Node DOM 模型检查；原生尺寸排版已目视检查，游戏内布局、点击即时刷新、动画播放仍需重启游戏实测。
- RHoi整项目legacy验证300秒超时；定向GUI/GFX/本地化检查通过，脚本GUI仅有已核对存在的刷新helper索引诊断。项目结构扫描通过，修复试运行无红项、未写入。
- 仅测试版开发目录；未同步上传目录、适配版或 Steam。

## 四区域运动部件（2026-11-12）

- `sectors_v3`保存内置ImageGen生成的空轨道补全、完整车厢、滚筒端面及农业轮；模型名未返回，完整逐图提示见prompts.json。只采用补全图中旧列车所在条带，其余背景沿用原画。
- `dashboard_sector_motion.py`按原生64帧序列打包运动：电线低亮流动，三个倾斜滚筒端面转动，完整列车沿透视轨道放大前进，农业轮旋转。列车不是重复方块，农业轮不是统一光圈。每区按当前地区在建数切换动／静；无新增事件或每日调度。
- 原生序列图宽均小于16384；只把部件所在局部区域打包，不将整屏复制64次。导出PNG总量约3.2MB（四条动画）；面板文字和中央点击区保持原样。HTML有独立四区状态，GIF以16fps的24秒完整周期展示（预览数据）。
- 原生图元与结构检查通过；脚本GUI仍只有既有刷新helper未索引诊断。生成源和运行36输出一致。动画实际加载、循环及工程开始／结束切换仍需用户重启钢四测试。

## 2026-11-13：四区仅保留图案

用户取消四区统计条。运行背景改用内置ImageGen修复后的no_plaques_v4/background.png；四块底条、箭头、统计文字和选中横线均移除。前景只保留中央分数面，透明产业图案仍可点击与显示原悬浮提示。顶部、底部按钮和中央启用显示条件保持。生成提示、尺寸和实际验证状态见对应prompt.txt及asset_manifest.json。
