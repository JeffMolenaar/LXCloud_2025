$root = Get-Location
$src = Join-Path $root 'project\working_copy'
$dst = Join-Path $root 'project'
if (!(Test-Path $src)) {
    Write-Host "Source not found: $src"
    exit 1
}
$items = Get-ChildItem -Path $src -Force
foreach ($it in $items) {
    $target = Join-Path $dst $it.Name
    if (Test-Path $target) { Remove-Item -Recurse -Force $target }
    Move-Item -LiteralPath $it.FullName -Destination $dst
    Write-Host "Moved: $($it.Name)"
}
# remove the empty working_copy folder if present
if (Test-Path $src) { Remove-Item -Recurse -Force $src; Write-Host 'Removed: project\working_copy' }
Write-Host 'Done.'
