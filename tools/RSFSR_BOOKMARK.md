# RSFSR路线展示入口

用户要求选国中间列展示斯大林领导的“俄罗斯苏维埃社会主义联邦共和国”，使用第五面旗帜和列宁背景；已再次明确仅改展示，进入游戏仍走现有RUS共和国开局。

- 来源：`tools/design/RUS_rsfsr_bookmark_20261018.json`；生成器`tools/generate_rsfsr_bookmark.py`默认/`--check`只读，`--write`更新11个文本文件和3份原旗帜的字节副本。检查为`tools/test_rsfsr_bookmark.py`，登记在`validate.py --group opening`。
- 中间第7个主要国家槽使用独立展示标签RSB，不再重复使用RUS。实际RUS书签、国家历史、政治人物和领土保持原样。RSB没有州、核心、单位、资源或外交关系，仅有展示所需的国家名、共产主义政府、无选举设置、俄共（布）党名及独立角色RSB_iosif_stalin_showcase。
- 展示角色的名字、大小头像、介绍和KR_bolshevik_stalin特质直接引用本模组已存在的斯大林资料；角色ID独立，不招募、转移或修改真实RUS_iosif_stalin。原生country_entry、minor_country_leader、info容器完整沿用KR，因此头像悬浮和下方信息栏读取同一份斯大林资料；原RUS卡片仍读取萨文科夫。
- 第五面旗RUS_sov_5的82×52、41×26、11×7三档文件逐字节复制为RSB.tga。使用原生GFX_shield_medium和原生旗帜布面遮罩，删除此前直接叠加的平面旗帜、斯大林头像及其多余图元；保留原生country按钮的正常、选中和悬浮外框。不生成或改绘光栅资源。
- `common/on_actions/00_RUS_rsfsr_bookmark.txt`在on_startup检查RSB是否为玩家，以`RUS = { change_tag_from = PREV }`把玩家交给RUS。完全参考已安装KR `on_actions_Central_Asia.txt`中KAZ到TRK的作用域与引擎效果，并核对本机effects_documentation.md。只转移玩家，不转移州、部队、科技或政府，不授予奖励，不切国策。00前缀将其放在国家开局钩子之前；普通RUS/其他国家开局和已经交接后的重新加载不再执行。RSB从不获得领土，不能作为真实新国家释放。
- 原生书签effect不变。测试执行实际生成的交接AST，覆盖展示入口、RUS、GER、AFG、无玩家和重复执行；同时验证上游KAZ/TRK参考同构、国家入口及共享控件AST、角色/本地化/旗帜引用和零领土边界。静态模型不能证明零领土展示入口可在当前游戏版本中正常开始，必须重启实机测试原生选国按钮及on_startup交接。
- 列宁背景复用GFX_RUS_intro_lenin_painting并等比裁切。coverup_3只遮y241..318的下方AAA占位，原画原点和缩放与上方背景一致；y222..241由上方两行标题覆盖。其他列遮罩不动。
- 两行标题172×38，底板复用原版tiled_paper_bg2.dds并采用8像素九宫格边框，启用裁切。三语文本UTF-8 BOM。原尺寸排布重建图只作静态检查，不是游戏截图。
- 只开发目录；不构建上传、不推送GitHub。实机验收应分别选择中间RSB、右侧RUS及其他国家，确认资料各自对应；从中间入口开始后应立即控制现有RUS共和国，斯大林展示资料不进入实际政府。
