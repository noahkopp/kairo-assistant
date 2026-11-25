@echo off
REM Start Kairo on Windows. First run installs what it needs (a few minutes).
REM   kairo.cmd            start talking
REM   kairo.cmd --google   connect Gmail and Google Calendar
cd /d "%~dp0"
where copilot >nul 2>nul || (echo Install GitHub Copilot CLI first: winget install GitHub.Copilot & pause & exit /b 1)
if not exist .venv\Scripts\python.exe (
  py -3 -m venv .venv 2>nul || python -m venv .venv || (echo Install Python 3 first: winget install Python.Python.3.12 & pause & exit /b 1)
)
.venv\Scripts\python.exe -m pip install -q --disable-pip-version-check -r requirements.txt || (echo Could not install Kairo's Python packages. & pause & exit /b 1)
if "%~1"=="--google" (.venv\Scripts\python.exe google_setup.py & exit /b)
.venv\Scripts\python.exe setup_tools.py
if "%~1"=="--setup-only" exit /b 0
.venv\Scripts\python.exe talk.py
pause
