# 临时政府工业面板退役（2026-11-06）

按用户截图移除整个临时政府工业场景、在建/竣工计数、四类工程台账，以及顶部经济复苏介绍。工业项目分类取消scripted_gui，亦不换成固定图片或占位容器，直接显示原生决议列表。

同时去除原决议上的RUS_rc_show_*筛选条件和“显示全部工业工程”操作。既有存档即使留有RUS_rc_filter数值也不再隐藏项目；没有新增迁移脚本。原解锁条件、政治点费用、计时、取消及奖励保持。开始/结算/取消的轻量标记保留，尤其RUS_rc_finished_*仍供新一五避免重复领取旧工程奖励使用。

每日GUI统计、原生计时读取、图片帧更新和UI按钮均停止注册。自有GUI/GFX/scripted_gui/on_actions/本地化输出为空声明或注释，防止旧文件残留；生成器不再重建面板。旧素材及provenance留档，prepare_dynamic_industry_assets.py仍仅为归档素材工具，不被文本生成器调用。

维护入口仍为generate_provisional_industry_gui.py和generate_national_plan.py组合入口；provisional_industry_dashboard.py现在只维护工程完成标记。新一五的资源账本、六地区分类、62项工程与倒计时保留，斯大林阶段识别保留。national_plan.native_base仅剔除冻结目录里的旧GUI刷新调用；不改原奖励和评分。

原生参考：已安装KR common/decisions/categories/00 Generic decision_cats.txt中不带picture/scripted_gui的原生分类。检查：5项界面退役回归比较删除前原玩法AST（只豁免旧筛选/刷新/overview）、分类无占位、无悬空筛选、46项完工记录、账本与生成一致性；另跑27项国家计划回归、结构检查与RHoi审计。游戏内需完全重启后确认决议栏不再保留原574px面板空间。

仅测试开发目录；上传目录不自动同步。
