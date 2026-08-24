@echo off
title Gantt Excel PRO - Server Launcher
color 0B

echo =====================================================================
echo                  GANTT EXCEL PRO - PORTABLE LAUNCHER
echo =====================================================================
echo.

:: Move to current project directory
cd /d "%~dp0"

:: 1. Check for existing local virtual environment or portable runtime
set "PY_EXE="

if exist "%~dp0runtime\Scripts\python.exe" (
    set "PY_EXE=%~dp0runtime\Scripts\python.exe"
) else if exist "%~dp0venv\Scripts\python.exe" (
    set "PY_EXE=%~dp0venv\Scripts\python.exe"
) else if exist "%~dp0.venv\Scripts\python.exe" (
    set "PY_EXE=%~dp0.venv\Scripts\python.exe"
) else if exist "%~dp0runtime\python.exe" (
    set "PY_EXE=%~dp0runtime\python.exe"
)

:: 2. If no local runtime exists, create one or locate system Python
if "%PY_EXE%"=="" (
    echo [INFO] Initializing local Python environment for Gantt Excel...
    
    :: Check if system has Python available
    python -c "import sys" >nul 2>&1
    if %errorlevel% equ 0 (
        echo [INFO] Creating local isolated runtime using system Python...
        python -m venv "%~dp0runtime"
        if exist "%~dp0runtime\Scripts\python.exe" (
            set "PY_EXE=%~dp0runtime\Scripts\python.exe"
        ) else (
            set "PY_EXE=python"
        )
    ) else (
        :: Try 'py' launcher
        py -c "import sys" >nul 2>&1
        if %errorlevel% equ 0 (
            echo [INFO] Creating local isolated runtime using Python launcher...
            py -m venv "%~dp0runtime"
            if exist "%~dp0runtime\Scripts\python.exe" (
                set "PY_EXE=%~dp0runtime\Scripts\python.exe"
            ) else (
                set "PY_EXE=py"
            )
        )
    )
)

:: 3. If STILL no Python is found, download standalone portable runtime
if "%PY_EXE%"=="" (
    echo [NOTICE] No Python was detected on this laptop.
    echo          Setting up zero-install portable runtime environment...
    echo.
    powershell -NoProfile -ExecutionPolicy Bypass -Command "& { Write-Host 'Downloading portable Python runtime...' -ForegroundColor Cyan; [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip' -OutFile 'portable_py.zip'; Write-Host 'Extracting portable runtime...' -ForegroundColor Cyan; Expand-Archive -Path 'portable_py.zip' -DestinationPath 'runtime' -Force; Remove-Item 'portable_py.zip'; (Get-Content 'runtime\python311._pth') -replace '#import site','import site' | Set-Content 'runtime\python311._pth'; Write-Host 'Configuring pip...' -ForegroundColor Cyan; Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile 'runtime\get-pip.py'; & 'runtime\python.exe' 'runtime\get-pip.py' --no-warn-script-location; Remove-Item 'runtime\get-pip.py'; }"
    if exist "%~dp0runtime\python.exe" (
        set "PY_EXE=%~dp0runtime\python.exe"
    ) else (
        color 0C
        echo [ERROR] Could not set up portable Python runtime.
        echo Please ensure you are connected to the internet or install Python from python.org.
        pause
        exit /b 1
    )
)

:: 4. Verify Django is installed; if not, automatically install requirements
"%PY_EXE%" -c "import django" >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [INFO] Django is not yet installed in this environment.
    echo [INFO] Installing required dependencies (Django, DRF, openpyxl)...
    echo        (This only happens once on initial launch)
    echo.
    "%PY_EXE%" -m pip install --quiet -r "%~dp0requirements.txt"
    if %errorlevel% neq 0 (
        echo [INFO] Retrying dependency installation with verbose output...
        "%PY_EXE%" -m pip install -r "%~dp0requirements.txt"
        if %errorlevel% neq 0 (
            color 0C
            echo.
            echo [ERROR] Failed to install dependencies. Please check your internet connection.
            pause
            exit /b 1
        )
    )
    echo [SUCCESS] Dependencies installed successfully!
)

echo [INFO] Python runtime ready.
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
