@echo off
REM LLM Debate System Setup Script for Windows

echo 🎯 LLM Debate System Setup
echo ==========================

REM Check Python version
python --version > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python from: https://python.org/
    pause
    exit /b 1
)

for /f "tokens=*" %%a in ('python --version') do set python_version=%%a
echo Python version: %python_version%

REM Check if Ollama is installed
ollama --version > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ❌ Ollama is not installed
    echo Please install Ollama from: https://ollama.ai/
    echo Then run: ollama serve
    pause
    exit /b 1
)

for /f "tokens=*" %%a in ('ollama --version') do set ollama_version=%%a
echo ✅ Ollama is installed
echo Ollama version: %ollama_version%

REM Check if Ollama is running
curl -s http://localhost:11434/api/tags > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ❌ Ollama is not running
    echo Please start Ollama with: ollama serve
    pause
    exit /b 1
)
echo ✅ Ollama is running

REM Install Python dependencies
echo 📦 Installing Python dependencies...
pip install -r requirements.txt

if %ERRORLEVEL% neq 0 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)
echo ✅ Dependencies installed successfully

REM Download required models
echo 🤖 Downloading required Ollama models...

echo Downloading llama3.1:70b...
ollama pull llama3.1:70b
if %ERRORLEVEL% equ 0 (
    echo ✅ llama3.1:70b downloaded successfully
) else (
    echo ⚠️ Failed to download llama3.1:70b - will be downloaded when first used
)

echo Downloading llama3.1:8b...
ollama pull llama3.1:8b
if %ERRORLEVEL% equ 0 (
    echo ✅ llama3.1:8b downloaded successfully
) else (
    echo ⚠️ Failed to download llama3.1:8b - will be downloaded when first used
)

echo Downloading mistral:7b...
ollama pull mistral:7b
if %ERRORLEVEL% equ 0 (
    echo ✅ mistral:7b downloaded successfully
) else (
    echo ⚠️ Failed to download mistral:7b - will be downloaded when first used
)

echo Downloading phi3:medium...
ollama pull phi3:medium
if %ERRORLEVEL% equ 0 (
    echo ✅ phi3:medium downloaded successfully
) else (
    echo ⚠️ Failed to download phi3:medium - will be downloaded when first used
)

REM Create .env file if it doesn't exist
if not exist .env (
    echo 📝 Creating .env file...
    copy .env.example .env > nul
    echo ✅ .env file created. Please edit it with your settings if needed.
)

REM Test the system
echo 🧪 Testing system initialization...
python -c "import asyncio; from main import LLMDebateSystem; asyncio.run(LLMDebateSystem().initialize())"

echo.
echo 🎉 Setup complete!
echo.
echo Usage options:
echo   1. Interactive CLI: python main.py
echo   2. Single question: python main.py "Your question here"
echo   3. Web interface: streamlit run streamlit_app.py
echo   4. REST API: python api.py
echo.
echo Example:
echo   python main.py "What are the benefits of renewable energy?"
echo.
pause
