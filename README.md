# Kairo

<img src="assets/kairo-avatar.png" width="110" align="right">

**A Jarvis-style voice assistant for Mac, Windows, and Linux.** Talk to it out loud and it talks back. It checks
your email and calendars, drafts replies, and learns about you as you go.

## Install

**Mac or Linux:** open Terminal, paste this line, and press Enter:
```bash
curl -fsSL https://raw.githubusercontent.com/noahkopp/kairo-assistant/main/install.sh | bash
```

**Windows 10/11:** open PowerShell (press the Windows key, type PowerShell, press Enter), paste
this line, and press Enter:
```powershell
irm https://raw.githubusercontent.com/noahkopp/kairo-assistant/main/install.ps1 | iex
```

The installer walks you through everything, in about 10 minutes:
1. It installs the tools Kairo needs.
2. It signs you in to **GitHub Copilot**, Kairo's brain. You need a GitHub account with Copilot; the free plan works.
3. It connects **Gmail and Google Calendar** (optional). It opens each Google page and tells you what to click.

**You need:** a microphone and speakers, and a GitHub account with Copilot (the free plan works).

## Use it

- **Start Kairo with the hotkey,** which the installer sets up for you. If Kairo is already running and asleep, the same key wakes it. Kairo runs minimized and says "Ready." To see what it's hearing, click its Terminal window in the Dock (on Windows, the taskbar).
  - **Mac:** Control+Option+K
  - **Windows and Linux:** Ctrl+Alt+K
- **Or start it from your apps:**
  - **Mac:** press Cmd+Space, type **Kairo**, and press Enter.
  - **Windows:** press the Windows key, type **Kairo**, and press Enter.
  - **Linux:** search your apps for **Kairo**.
- **Or type `kairo` in Terminal** (Mac and Linux).

  Then just talk.
- Kairo sends your message when you pause, and answers out loud.
- **Interrupt** by talking over it. Say "stop" or "wait" and it goes quiet.
- Say **"goodbye"** and it sleeps. Say **"Kairo"**, or press the hotkey, to wake it.
- Say **"shut down"** to close it.

The first time you talk to it, Kairo asks a few questions to get to know you.

## What it can do

| | Mac | Windows | Linux |
|---|:-:|:-:|:-:|
| Voice in and out, interrupting, sleep/wake | ✓ | ✓ | ✓ |
| Memory that learns about you | ✓ | ✓ | ✓ |
| Gmail: read, search, draft, mark read, archive, send when you say so | ✓ | ✓ | ✓ |
| Google Calendar | ✓ | ✓ | ✓ |
| Every calendar in the Calendar app (Outlook, iCloud, class feeds) | ✓ | | |
| Every account in the Mail app (Outlook, iCloud, school/work) | ✓ | | |

**On Windows or Linux:** to see an Outlook or school calendar, subscribe to it in Google Calendar (Other calendars → From URL).

Kairo saves facts about you, and lessons from your corrections, in `memory.md`. That file stays on your computer.

## Privacy

- Kairo runs on your computer. Your memory and sign-ins stay in the Kairo folder.
- Gmail access uses **your own** Google app, which you create during setup. Your email never goes through anyone else's project.
- Requests are answered by GitHub Copilot under your own GitHub account. Speech-to-text uses Google's free speech service.

## Later

- **Connect Gmail later:** run `kairo.command --google` in the Kairo folder. On Windows, run `kairo.cmd --google`.
- **Updates are automatic.** Each time Kairo starts, it gets the newest version first. Your memory and sign-ins are never touched.
- **Uninstall:** delete the `kairo-assistant` folder in your home folder. Then remove the launcher:
  - **Mac:** delete `/Applications/Kairo.app` and `~/Library/Services/Start Kairo.workflow`.
  - **Windows:** delete the Kairo Start menu entry.
  - **Linux:** delete `~/.local/share/applications/kairo.desktop`, and remove the Kairo shortcut in your keyboard settings.
