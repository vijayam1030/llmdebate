@echo off
echo ==========================================
echo    LLM Debate System - Development Mode
echo ==========================================
echo.

REM Change to project directory
cd /d "%~dp0"

echo 🔧 Starting development servers...
echo.

REM Check if we need to build Angular first
cd angular-ui
if not exist "dist" (
    echo Building Angular for first time...
    call npm run build
)
cd ..

echo 🌐 Development servers will start:
echo    • Backend: http://localhost:8000 (FastAPI with auto-reload)
echo    • Frontend: Served from backend at http://localhost:8000
echo.
echo 💡 For Angular development with live reload:
echo    Open a second terminal and run:
echo    cd angular-ui ^&^& npm start
echo    Then access Angular dev server at http://localhost:4200
echo.
echo ⚡ Press Ctrl+C to stop
echo ==========================================

REM Activate Python environment and start with reload
call .venv\Scripts\activate.bat
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload --log-level info
