# 新版顾问分类与俄罗斯派系

2026-10-31：正式适配版和测试版分别生成，不互相复制人物或数值文件。

## 来源与实现

- 原生参照：钢四 `interface/command_character_view.gui` 的 `command_character_view_filter_button`、`interface/ideas.gfx`、`localisation/simp_chinese/politics_l_simp_chinese.yml`。
- 当前 KR `1521695605/interface/command_character_view.gui` 保留了 `filter_grid`，却缺少上述模板。独立 `RUS_advisor_category_filter.gui` 补模板；GFX 别名引用原生按钮纹理，绕开正式版旧 `ideas.gfx` 的同路径覆盖。
- 主窗口从当前 KR 逐块生成，只把列表起点98→143、分类栏高50→95、每排8→10按钮；其余卡片、名字、肖像、任命按钮均保留。
- 原版18帧类别保持逐像素一致，追加19–27帧：俄共（布）、社革党、民粹派、最高纲领派、全俄劳联左/中/右、孟什维克、社民盟。图标为用户之前选定的九个完整图案，仅等比缩小和透明留白，无新生成。
- 使用已有派系身份特质的 `sprite` 接入原生类别。只修改本地特质的该字段；继承KR的特质放独立覆盖文件，不重复定义已有本地特质。原有身份特质的添加、移除、转派系逻辑不动；普通/简易/关系等级修正保持。通用工业、政治、军种分类保留，不把非社会主义顾问硬塞进这些派系。
- 英/俄/简中只添加 `ADVISOR_CATEGORY_19`–`27`，不替换原生1–18名称。

## 维护

`python tools/generate_advisor_categories.py --check` 默认只读，对照当前KR及本版特质检查；修改派系来源后运行 `--write`。只有 `--write --assets` 才重打包图集。独立模板按原生界面维护；如果KR已补模板，生成器会阻断，需先审查再撤除冗余兼容部分。

`python tools/test_advisor_categories.py` 检查源特质的所有非sprite字段、原18帧像素、两排几何范围和三语输出。素材源及SHA在 `tools/design/advisor_categories_20261031/`。图集1242×46、每帧46×46；前18帧来自KR，后9帧来自已有派系图案。

## 验证边界

静态校验不替代引擎实测。完全退出并重启游戏，加载对应开发loader，新局检查：顾问窗口图标与中文提示、点击/取消类别、派系改变后列表更新、已任命/未解锁顾问状态、普通与简易模式、非俄罗斯国家的原分类。尤其要实测新版引擎对追加19–27帧和多特质顾问的筛选行为。未新增脚本模拟筛选、每日钩子或任命限制。

本轮只更新两版开发源及既有开发loader版本标记为KR一致的1.19.4.*；不构建上传目录、不改其旧教育系统、不发布工坊。
