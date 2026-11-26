"""Turn Kairo's full computer control on or off:  kairo.command --computer-control on|off"""
import platform
import sys

import computer

on = len(sys.argv) > 1 and sys.argv[1].lower() in ("on", "yes", "true", "1")
computer.set_control(on)
if not on:
    print("Full computer control is OFF. Kairo can still open apps, websites, and files.")
    sys.exit(0)

print("Full computer control is ON: Kairo can see your screen, click, type, and press keys.")
print("It will ask before anything that sends, buys, deletes, or posts.")
print("Emergency stop: move your mouse hard into any corner of the screen.\n")
if platform.system() == "Darwin":
    print("Your Mac needs two permissions for Terminal (one time):")
    print("  1. System Settings -> Privacy & Security -> Accessibility -> turn on Terminal")
    print("  2. System Settings -> Privacy & Security -> Screen & System Audio Recording -> turn on Terminal")
    print("Then quit and reopen Terminal. Opening those settings now...")
    import subprocess
    subprocess.run(["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"])
try:
    info = computer.screenshot()
    print(f"\nTest screenshot worked ({info['width']}x{info['height']}).")
except Exception as e:
    print(f"\nTest screenshot didn't work yet ({e}). Grant the permissions above, then run this again.")
