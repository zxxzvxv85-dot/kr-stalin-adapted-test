# 彩蛋顾问（测试开发版，2026-11-04）

玩家俄罗斯开局可在决议栏“彩蛋”分类点击“邀请苏北辰”、“邀请larruping”、“邀请米娅”和“邀请心”。解锁和政治顾问任命均为0政治点；决议只解锁、不自动任命，不替换已任命的顾问。角色未通过对应决议解锁前不显示，AI不点。

列宁复活线路入口和启用简易模式也归入本分类，保留原决议ID、费用、一次性状态及效果。原分类的身份/路线限制保留在共享分类或各自决议中；不启用任何选项时不改变开局。所有入口消失后，空分类自动隐藏。列宁复活入口仍由import_lenin_revival.py生成；简易模式入口为原手写脚本，不新增效果副本。

| 顾问 | 特质 | 效果 |
|---|---|---|
| 苏北辰 | 制作组最锋利的剑 | 陆军攻击+20%、战场宽度-20%、补给消耗-20%、陆军组织度+20% |
| larruping | 赌徒 | 任命期间扫雷失败按成功结算；每局斗地主初始手牌保证四张2和大小王 |
| 心 | 自刎归天 | 组织度低于25%时的组织度损失-100% |
| 米娅 | 最强菜花蛇 | 任命期间每月土改分数+100；任命期间每次正常完成教育改革决议，永久为教育改革精神追加科研速度+5个百分点，无额外上限 |

米娅的月度奖励复用RUS_agri_credit_score，只在土改管理已启用且土改进行中或已成功时入账；土改未开启或失败不补发，完成后的超额分数按现有农业账本转为可支配收益。教育奖励接在53项活动/热情调节决议的正常完成守卫内，开工不发、取消不发、完成一次只发一次；不受教育收益倍率、原永久池科研上限或卸任影响。独立累计RUS_edu_mia_permanent_research，在教育改革本体每次刷新时加入科研速度，不另挂顾问动态精神；卸任后已获收益永久保留。完成当时须任命米娅，未任命时完成不追补。分类和分页按钮不计。完成效果以只读RUS_edu_mia_reward_preview原生预览显示+5%科研，该预览永不实际附加。

米娅使用用户2026-11-05提供的黑白人物图，裁剪215,0,1040,1080后按同一KR模板输出65×67 RGBA；三段介绍逐字保留，沿用黄色“背景：”及浅褐色正文。

苏北辰使用用户最终替换的军装人物图`4cdc0f60e2525ec01392198bf1530e0e.jpg`，不保留第一次白帽头像。larruping使用用户提供的钉子立方体图片。两个运行时头像均为65×67 RGBA，复用`art_templates/KR_advisor_frame_bukharin_260x268.png`及`Build-KRAdvisorPortrait.py`原流程（裁剪、灰度、透视、透明相框、缩小）；没有调用图生成或重绘角色。

原图、裁剪参数、SHA和显式重建入口在`art_sources/easter_egg_advisors_20261104/`；运行时PNG为`gfx/interface/advisors/RUS/RUS_su_beichen.png`和`RUS_larruping.png`。预览为`art_previews/RUS_easter_egg_advisors.png`，是游戏原生尺寸的4倍最近邻放大，不代表另一个高清游戏贴图。

## 生成和结算

- `generate_easter_egg_advisors.py`维护11份人物、特质、决议、分类、解锁效果、月度钩子、动态修正、GFX与三语本地化；默认只读，`--write`更新。图片只在`art_sources/easter_egg_advisors_20261104/build_portraits.py --write`显式重建，正常文本检查不重新绘图。
- 角色为独立`RUS_egg_*` ID，只有political_advisor角色，不添加领袖/将领，不覆盖既有人物或头像。解锁效果由国家身份、AI及一次性旗标保护，recruit_character只执行一次。
- 特质使用原生`army_attack_factor`、`combat_width_factor`、`supply_consumption_factor`、`army_org_factor`。参考KR political/theorist traits、现有RUS顾问和原生modifier文档。解锁提示沿用KR `available_political_advisor`及`show_ideas_tooltip`，不手写数值效果。
- 独立彩蛋顾问保持用户指定数值，不由简易模式顾问扫描器再加副本；既有普通顾问的简易加成保持原样。
- larruping通过`has_idea = RUS_egg_larruping_advisor`判断实际任命，单纯解锁不生效，解雇后恢复正常。`generate_tesla_minesweeper.py`先生成原结算体，再加active守卫；失败入口在任命时调用原胜利入口，胜利/失败重复回调均不重复领奖。原连胜奖励、随机合格州电网建设、简易模式奖励和60日维护不改。
- 检索现有扫雷逻辑只有踩雷失败入口，没有超时失败；关窗保留在建牌局，不视为结算。不自动解锁原特斯拉扫雷入口，不追溯补发旧局奖励。

## 验证和实测

`python tools/test_easter_egg_advisors.py`执行实际解锁/结算脚本，覆盖解锁防重、特质数值与图像绑定、正常成功/失败转换、未任命、解雇、踩雷点击、关窗、无可领奖地区、60日维护及重复领奖。扫雷原奖励体与其他规则AST对照本次修改前已审核提交`fcb5531`，基准固定以便提交后仍能检查。

还须检查两个生成器`--check`、`check_runtime_structure.py`、RHoi单文件及repair dry_run。静态/模型检查不替代实机：完全重启并用新局查看彩蛋分类、顾问列表/头像、任命/解雇后特质和踩雷结算，并按最新error.log核验。

## 心（2026-11-06）

“心”使用独立RUS_egg_xin政治顾问及RUS_egg_xin_trait，原生org_loss_at_low_org_factor=-1。原版英文MODIFIER_ORG_LOSS_AT_LOW_ORG_FACTOR说明为Organization loss when below 25%，简中为“组织度低于25%时的损失”；参考KR KR_high_command_traits.txt、01 Army Spirits.txt及本机modifier文档，不另写轮询单位组织度的脚本。数值和效果文字由引擎显示，沿用免费解锁后手动任命；不添加常驻精神或额外钩子，不被简易模式复制数值。

用户提供的两段介绍逐字保留，沿用黄色背景标题和浅褐色正文。原PNG归档xin_source.png，裁剪170,25,500,490并复用已有KR框，运行时65×67 RGBA，四人预览1200×344。仅确定性裁剪/灰度/透视/框，不调用图生成；其余三人运行头像字节不变。斗地主名单按现有生成源追加这一解锁人物，不改发牌、牌型或奖励。
