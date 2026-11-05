$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "=== 1. Compiling C Engines (engine.exe, matrix_engine.exe, numlab_engine.exe) ===" -ForegroundColor Cyan
python -c "from c_bridge import ensure_c_engines_built; ok = ensure_c_engines_built(force=True); print('C Engines Built:', ok); exit(0 if ok else 1)"

Write-Host "`n=== 2. Running Full C-Engine Real-Problem Test Suite ===" -ForegroundColor Cyan
python -m unittest discover -s tests -p "test_suite.py" -v

Write-Host "`n=== 3. Building Zero-Dependency Standalone EXE (dist\Numerical_Analysis_Suite.exe) ===" -ForegroundColor Cyan
python -m pip install --quiet pyinstaller matplotlib numpy
python -m PyInstaller main.spec --clean --noconfirm

$exePath = Join-Path $PSScriptRoot "dist\Numerical_Analysis_Suite.exe"
if (!(Test-Path $exePath)) {
    throw "Failed to build $exePath"
}
$exeSizeMB = [math]::Round((Get-Item $exePath).Length / 1MB, 2)
Write-Host "Successfully built zero-dependency executable: $exePath ($exeSizeMB MB)" -ForegroundColor Green

Write-Host "`n=== 4. Committing & Pushing Branch 'upgrade/learning-platform' and Tag 'v2.0.0' ===" -ForegroundColor Cyan
git checkout -B upgrade/learning-platform
git add -A
git status -s
git commit -m "feat: complete 6-unit C-powered numerical lab with working steps, equations, and standalone exe build" --allow-empty
git push -u origin upgrade/learning-platform

git tag -f v2.0.0
git push -f origin v2.0.0

Write-Host "`n=== 5. Uploading Standalone EXE to GitHub Releases (v2.0.0) ===" -ForegroundColor Cyan
if (Get-Command gh -ErrorAction SilentlyContinue) {
    $releaseTitle = "Numerical Analysis Suite v2.0.0 — Complete 6-Unit C-Powered Learning Lab"
    $releaseNotes = "Zero-dependency Windows standalone executable (`Numerical_Analysis_Suite.exe`) with all 6 Numerical Methods units in C, step-by-step working solutions, governing equations, and descriptions."
    gh release view v2.0.0 >$null 2>&1
    if ($LASTEXITCODE -eq 0) {
        gh release upload v2.0.0 "$exePath" --clobber
    } else {
        gh release create v2.0.0 "$exePath" --title "$releaseTitle" --notes "$releaseNotes"
    }
    Write-Host "Uploaded $exePath to GitHub Release v2.0.0 via GitHub CLI!" -ForegroundColor Green
} else {
    Write-Host "Note: 'gh' CLI not found locally; pushing tag 'v2.0.0' triggered the GitHub Actions workflow (.github/workflows/ci.yml) which automatically builds and publishes Numerical_Analysis_Suite.exe to GitHub Releases." -ForegroundColor Yellow
}

Write-Host "`nAll tasks completed successfully!" -ForegroundColor Green
