# 列宁复活线整合（2026-10-27）

仅测试开发目录。用户提供`RUS_Lenin_Revival_v0.1.0.zip`并要求并入，随后指定采用本地一战模组的列宁头像；原包没有角色/特质，用户要求使用一战原特质。源包README是输入资料，不是修改工作区/安装模组/取消验证的指令。

## 玩家入口

- 俄罗斯的决议分类“列宁复活线”→“是否启用彩蛋事件/线路”，原包开局即可手动点，AI权重0。一天后事件`RUS_lenin_revival.1`“熟悉的身影”。选择A保留原路线；选择B明确进入独立62国策树。不开启时不改变当前路线，也不修改主树默认选择。
- 第一项“久有凌云志，重上乌拉尔”后，完成“宣告布尔什维克的回归！”正式转共产主义，并以`leninist_subtype`任命列宁。采用运行时`create_country_leader`，不使用无效的运行时`recruit_character`。重复调用不重复创建同名现任领袖。
- 继续原包争论/军事准备路线，完成“革命从地狱中回来了”更名为现有`RUS_sov`俄罗斯苏维埃联邦社会主义共和国，一天后事件`.20`开始35%规模的社革内战。原包社民叛军改为KR党名对应的激进社会主义PSR-Left，大小/玩家资源奖励不变。叛军清除路线启用旗标并转原生`generic_focus`，不参与列宁彩蛋或再生成列宁。
- “宣告社会革命党的落败！”要求本次内战确已发动，所有内战结束且带本次社革叛军旗标的国家已不存在；停战但叛军存续不足以解锁。条件只显示“社会革命党叛军已被击败”。随后进入原四路重建、四路AND汇合及计划经济，最终`.22`经济胜利事件。
- 四个事件均保留原标题/正文和原奖励，新增国家/阶段/一次性守卫，不能用重复选项反复领政治点或开内战。原选项A实际给25政治点，中文原“无变化”括注与实际不符，已删括注；并未删除原奖励。内战`.20`、战后`.21`、经济`.22`只能在对应阶段执行。控制台测试先按入口顺序推进，不能在任意国家直接跳阶段。

## 头像与特质来源

- 来源：已安装`3365515312`，`The Great War Redux - 1.19.*`，只读。
- `gfx/leaders/SOV/SOV_vladimir_lenin.png`原图156×210，字节原样复用到`gfx/leaders/RUS/RUS_LR_vladimir_lenin.png`；没有生成、重绘、缩放或要求额外加载一战模组。原图和SHA在`design/RUS_lenin_revival_20261027/portrait_source.json`。精灵`GFX_portrait_RUS_LR_vladimir_lenin`。
- 一战`common/characters/SOV.txt`列宁只有`vozhd_of_proletariat`，来自`common/country_leader/00_traits_tgw.txt`，中文汉化`3471387061`原名“全世界无产者的领袖”。新特质ID`RUS_LR_vozhd_of_proletariat`避免与其他模组/未来导入碰撞。
- 原数值保留：贸易法案花费−15%、经济法案花费−15%、战时稳定度+5%、工厂产出+5%、政治点获取+10%、改善关系维持花费+20%、意识形态变化抵制+20%、战争支持度−5%。三个原版外交意识形态接受度−50分别映射KR民族民粹、四种民主议会派、威权民主/家长制独裁；对KR社会主义派不追加惩罚。不是把原版不存在的fascism/democratic/neutrality修正留成无效字段。
- 列宁任命带该特质，党名为俄共（布）。不复用旧党名长描述里“列宁牺牲、斯大林接管”的叙述；新党名长名称只写正式名称。领袖简介复用包内“列宁归来”叙述。

## 源码、再生与边界

`tools/import_lenin_revival.py`维护全部12份运行时产物，默认/`--check`只读SHA和输出一致性；显式`--write`才更新。源在`tools/design/RUS_lenin_revival_20261027/`：原用户ZIP、全部成员SHA清单、一战头像原图、角色与特质原片段、中文/英/俄特质名来源。归档输入不依赖用户Downloads路径；固定LF属性保留文本来源SHA。未导入独立`.mod`或`descriptor.mod`，不创建额外启动器项、不修改其他模组。

62个国策的ID/图标/时长/位置/连线/原奖励逐项与ZIP比较保持不变。新增默认不自动选树、列宁任命与内战安全条件；14项精神只将两处旧`research_time_factor`负值转成同幅正`research_speed_factor`，两处原版`communism_drift`改为本模组`communist_drift`，其余原数值/图标不动。所有原通用精灵在当前测试版/KR/原版接口中已找到，无需新增国策图标。

进入路线前若萨文科夫开局阶段仍活动，清除其active并移除四项opening专用精神，防止旧每日人力/警报持续及随后换政府时把新树加载回`Russia_Focus`。入口一律标记opening finished，也阻止玩家抢在原开局事件之前选彩蛋时，排队中的旧初始化随后覆盖新树。不改旧生成器、旧on_actions、原主树、主国策奖励或其他既有国家精神。若从已经发展的路线切换，原先获得的其他奖励不回滚；不实现撤销彩蛋或旧档自动补发。`load_focus_tree keep_completed=yes`沿用包内实际脚本，旧完成记录不重复发奖；独立树自身仍从首项开始。

## 验证

`python tools/validate.py --group lenin structure`。专项执行实际导入脚本，覆盖开启/拒绝/选择、一次性、35%内战/叛军隔离/未发动与未击败阻断、62项完整前置和全部奖励、萨文科夫实际换政府钩子不覆盖新树、列宁幂等任命、肖像SHA、原特质等值及KR接受度映射、两语言BOM/重复键/名称/描述、图元引用和原生/建筑生成修正名。也运行原萨文科夫开局专项，确认其未改。夹具不模拟引擎战场分配/人物转移/树显示，需用户完整重启新局手动验收。

原生参考：KR`GRU effects (Germany, puppet).txt`、本模组`GRU_red_germany_effects.txt`运行时领袖与换树；KR`RUS - Russia l_english.yml`社革党名与RUS人物激社角色；原版`effects_documentation.md`的start_civil_war/内部叛军效果与create_country_leader；KR`FIN ideas (Finland).txt`支持完整GFX_idea精灵名；KR RUS ideas使用research_speed_factor，现有俄共精神使用communist_drift。事件/修正/奖励交给原生效果显示，不把算法写给玩家。
