# HOI4 Mod 入门与本项目维护教程

版本：2026-08-01  
适用项目：[KR] 多么幼稚的幻想，但是斯大林——适配版 / 测试版

这份教程不是一篇只讲概念的通用文章，而是根据本项目实际开发过程整理的操作手册。目标是让你能够独立完成最常见的修改：改国策位置与时间、调整民族精神数值、改事件文本、添加决议、替换人物头像和图标、排查旧存档问题，以及安全地提交和发布。

如果你只想马上开始，先读第1、2、3、6、7、10和18章；如果准备制作自己的完整模组，再按顺序通读全文。

## 目录

1. 开始前必须理解的目录与加载关系
2. 推荐工具与最安全的修改流程
3. Paradox 脚本基础
4. 本项目文件结构与引用关系
5. ID、旗标、变量与命名规范
6. 本地化与中文编码
7. 国策制作与布局
8. 事件制作
9. 决议、任务与可重复决议
10. 民族精神、普通修正与动态修正
11. 人物、将领、顾问与特质
12. scripted trigger、scripted effect 与 on_action
13. 自动推进国策与旧存档兼容
14. 自定义 GUI 与动态进度条
15. 美术制作实战：国策图标、民族精神、人物肖像等
16. 音乐、事件音乐与加载界面
17. 兼容补丁与大型模组更新
18. 测试、错误日志、Git 与上传
19. 七个最常用的独立修改配方
20. 本项目开发中的典型故障案例
21. 入门练习路线

## 1. 开始前必须理解的目录与加载关系

### 1.1 四类目录不是一回事

本项目同时存在源码目录、测试目录、Steam 订阅目录和上传目录。它们的用途完全不同。

| 类型 | 本项目示例 | 能否直接修改 |
| --- | --- | --- |
| 正式适配版源码 | D:\steam\steamapps\workshop\content\394360\kr_stalin_adapted_local | 可以，默认权威版本 |
| 测试版源码 | D:\steam\steamapps\workshop\content\394360\kr_stalin_adapted_test | 可以，但应与适配版同步 |
| Steam 数字订阅目录 | 1521695605、3723313895、3746983015 等 | 不可以，只读参考 |
| 干净上传目录 | kr_stalin_adapted_local_upload、kr_stalin_adapted_test_upload | 不手工修改，由脚本生成 |

最重要的规则：不要在纯数字 Steam 创意工坊目录里开发。Steam 更新或重新订阅时可能直接覆盖它们。

正确做法是：

1. 在适配版源码中修改。
2. 把相同游戏内容同步到测试版。
3. 两边分别提交 Git。
4. 运行上传脚本生成干净上传目录。
5. Steam 上传器只选择正式上传目录对应的启动器条目。

### 1.2 HOI4 的模组覆盖方式

HOI4 不是把所有文件“智能合并”。大致有三种情况：

- 新文件、唯一 ID：通常可以与其他模组并存。
- 相同定义 ID：后加载的定义可能覆盖先加载的定义。
- 相同相对路径的大型文件：经常需要完整覆盖或人工合并，风险最高。

例如本项目修改俄罗斯国策时使用：

D:\steam\steamapps\workshop\content\394360\kr_stalin_adapted_local\common\national_focus\RUS focus (Russia).txt

这是一个大型 KR 文件副本。KR 更新这个文件后，本项目不会自动获得所有上游变化，必须进行人工对比和合并。

### 1.3 建议加载顺序

本项目通常按以下顺序加载：

1. Kaiserreich
2. KR 共产主义拓展前置
3. 本适配版或测试版
4. LKMT、更多自定义玩法等独立兼容补丁

兼容补丁必须放在它所兼容的两个模组之后。不要把兼容逻辑直接写进 KR、LKMT 或其他作者的订阅目录。

## 2. 推荐工具与最安全的修改流程

### 2.1 推荐工具

最低配置：

- Visual Studio Code 或 Notepad++
- 支持 Paradox Script / HOI4 语法高亮的扩展
- Git
- PowerShell
- GIMP、Krita 或 Photoshop
- 能正确导出 DDS 的插件或工具
- RHoiScribe，用于结构、引用、重复 ID 与错误检查

图片工具可以按习惯选择：

- GIMP：免费，支持 DDS，适合抠图、蒙版、调色。
- Krita：免费，绘画与笔刷体验好，适合图标再绘制。
- Photoshop：图层、动作、智能对象最方便，建议安装 Intel Texture Works 等 DDS 工具。
- Paint.NET：处理简单裁切和 DDS 很方便，但复杂合成能力较弱。

### 2.2 每次修改前的固定动作

在适配版目录打开 PowerShell：

~~~powershell
git status --short --branch
rg -n "你要修改的ID或中文文本" .
~~~

先搜索，再编辑。不要只凭截图猜文件。

建议的搜索顺序：

1. 搜中文标题，找到本地化键。
2. 搜本地化键，找到脚本 ID。
3. 搜脚本 ID，查看定义、调用、GFX、旧存档补发和兼容补丁。
4. 确认修改是否应同步到测试版或独立兼容补丁。

### 2.3 一次只改一个主题

例如“把革命集体主义增加2%适役人口”是一个主题。不要顺手把十个不相关文件一起格式化，否则很难知道哪一处导致游戏报错。

修改后先看差异：

~~~powershell
git diff --check
git diff -- "common/ideas/RUS_fr_military_reform_ideas.txt"
~~~

不要使用 git reset --hard 或 git checkout -- 清理工作树。本项目可能已经存在用户保留的 descriptor.mod 或未跟踪美术素材。

## 3. Paradox 脚本基础

### 3.1 键值、区块与列表

最基本的写法：

~~~hoi4
cost = 3
has_socialist_government = yes
~~~

区块使用大括号：

~~~hoi4
available = {
	has_completed_focus = RUS_fr_rebuild_revolutionary_military_council
	has_country_flag = RUS_fr_reform_stage_1
}
~~~

列表经常也写在大括号中：

~~~hoi4
traits = {
	old_guard
	politically_connected
}
~~~

井号是注释：

~~~hoi4
# 这行不会被游戏执行
army_experience = 20
~~~

### 3.2 Trigger 与 Effect 的区别

Trigger 是条件判断，Effect 是实际执行。

条件示例：

~~~hoi4
has_completed_focus = RUS_fr_military_rectification
has_country_flag = RUS_fr_reform_stage_1
NOT = { has_army_experience < 100 }
~~~

效果示例：

~~~hoi4
set_country_flag = RUS_fr_reform_stage_1
army_experience = -100
add_ideas = RUS_fr_revolutionary_collectivism_idea
~~~

同一个命令放错上下文，就可能出现 RHoiScribe 或 CWT 的 Unexpected field 报错。

### 3.3 AND、OR、NOT

一个普通区块中的多个条件通常相当于 AND：

~~~hoi4
available = {
	has_socialist_government = yes
	has_completed_focus = RUS_fr_military_rectification
}
~~~

OR 必须明确写出：

~~~hoi4
OR = {
	has_idea = RUS_fr_reform_disorganisation_4
	has_idea = RUS_fr_reform_disorganisation_4_comrades_abroad
}
~~~

排除条件：

~~~hoi4
NOT = {
	has_country_flag = RUS_fr_reform_stage_1
}
~~~

### 3.4 Scope：代码当前在操作谁

常见作用域：

- ROOT：当前国家或事件的根作用域。
- FROM：调用来源，具体含义随事件、on_action 而变。
- character：人物作用域。
- every_country：遍历所有国家。
- every_army_leader：遍历所有陆军将领。
- mio:某ID：指定军工机构。

本项目的 on_unit_leader_level_up 会先检查国家旗标，再进入 character 作用域给升级将领增加属性。修改这类代码前必须确认每一层大括号当前属于国家还是人物。

### 3.5 数值最容易犯的错误

多数百分比使用小数：

| 脚本值 | 游戏显示 |
| --- | --- |
| 0.01 | +1% |
| 0.10 | +10% |
| -0.15 | -15% |
| 0.5 | +50% |

但不是所有字段都按百分比显示。例如：

- political_power_factor = 0.15：政治点数获取修正 +15%。
- political_power_gain = 0.5：每日政治点数直接 +0.5。
- conscription = 0.02：直接增加2%适役人口。
- conscription_factor = 0.02：适役人口系数 +2%，含义不同。
- cost = 25：决议花费25政治点数，通常不是25%。

修改数值时先复制同类原版或 KR 代码，不要凭字段名字猜单位。

## 4. 本项目文件结构与引用关系

本项目的一个完整功能经常跨越多个文件：

~~~text
国策或决议
├─ common/national_focus 或 common/decisions
├─ 调用 scripted trigger / scripted effect
├─ 添加民族精神、变量、旗标或人物
├─ 触发 events 中的事件
├─ 使用 interface/*.gfx 注册的图片
└─ 显示 localisation 中的标题、描述和提示
~~~

军改 GUI 的链条更长：

~~~text
决议分类
→ scripted_gui
→ scripted trigger 判断状态
→ scripted effect / 事件执行阶段
→ interface .gui 摆放按钮和文字
→ interface .gfx 注册图片
→ gfx 文件提供背景、图标和进度条
→ localisation 提供所有文字
~~~

常用目录：

| 目录 | 用途 |
| --- | --- |
| common/national_focus | 国策树 |
| events | 事件逻辑 |
| common/decisions | 决议与任务 |
| common/decisions/categories | 决议分类 |
| common/ideas | 民族精神、顾问 idea |
| common/dynamic_modifiers | 数值由变量控制的动态精神 |
| common/characters | 领导人、将领、顾问 |
| common/scripted_effects | 可重复调用的效果 |
| common/scripted_triggers | 可重复调用的条件 |
| common/on_actions | 开局、每日、每周、升级等钩子 |
| common/scripted_guis | GUI 的可见条件和点击效果 |
| interface | GUI、Sprite、字体注册 |
| gfx | 实际图片、头像、字体图集 |
| localisation | 中文、英文、俄文文本 |
| music | OGG、asset 和音乐台定义 |

## 5. ID、旗标、变量与命名规范

### 5.1 所有自定义 ID 都要有前缀

本项目军改系统统一使用 RUS_fr_ 前缀，例如：

- RUS_fr_military_rectification
- RUS_fr_reform_stage_1
- RUS_fr_military_reform.50
- GFX_goal_RUS_fr_revolutionary_military_council

前缀能避免与 KR、其他子模组和原版重复。

### 5.2 Country Flag 适合保存开关状态

~~~hoi4
set_country_flag = RUS_fr_reform_stage_1
has_country_flag = RUS_fr_reform_stage_1
clr_country_flag = RUS_fr_reform_stage_1
~~~

适合表示：

- 是否选择某条路线
- 是否已经补发旧存档奖励
- 某阶段是否完成
- 某事件是否已经触发

旗标本身没有数字。

### 5.3 Variable 适合保存数字

~~~hoi4
set_variable = { RUS_fr_dashboard_reform_total_days = 120 }
add_to_variable = { RUS_fr_military_reform_materials = 15 }
multiply_variable = { RUS_example = 0.1 }
~~~

变量适合保存：

- 材料点数
- 进度天数
- 动态修正值
- 决议花费
- 共产主义支持率换算结果

计算百分比时要分清游戏变量是 0到1 还是 0到100。此前“9.02%支持率给了9%而不是0.9%”就是因为显示百分比和脚本小数尺度没有统一。

### 5.4 一次性补发一定要有防重复标记

~~~hoi4
if = {
	limit = {
		has_completed_focus = RUS_example_focus
		NOT = { has_country_flag = RUS_example_legacy_reward_granted }
	}
	add_ideas = RUS_example_idea
	set_country_flag = RUS_example_legacy_reward_granted
}
~~~

没有最后的旗标，每日 on_action 会每天重复加效果。

## 6. 本地化与中文编码

### 6.1 本地化文件结构

简体中文文件开头：

~~~yaml
l_simp_chinese:
 RUS_demo_focus:0 "示例国策"
 RUS_demo_focus_desc:0 "这是示例国策的描述。"
~~~

事件通常使用：

~~~yaml
 RUS_demo_event.1.t:0 "事件标题"
 RUS_demo_event.1.d:0 "事件正文"
 RUS_demo_event.1.a:0 "事件按钮"
~~~

你与我交流时使用的“标题//正文//按钮”只是沟通约定，不是 HOI4 文件语法。真正写入文件时会拆成 .t、.d、.a 三个本地化键。

### 6.2 UTF-8 BOM

HOI4 本地化 yml 应保存为 UTF-8 BOM。没有 BOM 时可能出现：

- 中文变成问号
- 整个文件不加载
- 游戏直接显示本地化键
- §、£ 等控制字符损坏

PowerShell 检查前三个字节：

~~~powershell
$p = "localisation\simp_chinese\RUS_fr_military_reform_l_simp_chinese.yml"
$b = [IO.File]::ReadAllBytes($p)
[BitConverter]::ToString($b[0..2])
~~~

正确结果应为 EF-BB-BF。

### 6.3 颜色与图标控制符

常见颜色：

- §Y黄色§!
- §G绿色§!
- §R红色§!
- §W白色§!

本项目报告事件曾因浅色背景上使用黄色、绿色数字导致看不清，后来统一改用更合适的普通黑色文本。颜色不是越多越好，要以实际背景可读性为准。

£GFX_xxx 是文本图标控制符，不能把 £ 写成普通问号。

### 6.4 字体缺字和编码损坏不是同一个问题

如果文本文件里已经是问号，通常是编码损坏。

如果文件里汉字正常，但游戏显示问号，通常是字体图集没有该字。军改 GUI 使用自定义北魏楷书字体时，“当前改革进度”中的部分字不在图集内，因此最后精简为“改革进度”。

解决字体缺字有三种方法：

1. 换用字体中已有的词。
2. 扩充字体图集和 fnt 字符映射。
3. GUI 英文版使用另一套完整拉丁字体。

## 7. 国策制作与布局

### 7.1 一个最小国策

~~~hoi4
focus = {
	id = RUS_demo_focus
	icon = GFX_goal_RUS_demo_focus
	cost = 3

	relative_position_id = RUS_fr_rebuild_revolutionary_military_council
	x = 0
	y = 1

	prerequisite = {
		focus = RUS_fr_rebuild_revolutionary_military_council
	}

	completion_reward = {
		army_experience = 20
		country_event = { id = RUS_demo_event.1 hours = 6 }
	}
}
~~~

普通情况下 cost 的1点约等于7天，因此 cost = 3 通常是21天。但 defines、国家修正或本项目的时间减免机制可能改变实际时间。

### 7.2 allow_branch、available、prerequisite 与 bypass

- allow_branch：整个分支是否存在或可显示。
- available：当前能不能选择。
- prerequisite：必须先完成哪些国策，也决定可视连线。
- bypass：满足条件时自动跳过国策。

本项目曾经遇到“实际条件正确，但国策树出现多余突出线段”。原因是 prerequisite 同时控制逻辑和可视连线。解决方式通常不是删除真实条件，而是：

- 用一个更合适的可视 prerequisite 连接父节点。
- 把其他真实要求放进 available。
- 在描述中说明额外前置条件。

### 7.3 x、y 与 relative_position_id

如果 B 相对 A：

~~~hoi4
relative_position_id = A
x = 2
y = 1
~~~

那么 B 在 A 的右侧2格、下方1格。

调整单个节点：修改该节点 x/y。

移动整棵子树：修改最上层根节点，所有相对它的后代会一起移动。

本项目最新的例子：

~~~hoi4
id = RUS_fr_post_revolutionary_armed_forces
x = 8
y = 9
offset = {
	x = -7
	trigger = { has_socialist_government = yes }
}
~~~

为了避免“军事民主制试行”与原有工业国策“电子计算机”重叠，我们把根节点 x 从7改为8。这样整套军改树右移1格，内部三条分支不会被拆散。

### 7.4 offset 会改变实机位置

offset 是条件性偏移。只计算 x/y 而忽略 offset，会得到错误结论。

布局排查必须同时检查：

- 当前节点 x/y
- relative_position_id
- 所有祖先节点
- offset
- 同层其他分支的标题框宽度
- 国策图标宽度
- 可视 prerequisite 连线

标题背景比图标宽，因此“坐标不相同”不等于“视觉上不会重叠”。

### 7.5 国策完成后触发事件

~~~hoi4
completion_reward = {
	hidden_effect = {
		country_event = {
			id = RUS_fr_military_reform.50
			hours = 6
		}
	}
}
~~~

使用 hours = 6 可以避免国策完成瞬间大量界面同时弹出，也更像一份随后递交的报告。

### 7.6 Tooltip 只负责显示，不负责效果

~~~hoi4
custom_effect_tooltip = RUS_demo_bonus_tt
~~~

这行只显示文字，不会真的增加数值。必须同时存在真正的 effect、idea 或 dynamic modifier。

“提示里写了加成但游戏没生效”时，第一步就是检查是否只有 tooltip。

## 8. 事件制作

### 8.1 Namespace 和事件 ID

文件顶部：

~~~hoi4
add_namespace = RUS_fr_military_reform
~~~

事件：

~~~hoi4
country_event = {
	id = RUS_fr_military_reform.50
	title = RUS_fr_military_reform.50.t
	desc = RUS_fr_military_reform.50.d
	picture = GFX_report_event_RUS_army_instructer
	is_triggered_only = yes

	option = {
		name = RUS_fr_military_reform.50.a
	}
}
~~~

Namespace 与数字 ID 的组合必须唯一。复制事件后忘记改数字，会造成覆盖或重复定义。

### 8.2 is_triggered_only

is_triggered_only = yes 表示事件不会随机自行触发，只能由国策、决议、on_action 或另一个事件调用。

本项目的工作报告、铁木辛哥评估报告、未来战争之首要等都采用这种方式。

### 8.3 延迟事件

~~~hoi4
country_event = {
	id = RUS_demo_event.2
	days = 7
}
~~~

“完成国策7天后触发”应由调用位置设置 days = 7，而不是把事件写成随机 MTTH。

### 8.4 事件选项

~~~hoi4
option = {
	name = RUS_demo_event.1.a
	ai_chance = { factor = 50 }
	set_country_flag = RUS_demo_route_a
}
~~~

只有一个按钮时，只保留一个 option。不要为了形式保留无意义的其他选项。

### 8.5 KR 风格事件写作

本项目积累出的写作原则：

- 正文写成世界内真实文件、报告、会议记录或人物经历。
- 不在正文解释“获得10%攻击”“解锁某决议”等后台机制。
- 机制放在按钮效果、国策效果栏或 tooltip。
- 报告类事件可编造合理数据增强代入感，但数据必须符合时代技术与行政能力。
- 有人物参与时不要把集体改革全部写成单个人的功劳。
- 长文要有段落、节奏和明确视角。

## 9. 决议、任务与可重复决议

### 9.1 决议分类

~~~hoi4
RUS_fr_military_reform_decisions = {
	icon = GFX_decision_generic_military
	priority = 950
	allowed = { original_tag = RUS }
	visible = { has_country_flag = RUS_fr_military_reform_unlocked }
	visible_when_empty = yes
	scripted_gui = RUS_fr_military_reform_dashboard
}
~~~

分类元数据放在 common/decisions/categories，具体决议放在 common/decisions。

### 9.2 可重复决议

本项目的材料调拨决议：

~~~hoi4
RUS_fr_federal_plan_armaments_allocation = {
	icon = GFX_decision_generic_industry
	cost = 25
	days_re_enable = 90

	available = {
		has_completed_focus = RUS_coordinate_development
	}

	complete_effect = {
		add_to_variable = {
			RUS_fr_military_reform_materials = 15
		}
	}

	ai_will_do = { factor = 5 }
}
~~~

days_re_enable 表示完成后多少天重新开放。

### 9.3 自定义花费

~~~hoi4
custom_cost_text = RUS_fr_cost_25_army_xp
custom_cost_trigger = {
	NOT = { has_army_experience < var:RUS_fr_xp_cost_25 }
}
complete_effect = {
	army_experience = var:RUS_fr_xp_cost_25_negative
}
~~~

自定义花费必须同时具备：

- 显示文本
- 能否支付的 trigger
- 实际扣除 effect

只写显示文本不会自动扣资源。

### 9.4 Mission 与普通决议

Mission 通常拥有持续时间和失败效果，普通决议一般点击后立即或延时完成。

阶段改革既可以做成 mission，也可以像本项目一样由 GUI 按钮设置进行中旗标，再安排延迟事件在90或120天后完成。后者更适合自定义进度条。

## 10. 民族精神、普通修正与动态修正

### 10.1 普通民族精神

~~~hoi4
ideas = {
	country = {
		RUS_demo_idea = {
			picture = RUS_demo_idea
			allowed = { always = no }
			removal_cost = -1

			modifier = {
				army_org_factor = 0.10
				army_defence_factor = 0.15
				supply_consumption_factor = -0.15
			}
		}
	}
}
~~~

picture 通常不带 GFX_idea_ 前缀，游戏会查找名为 GFX_idea_RUS_demo_idea 的 Sprite。

### 10.2 常用数值区别

本项目常用字段：

- army_attack_factor：全陆军攻击。
- army_defence_factor：全陆军防御。
- army_infantry_attack_factor：步兵攻击。
- army_armor_attack_factor：装甲攻击。
- special_forces_attack_factor：特种部队攻击。
- army_attack_against_major_factor：对主要国家攻击。
- army_speed_factor：陆军速度。
- supply_consumption_factor：补给消耗。
- combat_width_factor：战斗宽度修正。
- initiative_factor：主动性。
- coordination_bonus：协同性。
- production_factory_max_efficiency_factor：生产效率上限。
- industrial_capacity_factory：工厂产出。
- political_power_factor：政治点获取百分比。
- conscription：直接适役人口。

不要只改本地化显示，实际 modifier 也必须修改。

### 10.3 动态修正

当效果由变量实时计算时，使用 common/dynamic_modifiers：

~~~hoi4
RUS_fr_armour_specialisation = {
	icon = GFX_idea_generic_tank_manufacturer_1
	breakthrough_factor = RUS_fr_specialist_primary_bonus
	army_attack_factor = RUS_fr_specialist_secondary_bonus
}
~~~

变量改变后可能需要：

~~~hoi4
force_update_dynamic_modifier = yes
~~~

本项目“共产主义支持率的0.1倍”以及装甲攻防上限问题，核心不是 tooltip，而是：

1. 读取支持率时统一0到1的尺度。
2. 乘以0.1。
3. 对这部分额外加成单独封顶15%。
4. 不要把其他国策固定提供的10%也一起截断。
5. 因此最终总显示上限可以是25%。

### 10.4 修改民族精神的安全步骤

1. 搜民族精神中文名，找到本地化键。
2. 搜 ID，找到 common/ideas 或 dynamic_modifiers。
3. 确认它是否由变量控制。
4. 修改实际 modifier。
5. 修改 tooltip 或本地化。
6. 检查是否有旧存档补发或重算 effect。
7. 进游戏查看最终总值，而不只看单个 tooltip。

## 11. 人物、将领、顾问与特质

### 11.1 人物基本结构

~~~hoi4
characters = {
	RUS_demo_character = {
		name = RUS_demo_character

		portraits = {
			army = {
				large = GFX_portrait_RUS_demo_character_army_large
				small = GFX_portrait_RUS_demo_character_army_small
			}
		}

		corps_commander = {
			skill = 2
			attack_skill = 2
			defense_skill = 2
			planning_skill = 2
			logistics_skill = 1
			traits = { cavalry_officer politically_connected }
		}

		advisor = {
			slot = high_command
			idea_token = RUS_demo_character_high_command
			traits = { KR_MHC_cavalry_1 }
			cost = 50
		}
	}
}
~~~

### 11.2 定义人物不等于国家已经拥有他

人物还需要：

- 在历史文件中招募；
- 在国策奖励中 set_nationality；
- 使用 recruit_character；
- 或由 on_startup / on_daily 给老存档补发。

本项目布琼尼“代码存在但旧存档没有出现”就是典型例子。最终需要同时检查：

1. 人物定义是否加载。
2. 头像 GFX 是否存在。
3. 当前国家是否拥有角色。
4. 老存档是否经过补发。
5. 补发条件是否覆盖所有改革阶段。
6. 是否设置防重复旗标。

### 11.3 同一人物的大头像和小头像

本项目常见规则：

- 将领大头像：156×210，彩色。
- 顾问小头像：65×67，KR 风格黑白。
- 同一个人物必须分别注册 large 和 small Sprite。
- 不要把156×210大图直接缩放成顾问头像而不重新构图；脸会过小。

## 12. scripted trigger、scripted effect 与 on_action

### 12.1 为什么要拆成可复用代码

如果十个国策都使用同一套条件，不应复制十遍。把它写入 common/scripted_triggers：

~~~hoi4
RUS_demo_can_start = {
	has_socialist_government = yes
	has_country_flag = RUS_demo_unlocked
	NOT = { has_country_flag = RUS_demo_in_progress }
}
~~~

调用：

~~~hoi4
available = {
	RUS_demo_can_start = yes
}
~~~

效果同理：

~~~hoi4
RUS_demo_grant_reward = {
	add_ideas = RUS_demo_idea
	set_country_flag = RUS_demo_reward_granted
}
~~~

### 12.2 on_action

本项目使用：

- on_startup：读档或开局时修复状态。
- on_daily：每日更新 GUI、变量和旧存档缺失效果。
- on_weekly：执行较重的周期检查。
- on_unit_leader_level_up：将领升级时概率增加属性。
- on_unit_leader_created：新将领生成时附加特质。

on_daily 不能塞进过于庞大的 every_country / every_character 扫描，否则会拖慢游戏。能每周检查的内容不要每天检查。

### 12.3 将领升级概率

本项目铁木辛哥侧重步兵时使用独立 random_list：

~~~hoi4
random_list = { 50 = { add_attack = 1 } 50 = { } }
random_list = { 50 = { add_defense = 1 } 50 = { } }
random_list = { 50 = { add_planning = 1 } 50 = { } }
random_list = { 50 = { add_logistics = 1 } 50 = { } }
~~~

四次独立投掷意味着一次升级可能同时获得多个属性。若只允许四选一，就要写成一个 random_list，而不是四个。

## 13. 自动推进国策与旧存档兼容

### 13.1 自动推进不是普通国策队列

本项目军工线和肃反线能够与玩家当前选择的国家国策同时推进。实现思路是：

1. 设置某条自动线 active 旗标。
2. 检查材料和前置条件。
3. activate_shine_on_focus 显示国策正在进行。
4. 安排延迟事件。
5. 延迟结束后 complete_national_focus。
6. 清理进行中旗标，再挑选下一个节点。

这样不会占用玩家正常国策槽。

### 13.2 两条自动线必须使用独立状态

此前肃反线没有自动进行，是因为它与军工线共享了“当前已有自动项目”的锁。正确做法是分别维护：

- 肃反线 selected / active / in_progress
- 军工线 selected / active / in_progress

允许两套计时同时存在，但同一条线内部一次只能跑一个节点。

### 13.3 不存在的国策完成动画

出现“伏尔加河上的底特律”“宏大机械化计划”等错误动画时，通常是：

- complete_national_focus 指向旧 ID；
- 复制了 KR 原国策奖励但没有改 ID；
- 分支选择表仍引用已删除国策；
- 老存档残留事件继续完成旧节点。

排查方式：

~~~powershell
rg -n "complete_national_focus|activate_shine_on_focus" common events
~~~

检查所有被自动完成的 ID 是否确实存在。

### 13.4 老存档不会重跑 completion_reward

更新前已经完成的国策，更新后不会自动重新执行新增奖励。因此：

- 新存档：在 completion_reward 正常给奖励。
- 老存档：在 on_startup、on_daily 或一次性事件中补发。
- 补发后设置 country flag。
- 如果效果会随变量变化，还要重算 dynamic modifier。

## 14. 自定义 GUI 与动态进度条

### 14.1 GUI 由四层组成

1. interface/*.gui：位置、按钮、文字和图片元素。
2. interface/*.gfx：图片 Sprite 和字体注册。
3. common/scripted_guis：显示条件与按钮效果。
4. common/scripted_triggers / effects：复杂逻辑。

只改 .gui 不能让按钮真正执行游戏效果。

### 14.2 按钮绑定规则

GUI 元素名：

~~~hoi4
buttonType = {
	name = "RUS_fr_dashboard_stage_1_button"
	position = { x = 164 y = 81 }
	quadTextureSprite = "GFX_RUS_fr_dashboard_stage_1_grey"
	pdx_tooltip = "RUS_fr_dashboard_stage_1_tt"
}
~~~

scripted_gui 中对应：

~~~hoi4
triggers = {
	RUS_fr_dashboard_stage_1_button_click_enabled = {
		RUS_fr_can_start_reform_stage_one = yes
	}
}

effects = {
	RUS_fr_dashboard_stage_1_button_click = {
		set_country_flag = RUS_fr_reform_stage_1_in_progress
		country_event = { id = RUS_fr_military_reform.910 days = 120 }
	}
}
~~~

命名必须完全一致：元素名 + _click、_click_enabled、_visible 等后缀由 scripted GUI 约定识别。

### 14.3 动态进度条

本项目使用变量保存：

- 总天数
- 已经过天数
- 剩余天数
- 进度条 x 坐标
- 当前帧

每日 on_action 更新进度变量，scripted_gui properties 把变量传给 GUI。

制作进度条时要检查：

- 背景层是否在最底层。
- 裁切框是否真的显示。
- 进度条是否被其他 container 裁掉。
- x 偏移方向是否正确。
- 标题不要占用原有文字空间。
- 不同 UI 缩放倍率下是否仍可见。

### 14.4 GUI 字体

本项目自定义字体位于：

- gfx/fonts/RUS_fr_beiwei_15.*
- gfx/fonts/RUS_fr_beiwei_22.*
- interface/RUS_fr_military_reform_dashboard_fonts.gfx

字体图集通常包括：

- PNG/TGA 字形图
- FNT 字符坐标
- GFX 中的 bitmapfont 注册

缺任一部分都可能不显示。

## 15. 美术制作实战：国策图标、民族精神、人物肖像等

### 15.1 本项目实际使用的尺寸

HOI4 并非所有图片都只有一个绝对尺寸，最稳妥的方法是复制同类 KR 成品作为画布。下表是本项目当前成品的实际尺寸：

| 类型 | 本项目实例尺寸 | 说明 |
| --- | --- | --- |
| 国策图标 | 88×88、94×80 等 | 常见参考约95×85，按邻近 KR 图标画布制作 |
| 民族精神图标 | 60×68、65×67 | 小尺寸，必须强调轮廓 |
| 顾问小头像 | 65×67 | KR 顾问常用黑白头像 |
| 将领/领导人大头像 | 156×210 | 本项目将领保留彩色 |
| KR 报告事件卡片 | 281×311 | 竖向倾斜报告卡片构图 |
| 主菜单背景 | 1920×1440 | 4:3，不可把16:9直接纵向拉伸 |
| Steam 缩略图 | 512×512 | 正方形 |
| 自定义 GUI 图块 | 按 .gui 实际需要 | 必须与界面坐标共同测试 |

不要只看网上教程写的尺寸。先检查当前模组同类型图片和 GFX 注册，尤其是继承 KR 风格时。

### 15.2 通用美术工作流

无论做什么图标，都建议保留分层源文件：

1. 明确用途和最终尺寸。
2. 从 KR、原版或授权素材中找参考。
3. 建立两到四倍分辨率的工作画布。
4. 抠出主体并清理边缘。
5. 先用灰度检查明暗层次。
6. 调整色相、饱和度和对比度。
7. 添加边缘光、阴影、金属或纸张纹理。
8. 缩小到最终尺寸后再次锐化。
9. 检查透明通道。
10. 导出 PNG 预览与 DDS/PNG 游戏文件。
11. 注册 GFX。
12. 完全重启游戏实测。

高分辨率素材直接缩小通常会糊成一团。最终锐化必须在目标尺寸附近进行。

### 15.3 国策图标

#### 构图原则

KR 国策图标适合：

- 一个主要主体：人物、武器、建筑、文件、机器。
- 一个辅助符号：红旗、齿轮、花环、地图、闪电。
- 清楚的前中后景。
- 暗色背景与较亮主体。
- 少量金属、黄铜、红色点缀。
- 不使用可读小字。

在88到95像素的画布里，三个以上同等重要的主体通常会太乱。

#### 推荐流程

1. 从 gfx/interface/goals 中复制一个构图接近的 KR 图标作为尺寸参考。
2. 用钢笔或蒙版抠出主体。
3. 主体占画面高度约60%到85%。
4. 背景降低饱和度和清晰度。
5. 主体增加局部对比、边缘高光和细微投影。
6. 叠加轻微颗粒，让它不要像高清 AI 海报。
7. 缩到最终尺寸后使用0.3到0.8像素的锐化。
8. 在透明背景和游戏深色国策框中分别检查。

本项目用户反馈“AI味太浓、不需要这么高清、人物可以模糊一些”，核心处理方法就是：降低皮肤细节，统一人物边缘，增加胶片颗粒，让主体融入整体调色，而不是保持生成图的超锐利纹理。

#### GFX 注册

~~~hoi4
spriteTypes = {
	SpriteType = {
		name = "GFX_goal_RUS_demo_focus"
		texturefile = "gfx/interface/goals/RUS_demo_focus.dds"
	}
}
~~~

国策引用：

~~~hoi4
icon = GFX_goal_RUS_demo_focus
~~~

如果需要国策完成闪光动画，可复制本项目 RUS_fr_military_reform_icons.gfx 中的 _shine 模板，并把 animationmaskfile 改成自己的图标。

### 15.4 民族精神图标

民族精神只有约60×68或65×67，细节容纳能力比国策图标更低。

设计建议：

- 保留一个强轮廓主体。
- 人脸不要太小。
- 避免细密背景。
- 用明显的明暗分区表达主题。
- 红星、花环、盾牌、齿轮可以作为外框，但不要遮住主体。
- 先在100%实际像素大小观察，不要只在放大状态评价。

注册：

~~~hoi4
spriteTypes = {
	spriteType = {
		name = "GFX_idea_RUS_demo_idea"
		texturefile = "gfx/interface/ideas/RUS_demo_idea.png"
	}
}
~~~

民族精神定义：

~~~hoi4
RUS_demo_idea = {
	picture = RUS_demo_idea
}
~~~

注意 picture 写 RUS_demo_idea，而 Sprite 名是 GFX_idea_RUS_demo_idea。

### 15.5 顾问肖像与将领头像

本项目的规范：

- 将领大头像：彩色。
- 顾问小头像：黑白 KR 风格。
- 保持历史照片的原构图，除非头像比例明显不适配。
- 人物不应过度磨皮或呈现现代摄影棚效果。

#### 大头像 156×210

1. 选择胸像或半身像。
2. 眼睛高度与项目现有头像大致一致。
3. 头顶留少量空间，肩部不要被切得太窄。
4. 去除或弱化复杂背景。
5. 使用暗灰、军绿色、褐色等时代感背景。
6. 保留一定颗粒和镜头模糊。
7. 将人物与背景统一色温。
8. 导出带透明或完整背景的156×210图片。

#### 小头像 65×67

不能只把大图缩小。应重新裁切：

1. 以脸和肩章为中心。
2. 提高局部对比。
3. 转为黑白或低饱和度。
4. 适当提亮面部。
5. 背景尽量简单。
6. 缩小后检查五官是否仍能辨认。

GFX：

~~~hoi4
spriteType = {
	name = "GFX_portrait_RUS_demo_civilian_large"
	texturefile = "gfx/leaders/RUS/RUS_demo.png"
}
spriteType = {
	name = "GFX_portrait_RUS_demo_civilian_small"
	texturefile = "gfx/interface/advisors/RUS/RUS_demo.png"
}
~~~

人物定义必须引用同样的名称。

### 15.6 事件图与报告卡片

本项目的 KR 报告图采用：

- 高分辨率源图
- 轻微倾斜的照片或卡片
- 柔和投影
- 细微边缘高光
- 降饱和度
- 最终缩小到报告事件卡片尺寸

事件图不应直接塞一张现代高清照片。可以加入：

- 档案纸边缘
- 印刷网点
- 旧照片颗粒
- 轻微暗角
- 纸张阴影

但不要把正文文字画进图片；事件正文由本地化负责。

### 15.7 主菜单背景与加载图

本项目基线是1920×1440、4:3。

正确扩图：

- 根据原画内容真正补画左右或上下场景。
- 保持人物比例。
- 延续建筑、烟尘、部队和光线。
- 不使用模糊拉伸或柔和镜像填充。
- 不在图片中放游戏 UI 和可读文字。

错误做法：

- 把16:9图直接压成4:3。
- 只复制边缘并高斯模糊。
- 让主角人物被纵向拉长。
- 画面极度锐利，而 KR UI 本身偏旧照片与绘画质感。

### 15.8 DDS 与 PNG 导出

PNG 适合开发预览，也能用于不少 UI Sprite。DDS 在正式发布中更稳定。

建议：

- 带透明通道的 UI 图使用 BC3/DXT5 或无损 BGRA8。
- 不需要透明的背景可以使用 BC1/DXT1或无损格式。
- UI 图片通常不需要 mipmap。
- 导出后重新打开检查 Alpha。
- 不要只改扩展名。
- 文件路径、扩展名和 GFX texturefile 必须完全一致。

如果不确定压缩格式，复制同类型现有 DDS 的导出设置，而不是自行猜测。

### 15.9 图标制作自检表

- 在100%尺寸下主体是否一眼可辨？
- 轮廓是否与背景分离？
- 是否存在一圈白边或黑边？
- Alpha 是否干净？
- 是否有过多可读小字？
- 是否与 KR 的金属、纸张、浮雕和旧照片风格协调？
- 是否重复使用了明显不合适的国家符号？
- GFX 名、文件名、路径和脚本引用是否一致？
- 完全重启后是否显示？
- 灰色、彩色、完成态和高亮态是否都检查过？

## 16. 音乐、事件音乐与加载界面

### 16.1 一首事件音乐需要四处一致

以曼施坦因事件音乐为例：

1. music/rus_manstein_yablochko.ogg
2. music/zzz_stalin_manstein_yablochko.asset
3. music/zzz_stalin_manstein_yablochko.txt
4. 事件或国策中的 play_song / scoped_play_song

Asset：

~~~hoi4
music = {
	name = "RUS_manstein_yablochko"
	file = "rus_manstein_yablochko.ogg"
	volume = 0.85
}
~~~

音乐台：

~~~hoi4
music_station = "base_music"

music = {
	song = "RUS_manstein_yablochko"
	chance = {
		base = 0
	}
}
~~~

chance base = 0 可避免剧情专用曲随机播放。

### 16.2 音频格式

推荐 OGG Vorbis。若原文件是 NCM、MP3、FLAC 等，先转换为 OGG。

音乐没有声音时检查：

- 文件能否在普通播放器中播放。
- asset 名是否一致。
- station txt 是否注册。
- 调用名是否一致。
- 文件名大小写是否一致。
- 是否完全退出并重启游戏。

普通读档不能可靠重载音乐资产。

## 17. 兼容补丁与大型模组更新

### 17.1 为什么要独立兼容补丁

例如释放 CHI 傀儡：

- 本体适配版负责一般情况下固定彭湃等默认逻辑。
- 同时开启 LKMT 时，独立 LKMT 兼容补丁改为毛泽东领导、周恩来任副手。

这类逻辑不能直接写进 LKMT 本体，也不应让主模组无条件依赖 LKMT 的角色 ID。

### 17.2 兼容补丁目录

本项目已有：

- kr_stalin_lkmt_compat
- kr_stalin_more_custom_ai_compat
- kr_stalin_more_doctrines_compat

每个兼容补丁都应有自己的 descriptor、Git 仓库或提交历史、制作日志和依赖关系。

### 17.3 上游更新后的处理

1. 不要立即覆盖自己的文件。
2. 查上游更新了哪些文件。
3. 对比相同 ID 的代码块。
4. 保留上游新逻辑。
5. 重新应用本项目修改。
6. 检查已删除或重命名 ID。
7. 检查 game rule 和 AI 路线预设是否意外残留。
8. 新存档测试。
9. 再更新兼容补丁。

大型文件不要凭肉眼整份复制，优先围绕具体 ID 和引用进行合并。

## 18. 测试、错误日志、Git 与上传

### 18.1 静态测试

最低检查：

~~~powershell
git diff --check
~~~

再使用 RHoiScribe 检查：

- brace_balance
- unclosed_block
- 重复 ID
- 缺失本地化
- 缺失图片
- 无效引用
- replace_path 风险

KR 大型覆盖文件可能有大量既有 CWT 基线误报。不要看到红灯就自动改整份 KR 文件。必须先确认报错是否位于本次修改行附近。

### 18.2 游戏内测试

建议用 -debug 启动 HOI4，并检查文档目录下的 logs。

常用控制台命令：

- tdebug：显示国家、省份等调试信息。
- focus.autocomplete：国策立即完成。
- focus.nochecks：忽略国策条件。
- decision.nochecks：忽略决议条件。
- event RUS_fr_military_reform.50 RUS：手动触发事件。
- ai：开关 AI，便于测试。

UI、字体、音乐、人物、MIO 和 GFX 修改后应完全退出游戏再启动。返回主菜单通常不够。

### 18.3 新存档与旧存档都要测什么

新存档：

- 正常解锁。
- 正常完成国策。
- 奖励只发一次。
- 事件顺序正确。
- AI 条件正常。

旧存档：

- 已完成国策的新奖励是否补发。
- 人物是否补齐。
- 民族精神是否替换到正确阶段。
- 补发是否每天重复。
- GUI 变量是否初始化。
- 自动推进是否从正确节点继续。

### 18.4 Git 提交流程

~~~powershell
git status --short
git diff --check
git add -- "本次真正修改的文件"
git diff --cached --check
git commit -m "清楚说明本次改动"
~~~

不要使用 git add .，因为它可能把 descriptor.mod、源图、未跟踪草稿一起提交。

本项目要求每轮修改后分别提交适配版和测试版。GitHub 推送是另一件事，只有明确需要跨电脑同步时才执行。

### 18.5 干净上传目录

运行：

~~~powershell
.\tools\Build-CleanWorkshopUpload.ps1
~~~

脚本会：

- 只复制 Git 跟踪文件。
- 排除 .git、根目录 Markdown、tools。
- 排除 source、preview、draft 等美术草稿。
- 保留实际游戏资源和 descriptor.mod。
- 把旧上传目录改名备份。
- 重新生成新的 _upload 目录。

Steam 上传器必须选择正式上传目录，不要选择开发目录或数字订阅目录。

## 19. 七个最常用的独立修改配方

### 配方一：修改一个民族精神数值

例：把步兵攻防改为15%。

1. 搜中文名找到本地化键。
2. 搜 ID 找到 common/ideas 或 dynamic_modifiers。
3. 找到 army_infantry_attack_factor 和 army_infantry_defence_factor。
4. 改为0.15。
5. 检查 tooltip 是否同步。
6. 如果是动态变量，修改变量赋值和重算 effect。
7. 新存档与旧存档各测一次。

### 配方二：修改事件正文，不改按钮效果

1. 找事件 ID。
2. 打开 localisation/simp_chinese 对应文件。
3. 只改 .t 和 .d。
4. 不改 events 中 option。
5. 保持 UTF-8 BOM。
6. 检查引号和换行。

这正是“人民农业部只改正文，按钮不用修改”的做法。

### 配方三：移动整个国策子树

1. 找子树最上层根节点。
2. 确认所有后代都 relative_position_id 到该树内节点。
3. 检查根节点 offset。
4. 根节点 x + 1 即整树右移1格。
5. 不要逐个修改几十个后代节点。
6. 检查最左和最右边界。
7. 完全重启截图确认。

### 配方四：国策完成后触发事件

在 completion_reward 中加入：

~~~hoi4
hidden_effect = {
	country_event = {
		id = RUS_demo_event.1
		hours = 6
	}
}
~~~

再创建事件与三条本地化键。

### 配方五：添加一个可重复临时增益决议

~~~hoi4
RUS_demo_temporary_bonus = {
	icon = GFX_decision_generic_military
	cost = 25
	days_re_enable = 90

	available = {
		has_completed_focus = RUS_demo_focus
	}

	complete_effect = {
		add_timed_idea = {
			idea = RUS_demo_temporary_idea
			days = 90
		}
	}
}
~~~

再定义临时民族精神和本地化。

### 配方六：替换顾问肖像

1. 准备156×210大头像和65×67小头像。
2. 大头像放 gfx/leaders/RUS。
3. 小头像放 gfx/interface/advisors/RUS。
4. 在 interface .gfx 注册两个 Sprite。
5. 在 character 的 portraits 中引用。
6. 完全重启。
7. 同时检查顾问界面和人物界面。

### 配方七：为国策制作并注册新图标

1. 复制相近 KR 国策图标作为画布参考。
2. 在高分辨率画布完成合成。
3. 缩小并锐化到约88×88或邻近图标实际尺寸。
4. 导出 PNG/DDS。
5. 放入 gfx/interface/goals。
6. 在 interface .gfx 注册 GFX_goal_RUS_xxx。
7. 国策 icon 指向该 Sprite。
8. 如需要完成闪光，再注册 _shine。
9. 完全重启测试。

## 20. 本项目开发中的典型故障案例

| 现象 | 根因 | 正确处理 |
| --- | --- | --- |
| 9.02%支持率却给9%加成 | 百分比尺度错误 | 统一0到1尺度，再乘0.1 |
| 装甲攻防超过15% | 把总加成和该机制加成混在一起 | 只封顶支持率机制15%，允许其他国策再加10% |
| Tooltip 有效果但实际没有 | 只写 custom_effect_tooltip | 添加真实 modifier/effect |
| 旧存档没有布琼尼 | completion_reward 不会重跑 | on_startup/on_daily 一次性补发 |
| 肃反线不自动推进 | 与军工线共用锁 | 两条自动线使用独立 active/in_progress 状态 |
| 自动完成不存在的国策 | 旧 ID 残留 | 搜 complete_national_focus 和 shine 引用 |
| 国策标题互相重叠 | 只看节点坐标，忽略标题宽度和 offset | 按实际子树宽度与实机截图调整 |
| GUI 全是问号 | 编码损坏或字体缺字 | 检查 BOM；检查字体图集 |
| GUI 进度条不显示 | 层级、裁切、变量或 visible trigger 错误 | 逐层检查 .gui、scripted_gui 和每日更新 |
| 事件音乐无声 | 缺 OGG、asset、station 或调用之一 | 四处统一并完全重启 |
| 测试版比适配版大很多 | 把 Git、源图或草稿一起上传 | 使用干净上传脚本 |
| 兼容补丁释放错误领导人 | 主模组与 LKMT ID/效果冲突 | 在独立兼容补丁中覆盖释放效果 |

## 21. 入门练习路线

建议不要一开始就制作完整国家。按以下顺序练习：

### 第一阶段：只改文本和数字

1. 修改一个事件正文。
2. 修改一个民族精神的单项数值。
3. 修改一个国策时间。
4. 修改一个决议冷却时间。

目标：熟悉搜索、本地化、脚本小数和 Git diff。

### 第二阶段：增加简单内容

1. 新增一个只有一个按钮的报告事件。
2. 让现有国策完成后触发它。
3. 新增一个90天冷却的临时增益决议。
4. 新增一个普通民族精神。

目标：理解 ID、调用链和本地化。

### 第三阶段：人物与美术

1. 替换一个顾问小头像。
2. 制作一个民族精神图标。
3. 制作一个国策图标并注册 GFX。
4. 新增一个顾问并由国策解锁。

目标：理解 character、portrait、GFX 和图片路径。

### 第四阶段：运行时机制

1. 编写一个 scripted trigger。
2. 编写一个 scripted effect。
3. 用 on_startup 为旧存档补发奖励。
4. 用 country flag 防止重复补发。

目标：理解状态保存和旧存档。

### 第五阶段：GUI 与自动系统

1. 在现有 GUI 增加一行文字。
2. 增加一个灰色/彩色状态图标。
3. 增加一个按钮和 click effect。
4. 增加变量驱动的进度条。
5. 制作一条不占玩家国策槽的自动推进线。

目标：掌握本项目最复杂的系统。

## 结语：什么时候自己改，什么时候先问

适合自己直接改：

- 事件正文
- 单个数值
- 国策时间
- 决议冷却
- 国策坐标微调
- 已有图标或头像替换

建议先备份或先讨论：

- 大型国策树重排
- 动态修正计算
- 自动推进
- on_action
- 旧存档补发
- scripted GUI
- 兼容补丁
- 完整覆盖 KR 大文件

最有效的学习方式不是背命令，而是每次沿着“本地化键 → 脚本 ID → 调用 → 实际效果 → 资源 → 旧存档”这条链追踪一个功能。只要能独立追完这条链，你就已经具备维护本项目大部分内容的能力。

