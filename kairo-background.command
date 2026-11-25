#!/bin/bash
# Start Kairo with its Terminal window minimized to the Dock (used by Kairo.app and the hotkey).
printf '\e[2t'                       # ask Terminal to minimize this window
export KAIRO_ANNOUNCE=1              # say "Ready" when listening, since the window is hidden
exec "$(dirname "$0")/kairo.command"
