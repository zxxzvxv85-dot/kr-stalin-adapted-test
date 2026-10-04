# 红德重建内容整合说明

2026-10-04，将用户提供的 `hongde.zip` 整合至 `kr_stalin_adapted_test` 开发目录。仅修改开发源；未构建上传目录，未发布 Steam，也不随本任务推送 GitHub。

## 正常游戏中的入口

满足以下条件的德国傀儡，在下一日接入红德内容：

- `original_tag = GRU`，包括 KR 创建的动态 `Dxx` 国家；不包括原版帝国 `GER`。
- 仍为傀儡，宗主国的原始标签为 `RUS`，且俄罗斯当前共产主义执政，或已确立本模组的共产主义路线。
- 德国当前由共产主义、极权主义、工团主义或激进社会主义政府执政。
- 德国已经停战，且未接入过红德重建，也不是该系统产生的内战叛军。

释放、政府更换和自治等级变动的钩子只排入一天后的隐藏事件 `GRU_reconstruction.98`，让 KR 先完成政府、人物、法律与国策树初始化。每日检查覆盖“释放时尚在战争中、之后才停战”的情况；同一国家只能排一个接管事件。延迟期间不再符合条件时取消本次接管并清除排队旗标，之后重新符合条件仍可正常进入。

## 初始政府与旧逻辑的关系

依照用户最后一次明确更正，红德建政时由 **共产主义** 执政，关闭通常的议会选举；党名为德国共产党。将 KR 已选出的现任领袖转入 `marxism_leninism_subtype`，保留人物身份与肖像，不另行从俄罗斯抽调一位人物。

原包的 55% 激进社会主义支持率移至共产主义，其余配比保留，总和为 100：

| 意识形态 | 初始支持率 |
| --- | ---: |
| 共产主义 | 55% |
| 激进社会主义 | 0% |
| 工团主义 | 15% |
| 极权主义 | 10% |
| 社会民主主义 | 10% |
| 社会自由主义 | 3% |
| 社会保守主义 | 2% |
| 威权民主主义 | 2% |
| 家长制独裁 | 1% |
| 市场自由主义 | 1% |
| 民族民粹主义 | 1% |

既有 `RUS_stalin_set_country_radical_socialist_for_subject_release` 对所有原始标签为 GRU 的国家跳过强制转激社，改为调用红德排队入口。普通傀儡的行为及广西特殊处理保持原样；`stalin_form_sov.20` 不再对 GRU 生效。后续政府变化、读档时的原有检查或自治变化，不会重新设置红德的支持率、清空进度或重置国策。

国名使用原包的“德意志社会主义共和国”，地图颜色沿用原包红色。三种尺寸国旗直接复用已安装 KR 的 `GRU_radical_socialist.tga`，保存为 `GRU_red_germany.tga`，使新增共产主义政体也有明确的国旗资源。

## 包内机制

- 保留 **59 个国策**、原有前置和互斥关系及奖励数值。国策树不参与开局自动分配，只通过接管入口加载。
- 保留经济、治安、民生三项重建进度，以及无政府主义者、民族主义者、保皇派三项影响力；均限制在 0 至 100。
- 三项投资决议分别花费 50 政治点，增加对应重建进度 5 个百分点与稳定度 1%，冷却 60 天。
- 三项取缔决议分别花费 50 政治点，降低对应影响力 10 个百分点并增加战争支持度 1%，冷却 90 天。
- 每 20 天随机出现一种破坏事件。镇压花费 15 政治点，不损失重建进度，对应影响力增加 2 个百分点；放任则随机损失对应重建进度 1 至 10 个百分点，影响力增加 4 至 8 个百分点。
- 任意两项重建进度达到 100%，可以通过决议安排七天后的第一次大选。任意敌对影响力 **高于** 80% 时出现受干扰结果；等于 80% 不触发该结果。
- 大选结算移除“崩溃的德意志”，给予原包的稳定度、政治点和支持率奖励，其中原包的激社支持率增长改为共产主义支持率增长。提前完成“筹备第一次大选”的额外奖励保留。结算在事件选项中显示原生效果，不再藏在事件立即效果里。
- 任意两派影响力达到 100% 时，取消重建与尚未结算的大选，一天后爆发内战。叛军份额仍为 35%，保留原包按保皇派、民族主义者、无政府主义者的检查次序。由于触发条件要求两派满值，正常路径实际由前两种优先分支选出叛军。

“崩溃的德意志”保留原包七项修正，图标修复为 KR 已存在的 `generic_crippled_industry`。依照原包逻辑，接管只移除 KR 的占领政府精神；其他战后精神和法律不自动清除。

## 整合时修复的兼容问题

1. 原包无条件接管所有社会主义 GRU／GER，改为仅接入俄罗斯共产主义路线的 GRU 傀儡，并兼容动态标签。
2. 原包在政府更换钩子中立即换树，改为延迟接管，避免被 KR 同一次释放流程覆盖。资格直接检查实际执政党，避免依赖尚未刷新的 `KR_is_socialist` 缓存旗标。
3. 修复民族精神空 `picture =` 字段，以及国策树 `reset_on_civil_war` 的拼写错误（原生键为 `reset_on_civilwar`）；将四个国名颜色条目合并进本模组现有 `common/countries/cosmetic.txt`。
4. 重建初始化只执行一次；第一次选举只允许一个待办事件。内战发生后，已经排队或留在屏幕上的选举／破坏事件不能继续发奖、扣款或改变该阶段进度。
5. 内战只创建一次。移除原包 `start_civil_war` 内将本国 `ruling_party` 设为叛军意识形态的字段，原政府保留其政体；叛军由 `ideology` 指定。叛军清除继承的重建状态，回到 KR 的德国傀儡国策树，且不再自动进入本系统。
6. 自定义进度和影响力变化放入效果提示，政治点、稳定度、支持率和精神使用引擎原生效果；决议描述保留叙事，实时六项数值集中在决议组说明中。
7. 2026-10-04 实机反馈发现三个镇压选项沿用了原包的 `political_power >= 15`。游戏日志先报无效 trigger 和比较符解析错误，随后无法正确读取同文件后续事件，包括释放接管 `.98`，因此德国仍保留 KR 原树。改为 `NOT = { has_political_power < 15 }`，保留恰好 15 点也可镇压的规则。参考 KR `events/GBR events (United Kingdom).txt` 的 `united_kingdom_events.7` 与游戏 `documentation/triggers_documentation.md`。此前 Python 模型错误地接受了原包的 trigger 别名和比较符，且未执行选项可见条件；本次一并修正，不能仅依靠模型逻辑测试判断引擎能否加载脚本。

## 维护入口

| 内容 | 文件 |
| --- | --- |
| 准入与状态条件 | `common/scripted_triggers/GRU_red_germany_triggers.txt` |
| 接管与初始政体 | `common/scripted_effects/GRU_red_germany_effects.txt` |
| 外部强制转激社的 GRU 例外 | `common/scripted_effects/RUS_stalin_communist_effects.txt`、`events/stalin_form_sov.txt` |
| 释放／政府／每日钩子 | `common/on_actions/GRU_red_germany_on_actions.txt` |
| 59 节点国策 | `common/national_focus/GRU_red_germany_focus.txt` |
| 重建决议与决议组 | `common/decisions/GRU_reconstruction_decisions.txt`、同名 categories 文件 |
| 重建数值与结算 | `common/scripted_effects/GRU_reconstruction_effects.txt`、`common/scripted_triggers/GRU_reconstruction_triggers.txt` |
| 事件 | `events/GRU_reconstruction_events.txt` |
| 精神与简中显示 | `common/ideas/GRU_red_germany_ideas.txt`、`localisation/simp_chinese/GRU_red_germany_l_simp_chinese.yml` |
| 回归检查 | `tools/test_red_germany_integration.py`，登记在 `diplomacy` 检查组 |

用户提供的压缩包只有成品脚本和简体中文文本，没有其 README 所述的外部生成器与检查器。本次不引入那个 README 中的个人机器路径，也不覆盖本模组的 README 或 descriptor。导入脚本作为当前维护源，后续修改直接维护上述文件并执行本仓库的检查；原包 59 个国策节点、连线和奖励保持原样，树级字段只修复内战重置键的拼写。

参考了已安装 KR 的 `common/scripted_effects/GRU effects (Germany, puppet).txt`、`common/national_focus/GRU focus (German Republic).txt`、GRU ideas 文件、`common/countries/cosmetic.txt`、政府判定脚本及 KR 汉化 `GRU - German Republic l_simp_chinese.yml`。内战参数另对照本机游戏 `documentation/effects_documentation.md` 与 `events/AAT_Sweden.txt` 的 `AAT_Sweden_communism.4`：`ideology` 指定叛军，`ruling_party` 指定原国家的执政党。

## 验证与游戏内验收

```powershell
python tools/test_red_germany_integration.py
python tools/validate.py --group diplomacy structure
```

测试直接解析并执行本次脚本，覆盖固定／动态标签、非目标国家、俄罗斯路线判定、延迟期间失去资格、战争结束、政府钩子重入、重复释放回调、普通傀儡不回归、所有国策奖励、互斥路径可达、数值边界、投资成本与冷却、破坏脉冲、大选分支、奖励只结算一次，以及内战与待办／已弹出的选举相撞。另检查导入脚本的比较符，将条件名称与本机游戏文档及本模组 scripted triggers 核对，并测试三个镇压选项在政治点不足、恰好 15、超过 15 时的可选性和实际扣费。它不是 HOI4 引擎测试，不能代替领袖、国旗、国策布局和真实释放链的游戏内验收。

重新启动开发版，用新存档让共产主义路线俄罗斯释放 GRU，停战后推进一至两天，核对国名、现任领袖、共产主义 55% 支持率、新国策树和重建决议。持续推进 20 天检查破坏事件；完成重建、安排大选，或提高两派影响力检查内战。

必须完全退出并重新启动游戏，才能重新读取修正后的事件文件；只回主菜单或读档不足以验证这次解析修复。启动后先检查新 `logs/error.log`，应不再出现本文件的 `Invalid trigger 'political_power'` 及后续事件的连锁解析错误。

已有一个 GRU 国家时，可用原包调试事件快速查看内容（也可用于本次错误已经留下接管排队旗标的测试存档）：

```text
event GRU_reconstruction.99 GRU
```

该事件只接受 `original_tag = GRU` 的国家，不能创造不存在的国家。若 KR 使用的是动态标签，将最后的 `GRU` 换成实际 `Dxx` 标签。该调试入口绕过宗主国和停战要求，只适合测试；重复调用不会重置国策与进度。
