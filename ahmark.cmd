@echo off
setlocal
cd /d "%~dp0"

if "%~1"=="" (
    "%~dp0.venv\Scripts\python.exe" "%~dp0app.py"
) else (
    "%~dp0.venv\Scripts\python.exe" "%~dp0app.py" --command "%*"
)
