@echo off
setlocal

set "VENV_ACTIVATE=%~dp0..\hrms-venv\Scripts\activate.bat"

if not exist "%VENV_ACTIVATE%" (
    echo ERROR: HRMS virtual environment not found at "%~dp0..\hrms-venv".
    exit /b 1
)

if not exist "%~dp0manage.py" (
    echo ERROR: HRMS manage.py not found in "%~dp0".
    exit /b 1
)

call "%VENV_ACTIVATE%"
if errorlevel 1 (
    echo ERROR: Could not activate the HRMS virtual environment.
    exit /b 1
)

cd /d "%~dp0"
if errorlevel 1 (
    echo ERROR: Could not navigate to the HRMS project directory.
    exit /b 1
)

powershell -NoProfile -Command "$listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Parse('127.0.0.1'), 8001); try { $listener.Start(); $listener.Stop(); exit 0 } catch { Write-Host 'ERROR: HRMS cannot start because port 8001 is already in use on 127.0.0.1.'; exit 1 }"
if errorlevel 1 exit /b 1

python manage.py runserver 127.0.0.1:8001
