$archive = Join-Path -Path (Get-Location) -ChildPath 'archive\test-scripts-removed-20250924'
if (!(Test-Path $archive)) { New-Item -ItemType Directory -Path $archive | Out-Null }
$tests = Get-ChildItem -Path . -Filter 'test_*.py' -File
if (!$tests) { Write-Host 'No test_*.py files found in root.'; exit 0 }
foreach ($t in $tests) {
    Move-Item -LiteralPath $t.FullName -Destination $archive -Force
    Write-Host ("Moved: $($t.Name)")
}
Write-Host '--- New root listing (selected) ---'
$keep = @('app','config','static','templates','run.py','requirements.txt','Dockerfile','VERSION','database.conf.example','scripts','archive','removed')
foreach ($k in $keep) {
    if (Test-Path $k) { Write-Host $k }
}
