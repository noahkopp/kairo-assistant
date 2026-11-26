#!/bin/bash
# Start Kairo (Mac and Linux). First run installs what it needs (a few minutes).
#   ./kairo.command            start talking
#   ./kairo.command --google   connect Gmail and Google Calendar
#   ./kairo.command --setup-only
cd "$(dirname "$(readlink -f "$0" 2>/dev/null || echo "$0")")"
if [ -z "$1" ] && [ -x .venv/bin/python ] && .venv/bin/python launch.py; then
  echo "Kairo is already running; I woke it up."; exit 0
fi
# Auto-update: get the newest Kairo from GitHub (quietly; skipped if offline).
# Your memory, sign-ins and settings aren't part of the download, so they're never touched.
if [ -z "$KAIRO_UPDATED" ] && [ -d .git ]; then
  export KAIRO_UPDATED=1
  before="$(git rev-parse HEAD 2>/dev/null)"
  GIT_TERMINAL_PROMPT=0 git -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=5 \
    pull -q --ff-only >/dev/null 2>&1 || true
  if [ "$(git rev-parse HEAD 2>/dev/null)" != "$before" ]; then
    echo "Kairo updated to the newest version."
    exec "$PWD/kairo.command" "$@"      # run the updated launcher
  fi
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
if [ "$1" = "--computer-control" ]; then exec .venv/bin/python control_setup.py "$2"; fi
.venv/bin/python setup_tools.py
[ "$1" = "--setup-only" ] && exit 0
exec .venv/bin/python talk.py
