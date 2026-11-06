# 社会主义俄罗斯专属征兵法案（2026-11-06）

仅测试开发目录。用户确认六档数值、国策/投降度自动交接、德国消失后的手动范围；后来明确第2档为全军训练时间-20%，自动切换免费，手动基础花费150政治点。经济法案《全俄工农国防动员令》不属于此次修改。

## 来源与生成入口

- `generate_socialist_conscription.py` 维护六档法案、调度、钩子、补给技术、三语、图元及三个既有国策的追加调用。默认/`--check`只读，`--write`生成；不在导入时写盘。
- 原生参照：KR `common/ideas/00 Laws.txt`、`00_laws_scripted_effects.txt`、`00_hidden_tech_effects.txt`、`common/units/infantry.txt`、`common/units/unit_modifiers/unit_modifiers.txt`；原版64×64征兵图标及effects/modifiers文档。
- 生成 `common/ideas/00 Laws.txt` 的目的仅为给七项通用征兵法案加入 `visible = { NOT = { RUS_sc_context = yes } }`。其他法案字段逐字保留KR源；测试按AST核验经济/贸易和原征兵数值、条件均未改。KR升级后重新生成并审查差异，不手工维护一份脱离来源的法案表。
- 六项新法案独立为 `RUS_sc_volunteers/territorial/universal/wartime/extended/emergency`。`allowed`仅用稳定的`original_tag=RUS`，政体采用动态`visible`。萨文科夫时期仍用原七档，其他国家不显示新法案，也不获得新修正。

## 数值与切换

精确数值见生成源STATS；基础适役人口依次3%/2.5%/5%/7%/15%/25%，保留用户设置的第一档高于第二档，不自动“校正”。普遍义务兵役组织恢复为-15%（虽写在用户表格正面列，按实际负号执行）。第5/6档经济惩罚沿用KR-30%/-40%的工厂、船坞产出和建造速度。战争稳定度惩罚增加20%/50%/80%对应`war_stability_factor=-0.2/-0.5/-0.8`，该字段正数为减轻惩罚。

1. 进入社会主义俄罗斯采用第1档；同日已有后续国策则按已完成进度接续。
2. `RUS_fr_post_revolutionary_armed_forces`（革命后的武装力量）→第2档。
3. `RUS_fr_general_staff_experimental_formations`（严格训练制度）→第3档。
4. `RUS_future_foreign_062`（最后的斗争）→第4档。
5. GER存在期间，投降度严格大于0.20优先第5档，严格大于0.50优先第6档；恰好20%/50%不提前越级。恢复后回到当前投降度及已完成国策对应档，不额外设置永久危机锁。
6. GER不存在（不以投降代替灭国）后只开放第2/3/4档手动选择，不附加旧战争支持度/敌我强弱/国策门槛；当前在1/5/6时退出这些档，按正常进度转入2—4。每天不覆盖已手动选中的2—4档。

自动切换不扣政治点；三项可手动法案均设置原生基础`cost=150`，沿用原生法案界面及既有价格修正。自动检查只在需要换档时`add_ideas`，同组替换，不叠加六套修正。退出社会主义路线则换回对应通用法案，不给其他国家设置默认值。

三个国策追加小型交接helper，先提供受条件保护的原生法案效果预览，再隐藏设置里程碑并刷新，保留原奖励。里程碑解决completion_reward执行时完成标记尚未可读的时序；每日和政府变更钩子补充核验，危机档优先，完成低级国策不会压掉高级档。

民兵攻防/组织度使用原版已登记的`modifier_army_sub_unit_militia_*`，不把定向奖励误发全军。第1/2档沿用KR的`unlock_subunit=militia`使民兵实际可用。地域兵役的民兵补给-15%由不可研究、无弹窗的国家局部技术提供，切档撤销，反复刷新不叠加；第2档训练时间已按用户确认使用全军-20%。

## 图标与制作记录

- 内置`image_gen`逐张生成六个完整图标，工具未报告具体模型，不使用CLI/API。完整提示词、生成源路径见`tools/design/conscription_20261106/generated_sources.json`；生成原图已复制到同目录，各以`*_generated.png`留档。
- 用户后来要求使用素材库现成金属框，故显式允许拆框与合成。选用霜泽美术馆`3473772709/通用-素材合集/图标素材合集/素材合集－图标框（一）.PNG`第四枚圆框的金属环，源目录只读。坐标和输出SHA在`asset_manifest.json`。
- `build_socialist_conscription_icons.py --write`复用完整生成主体、替换生成框，人物对比度1.45/饱和度0.90，不锐化，保留柔化手绘轮廓；最终64×64透明DXT5 DDS。图元单独命名`GFX_idea_RUS_sc_*`，不覆盖任何共用图标。
- `native_size_comparison.png`上排原版、下排本轮，已查看64px轮廓、框与明暗；正式游戏中的选中/缩放效果尚需用户确认。

## 验证与限制

`python -B tools/generate_socialist_conscription.py --check`和`python -B tools/test_socialist_conscription.py`。15项模型测试执行实际生成调度，覆盖身份隔离、顺序/跨级国策、20/50严格边界、危机优先、恢复、无重复扣款、战后手动保留、补给撤销、源数值/原法案/原国策保留与图标格式。模型不是引擎实测。

`test_final_struggle.py`同步执行新增第4档helper，再验证原事件及战争目标；`test_military_refactor.py`检查原31项军备及整顿时序保留。结构/本地化扫描、RHoi单文件与修复dry-run另行执行。RHoi对未解析脚本helper产生CW263及外层CW262级联，递归展开已定义helper后的只读验证区分真实结构/字段问题，不改游戏源去迎合诊断。

仍需完全重启新局，实测转红当日法案切换/隐藏、国策完成即时交接、投降度变动、GER灭国后的手动费用与保留、民兵补给撤销、陆军HP/组织度及图标。未操作游戏，未构建上传目录、未推送GitHub。

本轮结果：15项专项、原军改及最后的斗争回归通过；12输出一致，499脚本/325本地化结构0错误；修复dry-run166建议未应用且无红项。项目级validate_hoi4_project调用300秒超时，未取得完整结果；新法案与效果递归展开helper后的原生字段校验绿色，其他相关单文件绿色。不能将上述静态/模型结果视为引擎或完整项目验收。
