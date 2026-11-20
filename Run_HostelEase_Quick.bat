@echo off
setlocal
title HostelEase - Fast Launcher
cd /d "%~dp0"

echo.
echo ==========================================
echo          HOSTELEase - FAST START
echo ==========================================
echo.

if not exist "manage.py" (
    echo ERROR: manage.py not found.
    echo Keep this file in the project root beside manage.py.
    pause
    exit /b 1
)

if not exist "venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found.
    echo Expected: venv\Scripts\python.exe
    echo Create the venv and install requirements.txt once.
    pause
    exit /b 1
)

set "PYTHON=%CD%\venv\Scripts\python.exe"

echo Starting Django server WITHOUT running migrations...
echo If you changed Django models, first run:
echo Update_HostelEase_Database.bat
echo.
echo Website: http://127.0.0.1:8000/
echo.

start "" cmd /c "timeout /t 3 /nobreak ^>nul ^& start http://127.0.0.1:8000/"
"%PYTHON%" manage.py runserver 127.0.0.1:8000

echo.
echo HostelEase server has stopped.
pause
endlocal
