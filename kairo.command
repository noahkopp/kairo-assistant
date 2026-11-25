#!/bin/bash
# Start Kairo (Mac and Linux). First run installs what it needs (a few minutes).
#   ./kairo.command            start talking
#   ./kairo.command --google   connect Gmail and Google Calendar
#   ./kairo.command --setup-only
cd "$(dirname "$0")"
if [ -z "$1" ] && [ -x .venv/bin/python ] && .venv/bin/python launch.py; then
  echo "Kairo is already running; I woke it up."; exit 0
fi
if [ "$(uname)" = "Darwin" ]; then
  command -v brew >/dev/null || { echo "Install Homebrew first: https://brew.sh"; exit 1; }
  command -v copilot >/dev/null || brew install copilot-cli
  brew list portaudio >/dev/null 2>&1 || brew install portaudio
  PY="$(command -v python3.12 || command -v python3)"
else
  command -v copilot >/dev/null || { echo "Install GitHub Copilot CLI first: curl -fsSL https://gh.io/copilot-install | bash"; exit 1; }
  PY="$(command -v python3)"
  [ -n "$PY" ] || { echo "Install Python 3 first (e.g. sudo apt install python3 python3-venv)"; exit 1; }
fi
[ -x .venv/bin/python ] || "$PY" -m venv .venv || { echo "Couldn't create a Python environment. On Ubuntu/Debian: sudo apt install python3-venv"; exit 1; }
.venv/bin/pip install -q --disable-pip-version-check -r requirements.txt || {
  echo "Couldn't install Kairo's Python packages."
  [ "$(uname)" = "Darwin" ] || echo "On Ubuntu/Debian, first run: sudo apt install portaudio19-dev python3-dev espeak-ng"
  exit 1; }
if [ "$1" = "--google" ]; then exec .venv/bin/python google_setup.py; fi
.venv/bin/python setup_tools.py
[ "$1" = "--setup-only" ] && exit 0
exec .venv/bin/python talk.py
