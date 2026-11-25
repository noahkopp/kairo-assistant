"""Checks Kairo's Gmail/Calendar connections. Run by kairo.command; safe to re-run."""
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SYSTEM = platform.system()          # "Darwin" (Mac), "Windows", or "Linux"
LAUNCH = "kairo.cmd" if SYSTEM == "Windows" else "./kairo.command"

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
    print(f"Gmail/Google Calendar: not set up yet (optional). To connect: {LAUNCH} --google")
except Exception as e:
    print(f"Gmail/Google Calendar: not connected yet ({e})")
if SYSTEM == "Darwin":
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


# ---------------------------------------------------------------- launchers --
def install_mac_app():
    """Kairo.app: opens Kairo in Terminal, or brings it forward if it's already running."""
    import tempfile

    APP = Path("/Applications/Kairo.app")
    SCRIPT = f'''on run
        set isRunning to (do shell script "cd '{HERE}' && (.venv/bin/python launch.py && echo yes || echo no)")
        tell application "Terminal"
            activate
            if isRunning is "no" then do script "cd {HERE} && ./kairo.command"
        end tell
    end run
    '''
    try:
        marker = APP / "Contents" / "Resources" / "kairo-launcher-v4"
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


def install_windows_shortcut():
    """Start menu entry 'Kairo' (press the Windows key, type Kairo, Enter)."""
    start_menu = Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
    link = start_menu / "Kairo.lnk"
    ps = (f"$s = (New-Object -ComObject WScript.Shell).CreateShortcut('{link}'); "
          f"$s.TargetPath = '{HERE / 'kairo.cmd'}'; $s.WorkingDirectory = '{HERE}'; "
          f"$s.Description = 'Kairo voice assistant'; $s.Hotkey = 'CTRL+ALT+K'; $s.Save()")
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True)
    if r.returncode == 0:
        print("Added Kairo to the Start menu. Hotkey: Ctrl+Alt+K (or press the Windows key and type Kairo).")
    else:
        print(f"Couldn't add a Start menu entry. Start Kairo by double-clicking kairo.cmd in {HERE}")


def install_linux_desktop_entry():
    """App-menu entry 'Kairo' that opens a terminal running Kairo."""
    apps = Path.home() / ".local" / "share" / "applications"
    apps.mkdir(parents=True, exist_ok=True)
    (apps / "kairo.desktop").write_text(f"""[Desktop Entry]
Type=Application
Name=Kairo
Comment=Kairo voice assistant
Exec={HERE / 'kairo.command'}
Icon={HERE / 'assets' / 'kairo-avatar.png'}
Terminal=true
Categories=Utility;
""")
    print("Added Kairo to your apps menu: search for Kairo to start it.")


def register_mac_app():
    """Make sure macOS (Spotlight, `open`, the hotkey) knows about Kairo.app."""
    app = "/Applications/Kairo.app"
    lsreg = ("/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework"
             "/Support/lsregister")
    subprocess.run([lsreg, "-f", app], capture_output=True)
    subprocess.run(["mdimport", app], capture_output=True)


def install_mac_hotkey():
    """Control+Option+K anywhere -> opens Kairo.app (a Quick Action with a keyboard shortcut)."""
    import plistlib
    wf = Path.home() / "Library" / "Services" / "Start Kairo.workflow" / "Contents"
    wf.mkdir(parents=True, exist_ok=True)
    plistlib.dump({"NSServices": [{
        "NSMenuItem": {"default": "Start Kairo"},
        "NSMessage": "runWorkflowAsService",
    }]}, (wf / "Info.plist").open("wb"))
    action = {
        "AMAccepts": {"Container": "List", "Optional": True, "Types": ["com.apple.cocoa.string"]},
        "AMActionVersion": "2.0.3",
        "AMApplication": ["Automator"],
        "AMParameterProperties": {"COMMAND_STRING": {}, "CheckedForUserDefaultShell": {},
                                  "inputMethod": {}, "shell": {}, "source": {}},
        "AMProvides": {"Container": "List", "Types": ["com.apple.cocoa.string"]},
        "ActionBundlePath": "/System/Library/Automator/Run Shell Script.action",
        "ActionName": "Run Shell Script",
        "ActionParameters": {"COMMAND_STRING": "open /Applications/Kairo.app", "CheckedForUserDefaultShell": True,
                             "inputMethod": 0, "shell": "/bin/bash", "source": ""},
        "BundleIdentifier": "com.apple.RunShellScript",
        "CFBundleVersion": "2.0.3",
        "CanShowSelectedItemsWhenRun": False,
        "CanShowWhenRun": True,
        "Category": ["AMCategoryUtilities"],
        "Class Name": "RunShellScriptAction",
        "InputUUID": "7D3A1C2E-0B1F-4E5A-9C8D-1A2B3C4D5E61",
        "Keywords": ["Shell", "Script", "Command", "Run", "Unix"],
        "OutputUUID": "7D3A1C2E-0B1F-4E5A-9C8D-1A2B3C4D5E62",
        "UUID": "7D3A1C2E-0B1F-4E5A-9C8D-1A2B3C4D5E63",
        "UnlocalizedApplications": ["Automator"],
        "arguments": {},
        "isViewVisible": 1,
        "location": "309.000000:253.000000",
        "nibPath": "/System/Library/Automator/Run Shell Script.action/Contents/Resources/Base.lproj/main.nib",
    }
    plistlib.dump({
        "AMApplicationBuild": "523",
        "AMApplicationVersion": "2.10",
        "AMDocumentVersion": "2",
        "actions": [{"action": action, "isViewVisible": 1}],
        "connectors": {},
        "workflowMetaData": {
            "serviceInputTypeIdentifier": "com.apple.Automator.nothing",
            "serviceOutputTypeIdentifier": "com.apple.Automator.nothing",
            "serviceProcessesInput": 0,
            "workflowTypeIdentifier": "com.apple.Automator.servicesMenu",
        },
    }, (wf / "document.wflow").open("wb"))
    key = "(null) - Start Kairo - runWorkflowAsService"
    subprocess.run(["defaults", "write", "pbs", "NSServicesStatus", "-dict-add", key,
                    '{ "enabled_context_menu" = 1; "enabled_services_menu" = 1; '
                    '"key_equivalent" = "^~k"; }'], capture_output=True)
    subprocess.run(["/System/Library/CoreServices/pbs", "-flush"], capture_output=True)
    subprocess.run(["/System/Library/CoreServices/pbs", "-update"], capture_output=True)
    print("Hotkey: Control+Option+K starts Kairo (or wakes it). If it doesn't work right away, "
          "log out and back in once.")


def install_linux_hotkey():
    """Ctrl+Alt+K on GNOME-based desktops (Ubuntu, Fedora). Others: set it by hand."""
    script = HERE / "kairo-hotkey.sh"
    script.write_text(f"""#!/bin/bash
# Ctrl+Alt+K: wake Kairo if it's running, otherwise open it in a terminal.
cd "{HERE}"
.venv/bin/python launch.py && exit 0
for t in gnome-terminal x-terminal-emulator konsole xfce4-terminal xterm; do
  if command -v "$t" >/dev/null; then
    if [ "$t" = gnome-terminal ]; then exec gnome-terminal -- "{HERE}/kairo.command"; fi
    exec "$t" -e "{HERE}/kairo.command"
  fi
done
""")
    script.chmod(0o755)
    if not shutil.which("gsettings"):
        print(f"To add a hotkey, bind Ctrl+Alt+K to {script} in your desktop's keyboard settings.")
        return
    base = "org.gnome.settings-daemon.plugins.media-keys"
    path = "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/kairo/"
    try:
        cur = subprocess.run(["gsettings", "get", base, "custom-keybindings"],
                             capture_output=True, text=True, check=True).stdout.strip()
        items = [] if cur.startswith("@") else [x.strip(" '") for x in cur.strip("[]").split(",") if x.strip()]
        if path not in items:
            items.append(path)
            subprocess.run(["gsettings", "set", base, "custom-keybindings",
                            "[" + ", ".join(f"'{x}'" for x in items) + "]"], check=True)
        schema = f"{base}.custom-keybinding:{path}"
        for k, v in (("name", "Kairo"), ("command", str(script)), ("binding", "<Control><Alt>k")):
            subprocess.run(["gsettings", "set", schema, k, v], check=True)
        print("Hotkey: Ctrl+Alt+K starts Kairo (or wakes it).")
    except Exception:
        print(f"To add a hotkey, bind Ctrl+Alt+K to {script} in your desktop's keyboard settings.")


def install_terminal_command():
    """Lets you type `kairo` in any Terminal window (Mac/Linux)."""
    target = HERE / "kairo.command"
    for d in (Path("/opt/homebrew/bin"), Path("/usr/local/bin"), Path.home() / ".local" / "bin"):
        if d == Path.home() / ".local" / "bin":
            d.mkdir(parents=True, exist_ok=True)
        if d.is_dir() and os.access(d, os.W_OK):
            link = d / "kairo"
            if link.is_symlink() or link.exists():
                link.unlink()
            link.symlink_to(target)
            if d == Path.home() / ".local" / "bin" and str(d) not in os.environ.get("PATH", ""):
                rc = Path.home() / (".zshrc" if SYSTEM == "Darwin" else ".bashrc")
                with rc.open("a") as f:
                    f.write('\nexport PATH="$HOME/.local/bin:$PATH"   # added by Kairo\n')
            print("Terminal command: type kairo to start Kairo.")
            return


if SYSTEM != "Windows":
    try:
        install_terminal_command()
    except Exception:
        pass

if SYSTEM == "Darwin":
    install_mac_app()
    register_mac_app()
    try:
        install_mac_hotkey()
    except Exception as e:
        print(f"Couldn't set up the hotkey ({e}). Start Kairo with Cmd+Space, Kairo.")
elif SYSTEM == "Windows":
    install_windows_shortcut()
else:
    install_linux_desktop_entry()
    install_linux_hotkey()
