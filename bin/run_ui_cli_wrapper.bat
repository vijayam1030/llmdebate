@echo off
REM CLI Wrapper Streamlit launcher for LLM Debate System
REM Maximum compatibility - directly wraps the working CLI script

echo Starting LLM Debate System Web UI (CLI Wrapper)...
echo.
echo This version directly wraps the working CLI script for
echo maximum compatibility and reliability.
echo.
echo The web interface will open automatically in your browser.
echo If not, manually open: http://localhost:8504
echo.
echo Press Ctrl+C to stop the server.
echo.

REM Change to the script directory
cd /d "%~dp0"

REM Start Streamlit with the CLI wrapper app
streamlit run streamlit_app_cli_wrapper.py --server.port 8504 --server.headless false

pause
