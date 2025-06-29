@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo    LLM Debate System - Quick Start
echo ==========================================
echo.

REM Change to project directory
cd /d "%~dp0"
echo Current directory: %CD%
echo.

echo 🔧 Quick build and start...

REM Check if angular-ui exists
if not exist "angular-ui" (
    echo ❌ angular-ui directory not found!
    echo Press any key to exit...
    pause
    exit /b 1
)

REM Build Angular (quick)
echo Building Angular frontend...
cd angular-ui
call npm run build --silent
if %errorlevel% neq 0 (
    echo ❌ Angular build failed!
    echo Press any key to exit...
    pause
    exit /b 1
)
cd ..

REM Check if virtual environment exists
if not exist ".venv" (
    echo ❌ Virtual environment not found! Please run start_full_system.bat first.
    echo Press any key to exit...
    pause
    exit /b 1
)

REM Activate Python environment and start server
echo Starting FastAPI backend...
call .venv\Scripts\activate.bat

echo.
echo 🚀 LLM Debate System Starting...
echo.
echo 🌐 Access Points:
echo    • UI: http://localhost:8000
echo    • API: http://localhost:8000/docs
echo    • Status: http://localhost:8000/api/status
echo.
echo ⚡ Press Ctrl+C to stop
echo ==========================================

python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

echo.
echo Server stopped. Press any key to close...
pause
