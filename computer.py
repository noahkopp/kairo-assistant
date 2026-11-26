"""Kairo's computer controls: open/quit apps, open websites and files, search, volume.
Works on Mac, Windows, and Linux (Linux volume needs pactl or amixer)."""
import os
import platform
import shutil
import subprocess
import urllib.parse
import webbrowser
from pathlib import Path

SYSTEM = platform.system()


def _run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30, **kw)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout or "command failed").strip().splitlines()[-1])
    return r.stdout.strip()


def open_app(name):
    """Open an app by name, e.g. 'Spotify', 'Notes', 'Calculator', 'Microsoft Word'."""
    if SYSTEM == "Darwin":
        _run(["open", "-a", name])
    elif SYSTEM == "Windows":
        _run(["powershell", "-NoProfile", "-Command", f"Start-Process '{name}'"])
    else:
        exe = shutil.which(name.lower()) or shutil.which(name.lower().replace(" ", "-"))
        if not exe:
            raise RuntimeError(f"Couldn't find an app called {name}")
        subprocess.Popen([exe], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    return {"opened": name}


def quit_app(name):
    """Quit an app (it may ask to save unsaved work)."""
    if SYSTEM == "Darwin":
        _run(["osascript", "-e", f'quit app "{name}"'])
    elif SYSTEM == "Windows":
        _run(["powershell", "-NoProfile", "-Command",
              f"Get-Process | Where-Object {{ $_.MainWindowTitle -and ($_.ProcessName -like '*{name}*' -or "
              f"$_.MainWindowTitle -like '*{name}*') }} | ForEach-Object {{ $_.CloseMainWindow() | Out-Null }}"])
    else:
        _run(["pkill", "-f", "-i", name])
    return {"quit": name}


def open_url(url):
    """Open a website in the default browser."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    webbrowser.open(url)
    return {"opened": url}


def search_web(query):
    """Open a Google search in the browser."""
    return open_url("https://www.google.com/search?q=" + urllib.parse.quote_plus(query))


def open_file(path):
    """Open a file or folder with its usual app. Paths are inside your home folder."""
    p = Path(os.path.expanduser(path)).resolve()
    if not str(p).startswith(str(Path.home().resolve())):
        raise ValueError("I only open files inside your home folder.")
    if not p.exists():
        raise FileNotFoundError(f"{p} doesn't exist")
    if SYSTEM == "Darwin":
        _run(["open", str(p)])
    elif SYSTEM == "Windows":
        os.startfile(str(p))
    else:
        subprocess.Popen(["xdg-open", str(p)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return {"opened": str(p)}


def set_volume(percent=None, mute=None):
    """Set the volume (0-100) and/or mute=true/false."""
    if SYSTEM == "Darwin":
        if percent is not None:
            _run(["osascript", "-e", f"set volume output volume {int(percent)}"])
        if mute is not None:
            _run(["osascript", "-e", f"set volume output muted {'true' if mute else 'false'}"])
    elif SYSTEM == "Windows":
        ps = "$w = New-Object -ComObject WScript.Shell; "
        if percent is not None:      # volume keys move 2% a press: all the way down, then up
            ps += f"1..50 | % {{ $w.SendKeys([char]174) }}; 1..{int(percent) // 2} | % {{ $w.SendKeys([char]175) }}; "
        if mute is not None:
            ps += "$w.SendKeys([char]173)"   # toggles mute
        _run(["powershell", "-NoProfile", "-Command", ps])
    else:
        if shutil.which("pactl"):
            if percent is not None:
                _run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{int(percent)}%"])
            if mute is not None:
                _run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "1" if mute else "0"])
        elif shutil.which("amixer"):
            if percent is not None:
                _run(["amixer", "-q", "sset", "Master", f"{int(percent)}%"])
            if mute is not None:
                _run(["amixer", "-q", "sset", "Master", "mute" if mute else "unmute"])
        else:
            raise RuntimeError("Volume control needs pactl or amixer.")
    return {"volume": percent, "muted": mute}


# ------------------------------------------------- full control (opt-in) --
# Seeing the screen, clicking, typing. Off unless the user turns it on with
#   kairo.command --computer-control on     (kairo.cmd on Windows)
import json

HERE = Path(__file__).resolve().parent
SETTINGS = HERE / "settings.json"
SCREEN = HERE / "files" / ".screen.png"


def _settings():
    try:
        return json.loads(SETTINGS.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def control_enabled():
    return bool(_settings().get("computer_control"))


def set_control(on):
    s = _settings()
    s["computer_control"] = bool(on)
    SETTINGS.write_text(json.dumps(s, indent=2))
    return s


def _require():
    if not control_enabled():
        raise RuntimeError("Full computer control is off. The user can turn it on by running "
                           "kairo.command --computer-control on (kairo.cmd on Windows) in Kairo's folder.")
    import pyautogui
    pyautogui.FAILSAFE = True          # slam the mouse into a screen corner to stop Kairo
    pyautogui.PAUSE = 0.15
    return pyautogui


def screenshot():
    """Capture the screen at click-coordinate size; view the saved image to see it."""
    pg = _require()
    w, h = pg.size()
    img = pg.screenshot()
    if img.size != (w, h):                       # Retina: shrink so pixels = click points
        img = img.resize((w, h))
    SCREEN.parent.mkdir(exist_ok=True)
    img.save(SCREEN)
    x, y = pg.position()
    return {"image": str(SCREEN.relative_to(HERE)), "width": w, "height": h, "mouse": [x, y],
            "note": "Open this image with your file viewer to see the screen. Coordinates in it "
                    "are the ones to click."}


def click(x, y, button="left", clicks=1):
    pg = _require()
    pg.click(int(x), int(y), clicks=int(clicks), button=button)
    return {"clicked": [int(x), int(y)], "button": button, "clicks": int(clicks)}


def type_text(text):
    pg = _require()
    if SYSTEM == "Darwin" or any(ord(c) > 127 for c in text):
        # paste instead of typing key by key: faster and handles any character
        import subprocess as sp
        if SYSTEM == "Darwin":
            sp.run(["pbcopy"], input=text, text=True)
            pg.hotkey("command", "v")
        else:
            pg.write(text, interval=0.01)
    else:
        pg.write(text, interval=0.01)
    return {"typed": len(text)}


def press(keys):
    """Press a key or combination: 'enter', 'tab', 'esc', 'cmd+l', 'ctrl+t', 'down'."""
    pg = _require()
    names = [k.strip().lower().replace("cmd", "command").replace("opt", "option")
             for k in keys.split("+")]
    pg.hotkey(*names) if len(names) > 1 else pg.press(names[0])
    return {"pressed": keys}


def scroll(direction="down", amount=5):
    pg = _require()
    n = int(amount) * (1 if direction == "up" else -1)
    pg.scroll(n * 100 if SYSTEM == "Darwin" else n * 120)
    return {"scrolled": direction, "amount": int(amount)}
