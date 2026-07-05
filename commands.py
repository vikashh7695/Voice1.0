"""
commands.py
Maps recognized speech to actions. Add new commands by writing a handler
function and registering it in COMMANDS below.
"""

import datetime
import os
import random
import re
import subprocess
import sys
import webbrowser

import wikipedia
import pywhatkit

import spotify_client
from speaker import speak

# ---- individual command handlers -------------------------------------------

# Desktop apps to launch. The right-hand side is the command run via subprocess.
# "code" works out of the box IF VS Code's installer added it to PATH
# (default checkbox on Windows/Mac installers). Test it yourself first by
# opening a terminal and typing: code --version
# If that fails, replace "code" with the full path to Code.exe, e.g.:
# r"C:\Users\<you>\AppData\Local\Programs\Microsoft VS Code\Code.exe"
WINDOWS_APPS = {
    "vs code": ["code"],
    "visual studio code": ["code"],
    "notepad": ["notepad"],
    "calculator": ["calc"],
    "file explorer": ["explorer"],
    "explorer": ["explorer"],
    "command prompt": ["cmd"],
    "terminal": ["wt"],  # Windows Terminal; falls back to cmd if not installed
}

MAC_APPS = {
    "vs code": ["open", "-a", "Visual Studio Code"],
    "visual studio code": ["open", "-a", "Visual Studio Code"],
    "notes": ["open", "-a", "Notes"],
    "calculator": ["open", "-a", "Calculator"],
    "finder": ["open", "-a", "Finder"],
    "terminal": ["open", "-a", "Terminal"],
}

LINUX_APPS = {
    "vs code": ["code"],
    "visual studio code": ["code"],
    "calculator": ["gnome-calculator"],
    "file manager": ["nautilus"],
    "terminal": ["gnome-terminal"],
}

APPS = WINDOWS_APPS if sys.platform.startswith("win") else (
    MAC_APPS if sys.platform == "darwin" else LINUX_APPS
)

WEBSITES = {
    "youtube": "https://youtube.com",
    "google": "https://google.com",
    "github": "https://github.com",
    "gmail": "https://mail.google.com",
}


def tell_time(_query: str) -> None:
    now = datetime.datetime.now().strftime("%I:%M %p")
    speak(f"It's currently {now}")


def tell_date(_query: str) -> None:
    today = datetime.datetime.now().strftime("%A, %B %d, %Y")
    speak(f"Today is {today}")


def open_target(query: str) -> None:
    """Handles both 'open <website>' and 'open <app>' in one command,
    since they usually share the trigger word 'open'."""

    # Check apps first (more specific matches like "vs code" before "code" alone)
    for name, command in sorted(APPS.items(), key=lambda x: -len(x[0])):
        if name in query:
            speak(f"Opening {name}")
            try:
                subprocess.Popen(command, shell=(sys.platform.startswith("win")))
            except FileNotFoundError:
                speak(f"I couldn't find {name} on your system. Check it's installed and on PATH.")
            return

    # Then check known websites
    for name, url in WEBSITES.items():
        if name in query:
            speak(f"Opening {name}")
            webbrowser.open(url)
            return

    # Generic fallback: "open browser" / "open web browser"
    if "browser" in query:
        speak("Opening your browser")
        webbrowser.open("https://google.com")
        return

    speak("I don't have that saved. You can add it to APPS or WEBSITES in commands.py")


def search_google(query: str) -> None:
    term = query.replace("search for", "").replace("search", "").strip()
    if not term:
        speak("What should I search for?")
        return
    speak(f"Searching Google for {term}")
    pywhatkit.search(term)


def play_spotify(query: str) -> None:
    song = query
    for phrase in ("on spotify", "in spotify", "from spotify", "via spotify", "spotify"):
        song = song.replace(phrase, "")
    song = song.replace("play", "").strip()
    # Clean up a dangling preposition left at the end, e.g. "believer in" -> "believer"
    song = re.sub(r"\s+(on|in|from|via)\s*$", "", song).strip()

    if not song:
        speak("What should I play on Spotify?")
        return

    speak(f"Searching Spotify for {song}")
    uri = spotify_client.search_track(song)

    if not uri:
        speak(
            "I couldn't find that on Spotify, or Spotify isn't set up yet. "
            "Check your .env file has the right client ID and secret."
        )
        return

    speak(f"Playing {song} on Spotify")
    if sys.platform.startswith("win"):
        os.startfile(uri)  # hands off to the installed Spotify app
    else:
        webbrowser.open(uri)


def play_youtube(query: str) -> None:
    term = query.replace("play", "").strip()
    if not term:
        speak("What should I play?")
        return
    speak(f"Playing {term} on YouTube")
    pywhatkit.playonyt(term)


def wiki_lookup(query: str) -> None:
    term = query.replace("who is", "").replace("what is", "").replace("wikipedia", "").strip()
    if not term:
        speak("Who or what should I look up?")
        return
    try:
        speak("Searching Wikipedia...")
        summary = wikipedia.summary(term, sentences=2)
        speak(summary)
    except wikipedia.exceptions.DisambiguationError:
        speak(f"There are multiple results for {term}. Try being more specific.")
    except wikipedia.exceptions.PageError:
        speak(f"I couldn't find anything on Wikipedia for {term}")


def tell_joke(_query: str) -> None:
    jokes = [
        "Why do programmers prefer dark mode? Because light attracts bugs.",
        "I told my computer I needed a break, and it said no problem, it'll go to sleep too.",
        "There are 10 types of people: those who understand binary, and those who don't.",
    ]
    speak(random.choice(jokes))


def already_awake(_query: str) -> None:
    speak("No need for a wake word here — just type or tap the mic and tell me what you need.")


def stop_assistant(_query: str) -> None:
    speak("Goodbye!")
    raise SystemExit


# ---- command routing --------------------------------------------------------
# Each entry: (list of trigger phrases, handler function)
# Checked top to bottom, first match wins — order matters.

COMMANDS = [
    (["what time", "current time"], tell_time),
    (["what date", "today's date", "what day"], tell_date),
    (["open"], open_target),
    (["spotify"], play_spotify),
    (["play"], play_youtube),
    (["search for", "search"], search_google),
    (["who is", "what is"], wiki_lookup),
    (["tell me a joke", "joke"], tell_joke),
    (["hey assistant", "hey python", "wake up"], already_awake),
    (["stop listening", "shut down", "power off", "stop", "exit", "quit", "goodbye"], stop_assistant),
]


def handle_command(query: str) -> None:
    """Match the recognized text against known triggers and run the handler."""
    if not query:
        return

    for triggers, handler in COMMANDS:
        if any(trigger in query for trigger in triggers):
            handler(query)
            return

    speak("I didn't understand that command. Try asking for the time, a joke, or to open a website.")