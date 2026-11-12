"""Shared runtime controls for cancellation and assistant shutdown."""

import threading


shutdown_event = threading.Event()
cancel_event = threading.Event()


def request_cancel():
    """Cancel the currently running operation without shutting down JARVIS."""
    cancel_event.set()


def clear_cancel():
    """Allow the next operation to run normally."""
    cancel_event.clear()


def is_cancelled():
    return cancel_event.is_set() or shutdown_event.is_set()