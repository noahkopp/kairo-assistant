# Kairo

<img src="assets/kairo-avatar.png" width="110" align="right">

**A Jarvis-style voice assistant for your Mac.** Talk to it out loud and it talks back. It checks
your email and calendars, drafts replies, and learns about you as you go.

## Install

Open **Terminal** (Cmd+Space, type Terminal, press Enter), paste this line, and press Enter:

```bash
curl -fsSL https://raw.githubusercontent.com/noahkopp/kairo-assistant/main/install.sh | bash
```

The installer walks you through everything, about 10 minutes:
1. **Installs the tools Kairo needs.**
2. **Signs you in to GitHub Copilot,** Kairo's brain. You need a free GitHub account with Copilot; the free plan works.
3. **Connects Gmail and Google Calendar (optional).** It opens each Google page and tells you what to click.

**You need** a Mac and a GitHub account with Copilot (the free plan works). The installer adds Homebrew if you don't have it.

## Use it

- **Start:** press Cmd+Space, type **Kairo**, and press Enter. Then just talk.
- Kairo sends your message when you pause, and answers out loud.
- **Interrupt** by talking over it. Say "stop" or "wait" and it goes quiet.
- Say **"goodbye"** and it sleeps. Say **"Kairo"** to wake it.
- Say **"shut down"** to close it.

The first time you talk to it, Kairo asks a few questions to get to know you.

## What it can do

- **Gmail:** read, search, summarize, draft replies, mark read, archive. It sends only when you say "send it."
- **Other email** (Outlook, iCloud, school or work accounts): anything in the Mac Mail app.
- **Calendars:** Google Calendar, plus everything in the Mac Calendar app (Outlook, iCloud, class feeds).
- **Memory:** Kairo saves facts about you and lessons from your corrections in `memory.md`. That file stays on your Mac.

## Privacy

- Kairo runs on your Mac. Your memory and sign-ins stay in the Kairo folder.
- Gmail access uses **your own** Google app, which you create during setup. Your email never goes through anyone else's project.
- Requests are answered by GitHub Copilot under your own GitHub account. Speech-to-text uses Google's free speech service.

## Later

- **Connect Gmail later:** `~/kairo-assistant/kairo.command --google`
- **Update Kairo:** run the install line again.
- **Uninstall:** delete the `kairo-assistant` folder in your home folder and `/Applications/Kairo.app`.
