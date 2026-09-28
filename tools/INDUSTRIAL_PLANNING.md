# 俄罗斯工业规划沙盘原型

本原型只加入测试版开发目录。2026-09-28 按用户要求，不同步上传目录。

## 入口与试用

- 玩家使用俄罗斯时，地图右下方、农业入口左侧显示独立的工业按钮；悬浮提示为“工业规划沙盘”。采用与农业相同的 `raid_filter` 挂接，参与中欧同盟时，两种入口位置互斥切换。
- 为便于直接试用，暂不要求先完成一五计划国策。原型只向人类玩家的原始 RUS 国家开放，AI 不经营。
- 窗口为 1184×726，可拖动；关闭按钮和 Esc 都保留布局、投资、材料、轮次和成绩，再次打开继续。
- 点击地图编号，在右侧建设或升级，然后点击“结算本轮”。“刷新预测”不生产、不推进轮次。“重新规划”必须再次确认，只清空本沙盘。
- 使用开发版重新启动游戏后测试。预览图由实际 GUI 坐标和脚本夹具生成，不是游戏截图；字体尺寸、入口挂接及真实存读档仍需实机验证。

## 地理分区

使用已安装 KR 的省份图、省份颜色表和 104 个 RUS/TRM 开局地区，合并为 36 个不规则经济区。边界保留真实地区轮廓，不把俄罗斯切成等大方格；西部围绕工业中心细分，西伯利亚与远东使用较大的资源腹地。

`build_industrial_planning_map.py` 的 `DISTRICTS` 是唯一分区来源。每条记录为“中心州 + 成员州列表”，各州只归属一处。编号和地区中心之间必要时用引线相连，挪动编号不挪动地理边界。每区的实际经营资格按命名中心州的拥有权与控制权检查。外贝加尔、远东等地失去控制时，地图仍显示，但不能建设或参与生产。

煤矿潜力来自组内 KR `coal` 资源，铁矿潜力来自 `steel` 资源；它们只约束虚拟矿山位置，不给国家增添原生资源。地块陆地接壤关系由地图数据计算，另有鄂霍次克—堪察加、哈巴罗夫斯克—北萨哈林两条明确的海运接驳。金色线路表示陆路，蓝色虚线表示接驳。

## 经营规则

每区只能容纳一种工业设施，设施和铁路分别升级，最高三级。下表均为一级、每轮数量。

| 项目 | 升一级投资 | 作用 |
| --- | ---: | --- |
| 煤矿 | 2 | 产出 3 煤，需要煤矿潜力 |
| 铁矿 | 2 | 产出 3 铁，需要铁矿潜力 |
| 电站 | 3 | 消耗 1 煤，提供 6 电力 |
| 钢铁厂 | 4 | 最多产出 2 钢，每钢消耗 1 煤、1 铁、2 电力、1 加工运力 |
| 机械厂 | 5 | 最多产出 2 机械，每机械消耗 2 钢、1 电力、1 加工运力 |
| 铁路 | 2 | 与相邻有铁路地区连通；接通莫斯科后，每级提供 2 加工运力 |

生产顺序为采矿、发电、炼钢、机械。所有设施都须通过铁路连接莫斯科枢纽；失去枢纽或线路中断时，断开的设施不贡献产量与运力。电力不跨轮保留，原料和机械库存保留。电站有煤时按已建等级发电，多余电力当轮作废；铁路是区域网络容量，尚不模拟每条线路的货运路径或运输距离。采矿与发电不额外消耗加工运力。

开始时投资 24，煤 6、铁 4、钢 2、机械 0，并提供一套可以完成第一轮目标的起始产业链。五轮累计机械目标为 **2、6、12、18、25**；每轮达标获得 20 分，进入下一轮增加 18 投资。第五轮结束后停止结算，继续查看或重新规划。回归测试包含一条不透支预算、沿实际邻接网络扩建并拿到 100 分的路线。

拆除返还本局在该设施或铁路上实际支付的投资，免费的起始等级不能变现；已产出的原料和机械不回收。建设、拆除和结算均在执行时复核资格，不能通过强制点击绕过成本或重复领取结算。

这是独立沙盘：不改国家工厂、经济盈余、政治点、现有一五计划分数或正式奖励。虚拟投资及机械成绩也不进入简易模式翻倍。后续如接入正式一五计划，需另设不可重复领奖的结算接口，不能直接把可反复重开的分数用于发奖。

## 文件与状态

| 用途 | 维护源／运行文件 |
| --- | --- |
| 地理数据和图片 | `build_industrial_planning_map.py` → `tools/data/industrial_planning_map.json`、`gfx/interface/RUS_industrial_planning/` |
| 规则、界面和本地化生成 | `generate_industrial_planning.py` 的 `render_outputs()` 返回 9 个相对路径及内容 |
| 游戏入口、可见性和按钮 | `common/scripted_guis/RUS_industrial_planning.txt`、`interface/RUS_industrial_planning.gui` |
| 建设及生产 | `common/scripted_effects/RUS_industrial_planning_effects.txt`、对应 scripted_triggers |
| 动态文本及资源 | `common/scripted_localisation/RUS_industrial_planning_loc.txt`、同名 `.gfx` 和三语 `.yml` |
| 验证和布局预览 | `test_industrial_planning.py`、`preview_industrial_planning.py` |

所有运行状态使用 `RUS_ip_` 前缀。`initialized/open/finished/restart_armed` 为国家旗标；`n0_*` 至 `n35_*` 保存类型、等级、铁路、实际付款和连通缓存；`round/budget/coal/iron/steel/machines/score` 为存档状态。`next_*` 只保存预测，结算时统一写入库存。`selected/sel_*/dirty` 管理界面；关闭界面不清空经营状态，重新规划显式重置。

没有新增日度、月度或每帧生产钩子；领土发生变化后点击刷新或操作按钮时重算。连接算法最多迭代 36 次；生产循环受设施等级限制，单循环最多 216 次。使用 KR 已采用的 `while_loop_effect`，不可改成其他 P 社游戏的 `while` 语法。

## 生成与验证

普通检查不重绘图片。地图 JSON 保存 KR 依赖及每个图片的 SHA-256，依赖变化会报错，先审查上游变化再显式重建。原型中文完整，英文提供对应规则，俄语只翻译部分标题和按钮，其余暂用英文。

```powershell
python -B tools/build_industrial_planning_map.py --check
python -B tools/generate_industrial_planning.py --check
python -B tools/test_industrial_planning.py
python -B tools/validate.py --group industry

# 调整地理分区时才重绘；之后重新生成文本。
python -B tools/build_industrial_planning_map.py --write
python -B tools/generate_industrial_planning.py --write

# --output-root 可输出到临时目录验收，不覆盖开发源码。
python -B tools/generate_industrial_planning.py --output-root C:/Temp/industrial-text-preview

# 根据实际坐标、三语键的中文值和初始状态生成布局预览，仅写 output/。
python -B tools/preview_industrial_planning.py
python -B tools/preview_industrial_planning.py --finished
```

地图构建可通过 `HOI4_KR_ROOT` 指定 KR 路径，统一验证入口的 `--kr-root` 会传入该变量。图形工具依赖 Pillow；测试执行实际生成的脚本，但不代替 HOI4 引擎测试。

实机重点：农业旁的工业入口与中欧同盟按钮同时显示时的布局；各缩放比例下文字与按钮；失去控制及断铁路后的停产；五轮目标、结束后禁止重复结算、关闭再打开及保存重载。游戏测试由用户执行，本轮不启动游戏、不构建上传目录。
