$root = Get-Location
$timestamp = (Get-Date).ToString('yyyyMMdd-HHmmss')
$removedDir = Join-Path $root "removed\project-root-$timestamp"
New-Item -ItemType Directory -Path $removedDir | Out-Null

# Items to move from repo root into removed archive (these are runtime duplicates)
$items = @('app','config','static','templates','run.py','requirements.txt','Dockerfile','docker-compose.yml','scripts')

foreach ($item in $items) {
    $path = Join-Path $root $item
    if (Test-Path $path) {
        # Don't move the project folder
        if ($item -eq 'project') { continue }
        try {
            Move-Item -LiteralPath $path -Destination $removedDir -Force
            Write-Host "Moved: $item -> $removedDir"
        } catch {
            Write-Host "Failed to move: $item : $_"
        }
    } else {
        Write-Host "Not found (skipped): $item"
    }
}

Write-Host "Root runtime duplicates moved to: $removedDir"
