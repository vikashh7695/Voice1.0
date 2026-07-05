"""
main.py
Entry point. Runs a loop: listen -> (check wake word) -> command session -> repeat.

Usage:
    python main.py
Say "hey assistant" to wake it up, then speak commands one after another —
no need to repeat the wake word between them. After a couple of silences
in a row, it goes back to sleep and waits for the wake word again.
Say "stop" / "exit" / "quit" / "stop listening" / "shut down" to end
the program entirely.
"""

import multiprocessing

from listener import listen, calibrate
from speaker import speak
from commands import handle_command

WAKE_WORDS = ["hey assistant", "hey python", "wake up"]
COMMAND_RETRY_ATTEMPTS = 3   # re-listens within a single command attempt
SESSION_SILENCE_LIMIT = 2    # consecutive empty command attempts before sleeping


def get_command() -> str:
    """Actively retry listening until we get something, instead of
    giving up after a single empty attempt."""
    for attempt in range(COMMAND_RETRY_ATTEMPTS):
        command_text = listen(phrase_time_limit=6)
        if command_text:
            return command_text
        if attempt < COMMAND_RETRY_ATTEMPTS - 1:
            speak("I didn't catch that, go ahead.")
    return ""


def command_session() -> None:
    """Keep taking commands back-to-back after a single wake word,
    until the user goes quiet for a couple of turns or says stop."""
    silence_streak = 0

    while silence_streak < SESSION_SILENCE_LIMIT:
        command_text = get_command()

        if not command_text:
            silence_streak += 1
            continue

        silence_streak = 0
        handle_command(command_text)  # may raise SystemExit via "stop"

    speak("Going back to sleep. Say the wake word when you need me.")


def main() -> None:
    calibrate()
    speak("Voice assistant ready. Say a wake word to begin.")

    while True:
        text = listen()

        if not text:
            continue

        if any(wake in text for wake in WAKE_WORDS):
            speak("Yes?")
            # Re-calibrate here too - background noise can drift over a
            # long-running session, and accuracy matters most right when
            # you're about to give a command (e.g. a short word like "stop").
            calibrate()
            try:
                command_session()
            except SystemExit:
                break
        # else: ignore ambient speech until wake word is heard


if __name__ == "__main__":
    # Prevents the packaged .exe from re-launching itself as a subprocess
    # on Windows - some bundled dependency (commonly something pulled in
    # via pyautogui/mouseinfo through pywhatkit) spawns a child process,
    # and without this guard PyInstaller's onefile bootloader can end up
    # re-running the whole script as that child, which looks like a restart.
    multiprocessing.freeze_support()

    try:
        main()
    except KeyboardInterrupt:
        speak("Shutting down.")