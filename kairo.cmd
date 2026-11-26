@echo off
REM Start Kairo on Windows. First run installs what it needs (a few minutes).
REM   kairo.cmd            start talking
REM   kairo.cmd --google   connect Gmail and Google Calendar
cd /d "%~dp0"
if "%~1"=="" if exist .venv\Scripts\python.exe .venv\Scripts\python.exe launch.py && exit /b 0
REM Auto-update from GitHub (skipped if offline). The block below is read all at once, so
REM updating this file while it runs is safe; afterwards the new version is started.
if not defined KAIRO_UPDATED (
  set KAIRO_UPDATED=1
  set GIT_TERMINAL_PROMPT=0
  git pull -q --ff-only >nul 2>nul
  call "%~f0" %*
  exit /b
)
where copilot >nul 2>nul || (echo Install GitHub Copilot CLI first: winget install GitHub.Copilot & pause & exit /b 1)
if not exist .venv\Scripts\python.exe (
  py -3 -m venv .venv 2>nul || python -m venv .venv || (echo Install Python 3 first: winget install Python.Python.3.12 & pause & exit /b 1)
)
.venv\Scripts\python.exe -m pip install -q --disable-pip-version-check -r requirements.txt || (echo Could not install Kairo's Python packages. & pause & exit /b 1)
if "%~1"=="--google" (.venv\Scripts\python.exe google_setup.py & exit /b)
if "%~1"=="--computer-control" (.venv\Scripts\python.exe control_setup.py %2 & exit /b)
.venv\Scripts\python.exe setup_tools.py
if "%~1"=="--setup-only" exit /b 0
.venv\Scripts\python.exe talk.py
pause
