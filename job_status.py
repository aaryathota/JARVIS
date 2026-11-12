"""
Shorts job status - one shared place the pipeline reports to and the dashboard reads from.
Works for jobs started from the dashboard AND by voice.
"""

import threading
import time
from collections import deque

_lock = threading.Lock()
_state = {}
_log = deque(maxlen=400)


def _blank():
    return {"running": False, "step": "Awaiting orders, sir…", "total": 0,
            "clips": [], "result": [], "url": "", "error": ""}


_state.update(_blank())


def start(total, url=""):
    with _lock:
        _state.update(_blank())
        _state.update(running=True, total=total, url=url, step="Starting…",
                      clips=[{"n": i + 1, "status": "queued", "detail": "", "start": None,
                              "reason": "", "title": "", "url": "", "id": ""} for i in range(total)])
        _log.clear()


def step(text):
    with _lock:
        _state["step"] = text


def clip(n, **fields):
    """Update clip number n (1-based): status, detail, start, reason, title, url, id."""
    with _lock:
        if 1 <= n <= len(_state["clips"]):
            _state["clips"][n - 1].update(fields)


def finish(result=None, error=""):
    with _lock:
        _state["running"] = False
        _state["result"] = list(result or [])
        _state["error"] = error
        _state["step"] = (f"Mission complete — {len(_state['result'])} Short(s) uploaded"
                          if _state["result"] else "Finished — nothing was uploaded (see log)")


def is_running():
    with _lock:
        return _state["running"]


def snapshot():
    with _lock:
        snap = dict(_state)
        snap["clips"] = [dict(c) for c in _state["clips"]]
        snap["log"] = list(_log)[-120:]
        return snap


def say(*args, sep=" ", **kwargs):
    """print() that also records the line for the dashboard log."""
    msg = sep.join(str(a) for a in args)
    try:
        print(msg, **kwargs)
    except Exception:
        pass
    stamp = time.strftime("%H:%M:%S")
    for line in msg.split("\n"):
        if line.strip():
            _log.append(f"{stamp}  {line.strip()}")