"""Hotkey / launcher helper: if Kairo is already running, wake it up instead of starting a
second copy. Exit code 0 = it was running (and was woken), 1 = not running.

  python launch.py --wake-if-running
"""
import os
import platform
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PID_FILE = HERE / ".kairo.pid"
WAKE_FILE = HERE / ".wake"


def alive(pid):
    if platform.system() == "Windows":
        import ctypes
        k = ctypes.windll.kernel32
        h = k.OpenProcess(0x1000, False, pid)          # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return False
        code = ctypes.c_ulong()
        k.GetExitCodeProcess(h, ctypes.byref(code))
        k.CloseHandle(h)
        return code.value == 259                       # STILL_ACTIVE
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def running():
    try:
        return alive(int(PID_FILE.read_text().strip()))
    except (FileNotFoundError, ValueError):
        return False


if __name__ == "__main__":
    if running():
        WAKE_FILE.touch()
        sys.exit(0)
    sys.exit(1)
