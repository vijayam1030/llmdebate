@echo off
echo Starting LLM Debate System...
echo.
echo Project Structure: Ultra-Clean Root Directory
echo - Only essential files in root
echo - All configs in /system/ folder  
echo - All scripts in /bin/ folder
echo.
cd /d "%~dp0.."
echo Running: streamlit run streamlit_app_session.py
echo.
streamlit run streamlit_app_session.py
pause
