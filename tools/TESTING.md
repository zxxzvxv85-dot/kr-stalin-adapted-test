# 测试和生成结果检查

从任意工作目录运行 `python <源码目录>/tools/validate.py`。默认执行 `validation_checks.json` 中全部检查，不修改游戏脚本、生成结果或基线文件。

```powershell
python tools/validate.py
python tools/validate.py --list
python tools/validate.py --group agriculture advisors
python tools/validate.py --group military --group generated
python tools/validate.py --game-root 'D:/steam/steamapps/common/Hearts of Iron IV' --kr-root '../1521695605'
```

分组为 `agriculture`、`diplomacy`、`military`、`advisors`、`easy`、`generated`、`format`、`structure`、`interface`。重复指定的检查只运行一次。新增测试应登记清单的 `id`、`path`、`groups`；有外部依赖时填写 `requires`。生成器只登记 `--check`，禁止将 `--write`、`--record` 或打包构建纳入验证入口。

需要 Python 3 和 Node.js；布局检查读取已安装游戏的字体。KR 对照检查使用安装中的 KR 和记录的源文件哈希；VDV 兼容检查另外读取同级 `3105210203`、`3555444820` 两个技术扩展。缺依赖、脚本异常、数值断言失败、生成结果漂移均返回非零状态并显示原因。路径可由命令行或 `HOI4_GAME_ROOT`、`HOI4_KR_ROOT` 指定；子检查使用相同环境值。

`test_support/` 保存只读解析器和有限机制模拟器，导入不会执行任何测试。农业、地区外交与乌克兰场景各自明确建模支持的命令；遇到未知命令必须失败，不把未知逻辑一律当作通过。音频、KR 波兰影响力再分配等引擎或上游机制在专用测试中标明边界。不要把这些夹具当成完整 HOI4 引擎。

测试不读取 `git show HEAD` 或某个固定提交。维护业务规则时同步修改对应场景与边界，不为过时断言恢复旧玩法。比如订单默认不接受、农机需求 8000、援助决议 10 政治点，以及新欧洲整合固定 1000/2000 政治点均按目前规则验证；顾问检查依据制作日志中 2026-09-15 撤回过度原版化的规则，不能要求自定义顾问与 KR 完全相同。

生成器一致性检查比较可再生成的最终文件；文本测试检查本地化编码、键、颜色、引用和实际字体宽度。发布仍需在游戏退出后单独运行 `Build-CleanWorkshopUpload.ps1`。检查通过仅证明静态结构与被覆盖场景成立；游戏加载、UI 展示、事件时序和原生存档仍需游戏内抽查。

农业独立窗口的 `test_agriculture_window.cjs` 比较 15 个按钮与原决议的实际结算，覆盖普通／简易模式、政治点小数边界、积分和次数限制、项目重复执行、窗口关闭与系统关闭、AI／其他国家拒绝操作。`test_national_agriculture_layout.cjs` 同时检查卡片和窗口外框的坐标及三语字体宽度。入口、生成顺序与实机抽查步骤见 `AGRICULTURE_WINDOW.md`。

`test_agriculture_factory_conversion.cjs` 专门验证拆军工后立即投产、专用产能不重复占用民工、每日实际产出、建筑支付与五次上限，以及停产恢复、工厂损失、库存已满和既有额度。它曾在修复前以“转换后投入产线仍为 0”失败，用于保护此次实际缺陷。
