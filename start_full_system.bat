@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo    LLM Debate System - Full Stack Launcher
echo ==========================================
echo.

REM Change to project directory
cd /d "%~dp0"
echo Current directory: %CD%
echo.

echo 🔧 Checking Prerequisites...
echo.

REM Check if Python is available
echo Testing Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found! Please install Python 3.8+ and add to PATH
    echo Press any key to exit...
    pause
    exit /b 1
) else (
    echo ✅ Python found: 
    python --version
)

REM Check if Node.js is available
echo Testing Node.js installation...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js not found! Please install Node.js and add to PATH
    echo Press any key to exit...
    pause
    exit /b 1
) else (
    echo ✅ Node.js found: 
    node --version
)

REM Check if npm is available
echo Testing npm installation...
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ npm not found! Please install npm (usually comes with Node.js)
    echo Press any key to exit...
    pause
    exit /b 1
) else (
    echo ✅ npm found: 
    npm --version
)
echo.

echo 📦 Setting up Angular Frontend...
cd angular-ui

REM Install npm dependencies if node_modules doesn't exist
if not exist "node_modules" (
    echo Installing npm dependencies...
    call npm install
    if %errorlevel% neq 0 (
        echo ❌ npm install failed!
        pause
        exit /b 1
    )
)

echo Building Angular application...
call npm run build
if %errorlevel% neq 0 (
    echo ❌ Angular build failed!
    pause
    exit /b 1
)

echo ✅ Angular build completed successfully!
echo.

REM Go back to project root
cd ..

echo 🐍 Setting up Python Backend...

REM Check if virtual environment exists
if not exist ".venv" (
    echo Creating Python virtual environment...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo ❌ Failed to create virtual environment!
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Install Python dependencies
echo Installing Python dependencies...
pip install -r system\requirements.txt
if %errorlevel% neq 0 (
    echo ❌ Failed to install Python dependencies!
    pause
    exit /b 1
)

echo ✅ Python setup completed successfully!
echo.

echo 🚀 Starting LLM Debate System...
echo.
echo 🌐 Server will be available at:
echo    • Main UI: http://localhost:8000
echo    • API Docs: http://localhost:8000/docs  
echo    • Status: http://localhost:8000/api/status
echo.
echo ⚡ Press Ctrl+C to stop the server
echo ==========================================
echo.

REM Start the FastAPI server
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

echo.
echo 🛑 Server stopped.
echo.
echo Script completed. Press any key to close this window...
pause
