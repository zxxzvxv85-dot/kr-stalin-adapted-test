# 俄罗斯情报机构徽章

两个选择通过 `common/intelligence_agencies/RUS_stalin_agencies.txt` 追加，仅供原始标签 RUS 选择，`default = { always = no }` 保留 KR 原有默认选择。

- NKVD 直接引用原版 `GFX_intelligence_agency_logo_sov`，不复制或重绘原版 DDS。
- KGB 来自用户提供的盾剑徽章；内置 image_gen 去白底，模型标识未由工具返回。原图、1254×1254 透明输出和完整提示词均保留在本目录。
- 运行资源为 `gfx/interface/operatives/agencies/agency_logo_RUS_KGB.png`：RGBA PNG，233×119，两帧；两帧使用相同主体尺寸。主体保持比例，高度 106 像素，与 KR VGPU 的可见高度相当，剑柄和剑尖均保留。选择框沿用原版 0.7 比例，不修改 GUI 槽位或缩放。
- `tools/build_intelligence_agency_logos.cjs` 只做引擎排版导出，默认只读检查。支持 `--check`、`--write`、`--output-root`；需要 Node.js 的 `@napi-rs/canvas`。不重新调用图像生成服务。
- 已并排检查 VGPU、NKVD、KGB 在实际选择框比例下的可读性；尺寸、透明通道、边界、引用与默认选择检查通过。游戏中的点击、悬停与存档显示仍交由用户实测。

完整提示词见 [kgb_prompt.txt](kgb_prompt.txt)，输入输出及 KR 参考哈希见 [manifest.json](manifest.json)。`tools/` 和 `output/` 不进入上传包。
