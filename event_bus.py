"""
event_bus.py
Tiny publish/subscribe helper so listener.py and speaker.py can announce
what they heard/said without importing a GUI directly. Keeps the console
and tray versions working with zero changes: if nothing subscribes,
emit() is just a harmless no-op.
"""

from typing import Callable, List

_subscribers: List[Callable[[str, str], None]] = []


def subscribe(callback: Callable[[str, str], None]) -> None:
    """Register a function to be called as callback(kind, payload) for
    every event. kind is one of: "user", "assistant", "status"."""
    _subscribers.append(callback)


def emit(kind: str, payload: str) -> None:
    for callback in _subscribers:
        try:
            callback(kind, payload)
        except Exception:
            pass  # a broken subscriber should never crash the voice loop