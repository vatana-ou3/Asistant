@echo off
setlocal
cd /d "%~dp0"
if exist "%~dp0runtime\ahmark.ready" (
    echo Ah Mark is already running and ready.
    exit /b 0
)

echo Loading Ah Mark...
start "Ah Mark" /min "%~dp0.venv\Scripts\python.exe" "%~dp0app.py" --wake-word

set /a waited=0
:wait_for_ready
if exist "%~dp0runtime\ahmark.ready" goto ready
ping 127.0.0.1 -n 2 >nul
set /a waited+=1
if %waited% LSS 60 goto wait_for_ready

echo Ah Mark did not become ready within 60 seconds.
echo Restore the minimized Ah Mark window to see the error.
exit /b 1

:ready
echo I'm ready. Say "Hey bro" when you need me.
