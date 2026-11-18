"""
Live Clipper - turn an ONGOING YouTube live stream into Shorts.

Give it a live-stream link and it will:
  1. check the stream is really live (yt-dlp)
  2. REWIND into YouTube's DVR buffer and record the last few minutes
     (optionally keep WATCHING and record new chunks as the stream continues)
  3. find the best moments in what it recorded
        - transcript + AI ranking (your existing clip_picker)
        - falls back to "loudest moments" if there is no transcript
  4. render each moment as a vertical Short, burn in captions,
     write the title/description with AI, and upload to YouTube ONLY

Everything is free: yt-dlp + FFmpeg + Groq free tier (+ local Whisper fallback).

Public API
    extract_youtube_url(text)            -> url or None
    is_live_url(url)                     -> True / False  (never raises)
    clip_live_stream(url, ...)           -> list of YouTube video IDs
                                            (or clip file paths when upload=False)
"""

import array
import glob
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
import time
import wave
from datetime import datetime
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from job_status import say

MAX_BUFFER_MINUTES = 10   # transcription limit for one recording (keeps Groq uploads < 25 MB)
MIN_USEFUL_SECONDS = 15   # a recording shorter than this is treated as "stream ended"
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


# YouTube only hands out HLS (the format FFmpeg can rewind) to some "clients".
# Try the default first, then the ones that usually do.
_CLIENT_ATTEMPTS = [None, ["web_safari"], ["ios"], ["mweb"], ["tv"], ["android_vr"]]


def resolve_stream(url, first_info=None):
    """Find a rewindable HLS stream. Returns (info, [stream urls], headers).
    Tries several YouTube clients and explains exactly what came back if none works."""
    seen = []
    for clients in _CLIENT_ATTEMPTS:
        name = ",".join(clients) if clients else "default"
        try:
            info = first_info if (clients is None and first_info) else probe_stream(url, clients)
        except Exception as e:
            seen.append(f"{name}: {type(e).__name__}: {str(e)[:70]}")
            continue
        try:
            inputs, headers = _hls_inputs(info)
            if clients:
                say(f"[LIVE] Using the '{name}' YouTube client")
            return info, inputs, headers
        except RuntimeError:
            protos = sorted({(f.get("protocol") or "?") for f in info.get("formats", [])})
            seen.append(f"{name}: {len(info.get('formats', []))} formats, protocols={protos}")
    say("[LIVE] No rewindable (HLS) stream from any YouTube client -> " + " | ".join(seen))
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
# 2. Record
# --------------------------------------------------------------------------
def record_live(inputs, out_path, seconds, rewind_seconds=0, ua=DEFAULT_UA):
    """
    Record `seconds` of the live stream into out_path (mkv, stream copy).
    rewind_seconds > 0 starts that far BEHIND the live edge (DVR) - past media is
    fetched almost instantly, so a 5-minute rewind finishes in well under 5 minutes.
    Returns the number of seconds recorded.
    """
    back_segments = 1
    if rewind_seconds > 0:
        seg_dur, n_segs = _playlist_stats(inputs[0], ua)
        available = n_segs * seg_dur if n_segs else rewind_seconds
        requested = rewind_seconds
        rewind_seconds = min(rewind_seconds, available)
        back_segments = max(1, math.ceil(rewind_seconds / seg_dur))
        if seconds <= requested:  # rewind-only recording: don't wait for footage that doesn't exist yet
            seconds = rewind_seconds
        say(f"[LIVE] Rewinding ~{rewind_seconds:.0f}s ({back_segments} segments of {seg_dur:.1f}s)")

    cmd = [_ffmpeg(), "-y", "-loglevel", "error", "-user_agent", ua]
    for src in inputs:
        cmd += ["-live_start_index", str(-back_segments), "-i", src]
    if len(inputs) == 2:
        cmd += ["-map", "0:v:0", "-map", "1:a:0"]
    cmd += ["-t", str(int(seconds)), "-c", "copy", out_path]

    say(f"[LIVE] Recording {int(seconds)}s of the stream...")
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    deadline = time.time() + seconds + 90  # real-time recording + generous slack
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
    err = (proc.stderr.read() if proc.stderr else "")[-300:]
    if not (os.path.exists(out_path) and os.path.getsize(out_path) > 0):
        say(f"[LIVE] Recording failed: {err}")
        return 0.0
    return _duration(out_path)


# --------------------------------------------------------------------------
# 3. Find the best moments
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
    except Exception as e:
        say(f"[LIVE] Smart picking failed ({type(e).__name__}: {str(e)[:100]})")
    if not moments:
        say("[LIVE] Using loudest-moment picking")
        moments = _loudest_windows(recording, n, clip_seconds, duration)
    return moments[:n]


# --------------------------------------------------------------------------
# 4. Main entry point
# --------------------------------------------------------------------------
def clip_live_stream(url, num_clips=2, clip_seconds=None, rewind_minutes=5, watch_minutes=0,
                     chunk_minutes=5, upload=True, privacy_status="public", niche="entertainment",
                     manage_job_status=True, video_format=None):
    """
    Clip a live YouTube stream.

    num_clips       Shorts to make from the rewind recording
    clip_seconds    target length of each clip (default: 30s for Shorts, 3 min for proper videos)
    video_format    "short" (vertical Short) | "video" (proper horizontal video) | None = settings default
    rewind_minutes  how far back to look first (0 = skip)       max 10
    watch_minutes   then keep watching this long for new moments (0 = don't)
    chunk_minutes   while watching, make 1 Short from every chunk of this size   max 10

    Returns list of YouTube video IDs (or file paths if upload=False).
    """
    import job_status
    from video_clipper import create_video_clip
    from caption_generator import generate_caption, get_clip_transcript
    from video_format import resolve, spec as format_spec

    fmt = resolve(video_format)
    fspec = format_spec(fmt)
    is_short = fmt == "short"
    clip_seconds = clip_seconds or fspec["clip_seconds"]

    rewind_minutes = max(0, min(int(rewind_minutes), MAX_BUFFER_MINUTES))
    chunk_minutes = max(1, min(int(chunk_minutes), MAX_BUFFER_MINUTES))
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

    for r_idx, (label, rec_seconds, rewind, wanted) in enumerate(rounds, 1):
        if _cancelled():
            break
        job_status.step(f"Live round {r_idx}/{len(rounds)}: "
                        f"{'recording the last ' + str(rec_seconds // 60) + ' min' if label == 'rewind' else 'watching for new moments'}")
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        recording = f"downloads/live_{vid}_{stamp}.mkv"

        # Stream URLs can expire during a long watch session - refresh after the first round
        if r_idx > 1:
            try:
                _, inputs, headers = resolve_stream(url)
            except Exception:
                say("[LIVE] Stream is no longer available - stopping")
                break

        got = record_live(inputs, recording, rec_seconds, rewind_seconds=rewind, ua=ua)
        if got < MIN_USEFUL_SECONDS:
            say("[LIVE] Not enough footage recorded (stream may have ended)")
            _cleanup(recording)
            break
        say(f"[LIVE] Recorded {got:.0f}s - looking for the best moments...")

        moments = pick_moments(recording, title, wanted, clip_seconds, fspec["min_seconds"],
                               fspec["max_seconds"], fspec["label"])
        if not moments:
            say("[LIVE] No good moments found in this recording")
            _cleanup(recording)
            continue

        for m in moments:
            slot += 1
            if _cancelled():
                break
            lo, hi = (15, 60) if is_short else (30, fspec["max_seconds"])
            clip_len = max(lo, min(hi, round(m["end"] - m["start"])))
            say(f"[LIVE] Clip {slot}/{total}: {m['start']:.0f}s -> {m['end']:.0f}s - {m.get('reason', '')}")
            job_status.clip(slot, status="cutting", start=m["start"], reason=m.get("reason", ""),
                            detail="Creating vertical Short" if is_short else "Creating video")
            clip_path = None
            try:
                clip_path = create_video_clip(input_video=recording, start_time=m["start"],
                                              duration=clip_len, vertical=is_short)
                if clip_path and os.path.exists(clip_path):
                    job_status.clip(slot, status="captioning", detail="Burning in captions")
                    from caption_burner import add_captions
                    clip_path = add_captions(clip_path)
            except Exception as e:
                say(f"[LIVE] Clip {slot} failed: {type(e).__name__}: {e}")
                continue
            if not (clip_path and os.path.exists(clip_path)):
                say(f"[LIVE] Clip {slot} was not created")
                continue

            if not (upload and uploader):
                results.append(clip_path)
                job_status.clip(slot, status="saved", detail="Saved locally")
                say(f"[LIVE] Saved locally: {clip_path}")
                continue

            try:
                transcript = get_clip_transcript(recording, m["start"], m["end"])
                cap = generate_caption(title, description, channel, url, transcript, slot,
                                       moment_note=m.get("reason", ""), niche=niche, video_format=fmt)
                job_status.clip(slot, status="uploading", title=cap.get("title", ""),
                                detail="Uploading to YouTube")
                video_id = uploader.upload_video(
                    video_file=clip_path, title=cap["title"], description=cap["description"],
                    tags=cap["tags"], category=cap.get("category_id", "24"),
                    privacy_status=privacy_status, pinned_comment=cap.get("pinned_comment"),
                    video_format=fmt)
                if video_id:
                    results.append(video_id)
                    short_url = (f"https://www.youtube.com/shorts/{video_id}" if is_short
                                 else f"https://www.youtube.com/watch?v={video_id}")
                    job_status.clip(slot, status="done", id=video_id, url=short_url)
                    say(f"[LIVE] Uploaded: {short_url}")
                    _cleanup(clip_path)
                else:
                    say(f"[LIVE] Upload failed - clip kept at {clip_path}")
            except Exception as e:
                say(f"[LIVE] Upload error ({type(e).__name__}): {e}. Clip kept at {clip_path}")
        _cleanup(recording)

    if started_here:
        job_status.finish(results if upload else [])
    return results


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