# Milestone Management - PowerShell Launcher
Set-Location -Path $PSScriptRoot

Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "               MILESTONE MANAGEMENT - SERVER LAUNCHER" -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "[INFO] Creating virtual environment (.venv)..." -ForegroundColor Yellow
    python -m venv "$PSScriptRoot\.venv"
}

if (Test-Path $venvPython) {
    $pyExe = $venvPython
} else {
    $pyExe = "python"
}

Write-Host "[INFO] Active Python: $pyExe" -ForegroundColor Cyan

# Check if packages exist
& $pyExe -c "import django, rest_framework, openpyxl" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[1/3] Installing requirements..." -ForegroundColor Yellow
    & $pyExe -m pip install -r "$PSScriptRoot\requirements.txt"
} else {
    Write-Host "[1/3] Dependencies verified." -ForegroundColor Green
}

Write-Host "[2/3] Applying database migrations..." -ForegroundColor Green
& $pyExe "$PSScriptRoot\manage.py" migrate --noinput
& $pyExe "$PSScriptRoot\manage.py" seed_data

Write-Host "[3/3] Starting server at http://127.0.0.1:8000/ ..." -ForegroundColor Cyan
Start-Process "http://127.0.0.1:8000/login/"
& $pyExe "$PSScriptRoot\manage.py" runserver 127.0.0.1:8000
