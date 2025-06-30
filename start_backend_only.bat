@echo off
echo ================================================
echo    LLM Debate System - Backend Only
echo ================================================
echo.
echo Starting backend with Pinggy tunnel...
echo Frontend can be started manually with: npm start
echo.

REM Change to the script directory
cd /d "%~dp0"

REM Run the Python startup script
python.exe start_backend_only.py

echo.
echo ================================================
echo    Backend stopped
echo ================================================
pause