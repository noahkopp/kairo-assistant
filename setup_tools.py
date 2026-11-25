"""Checks Kairo's Gmail/Calendar connections. Run by kairo.command; safe to re-run."""
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# 1. Your memory file (private, stays on this Mac).
if not (HERE / "memory.md").exists():
    shutil.copy(HERE / "memory.template.md", HERE / "memory.md")

# 2. Make sure Google and the Mac calendars work now, not mid-conversation.
sys.path.insert(0, str(HERE))
try:
    import google_tools
    google_tools.warm_up()          # opens the browser to sign in only if needed
    print("Gmail and Google Calendar: connected.")
except FileNotFoundError:
    print("Gmail/Google Calendar: not set up yet (optional). To connect: ./kairo.command --google")
except Exception as e:
    print(f"Gmail/Google Calendar: not connected yet ({e})")
try:
    import mac_calendar
    n = len(mac_calendar.list_calendars())
    print(f"Mac calendars: connected ({n} calendars from the Calendar app).")
except Exception as e:
    print(f"Mac calendars: not connected yet ({e})")
try:
    import mac_mail
    accts = mac_mail.mail_accounts()
    names = ", ".join(a["name"] for a in accts) or "none"
    print(f"Mac Mail: connected (accounts: {names}).")
    if not accts:
        print("  To add an email account: System Settings -> Internet Accounts -> the account "
              "-> turn on Mail.")
except Exception as e:
    print(f"Mac Mail: not connected yet ({e})")

# Kairo.app: opens Kairo in Terminal (or brings it forward if it's already running).
# Open it with Spotlight (Cmd+Space, "Kairo") or a keyboard shortcut.
import subprocess
import tempfile

APP = Path("/Applications/Kairo.app")
SCRIPT = f'''on run
    set isRunning to (do shell script "pgrep -f 'python talk.py' >/dev/null && echo yes || echo no")
    tell application "Terminal"
        activate
        if isRunning is "no" then do script "cd {HERE} && ./kairo.command"
    end tell
end run
'''
try:
    marker = APP / "Contents" / "Resources" / "kairo-launcher-v2"
    if not marker.exists():
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "kairo.applescript"
            src.write_text(SCRIPT)
            if APP.exists():
                subprocess.run(["rm", "-rf", str(APP)], check=True)
            subprocess.run(["osacompile", "-o", str(APP), str(src)], check=True, capture_output=True)
            # Kairo's avatar as the app icon
            icon_src = HERE / "assets" / "kairo-avatar.png"
            iconset = Path(tmp) / "kairo.iconset"
            iconset.mkdir()
            for size in (16, 32, 128, 256, 512):
                for scale in (1, 2):
                    px = size * scale
                    name = f"icon_{size}x{size}{'@2x' if scale == 2 else ''}.png"
                    subprocess.run(["sips", "-z", str(px), str(px), str(icon_src), "--out", str(iconset / name)],
                                   capture_output=True)
            icns = APP / "Contents" / "Resources" / "applet.icns"
            subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o", str(icns)], capture_output=True)
        marker.touch()
        subprocess.run(["touch", str(APP)])
        print("Installed Kairo.app: press Cmd+Space, type Kairo, press Enter to start it.")
except Exception as e:
    print(f"Couldn't install Kairo.app ({e}). You can still start Kairo with ./kairo.command")
