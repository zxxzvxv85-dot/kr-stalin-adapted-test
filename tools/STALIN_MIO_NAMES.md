# 斯大林上台后的军工机构名称

用户最新飞机映射（2026-10-19）：OSOAVIA→伊留申，Sokol及两个衍生→拉沃契金，TsAGI→图波列夫与佩特利亚科夫联合，Gamayun→苏霍伊，Duks→米高扬-格列维奇；均保留“设计局”完整称呼。只调整名称源，不交换实际机构/特质/数值或改名门槛，介绍正文保留历史内容，提取TXT按新映射刷新。

用户最新简化：OKMO批准名称改为“莫洛佐夫机械制造设计局”，不带“哈尔科夫”，机构/整合/对应改进特质同步。`extract_rus_mio_introductions.py`默认只读，`--write`输出29个RUS机构的中文类型/介绍TXT及来源JSON至`output/rus_mio_introductions_20261019`；正文沿用现有本地化，不随名称擅自重写。25条有正文，4条无正文注明；两个索科尔分支保留并标识继承关系。

用户2026-10-19提供23项名称映射，并要求之前的对应特质一起改名。来源为`design/RUS_stalin_mio_names.json`；索科尔的建设/生产衍生机构沿用同一新名称，共处理25个实例。含企业旧名的15种原厂特质标题映射在`design/RUS_stalin_mio_trait_names.json`。

同日装甲总局接入后，条件整合标题/停用名称从兵器五家扩为两总局十二家；共用相同企业名称源。原厂特质/修正仍不因改名而改变，七家装甲原厂的新增合并可用性门槛由装甲总局生成器独立维护，名称测试只放行这七个精确门槛，其他字段仍逐AST对照。

实机修正（同日）：用户确认整合特质标题把`[RUSStalinMioMerge_okmo]`原样显示，但悬浮正文Company函数可解析。12个总局整合标题现由各自生成器从本名称JSON直接生成中文；它们只在斯大林路线后段解锁。Merge函数和中间键已删除，Company函数保留用于正文。不要重新给这些特质标题接动态函数；检查新增12个字面标题断言。本次键/特质ID不变，重启可继续已有总局存档，显示仍需用户实测。

## 入口与边界

- `generate_stalin_mio_names.py --write`生成专用效果、触发器、日常钩子、条件本地化、三语本地化，并只给`stalin_form_sov.5.b`末尾追加一次隐藏改名调用；默认及`--check`只读。
- `RUS_stalin_mio_names_active`要求RUS且斯大林现任或已有`RUS_stalin_ml_promoted`/`RUS_stalin_communist_path`。旗标表示已经上台，后续换领袖仍保留工业命名；其他国家和上台前不触发。
- 效果要求AAT并逐个确认MIO实例存在，只用原生`set_mio_name_key`。不创建新实例，不转移经费/等级，不动特质、方针、任务、科技或原国策树。
- 事件立即应用；`on_daily_RUS`正常维护名称，覆盖以后原生工厂培养或国策另行改名。已有实例的斯大林存档在完全重启后下一游戏日可接入，不需要补建MIO目录或增加迁移标记。这不解决旧档缺失总局/方针资格的问题，后者仍需新档。
- 15种原厂标题使用引擎原生`RUS_<原name键>`优先级，条件本地化在MIO作用域用FROM检查所属国家；不覆盖全局共享`KR_MIO_Trait_*`，不改原MIO定义。重复培养的同名各档自动沿用。
- 总局五家整合节点及原厂停用提示使用相同条件名称；总局生成器和预览spec同步。图拉名称不变。历史企业介绍不是特质标题，保留原叙事；英俄未获得新译名，保留原KR名称回退。

## 参考与验证

- 本机游戏`documentation/effects_documentation.md`的`set_mio_name_key`、`common/military_industrial_organization/organizations/_documentation.md`的TAG前缀查找和MIO作用域/FROM说明。
- 本机KR `common/national_focus/RUS focus (Russia).txt`的社会主义工业改名、`RUS_organization.txt`的原始name和trait、`RUS scripted_loc (Russia).txt`的动态MIO名称；2946487287简中原厂“改进…”标题。使用同类原生方式，不擅自改效果文案。
- `validate.py --group mio opening`登记两项新检查。模型覆盖23+2实例、上台前后、仅原KR改名旗标、其他国家、缺少DLC/实例、重复应用及后续原生改名；确认经费、等级、任务、方针和原MIO完整AST不变，事件只追加指定调用；检查五家整合提示、15种条件标题、生成一致性、BOM和重复键。
- 2026-10-19：7/7静态/模型检查通过，运行结构392脚本/268本地化零错误。RHoiScribe新增专用文件及本地化绿色，事件的自定义效果/人物索引诊断按定义复核；项目无括号/未闭合块阻断。项目将跨语言同名本地化误报重复、把scripted_loc函数name误报缺本地化，未据此改正常定义。repair dry_run零建议/零修改；Git空白检查通过。
- 用户自行实测；本轮不操作正在运行的游戏。需重启查看MIO列表、特质标题及效果悬浮，尚未以最终版本进行实机验收。只开发测试目录，不构建上传、不推送GitHub。
