"""
tray.py
Alternative entry point: runs the voice assistant hidden in the system
tray instead of a visible console window. Right-click the tray icon
and choose "Quit" to exit, or say "stop" / "exit" / "quit" by voice —
both do the same thing.

Usage:
    python tray.py
"""

import multiprocessing
import threading

from PIL import Image, ImageDraw
import pystray

from main import main as run_assistant_loop

icon = None  # set in main(); read by run_voice_loop() to close the tray
             # icon if the assistant exits via a voice "stop" command


def build_icon_image() -> Image.Image:
    """Draws a simple microphone icon at runtime, so no external
    .ico/.png file needs to ship alongside the exe."""
    size = 64
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    blue = (80, 130, 255, 255)

    draw.rounded_rectangle([22, 6, 42, 38], radius=10, fill=blue)          # mic body
    draw.arc([14, 22, 50, 50], start=0, end=180, fill=blue, width=4)       # mic stand arc
    draw.line([32, 50, 32, 58], fill=blue, width=4)                       # stand pole
    draw.line([20, 58, 44, 58], fill=blue, width=4)                       # base

    return image


def quit_assistant(icon_ref: "pystray.Icon", _item) -> None:
    icon_ref.stop()


def run_voice_loop() -> None:
    """Runs the existing console assistant loop on a background thread.
    If it exits (voice 'stop' raises SystemExit inside it), also close
    the tray icon so the whole program ends cleanly."""
    try:
        run_assistant_loop()
    except SystemExit:
        pass
    finally:
        if icon is not None:
            icon.stop()


def main() -> None:
    global icon

    menu = pystray.Menu(pystray.MenuItem("Quit", quit_assistant))
    icon = pystray.Icon("VoiceAssistant", build_icon_image(), "Voice Assistant", menu)

    listener_thread = threading.Thread(target=run_voice_loop, daemon=True)
    listener_thread.start()

    icon.run()  # blocks the main thread until icon.stop() is called


if __name__ == "__main__":
    # Prevents the packaged .exe from re-launching itself as a subprocess
    # on Windows (same reasoning as in main.py).
    multiprocessing.freeze_support()
    main()