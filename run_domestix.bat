@echo off
title Domestix - Smart Household Management Platform
color 0B
echo ===============================================================================
echo                 DOMESTIX - SMART HOUSEHOLD MANAGEMENT APPLICATION
echo    Saee Takale (5185) ^| Ayusha Kale (3205) ^| Pranav Joshi (5208) ^| Vaishnavi Thite (5188)
echo ===============================================================================
echo.

:: 1. Check if Python is installed
set PY_CMD=
where py >nul 2>nul
if %errorlevel% equ 0 (
    set PY_CMD=py
    goto :PYTHON_FOUND
)

where python >nul 2>nul
if %errorlevel% equ 0 (
    set PY_CMD=python
    goto :PYTHON_FOUND
)

:PYTHON_NOT_FOUND
echo [!] Python was not detected on this PC.
echo [*] No problem! Launching Domestix in Standalone Instant Mode...
timeout /t 2 >nul
start "" "login.html"
exit /b 0

:PYTHON_FOUND
echo [*] Python detected (%PY_CMD%).
echo [*] Checking dependencies (FastAPI, Uvicorn)...
%PY_CMD% -m pip install -r requirements.txt --quiet

echo [*] Initializing SQLite database (domestix.db)...
%PY_CMD% -c "from backend.database import init_db; init_db()" >nul 2>nul

echo [*] Launching Domestix in your web browser...
start "" "http://127.0.0.1:8000/login.html"

echo.
echo ===============================================================================
echo  Domestix Server is RUNNING at http://127.0.0.1:8000
echo  - Press Ctrl+C in this window anytime to stop the server.
echo ===============================================================================
echo.

%PY_CMD% -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
pause
