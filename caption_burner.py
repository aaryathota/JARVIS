"""
Caption Burner - adds word-by-word "Shorts style" captions INTO the video.

Pipeline (100% free):
  1. Transcribe the finished clip with word timestamps
       a) Groq Whisper API (free tier, fast)  - used if a Groq key is present
       b) faster-whisper running locally       - fallback (already in requirements.txt)
  2. Build an ASS subtitle file (big bold text, current word highlighted)
  3. Burn it into the video with FFmpeg's libass filter

It NEVER raises: if anything fails the original clip is returned untouched,
so uploads keep working exactly as before.

Settings (settings.json, optional):
  "captions": {
      "enabled": true,
      "font": "Arial",          # font NAME installed on the system
      "font_size": 84,
      "highlight": "#FFE600",   # colour of the word being spoken
      "text_color": "#FFFFFF",
      "outline": 6,
      "uppercase": true,
      "words_per_line": 3,
      "margin_bottom": 620,     # px from bottom of the 1080x1920 frame
      "language": "en"
  }
"""

import json
import os
import shutil
import subprocess
import tempfile

from job_status import say

HERE = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(HERE, "settings.json")

DEFAULTS = {
    "enabled": True,
    "font": "Arial",
    "font_size": 84,
    "highlight": "#FFE600",
    "text_color": "#FFFFFF",
    "outline": 6,
    "uppercase": True,
    "words_per_line": 3,
    "margin_bottom": 620,
    "language": "en",
}


# --------------------------------------------------------------------------
# Settings helpers
# --------------------------------------------------------------------------
def _cfg():
    cfg = dict(DEFAULTS)
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            cfg.update(json.load(f).get("captions", {}))
    except (OSError, ValueError):
        pass
    return cfg


def _video_size(cfg_path_video=None):
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            v = json.load(f).get("video", {})
        return int(v.get("width", 1080)), int(v.get("height", 1920))
    except (OSError, ValueError):
        return 1080, 1920


def _probe_size(path):
    """(width, height) of the video file, or None."""
    try:
        from video_clipper import _tool
        r = subprocess.run([_tool("ffprobe"), "-v", "error", "-select_streams", "v:0",
                            "-show_entries", "stream=width,height", "-of", "csv=p=0:s=x", path],
                           capture_output=True, text=True, timeout=30)
        w, h = r.stdout.strip().split("x")[:2]
        return int(w), int(h)
    except Exception:
        return None


def _groq_key():
    key = os.getenv("GROQ_API_KEY")
    if key:
        return key
    try:
        with open(os.path.join(HERE, "credentials.json"), "r", encoding="utf-8-sig") as f:
            return json.load(f).get("groq_api_key", "")
    except Exception:
        return ""


# --------------------------------------------------------------------------
# 1. Transcription -> list of {"word", "start", "end"}
# --------------------------------------------------------------------------
def _extract_audio(video_path, out_wav):
    from video_clipper import _tool
    cmd = [_tool("ffmpeg"), "-y", "-i", video_path, "-vn", "-ac", "1",
           "-ar", "16000", "-c:a", "pcm_s16le", out_wav]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return r.returncode == 0 and os.path.exists(out_wav)


def _get(obj, name, default=None):
    return obj.get(name, default) if isinstance(obj, dict) else getattr(obj, name, default)


def _transcribe_groq(audio_path, language):
    key = _groq_key()
    if not key:
        return []
    from groq import Groq
    client = Groq(api_key=key)
    with open(audio_path, "rb") as f:
        resp = client.audio.transcriptions.create(
            file=(os.path.basename(audio_path), f.read()),
            model=os.getenv("GROQ_WHISPER_MODEL", "whisper-large-v3-turbo"),
            response_format="verbose_json",
            timestamp_granularities=["word"],
            language=language or None,
        )
    words = _get(resp, "words", []) or []
    return [{"word": str(_get(w, "word", "")).strip(),
             "start": float(_get(w, "start", 0)),
             "end": float(_get(w, "end", 0))} for w in words if str(_get(w, "word", "")).strip()]


def _transcribe_local(audio_path, language):
    from faster_whisper import WhisperModel  # optional dependency
    model = WhisperModel(os.getenv("WHISPER_MODEL", "base"),
                         device=os.getenv("WHISPER_DEVICE", "cpu"),
                         compute_type=os.getenv("WHISPER_COMPUTE_TYPE", "int8"))
    segments, _ = model.transcribe(audio_path, word_timestamps=True,
                                   vad_filter=True, language=language or None)
    out = []
    for seg in segments:
        for w in (seg.words or []):
            t = w.word.strip()
            if t:
                out.append({"word": t, "start": float(w.start), "end": float(w.end)})
    return out


def transcribe_words(video_path, language="en"):
    tmp = tempfile.mkdtemp(prefix="jarvis_cap_")
    try:
        wav = os.path.join(tmp, "audio.wav")
        if not _extract_audio(video_path, wav):
            say("[CAPTION BURN] Could not extract audio")
            return []
        for name, fn in (("Groq Whisper", _transcribe_groq),
                         ("local faster-whisper", _transcribe_local)):
            try:
                words = fn(wav, language)
                if words:
                    say(f"[CAPTION BURN] Transcribed {len(words)} words with {name}")
                    return words
            except ImportError:
                continue
            except Exception as e:
                say(f"[CAPTION BURN] {name} failed: {type(e).__name__}: {str(e)[:120]}")
        return []
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --------------------------------------------------------------------------
# 2. ASS subtitle file
# --------------------------------------------------------------------------
def _ass_time(t):
    t = max(t, 0)
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def _ass_color(hex_rgb):
    """'#RRGGBB' -> ASS '&HBBGGRR&'"""
    h = hex_rgb.lstrip("#")
    if len(h) != 6:
        h = "FFFFFF"
    return f"&H{h[4:6]}{h[2:4]}{h[0:2]}&"


def _escape(text):
    return text.replace("\\", "").replace("{", "(").replace("}", ")")


def _group(words, per_line):
    """Split words into short on-screen chunks, breaking on pauses/punctuation."""
    groups, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        gap = (words[i + 1]["start"] - w["end"]) if i + 1 < len(words) else 99
        ends_sentence = w["word"][-1:] in ".?!,"
        if len(cur) >= per_line or gap > 0.6 or (ends_sentence and len(cur) >= 2):
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)
    return groups


def build_ass(words, cfg, width=1080, height=1920):
    text_c = _ass_color(cfg["text_color"])
    hi_c = _ass_color(cfg["highlight"])
    size = int(cfg["font_size"])
    outline = int(cfg["outline"])
    margin_v = int(cfg["margin_bottom"])
    header = (
        "[Script Info]\nScriptType: v4.00+\n"
        f"PlayResX: {width}\nPlayResY: {height}\nWrapStyle: 2\nScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
        "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
        "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Default,{cfg['font']},{size},{text_c},{text_c},&H00000000&,&H64000000&,"
        f"-1,0,0,0,100,100,0,0,1,{outline},2,2,60,60,{margin_v},1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    events = []
    for group in _group(words, max(1, int(cfg["words_per_line"]))):
        for idx, w in enumerate(group):
            start = w["start"]
            # keep the line on screen until the next word starts (no flicker)
            if idx + 1 < len(group):
                end = group[idx + 1]["start"]
            else:
                end = max(w["end"], start + 0.25)
            parts = []
            for j, other in enumerate(group):
                t = _escape(other["word"])
                if cfg["uppercase"]:
                    t = t.upper()
                if j == idx:
                    parts.append(f"{{\\c{hi_c}\\fscx112\\fscy112}}{t}{{\\c{text_c}\\fscx100\\fscy100}}")
                else:
                    parts.append(t)
            events.append(
                f"Dialogue: 0,{_ass_time(start)},{_ass_time(end)},Default,,0,0,0,,{' '.join(parts)}"
            )
    return header + "\n".join(events) + "\n"


# --------------------------------------------------------------------------
# 3. Burn with FFmpeg
# --------------------------------------------------------------------------
def burn_ass(video_path, ass_text, out_path):
    from video_clipper import _tool, _encoder, _settings
    settings = _settings().get("video", {})
    encoders = [_encoder(settings)]
    if encoders[0] != "libx264":
        encoders.append("libx264")  # GPU encoder listed but unusable -> retry on CPU
    tmp = tempfile.mkdtemp(prefix="jarvis_ass_")
    try:
        with open(os.path.join(tmp, "captions.ass"), "w", encoding="utf-8") as f:
            f.write(ass_text)
        for encoder in encoders:
            # cwd trick: a bare filename in the filter avoids Windows "C:\" escaping hell
            cmd = [
                _tool("ffmpeg"), "-y", "-i", os.path.abspath(video_path),
                "-vf", "ass=captions.ass",
                "-c:v", encoder,
                "-preset", "p4" if encoder == "h264_nvenc" else settings.get("preset", "fast"),
                *(["-cq", str(settings.get("crf", 23))] if encoder == "h264_nvenc"
                  else ["-crf", str(settings.get("crf", 23))]),
                "-pix_fmt", "yuv420p",
                "-c:a", "copy",
                os.path.abspath(out_path),
            ]
            r = subprocess.run(cmd, cwd=tmp, capture_output=True, text=True, timeout=600)
            if r.returncode == 0 and os.path.exists(out_path) and os.path.getsize(out_path) > 0:
                return True
            say(f"[CAPTION BURN] {encoder} failed, trying next: {r.stderr[-200:]}")
        return False
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------
def add_captions(clip_path):
    """Return the path of the captioned clip (same path, replaced in place).
    On any failure, returns clip_path unchanged."""
    try:
        cfg = _cfg()
        if not cfg["enabled"]:
            return clip_path
        say("[CAPTION BURN] Adding on-screen captions...")
        words = transcribe_words(clip_path, cfg["language"])
        if not words:
            say("[CAPTION BURN] No speech found - keeping clip without captions")
            return clip_path
        w, h = _probe_size(clip_path) or _video_size()
        if w > h:  # horizontal (proper video): smaller text near the bottom, more words per line
            cfg = dict(cfg, font_size=round(h * 0.058), margin_bottom=round(h * 0.07),
                       outline=max(3, round(h * 0.005)), words_per_line=max(int(cfg["words_per_line"]), 5))
        ass = build_ass(words, cfg, w, h)
        tmp_out = os.path.splitext(clip_path)[0] + "_cap.mp4"
        if burn_ass(clip_path, ass, tmp_out):
            os.replace(tmp_out, clip_path)
            say("[CAPTION BURN] Captions burned in")
        else:
            if os.path.exists(tmp_out):
                os.remove(tmp_out)
    except Exception as e:
        say(f"[CAPTION BURN] Skipped: {type(e).__name__}: {e}")
    return clip_path


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        add_captions(sys.argv[1])
    else:
        print("usage: python caption_burner.py clips/some_clip.mp4")