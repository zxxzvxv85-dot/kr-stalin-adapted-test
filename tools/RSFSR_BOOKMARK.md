# RSFSR路线展示入口

用户20261018要求在选国界面中间列增加“俄罗斯苏维埃社会主义联邦共和国”，斯大林头像、现有列宁原画背景及截图中的第一段历史简介；随后明确实际入口仍是俄罗斯共和国。

- 生成源：`tools/design/RUS_rsfsr_bookmark_20261018.json`。
- 生成器：`tools/generate_rsfsr_bookmark.py`，默认/`--check`只读，`--write`更新6个文本运行文件。
- 检查：`tools/test_rsfsr_bookmark.py`，已注册`validate.py --group opening`。
- 使用KR原`the_gathering_storm.txt`的第7个主要国家槽（从0计为6），替换中间上方AAA占位。实际国家标签仍为RUS；右侧原RUS条目和其余所有条目保持原样。
- 展示条目采用`ideology=totalist`及原生`override_leader_portrait=RUS_iosif_stalin`；后者参考本机原版日本书签同类属性。书签effect完全不变，不增国家、不转移省份、不修改国家历史、实际政权、领袖或国旗。
- 用户实机确认重复RUS卡片仍读取萨文科夫，不能只依赖书签头像覆盖项。中间卡片在国家网格之后显式绘制`GFX_portrait_RUS_iosif_stalin_civilian_large`，位置537/141、比例0.3072，与KR原生country_leader一致；图像为156×210不透明RGB，完整盖住该卡片原头像，标题在其后绘制。图标alwaystransparent=yes，保留下层选择按钮，不修改共用country_entry或右侧俄罗斯卡片。
- 中间背景复用`GFX_RUS_intro_lenin_painting`原图，采用等比例GUI裁切，隐藏原中央KR标志。只有该卡片叠加被动标题与用户最新指定第五版`RUS_sov_5`旗帜；使用本地文案避免修改全局RUS国家名，所有原生country点击控件仍保留。三语两项文字均有UTF-8 BOM。
- `coverup_3`只遮下方占位格：原KR的172×192遮罩同时盖住中间两格，全部隐藏又会露出下方AAA的灰色头像和“可整合领土”。现将遮罩限于y241..318，使用与列宁背景同原点、同比例的原画；y222..241由上方两行标题覆盖。回归检查上方卡片不被遮住、下方占位格全部覆盖及原画连续；其他列遮罩不动。
- 两行标题使用独立`corneredTileSpriteType`，复用原版`tiled_paper_bg2.dds`但将边框设为8像素，标题容器裁切为172×38。原版同名底板的64像素边框不能用于38像素高度，会撑出大块黑底。未新增或改绘光栅资源。
- 预览布局图在`output/rsfsr_bookmark_20261018/`，仅用于原尺寸排布检查，不是游戏运行截图。需要重启后确认重复RUS展示条目在引擎中的选择、肖像和简介绑定。
- 当前只开发目录；未经用户另行要求，不同步上传目录，不推送GitHub。
