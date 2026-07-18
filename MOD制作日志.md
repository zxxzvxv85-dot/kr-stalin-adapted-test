# [KR] 多么幼稚的幻想，但是斯大林——制作日志与开发备忘

最后更新：2026-07-16

## 1. 文档用途

本文件用于长期记录本模组的设计决定、实际实现位置、资源来源、已知问题和验证方法。以后新增机制或美术时应继续追加，不要只记录“改了什么”，还要记录“为什么这样改”和“如何验证”。

状态标记：

- **已实现**：脚本与资源已经写入适配版和测试版。
- **待实测**：静态检查通过，但仍需在完整重启后的游戏中验证。
- **规划中**：仅完成方案研究，尚未写入脚本。

## 2. 工作目录与同步规则

| 用途 | 路径 | 说明 |
| --- | --- | --- |
| 适配版（主开发版） | `D:\steam\steamapps\workshop\content\394360\kr_stalin_adapted_local` | 日常修改的权威版本 |
| 测试版 | `D:\steam\steamapps\workshop\content\394360\kr_stalin_adapted_test` | 每次完成修改后同步 |
| 原始订阅模组 | `D:\steam\steamapps\workshop\content\394360\3723313895` | `Stalin Returns - A Kaiserreich Submod`，只作为上游参考，不直接开发 |
| Kaiserreich | `D:\steam\steamapps\workshop\content\394360\1521695605` | KR 原版脚本、美术与本地化参考 |
| 霜泽美术馆 | `D:\steam\steamapps\workshop\content\394360\3473772709` | 美术教程、PSD、国策图标与免抠素材 |
| 秋起图书馆 | `D:\steam\steamapps\workshop\content\394360\3445449478` | 钢四代码、GUI、工具与资料参考 |

同步原则：

1. 先修改适配版，再将对应文件同步到测试版。
2. 不覆盖两版之间有意保留的 descriptor、版本号或发布信息差异。
3. 完成后比较对应文件 SHA-256；应一致的机制文件必须哈希一致。
4. Steam 订阅目录可能自动更新，不能把唯一开发成果只放在订阅模组目录中。

## 3. 当前已实现内容

### 3.1 季诺维也夫与权力平衡

状态：**已实现**

设计决定：取消季诺维也夫对权力平衡的影响，包括他作为二把手以及作为国家领导人时的影响。以后修改社会主义政治机制时，不应重新添加以季诺维也夫身份为条件的周期性权力平衡推动。

相关政治文本仍可保留季诺维也夫作为剧情人物的作用；取消的是数值上的权力平衡影响，而不是删除其历史与剧情地位。

### 3.2 克利缅特·伏罗希洛夫

状态：**已实现**

解锁条件：完成国策 `RUS_rehabilitate_red_army`（平反红军）。

将领设定：

- 身份：陆军元帅。
- 等级：4。
- 攻击 / 防御 / 计划 / 后勤：`3 / 5 / 4 / 6`。
- 特质：`old_guard`、`inflexible_strategist`、`politically_connected`。

陆军部长设定：

- 职位：`army_chief`。
- 特质：`KR_army_breakthrough_2`，即与邓尼金相同的“陆军突破（大师）”。
- 花费：50 政治点数。

头像规则：

- 将领大头像保持彩色。
- 陆军部长 / 小头像使用 KR 风格黑白版本。
- 用户要求仅进行黑白处理，不额外裁切或改变构图。

主要文件：

- `common/characters/zzz_RUS_kliment_voroshilov.txt`
- `common/national_focus/RUS focus (Russia).txt`
- `common/on_actions/on_actions_Russia.txt`
- `localisation/simp_chinese/RUS_stalin_voroshilov_l_simp_chinese.yml`
- 对应的 `interface` / `gfx` 头像注册与图片文件

老存档兼容：每日检查已经完成“平反红军”但尚未拥有伏罗希洛夫的国家，并补充招募该角色。

### 3.3 曼施坦因事件音乐

状态：**已实现，待完整重启后实测**

目标：点击曼施坦因政变事件 `russia_events.926` 的按钮后播放《Эх, яблочко》。

当前调用：

```hoi4
play_song = "RUS_manstein_yablochko"
```

音乐注册必须同时具备三部分：

1. `music/rus_manstein_yablochko.ogg`
2. `music/zzz_stalin_manstein_yablochko.asset`
3. `music/zzz_stalin_manstein_yablochko.txt`，将歌曲加入 `base_music`，随机播放概率为 0

资源名必须统一为 `RUS_manstein_yablochko`。仅有 OGG 和 `.asset` 而缺少音乐台 `.txt` 时，事件调用可能无声。

当前 OGG 与用户提供的源文件 SHA-256 一致：

`E7AB3C9E1D2B8F450E8DB73481C2A40DC16B599B047CBEA742EAF29EE584BE05`

### 3.4 联邦计划委员会

状态：**已实现**

来源：仿照原版捷克斯柯达优先事项机制，仅移植生产优先级核心，不移植武器出口办公室。

解锁：社会主义俄罗斯成立后自动启用。老存档满足社会主义政府及 `RUS_socrus_happened` 条件时，由周期检查补发。

五种生产优先事项：

1. 重工业计划
2. 步兵装备计划
3. 装甲车辆计划
4. 航空工业计划
5. 海军工业计划

优化规则：

- 初始优化等级：2。
- 最大优化等级：4。
- 切换生产优先事项：优化等级重置为 1。
- 保持同一优先事项：随周期逐步恢复优化等级。
- 完整包含五类重心的分级民族精神和原版斯柯达核心加成。

当前国策树窗口坐标：

```hoi4
position = { x = 400 y = 30 }
```

坐标规则：

- `inlay_window position` 使用国策画布坐标，不是普通国策格坐标。
- X 增大向右，Y 增大向下。
- `y = 0` 的实测结果是窗口可能完全消失或被边界裁切，应保留正数 Y。
- 普通国策的 `x / y / relative_position_id` 不能直接换算为内嵌窗口坐标。

主要文件：

- `common/focus_inlay_windows/RUS_federal_planning_commission_inlay_window.txt`
- `common/ideas/RUS_federal_planning_commission_ideas.txt`
- `common/scripted_effects/RUS_federal_planning_commission_effects.txt`
- `common/scripted_localisation/RUS_federal_planning_commission_scripted_localisation.txt`
- `common/scripted_triggers/RUS_federal_planning_commission_triggers.txt`
- `common/national_focus/RUS focus (Russia).txt`
- `common/on_actions/on_actions_Russia.txt`
- `interface/RUS_federal_planning_commission.gui`
- `interface/RUS_federal_planning_commission.gfx`
- `gfx/interface/rus_fpc/`
- `localisation/*/RUS_federal_planning_commission_l_*.yml`

已经解决的问题：

- 中文、俄文及 `§ / £` 控制字符曾被写成字面量 `?`，现已重建中、英、俄本地化。
- 本地化文件必须使用 UTF-8 BOM。
- `£GFX_prod_eff_cap` 是图标控制符；`§Y...§!` 等是颜色控制符，不能用普通问号替代。
- 原版空行键 `generic_skip_one_line_tt` 在当前组合中未加载，曾直接显示为代码。现改用自有键 `RUS_fpc_skip_one_line_tt: " \n"`。

## 4. 美术规范与资源索引

### 4.1 当前项目美术规范

- KR 部长 / 顾问头像：黑白处理，保持原构图，除非另有要求不重新裁切。
- 将领头像：保持彩色。
- KR 报告事件图：使用高分辨率倾斜卡片、柔和阴影、轻微边缘高光和最终缩小的处理流程。
- 国策与民族精神图标：优先使用原版 / KR 的浮雕、金属、花环和暗色绘制风格。
- 不直接套用 TFR 的霓虹电子风、TNO 的电子界面风或赤潮的超事件风格。

### 4.2 霜泽美术馆评估

目录：`D:\steam\steamapps\workshop\content\394360\3473772709`

规模：约 274 个文件、3.69 GiB。它是跨模组教程和素材库，并非 KR 专用美术包。

最有价值的资源：

- `通用-素材合集/国策图标制作素材.zip`
  - 约 746 个条目。
  - 包含共产主义花环、齿轮、武器、旗帜、盾牌、国策框、人物背景和大量 PSD / PNG。
  - 对社会主义俄罗斯国策图标、民族精神和 MIO 图标价值最高。
- `其他/原版图标处理教程.png`
- `其他/原版浮雕风制作.mp4`
- `通用-素材合集/图标素材合集/素材合集（一）.png`
- `通用-素材合集/纹理及背景素材/`
- 天空、烟雾、火焰、光效、地图等通用素材
- `TFR/教程-文档类/事件图流水线教程 by薄荷QWQ.docx`，只借鉴处理思路，不直接套用 TFR 成品样式

中等价值：

- TNO / TFR 人像修复、抠图、调色教程，可用于基础处理。
- TFR 事件 PSD 与加载图可参考图层组织和构图。

低价值或不宜直接使用：

- TFR、TNO、赤潮的完整 UI 和成品模板与 KR 视觉语言不一致。
- 来源不明的 EXE 工具不应未经检查直接运行。

版权注意：README 写有“欢迎各位使用”，但没有正式许可证；包内包含其他作者、其他模组和第三方来源素材。私人开发和测试可以参考，公开发布时应记录来源、补充署名，并避免整包原样转载。

### 4.3 秋起图书馆

目录：`D:\steam\steamapps\workshop\content\394360\3445449478`

主要价值在代码、GUI、工具和教程，不是美术成品库。以后进行自定义 GUI、国策界面或复杂机制时可优先检索此目录。

## 5. MIO 军工机构扩展方案

状态：**规划中，尚未指定具体 MIO 与国策**

国策可以在游戏途中永久强化 MIO。

直接改变基础属性示例：

```hoi4
completion_reward = {
	mio:RUS_example_organization = {
		add_mio_research_bonus = 0.05
		add_mio_funds_gain_factor = 0.20
		add_mio_task_capacity = 1
	}
}
```

适用于研究加成、资金获取、任务容量、升级需求和生产线指派花费等基础数值。

若要追加攻击、防御、突破、可靠性、生产花费或资源消耗等具体装备效果，应在对应 MIO 定义中添加专属 `add_trait`，再由国策完成：

```hoi4
mio:RUS_example_organization = {
	complete_mio_trait = RUS_mio_trait_new_effect
}
```

注意：`complete_mio_trait` 会直接完成特质，并自动增加 1 级 MIO 规模。若只想让玩家日后自行购买，应通过特质的 `available` 条件绑定国策，并只显示解锁提示。

老存档规则：

- 国策尚未完成：之后完成时正常获得奖励。
- 国策在更新前已经完成：`completion_reward` 不会重跑，需要 on_action、事件或决议做一次性补发，并设置防重复标记。

## 6. 技术备忘

### 6.1 本地化

- HOI4 `.yml` 使用 UTF-8 BOM。
- 修改后检查前三个字节必须是 `EF BB BF`。
- 不要用会把中文、俄文、`§` 或 `£` 转成问号的写入方式。
- 动态变量 `[?RUS_variable]` 中的问号是合法语法，不能误删。
- 自定义本地化键尽量使用 `RUS_` 前缀，避免依赖可能被 KR `replace_path` 隔离的原版通用键。

### 6.2 音乐

- 事件音乐至少检查 OGG、`.asset`、音乐台 `.txt` 和事件调用名四处是否一致。
- 事件要求“点击按钮后立即播放”时优先用 `play_song`。
- `chance = { base = 0 }` 可防止专用剧情曲随机进入普通播放列表。
- 新增音乐后必须完全重启游戏，普通读档不能重新加载音频资产定义。

### 6.3 国策树内嵌窗口

- `inlay_window position` 与普通国策格坐标是两套系统。
- 每次调整后必须在目标国策树、常用缩放倍率和实际分辨率下截图验证。
- 不应仅根据普通国策的 `x/y` 推算内嵌窗口位置。

### 6.4 老存档兼容

任何国策奖励新增内容都要问两个问题：

1. 新存档完成国策时是否能正常获得？
2. 老存档已经完成该国策时是否有补发机制？

补发必须有明确条件和防重复标记，避免每日重复添加人物、民族精神、变量或 MIO 特质。

## 7. 每次修改后的验证清单

脚本检查：

- 大括号数量相等。
- 引号成对。
- 新 token 在定义、调用和本地化中拼写一致。
- 没有意外残留 `generic_skip_one_line_tt`、`GFX_...` 或未本地化代码。

资源检查：

- 图片路径、GFX sprite 名、实际文件名一致。
- 音乐 OGG、asset、station txt 和事件调用一致。
- 中文与特殊字符未损坏。

双版本检查：

- 适配版与测试版对应文件 SHA-256 一致。
- 两版文件数量和新增资源一致。

游戏内检查：

- 完全重启游戏，而不只是返回主菜单。
- 新存档验证触发流程。
- 老存档验证补发与防重复。
- 查看 `Documents/Paradox Interactive/Hearts of Iron IV/logs/error.log`。
- UI 修改必须截图确认位置、遮挡、文本、图标与不同缩放倍率。

## 8. 当前待办与待实测

- 完整重启后重新触发曼施坦因事件，确认《Эх, яблочко》立即播放。
- 在 `(400,30)` 坐标下再次确认联邦计划委员会不遮挡国策且不被顶部裁切。
- 以后确定具体 MIO、对应国策和追加数值后，实现国策强化军工机构。
- 公开发布使用霜泽美术馆素材前，逐项确认来源与署名要求。

## 9. 更新记录

### 2026-07-17

- 根据实机 `error.log` 的 `recruit_character: Unknown character RUS_kliment_voroshilov`，确认独立的 `zzz_RUS_kliment_voroshilov.txt` 没有进入启动时角色数据库。现将完整角色定义并入确定会加载的 `common/characters/RUS characters.txt`，删除独立文件；国策奖励与每日老存档补发继续使用 `recruit_character`。该修复必须完全退出并重启 HOI4 后才会生效，随后旧存档推进一天即可触发补发。
- 再次实机验证发现，每日补发会执行但旧战役持续报告 `Unknown character`；将角色主文件放进最终兼容层后错误仍存在，证明根因并非 More Custom AI 的文件覆盖，而是旧存档在战役建立时已经固化角色数据库，后加的预定义角色无法用 `recruit_character` 注入。现撤销兼容层的整份角色文件，改用运行时 `generate_character` 动态生成伏罗希洛夫，使新档、旧档以及 More Custom AI 组合均走同一条可执行流程；动态角色同时包含等级 4、`3/5/4/6` 的陆军元帅身份和“陆军突破（大师）”陆军部长身份。

### 2026-07-18

- 为 `KR Tech Extension`、`Unoffical KRTX Patch Reupload` 与其简体中文包制作直接兼容：三个模组均声明依赖 Local Loader 并更新为 `1.19.*`；两个代码版的 `antitank3` 新增通向 `sp_advance_sabot_shells` 的支线，解决科技拓展界面中的 `Found no grid box`；从 `artillery5`、`antiair5`、`antitank5` 删除提前解锁 `auto_loader`；新增末尾模块覆盖，保留 KRTX 的 `tank_special_module_stabilizer` 类别及稳定器 1–4 级升级链，同时应用本模组的稳定器与自动装弹机属性。并移除本模组三个合并版 `artillery.txt` 中重复的 `sp_advance_sabot_shells` 定义，使独立兼容科技文件成为唯一科技定义来源。
- 从 KRTX 移植现代高速加农炮与现代重型加农炮为本模组独立模块，避免被上游同名 ID 覆盖。现代高速加农炮设为软攻 `45`、硬攻 `60`，现代重型加农炮设为软攻 `50`、硬攻 `55`，其余穿深、突破、造价、速度、可靠性和资源消耗沿用 KRTX 补丁版。研究 `main_battle_tank_chassis` 后由隐藏兼容科技解锁；模块使用专属 `RUS_modern_main_armament` 类别，只有 KRTX 的现代坦克炮塔、现代固定战斗室及后续现代炮塔接受该类别，因此无法安装在早期底盘上。图标素材复制进适配版与测试版，旧存档在每日刷新时补发解锁。

### 2026-07-16

- 将适配版、测试版、Local Loader 与 `[KR] Stalin Adapted - More Custom AI Compat` 更新至游戏版本 `1.19.2`（支持 `1.19.*`）。
- 完成适配版与 More Custom AI 的双模组冲突审计：实际同路径冲突仅有俄罗斯国策与俄罗斯事件两个文件；More Custom AI 的 `replace_path` 不覆盖本模组新增脚本目录。
- 以当前适配版为权威基底重建兼容补丁，仅保留 More Custom AI 的法俄条约玩家提示、英国好感判定和既有博尔德列夫调整；联邦计划委员会、伏罗希洛夫、曼施坦因音乐及社会主义俄罗斯新增内容均保留。
- 修复 `on_actions_Russia.txt` 的 `InitPostRead failed`：删除每日动作中重复动态创建弗伦泽理论家顾问角色的旧补丁，避免每日动作整体初始化失败。
- 修复曼施坦因 `unit_leader_event` 的作用域：由 `FROM`（俄罗斯国家）提交白军反抗小游戏启动请求；删除小游戏内重复完成 `RUS_red_flag_over_kremlin` 的逻辑，避免事件及国策重复执行。
- 实机日志确认人物事件中的直接 `country_event` 仍会被旧存档吞掉；现改为按钮写入一次性待处理国家旗标，再由 `on_daily_RUS` 的国家作用域可靠启动。对已经点击过曼施坦因按钮、但小游戏尚未开始的老存档，使用 `RUS_socrus_happened` 自动补发一次，并以 `RUS_white_revolt_start_dispatched` 防重。
- 为“纠正历史进程”增加新旧存档兼容检查：社会主义且独立的俄罗斯若已完成 `RUS_russian_congress`、但未完成外交线首个国策 `RUS_self_determination`，下一次每日刷新会自动补完并刷新国策树布局。
- 实机确认 More Custom AI 的旧曼施坦因选项与白军小游戏胜利结算分别执行了一次 `RUS_initialise_socrus`，造成社会主义事件链重复。兼容补丁依赖名已改为实际启用的 Local Loader 与 More Custom AI 名称，并在小游戏结算加入 `RUS_white_army_red_baron` 防重复检测。
- 曼施坦因歌曲调用改用 KR 现行的 `scoped_play_song`，启动请求改用人物作用域可可靠设置的全局待处理旗标。
- 按事件原设计，将 `RUS_red_flag_over_kremlin` 的自动完成放在“白军拒绝缴械”开场事件按钮中，并使用 `has_completed_focus` 防重复；已经点击开场事件但缺失该国策的存档，会在小游戏进行中或结束后的下一次每日刷新补发。
- 实机确认尚未加入国家的预定义角色不能通过人物作用域 `set_nationality` 招募。伏罗希洛夫的国策奖励与老存档补发、以及斯大林的缺失角色补发均恢复为 `recruit_character`；现有存档完成“平反红军”后会在下一次每日刷新补入伏罗希洛夫。
- 修正自动装弹机科技来源：从 KR 与 More Custom AI 的 `artillery5`、`antiair5`、`antitank5` 中删除旧解锁，并移除自定义文件中无效的重复科技定义。现在 `auto_loader` 只由 `sp_advance_sabot_shells`（先进脱壳穿甲弹）或对应老存档兼容科技解锁，OF-63 等科技的自动生成说明也不再显示自动装弹机。
- 完成 1.19 语法适配：`add_army_experience` 改为 `army_experience`，决议 `cancel_if` 改为 `cancel_trigger`，修正季诺维也夫议程的欧洲国家判定，并为高级炮兵科技补齐文件变量。
- 曾尝试将斯大林与伏罗希洛夫的老存档补发改为人物作用域 `set_nationality`，但实机确认未招募角色无法用该效果加入国家，现已撤销并恢复为国家作用域 `recruit_character`。
- 新增 `RUS_stalin_purge_white_generals_safe`，替换 KR 已失效的 `PREV.PREV` 白军将领清洗作用域，停止 `error.log` 大量重复报错。
- 静态校验确认：关键文件大括号、引号成对；适配版与测试版对应文件 SHA-256 一致；兼容补丁相对适配版仅保留上述预期差异。

### 2026-07-15

- 建立本制作日志。
- 盘点霜泽美术馆与秋起图书馆，记录适用于 KR 项目的素材和风险。
- 确认可在游戏途中通过国策强化 MIO，并记录两种实现方式。

### 2026-07-14

- 完成联邦计划委员会核心机制移植及中、英、俄本地化修复。
- 委员会国策树窗口最终调整为 `(400,30)`。
- 修复空行本地化键直接显示代码的问题。
- 补齐曼施坦因事件音乐的音乐台注册，并改为按钮效果直接调用歌曲。

### 本轮较早内容

- 移植伏罗希洛夫并调整为等级 4、属性 `3/5/4/6`。
- 将伏罗希洛夫陆军部长效果改为“陆军突破（大师）”。
- 将部长头像做黑白处理，将领头像保持彩色。
- 取消季诺维也夫作为二把手和领导人时对权力平衡的数值影响。
