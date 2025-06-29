@echo off
echo Cleaning up Streamlit files and updating to Angular UI...

REM Move main streamlit file to legacy
move "streamlit_app_session.py" "legacy\"

REM Update bin scripts to point to new Angular UI
echo @echo off > "bin\launch_angular_ui.bat"
echo echo Starting LLM Debate System with Angular UI... >> "bin\launch_angular_ui.bat"
echo cd /d "%%~dp0\.." >> "bin\launch_angular_ui.bat"
echo ".venv\Scripts\python.exe" -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload >> "bin\launch_angular_ui.bat"
echo pause >> "bin\launch_angular_ui.bat"

echo Cleanup complete! Use start_angular_ui.bat or bin\launch_angular_ui.bat to run the new system.
pause
