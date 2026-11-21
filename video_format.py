"""
Video format - one place that knows the difference between a YouTube Short
and a proper (horizontal, longer) YouTube video.

  "short"  vertical 9:16, ~30 s, #Shorts title/tags, short titles
  "video"  horizontal 16:9, length of your choice (asked in minutes), normal title/tags, Instagram skipped

Default for anything that isn't asked: settings.json -> "upload_format" ("short" or "video").
"""

import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))

FORMATS = {
    "short": {
        "label": "YouTube Shorts", "noun": "Short", "vertical": True,
        "clip_seconds": 30, "min_seconds": 20, "max_seconds": 45, "max_title": 60,
    },
    "video": {
        "label": "proper YouTube videos", "noun": "video", "vertical": False,
        "clip_seconds": 180, "min_seconds": 90, "max_seconds": 300, "max_title": 100,
    },
}


def default_format():
    try:
        with open(os.path.join(HERE, "settings.json"), "r", encoding="utf-8") as f:
            value = json.load(f).get("upload_format", "short")
        return value if value in FORMATS else "short"
    except (OSError, ValueError):
        return "short"


def normalize(value):
    """'short' / 'video' for a clear value, None if it isn't one."""
    v = str(value or "").strip().lower()
    if v in FORMATS:
        return v
    if v in {"shorts", "s", "1", "vertical"}:
        return "short"
    if v in {"videos", "v", "2", "long", "proper", "normal", "regular", "horizontal", "landscape"}:
        return "video"
    return None


def resolve(value=None):
    """Always returns 'short' or 'video' (falls back to the settings default)."""
    return normalize(value) or default_format()


def parse_answer(text):
    """Understand a typed/spoken answer to 'Shorts or proper videos?'. None if unclear."""
    t = (text or "").strip().lower()
    if not t:
        return None
    if re.search(r"\bshorts?\b|\bvertical\b", t):
        return "short"
    if re.search(r"\bvideos?\b|\bproper\b|\blong\b|\bfull\b|\bhorizontal\b|\blandscape\b|\bnormal\b|\bregular\b", t):
        return "video"
    return normalize(t)


def from_command(text):
    """Format named in a command ('upload shorts', 'make proper videos'). None if not stated.
    Strict on purpose: 'from this video' must NOT count as asking for a proper video."""
    t = (text or "").lower()
    if re.search(r"\bshorts?\b|\bvertical\b", t):
        return "short"
    if re.search(r"\b(proper|full|long|long-form|normal|regular|horizontal|landscape)\s+videos?\b", t):
        return "video"
    return None


MAX_VIDEO_MINUTES = 60
DEFAULT_VIDEO_MINUTES = 5


def clamp_minutes(minutes):
    try:
        return max(1.0, min(float(MAX_VIDEO_MINUTES), float(minutes)))
    except (TypeError, ValueError):
        return float(DEFAULT_VIDEO_MINUTES)


def minutes_from_command(text):
    """'make 10 minute videos' -> 10.  None if no length with a unit was said."""
    m = re.search(r"(\d+(?:\.\d+)?)\s*[- ]?\s*(?:minutes?|mins?)\b", (text or "").lower())
    return clamp_minutes(m.group(1)) if m else None


def parse_minutes_answer(text, default=DEFAULT_VIDEO_MINUTES):
    """Understand a typed/spoken answer to 'how many minutes?' ('10', '10 minutes', '' -> default)."""
    t = (text or "").strip().lower()
    if not t:
        return clamp_minutes(default)
    m = re.search(r"\d+(?:\.\d+)?", t)
    return clamp_minutes(m.group(0)) if m else clamp_minutes(default)


def spec(fmt, minutes=None):
    """Format settings. For proper videos, `minutes` sets the length you asked for (+/- 15%)."""
    fmt = resolve(fmt)
    base = FORMATS[fmt]
    if fmt == "video" and minutes:
        target = int(clamp_minutes(minutes) * 60)
        return dict(base, clip_seconds=target, min_seconds=int(target * 0.85), max_seconds=int(target * 1.15))
    return base