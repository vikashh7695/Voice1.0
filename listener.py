"""
listener.py
Handles microphone input and converts speech to text using Google's
speech recognition API (free tier, requires internet).
"""

import logging
import os

import setuptools  # noqa: F401  (must import before speech_recognition on Python 3.12+, restores distutils shim)
import speech_recognition as sr

import event_bus

# Log every recognition attempt to a file next to the script/exe, since
# the windowed builds have no visible console. If a command seems to
# get "ignored", check assistant.log - it shows exactly what was heard
# (or that nothing was heard at all).
LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assistant.log")
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

recognizer = sr.Recognizer()
recognizer.pause_threshold = 1.0   # seconds of silence before it stops listening
# No hardcoded energy_threshold here on purpose - dynamic_energy_threshold
# (on by default) lets the recognizer adapt to the room's actual noise
# level each time, rather than using one fixed number that could be wrong
# for your mic and end up filtering out quieter/shorter words.

_calibrated = False


def calibrate() -> None:
    """Run this at startup (and again whenever background noise may have
    changed) so per-call listening doesn't have to re-calibrate, which
    eats the first half-second of your speech."""
    global _calibrated
    with sr.Microphone() as source:
        print("Calibrating for background noise, stay quiet for a moment...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
    _calibrated = True
    logging.info(f"Calibrated. energy_threshold={recognizer.energy_threshold:.1f}")


def listen(phrase_time_limit: int = 8) -> str:
    """
    Listens on the default microphone and returns recognized text
    in lowercase. Returns an empty string if nothing was understood.
    """
    if not _calibrated:
        calibrate()

    with sr.Microphone() as source:
        print("Listening...")
        event_bus.emit("status", "listening")
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=phrase_time_limit)
        except sr.WaitTimeoutError:
            logging.info("No speech detected (timeout).")
            event_bus.emit("status", "idle")
            return ""

    try:
        text = recognizer.recognize_google(audio)
        print(f"You: {text}")
        logging.info(f"Heard: '{text}'")
        event_bus.emit("user", text)
        event_bus.emit("status", "idle")
        return text.lower()
    except sr.UnknownValueError:
        logging.info("Heard something, but couldn't transcribe it.")
        event_bus.emit("status", "idle")
        return ""
    except sr.RequestError as e:
        print("Speech service is unreachable (check your internet connection).")
        logging.warning(f"Speech API request failed: {e}")
        event_bus.emit("status", "idle")
        return ""