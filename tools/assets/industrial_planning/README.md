# KR 工业规划地图美术源

2026-09-28 按用户最终明确要求，游戏地图与州界为唯一几何依据。通过内置 `image_gen` 编辑固定 KR 地理线稿，改善印刷材质与配色。工具未返回具体模型名称；未使用 CLI/API 或外部凭据。

- `geography_reference.png`：1168×432 参照，由已安装 KR 的 `map/provinces.bmp`、`map/definition.csv` 和 RUS/TRM 州历史生成，覆盖 36 个州组及 104 个游戏州。北部斜线带表示 KR 地图以外的区域，不是海水。
- `atlas_source.png`：选定的 ImageGen 原始输出，2062×763。1930 年代规划图风格，增加印刷纸纹、细线和低对比度底色；无文字、设施或交互元素，不增画现实海岸、现代国界、河流或山脉。
- `prompt.txt`：最终实际提交给内置工具的完整提示词，明确以 KR 参照为准，禁止用现实俄罗斯轮廓修改几何。
- 游戏贴图：`gfx/interface/RUS_industrial_planning/map.png`，1168×432 RGBA。构建器将固定源图缩放至原画布，不裁切、不再次调用生成服务。地区高亮、节点、设施和运输连线保持独立。

选定原始生成文件：`C:/Users/Administrator/.codex/generated_images/01a09acc-a453-7b83-8df7-6e765bd73237/exec-f9c7a9fd-2e62-423f-abe2-8169f796e16d.png`。项目内已保存完整副本，不依赖此机器路径。

地图不是现代国界图。按州组显示 KR 的俄罗斯/远东经营范围；运行时继续检查各中心州的拥有、控制及建筑条件。绘画不决定资源、运输拓扑或奖励。

`build_industrial_planning_map.py` 构建时先验证新算出的 KR 参考像素与保存参照完全相同；若 KR 更新使几何变化，构建停止，要求核对美术。只读 `--check` 校验 KR 文件、美术来源及 120 张运行图片的 SHA-256，不重新绘图。参考、源图与完整提示词的哈希记录在 `tools/data/industrial_planning_map.json`。

检查：已查看原尺寸叠加预览，北界标签、地区高亮、设施图标与连线可辨认；36 区成员、中心、点击位置、资源及运输关系与 KR 构建基准一致。此次换图仅改变底图及来源记录，其余 119 张运行图哈希一致。预览不是实机截图，游戏渲染由用户测试。

现实地理草案已从维护代码及运行数据移除，仅归档在 `output/industrial_planning/geography/rejected-real-world/`。现有上传构建排除 `tools/`、`output/`；本轮依用户要求未执行上传构建。
