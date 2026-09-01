Write-Host "Starting FleetFlow Master..." -ForegroundColor Cyan
if (Test-Path "..\FSM\Scripts\python.exe") {
    & "..\FSM\Scripts\python.exe" app.py
} elseif (Test-Path "venv\Scripts\python.exe") {
    & "venv\Scripts\python.exe" app.py
} else {
    python app.py
}
