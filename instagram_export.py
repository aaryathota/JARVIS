"""
Instagram export - NO Instagram login, ever.

Automated logins are the thing that gets Instagram accounts flagged or banned, so JARVIS no
longer talks to Instagram at all. Instead, every Short that is made is also saved here:

    instagram_ready/
        20261118_201530_funny-moment.mp4   <- vertical 9:16, captions already burned in
        20261118_201530_funny-moment.txt   <- title + caption, ready to paste

Upload them to Instagram yourself, then delete them (JARVIS never deletes this folder).
Change the folder with the INSTAGRAM_EXPORT_DIR environment variable.
"""

import os
import re
import shutil
from datetime import datetime

EXPORT_DIR = os.getenv("INSTAGRAM_EXPORT_DIR", "instagram_ready")


def _slug(text, limit=40):
    text = re.sub(r"[^a-z0-9]+", "-", (text or "clip").lower()).strip("-")
    return (text[:limit].strip("-")) or "clip"


def _for_instagram(text):
    """Drop YouTube-only tags (#Shorts / #youtubeshorts) from a title or caption."""
    text = re.sub(r"\s*#(?:youtube)?shorts\b", "", text or "", flags=re.I)
    return re.sub(r"[ \t]+\n", "\n", text).strip()


def save_for_instagram(clip_path, title="", caption="", video_format="short", move=False):
    """
    Put a captioned clip (plus a caption text file) in the instagram_ready folder.
    Only vertical Shorts are exported - Reels are 9:16 - proper videos are skipped.
    move=True moves the file instead of copying it. Returns the new path, or None.
    Never raises.
    """
    try:
        if video_format != "short":
            return None
        if not (clip_path and os.path.exists(clip_path)):
            return None
        os.makedirs(EXPORT_DIR, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = os.path.join(EXPORT_DIR, f"{stamp}_{_slug(title)}")
        dest = base + ".mp4"
        n = 2
        while os.path.exists(dest):                      # two clips in the same second
            dest = f"{base}_{n}.mp4"
            n += 1
        (shutil.move if move else shutil.copy2)(clip_path, dest)
        with open(os.path.splitext(dest)[0] + ".txt", "w", encoding="utf-8") as f:
            f.write(_for_instagram(title) + "\n\n" + _for_instagram(caption)[:2200] + "\n")
        print(f"[INSTAGRAM READY] Saved captioned clip: {dest}  "
              f"(upload it yourself, then delete it)")
        return dest
    except Exception as e:
        print(f"[INSTAGRAM READY] Could not save a copy: {type(e).__name__}: {e}")
        return None