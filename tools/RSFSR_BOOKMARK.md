# RSFSR路线展示入口

用户20261018要求在选国界面中间列增加“俄罗斯苏维埃社会主义联邦共和国”，斯大林头像、现有列宁原画背景及截图中的第一段历史简介；随后明确实际入口仍是俄罗斯共和国。

- 生成源：`tools/design/RUS_rsfsr_bookmark_20261018.json`。
- 生成器：`tools/generate_rsfsr_bookmark.py`，默认/`--check`只读，`--write`更新6个文本运行文件。
- 检查：`tools/test_rsfsr_bookmark.py`，已注册`validate.py --group opening`。
- 使用KR原`the_gathering_storm.txt`的第7个主要国家槽（从0计为6），替换中间上方AAA占位。实际国家标签仍为RUS；右侧原RUS条目和其余所有条目保持原样。
- 展示条目采用`ideology=totalist`及原生`override_leader_portrait=RUS_iosif_stalin`；后者参考本机原版日本书签同类属性。书签effect完全不变，不增国家、不转移省份、不修改国家历史、实际政权、领袖或国旗。
- 中间背景复用`GFX_RUS_intro_lenin_painting`原图，采用等比例GUI裁切，隐藏原中央KR标志。只有该卡片叠加被动标题与用户最新指定第五版`RUS_sov_5`旗帜；使用本地文案避免修改全局RUS国家名，所有原生country点击控件仍保留。三语两项文字均有UTF-8 BOM。
- 必须隐藏同窗口中的`coverup_3`：KR在国家网格之后用此172×192遮罩盖住原本空白的中间两格。仅隐藏KR标志或替换底层背景，仍会遮住整个新卡片。回归按原生遮罩的绘制顺序及矩形范围检查，保留遮罩节点但设置`hide=yes`；其他列遮罩不动。
- 预览布局图在`output/rsfsr_bookmark_20261018/`，仅用于原尺寸排布检查，不是游戏运行截图。需要重启后确认重复RUS展示条目在引擎中的选择、肖像和简介绑定。
- 当前只开发目录；未经用户另行要求，不同步上传目录，不推送GitHub。
