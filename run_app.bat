@echo off
setlocal EnableDelayedExpansion
title Milestone Management - Server Launcher
color 0B

echo =====================================================================
echo                MILESTONE MANAGEMENT - PORTABLE LAUNCHER
echo =====================================================================
echo.

:: Move to current project directory
cd /d "%~dp0"

:: 1. Check for existing local virtual environment or portable runtime
set "PY_EXE="
if exist "%~dp0runtime\Scripts\python.exe" set "PY_EXE=%~dp0runtime\Scripts\python.exe"
if not defined PY_EXE if exist "%~dp0venv\Scripts\python.exe" set "PY_EXE=%~dp0venv\Scripts\python.exe"
if not defined PY_EXE if exist "%~dp0.venv\Scripts\python.exe" set "PY_EXE=%~dp0.venv\Scripts\python.exe"
if not defined PY_EXE if exist "%~dp0runtime\python.exe" set "PY_EXE=%~dp0runtime\python.exe"

:: 2. If no local runtime exists, try creating one using system Python
if not defined PY_EXE (
    python -c "import sys" >nul 2>&1
    if not errorlevel 1 (
        echo [INFO] Creating local virtual environment in runtime folder...
        python -m venv "%~dp0runtime"
        if exist "%~dp0runtime\Scripts\python.exe" (
            set "PY_EXE=%~dp0runtime\Scripts\python.exe"
        ) else (
            set "PY_EXE=python"
        )
    )
)

if not defined PY_EXE (
    py -c "import sys" >nul 2>&1
    if not errorlevel 1 (
        echo [INFO] Creating local virtual environment via py launcher...
        py -m venv "%~dp0runtime"
        if exist "%~dp0runtime\Scripts\python.exe" (
            set "PY_EXE=%~dp0runtime\Scripts\python.exe"
        ) else (
            set "PY_EXE=py"
        )
    )
)

:: 3. If STILL no Python is found, call download helper subroutine
if not defined PY_EXE (
    call :SETUP_PORTABLE_PYTHON
)

if not defined PY_EXE (
    color 0C
    echo [ERROR] No Python environment could be established.
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 4. Verify Django is installed; if not, install requirements
"%PY_EXE%" -c "import django" >nul 2>&1
if errorlevel 1 (
    echo.
    echo [INFO] Installing required packages: Django, DRF, OpenPyXL...
    "%PY_EXE%" -m pip install -r "%~dp0requirements.txt"
    if errorlevel 1 (
        color 0C
        echo.
        echo [ERROR] Failed to install requirements. Please check your internet connection.
        pause
        exit /b 1
    )
    echo [SUCCESS] Dependencies installed successfully.
)

echo [INFO] Python runtime ready.
echo.
echo [1/3] Applying database migrations...
"%PY_EXE%" manage.py migrate --noinput
if errorlevel 1 (
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

echo [3/3] Starting Milestone Management server...
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
exit /b 0

:: ========================================================================
:: Subroutines
:: ========================================================================
:SETUP_PORTABLE_PYTHON
echo [NOTICE] Setting up standalone portable Python runtime...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference='SilentlyContinue'; [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip' -OutFile 'portable_py.zip'; Expand-Archive -Path 'portable_py.zip' -DestinationPath 'runtime' -Force; Remove-Item 'portable_py.zip'; $pth=Get-Content 'runtime\python311._pth'; $pth -replace '#import site','import site' | Set-Content 'runtime\python311._pth'; Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile 'runtime\get-pip.py'; & 'runtime\python.exe' 'runtime\get-pip.py' --no-warn-script-location; Remove-Item 'runtime\get-pip.py';"
if exist "%~dp0runtime\python.exe" set "PY_EXE=%~dp0runtime\python.exe"
exit /b 0
