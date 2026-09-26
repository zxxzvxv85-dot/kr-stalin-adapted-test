# 构成主义介绍界面

仅测试版覆盖介绍窗口，不覆盖 KR 的全局徽标或其他菜单。

| 入口 | 用途 |
| --- | --- |
| `interface/kaiserreich/intro_screen.gui` | 原控件布局、配色资源、标题与面板衔接；只在 KR 原主窗口增加整体滑入动画 |
| KR 的 `common/scripted_guis/00_intro_screen_gui.txt` | 本模组不再覆盖；四页均沿原关系直接挂在 `kr_intro_screen_container` 上，复用上游全部逻辑 |
| `interface/RUS_intro_header.gfx`、`interface/RUS_intro_theme.gfx` | 专用精灵定义，不改共享按钮 |
| `build_intro_theme.py` | 显式 `--write` 生成 12 张纹理；默认或 `--check` 只校验哈希，不重画；支持 `--output-root` |
| `test_intro_header.py` | 与当前安装 KR 对比控件和逻辑，检查资源尺寸、帧数、标题完整性及动画几何 |
| `preview_intro_theme.cjs` | 用实际纹理和 KR 简中文本生成离线布局图；需要 `@napi-rs/canvas`，仅作布局参考 |

入场时长 1,200 毫秒，使用引擎界面时间，暂停游戏也不依赖游戏日推进。保留原来的 720×840 主窗口及中心对齐，以 `position.x=-100%` 从画面左侧进入，`show_position={x=0 y=-20}` 恢复 KR 原位置。标题、背景与各页文字只有同一个主窗口位移；没有反向补偿、额外裁切或新增脚本父窗口。切页时主窗口不重新隐藏，四页仍是实时控件。

2026-09-25 的实机日志已经证明上一版额外嵌套存在缺陷：四条 `Parent window for kr_intro_screen_tab_N is not found` 对应正文脱离主框。该覆盖脚本已移除，不应仅凭离线排版或两个位移相消的数学检查重新引入它。回归检查要求原主窗口名称、原脚本挂接关系和原控件局部坐标一致。

标题使用用户批准的内置 `image_gen` 结果，原始 PNG 为 1860×846 RGBA。`art_sources/intro_header_v2_source.png` 保存原图，`intro_header_v2_prompt.txt` 保存实际完整提示词；运行标题与原图字节相同。

面板改用内置 `image_gen` 新绘制的完整印刷边框，原图为 1532×1026 RGBA，保存于 `art_sources/intro_frame_v2_source.png`，实际提示词在 `intro_frame_v2_prompt.txt`。构建时将整张素材等比近似缩至 728×488，不裁切或重画图案；原比例差低于 0.1%。由于原图带半透明磨损，GUI 在它下面另放全不透明的深色底板，确保地图和地名不会透过正文。页签、按钮、勾选框和翻页箭头由代码绘制分层细线、切角及细微油墨变化，文字仍由游戏显示。

参照 KR 1.7 的 `interface/kaiserreich/intro_screen.gui/.gfx`、`common/scripted_guis/00_intro_screen_gui.txt`，原生窗口动画参照游戏的 `interface/command_character_view.gui`。新增 override 与当前 KR 的行为差异由回归检查约束；KR 更新后先审查测试报告，不能自动覆盖本模组逻辑。

资源、尺寸与静态逻辑检查不能代替游戏验收。重启游戏后检查首次打开、关闭再开、四个标签页、翻页、选项及继续按钮；优先确认正文与插画回到框内，以及最新日志不再出现上述四条父窗口错误，再观察动画与分辨率/界面缩放。
