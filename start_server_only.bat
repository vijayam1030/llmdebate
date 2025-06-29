@echo off
echo Starting LLM Debate System...
echo.

REM Go to project directory
cd /d "%~dp0"

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Start the server directly
echo Starting FastAPI server...
echo Open http://localhost:8000 in your browser
echo.

python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

pause
