"""Talk to Kairo out loud: it listens, sends when you stop talking, and speaks the reply.

Copilot (the kairo agent) does the thinking. This script only adds ears and a voice.
Start it with:  ./kairo.command   (or double-click kairo.command in Finder)
Interrupt Kairo while it's talking by just speaking (or press Ctrl+C to cut it off).
Say "goodbye" and it sleeps until you say "Kairo" again. Say "shut down" (or press Ctrl+C)
to close it completely.
"""
import os
import re
import shutil
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path

import speech_recognition as sr

HERE = Path(__file__).resolve().parent
SILENCE = float(os.environ.get("KAIRO_SILENCE_SECONDS", "2.5"))   # pause that means "send"
RATE = os.environ.get("KAIRO_VOICE_RATE", "185")
VOICE_PREFS = [os.environ.get("KAIRO_VOICE", ""), "Jamie (Premium)", "Jamie (Enhanced)", "Jamie",
               "Daniel (Premium)", "Daniel (Enhanced)", "Daniel"]
SLEEP_PHRASES = ["goodbye", "good bye", "goodnight", "good night", "bye", "stop listening",
                 "that's all", "that is all", "stop", "see you later", "see ya", "go to sleep"]
OFF_PHRASES = ["shut down", "shutdown", "turn off", "power down", "exit", "quit"]
HUSH_PHRASES = ["stop", "wait", "hold on", "hang on", "pause", "quiet", "shh", "okay okay",
                "ok ok", "enough", "never mind", "nevermind"]
WAKE_WORDS = ["kairo", "cairo", "kyro", "kiro", "kyra", "chiro", "kai ro", "kyrie", "cairo's"]


def _short_match(text, phrases):
    words = re.sub(r"[^a-z' ]", " ", text.lower()).split()
    if not words or len(words) > 5:          # longer sentences are real requests
        return False
    joined = " ".join(words)
    return any(re.search(rf"\b{re.escape(p)}\b", joined) for p in phrases)


def is_goodbye(text):
    """Short sign-offs like 'goodbye', 'bye Kairo', 'okay goodbye Cairo' -> Kairo goes to sleep."""
    return _short_match(text, SLEEP_PHRASES)


def is_shutdown(text):
    """'shut down', 'turn off', 'quit' -> Kairo closes completely."""
    return _short_match(text, OFF_PHRASES)


def wake_request(text):
    """If the user said Kairo's name, return what they said after it ('' if just the name).
    Returns None if the name wasn't said."""
    low = text.lower()
    for w in WAKE_WORDS:
        m = re.search(rf"\b{re.escape(w)}\b[,.!?]*", low)
        if m:
            return text[m.end():].strip(" ,.!?")
    return None


def pick_voice():
    out = subprocess.run(["say", "-v", "?"], capture_output=True, text=True).stdout
    installed = {re.split(r"\s{2,}", line.strip())[0] for line in out.splitlines() if line.strip()}
    for v in VOICE_PREFS:
        if v and v in installed:
            return v
    return None


VOICE = pick_voice()


ROMAN = {"I": "1", "II": "2", "III": "3", "IV": "4", "V": "5", "VI": "6", "VII": "7",
         "VIII": "8", "IX": "9", "X": "10"}
COURSE_WORDS = (r"Lab|Laboratory|Part|Level|Unit|Module|Section|Chapter|Volume|Phase|Exam|Quiz|"
                r"Biology|Chemistry|Physics|Anatomy|Physiology|Calculus|Kinesiology|Spanish|French|"
                r"English|Composition|Algebra|Statistics|Psychology|Practicum|Seminar|Clinical|Course")


def numerals(text):
    """'General Biology Lab I' -> 'General Biology Lab 1'; 'Exam III' -> 'Exam 3'.
    Multi-letter numerals (II, III, IV...) convert anywhere; a lone 'I' only after a course word."""
    text = re.sub(r"\b(II|III|IV|VI|VII|VIII|IX)\b", lambda m: ROMAN[m.group(1)], text)
    return re.sub(rf"\b({COURSE_WORDS})\s+(I|V|X)\b(?!')", lambda m: f"{m.group(1)} {ROMAN[m.group(2)]}", text)


EARS = {}          # the recognizer and mic, set up in main()
INTERRUPT_LOUDNESS = float(os.environ.get("KAIRO_INTERRUPT_LOUDNESS", "2.5"))  # x room noise


def _is_echo(heard, spoken):
    """True if what the mic picked up is mostly Kairo's own voice from the speakers."""
    words = re.findall(r"[a-z']+", heard.lower())
    if not words:
        return True
    said = set(re.findall(r"[a-z']+", spoken.lower()))
    return sum(w in said for w in words) / len(words) > 0.6


def speak(text):
    """Say text out loud. Returns what the user said if they interrupted, else None."""
    text = numerals(text)
    clean = re.sub(r"```.*?```", " (I've put some code on screen.) ", text, flags=re.S)
    clean = re.sub(r"[*_#`>|]", "", clean)
    clean = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", clean)          # [link](url) -> link
    cmd = ["say", "-r", RATE] + (["-v", VOICE] if VOICE else [])
    proc = subprocess.Popen(cmd + [clean])
    caught = {}

    def listen_for_interrupt():
        rec, mic = EARS.get("rec"), EARS.get("mic")
        if not rec:
            return
        ears = sr.Recognizer()
        ears.dynamic_energy_threshold = False
        ears.energy_threshold = rec.energy_threshold * INTERRUPT_LOUDNESS   # ignore quiet echo
        ears.pause_threshold = 1.0
        with mic as source:
            while proc.poll() is None:
                try:
                    audio = ears.listen(source, timeout=1, phrase_time_limit=8)
                except sr.WaitTimeoutError:
                    continue
                if proc.poll() is not None:
                    break
                try:
                    heard = ears.recognize_google(audio)
                except (sr.UnknownValueError, sr.RequestError):
                    continue
                if _is_echo(heard, clean):
                    continue
                caught["text"] = heard
                proc.terminate()
                break

    t = threading.Thread(target=listen_for_interrupt, daemon=True)
    t.start()
    try:
        proc.wait()
    except KeyboardInterrupt:                    # Ctrl+C while talking = just stop talking
        proc.terminate()
        print("(interrupted)")
    t.join(timeout=10)
    if caught.get("text"):
        print("(interrupted)")
    return caught.get("text")


def ask_kairo(message, first):
    now = datetime.now().astimezone().strftime("%A, %B %d, %Y, %I:%M %p %Z")
    message = f"[Now: {now}. Spoken by the user; may contain speech-to-text mistakes.]\n{message}"
    cmd = ["copilot", "-p", message, "--agent=kairo", "-s", "--no-color",
           "--allow-tool=read", "--allow-tool=write(memory.md)", "--allow-tool=shell(./kt:*)"]
    if os.environ.get("KAIRO_MODEL"):
        cmd.append(f"--model={os.environ['KAIRO_MODEL']}")
    if not first:
        cmd.append("--continue")                                    # same conversation
    run = subprocess.run(cmd, capture_output=True, text=True, cwd=HERE)
    reply = run.stdout.strip()
    if run.returncode != 0 or not reply:
        err = (run.stderr or "").strip().splitlines()
        return "Sorry, Copilot gave me an error. " + (err[-1] if err else "")
    return reply


def sync_memory():
    """Back up what Kairo learned (memory.md) to GitHub, quietly. Skips if nothing changed."""
    git = ["git", "-C", str(HERE)]
    if subprocess.run(git + ["ls-files", "--error-unmatch", "memory.md"], capture_output=True).returncode != 0:
        return                         # memory.md is private to this Mac (the default)
    if not subprocess.run(git + ["status", "--porcelain", "memory.md"], capture_output=True, text=True).stdout.strip():
        return
    subprocess.run(git + ["commit", "-q", "-m", "Kairo memory update", "memory.md"], capture_output=True)
    ok = subprocess.run(git + ["push", "-q"], capture_output=True).returncode == 0
    print("Saved what I learned to GitHub." if ok else "Saved what I learned (GitHub upload will retry next time).")


def main():
    if not shutil.which("copilot"):
        sys.exit("Copilot CLI isn't installed. Run: brew install copilot-cli")
    rec = sr.Recognizer()
    rec.pause_threshold = SILENCE
    rec.dynamic_energy_threshold = True
    mic = sr.Microphone()
    with mic as source:
        print("Calibrating the mic, stay quiet for a second...")
        rec.adjust_for_ambient_noise(source, duration=1)
    EARS.update(rec=rec, mic=mic)

    print(f"\nKairo is listening (voice: {VOICE or 'default'}). Talk over it to interrupt. "
          "Say 'goodbye' to pause, 'shut down' to close.\n")
    first = True
    pending = None                       # something the user said while interrupting Kairo
    if not (HERE / ".kairo-started").exists():
        reply = ask_kairo("Hi Kairo.", first=True)
        (HERE / ".kairo-started").touch()
        first = False
        print(f"Kairo: {reply}\n")
        pending = speak(reply)

    asleep = False
    try:
        while True:
            interrupted = False
            if pending:
                heard, pending, interrupted = pending, None, True
            else:
                with mic as source:
                    print("Sleeping. Say 'Kairo' to wake me..." if asleep else "Listening...")
                    try:
                        audio = rec.listen(source, timeout=None, phrase_time_limit=90)
                    except KeyboardInterrupt:
                        break
                try:
                    heard = rec.recognize_google(audio)
                except sr.UnknownValueError:
                    continue                                            # silence or noise
                except sr.RequestError:
                    print("Speech recognition needs internet. Trying again...")
                    continue

            if is_shutdown(heard):
                print(f"You: {heard}")
                speak("Shutting down. Goodbye.")
                break
            if asleep:
                rest = wake_request(heard)
                if rest is None:
                    continue                                            # not for Kairo; stay asleep
                print(f"You: {heard}")
                asleep = False
                if not rest:
                    pending = speak("Yes?")
                    continue
                heard = rest                                            # "Kairo, what's due today?"
            else:
                print(f"You: {heard}")
                if interrupted and (_short_match(heard, HUSH_PHRASES) or wake_request(heard) == ""):
                    continue                                            # "stop" / "Kairo" = just be quiet
                if is_goodbye(heard):
                    speak("Goodbye. Say my name if you need me.")
                    asleep = True
                    sync_memory()
                    continue
                rest = wake_request(heard)
                if rest == "":                                          # just "Kairo" / "wait"
                    pending = speak("Yes?")
                    continue

            print("Kairo is thinking...")
            reply = ask_kairo(heard, first)
            first = False
            print(f"Kairo: {reply}\n")
            pending = speak(reply)
    finally:
        sync_memory()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBye.")
