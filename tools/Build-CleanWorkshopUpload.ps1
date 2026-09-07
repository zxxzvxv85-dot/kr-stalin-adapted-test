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
    '^(?:\.gitattributes|\.gitignore)$',
    '^[^/]+\.md$',
    '^tools/',
    '^output/',
    '^tmp/',
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

# Finish and verify a sibling staging directory before touching the active upload.
$staging = "$destination.staging.$([Guid]::NewGuid().ToString('N'))"
New-Item -ItemType Directory -Path $staging -ErrorAction Stop | Out-Null

$copied = 0
foreach ($relativePath in $publishFiles) {
    $sourceFile = [System.IO.Path]::GetFullPath((Join-Path $source $relativePath))
    $destinationFile = [System.IO.Path]::GetFullPath((Join-Path $staging $relativePath))

    if (-not $sourceFile.StartsWith($source + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
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
# Backups are retained; a failed build must never destroy the recovery source.

$totalBytes = (Get-ChildItem -LiteralPath $destination -Recurse -File | Measure-Object -Property Length -Sum).Sum
[pscustomobject]@{
    Source = $source
    Destination = $destination
    CopiedFiles = $copied
    ExcludedTrackedFiles = $trackedFiles.Count - @($publishFiles | Where-Object { $_ -in $trackedFiles }).Count
    IncludedUntrackedFiles = @($publishFiles | Where-Object { $_ -in $untrackedFiles }).Count
    SizeMiB = [Math]::Round($totalBytes / 1MB, 3)
}
