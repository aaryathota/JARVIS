"""
ffmpeg finder - locates a MODERN ffmpeg no matter what order PATH is in.

Old ffmpeg builds (e.g. 2013) crash on YouTube's HTTPS streams. This module
checks every ffmpeg it can find, reads its libavcodec version, and picks the
newest one. Set the FFMPEG_PATH environment variable to force a specific one.
"""

import glob
import os
import re
import shutil
import subprocess

MIN_LIBAVCODEC = 58  # ffmpeg 4.x or newer
_cache = {}


def _libavcodec(path):
    try:
        out = subprocess.run([path, "-version"], capture_output=True, text=True, timeout=15).stdout
        m = re.search(r"libavcodec\s+(\d+)\.", out)
        return int(m.group(1)) if m else 0
    except Exception:
        return 0


def _runs_ok(path):
    """Quick sanity check: the binary can actually run a tiny encode."""
    try:
        r = subprocess.run(
            [path, "-v", "error", "-f", "lavfi", "-i", "color=c=black:s=64x64:d=0.1", "-f", "null", "-"],
            capture_output=True, timeout=20,
        )
        return r.returncode == 0
    except Exception:
        return False


def _candidates():
    exe = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
    found = []
    bundled = []

    def add(p):
        if p and os.path.isfile(p):
            key = os.path.normcase(os.path.realpath(p))
            if key not in [os.path.normcase(os.path.realpath(x)) for x in found]:
                found.append(p)

    for d in os.environ.get("PATH", "").split(os.pathsep):
        add(os.path.join(d.strip('"'), exe))

    local = os.environ.get("LOCALAPPDATA", "")
    if local:
        add(os.path.join(local, "Microsoft", "WinGet", "Links", exe))
        pattern = os.path.join(local, "Microsoft", "WinGet", "Packages", "*", "**", "bin", exe)
        for p in glob.glob(pattern, recursive=True):
            add(p)

    for p in (r"C:\ffmpeg\bin\ffmpeg.exe", r"C:\Program Files\ffmpeg\bin\ffmpeg.exe"):
        add(p)

    try:  # bundled with moviepy / imageio-ffmpeg when installed
        import imageio_ffmpeg
        bundled.append(imageio_ffmpeg.get_ffmpeg_exe())
    except Exception:
        pass
    return found, bundled


def find_ffmpeg():
    """Return the path of the newest ffmpeg found, or None if none is modern enough."""
    if "path" in _cache:
        return _cache["path"]

    override = os.environ.get("FFMPEG_PATH")
    if override and os.path.isfile(override):
        _cache["path"] = override
        return override

    system, bundled = _candidates()

    def best_of(paths):
        best, best_ver = None, 0
        for p in paths:
            v = _libavcodec(p)
            if v >= MIN_LIBAVCODEC and v > best_ver and _runs_ok(p):
                best, best_ver = p, v
        return best

    # Installed copies (winget, PATH, C:\ffmpeg) win; the bundled one is a last resort
    _cache["path"] = best_of(system) or best_of(bundled)
    return _cache["path"]


def find_ffprobe():
    """ffprobe from the same folder as the chosen ffmpeg, else from PATH."""
    ff = find_ffmpeg()
    if ff:
        probe = os.path.join(os.path.dirname(ff), "ffprobe.exe" if os.name == "nt" else "ffprobe")
        if os.path.isfile(probe):
            return probe
    return shutil.which("ffprobe")