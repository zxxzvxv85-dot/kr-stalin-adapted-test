[CmdletBinding()]
param(
    [string]$SourceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$DestinationRoot = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

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

$insideWorkTree = git -C $source rev-parse --is-inside-work-tree
if ($LASTEXITCODE -ne 0 -or $insideWorkTree -ne "true") {
    throw "Source directory is not a Git worktree: $source"
}

$excludePatterns = @(
    '^(?:\.gitattributes|\.gitignore)$',
    '^[^/]+\.md$',
    '^tools/',
    '(?i)(?:^|/)[^/]*(?:_source|_preview(?:_v?\d+)?|_draft)[^/]*\.(?:png|jpe?g|dds|tga|psd)$',
    '(?i)^thumbnail_before_.*$',
    '(?i)^thumbnail_old\.(?:png|jpe?g)$',
    '(?i)^thumbnail_preview\.(?:png|jpe?g)$'
)

$trackedFiles = @(git -C $source -c core.quotepath=false ls-files)
if ($LASTEXITCODE -ne 0) {
    throw "Unable to enumerate tracked files."
}
$deletedFiles = @(git -C $source -c core.quotepath=false ls-files --deleted)
$deletedSet = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
foreach ($deletedFile in $deletedFiles) {
    [void]$deletedSet.Add($deletedFile)
}

$publishFiles = @(
    $trackedFiles | Where-Object {
        $relativePath = $_
        -not $deletedSet.Contains($relativePath) -and
        -not ($excludePatterns | Where-Object { $relativePath -match $_ })
    }
)

if (Test-Path -LiteralPath $destination) {
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $backup = "$destination.previous.$timestamp"
    $resolvedDestination = (Resolve-Path -LiteralPath $destination).Path
    if (-not $resolvedDestination.Equals($destination, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Resolved upload directory differs from the verified destination: $resolvedDestination"
    }
    Move-Item -LiteralPath $destination -Destination $backup
    Write-Host "Previous upload directory moved to: $backup"
}

# Retain only the newest safety backup so repeated builds do not accumulate
# large .previous.* directories indefinitely.
$previousDirectories = @(
    Get-ChildItem -LiteralPath $destinationParent -Directory -Filter "$destinationName.previous.*" |
        Sort-Object Name -Descending
)
foreach ($oldPreviousDirectory in ($previousDirectories | Select-Object -Skip 1)) {
    $oldPreviousPath = [System.IO.Path]::GetFullPath($oldPreviousDirectory.FullName).TrimEnd([System.IO.Path]::DirectorySeparatorChar)
    $oldPreviousParent = [System.IO.Path]::GetFullPath((Split-Path -Parent $oldPreviousPath)).TrimEnd([System.IO.Path]::DirectorySeparatorChar)
    $oldPreviousName = Split-Path -Leaf $oldPreviousPath
    if (-not $oldPreviousParent.Equals($destinationParent, [System.StringComparison]::OrdinalIgnoreCase) -or
        -not $oldPreviousName.StartsWith("$destinationName.previous.", [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove an unverified previous upload directory: $oldPreviousPath"
    }
    Remove-Item -LiteralPath $oldPreviousPath -Recurse -Force
    Write-Host "Removed older upload backup: $oldPreviousPath"
}

New-Item -ItemType Directory -Path $destination -Force | Out-Null

$copied = 0
foreach ($relativePath in $publishFiles) {
    $sourceFile = [System.IO.Path]::GetFullPath((Join-Path $source $relativePath))
    $destinationFile = [System.IO.Path]::GetFullPath((Join-Path $destination $relativePath))

    if (-not $sourceFile.StartsWith($source, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Tracked source path escaped the source root: $relativePath"
    }
    if (-not $destinationFile.StartsWith($destination, [System.StringComparison]::OrdinalIgnoreCase)) {
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
    $copied++
}

$totalBytes = (Get-ChildItem -LiteralPath $destination -Recurse -File | Measure-Object -Property Length -Sum).Sum
[pscustomobject]@{
    Source = $source
    Destination = $destination
    CopiedFiles = $copied
    ExcludedTrackedFiles = $trackedFiles.Count - $publishFiles.Count
    SizeMiB = [Math]::Round($totalBytes / 1MB, 3)
}
