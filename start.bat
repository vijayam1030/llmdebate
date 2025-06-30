@echo off
echo ================================================
echo    LLM Debate System - Unified Launcher
echo ================================================
echo.
echo Starting backend with Cloudflare tunnel (serves complete app)...
echo.

REM Change to the script directory
cd /d "%~dp0"

REM Stop any existing ngrok processes
taskkill /f /im ngrok.exe 2>nul

REM Stop any existing python processes (optional cleanup)
REM taskkill /f /im python.exe 2>nul

REM Run the Python startup script
python.exe start_app.py

echo.
echo ================================================
echo    All services stopped
echo ================================================
pause