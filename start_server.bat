@echo off
echo Starting FastAPI server for LLM Debate System...
echo.
echo Server will be available at: http://localhost:8000
echo API documentation at: http://localhost:8000/docs
echo Status endpoint: http://localhost:8000/api/status
echo.
echo Press Ctrl+C to stop the server
echo.

python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
