@echo off
echo ========================================
echo    AMEWS - Backend Server
echo    Aadhaar Misuse Early-Warning System
echo ========================================
echo.

cd /d "%~dp0backend"

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt --quiet

REM Start the server
echo.
echo Starting AMEWS Backend Server...
echo API will be available at: http://localhost:8000
echo API Docs at: http://localhost:8000/docs
echo.
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause
