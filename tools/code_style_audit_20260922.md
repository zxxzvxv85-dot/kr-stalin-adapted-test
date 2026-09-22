# 测试版代码规范扫描：2026-09-22

## 范围与限制

扫描当前测试版全项目索引（1238 个文件、19291 个定义、34528 个引用），运行 RHoiScribe legacy 验证及只读修复预检，并人工对照 KR 决议范例。未运行游戏；并非逐个国策、事件及所有界面的游戏内验收。

## 发现

1. **农业兑换回归测试已过时，需要更新。** `tools/test_agri_development.cjs:464` 仍要求 `RUS_agri_exchange_rations_effect_tt` 等旧手写提示键。当前决议已改用原生 `effect_tooltip` 中的 `add_timed_idea`，对应旧键已删除。测试前面的付款、名额、援助、季度结算等16项通过，最后本地化断言失败。应改为检查当前引用及原生展示，不应为了测试恢复旧手写效果。
2. **军事改革存在两套推进代码，需复核可达路径。** `common/national_focus/RUS focus (Russia).txt` 约30407行起仍有按国策天数扣物资并即时完成的代码；`common/scripted_effects/RUS_fr_auto_focus_effects.txt` 仍有按固定物资启动、通过事件计时完成的代码。顶部提示只介绍前一种。不能只凭两套代码存在就断言重复执行；需逐一确认触发与入口，再决定删除旧路径或调整提示。
3. **土改兑换当前展示已符合此次要求。** `common/decisions/RUS_agri_development_decisions.txt` 以 `effect_tooltip` 展示原生限时民族精神，实际发放在付款成功后的 `hidden_effect` 中；中文描述只保留叙事。无需重新手写修正名称和数值。

## 排除的误报

- 验证器把 `enable`、`set_variable`、`targeted_modifier` 等嵌套语句当作重复定义；不能批量改名。
- 报出的5个缺失纹理均实际存在于游戏本体 gfx 目录，包括 artillery_regiments、rocket_bonus、FRA_motorized_focus、helicopter_1、ARMY_SPEED_FACTOR；属于扫描只含测试版根目录的依赖遗漏。
- 其余缺失引用及重复定义需结合 KR、本体与其他依赖逐项归类，原始告警数量不等于实际 bug 数量。

## KR 参考

- `1521695605/common/decisions/BUK decisions (Bukhara).txt:347`：原生 `add_timed_idea` 显示民族精神及期限。
- `1521695605/common/decisions/01 Central Asia decisions.txt:259`：`effect_tooltip` 展示效果，避免把执行与说明混为一体。

本次为扫描与规范落盘，未批量修改游戏逻辑或数值。
