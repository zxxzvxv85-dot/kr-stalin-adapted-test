# 临时政府工业 GUI（2026-11-01动态版）

只开发测试版第一阶段；正式版与两版上传目录不包含本轮改动。旧debug工业沙盘保留原状态。

## 入口与交互

人类俄罗斯进入社会主义/共产主义政府、斯大林尚未执政时，在原“工业项目”决议分类显示。504×574窗口包括原492×394厂区、危机缓解刻度与四张工程台账卡。点击文件/厂房/机车/吊机及台账卡只筛选原生决议，关闭筛选查看全部；不会支付费用、开始工程或授予奖励。“施工图”按钮切换为使用霜泽小素材组成的四部门工程板，仍可分别点击。两个视图共用真实统计。

厂区3帧：黑色星期一5/6级为停工，3/4级为恢复施工，1/2级及危机已解除为复产；有任一统计内项目在建时优先显示施工画面。危机条按实际六级精神显示7个刻度。它们是委员会辖区的概览，不代表图中每座设施已经按地块逐一建成。没有假设新产业链、生产量或损坏系统。

46项已有定时工程的剩余天数由引擎days_decision_timeout@ID读取；每帧用scripted GUI triggers/_临时变量重算各组与总在建数、最近竣工天数，无新增每日on_action。竣工数是项目种类数；原remove_effect末尾仅追加hidden_effect中的RUS_rc_finished_ID标记，重复电气化不重复累计种类。未改费用、原耗时、奖励、解锁、AI、取消或目标地块。原脚本自然结算仍由原生决议处理，不把预览国策开放。

在建组显示旋转齿轮，道路施工时厂区显示轻微烟尘循环。frameAnimatedSpriteType参考KR interface/core.gfx，变量选帧参考KR奥斯曼scripted GUI，动态image参考KR塞尔维亚GUI；计时字段以安装游戏documentation/dynamic_variables_documentation.md为准。用户负责重启新开局实测；临时变量在真实界面刷新、点击alpha命中、动画和分类高度尚不可由离线预览证明。

## 素材与生成

四张霜泽图标合集拆为45页、2797个连接图块逐页查看（含重复及少量相邻聚合），编号和完整预览保存在工作区output/provisional_industry_dynamic_20261101/catalog。12项选用素材的原图、坐标及SHA在tools/design/provisional_industry_20261101/library_sources.json；煤堆单独裁掉下方鱼图案。工程板使用厂房、吊机、煤、砖料、木箱、工具和蓝图，台账使用金钱、厂房、蓝图和工具，计时钟、齿轮、烟尘与边框也来自该馆；金属底纹来自纹理（五）。未修改3473772709订阅目录。

两张厂区状态图通过内置image_gen编辑既有20261030混合素材场景；准确提示词、工具、尺寸、SHA见同目录provenance.json。复产沿用原场景，停工/施工保留主体位置。prepare_dynamic_industry_assets.py只进行素材打包、透明点击图、原素材组合与12帧动画打包；--check默认只读，不调用图生成。原静态资产保留，动态资产位于gfx/interface/RUS_provisional_industry/dynamic。

文本入口仍为generate_provisional_industry_gui.py，动态扩展在provisional_industry_dashboard.py。其他生成器改写同一决议文件后需重新运行；标记块幂等维护，默认只读。新开局为基线，不为旧存档推测补发竣工记录。

## 验证与预览

运行test_provisional_industry_gui.py（7项，含原玩法AST保持、46项计时的28种边界组合、三帧点击像素一致与生成幂等）、check_runtime_structure.py、generate_provisional_industry_gui.py --check、prepare_dynamic_industry_assets.py --check。

output/provisional_industry_dynamic_20261101/工业复兴委员会_交互预览.html可离线切换两视图/三状态并点击设施；6张PNG和GIF来自实际GUI坐标与资源的离线渲染。数字为演示值，预览不是游戏截图或运行时验收。
