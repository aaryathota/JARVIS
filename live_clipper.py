"""
Live Clipper - turn an ONGOING YouTube live stream into Shorts or proper videos.

It works exactly like clipping an already-uploaded video:

  1. Take the time window you give (e.g. "the last 10 minutes") as the "full video".
  2. SCAN it cheaply: download only the small audio / lowest-quality copy of that window.
  3. Pick the best moments in it (transcript + AI ranking, or loudest moments).
  4. Download ONLY those moments in good quality (a ~30 s slice, not 10 minutes).
  5. Make the Short / video, burn in captions, write the title with AI,
     upload to YouTube, and save a captioned copy in instagram_ready/ for you to post
     on Instagram yourself (JARVIS never logs in to Instagram).

If anything in that smart path is unavailable for a stream, it falls back to
downloading the whole window and picking inside it.

Everything is free: yt-dlp + FFmpeg + Groq free tier (+ local Whisper fallback).

Public API
    extract_youtube_url(text)            -> url or None
    is_live_url(url)                     -> True / False  (never raises)
    clip_live_stream(url, ...)           -> list of YouTube video IDs
                                            (or clip file paths when upload=False)
"""

import array
import glob
import importlib
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
import wave
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from job_status import say

MAX_BUFFER_MINUTES = 30   # longest time window one scan covers (long audio is sent as small mp3)
MIN_USEFUL_SECONDS = 15   # footage shorter than this is treated as "stream ended"
DEFAULT_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

_YT_URL = re.compile(
    r"(https?://(?:www\.|m\.)?(?:youtube\.com/(?:watch\?[^\s]*v=|live/|shorts/|embed/)|youtu\.be/)[\w\-]{6,}[^\s]*)",
    re.I)


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------
def extract_youtube_url(text):
    """Pull a YouTube link out of a spoken/typed command. None if there isn't one."""
    m = _YT_URL.search(text or "")
    return m.group(1).rstrip(".,)") if m else None


def _cancelled():
    try:
        from control import is_cancelled
        return is_cancelled()
    except Exception:
        return False


def _ffmpeg():
    from video_clipper import _tool
    return _tool("ffmpeg")


def _duration(path):
    try:
        from video_clipper import get_video_duration
        return float(get_video_duration(path) or 0)
    except Exception:
        return 0.0


# --------------------------------------------------------------------------
# 1. Is it live? + find the stream
# --------------------------------------------------------------------------
def probe_stream(url, clients=None):
    """yt-dlp metadata for the URL (no download). Raises on failure.
    clients: optional list of YouTube player clients to ask for (e.g. ["web_safari"])."""
    import yt_dlp
    opts = {"skip_download": True, "noplaylist": True, "quiet": True, "no_warnings": True}
    if clients:
        opts["extractor_args"] = {"youtube": {"player_client": list(clients)}}
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)


# YouTube only hands out HLS (the format we can rewind) to some "clients", and it is
# flaky about which one answers. Try them all, remember the one that worked, retry.
_CLIENT_ATTEMPTS = [("default", None), ("web_safari", ["web_safari"]), ("ios", ["ios"]),
                    ("mweb", ["mweb"]), ("tv", ["tv"]), ("android_vr", ["android_vr"])]
_preferred_client = [None]   # name of the client that worked last time


def resolve_stream(url, first_info=None, rounds=3):
    """Find a rewindable HLS stream. Returns (info, [stream urls], headers).
    Tries several YouTube clients (best-known first) and retries, because YouTube's
    answer changes from request to request."""
    order = list(_CLIENT_ATTEMPTS)
    pref = _preferred_client[0]
    if pref:
        order.sort(key=lambda c: 0 if c[0] == pref else 1)
    seen = []
    for attempt in range(rounds):
        for name, clients in order:
            try:
                info = first_info if (name == "default" and first_info and attempt == 0) \
                    else probe_stream(url, clients)
            except Exception as e:
                seen.append(f"{name}: {type(e).__name__}: {str(e)[:60]}")
                continue
            try:
                inputs, headers = _hls_inputs(info)
                _preferred_client[0] = name
                if name != "default":
                    say(f"[LIVE] Using the '{name}' YouTube client")
                return info, inputs, headers
            except RuntimeError:
                protos = sorted({(f.get("protocol") or "?") for f in info.get("formats", [])})
                seen.append(f"{name}: {len(info.get('formats', []))} formats, protocols={protos}")
        if attempt < rounds - 1:
            say("[LIVE] YouTube did not give a usable stream - trying again...")
            time.sleep(2)
    say("[LIVE] No rewindable (HLS) stream from any YouTube client -> " + " | ".join(seen[-8:]))
    say("[LIVE] Fix: update yt-dlp (pip install -U yt-dlp) and install Deno (https://deno.com) "
        "so yt-dlp can unlock all formats; then try again. Run `yt-dlp -F <link>` to see what YouTube offers.")
    raise RuntimeError("No playable live (HLS) stream found for this link")


def _is_live_info(info):
    return bool(info.get("is_live")) or info.get("live_status") in ("is_live", "post_live")


def is_live_url(url):
    """True if the link is a stream that is live right now. Never raises."""
    try:
        return _is_live_info(probe_stream(url))
    except Exception as e:
        say(f"[LIVE] Could not check live status: {type(e).__name__}: {str(e)[:100]}")
        return False


def _hls_inputs(info):
    """Return ([urls], headers) for the best <=720p HLS stream. Muxed preferred."""
    fmts = [f for f in info.get("formats", []) if f.get("url") and "m3u8" in (f.get("protocol") or "")]
    has_v = lambda f: f.get("vcodec") not in (None, "none")
    has_a = lambda f: f.get("acodec") not in (None, "none")

    def best(cands):
        under = [f for f in cands if (f.get("height") or 0) <= 720]
        if under:
            return max(under, key=lambda f: (f.get("height") or 0, f.get("tbr") or 0))
        return min(cands, key=lambda f: f.get("height") or 10 ** 6)

    muxed = [f for f in fmts if has_v(f) and has_a(f)]
    if muxed:
        f = best(muxed)
        return [f["url"]], f.get("http_headers") or info.get("http_headers") or {}
    vids = [f for f in fmts if has_v(f) and not has_a(f)]
    auds = [f for f in fmts if has_a(f) and not has_v(f)]
    if vids and auds:
        v = best(vids)
        a = max(auds, key=lambda f: f.get("abr") or f.get("tbr") or 0)
        return [v["url"], a["url"]], v.get("http_headers") or info.get("http_headers") or {}
    for key in ("manifest_url", "url"):
        if info.get(key) and "m3u8" in info[key]:
            return [info[key]], info.get("http_headers") or {}
    raise RuntimeError("No playable live (HLS) stream found for this link")


def _fetch(url, ua):
    req = Request(url, headers={"User-Agent": ua})
    with urlopen(req, timeout=12) as r:
        return r.read().decode("utf-8", "replace")


def _playlist_stats(url, ua=DEFAULT_UA):
    """(average segment seconds, number of segments) of an HLS media playlist."""
    try:
        text = _fetch(url, ua)
        if "#EXT-X-STREAM-INF" in text:  # master playlist -> follow the last variant
            variants = [l.strip() for l in text.splitlines() if l.strip() and not l.startswith("#")]
            if variants:
                text = _fetch(urljoin(url, variants[-1]), ua)
        durs = [float(x) for x in re.findall(r"#EXTINF:([\d.]+)", text)]
        if durs:
            return sum(durs) / len(durs), len(durs)
    except Exception as e:
        say(f"[LIVE] Could not read playlist ({type(e).__name__}); assuming 5s segments")
    return 5.0, 0


# --------------------------------------------------------------------------
# 2. Fetching past footage (segments are plain files - download them directly)
# --------------------------------------------------------------------------
_http_session = [None]


def _http():
    """One shared HTTP session (keep-alive connections look like a normal player, not a bot)."""
    if _http_session[0] is None:
        import requests
        from requests.adapters import HTTPAdapter
        sess = requests.Session()
        for scheme in ("https://", "http://"):
            sess.mount(scheme, HTTPAdapter(pool_connections=8, pool_maxsize=8))
        _http_session[0] = sess
    return _http_session[0]


def _download_bytes(url, ua, tries=4):
    """GET with retries and backoff (YouTube sometimes answers 403/429 to a burst of requests)."""
    last = None
    for i in range(tries):
        try:
            r = _http().get(url, headers={"User-Agent": ua, "Accept": "*/*",
                                          "Accept-Language": "en-US,en;q=0.9"}, timeout=20)
            if r.status_code == 200 and r.content:
                return r.content
            last = RuntimeError(f"HTTP {r.status_code}")
        except Exception as e:
            last = e
        time.sleep(0.8 * (i + 1))
    raise last


def parse_media_playlist(url, ua=DEFAULT_UA):
    """Read an HLS media playlist -> {"segments": [{"seq","dur","uri"}], "map": init-segment uri or None}."""
    text = _fetch(url, ua)
    if "#EXT-X-STREAM-INF" in text:  # master playlist -> follow the last variant
        variants = [l.strip() for l in text.splitlines() if l.strip() and not l.startswith("#")]
        url = urljoin(url, variants[-1])
        text = _fetch(url, ua)
    m = re.search(r"#EXT-X-MEDIA-SEQUENCE:(\d+)", text)
    media_seq = int(m.group(1)) if m else 0
    segs, dur = [], None
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("#EXTINF:"):
            dur = float(line.split(":", 1)[1].split(",")[0])
        elif line and not line.startswith("#") and dur is not None:
            uri = urljoin(url, line)
            sq = re.search(r"/sq/(\d+)", uri)  # YouTube numbers segments identically across qualities
            segs.append({"seq": int(sq.group(1)) if sq else media_seq + len(segs), "dur": dur, "uri": uri})
            dur = None
    mp = re.search(r'#EXT-X-MAP:URI="([^"]+)"', text)
    return {"segments": segs, "map": urljoin(url, mp.group(1)) if mp else None}


def _download_segments(segments, init_uri, out_path, ua, work_dir, workers=4):
    """Download segments in parallel and merge them into ONE plain media file
    (MPEG-TS, or init + fragments for fMP4). FFmpeg reads that reliably and never
    has to wait for the live edge. Raises if any segment can't be fetched."""
    os.makedirs(work_dir, exist_ok=True)
    jobs = [(os.path.join(work_dir, f"s{k:05d}.seg"), g["uri"]) for k, g in enumerate(segments)]
    init_path = None
    if init_uri:
        init_path = os.path.join(work_dir, "init.seg")
        jobs.append((init_path, init_uri))

    def grab(job):
        path, u = job
        data = _download_bytes(u, ua)
        if not data or data[:1] == b"<":      # HTML error page, not media
            raise RuntimeError("segment came back as an error page")
        with open(path, "wb") as f:
            f.write(data)

    with ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(grab, jobs))
    with open(out_path, "wb") as out:
        if init_path:
            with open(init_path, "rb") as f:
                out.write(f.read())
        for k in range(len(segments)):
            seg = os.path.join(work_dir, f"s{k:05d}.seg")
            with open(seg, "rb") as f:
                out.write(f.read())
            try:
                os.remove(seg)
            except OSError:
                pass
    if os.path.getsize(out_path) < 10_000:
        raise RuntimeError("downloaded footage is too small")
    return out_path


def _snapshot_window(url, rewind_seconds, work_dir, ua=DEFAULT_UA, workers=4):
    """
    Copy the PAST part of a live HLS playlist (the last `rewind_seconds`) and merge it into
    ONE plain media file. Returns (seconds covered, merged file path); (0.0, None) on failure.
    """
    try:
        pl = parse_media_playlist(url, ua)
        segs = pl["segments"]
        if not segs:
            return 0.0, None
        picked, covered = [], 0.0
        for g in reversed(segs):          # newest -> oldest until we have enough
            picked.append(g)
            covered += g["dur"]
            if covered >= rewind_seconds:
                break
        picked.reverse()
        merged = os.path.join(work_dir, "window.mp4" if pl["map"] else "window.ts")
        os.makedirs(work_dir, exist_ok=True)
        _download_segments(picked, pl["map"], merged, ua, work_dir, workers)
        return covered, merged
    except Exception as e:
        say(f"[LIVE] Could not snapshot the stream history ({type(e).__name__}: {str(e)[:80]})")
        return 0.0, None


def record_live(inputs, out_path, seconds, rewind_seconds=0, ua=DEFAULT_UA):
    """
    Fallback / watch recording: save `seconds` of the stream into out_path (mkv, stream copy).
    rewind_seconds > 0 grabs that much PAST footage first (instantly, no waiting).
    Returns the number of seconds recorded.
    """
    window_files, window_dirs, snapshot = [], [], False
    back_segments = 1
    if rewind_seconds > 0:
        stem = os.path.splitext(out_path)[0]
        covered = []
        say("[LIVE] Fetching the past footage...")
        for i, src in enumerate(inputs):
            wdir = f"{stem}_win{i}"
            window_dirs.append(wdir)
            cov, pl = _snapshot_window(src, rewind_seconds, wdir, ua)
            covered.append(cov)
            window_files.append(pl)
        if covered and min(covered) > 0:
            snapshot = True
            have = min(covered)
            if have < rewind_seconds - 10:
                say(f"[LIVE] Stream only keeps ~{have:.0f}s of history - using that")
            seconds = have if seconds <= rewind_seconds else seconds
            say(f"[LIVE] Rewinding ~{have:.0f}s - grabbing past footage now (no waiting)")
        else:
            # last resort: FFmpeg's own live_start_index
            seg_dur, n_segs = _playlist_stats(inputs[0], ua)
            available = n_segs * seg_dur if n_segs else rewind_seconds
            requested = rewind_seconds
            rewind_seconds = min(rewind_seconds, available)
            back_segments = max(1, math.ceil(rewind_seconds / seg_dur))
            if seconds <= requested:
                seconds = rewind_seconds
            say(f"[LIVE] Rewinding ~{rewind_seconds:.0f}s ({back_segments} segments of {seg_dur:.1f}s)")

    cmd = [_ffmpeg(), "-y", "-loglevel", "error"]
    if snapshot:   # everything is already on disk as plain media files
        for pl in window_files:
            cmd += ["-analyzeduration", "20M", "-probesize", "20M", "-fflags", "+genpts", "-i", pl]
    else:
        cmd += ["-user_agent", ua]
        for src in inputs:
            cmd += ["-live_start_index", str(-back_segments), "-i", src]
    if len(inputs) == 2:
        cmd += ["-map", "0:v:0", "-map", "1:a:0"]
    cmd += ["-t", str(int(seconds)), "-c", "copy", out_path]

    if snapshot:
        say(f"[LIVE] Assembling {int(seconds)}s of the stream...")
    else:
        say(f"[LIVE] Last resort: recording in real time - this will take about {seconds / 60:.0f} min "
            f"(YouTube blocked the fast download).")
    t0 = time.time()
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    deadline = time.time() + (max(300, seconds) if snapshot else seconds + 90)
    try:
        while proc.poll() is None:
            if _cancelled() or time.time() > deadline:
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()
                break
            time.sleep(0.5)
    finally:
        if proc.poll() is None:
            proc.kill()
        for wdir in window_dirs:
            shutil.rmtree(wdir, ignore_errors=True)
    if snapshot:
        say(f"[LIVE] Rewind footage ready in {time.time() - t0:.0f}s")
    err = (proc.stderr.read() if proc.stderr else "")[-800:]
    if not (os.path.exists(out_path) and os.path.getsize(out_path) > 0):
        say(f"[LIVE] Recording failed: {err}")
        return 0.0
    return _duration(out_path)


# --------------------------------------------------------------------------
# 3. SMART REWIND - scan the window cheaply, then fetch only the best slices
# --------------------------------------------------------------------------
def _hls_variants(info):
    """Muxed (video+audio) HLS variants, lowest quality first. [] if none."""
    out = []
    for f in info.get("formats", []):
        if f.get("url") and "m3u8" in (f.get("protocol") or "") \
                and f.get("vcodec") not in (None, "none") and f.get("acodec") not in (None, "none"):
            out.append({"url": f["url"], "height": f.get("height") or 0, "tbr": f.get("tbr") or 0})
    return sorted(out, key=lambda v: (v["height"], v["tbr"]))


def _audio_variant(info):
    """Smallest audio-only HLS variant (ideal for scanning), or None."""
    auds = [f for f in info.get("formats", [])
            if f.get("url") and "m3u8" in (f.get("protocol") or "")
            and f.get("acodec") not in (None, "none") and f.get("vcodec") in (None, "none")]
    if not auds:
        return None
    f = min(auds, key=lambda f: f.get("abr") or f.get("tbr") or 10 ** 6)
    return {"url": f["url"], "height": 0, "tbr": f.get("tbr") or 0}


def _remux(src, dst, ua=DEFAULT_UA):
    """Normalise timestamps of a merged segment file into an mkv. Returns True on success."""
    r = subprocess.run([_ffmpeg(), "-y", "-loglevel", "error", "-fflags", "+genpts", "-i", src,
                        "-c", "copy", dst], capture_output=True, text=True, timeout=300)
    return r.returncode == 0 and os.path.exists(dst) and os.path.getsize(dst) > 0


def _ffmpeg_fetch_slice(variant_url, first_seq, last_seq, out_path, ua, pad=1):
    """
    Fetch segments first_seq..last_seq (+/- `pad`) of a live variant with FFmpeg's OWN downloader
    (it often gets through when a plain Python download is blocked).
    Returns the sequence number of the first segment it really started at, or None.
    """
    try:
        pl = parse_media_playlist(variant_url, ua)
        segs = pl["segments"]
        if not segs:
            return None
        have_first, end_seq = segs[0]["seq"], segs[-1]["seq"]
        start_seq = first_seq - pad
        if start_seq < have_first or last_seq > end_seq:
            return None                                    # no longer in the buffer
        back = end_seq - start_seq + 1
        avg = sum(g["dur"] for g in segs) / len(segs)
        count = (last_seq - first_seq + 1) + 2 * pad
        cmd = [_ffmpeg(), "-y", "-loglevel", "verbose", "-user_agent", ua,
               "-live_start_index", str(-back), "-i", variant_url,
               "-t", f"{count * avg:.1f}", "-c", "copy", out_path]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=max(300, int(count * avg * 3)))
        if r.returncode != 0 or not (os.path.exists(out_path) and os.path.getsize(out_path) > 0):
            say(f"[LIVE] FFmpeg downloader failed too: {r.stderr[-120:]}")
            return None
        for m in re.finditer(r"Opening '([^']+)' for reading", r.stderr):   # which segment did it start at?
            num = re.search(r"/sq/(\d+)", m.group(1)) or re.search(r"_(\d+)\.(?:ts|m4s|mp4|aac)", m.group(1))
            if num and int(num.group(1)) >= have_first:
                return int(num.group(1))
        return start_seq
    except Exception as e:
        say(f"[LIVE] FFmpeg downloader error: {type(e).__name__}: {str(e)[:80]}")
        return None


def smart_rewind_jobs(info, window_seconds, wanted, clip_seconds, fspec, title, ua, vid, stamp):
    """
    Treat the last `window_seconds` as a full video:
      1. scan it (audio / lowest quality only - small and fast)
      2. pick the best moments
      3. download ONLY those moments in the best quality YouTube lets us have
         (direct download -> FFmpeg's downloader -> next lower quality)

    Returns jobs [{"rec", "m", "transcript", "owned"}] (empty list = nothing good found),
    or None if this stream can't be handled this way (caller falls back).
    """
    tmp = None
    wav = None
    try:
        variants = _hls_variants(info)
        if not variants:
            return None
        scan = _audio_variant(info) or variants[0]       # cheapest thing that has sound

        scan_pl = parse_media_playlist(scan["url"], ua)
        segs = scan_pl["segments"]
        if not segs:
            return None
        window, total = [], 0.0
        for g in reversed(segs):                          # the last `window_seconds` of history
            window.insert(0, g)
            total += g["dur"]
            if total >= window_seconds:
                break
        if total < MIN_USEFUL_SECONDS:
            return None
        if total < window_seconds - 10:
            say(f"[LIVE] Stream only keeps ~{total:.0f}s of history - scanning that")
        say(f"[LIVE] Scanning the last {total:.0f}s (small download) to find the best moments...")

        os.makedirs("downloads", exist_ok=True)
        tmp = tempfile.mkdtemp(prefix="jarvis_rew_")
        scan_file = os.path.join(tmp, "scan.mp4" if scan_pl["map"] else "scan.ts")
        t0 = time.time()
        _download_segments(window, scan_pl["map"], scan_file, ua, os.path.join(tmp, "scan_parts"))
        wav = f"downloads/live_{vid}_{stamp}_scan.wav"
        r = subprocess.run([_ffmpeg(), "-y", "-loglevel", "error", "-fflags", "+genpts", "-i", scan_file,
                            "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", wav],
                           capture_output=True, text=True, timeout=600)
        if r.returncode != 0 or not os.path.exists(wav):
            say(f"[LIVE] Could not read the scanned audio: {r.stderr[-150:]}")
            return None
        say(f"[LIVE] Scan ready in {time.time() - t0:.0f}s")

        moments = pick_moments(wav, title, wanted, clip_seconds, fspec["min_seconds"],
                               fspec["max_seconds"], fspec["label"])
        if not moments:
            return []

        from caption_generator import get_clip_transcript
        cum, t = [], 0.0
        for g in window:
            cum.append(t)
            t += g["dur"]
        base_seq, avg_dur = window[0]["seq"], total / len(window)

        def time_of_seq(q):                               # position of a segment on the scan timeline
            idx = q - base_seq
            return cum[idx] if 0 <= idx < len(cum) else idx * avg_dur

        # best quality first (<=720p), then step down; the scan variant is the known-good last rung
        ladder = sorted([v for v in variants if v["height"] <= 720], key=lambda v: -v["height"]) or variants
        if scan in variants and scan not in ladder:
            ladder.append(scan)

        def fetch_all(hv):
            hv_pl = scan_pl if hv["url"] == scan["url"] else parse_media_playlist(hv["url"], ua)
            by_seq = {g["seq"]: g for g in hv_pl["segments"]}
            made = []
            for n, m in enumerate(moments, 1):
                i0 = max(i for i in range(len(window)) if cum[i] <= m["start"] + 1e-6)
                i1 = min(len(window) - 1, max(i for i in range(len(window)) if cum[i] < m["end"] - 1e-6))
                seqs = [window[i]["seq"] for i in range(i0, i1 + 1)]
                span = sum(window[i]["dur"] for i in range(i0, i1 + 1))
                if any(q not in by_seq for q in seqs) or \
                        abs(sum(by_seq[q]["dur"] for q in seqs) - span) > 2.0:
                    say("[LIVE] Quality variants are not aligned for this stream")
                    for j in made:
                        _cleanup(j["rec"])
                    return None
                say(f"[LIVE] Downloading only moment {n}/{len(moments)} "
                    f"({span:.0f}s at {hv['height'] or 'best'}p)...")
                ext = ".mp4" if hv_pl["map"] else ".ts"
                raw = f"downloads/live_{vid}_{stamp}_m{n}{ext}"
                mkv = f"downloads/live_{vid}_{stamp}_m{n}.mkv"
                try:
                    _download_segments([by_seq[q] for q in seqs], hv_pl["map"], raw, ua,
                                       os.path.join(tmp, f"{hv['height']}p_m{n}"))
                    if _remux(raw, mkv):
                        os.remove(raw)
                        slice_path = mkv
                    else:
                        slice_path = raw
                    offset = m["start"] - cum[i0]
                except Exception as e:
                    say(f"[LIVE] Direct download blocked ({type(e).__name__}: {str(e)[:40]}) "
                        f"- trying FFmpeg's own downloader...")
                    _cleanup(raw)
                    real_first = _ffmpeg_fetch_slice(hv["url"], seqs[0], seqs[-1], mkv, ua)
                    if real_first is None:
                        _cleanup(mkv)
                        for j in made:
                            _cleanup(j["rec"])
                        return None
                    slice_path = mkv
                    offset = m["start"] - time_of_seq(real_first)
                offset = max(0.0, offset)
                made.append({"rec": slice_path, "owned": True,
                             "transcript": get_clip_transcript(wav, m["start"], m["end"]),
                             "m": dict(m, start=offset, end=offset + (m["end"] - m["start"]))})
            return made

        for k, hv in enumerate(ladder):
            jobs = fetch_all(hv)
            if jobs:
                if k:
                    say(f"[LIVE] Note: the sharper copies were blocked, so these clips are {hv['height']}p")
                return jobs
            if k + 1 < len(ladder):
                say(f"[LIVE] {hv['height']}p is blocked - trying {ladder[k + 1]['height']}p...")
        return None
    except Exception as e:
        say(f"[LIVE] Smart rewind unavailable ({type(e).__name__}: {str(e)[:100]}) - using the full-window fallback")
        return None
    finally:
        if wav:
            _cleanup(wav)
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)


# --------------------------------------------------------------------------
# 4. Find the best moments
# --------------------------------------------------------------------------
def _write_json3(words, path, max_words=9, pause=0.7):
    """Words with timestamps -> YouTube json3 subtitles (what clip_picker expects)."""
    events, cur = [], []

    def flush():
        if cur:
            t0, t1 = cur[0]["start"], cur[-1]["end"]
            events.append({"tStartMs": int(t0 * 1000), "dDurationMs": int(max(t1 - t0, 0.3) * 1000),
                           "segs": [{"utf8": " ".join(w["word"] for w in cur)}]})
            cur.clear()

    for i, w in enumerate(words):
        cur.append(w)
        gap = (words[i + 1]["start"] - w["end"]) if i + 1 < len(words) else 99
        if len(cur) >= max_words or gap > pause or w["word"][-1:] in ".?!":
            flush()
    flush()
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"events": events}, f)
    return bool(events)


def _loudest_windows(recording, n, clip_seconds, duration):
    """Fallback picker: the n loudest, non-overlapping windows (crowd / streamer reactions)."""
    tmp = tempfile.mkdtemp(prefix="jarvis_live_")
    try:
        wav_path = os.path.join(tmp, "a.wav")
        r = subprocess.run([_ffmpeg(), "-y", "-loglevel", "error", "-i", recording, "-vn", "-ac", "1",
                            "-ar", "8000", "-c:a", "pcm_s16le", wav_path],
                           capture_output=True, text=True, timeout=300)
        if r.returncode != 0 or not os.path.exists(wav_path):
            return []
        with wave.open(wav_path, "rb") as w:
            rate = w.getframerate()
            samples = array.array("h")
            samples.frombytes(w.readframes(w.getnframes()))
        per_sec = []
        for s in range(0, len(samples) - rate + 1, rate):
            chunk = samples[s:s + rate]
            per_sec.append(sum(x * x for x in chunk) / max(len(chunk), 1))
        win = int(clip_seconds)
        if len(per_sec) < win:
            return []
        prefix = [0.0]
        for v in per_sec:
            prefix.append(prefix[-1] + v)
        cands = sorted(((prefix[i + win] - prefix[i], i) for i in range(len(per_sec) - win + 1)), reverse=True)
        picks = []
        for score, start in cands:
            if all(abs(start - p["start"]) >= win for p in picks):
                picks.append({"start": float(start), "end": float(start + win), "score": round(score, 1),
                              "reason": "Loudest moment (big reaction or hype)", "hook_text": ""})
            if len(picks) >= n:
                break
        return picks
    except Exception as e:
        say(f"[LIVE] Loudness analysis failed: {type(e).__name__}: {e}")
        return []
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def pick_moments(recording, title, n, clip_seconds, min_len=20, max_len=45, kind="YouTube Shorts"):
    """Best n moments in the recording: transcript + AI first, loudness as the safety net."""
    duration = _duration(recording)
    if duration < clip_seconds:
        return [{"start": 0.0, "end": duration, "score": 0, "reason": "Recent moment", "hook_text": ""}] \
            if duration >= MIN_USEFUL_SECONDS else []
    moments = []
    try:
        from caption_burner import transcribe_words
        words = transcribe_words(recording)
        if words:
            base = os.path.splitext(recording)[0]
            if _write_json3(words, base + ".en.json3"):
                from clip_picker import pick_viral_moments
                moments = pick_viral_moments({"title": title}, recording, duration, n, clip_seconds,
                                             min_len=min_len, max_len=max_len, kind=kind)
    except ImportError as e:
        say("[LIVE] Your clip_picker.py is out of date (no pick_viral_moments) - copy the newest "
            f"clip_picker.py into your JARVIS folder to get AI-picked moments. ({str(e)[:60]})")
    except Exception as e:
        say(f"[LIVE] Smart picking failed ({type(e).__name__}: {str(e)[:100]})")
    if not moments:
        say("[LIVE] Using loudest-moment picking")
        moments = _loudest_windows(recording, n, clip_seconds, duration)
    return moments[:n]


# --------------------------------------------------------------------------
# 5. Main entry point
# --------------------------------------------------------------------------
def clip_live_stream(url, num_clips=2, clip_seconds=None, rewind_minutes=5, watch_minutes=0,
                     chunk_minutes=5, upload=True, privacy_status="public", niche="entertainment",
                     manage_job_status=True, video_format=None, video_minutes=None):
    """
    Clip a live YouTube stream.

    num_clips       clips to make from the time window you give
    clip_seconds    target length of each clip (default: 30s for Shorts, 3 min for proper videos)
    video_format    "short" (vertical Short) | "video" (proper horizontal video) | None = settings default
    video_minutes   length of each proper video in minutes (ignored for Shorts)
    rewind_minutes  the window to look through, counted back from now (0 = skip)   max 10
    watch_minutes   then keep watching this long for new moments (0 = don't)
    chunk_minutes   while watching, make 1 clip from every chunk of this size      max 10

    Returns list of YouTube video IDs (or file paths if upload=False).
    """
    import job_status
    from video_clipper import create_video_clip
    from caption_generator import generate_caption, get_clip_transcript
    from video_format import resolve, spec as format_spec

    fmt = resolve(video_format)
    is_short = fmt == "short"
    if not is_short and video_minutes and float(video_minutes) > MAX_BUFFER_MINUTES / 1.15:
        video_minutes = MAX_BUFFER_MINUTES / 1.15
        say(f"[LIVE] A live scan covers at most {MAX_BUFFER_MINUTES} minutes, so the video will be "
            f"about {int(video_minutes)} minutes.")
    fspec = format_spec(fmt, video_minutes)
    clip_seconds = clip_seconds or fspec["clip_seconds"]

    rewind_minutes = max(0, min(int(rewind_minutes), MAX_BUFFER_MINUTES))
    chunk_minutes = max(1, min(int(chunk_minutes), MAX_BUFFER_MINUTES))
    if not is_short:   # the whole video has to fit inside the time window that is scanned
        need = min(MAX_BUFFER_MINUTES, math.ceil(fspec["max_seconds"] / 60))
        if rewind_minutes:
            rewind_minutes = max(rewind_minutes, need)
        chunk_minutes = max(chunk_minutes, need)
    watch_minutes = max(0, int(watch_minutes))
    num_clips = max(1, int(num_clips))

    rounds = []  # (label, record_seconds, rewind_seconds, clips_wanted)
    if rewind_minutes:
        rounds.append(("rewind", rewind_minutes * 60, rewind_minutes * 60, num_clips))
    left = watch_minutes
    while left > 0:
        m = min(chunk_minutes, left)
        rounds.append(("watch", m * 60, 0, 1))
        left -= m
    if not rounds:
        rounds.append(("rewind", 3 * 60, 3 * 60, num_clips))
    total = sum(r[3] for r in rounds)

    _check_installation()
    say("[LIVE] Checking the stream...")
    try:
        info = probe_stream(url)
    except Exception as e:
        say(f"[LIVE] Could not open that link: {type(e).__name__}: {str(e)[:120]}")
        return []
    if not _is_live_info(info):
        say("[LIVE] That video is not live right now.")
        return []

    title = info.get("title") or "Live stream"
    channel = info.get("channel") or info.get("uploader") or "the streamer"
    description = info.get("description") or ""
    vid = info.get("id") or "live"
    say(f"[LIVE] LIVE: {title} - {channel}")

    started_here = False
    if manage_job_status and not job_status.is_running():
        job_status.start(total, url)
        started_here = True
    job_status.step(f"Clipping live stream: {title[:60]}")

    try:
        info, inputs, headers = resolve_stream(url, first_info=info)
    except Exception as e:
        say(f"[LIVE] {e}")
        if started_here:
            job_status.finish([], error=str(e))
        return []
    ua = (headers or {}).get("User-Agent") or DEFAULT_UA

    uploader = None
    if upload:
        try:
            from youtube_uploader import YouTubeUploader
            uploader = YouTubeUploader()
            if not uploader.youtube:
                uploader = None
        except Exception as e:
            say(f"[LIVE] YouTube uploader unavailable: {e}")
    if upload and not uploader:
        say("[LIVE] Not signed in to YouTube - clips will be saved locally instead")

    os.makedirs("downloads", exist_ok=True)
    os.makedirs("clips", exist_ok=True)
    results, slot = [], 0

    def _process(job, slot_no):
        """Turn one moment into a Short / video, caption it, upload to YouTube (+ Instagram)."""
        m, recording = job["m"], job["rec"]
        lo, hi = (15, 60) if is_short else (30, fspec["max_seconds"])
        clip_len = max(lo, min(hi, round(m["end"] - m["start"])))
        say(f"[LIVE] Clip {slot_no}/{total}: {m.get('reason', '')}")
        job_status.clip(slot_no, status="cutting", start=m["start"], reason=m.get("reason", ""),
                        detail="Creating vertical Short" if is_short else "Creating video")
        clip_path = None
        try:
            clip_path = create_video_clip(input_video=recording, start_time=m["start"],
                                          duration=clip_len, vertical=is_short)
            if clip_path and os.path.exists(clip_path):
                job_status.clip(slot_no, status="captioning", detail="Burning in captions")
                from caption_burner import add_captions
                clip_path = add_captions(clip_path)
        except Exception as e:
            say(f"[LIVE] Clip {slot_no} failed: {type(e).__name__}: {e}")
            return
        if not (clip_path and os.path.exists(clip_path)):
            say(f"[LIVE] Clip {slot_no} was not created")
            return

        if not (upload and uploader):
            results.append(clip_path)
            job_status.clip(slot_no, status="saved", detail="Saved locally")
            say(f"[LIVE] Saved locally: {clip_path}")
            return

        try:
            transcript = job["transcript"] if job.get("transcript") is not None \
                else get_clip_transcript(recording, m["start"], m["end"])
            cap = generate_caption(title, description, channel, url, transcript, slot_no,
                                   moment_note=m.get("reason", ""), niche=niche, video_format=fmt)
            job_status.clip(slot_no, status="uploading", title=cap.get("title", ""),
                            detail="Uploading to YouTube")
            video_id = uploader.upload_video(
                video_file=clip_path, title=cap["title"], description=cap["description"],
                tags=cap["tags"], category=cap.get("category_id", "24"),
                privacy_status=privacy_status, pinned_comment=cap.get("pinned_comment"),
                video_format=fmt)
            if not video_id:
                say(f"[LIVE] Upload failed - clip kept at {clip_path}")
                return
            results.append(video_id)
            link = (f"https://www.youtube.com/shorts/{video_id}" if is_short
                    else f"https://www.youtube.com/watch?v={video_id}")
            job_status.clip(slot_no, status="done", id=video_id, url=link)
            say(f"[LIVE] Uploaded: {link}")

            if is_short:    # no Instagram login: save a captioned copy to post by hand
                from instagram_export import save_for_instagram
                save_for_instagram(clip_path, cap["title"], cap["description"], fmt)
            _cleanup(clip_path)
        except Exception as e:
            say(f"[LIVE] Upload error ({type(e).__name__}): {e}. Clip kept at {clip_path}")

    for r_idx, (label, rec_seconds, rewind, wanted) in enumerate(rounds, 1):
        if _cancelled():
            break
        job_status.step(f"Live round {r_idx}/{len(rounds)}: "
                        f"{'scanning the last ' + str(rec_seconds // 60) + ' min' if label == 'rewind' else 'watching for new moments'}")
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Stream URLs can expire during a long watch session - refresh after the first round
        if r_idx > 1:
            try:
                info, inputs, headers = resolve_stream(url)
            except Exception:
                say("[LIVE] Stream is no longer available - stopping")
                break

        jobs = None
        if label == "rewind":
            # Smart path: scan the window cheaply -> download ONLY the best slices
            jobs = smart_rewind_jobs(info, rec_seconds, wanted, clip_seconds, fspec, title, ua, vid, stamp)
            if jobs is not None and not jobs:
                say("[LIVE] No good moments found in that time window")
                continue

        shared = None
        if jobs is None:
            # Fallback / watch rounds: get the whole footage, then pick moments inside it
            shared = f"downloads/live_{vid}_{stamp}.mkv"
            got = record_live(inputs, shared, rec_seconds, rewind_seconds=rewind, ua=ua)
            if got < MIN_USEFUL_SECONDS:
                say("[LIVE] Not enough footage (stream may have ended)")
                _cleanup(shared)
                break
            say(f"[LIVE] Got {got:.0f}s - looking for the best moments...")
            moments = pick_moments(shared, title, wanted, clip_seconds, fspec["min_seconds"],
                                   fspec["max_seconds"], fspec["label"])
            if not moments:
                say("[LIVE] No good moments found in this footage")
                _cleanup(shared)
                continue
            jobs = [{"rec": shared, "m": m, "transcript": None, "owned": False} for m in moments]

        for job in jobs:
            slot += 1
            if _cancelled():
                break
            try:
                _process(job, slot)
            finally:
                if job.get("owned"):
                    _cleanup(job["rec"])           # the downloaded slice is no longer needed
        if shared:
            _cleanup(shared)

    if started_here:
        job_status.finish(results if upload else [])
    return results


def _check_installation():
    """Tell the user exactly which files are out of date (they get copied one by one)."""
    import inspect
    old = []
    checks = [("clip_picker.py", "clip_picker", "pick_viral_moments", "min_len"),
              ("caption_generator.py", "caption_generator", "generate_caption", "video_format"),
              ("youtube_uploader.py", "youtube_uploader", "YouTubeUploader.upload_video", "video_format"),
              ("video_clipper.py", "video_clipper", "create_video_clip", "vertical")]
    for filename, module, attr, param in checks:
        try:
            obj = importlib.import_module(module)
            for part in attr.split("."):
                obj = getattr(obj, part)
            if param not in inspect.signature(obj).parameters:
                old.append(filename)
        except ModuleNotFoundError as e:
            if e.name == module:          # the JARVIS file itself is missing
                old.append(filename)      # (a missing third-party library is not our business here)
        except Exception:
            old.append(filename)
    try:
        importlib.import_module("video_format")
    except Exception:
        old.append("video_format.py")
    if old:
        say("[LIVE] These files look out of date - copy the newest versions into your JARVIS folder: "
            + ", ".join(sorted(set(old))))


def _cleanup(path):
    """Delete a recording / clip and its subtitle sidecar."""
    for p in [path] + glob.glob(glob.escape(os.path.splitext(path)[0]) + ".en*.json3"):
        try:
            if os.path.exists(p):
                os.remove(p)
        except OSError:
            pass


if __name__ == "__main__":
    import sys
    target = extract_youtube_url(" ".join(sys.argv[1:])) if len(sys.argv) > 1 else None
    if not target:
        print("usage: python live_clipper.py <youtube live link> [num_clips] [rewind_minutes] [watch_minutes]")
        sys.exit(1)
    args = [int(a) for a in sys.argv[2:5] if a.isdigit()]
    clip_live_stream(target, *(args[:1] or [2]),
                     rewind_minutes=(args[1] if len(args) > 1 else 5),
                     watch_minutes=(args[2] if len(args) > 2 else 0))