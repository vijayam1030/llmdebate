@echo off
echo Starting LLM Debate System with Angular UI...
cd /d "%~dp0"
".venv\Scripts\python.exe" -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
pause
