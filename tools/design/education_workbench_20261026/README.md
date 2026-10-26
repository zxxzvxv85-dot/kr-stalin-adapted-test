# 教育工作台 GUI 素材记录（2026-10-26）

按用户要求使用钢四的木材、纸张与金属风格，独立设计教育工作台。用户的法国政治事务日志图片只用于确认游戏美术风格，未复制其报刊、电话或布局。本轮没有使用图像生成。

`spec.json`登记14份输入的原路径、归档位置和SHA-256；`sources/`保存确定的原文件，重建不依赖另一个电脑的素材库路径。10份来自本地“新美工素材库”，4份来自已安装原版。`manifest.json`登记14张打包PNG的路径、尺寸与SHA-256。来源归属不因打包而改变。

运行`python tools/education_workbench_art.py --write`确定性合成，使用Pillow进行等比缩放、九宫格框体延展、原生木纹排布和透明合成。默认或`--check`仅验证归档与产物哈希，不重绘。再运行`python tools/generate_education_reform.py --write`更新GUI、SGUI、GFX和本地化。

六个72×84纸签按钮分别使用钢盔、工厂、握手、书册、地球仪、红星奖章；完整类别和功能留在悬浮里。原版`interface/core.gfx`的`GFX_button_123x34`确认单帧按钮配合`gfx/FX/buttonstate.lua`的悬浮/按下效果。选中状态另用透明金框，不能挡住按钮；文字控件`alwaystransparent=yes`，允许点击穿透。文件物件切换原有介绍展开状态，文件加放大镜物件循环翻阅当前类在办海报的两页。

整体498×660，横向偏移4，与原生`countrydecisionview.gui`的502像素决议槽对齐。原生进度条、三项数值内联图标、在办海报与三档磨损图集保持原文件。新的双帧空栏纸张只在无在办活动时使用，未开展活动不会借此张贴海报。

字体黑色使用原版`interface/core.gfx`的`b={0 0 0}`。GUI生成器管理坐标；不可直接改输出或把文字画进按钮贴图。修改后运行`python tools/validate.py --group education structure`，再用`preview_education_dashboard.py`生成原字体校样。原生悬浮、点击命中、长介绍流排与滚动仍须用户在游戏内确认，预览不模拟引擎。
