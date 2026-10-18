# RSFSR路线展示入口

用户要求有趣国家页的中间介绍卡片展示斯大林、钢铁之心、第五面苏俄旗和列宁背景；进入地图选国应显示萨文科夫，实际开局始终走现有RUS共和国。

- 来源：tools/design/RUS_rsfsr_bookmark_20261018.json；生成器generate_rsfsr_bookmark.py默认/--check只读，--write更新8份文本并删除7份已废弃RSB文件；test_rsfsr_bookmark.py登记于validate.py --group opening，依赖本机KR与游戏原版。
- 中间第7槽直接绑定RUS，右侧原RUS书签保持上游内容，两个入口都选择拥有实际领土的RUS。完全删除零领土RSB标签、国家定义、历史、旗帜副本和on_startup切换脚本；没有玩家切换、观察者切换、政府重置、领土借用或进游戏后修补。
- 展示人物RUS_rsfsr_stalin_showcase属于RUS，本体只有name和portraits，没有country_leader、advisor、corps_commander等任何职务。RUS历史末尾由独立标记包围的唯一recruit_character登记此人物，不修改真实RUS_iosif_stalin、萨文科夫、执政党、党派支持率或任何游戏数值。参照本机原版JAP_emperor_hirohito：同样没有领袖职务，历史中登记，书签override_leader_portrait显示其画像。
- 书签的override_leader_portrait现在指向已登记的展示人物；此前直接指向未登记的原斯大林导致覆盖未生效。展示人物使用独立姓名本地化别名，配套_override_instant=钢铁之心、_override_delayed为空，参考原版core_l_english.yml的Hirohito专用提示模式；不再显示原始键名，也不授予真实领袖任何额外特质或数值。
- 第五旗只在介绍卡片固定位置绘制，源为现有medium/RUS_sov_5.tga放大两倍，再叠原版82×52的flag_overlay.dds布面，二者穿透鼠标。保留原生头像按钮和外框状态。没有生成或修改光栅素材。
- 地图选国窗口gamesetup_country_details以及介绍页之外的全部GUI块与KR上游AST一致，不加斯大林覆盖；地图选国与游戏读真实RUS，故应显示萨文科夫、共和国党派和三色旗。介绍卡片使用斯大林展示头像与专用悬浮；原生共享资料栏的具体显示仍需实机核对，不承诺普通bookmarks字段能独立覆盖同一国家的全部资料。
- 两行标题172×38、8像素九宫格边框并裁切；列宁原画等比裁切；coverup_3只遮y241..318下方AAA，背景原点和缩放连续；其他列保持不变。
- 生成器与Savinkov开局生成器共同涉及RUS历史，但分别只重建自己拥有的标记区域，其余字节保留；两个--check均须通过。默认检查不删除废弃文件，发现遗留会报STALE；显式--write只删除固定列出的本功能废弃路径。
- 回归检查真实RUS入口有领土、原执政党、无RSB/切换钩子、地图GUI不变、展示人物无职务且已登记、专用提示齐全、旗帜布面、标题及占位遮挡。静态检查不能代替真实选国流程。
- 本轮修复以新开局为准，不迁移已通过RSB启动的观察者存档。当前界面可先手动点击地图上的真实俄罗斯，确认萨文科夫/三色旗后开始；更新后完全重启，从中间卡片到地图选国再到正式开局验收，并确认可以操作RUS单位与政治界面。只开发目录，不构建上传、不推送GitHub。
