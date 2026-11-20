@echo off
setlocal
title HostelEase - Update Database
cd /d "%~dp0"

echo.
echo ==========================================
echo       HOSTELEase - DATABASE UPDATE
echo ==========================================
echo.

if not exist "manage.py" (
    echo ERROR: manage.py not found.
    echo Keep this file in the project root beside manage.py.
    pause
    exit /b 1
)

if not exist "venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found at venv\Scripts\python.exe.
    pause
    exit /b 1
)

set "PYTHON=%CD%\venv\Scripts\python.exe"

echo Step 1/2: Creating migrations for changed models...
"%PYTHON%" manage.py makemigrations
if errorlevel 1 (
    echo.
    echo ERROR: makemigrations failed. Check the error above.
    pause
    exit /b 1
)

echo.
echo Step 2/2: Applying migrations to the database...
"%PYTHON%" manage.py migrate --noinput
if errorlevel 1 (
    echo.
    echo ERROR: migrate failed. Check PostgreSQL and .env settings.
    pause
    exit /b 1
)

echo.
echo SUCCESS: Database is up to date.
pause
endlocal
