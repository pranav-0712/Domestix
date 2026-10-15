@echo off
title Domestix - Smart Household Management Server
echo =====================================================================
echo  DOMESTIX | Smart Household Management Platform
echo  Team Members:
echo    - Saee Takale (5185)
echo    - Ayusha Kale (3205)
echo    - Pranav Joshi (5208)
echo    - Vaishnavi Thite (5188)
echo =====================================================================
echo.
echo Starting FastAPI REST Server on http://127.0.0.1:8000 ...
echo Database: SQLite3 (domestix.db)
echo.
py -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
pause
