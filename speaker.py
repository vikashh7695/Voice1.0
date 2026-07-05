"""
speaker.py
Handles all text-to-speech (TTS) output using pyttsx3 (offline, no API key needed).

Note: a fresh engine is built for every call to speak(), rather than
reusing one global engine across the whole program. pyttsx3's SAPI5
driver (Windows) has a well-known bug where reusing the same engine
instance causes engine.runAndWait() to hang on the second call onward -
rebuilding it each time avoids that entirely, at the cost of a tiny
(unnoticeable) extra startup delay per utterance.
"""

import pyttsx3

import event_bus

VOICE_RATE = 175      # words per minute
VOICE_VOLUME = 1.0    # 0.0 to 1.0
VOICE_INDEX = 1       # 0 = default, 1 = often female on Windows


def _build_engine() -> "pyttsx3.Engine":
    engine = pyttsx3.init()
    engine.setProperty("rate", VOICE_RATE)
    engine.setProperty("volume", VOICE_VOLUME)

    voices = engine.getProperty("voices")
    if len(voices) > VOICE_INDEX:
        engine.setProperty("voice", voices[VOICE_INDEX].id)

    return engine


def speak(text: str) -> None:
    """Speak the given text out loud and also print it, so you have a log."""
    print(f"Assistant: {text}")
    event_bus.emit("assistant", text)
    event_bus.emit("status", "speaking")

    engine = _build_engine()
    engine.say(text)
    engine.runAndWait()
    engine.stop()

    event_bus.emit("status", "idle")