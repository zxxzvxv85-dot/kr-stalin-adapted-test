[CmdletBinding()]
param(
    [string]$SourceRoot = "",
    [string]$DestinationRoot = "",
    # An explicit runtime-file allowlist updates an existing upload snapshot.
    # Omitted files keep the upload version, including development-only GUIs.
    [string[]]$UpdatePaths = @()
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Resolve after parameter binding; Windows PowerShell can leave $PSScriptRoot
# empty while evaluating a default parameter expression.
if ([string]::IsNullOrWhiteSpace($SourceRoot)) {
    $SourceRoot = Split-Path -Parent $PSScriptRoot
}
$source = [System.IO.Path]::GetFullPath($SourceRoot).TrimEnd([System.IO.Path]::DirectorySeparatorChar)
if ([string]::IsNullOrWhiteSpace($DestinationRoot)) {
    $DestinationRoot = "$source" + "_upload"
}
$destination = [System.IO.Path]::GetFullPath($DestinationRoot).TrimEnd([System.IO.Path]::DirectorySeparatorChar)

if (-not (Test-Path -LiteralPath $source -PathType Container)) {
    throw "Source directory does not exist: $source"
}
if ($source.Equals($destination, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Source and destination must be different directories."
}

$sourceParent = [System.IO.Path]::GetFullPath((Split-Path -Parent $source)).TrimEnd([System.IO.Path]::DirectorySeparatorChar)
$destinationParent = [System.IO.Path]::GetFullPath((Split-Path -Parent $destination)).TrimEnd([System.IO.Path]::DirectorySeparatorChar)
$destinationName = Split-Path -Leaf $destination
if (-not $sourceParent.Equals($destinationParent, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "For safety, the upload directory must be a sibling of the source directory."
}
if (-not $destinationName.EndsWith("_upload", [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "For safety, the upload directory name must end with _upload."
}

function Assert-GameStopped {
    if (Get-Process -Name hoi4 -ErrorAction SilentlyContinue) {
        throw "Hearts of Iron IV is running. Exit the game before rebuilding the upload directory. No upload files were changed."
    }
}
Assert-GameStopped

$insideWorkTree = git -C $source rev-parse --is-inside-work-tree
if ($LASTEXITCODE -ne 0 -or $insideWorkTree -ne "true") {
    throw "Source directory is not a Git worktree: $source"
}

$excludePatterns = @(
    '^\.git/',
    '^(?:\.gitattributes|\.gitignore|\.editorconfig)$',
    '^[^/]+\.md$',
    '^tools/',
    '^docs/',
    '^output/',
    '^tmp/',
    '^\.vscode/',
    '(?i)(?:^|/)[^/]*(?:_source|_preview(?:_v?\d+)?|_draft)[^/]*\.(?:png|jpe?g|dds|tga|psd)$',
    '(?i)^thumbnail_before_.*$',
    '(?i)^thumbnail_old\.(?:png|jpe?g)$',
    '(?i)^thumbnail_preview\.(?:png|jpe?g)$'
)

$trackedFiles = @(git -C $source -c core.quotepath=false ls-files)
if ($LASTEXITCODE -ne 0) {
    throw "Unable to enumerate tracked files."
}
$untrackedFiles = @(git -C $source -c core.quotepath=false ls-files --others --exclude-standard)
if ($LASTEXITCODE -ne 0) {
    throw "Unable to enumerate untracked files."
}
$candidateFiles = @(($trackedFiles + $untrackedFiles) | Sort-Object -Unique)
$deletedFiles = @(git -C $source -c core.quotepath=false ls-files --deleted)
$deletedSet = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
foreach ($deletedFile in $deletedFiles) {
    [void]$deletedSet.Add($deletedFile)
}

$publishFiles = @(
    $candidateFiles | Where-Object {
        $relativePath = $_
        -not $deletedSet.Contains($relativePath) -and
        -not ($excludePatterns | Where-Object { $relativePath -match $_ })
    }
)

if ($publishFiles.Count -eq 0 -or 'descriptor.mod' -notin $publishFiles) {
    throw "Refusing to publish an empty or descriptor-less mod."
}

$fileSources = [System.Collections.Generic.Dictionary[string,string]]::new([System.StringComparer]::OrdinalIgnoreCase)
foreach ($relativePath in $publishFiles) {
    $fileSources[$relativePath] = $source
}
$selective = $UpdatePaths.Count -gt 0
$updatedFiles = @()
if ($selective) {
    if (-not (Test-Path -LiteralPath (Join-Path $destination 'descriptor.mod') -PathType Leaf)) {
        throw "A selective update requires an existing upload snapshot with descriptor.mod."
    }
    if ((Get-Item -LiteralPath $destination).Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
        throw "Refusing to read a redirected upload directory: $destination"
    }
    $updatedFiles = @($UpdatePaths | ForEach-Object {
        $relative = $_.Replace('\', '/')
        if ([System.IO.Path]::IsPathRooted($relative) -or $relative -match '(^|/)\.\.?(/|$)' -or
            $relative -notin $publishFiles) {
            throw "Update path must name a present, publishable source file: $_"
        }
        $relative
    } | Sort-Object -Unique)
    $fileSources.Clear()
    foreach ($item in (Get-ChildItem -LiteralPath $destination -Recurse -Force)) {
        if ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
            throw "Refusing a redirected item in the upload snapshot: $($item.FullName)"
        }
        if ($item.PSIsContainer) { continue }
        $relative = $item.FullName.Substring($destination.Length + 1).Replace('\', '/')
        if ($excludePatterns | Where-Object { $relative -match $_ }) {
            throw "Selective updates require a clean upload snapshot; unexpected development file: $relative"
        }
        $fileSources[$relative] = $destination
    }
    foreach ($relativePath in $updatedFiles) {
        $fileSources[$relativePath] = $source
    }
    $publishFiles = @($fileSources.Keys | Sort-Object)
}

# Finish and verify a sibling staging directory before touching the active upload.
$staging = "$destination.staging.$([Guid]::NewGuid().ToString('N'))"
New-Item -ItemType Directory -Path $staging -ErrorAction Stop | Out-Null

$copied = 0
foreach ($relativePath in $publishFiles) {
    $copyRoot = $fileSources[$relativePath]
    $sourceFile = [System.IO.Path]::GetFullPath((Join-Path $copyRoot $relativePath))
    $destinationFile = [System.IO.Path]::GetFullPath((Join-Path $staging $relativePath))

    if (-not $sourceFile.StartsWith($copyRoot + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Tracked source path escaped the source root: $relativePath"
    }
    if (-not $destinationFile.StartsWith($staging + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Generated destination path escaped the upload root: $relativePath"
    }
    if (-not (Test-Path -LiteralPath $sourceFile -PathType Leaf)) {
        throw "Tracked file is missing from the working tree: $relativePath"
    }

    $parent = Split-Path -Parent $destinationFile
    if (-not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    Copy-Item -LiteralPath $sourceFile -Destination $destinationFile -Force
    if ((Get-FileHash -LiteralPath $sourceFile -Algorithm SHA256).Hash -ne
        (Get-FileHash -LiteralPath $destinationFile -Algorithm SHA256).Hash) {
        throw "Staging checksum mismatch: $relativePath. The active upload is unchanged."
    }
    $copied++
}

Assert-GameStopped
$backup = $null
if (Test-Path -LiteralPath $destination) {
    $resolvedDestination = (Resolve-Path -LiteralPath $destination).Path
    if (-not $resolvedDestination.Equals($destination, [System.StringComparison]::OrdinalIgnoreCase) -or
        ((Get-Item -LiteralPath $destination).Attributes -band [System.IO.FileAttributes]::ReparsePoint)) {
        throw "Refusing to replace a redirected upload directory: $destination"
    }
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss-fff"
    $backup = "$destination.previous.$timestamp"
    # Directory.Move performs a same-volume rename. Move-Item can partially move
    # a locked directory's children before throwing, leaving an unusable mod.
    [System.IO.Directory]::Move($destination, $backup)
}
try {
    [System.IO.Directory]::Move($staging, $destination)
}
catch {
    if ($null -ne $backup -and -not (Test-Path -LiteralPath $destination)) {
        [System.IO.Directory]::Move($backup, $destination)
    }
    throw
}
if ($null -ne $backup) {
    Write-Host "Previous upload retained at: $backup"
}

# 每次重建都会留下一个约 400 MB 的 _upload.previous.*；只保留最近几份，
# 更早的自动清掉（历史上曾累积到 184 份 / 73 GB）。清理失败不影响打包结果。
$backupKeep = 3
$backups = @(
    Get-ChildItem -LiteralPath $destinationParent -Directory |
        Where-Object { $_.Name -like "$destinationName.previous.*" } |
        Sort-Object Name -Descending
)
if ($backups.Count -gt $backupKeep) {
    foreach ($old in $backups[$backupKeep..($backups.Count - 1)]) {
        $resolved = [System.IO.Path]::GetFullPath($old.FullName)
        if (-not $resolved.StartsWith($destinationParent + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
            Write-Warning "Skip pruning outside the upload parent: $resolved"
            continue
        }
        if ($old.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
            Write-Warning "Skip redirected backup: $resolved"
            continue
        }
        Remove-Item -LiteralPath $resolved -Recurse -Force
        Write-Host "Pruned old backup: $($old.Name)"
    }
}
# A failed build must never destroy the newest recovery source.

$totalBytes = (Get-ChildItem -LiteralPath $destination -Recurse -File | Measure-Object -Property Length -Sum).Sum
[pscustomobject]@{
    Source = $source
    Destination = $destination
    CopiedFiles = $copied
    BuildMode = $(if ($selective) { 'SelectedFiles' } else { 'FullSource' })
    UpdatedSourceFiles = $(if ($selective) { $updatedFiles.Count } else { $copied })
    PreservedUploadFiles = $(if ($selective) { $copied - $updatedFiles.Count } else { 0 })
    ExcludedTrackedFiles = $trackedFiles.Count - @($publishFiles | Where-Object { $_ -in $trackedFiles }).Count
    IncludedUntrackedFiles = @($publishFiles | Where-Object { $_ -in $untrackedFiles }).Count
    SizeMiB = [Math]::Round($totalBytes / 1MB, 3)
}
