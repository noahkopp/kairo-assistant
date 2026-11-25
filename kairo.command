#!/bin/bash
# Start Kairo with voice. First run installs what it needs (a few minutes).
cd "$(dirname "$0")"
command -v brew >/dev/null || { echo "Install Homebrew first: https://brew.sh"; exit 1; }
command -v copilot >/dev/null || brew install copilot-cli
brew list portaudio >/dev/null 2>&1 || brew install portaudio
PY="$(command -v python3.12 || command -v python3)"
[ -x .venv/bin/python ] || "$PY" -m venv .venv
.venv/bin/pip install -q --disable-pip-version-check -r requirements.txt
if [ "$1" = "--google" ]; then exec .venv/bin/python google_setup.py; fi
.venv/bin/python setup_tools.py
[ "$1" = "--setup-only" ] && exit 0
exec .venv/bin/python talk.py
