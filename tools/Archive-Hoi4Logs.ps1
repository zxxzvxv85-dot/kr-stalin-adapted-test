<#
把当前 HOI4 运行日志归档到 tmp/log_history/<时间戳>/，方便事后对比「前一次运行」。

用法（游戏运行中或刚退出都可以，越早越好——下次启动会覆盖 logs/）：
    powershell -NoProfile -ExecutionPolicy Bypass -File tools\Archive-Hoi4Logs.ps1
可选 -Tag 给这次归档起个名字：
    ... -File tools\Archive-Hoi4Logs.ps1 -Tag "测试-新外交线"

注意：HOI4 每次启动都会重写 Documents/Paradox Interactive/Hearts of Iron IV/logs/ 下的
error.log / system.log / game.log / setup.log；只有崩溃的那几次会连同日志一起存进
Documents/.../crashes/<时间戳>/。所以想看「上一次」的日志，必须在下次启动前先归档。
#>
[CmdletBinding()]
param(
    [string]$Tag = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$documents = Join-Path $env:USERPROFILE "Documents\Paradox Interactive\Hearts of Iron IV"
$logs = Join-Path $documents "logs"
if (-not (Test-Path -LiteralPath $logs -PathType Container)) {
    throw "找不到 HOI4 日志目录：$logs"
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$name = if ([string]::IsNullOrWhiteSpace($Tag)) { $stamp } else { "$stamp-$Tag" }
$destination = Join-Path (Join-Path $repoRoot "tmp\log_history") $name
New-Item -ItemType Directory -Path $destination -Force | Out-Null

$copied = 0
foreach ($file in Get-ChildItem -LiteralPath $logs -File) {
    Copy-Item -LiteralPath $file.FullName -Destination (Join-Path $destination $file.Name) -Force
    $copied++
}

# 崩溃目录里也连着日志，一并留一份索引，方便知道哪次崩过
$crashRoot = Join-Path $documents "crashes"
if (Test-Path -LiteralPath $crashRoot) {
    $crashes = Get-ChildItem -LiteralPath $crashRoot -Directory | Sort-Object LastWriteTime -Descending |
        Select-Object -First 5 |
        ForEach-Object { "{0}  {1}" -f $_.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss"), $_.Name }
    $crashes | Set-Content -LiteralPath (Join-Path $destination "recent-crashes.txt") -Encoding utf8
}

Write-Host "已归档 $copied 个日志文件到：$destination"
