$src = Get-Location
$dst = Join-Path $src 'project'
if (!(Test-Path $dst)) { New-Item -ItemType Directory -Path $dst | Out-Null }
$items = @('app','config','static','templates','run.py','requirements.txt','Dockerfile','docker-compose.yml','database.conf.example','VERSION','scripts','README.md')
foreach ($i in $items) {
    $srcPath = Join-Path $src $i
    if (Test-Path $srcPath) {
        $destPath = Join-Path $dst $i
        if (Test-Path $destPath) { Remove-Item -Recurse -Force $destPath }
        Copy-Item -Recurse -Force -Path $srcPath -Destination $dst
        Write-Host "Copied: $i"
    } else {
        Write-Host "Skipped (not found): $i"
    }
}
Write-Host "Project working copy created at: $dst"