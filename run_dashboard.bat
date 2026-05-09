@echo off
title NCCC SOC Dashboard

echo =====================================
echo Starting NCCC Dashboard...
echo =====================================

REM 👉 Activate virtual environment (if using)
call venv\Scripts\activate

REM 👉 Move to project directory
cd /d D:\NCCC_DASHBOARD\nccc_dashboard

REM 👉 Run app
python app.py

pause