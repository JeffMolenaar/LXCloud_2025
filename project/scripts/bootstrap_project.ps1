<#
Bootstrap script: create a clean `project/working_copy` containing the working project.

Behavior:
- If `project/working_copy` exists it will be renamed to `project/working_copy.bak-<timestamp>`.
- Copies a curated list of folders and root files into the new `project/working_copy`.
#>

param()

Set-StrictMode -Version Latest

# Repository root is the parent directory of the scripts folder
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Split-Path -Parent $scriptPath
Push-Location $root

$projectDir = Join-Path $root 'project'

# If project exists, move to backup
function Backup-IfExists([string]$path) {
    if (Test-Path $path) {
        $bak = "$path.bak-$(Timestamp)"
        Write-Host ("Backing up existing {0} -> {1}" -f $path, $bak)
        Rename-Item -Path $path -NewName (Split-Path $bak -Leaf)
    }
}

$working = $projectDir

function Timestamp {
    return (Get-Date).ToString('yyyyMMdd-HHmmss')
}

Backup-IfExists $working
Write-Host ("Creating {0}..." -f $working)
New-Item -ItemType Directory -Path $working -Force | Out-Null

$foldersToCopy = @('app','config','static','templates','scripts','archive')
$filesToCopy = @('run.py','requirements.txt','Dockerfile','README.md','VERSION','database.conf.example')

foreach ($f in $foldersToCopy) {
    if (Test-Path $f) {
        $dest = Join-Path $working $f
    Write-Host ("Copying folder: {0} -> {1}" -f $f, $dest)
        Copy-Item -Path $f -Destination $dest -Recurse -Force
    } else {
    Write-Host ("Skipping missing folder: {0}" -f $f)
    }
}

foreach ($f in $filesToCopy) {
    if (Test-Path $f) {
    Write-Host ("Copying file: {0}" -f $f)
        Copy-Item -Path $f -Destination $working -Force
    } else {
    Write-Host ("Skipping missing file: {0}" -f $f)
    }
}

Write-Host ("Bootstrap complete. Working copy is at: {0}" -f $working)

Pop-Location
