@echo off
echo ========================================
echo    AMEWS - Frontend Dashboard
echo    Aadhaar Misuse Early-Warning System
echo ========================================
echo.

cd /d "%~dp0frontend"

REM Check if node_modules exists
if not exist "node_modules" (
    echo Installing dependencies...
    npm install
)

echo.
echo Starting AMEWS Dashboard...
echo Dashboard will be available at: http://localhost:3000
echo.
npm start

pause
