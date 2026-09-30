# Stalin Returns 测试版开发仓库

本仓库保存 Mod 的完整开发源码、开发工具、美术源文件和维护记录。GitHub 是跨电脑同步开发进度的唯一来源，Steam 创意工坊目录不能代替源码仓库。

## 玩家下载与安装

**只想试玩：下载整个 `main` 分支的 ZIP，不要逐个下载脚本或只下载最近修改的文件。** 仓库当前为公开仓库，可以直接使用 [下载最新开发版 ZIP](https://github.com/zxxzvxv85-dot/kr-stalin-adapted-test/archive/refs/heads/main.zip)，也可以在仓库页面点击 **Code → Download ZIP**。开发版可能包含仍在测试的内容，与创意工坊已发布版本不一定相同。

### 1. 准备前置模组

需要安装并启用 `descriptor.mod` 声明的两个前置：

- [Kaiserreich](https://steamcommunity.com/sharedfiles/filedetails/?id=1521695605)
- [KR共产主义拓展前置 Kaiserreich Communism Pre-Expansion](https://steamcommunity.com/sharedfiles/filedetails/?id=3391120577)

使用简体中文时还应启用配套的 [Kaiserreich 简体中文汉化](https://steamcommunity.com/sharedfiles/filedetails/?id=2946487287)。本仓库不包含这些前置；游戏与前置版本应匹配。本次快照的 `descriptor.mod` 标注游戏版本为 `1.19.2.0`，这不代表已验证后续所有版本。

### 2. 放置下载的文件

解压 ZIP，将包含 `descriptor.mod`、`common`、`events` 等内容的那一层文件夹改名为 `kr_stalin_adapted_test`，放入：

```text
文档/Paradox Interactive/Hearts of Iron IV/mod/kr_stalin_adapted_test/
```

如果 Windows 的“文档”已重定向到 OneDrive 或其他位置，请使用实际的游戏用户目录。最终应是 `kr_stalin_adapted_test/descriptor.mod`，不能在里面再套一层 `kr-stalin-adapted-test-main`。

直接保留解压后的全部内容即可。若只保留运行文件，必须完整保留以下内容及其子目录：

```text
common/
events/
gfx/
history/
interface/
localisation/
music/
descriptor.mod
thumbnail.png
```

`tools/`、各类 `.md` 文档和编辑器配置不参与游戏运行；玩家无需安装 Python、Node.js、Codex 或 RHoiScribe。`_local_loader` 是开发者本机的目录联接，`_upload` 是创意工坊构建目录，都不是玩家需要下载的文件。

### 3. 建立本地启动器条目

先关闭游戏和启动器。在**下载后用于游玩的副本**中打开 `descriptor.mod`：将 `name` 改为 `"[KR] 多么幼稚的幻想，但是斯大林 - GitHub开发版"`，删除 `remote_file_id` 所在行，其余内容保留。这样不会把本地副本当成已订阅的创意工坊条目。

将修改后的 `descriptor.mod` 复制到上一层 `mod` 文件夹，并重命名为 `kr_stalin_adapted_test_github.mod`；注意不能变成 `.mod.txt`。在这个外部 `.mod` 文件末尾添加一行，指向你刚才放置的模组目录，例如：

```text
path="C:/Users/你的Windows用户名/Documents/Paradox Interactive/Hearts of Iron IV/mod/kr_stalin_adapted_test"
```

务必把示例改为自己电脑上的**实际绝对路径**，使用正斜杠 `/`。最终目录结构为：

```text
mod/
├─ kr_stalin_adapted_test_github.mod
└─ kr_stalin_adapted_test/
   ├─ descriptor.mod
   ├─ common/
   ├─ events/
   └─ …其余运行文件
```

重新打开启动器，将“GitHub开发版”和前置模组加入同一个播放集。只启用一份斯大林模组，关闭同一模组的创意工坊版、适配版或其他开发副本，以免相互覆盖。开发版建议用新存档测试。

以后更新时，关闭游戏和启动器，完整替换这个本地副本，再重复本节的描述文件处理；不要只覆盖几个改动文件，否则旧版本已删除的脚本可能残留。下文的同步工具和制作工具说明面向开发者，普通玩家无需执行。

## 本地目录如何分工

当前开发流程将源码、游戏加载入口和创意工坊上传内容分开存放：

| 目录类型 | 本机示例 | 用途 |
| --- | --- | --- |
| Git 源码目录 | `D:\steam\steamapps\workshop\content\394360\kr_stalin_adapted_test` | 实际编辑、检查、提交和推送的位置 |
| 启动器投影 | `D:\steam\steamapps\workshop\content\394360\kr_stalin_adapted_test_local_loader` | 由目录联接组成，供 HOI4 启动器加载测试，不在这里重复修改 |
| 干净上传目录 | `D:\steam\steamapps\workshop\content\394360\kr_stalin_adapted_test_upload` | 由构建脚本生成，专供创意工坊上传，不手工修改、不提交 Git |
| Steam 数字订阅目录 | `...\394360\3746983015` 等 | 已发布或订阅的快照，只读参考，Steam 更新时可能被覆盖 |

当前只开发测试版。正式适配版及所有纯数字工坊目录只读，不随测试版修改同步。

功能入口、生成器归属、状态生命周期和参考副本见 [维护索引](维护索引.md)；检查命令见 `tools/validate.py --help`。

最重要的规则：**只在非数字的 Git 源码目录中开发；测试时使用 loader；发布时只选择 `_upload`。**

## 一轮开发的正确顺序

1. 在源码目录执行 `git status -sb`、`git fetch origin`；工作树干净时再执行 `git pull --ff-only origin main`。
2. 按维护索引修改测试版源码或生成源；运行 `python -B tools/validate.py`。生成器默认只读检查，确认修改后使用 `--write`。
3. 通过对应的 `*_local_loader` 启动器条目进游戏测试。
4. 完成静态检查、游戏测试、制作日志和本地 Git 提交。
5. 需要跨电脑继续时，将提交推送到 GitHub，并核对远端 `main` 哈希。
6. 需要更新创意工坊时，在源码目录运行：

```powershell
pwsh -NoProfile -File tools/Build-CleanWorkshopUpload.ps1
```

脚本会把旧 `_upload` 改名为一个时间戳备份，再从源码生成新的干净上传目录；自动上传备份只保留最近三份，不能代替永久源码参考副本。它会排除 `.git`、开发文档、工具、缓存以及美术草稿。Steam 上传器应选择 `_upload` 对应的启动器条目，不能选择源码目录、loader 或数字订阅目录。

如果只发布指定功能、需要保留上传目录中的其他版本，可在 PowerShell 中使用显式文件清单：`& ./tools/Build-CleanWorkshopUpload.ps1 -UpdatePaths @('common/路径/文件.txt', 'localisation/simp_chinese/文件.yml')`。清单必须包含该功能全部新增或修改的运行文件；其余文件从现有上传快照保留，开发目录里新加的 GUI 不会自动混入。此模式要求已有干净上传目录，不处理删除文件；仍会先完成临时构建和逐文件哈希验证，再整体替换并备份。

## 换电脑继续开发

在新电脑上登录有权限的 GitHub 账号，然后把仓库克隆到一个**非纯数字、可写且稳定**的目录：

```powershell
git clone https://github.com/zxxzvxv85-dot/kr-stalin-adapted-test.git
```

不要克隆到 `3746983015`、`3723313895` 等 Steam 数字目录。首次使用时还需为 HOI4 启动器建立本地 `.mod` 条目或 loader 投影，并使其指向源码目录；创意工坊上传条目则应指向单独生成的 `_upload`。

同一时间只使用一台电脑修改 `main`。换电脑前，上一台电脑必须完成提交和推送；新电脑开始前必须先拉取，并确认 `git status -sb` 没有遗留改动。

## 必装的两个 HOI4 工具

### 1. HOI4 社区制作工坊插件

私有仓库：<https://github.com/zxxzvxv85-dot/hoi4-library-gallery>

建议克隆到：

```powershell
git clone https://github.com/zxxzvxv85-dot/hoi4-library-gallery.git "$env:USERPROFILE\plugins\hoi4-library-gallery"
```

首次安装时，让新电脑上的 Codex 执行：“将
`%USERPROFILE%\plugins\hoi4-library-gallery` 注册到默认个人插件市场并安装”。如果个人市场中已经存在该条目，则直接运行：

```powershell
codex plugin add hoi4-library-gallery@personal
```

安装或更新后新开一个 Codex 任务，使新的 Skill 和 MCP 进程生效。插件负责读取已经提炼的秋起图书馆、霜泽美术馆教程，以及代码、美术和兼容工作流。

### 2. RHoiScribe MCP

RHoiScribe 是另一个独立项目，**不会包含在社区制作工坊插件仓库中，必须另外下载**：

- 项目主页：<https://github.com/czxieddan/RHoiScribe>
- 下载页面：<https://github.com/czxieddan/RHoiScribe/releases>

Windows 下载 `rhoiscribe-windows-x86_64.exe`，放入稳定目录，例如：

```text
%USERPROFILE%\.codex\mcp\RHoiScribe\rhoiscribe-windows-x86_64.exe
```

在 Codex MCP 配置中注册：

```toml
[mcp_servers.rhoiscribe]
command = "C:\\Users\\<用户名>\\.codex\\mcp\\RHoiScribe\\rhoiscribe-windows-x86_64.exe"
args = []
```

安装后读取 `rhoiscribe://hoi4/knowledge/catalog`，并调用一次 `search_hoi4_knowledge` 做冒烟测试。社区制作工坊侧重教程、美术和既有案例，RHoiScribe 负责项目发现、HOI4/CWT 语言检查、引用追踪、错误分类和安全修复预览；当前开发流程要求两者都可用。

更完整的 Mod 结构、测试和上传说明见 [HOI4_MOD入门与本项目维护教程.md](HOI4_MOD入门与本项目维护教程.md)，给 Codex 的强制开发约定见 [AGENTS.md](AGENTS.md)。
