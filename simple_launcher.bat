@echo off
echo ==========================================
echo    LLM Debate System - Simple Launcher
echo ==========================================
echo.

REM Change to project directory
cd /d "%~dp0"
echo Current directory: %CD%
echo.

echo 🔧 Checking basic requirements...

REM Quick check - just try the commands
python --version
if %errorlevel% neq 0 (
    echo ❌ Python not available
    goto :error
)

node --version
if %errorlevel% neq 0 (
    echo ❌ Node.js not available  
    goto :error
)

npm --version
if %errorlevel% neq 0 (
    echo ❌ npm not available
    goto :error
)

echo ✅ All tools available!
echo.

echo 📦 Setting up Angular...
cd angular-ui

REM Install dependencies if needed
if not exist "node_modules" (
    echo Installing npm dependencies...
    npm install
    if %errorlevel% neq 0 goto :error
)

echo Building Angular...
npm run build
if %errorlevel% neq 0 goto :error

cd ..
echo ✅ Angular setup complete!
echo.

echo 🐍 Setting up Python...

REM Create venv if needed
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    if %errorlevel% neq 0 goto :error
)

REM Activate and install
call .venv\Scripts\activate.bat
echo Installing Python dependencies...
pip install -r system\requirements.txt
if %errorlevel% neq 0 goto :error

echo ✅ Python setup complete!
echo.

echo 🚀 Starting server...
echo.
echo 🌐 Server will be available at:
echo    • Main UI: http://localhost:8000
echo    • API Docs: http://localhost:8000/docs
echo    • Status: http://localhost:8000/api/status
echo.
echo ⚡ Press Ctrl+C to stop the server
echo ==========================================

python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

goto :end

:error
echo.
echo ❌ Setup failed! Check the error above.
echo.

:end
echo.
echo Press any key to close...
pause
