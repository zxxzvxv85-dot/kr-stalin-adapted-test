# 独立工业规划沙盘维护说明

当前实现：2026-09-30，六区不规则格子厂区、随机矿点与岩壁、21 种设施、七类成品、自动跨区货运、1800 天连续生产与 500 产值目标。旧的 36 经济区地图、地区资金与物流系统已退出当前生成入口；本轮货运是局部厂区沙盘的新模块。

## 唯一生成入口

```powershell
python tools/generate_industrial_planning.py --check
python tools/generate_industrial_planning.py --write
```

默认只检查，不写文件。支持 `--output-root <临时目录>` 独立复现13份文本与11张纯色UI纹理，三语本地化使用UTF-8 BOM。文本允许换行规范化；PNG按二进制原样比较，不转换CRLF。不得直接改生成后的脚本、GUI 或本地化。

- `tools/build_factory_regions.py`：只读 KR 州/省份栅格，量化为六区格子几何与资源参考；仅输出 JSON，不生成或编辑图片。默认检查，显式 `--write` 更新 `tools/data/industrial_planning_factory_regions.json`。
- `tools/industrial_planning_catalog.py`：设施、每级成本、每日速率、每单位投入、地区门槛、矿点配额、产品价格及生产次序的唯一目录。新增矿种或设施先改这里；不能只改 UI 数字。
- `tools/industrial_planning_factory.py`：加载格子定义、建设限制、连接与产能、每日配方、投资退款、计时与重置。
- `tools/industrial_planning_factory_ui.py`：GUI/GFX、三语文本、动态名称、入口与帮助页。
- `tools/industrial_planning_factory_freight.py`：持久线路配置、只读批次预测、到货／发运／期满返还。
- `tools/industrial_planning_factory_freight_ui.py`：运输分页、目的地和货物按钮、线路状态、来货清单。
- `tools/industrial_planning_factory_assets.py`：确定性生成不透明纯色UI矩形，包含36×36等级底色、16×16图例、40×2/2×40选中细框。资产位于 `gfx/interface/RUS_factory_planning/`，经统一生成入口显式写入；没有导入副作用。
- `tools/test_factory_planning.py`：运行生成后的 Clausewitz 脚本，含独立图论判定与守恒检查。
- `tools/test_factory_industries.py`：特色矿点配额、按地区和菜单限制建造、十种材料守恒、成品计价、六区完整产业链与可负担开局。
- `tools/test_factory_freight.py`：执行实际生成脚本，检查货运守恒、持续自动发运、恢复、控制边界和进口材料加工。
- `tools/test_industrial_planning.py`：统一验证保留的入口，调用以上测试。
- `tools/test_factory_layout.py`：引用、三语 BOM/键、字体与资源、按钮绑定、分页残框和沙盘隔离。
- `tools/preview_industrial_planning.py`：读取实际 GUI 与本地素材做布局预览，只写 `output/industrial_planning/`，不是游戏截图。
- 玩家说明：根目录 `工业建设GUI玩法说明.md`。

## 输出与边界

仍生成 `RUS_industrial_planning` 对应的 triggers、effects、scripted_gui、on_actions、scripted_localisation、decisions/category、GUI/GFX 和三语本地化，共 13 份。动态修正文件保留生成声明但没有修正定义。

没有国家工厂/人力/资源占用、领土与铁路调用、债务惩罚，也没有旧一五计划的奖励或入口调用。新游戏是验收基线，不迁移此前地区经营原型的存档。保留测试决议解锁和 raid_filter 侧边独立入口，并保留中欧同盟时的入口避让。

此前 `industrial_planning_economy.py`、`industrial_planning_regions.py`、`industrial_planning_supply.py`、`industrial_planning_supply_ui.py`、`industrial_planning_rail.py`、`build_industrial_planning_map.py` 与旧地图数据、美术仍作为历史参考留在开发目录；当前入口及新六区几何构建器不导入或引用它们。旧 supply/rail 专用测试仅适用于旧实现，不再由当前验证入口调用。正常开发不要运行旧地图的写入命令。需要查回旧实现时可参考提交 `4439a62`；最初五轮原型为 `a0914ea`。当前没有恢复轮数。

## 状态与算法

国家变量前缀 `RUS_ip_`；新初始化标识 `RUS_ip_factory_initialized`。`ui_unlocked` 控制入口、`open` 控制窗口、`started/active/finished` 控制阶段、`help_open` 控制分页。按钮在显示和实际执行两侧都检查窗口、页面及可操作状态。

六区共 851 个有效格子，分别为 112、98、179、143、199、120；索引连续但邻接仅限同区。察里津由92格扩大到179格，纳入KR州217、218、232、233、234、235、236、237、238、245、787、961、1006，覆盖顿河、库班和北高加索；排除229阿塞拜疆、230亚美尼亚、231格鲁吉亚、1080阿布哈兹。需要包含捷列克、车臣和新罗西斯克，避免遗漏新版KR切分出的州而断开腹地。各区形状、尺寸、调度站、12格起步区与不受岩壁影响的连通骨架保存在JSON。每格terrain：0普通、1煤、2铁、3岩壁、4调度站、5铝土矿、6铬矿、7钨矿、8油田。线路应排除terrain=3。type：0空，1—5原设施编号，6—14采矿／加工／发电，15—20六区成品厂，21运输站。当前区域region，所选格selected；rN_selected记住各区上次选择。

煤铁岩壁配额为16/20/10、10/12/8、20/28/16、28/36/16、36/36/20、16/32/20。额外矿点按铝／铬／钨／油依次为0/0/0/0、10/0/0/0、0/8/4/10、6/8/0/4、16/8/0/0、2/6/6/4。`kr_resources`从同一组KR州记录coal、steel、aluminium、chromium、tungsten、oil；察里津新增腹地合计铬57、钨21、油46，配额不等于原生资源数。重新量化轮廓生成更大格网，不放大单格贴图。起步区仍为12格，故36投资基础开局不变。

随机只在 initialize 内执行：先给起步区两个矿位随机分配煤铁，再按地区配额无放回抽取岩壁和剩余矿点。使用原生 random_list 的 modifier factor=0 排除已占地块，while_loop_effect 按确定次数抽样。protected 是连通支配集；每个非骨架格子都邻接骨架，岩壁只能位于骨架之外，故随机后所有非岩壁格都可从调度站抵达。起步区除矿点和调度站外都是普通地，不被额外矿点占满。

每格持久变量：terrain、type、level、rail、paid、rail_paid、paused；route/effective 为缓存。各区 rN_* 的 STORED 字段保存十种材料、七类成品累计交付和 value，rN_next_* 为纯预测。无前缀 STOCKS 变量只缓存所选区显示，不能用于扣料；无前缀 PRODUCTS 与 value 是六区合计，不得被所选区缓存覆盖。budget 共享。地区切换不初始化、不跨区调拨。设施／线路最高三级，调度站自带三级线路，不可拆改；线路每级 1，设施成本见目录。

网络采用单调松弛，最多len(CELLS)=851遍（安全上限，实际在收敛时提前结束）。各区调度站同时作为独立根。每格route是通往本区调度站的所有正交路径中“最弱线路等级”的最大值；孤立环路保持零，岩壁禁止传递。effective=min(level,route)，停机为零；产能按区域汇总，不模拟共享路段累计拥堵。

refresh 重算网络、各区产能、纯预测、选择缓存与 dirty。rN_forecast 按 PROCESS_ORDER 对各区库存独立计算采矿→炼油→发电→钢→铝／合金→特色制造→通用机械。每道工序按有效产能与所有投入／电力的允许数量取最小值，扣除实际投入、加入 next_* 产出；同日新材料可继续使用。目录的 inputs 是每单位产出的耗料比例，UI 的每日投入为 ratio×rate，不能混淆。炼油厂不耗电网，避免油电循环无法启动。铬、钨合金共用 alloy 库存；特色制造优先于通用机械，停机可改变分配。浮点负余量钳制到非负，产率短缺阈值 0.0001。

各区只汇总和运行allowed(kind,rid)的设施。采矿6—9按本区矿额限制；加工10—14允许在所有地区建设以消耗进口材料；特色成品15—20仍按地区限定。运输站21每区最多一座，transport_sites统计包括断线／停机的已建站，transport_capacity统计有效等级。限制同时用于can_build、实际build执行与GUI。特色厂类型ID固定，不随切区改名。forecast汇总七类成品与产值；每次实际产出乘固定价格，再加入investment_output和next_value。原料、中间材料均不获投资。

`daily`仅对已解锁、初始化且active的人类俄罗斯运行。顺序为refresh_network→freight_arrivals→forecast→一次写回各区STORED及生产收入→freight_dispatch（days_left>1）→减计时→期满freight_finish→refresh_values。到货材料当天可生产，日末出口不抢本日生产用料。refresh_network只计算线路和设施能力；refresh_values计算预测、货运显示和选择缓存；普通refresh仍调用两者。每日不再重复扫描两次相同网络，库存变化不改变线路。第1800次结算后停止，不提前因500产值达标而结束。on_startup仅刷新，不推进货运、生产或资金。

共享初始投资40，各区煤6、铁4、钢2，其余STORED为0；初始布置不计时。预算守恒：`budget = 40 + earned - spent + refunded - freight_spent`，`earned = value = sum(product_quantity * price)`。freight_spent为实际净运费，期满未完成批次的退款在此扣除。价格：机械1、机床2、航空部件3、拖拉机1.5、铁路装备2.5、发电设备3、精密工具4。拆除退还实付，立即清零已付字段。显式二次确认重置恢复六区开局并重抽地形，同时清除材料、成品、产值、运输配置与批次；重复打开、解锁、帮助或刷新不重置预算。

## 自动跨区运输

目录常量FREIGHT_KIND=21，每级建设投资10，最高3级；单批6×min(出发有效站级,目的有效站级)，每单位运费0.1，最低批量1，保留量0/3/6/12、默认6。FREIGHT_DAYS为对称六区基础距离表，实际天数max(1,base+1-较低站级)，无原生地图铁路调用。

每区保留一条配置线路：freight_enabled/destination/resource/reserve_setting。开启后一直自动运行，缺料、缺资金或站点不可用只暂停，不清除enabled；上一批卸货后可同日发下一批。每区一个在途批次：freight_amount/days/cargo/to/fee为发货时快照；改配置只影响下一批。十种STOCKS都可运，电力和PRODUCTS不可运。累计sent/received/returned用于审计，当前incoming_count/amount是纯汇总缓存。

freight_preview/rN_freight_plan只计算可发量、较低能力、预计运费、时间和状态；实际dispatch每天在生产之后重新检查当前库存和预算。发货减出发库存、扣运费，接收地当日尚不入库；arrivals每天减一次倒计时，归零且目的站有效时一次性入库并清空快照。目的站断线则保持amount且days=0；出发站拆除不丢已发货物。source按0—5顺序使用共享预算，一个接收区可同时接收多个来源。最后一天无新发货，未完成批次退货并退运费，二次调用finish不能重复退款。

货运设置click在显示与实际效果中同时检查可编辑、非帮助页、build_page=2和对应region。关闭GUI、切图、存读档不推进或重置在途日数。模块内部到货／发货只能从daily提交路径调用，UI只调用设置与纯刷新。

## 界面与提示参考

窗口1600×1040，地图最大23×17外框；每格40×40、步长42，各区在966×714视区居中，左上角为(32,250)。右栏从x=1056开始，库存、地区标签与矿种条放在地图上方，等级图例与网络统计在y=967，底部按钮y=995。地区矿额移至网络统计悬浮提示，等级说明移至色块悬浮提示，给更高地图留空间。仅保留格子图标、底色与线段；坐标和等级数值在tooltip/detail。没有俄罗斯地图纹理或STATE名称。资金、资源、设施及线路图标复用已安装KR/原版素材。纯色PNG用于代码定义的UI几何，不是生成式美术。

`build_page`为0基础／1特色／2运输；特色目录最多五行两列，基础目录增加运输站。特色按钮及运输设置、标题、成本和图标必须共享“非帮助页＋对应地区＋菜单页”的可见条件，实际click再检查同样条件。运输页隐藏普通建造、拆除和生产预测区域，显示五个目的地、十种货物、保留量、自动发运、预估费用及到货统计。地图上方在所有地区显示七种额外库存以查看进口材料。布局测试逐区逐页检查显隐，文字不能覆盖真实格子。

复用资源决议图标、KR MIO 炼油／燃料图标、原版先进机床与基础机床技术图标（分别表示机床厂和精密工具）。读取纹理尺寸，在 GUI 中统一到 32px 外框、格子图标 28px；不改源贴图、不制造新的光栅资产。素材搜索支持 HOI4_KR_ROOT 与 HOI4_GAME_ROOT，默认从开发目录推导。俄罗斯文本保留既有英文回退规则；简中与英文完整，三语键集合一致。

- KR `interface/core.gfx`：确认 `hoi_16mbs`、`hoi_20b` 等真实字体与数值颜色。
- KR `common/scripted_effects/00_useful_scripted_effects.txt`：`while_loop_effect`，以及约1708行 random_list + modifier factor=0 的排除抽样写法。
- KR `common/scripted_guis/germany_mitteleuropa.txt`、`common/scripted_effects/MIT effects (Mitteleuropa).txt`：玩家上下文、dirty、分页和受限点击、变量检查参考。运输站复用KR `gfx/interface/military_industrial_organization/trait_icons/generic/railway_icon.png`，按原有32px/28px外框缩放。
- KR `interface/kaiserreich/countrypoliticsview.gfx` 及本模组已实测开局面板：普通spriteType绑定PNG纹理。无纹理progressbartype曾在实机显示为错尺寸黑框，已移除；预览器禁止自行模拟这类无纹理色块，以免再次掩盖渲染错误。
- KR UPC 党派背景的 iconType + corneredTileSpriteType：独立控制卡片显隐，避免嵌套窗口背景跨页泄漏。
- 原版 `interface/core_bare_minimum.gfx`：`gfx/interface/transp_white.dds` 原生线段材质。
- KR 简中 `KR_common/st manager l_simp_chinese.yml` 与地区管理 GUI：显式 pdx_tooltip 绑定写法。当前奖励全是自定义沙盘值，所以直接使用彩色自定义提示，没有虚构原生工厂效果。

所有卡片、选中细框和连线都随页面显隐；地区专属部件还检查 region，隐藏地图按钮不能穿透；厂区动作在帮助页不能穿透执行。线段在背景之上、设施图标之下，描绘相邻格子的真实运输连接。主界面“30天”是下一日产率折算，不是未来整月模拟。

地块tooltip标题直接由地区元数据写入对应语言名称。不要把地区名写成 `$RUS_ip_region_N$` 再期待pdX工具提示递归展开：实机曾直接露出键名。地形和状态仍使用已经生效的scripted localisation，动态数值保留原生变量显示。

## 验证与预览

```powershell
python tools/test_industrial_planning.py
python tools/test_factory_industries.py
python tools/test_factory_freight.py
python tools/test_factory_layout.py
python tools/generate_industrial_planning.py --check
python tools/preview_industrial_planning.py
python tools/preview_industrial_planning.py --idle --region 4 --seed 47
python tools/preview_industrial_planning.py --idle --specialty --region 5
python tools/preview_industrial_planning.py --idle --freight --region 2
python tools/preview_industrial_planning.py --help-page
python tools/preview_industrial_planning.py --finished
python tools/build_factory_regions.py
python tools/validate.py --group industry
```

检查实际生成脚本，而不是仅检查源代码含某段字符串。保留249项基础模型场景及122项特色产业场景，覆盖随机地形、独立图论对照、材料／电力／计价守恒、六条产业链生命周期、真实预算开局和完整1800天合法扩产。六链夹具注入10000建造预算以隔离配方检查，不冒充真实开局。新增28项货运场景覆盖十种材料、批次计时、持续自动发运、短缺恢复、单站限制、弱端能力、保留量、费用守恒、隐藏点击、改配置、断线待卸、数据恢复、多源来货、进口当日加工、期满和重置。布局检查涵盖三个页面和全部地区显隐，测试不以静态通过代替引擎实测。

执行相关 RHoiScribe 文件与项目检查及 `repair_hoi4_project(dry_run=true)`，区分上游自定义效果索引误报；不应用全项目通用格式修复。最后做独立生成复现、BOM/重复键和 Git 空白检查。运行时仍由用户新开局验证，不自动启动游戏；本任务不构建上传目录。
