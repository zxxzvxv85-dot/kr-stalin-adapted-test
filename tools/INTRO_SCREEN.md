# 构成主义介绍界面

仅测试版覆盖介绍窗口，不覆盖 KR 的全局徽标或其他菜单。

| 入口 | 用途 |
| --- | --- |
| `interface/kaiserreich/intro_screen.gui` | 原控件布局、配色资源、标题与面板衔接；两个反向移动的原生窗口共同完成裁切展开 |
| `common/scripted_guis/00_intro_screen_gui.txt` | 在 KR 原逻辑外新增可见性容器；四个标签页挂到动画内容容器；其余条件、点击效果与属性保持一致 |
| `interface/RUS_intro_header.gfx`、`interface/RUS_intro_theme.gfx` | 专用精灵定义，不改共享按钮 |
| `build_intro_theme.py` | 显式 `--write` 生成 14 张纹理；默认或 `--check` 只校验哈希，不重画；支持 `--output-root` |
| `test_intro_header.py` | 与当前安装 KR 对比控件和逻辑，检查资源尺寸、帧数、标题完整性及动画几何 |
| `preview_intro_theme.cjs` | 用实际纹理和 KR 简中文本生成离线布局图；需要 Node Canvas，仅作布局参考 |

展开时长 1,200 毫秒，使用引擎界面时间，暂停游戏也不依赖游戏日推进。外层 800 像素宽的裁切窗口从 x=-800 移至 0；内容窗口从 x=840 移至 40，相同缓动保证内容位置固定。主内容与裁切层均由 scripted GUI 的可见性显式驱动。动画结束保持完整界面，切换标签页不改变这两层的可见性；四页仍是实时控件。需在游戏里验证引擎实际的裁切继承、同步开关及点击。

标题使用用户批准的内置 `image_gen` 结果，原始 PNG 为 1860×846 RGBA。`art_sources/intro_header_v2_source.png` 保存原图，`intro_header_v2_prompt.txt` 保存实际完整提示词。运行纹理与原图字节相同；原图周缘留白不足的细节不再另行重画。面板、页签和按钮是代码绘制的红、炭黑、米白几何图形，文字由游戏显示。

参照 KR 1.7 的 `interface/kaiserreich/intro_screen.gui/.gfx`、`common/scripted_guis/00_intro_screen_gui.txt`，原生窗口动画参照游戏的 `interface/command_character_view.gui`。新增 override 与当前 KR 的行为差异由回归检查约束；KR 更新后先审查测试报告，不能自动覆盖本模组逻辑。

资源、尺寸与静态逻辑检查不能代替游戏验收。重启游戏后检查首次打开、关闭再开、四个标签页、翻页、选项及继续按钮；留意展开时文字是否和边框同步，以及分辨率/界面缩放下是否裁掉底部。
