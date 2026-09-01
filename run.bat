@echo off
echo Starting FleetFlow Master...
if exist "..\FSM\Scripts\python.exe" (
    "..\FSM\Scripts\python.exe" app.py
) else if exist "venv\Scripts\python.exe" (
    "venv\Scripts\python.exe" app.py
) else (
    python app.py
)
pause
