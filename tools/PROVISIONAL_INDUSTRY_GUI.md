# 临时政府工业GUI

本模块是既有工业决议的可视化入口，只开发第一阶段。上传目录不包含本轮改动；旧debug沙盘继续保留。

## 入口与范围

人类俄罗斯进入社会主义/共产主义政府且斯大林尚未执政时，在决议“工业项目”分类显示。新增“显示全部工业工程”是无费用UI复位，确保当前分类无已解锁项目时仍可切回。点场景设施只写RUS_rc_filter，不支付费用或授予奖励。实际工程依旧使用原生决议列表、原解锁条件及费用；“为发展奠基”“国民经济普查”等禁选预览国策没有被开放。

- 文件：黑色星期一恢复项目（从实际调用RUS_decrease_black_monday分类）。
- 厂房：非道路/铁路的工业、能源和资源项目。
- 蒸汽机车：北方路线、三段铁路扩建及中亚铁路。
- 吊车：中央、北方及伏尔加道路。
- 计时任务不参加筛选。阶段之外所有筛选旁路，不改变AI或其他政府的可见规则。

第二阶段由RUS_rc_stalin_phase识别RUS_stalin_ml_promoted旗标或斯大林现任领袖；本阶段GUI关闭，原生决议继续使用。第二阶段画面与新机制尚未开发。根窗口隐藏后实际决议类别高度仍需游戏验收。

## 来源与生成

文本来源`generate_provisional_industry_gui.py`，默认检查，`--write`写入。共享决议/分类文件只维护标记UI块；未来其他生成器改写共享文件后应再执行本生成器。所有原奖励/条件由原模块维护，不在此复制。

美术来源是本地新美工素材库中的Factories5、火车、Crane、Documents_and_Papers、Railroad与原版斯柯达框；原素材组合后使用内置image_gen生成衔接，再单独修正机车。完整提示词及文件来源在`design/provisional_industry_20261030/provenance.json`。先前用户否定的纯生成风格和散排方案不用于游戏。

源图1401×1123，底图492×394，窗口504×426。`prepare_provisional_industry_assets.py --write`只进行游戏打包：等比例近似缩至底图、按多边形生成四张原像素透明贴图；默认只验保存的SHA，不生成图像。`transparencecheck=yes`沿原生GFX写法，`buttonstate.lua`提供悬浮反馈。后续换图必须重查四个区域和MASKS，不能只覆盖底图。原尺寸排版预览是本地绘制，不是游戏截图。

## 检查

```powershell
python tools/generate_provisional_industry_gui.py --check
python tools/prepare_provisional_industry_assets.py
python tools/test_provisional_industry_gui.py
python tools/check_runtime_structure.py
```

运行时需重启验证：临时政府出现面板；四处设施正确响应；筛选无项目仍能复位；工程原费用/时长及效果；斯大林上台后筛选失效、面板关闭且原决议仍显示。静态检查不能验证引擎里的点击命中和动态排版。
