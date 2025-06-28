@echo off
echo Starting LLM Debate System Web UI...
echo.
echo Make sure Ollama is running before proceeding!
echo If Ollama is not running, start it first.
echo.
echo The web interface will open at: http://localhost:8501
echo.
pause
streamlit run streamlit_app.py
