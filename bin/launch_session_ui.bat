@echo off
REM Launch the session-based Streamlit UI
echo.
echo LLM Debate System - Session UI Launcher
echo ==========================================
echo.
echo Starting session-based UI (true model persistence)
echo This may take a moment...
echo.

REM Change to script directory
cd /d "%~dp0"

REM Launch the session UI
python launch_session_ui.py

echo.
echo 🛑 UI has been closed.
pause
