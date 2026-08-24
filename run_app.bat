@echo off
title Gantt Excel PRO - Server Launcher
color 0B

echo =====================================================================
echo                  GANTT EXCEL PRO - LAUNCHER
echo =====================================================================
echo.

:: Move to current project directory
cd /d "%~dp0"

:: Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] Python was not found in your system PATH!
    echo Please install Python 3.12+ and add it to your PATH.
    echo.
    pause
    exit /b 1
)

echo [1/4] Checking Python packages and dependencies...
python -c "import django, rest_framework, openpyxl" >nul 2>&1
if %errorlevel% neq 0 (
    echo      Installing missing dependencies (Django, DRF, openpyxl)...
    python -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        color 0C
        echo [ERROR] Failed to install dependencies from requirements.txt!
        echo Please ensure you have internet access or run: pip install -r requirements.txt
        pause
        exit /b 1
    )
)
echo      Dependencies are ready.
echo.

echo [2/4] Applying database migrations...
python manage.py migrate --noinput
if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] Database migration failed.
    pause
    exit /b 1
)
echo      Database is up to date.
echo.

echo [3/4] Initializing Master Administrator and seed data...
python manage.py seed_data >nul 2>&1
echo      Master Account: username 'aman', password '123456'
echo.

echo [4/4] Launching web browser and starting Django server...
echo.
echo =====================================================================
echo  Server URL: http://127.0.0.1:8000/
echo  Admin User: aman
echo  Admin Pass: 123456
echo =====================================================================
echo.
echo Press Ctrl+C in this terminal window anytime to stop the server.
echo.

:: Automatically launch default browser after 2 seconds
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:8000/login/"

:: Start Django development server
python manage.py runserver 127.0.0.1:8000

pause
