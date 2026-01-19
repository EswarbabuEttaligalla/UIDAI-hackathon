@echo off
echo ========================================
echo    AMEWS - Full System Startup
echo    Aadhaar Misuse Early-Warning System
echo ========================================
echo.
echo Starting Backend and Frontend servers...
echo.

REM Start backend in new window
start "AMEWS Backend" cmd /k "cd /d %~dp0 && call start-backend.bat"

REM Wait a few seconds for backend to initialize
timeout /t 5 /nobreak > nul

REM Start frontend in new window
start "AMEWS Frontend" cmd /k "cd /d %~dp0 && call start-frontend.bat"

echo.
echo Both servers are starting...
echo.
echo Backend API: http://localhost:8000
echo Frontend Dashboard: http://localhost:3000
echo API Documentation: http://localhost:8000/docs
echo.
echo Login Credentials:
echo   Username: admin
echo   Password: admin123
echo.
pause
