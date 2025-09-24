$python = 'python'
$errors = @()
Get-ChildItem -Path (Join-Path (Get-Location) 'project') -Recurse -Include *.py | ForEach-Object {
    $file = $_.FullName
    try {
        & $python -m py_compile $file 2>$null
    } catch {
        $errors += "$file : $($_.Exception.Message)"
    }
}
if ($errors.Count -gt 0) {
    Write-Host "PYTHON COMPILE ERRORS:" -ForegroundColor Red
    $errors | ForEach-Object { Write-Host $_ }
    exit 1
} else {
    Write-Host "All python files in project/ compiled successfully." -ForegroundColor Green
}
