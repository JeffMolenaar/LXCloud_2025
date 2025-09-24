<#
perform_cleanup.ps1

Moves a curated list of non-essential top-level files and folders into
`removed/cleanup-<timestamp>/` so the repository root becomes clean.

Run from the repository root with:
  powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\perform_cleanup.ps1
#>

Set-StrictMode -Version Latest

$ts = Get-Date -Format yyyyMMdd-HHmmss
$removed = Join-Path (Get-Location) ("removed\cleanup-$ts")
New-Item -ItemType Directory -Path $removed | Out-Null

$items = @(
    '.vscode',
    'project',
    'create_sample_controllers.py',
    'create_test_stale_controller.py',
    'database_install.sh',
    'database_setup_manual.sh',
    'DATABASE_SETUP.md',
    'CONTROLLER_API.md',
    'CONTROLLER_STATUS.md',
    'MQTT_TO_API_MIGRATION.md',
    'PER_CONTROLLER_TIMEOUT.md',
    'INSTALL.md',
    'VSCODE_SETUP.md',
    'debug_controller_status.py',
    'fix_controller_status.py',
    'migrate_marker_config.py'
)

Write-Host "Cleanup target: $removed"

$moved = @()
$skipped = @()

foreach ($i in $items) {
    if (Test-Path $i) {
        try {
            Move-Item -LiteralPath $i -Destination $removed -Force -ErrorAction Stop
            Write-Host "Moved: $i"
            $moved += $i
        } catch {
            $msg = $_.Exception.Message
            Write-Host ("Failed to move {0}: {1}" -f $i, $msg)
        }
    } else {
        Write-Host "Not found: $i"
        $skipped += $i
    }
}

Write-Host '--- Summary ---'
Write-Host "Moved items: $($moved.Count)"
foreach ($it in $moved) { Write-Host "  - $it" }
Write-Host "Skipped (not present): $($skipped.Count)"
foreach ($it in $skipped) { Write-Host "  - $it" }

Write-Host "Removed folder created at: $removed"
