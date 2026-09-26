# 构成主义介绍界面

仅测试版覆盖介绍窗口，不覆盖 KR 的全局徽标或其他菜单。

| 入口 | 用途 |
| --- | --- |
| `interface/kaiserreich/intro_screen.gui` | 原控件布局、配色资源、标题与面板衔接；KR 原主窗口统一原位淡入、淡出 |
| `common/scripted_guis/00_intro_screen_gui.txt` | 最小覆盖 KR：两处关闭入口缓存当前标签页，四页在主窗口淡出期间保留内容；原父窗口和其他逻辑不变 |
| `common/scripted_localisation/RUS_country_intro_scripted_loc.txt`、`localisation/replace/RUS_country_intro_l_*.yml` | 在国家标签页插入俄国新首页；后四页继续引用 KR 原本地化键，其他国家转回 KR 原选择函数 |
| `history/countries/RUS - Russia.txt` 的 `country_intro_page_count` | KR 使用从零开始的末页索引；值为 4，即新开局俄国共有五页 |
| `interface/RUS_intro_header.gfx`、`interface/RUS_intro_theme.gfx`、`interface/RUS_intro_portrait.gfx` | 专用精灵定义，不改共享按钮；列宁插画只在 RUS 的国家介绍中显示 |
| `build_intro_theme.py` | 显式 `--write` 生成 12 张纹理；默认或 `--check` 只校验哈希，不重画；支持 `--output-root` |
| `test_intro_header.py`、`test_intro_content.py` | 与当前安装 KR 对比控件和逻辑，检查资源尺寸、帧数、标题完整性、32 组关闭重开状态及五页前后翻页、非俄国回退和配色闭合 |
| `preview_intro_theme.cjs` | 用实际纹理和 KR 简中文本生成离线布局图；需要 `@napi-rs/canvas`，仅作布局参考 |

打开和关闭均使用主窗口的 `fade_time=2000`、`fade_type=linear`，即 2 秒原位整体淡入、淡出。保留原来的 720×840 主窗口、中心对齐和 `position={x=0 y=-20}`，不再设置位移动画。标题、背景、正文与按钮均随同一个主窗口改变透明度；没有反向补偿、额外裁切或新增脚本父窗口。切页时主窗口不重新隐藏，四个标签页仍是实时控件，游戏日期不参与动画计时。这是整体透明度过渡，不是从左到右的空间渐变遮罩。

KR 的关闭入口会清除 `kr_intro_screen_variable`，使对应正文页立刻不可见。最小覆盖在顶栏开关、继续按钮关闭时先把当前标签页保存至国家变量 `RUS_intro_fading_tab`；四页只在主窗口已关闭时读取这个缓存，使最后一页随主窗口一起淡出。重新打开时清除缓存，按 KR 原逻辑显示第一个标签页；正文页码与路线剧透状态继续保留。主窗口可见条件仍只取决于 KR 原变量，所以残留缓存不会独立打开界面；不要向四页各自添加淡入淡出，否则普通切页也会交叠。

俄国国家介绍依次为“未竟的十月”、原国家概况、“白卫往事”、“通往第三俄罗斯之路”、“和平与面包”。首页中文为用户定稿，仅将用户确认的列宁遇刺日期改为 1918 年 8 月，并加入原生颜色标记；英俄文本使用对应翻译。KR 原文、滚动框和交互结构不变。页数通过国家历史初始化，以新开局为基线，没有新增旧存档迁移或重置当前页码的钩子。

左侧插画使用用户提供的列宁原画，完整 JPG 保存在 `tools/art_sources/intro_lenin_source.jpg`（800×1091，SHA-256 `adb3a8b7488b0f1ee8a5e46c679edf5f7a90677b0619f1e866d62b9292525e20`）。运行文件 `gfx/interface/rus_intro_portrait/lenin_painting.png` 仅由 `@napi-rs/canvas` 完整转为 PNG，已核对同一解码器下的像素一致，没有重绘、修色或栅格裁剪。GUI 的装饰性子容器保持原插画 168×376 的尺寸，以 `scale=0.344638` 等比缩放并裁掉右侧，保留原图左侧约 487.47 像素及完整高度，覆盖列宁的头部、双手和身体。此子容器没有单独 scripted GUI 注册，也不承载按钮或文字。两条可见性条件只替换 RUS 五页国家介绍的插画；其他国家继续使用 KR 原图选择器。调整取景时改 GUI 并同步离线预览，不修改原画。

2026-09-25 的实机日志已经证明上一版额外嵌套存在缺陷：四条 `Parent window for kr_intro_screen_tab_N is not found` 对应正文脱离主框。失败的额外父窗口结构已移除；本次为关闭缓存引入的覆盖仍保留 KR 原有的全部直接父子关系，不能恢复旧的嵌套。回归检查要求原主窗口名称、原脚本挂接关系和原控件局部坐标一致，并在剔除本次缓存逻辑后逐节点比较整个 KR 原脚本。

标题使用用户批准的内置 `image_gen` 结果，原始 PNG 为 1860×846 RGBA。`art_sources/intro_header_v2_source.png` 保存原图，`intro_header_v2_prompt.txt` 保存实际完整提示词；运行标题与原图字节相同。

面板改用内置 `image_gen` 新绘制的完整印刷边框，原图为 1532×1026 RGBA，保存于 `art_sources/intro_frame_v2_source.png`，实际提示词在 `intro_frame_v2_prompt.txt`。构建时将整张素材等比近似缩至 728×488，不裁切或重画图案；原比例差低于 0.1%。由于原图带半透明磨损，GUI 在它下面另放全不透明的深色底板，确保地图和地名不会透过正文。页签、按钮、勾选框和翻页箭头由代码绘制分层细线、切角及细微油墨变化，文字仍由游戏显示。

布局和交互参照 KR 1.7 的 `interface/kaiserreich/intro_screen.gui/.gfx`、`common/scripted_guis/00_intro_screen_gui.txt`。淡出方式参照本机“帝国雄心（重置/世界线）”4.0（工坊 ID `3206158781`）的 `interface/TNO_Country_Info_Screen.gui` 中主窗口：原参考为 `fade_time=15000`、`fade_type=linear`，本界面按用户要求使用 2 秒时长。参考文件 SHA-256 为 `0465f6523e699413f716250e48612faafd237c7b436f0c2bb1f1eb8a909f146f`；没有复制其图片、电视信号装饰或专属玩法逻辑。

本次 KR 覆盖源文件 SHA-256 为 `9d8dc0c954845bec76221055d8d15afa7087f715367b4df355beca7025a2b859`。覆盖与当前安装 KR 的行为差异由回归检查约束；KR 更新后先审查测试报告，不能自动覆盖本模组逻辑。

资源、尺寸与静态逻辑检查不能代替游戏验收。重启游戏后检查首次打开、继续按钮关闭、Ctrl+I/顶栏关闭、快速关闭重开、四个标签页、翻页及选项；确认正文与框体原位同步淡出、切页没有交叠，以及最新日志没有上述父窗口错误。静态状态检查不能验证引擎在淡出期间的绘制和点击拦截，仍须在暂停游戏及不同分辨率/界面缩放下实测。
