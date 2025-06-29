@echo off
echo ==========================================
echo    Debug - Testing Basic Setup
echo ==========================================
echo.

REM Change to project directory
cd /d "%~dp0"
echo Current directory: %CD%
echo.

echo Testing basic commands...
echo.

echo 1. Testing Python:
python --version
if %errorlevel% neq 0 (
    echo ❌ Python test failed!
) else (
    echo ✅ Python OK
)
echo.

echo 2. Testing Node.js:
node --version
if %errorlevel% neq 0 (
    echo ❌ Node.js test failed!
) else (
    echo ✅ Node.js OK
)
echo.

echo 3. Testing npm:
npm --version
if %errorlevel% neq 0 (
    echo ❌ npm test failed!
) else (
    echo ✅ npm OK
)
echo.

echo 4. Checking directories:
if exist "angular-ui" (
    echo ✅ angular-ui directory found
) else (
    echo ❌ angular-ui directory NOT found
)

if exist "system" (
    echo ✅ system directory found
) else (
    echo ❌ system directory NOT found
)

if exist "api" (
    echo ✅ api directory found
) else (
    echo ❌ api directory NOT found
)

if exist ".venv" (
    echo ✅ .venv directory found
) else (
    echo ⚠️ .venv directory not found (will be created)
)
echo.

echo 5. Checking files:
if exist "system\requirements.txt" (
    echo ✅ requirements.txt found
) else (
    echo ❌ requirements.txt NOT found
)

if exist "angular-ui\package.json" (
    echo ✅ package.json found
) else (
    echo ❌ package.json NOT found
)
echo.

echo ==========================================
echo Debug complete! 
echo If you see any ❌ symbols above, those need to be fixed.
echo Press any key to close...
pause
