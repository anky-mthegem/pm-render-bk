@echo off
setlocal
title Milestone Management - Server Launcher
color 0B

echo =====================================================================
echo                MILESTONE MANAGEMENT - SERVER LAUNCHER
echo =====================================================================
echo.

cd /d "%~dp0"

:: -----------------------------------------------------------------------
:: 1. Check for existing virtual environment
:: -----------------------------------------------------------------------
set "PY_EXE="
if exist "%~dp0.venv\Scripts\python.exe" (
    set "PY_EXE=%~dp0.venv\Scripts\python.exe"
    goto :VENV_READY
)
if exist "%~dp0venv\Scripts\python.exe" (
    set "PY_EXE=%~dp0venv\Scripts\python.exe"
    goto :VENV_READY
)
if exist "%~dp0runtime\Scripts\python.exe" (
    set "PY_EXE=%~dp0runtime\Scripts\python.exe"
    goto :VENV_READY
)

:: -----------------------------------------------------------------------
:: 2. If no virtual environment exists, create one using system Python
:: -----------------------------------------------------------------------
echo [INFO] No local virtual environment found. Setting up .venv...

set "SYS_PY="
python --version >nul 2>&1
if not errorlevel 1 (
    set "SYS_PY=python"
    goto :CREATE_VENV
)

py --version >nul 2>&1
if not errorlevel 1 (
    set "SYS_PY=py"
    goto :CREATE_VENV
)

:NO_PYTHON
color 0C
echo [ERROR] Python was not detected on this system.
echo Please install Python 3.10+ from https://www.python.org/downloads/
echo Make sure to check "Add Python to PATH" during installation.
echo.
pause
exit /b 1

:CREATE_VENV
echo [INFO] Creating Python virtual environment in .venv folder...
%SYS_PY% -m venv "%~dp0.venv"
if exist "%~dp0.venv\Scripts\python.exe" (
    set "PY_EXE=%~dp0.venv\Scripts\python.exe"
    echo [SUCCESS] Virtual environment created successfully.
    goto :VENV_READY
)
echo [WARNING] Could not create virtual environment. Using system Python directly.
set "PY_EXE=%SYS_PY%"

:VENV_READY
echo [INFO] Active Python environment: %PY_EXE%
echo.

:: -----------------------------------------------------------------------
:: 3. Check and install dependencies into the active environment
:: -----------------------------------------------------------------------
"%PY_EXE%" -c "import django, rest_framework, openpyxl" >nul 2>&1
if not errorlevel 1 goto :DEPS_OK

echo [1/3] Installing required packages: Django, DRF, openpyxl...
"%PY_EXE%" -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 goto :PIP_FAIL
echo [SUCCESS] All packages installed successfully.
goto :DEPS_DONE

:PIP_FAIL
color 0C
echo.
echo [ERROR] Failed to install packages. Please check your internet connection.
pause
exit /b 1

:DEPS_OK
echo [1/3] Dependencies verified: Django, DRF, openpyxl.

:DEPS_DONE
echo.

:: -----------------------------------------------------------------------
:: 4. Run database migrations & initialize seed data
:: -----------------------------------------------------------------------
echo [2/3] Setting up database...
"%PY_EXE%" "%~dp0manage.py" migrate --noinput
if errorlevel 1 goto :MIGRATE_FAIL

"%PY_EXE%" "%~dp0manage.py" seed_data >nul 2>&1
echo      Database is up to date.
echo.
goto :START_SERVER

:MIGRATE_FAIL
color 0C
echo [ERROR] Database migration failed.
pause
exit /b 1

:: -----------------------------------------------------------------------
:: 5. Launch application
:: -----------------------------------------------------------------------
:START_SERVER
echo [3/3] Starting Milestone Management server...
echo =====================================================================
echo  Server URL: http://127.0.0.1:8000/
echo =====================================================================
echo.
echo Press Ctrl+C in this window anytime to stop the server.
echo.

start http://127.0.0.1:8000/login/

"%PY_EXE%" "%~dp0manage.py" runserver 127.0.0.1:8000
pause
