"""Guided Gmail + Google Calendar setup for Kairo (about 5 minutes, one time).

Kairo uses your OWN small Google app, so your email never goes through anyone else's
project. This opens each Google page for you and tells you what to click.

  .venv/bin/python google_setup.py
"""
import shutil
import sys
import time
import webbrowser
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGET = HERE / "credentials.json"
DOWNLOADS = Path.home() / "Downloads"

B, R = "\033[1m", "\033[0m"


def step(n, title, url, lines):
    print(f"\n{B}Step {n} of 4: {title}{R}")
    for line in lines:
        print(f"   - {line}")
    input(f"\n   Press Enter to open the page...")
    webbrowser.open(url)
    input("   When you're done on that page, press Enter here. ")


def main():
    if TARGET.exists():
        print("Google is already set up (credentials.json found).")
        return sign_in()

    print(f"\n{B}Connect Gmail and Google Calendar{R}")
    print("Kairo needs a small Google app that belongs to you. Four quick steps; I'll open")
    print("each page. Sign in with the Google account whose Gmail you want Kairo to use.")

    step(1, "Create a project",
         "https://console.cloud.google.com/projectcreate",
         ["Project name: Kairo", "Click Create, and wait a few seconds for it to finish",
          "If Google asks you to accept terms first, accept them"])

    step(2, "Turn on Gmail and Calendar",
         "https://console.cloud.google.com/flows/enableapi?apiid=gmail.googleapis.com,calendar-json.googleapis.com",
         ["Make sure the project at the top says Kairo", "Click Next, then Enable"])

    step(3, "Name your app",
         "https://console.cloud.google.com/auth/overview",
         ["Click Get started",
          "App name: Kairo.  Support email: your email.  Click Next",
          "Audience: External.  Click Next",
          "Contact email: your email.  Click Next, check the box, click Create",
          "Then click Audience on the left, and click Publish app, then Confirm",
          "  (this keeps you signed in; otherwise Google signs you out every 7 days)"])

    started = time.time()
    step(4, "Download your key",
         "https://console.cloud.google.com/auth/clients/create",
         ["Application type: Desktop app.  Name: Kairo",
          "Click Create, then click Download JSON in the box that appears"])

    found = wait_for_download(started)
    if not found:
        print("\nI couldn't find the downloaded file. Move the file that starts with")
        print(f"'client_secret_' into {HERE} and rename it credentials.json, then run this again.")
        sys.exit(1)
    shutil.copy(found, TARGET)
    print(f"\nGot it ({found.name}).")
    sign_in()


def wait_for_download(since, seconds=120):
    print("\nLooking for the downloaded file in Downloads...")
    deadline = time.time() + seconds
    while time.time() < deadline:
        files = [f for f in DOWNLOADS.glob("client_secret_*.json") if f.stat().st_mtime >= since - 600]
        if files:
            return max(files, key=lambda f: f.stat().st_mtime)
        time.sleep(2)
    files = sorted(DOWNLOADS.glob("client_secret_*.json"), key=lambda f: f.stat().st_mtime)
    return files[-1] if files else None


def sign_in():
    print(f"\n{B}Last step: sign in{R}")
    print("   Your browser will open. Pick your Google account.")
    print("   Google will say it hasn't verified this app. That's expected: it's YOUR app.")
    print("   Click Advanced, then Go to Kairo, then check every box and click Continue.")
    input("\n   Press Enter to open the sign-in page...")
    sys.path.insert(0, str(HERE))
    import google_tools
    google_tools.warm_up()
    print(f"\n{B}Gmail and Google Calendar are connected.{R}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped. Run kairo.command --google (kairo.cmd --google on Windows) anytime to finish.")
