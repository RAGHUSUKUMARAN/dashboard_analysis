@echo off

cd /d D:\NCCC_DASHBOARD

start http://127.0.0.1:8050

D:\NCCC_DASHBOARD\venv\Scripts\python.exe -m nccc_dashboard.app

pause