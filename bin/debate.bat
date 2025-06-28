@echo off
REM LLM Debate System - Windows Launcher

echo 🎯 LLM Debate System - Windows Launcher
echo ==========================================

REM Check if Python is available
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python from: https://python.org/
    pause
    exit /b 1
)

REM Parse command line arguments
set "ARGS="
set "WEB_MODE=0"
set "API_MODE=0"
set "SKIP_CHECK=0"

:parse_args
if "%~1"=="" goto :args_done
if /i "%~1"=="--web" (
    set "WEB_MODE=1"
    shift
    goto :parse_args
)
if /i "%~1"=="--api" (
    set "API_MODE=1"
    shift
    goto :parse_args
)
if /i "%~1"=="--skip-check" (
    set "SKIP_CHECK=1"
    shift
    goto :parse_args
)
if /i "%~1"=="--help" (
    goto :show_help
)
set "ARGS=%ARGS% %1"
shift
goto :parse_args

:args_done

REM Launch the appropriate mode
if %WEB_MODE%==1 (
    echo 🌐 Launching Web Interface...
    python run.py --web
    goto :end
)

if %API_MODE%==1 (
    echo 🔌 Launching API Server...
    python run.py --api
    goto :end
)

REM CLI mode
if %SKIP_CHECK%==1 (
    python run.py --skip-check %ARGS%
) else (
    python run.py %ARGS%
)

goto :end

:show_help
echo.
echo LLM Debate System - Usage:
echo.
echo   debate.bat                              # Interactive CLI mode
echo   debate.bat "Your question here"         # Direct question mode
echo   debate.bat --web                        # Launch web interface
echo   debate.bat --api                        # Launch API server
echo   debate.bat --skip-check                 # Skip model check
echo   debate.bat --help                       # Show this help
echo.
echo Examples:
echo   debate.bat "What are the benefits of AI?"
echo   debate.bat --web
echo   debate.bat --skip-check "Climate change solutions"
echo.
goto :end

:end
if %ERRORLEVEL% neq 0 (
    echo.
    echo ❌ Application exited with errors
    pause
)
