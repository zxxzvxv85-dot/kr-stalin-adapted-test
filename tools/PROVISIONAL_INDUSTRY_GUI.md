# 临时政府动态工业GUI（2026-11-01实测修正）

只改测试版开发目录。人类社会主义俄罗斯、斯大林尚未上台时，在原“工业项目”分类显示。保留504×574动态厂区和四张工程台账卡；点击设施/卡片筛选原决议，通过列表中的“显示全部工业工程”恢复全部。已删除黄色选中轮廓、施工图视图、施工图切换按钮、叉号按钮和“黑色星期一：…”状态文字。台账中文使用原生中文覆盖的hoi_16mbs、行高18；铁路图标改用KR现成蒸汽机车（来源见library_sources.json）。

## 数据与分区变化

此前triggers/_临时统计在用户实机没有正常驱动显示，现撤掉该入口。RUS_rc_refresh在国家作用域更新持久UI变量；46项定时工程的complete_effect、remove_effect、cancel_effect分别追加隐藏UI观察块，开始/结算/取消时刷新，global on_daily在人类临时政府阶段校正原生days_decision_timeout@ID。点击设施、台账卡或“显示全部工业工程”也刷新。仅UI命名空间的变量/标记变化，原成本、耗时、解锁、AI及奖励保持。

running/settled标记处理回调与引擎计时增删的先后：刚点击时计时尚未建立也先显示在建；结算/取消回调仍能读到旧正计时时不重复统计；重复开展会清除settled。原生正计时可直接识别已在建项目，不靠猜测补历史完成记录。计时尚未出现时显示“工程启动中”，不会显示0天竣工。已完成数仍是项目种类，不是重复点击次数。

厂区底图仍随实际危机等级选三帧。文件/厂房/铁路/道路分别使用自己的frame变量：本组在建→施工帧，本组已有完成→复产帧，其余使用底图阶段。道路在建显示烟尘，铁路在建显示蒸汽，四组在建显示齿轮。退役的RUS_rc_blueprint_view不再被任何显隐条件读取，因此此前切过施工图也不会导致厂区隐藏。原精神和危机逻辑保持。

## 维护与素材

文本入口generate_provisional_industry_gui.py，扩展provisional_industry_dashboard.py；默认/--check只读，--write显式更新12份输出。素材由prepare_dynamic_industry_assets.py显式打包，默认只校验；旧施工图、按钮和描边图片已停止生成和注册，既有图片留作未引用产物。

四张霜泽主图标合集曾逐页查看45页、2797个图块，所选坐标/SHA在tools/design/provisional_industry_20261101/library_sources.json；本轮铁路追加KR原图。两张厂区状态图由内置image_gen编辑既有混合素材场景，提示词/尺寸/SHA见provenance.json。订阅目录只读。本轮没有生成或重绘图片。

原生参考：KR core.gfx的frameAnimatedSpriteType、奥斯曼GUI变量选帧、00_on_actions_global.txt的on_daily，以及本机documentation/dynamic_variables_documentation.md的days_decision_timeout。

7项专项含原玩法AST、46项计时49组边界（含回调先于计时、结束仍有旧计时）、逐部门帧、三帧alpha像素、幂等及阶段隔离。check_runtime_structure.py检查结构/本地化；RHoi检查相关文件并repair dry_run。用户需完全重启读档后推进一天，核对已在建工程、开始/取消/结束、重复工程、中文、图标与区域变化。静态和模型通过不等于引擎验收；历史完成项目不追补。
