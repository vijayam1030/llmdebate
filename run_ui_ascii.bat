@echo off
REM ASCII-safe Streamlit launcher for LLM Debate System
REM No Unicode/emoji issues on Windows

echo Starting ASCII-safe LLM Debate System Web UI...
echo.
echo This version avoids all Unicode/emoji characters
echo that can cause encoding issues on Windows.
echo.
echo The web interface will open automatically in your browser.
echo If not, manually open: http://localhost:8503
echo.
echo Press Ctrl+C to stop the server.
echo.

REM Change to the script directory
cd /d "%~dp0"

REM Start Streamlit with the ASCII-safe app
streamlit run streamlit_app_ascii.py --server.port 8503 --server.headless false

pause
