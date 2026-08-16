# Stalin Returns 适配版 / 测试版开发仓库

本仓库保存 Mod 的完整开发源码、开发工具、美术源文件和维护记录。GitHub 是跨电脑同步开发进度的唯一来源，Steam 创意工坊目录不能代替源码仓库。

## 本地目录如何分工

当前开发流程将源码、游戏加载入口和创意工坊上传内容分开存放：

| 目录类型 | 本机示例 | 用途 |
| --- | --- | --- |
| Git 源码目录 | `D:\steam\steamapps\workshop\content\394360\kr_stalin_adapted_test` | 实际编辑、检查、提交和推送的位置 |
| 启动器投影 | `D:\steam\steamapps\workshop\content\394360\kr_stalin_adapted_test_local_loader` | 由目录联接组成，供 HOI4 启动器加载测试，不在这里重复修改 |
| 干净上传目录 | `D:\steam\steamapps\workshop\content\394360\kr_stalin_adapted_test_upload` | 由构建脚本生成，专供创意工坊上传，不手工修改、不提交 Git |
| Steam 数字订阅目录 | `...\394360\3746983015` 等 | 已发布或订阅的快照，只读参考，Steam 更新时可能被覆盖 |

正式适配版同样采用 `kr_stalin_adapted_local`、`kr_stalin_adapted_local_loader` 和 `kr_stalin_adapted_local_upload` 三目录分离的结构。

最重要的规则：**只在非数字的 Git 源码目录中开发；测试时使用 loader；发布时只选择 `_upload`。**

## 一轮开发的正确顺序

1. 在源码目录执行 `git status -sb`、`git fetch origin`；工作树干净时再执行 `git pull --ff-only origin main`。
2. 只修改源码目录，并按需要同步适配版与测试版。
3. 通过对应的 `*_local_loader` 启动器条目进游戏测试。
4. 完成静态检查、游戏测试、制作日志和本地 Git 提交。
5. 需要跨电脑继续时，将提交推送到 GitHub，并核对远端 `main` 哈希。
6. 需要更新创意工坊时，在源码目录运行：

```powershell
.\tools\Build-CleanWorkshopUpload.ps1
```

脚本会把旧 `_upload` 改名为一个时间戳备份，再从源码生成新的干净上传目录。它会排除 `.git`、开发文档、工具、缓存以及美术草稿。Steam 上传器应选择 `_upload` 对应的启动器条目，不能选择源码目录、loader 或数字订阅目录。

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
