# 开发工具入口

先读根目录的 `维护索引.md` 查功能归属。此目录不会进入上传包；文件存在不表示它适合对当前版本直接执行。

| 类别 | 入口 | 使用约定 |
| --- | --- | --- |
| 日常验证 | `validate.py`、`validation_checks.json` | 默认全部只读；用 `--group` 筛选。详见 `TESTING.md` |
| 顾问生成 | `generate_relationship_advisor_tiers.py` | 维护等级数据和普通/简易模式特质，包含三语说明 |
| 简易模式生成 | 五个 `generate_easy_mode_*.py` | 分别维护顾问、民族精神、军改、其他动态修正、科技；默认 `--check` |
| 国家农业生成 | `generate_national_agriculture.cjs` | 基础逻辑→说明数据→卡片与独立窗口→订单浏览器；整批检查最终输出 |
| 农业 UI 子构建 | `build_agriculture_card_gui.py`、`agriculture_standalone_window.py`、`agriculture_order_browser.py` | 纯文本渲染可导入；独立窗口从原决议读取操作定义，维护说明见 `AGRICULTURE_WINDOW.md`；重画素材需显式 `--assets` |
| 农业窗口预览 | `preview_agriculture_window.py` | 用实际界面位置与原生纹理生成离线示意图；`--admin-page 0/1`、`--card-page 1..5` 选择页面，输出到 `output/`，不替代游戏内测试 |
| 其他维护界面 | `generate_tesla_minesweeper.py`、`generate_europe_intervention_gui.py`、`build_military_dashboard.cjs` | 默认只检查文本；图片重建与文本构建分开 |
| 介绍界面皮肤 | `build_intro_theme.py`、`test_intro_header.py` | 默认只校验纹理哈希及 KR 控件/逻辑；显式 `--write` 重画几何皮肤并原样复制已批准标题，详见 `INTRO_SCREEN.md` |
| 输出与依赖公共层 | `generation_io.py`、`kr_generation_baseline.py` | 整批路径预检、编码、只读比对；KR 基线只在审查后显式 `--record` |
| 手写脚本格式 | `format_runtime_scripts.py` | `--list` 查目标，默认只读；显式 `--write` 展开复杂长行，词法序列与 AST 必须保持一致 |
| 整体结构 | `check_runtime_structure.py` | 扫描所有运行目录括号/编码，检查真正唯一的 ID；不替代引擎作用域检查 |
| 构建上传目录 | `Build-CleanWorkshopUpload.ps1` | 游戏退出后单独执行；从源码构建、校验、替换上传目录 |
| 显式奖励转换 | `apply_easy_mode_rewards.py`、`apply_easy_mode_tech.py` | 默认只读，维护新奖励时先审查报告再显式写入，不由日常检查自动执行 |
| 历史迁移 | `archive/` | 军工迁移及已被后续设计取代的顾问隔离实验只供参考，禁止直接执行 |
| 农业旧补丁兼容入口 | `apply_easy_mode_agriculture.py` | 已改为委托农业生成源，默认只读，不再在产物上叠补丁 |
| 美术、媒体和设计实验 | `build_*_icon*`、`*_bolshevik_*`、`*_psr_*`、`convert_music_to_ogg.py`、`Build-SovietFoundationVideo.py` | 仅在对应美术/媒体任务使用，可能依赖本地源素材；不会由普通验证自动执行 |
| 设计图导入导出 | `*drawio*`、`export_focus_tree_to_drawio.py`、`import_foreign_focus_icons.py` | 修改前核查方向、目标与当前图，不能用历史图反向覆盖现行国策 |
| 审计与预览 | `code_style_audit_*.md`、`readiness_balance_audit.md`、`preview_*`、`render_*` | 报告注明日期，只代表当时状态；预览产物放 `output/` 或临时目录 |

新增工具沿用以上边界，不把临时迁移包装成默认生成步骤。需要新增生成器时，先提供 `render_outputs()`，再接公共 CLI；不得导入测试文件借用解析器，公共测试工具位于 `test_support/`。

默认检查不应改变文件哈希或修改时间。可在源码树外使用 `--output-root` 验证可再生成性；未经 `--write` 不允许把输出写回源码树内部。生成文件中需要保留的手工修订，应先回收到相应逻辑或数据源再重建。
