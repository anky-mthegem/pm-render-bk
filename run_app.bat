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

echo [1/3] Applying database migrations...
python manage.py migrate --noinput
if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] Database migration failed.
    pause
    exit /b 1
)
echo      Migrations up to date.
echo.

echo [2/3] Checking demo data and admin credentials...
python manage.py seed_data >nul 2>&1
echo      Admin account ready: username 'aman', password '123456'
echo.

echo [3/3] Launching web browser and starting Django server...
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
