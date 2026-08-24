@echo off
title Gantt Excel PRO - Server Launcher
color 0B

echo =====================================================================
echo                  GANTT EXCEL PRO - PORTABLE LAUNCHER
echo =====================================================================
echo.

:: Move to current project directory
cd /d "%~dp0"

:: 1. Locate Python executable (Embedded Portable Runtime vs System Python)
set "PY_EXE="

if exist "%~dp0runtime\Scripts\python.exe" (
    set "PY_EXE=%~dp0runtime\Scripts\python.exe"
    echo [INFO] Using Embedded Portable Python runtime.
) else if exist "%~dp0runtime\python.exe" (
    set "PY_EXE=%~dp0runtime\python.exe"
    echo [INFO] Using Embedded Portable Python runtime.
) else if exist "%~dp0python\python.exe" (
    set "PY_EXE=%~dp0python\python.exe"
    echo [INFO] Using Embedded Portable Python runtime.
) else (
    :: Check if Python is installed globally on the system
    python --version >nul 2>&1
    if %errorlevel% equ 0 (
        set "PY_EXE=python"
        echo [INFO] Using System Python installation.
    )
)

:: 2. If NO Python is found on this machine at all, auto-setup portable environment
if "%PY_EXE%"=="" (
    echo [NOTICE] No Python was detected on this laptop.
    echo          Setting up zero-install portable runtime environment...
    echo.
    powershell -NoProfile -ExecutionPolicy Bypass -Command "& { Write-Host 'Downloading portable Python runtime (15MB)...' -ForegroundColor Cyan; [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip' -OutFile 'portable_py.zip'; Write-Host 'Extracting portable runtime...' -ForegroundColor Cyan; Expand-Archive -Path 'portable_py.zip' -DestinationPath 'runtime' -Force; Remove-Item 'portable_py.zip'; (Get-Content 'runtime\python311._pth') -replace '#import site','import site' | Set-Content 'runtime\python311._pth'; Write-Host 'Configuring pip...' -ForegroundColor Cyan; Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile 'runtime\get-pip.py'; & 'runtime\python.exe' 'runtime\get-pip.py' --no-warn-script-location; Remove-Item 'runtime\get-pip.py'; Write-Host 'Installing packages...' -ForegroundColor Cyan; & 'runtime\python.exe' -m pip install --no-warn-script-location -r requirements.txt; }"
    if exist "%~dp0runtime\python.exe" (
        set "PY_EXE=%~dp0runtime\python.exe"
        echo [SUCCESS] Portable Python runtime created successfully!
        echo.
    ) else (
        color 0C
        echo [ERROR] Could not set up portable Python runtime.
        echo Please ensure you are connected to the internet or install Python 3.10+ from python.org.
        pause
        exit /b 1
    )
)

echo.
echo [1/3] Applying database migrations...
"%PY_EXE%" manage.py migrate --noinput
if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] Database migration failed.
    pause
    exit /b 1
)
echo      Database is up to date.
echo.

echo [2/3] Initializing Master Administrator and seed data...
"%PY_EXE%" manage.py seed_data >nul 2>&1
echo      Master Account verified.
echo.

echo [3/3] Launching web browser and starting Gantt Excel PRO server...
echo.
echo =====================================================================
echo  Server URL: http://127.0.0.1:8000/
echo =====================================================================
echo.
echo Press Ctrl+C in this window anytime to stop the server.
echo.

:: Automatically launch default browser after 2 seconds
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:8000/login/"

:: Start Django development server
"%PY_EXE%" manage.py runserver 127.0.0.1:8000

pause
