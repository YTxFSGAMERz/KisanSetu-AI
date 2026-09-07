@echo off
setlocal enabledelayedexpansion

REM ============================================================================
REM KisanSetu AI - Application Launcher
REM Launches Backend [FastAPI], Frontend [Next.js], and Notifier Tray App
REM ============================================================================

title KisanSetu AI Launcher

set "PROJECT_ROOT=%~dp0"
set "BACKEND_DIR=%PROJECT_ROOT%backend"
set "FRONTEND_DIR=%PROJECT_ROOT%frontend"
set "NOTIFIER_DIR=%PROJECT_ROOT%kisansetu_notifier"

echo ============================================================================
echo   KisanSetu AI - Smart Procurement Management Platform
echo   Launching development environment...
echo ============================================================================
echo.

REM 1. Verify Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python was not found in your system PATH!
    echo Please install Python 3.10+ and add it to PATH.
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 2. Verify Node / npm
where npm >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js / npm was not found in your system PATH!
    echo Please install Node.js 18+ and add it to PATH.
    echo Download: https://nodejs.org/
    pause
    exit /b 1
)

REM 3. Auto-seed local SQLite database if missing
if exist "%BACKEND_DIR%\kisansetu.db" goto :AFTER_DB_SEED
echo [*] Local database not found. Initializing SQLite database...
pushd "%BACKEND_DIR%"
python -m app.database.setup_local_db
popd
echo [*] Database initialized successfully!
echo.
:AFTER_DB_SEED

REM 4. Check Frontend dependencies
if exist "%FRONTEND_DIR%\node_modules" goto :AFTER_FRONTEND_DEPS
echo [*] Frontend dependencies not found. Installing packages...
pushd "%FRONTEND_DIR%"
call npm install
popd
echo [*] Dependencies installed!
echo.
:AFTER_FRONTEND_DEPS

REM 5. Auto-install Notifier dependencies [first run only]
if not exist "%NOTIFIER_DIR%\requirements.txt" goto :AFTER_NOTIFIER_DEPS
if exist "%NOTIFIER_DIR%\_deps_installed" goto :AFTER_NOTIFIER_DEPS
echo [*] Installing KisanSetu Notifier dependencies [one-time]...
python -m pip install -r "%NOTIFIER_DIR%\requirements.txt" --quiet
if %errorlevel% neq 0 (
    echo [WARN] Notifier dependency install had issues. Tray app may not work.
) else (
    echo. > "%NOTIFIER_DIR%\_deps_installed"
    echo [*] Notifier dependencies installed!
)
echo.
:AFTER_NOTIFIER_DEPS

REM 5b. Ensure ADB Port Forwarding for Termux SMS Bridge [if phone connected]
where adb.exe >nul 2>&1
if %errorlevel% equ 0 (
    adb forward tcp:8080 tcp:8080 >nul 2>&1
)

REM 6. Detect Python Virtual Environment [if available]
set "VENV_ACTIVATE="
if exist "%BACKEND_DIR%\venv\Scripts\activate.bat" (
    set "VENV_ACTIVATE=call "%BACKEND_DIR%\venv\Scripts\activate.bat" && "
) else if exist "%PROJECT_ROOT%venv\Scripts\activate.bat" (
    set "VENV_ACTIVATE=call "%PROJECT_ROOT%venv\Scripts\activate.bat" && "
) else if exist "%BACKEND_DIR%\.venv\Scripts\activate.bat" (
    set "VENV_ACTIVATE=call "%BACKEND_DIR%\.venv\Scripts\activate.bat" && "
) else if exist "%PROJECT_ROOT%.venv\Scripts\activate.bat" (
    set "VENV_ACTIVATE=call "%PROJECT_ROOT%.venv\Scripts\activate.bat" && "
)

REM 7. Launch services via Windows Terminal [wt.exe] or Fallback
where wt.exe >nul 2>&1
if %errorlevel% neq 0 goto :FALLBACK

echo [*] Windows Terminal detected.
echo [*] Opening Backend, Frontend, and Notifier...
echo.
echo     Left Pane  : Backend API [FastAPI]  -^> http://127.0.0.1:8000
echo     Right Pane : Frontend UI [Next.js]  -^> http://localhost:3000
echo     API Docs   : Swagger UI             -^> http://127.0.0.1:8000/docs
echo.

if /i "%~1"=="--tabs" goto :LAUNCH_TABS

:LAUNCH_SPLIT
wt.exe -w new --title "KisanSetu AI" -d "%BACKEND_DIR%" cmd /k "title KisanSetu Backend && echo ==================================================== && echo   KisanSetu AI - Backend Server [FastAPI] && echo   API Docs: http://127.0.0.1:8000/docs && echo ==================================================== && echo. && %VENV_ACTIVATE%python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000" ^; split-pane -V --title "KisanSetu Frontend" -d "%FRONTEND_DIR%" cmd /k "title KisanSetu Frontend && echo ==================================================== && echo   KisanSetu AI - Frontend Web App [Next.js] && echo   Web App:  http://localhost:3000 && echo ==================================================== && echo. && npm run dev"
goto :LAUNCH_NOTIFIER

:LAUNCH_TABS
wt.exe -w new --title "KisanSetu Backend" -d "%BACKEND_DIR%" cmd /k "title KisanSetu Backend && echo ==================================================== && echo   KisanSetu AI - Backend Server [FastAPI] && echo   API Docs: http://127.0.0.1:8000/docs && echo ==================================================== && echo. && %VENV_ACTIVATE%python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000" ^; new-tab --title "KisanSetu Frontend" -d "%FRONTEND_DIR%" cmd /k "title KisanSetu Frontend && echo ==================================================== && echo   KisanSetu AI - Frontend Web App [Next.js] && echo   Web App:  http://localhost:3000 && echo ==================================================== && echo. && npm run dev"
goto :LAUNCH_NOTIFIER

:FALLBACK
echo [!] Windows Terminal [wt.exe] was not found in PATH.
echo [*] Launching in standard Command Prompt windows...
echo.
start "KisanSetu AI - Backend" /d "%BACKEND_DIR%" cmd /k "title KisanSetu Backend && echo Starting Backend... && %VENV_ACTIVATE%python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
start "KisanSetu AI - Frontend" /d "%FRONTEND_DIR%" cmd /k "title KisanSetu Frontend && echo Starting Frontend... && npm run dev"

:LAUNCH_NOTIFIER
REM 8. Launch KisanSetu Notifier tray app in background
if exist "%NOTIFIER_DIR%\main.py" (
    echo [*] Scheduling KisanSetu Notifier tray app...
    start "" /min cmd /c "ping 127.0.0.1 -n 9 >nul && pythonw "%NOTIFIER_DIR%\main.py" 2>"%NOTIFIER_DIR%\notifier.log""
)

REM 9. Browser launch [unless --no-browser is passed]
if /i not "%~1"=="--no-browser" if /i not "%~2"=="--no-browser" (
    echo [*] Opening browser at http://localhost:3000 shortly...
    start "" /min cmd /c "ping 127.0.0.1 -n 5 >nul & start http://localhost:3000"
)

echo.
echo [OK] All services initiated!
echo      Backend  : http://127.0.0.1:8000
echo      Frontend : http://localhost:3000
if exist "%NOTIFIER_DIR%\main.py" (
    echo      Notifier : Running in system tray [taskbar bottom-right]
)
echo.
ping 127.0.0.1 -n 3 >nul
exit /b 0
