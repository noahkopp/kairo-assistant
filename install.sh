#!/bin/bash
# Kairo installer for Mac and Linux. (Windows: see install.ps1.)
#   curl -fsSL https://raw.githubusercontent.com/noahkopp/kairo-assistant/main/install.sh | bash
set -e
REPO="https://github.com/noahkopp/kairo-assistant.git"
DIR="${KAIRO_DIR:-$HOME/kairo-assistant}"

say_step() { printf "\n\033[1m==> %s\033[0m\n" "$1"; }

if [ "$(uname)" = "Darwin" ]; then
  say_step "Checking Homebrew"
  if ! command -v brew >/dev/null; then
    echo "Installing Homebrew (Mac's package manager). It may ask for your Mac password."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" </dev/tty
    eval "$(/opt/homebrew/bin/brew shellenv 2>/dev/null || /usr/local/bin/brew shellenv)"
  fi
  say_step "Installing tools (Python, GitHub Copilot CLI, audio)"
  brew list python@3.12 >/dev/null 2>&1 || brew install python@3.12
  brew list portaudio   >/dev/null 2>&1 || brew install portaudio
  command -v copilot >/dev/null || brew install copilot-cli
  command -v git >/dev/null || brew install git
else
  say_step "Installing tools (Python, audio, voice). This may ask for your password."
  if command -v apt-get >/dev/null; then
    sudo apt-get update -qq </dev/tty
    sudo apt-get install -y -qq git python3 python3-venv python3-dev portaudio19-dev espeak-ng curl </dev/tty
  elif command -v dnf >/dev/null; then
    sudo dnf install -y -q git python3 python3-devel portaudio-devel espeak-ng curl </dev/tty
  elif command -v pacman >/dev/null; then
    sudo pacman -S --needed --noconfirm git python portaudio espeak-ng curl </dev/tty
  else
    echo "Please install: git, python3 (with venv), portaudio (dev files), espeak-ng. Then run this again."
  fi
  if ! command -v copilot >/dev/null; then
    say_step "Installing GitHub Copilot CLI"
    curl -fsSL https://gh.io/copilot-install | bash
    export PATH="$HOME/.local/bin:$PATH"
  fi
fi

say_step "Downloading Kairo to $DIR"
if [ -d "$DIR/.git" ]; then
  git -C "$DIR" pull -q --ff-only
else
  git clone -q "$REPO" "$DIR"
fi
chmod +x "$DIR/kairo.command" "$DIR/kt"

say_step "Setting up Kairo"
"$DIR/kairo.command" --setup-only </dev/tty

say_step "Sign in to GitHub Copilot (Kairo's brain)"
echo "You need a GitHub account with Copilot; the free plan works."
echo "Copilot will open now. Sign in if it asks, choose to TRUST this folder, then type /exit"
read -r -p "Press Enter to continue..." </dev/tty
( cd "$DIR" && copilot </dev/tty ) || true

if [ -f "$DIR/token.json" ]; then
  echo; echo "Gmail and Google Calendar are already connected."
else
say_step "Gmail and Google Calendar (optional)"
read -r -p "Connect Gmail and Google Calendar now? Takes about 5 minutes. [y/N] " yn </dev/tty
if [[ "$yn" =~ ^[Yy] ]]; then
  "$DIR/kairo.command" --google </dev/tty || true
else
  echo "Skipped. Connect it later with:  $DIR/kairo.command --google"
fi
fi

if [ "$(uname)" = "Darwin" ]; then
  printf "\n\033[1mKairo is installed.\033[0m Press Cmd+Space, type Kairo, press Enter to start talking.\n"
else
  printf "\n\033[1mKairo is installed.\033[0m Search your apps for Kairo, or run: %s/kairo.command\n" "$DIR"
fi
