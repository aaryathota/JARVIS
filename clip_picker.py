"""
Clip Picker - finds the most engaging moments of a video.

Signals used (whatever is available for the video):
  1. YouTube's "Most replayed" heatmap (info["heatmap"]) - real viewer data
  2. The transcript (English subtitles) - scored for energy/reactions
  3. The AI (Groq) reads the best candidates and ranks them

If nothing is available, it returns [] and the caller falls back to random clips.
"""

from job_status import say
import bisect
import json
import os
import re

from caption_generator import _ask_groq, _parse_json, find_subtitle_file

STEP = 10  # seconds between candidate window starts

# Words/phrases that usually show up at big moments in reaction-style content
KEYWORDS = [
    "oh my god", "no way", "what the", "wait", "holy", "insane", "crazy",
    "unbelievable", "are you serious", "i can't", "scream", "shut up",
    "let's go", "hold on", "bro", "dude", "what happened", "look at",
    "secret", "mistake", "never", "worst", "best", "the truth", "actually",
]
REACTION_TAGS = ["[laughter]", "[applause]", "[cheering]", "[screaming]", "[gasps]"]
REJECT_TERMS = ("sponsor", "sponsored by", "welcome back", "subscribe", "intro", "outro")


# --------------------------------------------------------------------------
# Loading data
# --------------------------------------------------------------------------
def load_segments(subtitle_anchor):
    """Return a sorted list of (start, end, text) from the json3 subtitles."""
    path = find_subtitle_file(subtitle_anchor)
    if not path:
        return _transcribe_locally(subtitle_anchor)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        say(f"[PICKER] Could not read subtitles: {e}")
        return []
    segs = []
    for ev in data.get("events", []):
        t0 = ev.get("tStartMs", 0) / 1000.0
        t1 = t0 + ev.get("dDurationMs", 0) / 1000.0
        text = "".join(s.get("utf8", "") for s in ev.get("segs", []) or [])
        text = re.sub(r"\s+", " ", text.replace("\n", " ")).strip()
        if text:
            segs.append((t0, t1, text))
    segs.sort(key=lambda s: s[0])
    return segs


def _transcribe_locally(video_path):
    """Use faster-whisper only when installed; subtitle parsing remains the default."""
    if not video_path or not os.path.isfile(video_path):
        return []
    try:
        import importlib
        WhisperModel = importlib.import_module("faster_whisper").WhisperModel
    except ImportError:
        say("[PICKER] faster-whisper is not installed; continuing without local transcription")
        return []
    try:
        model_name = os.getenv("WHISPER_MODEL", "small")
        model = WhisperModel(model_name, device=os.getenv("WHISPER_DEVICE", "cpu"),
                             compute_type=os.getenv("WHISPER_COMPUTE_TYPE", "int8"))
        segments, _ = model.transcribe(video_path, word_timestamps=True)
        return [(float(segment.start), float(segment.end), segment.text.strip())
                for segment in segments if segment.text.strip()]
    except Exception as error:
        say(f"[PICKER] Local transcription unavailable: {type(error).__name__}: {error}")
        return []


def _heat_lookup(heatmap):
    """Return f(t) -> 0..1 'most replayed' strength, or None if no heatmap."""
    if not heatmap:
        return None
    try:
        bins = sorted(
            (float(b["start_time"]), float(b["end_time"]), float(b["value"]))
            for b in heatmap
        )
    except Exception:
        return None
    starts = [b[0] for b in bins]
    top = max(b[2] for b in bins) or 1.0

    def heat(t):
        i = bisect.bisect_right(starts, t) - 1
        if i < 0 or i >= len(bins):
            return 0.0
        return bins[i][2] / top

    return heat


# --------------------------------------------------------------------------
# Scoring
# --------------------------------------------------------------------------
def _window_text(segments, starts, t0, t1):
    i = max(bisect.bisect_left(starts, t0) - 1, 0)
    out = []
    while i < len(segments) and segments[i][0] < t1:
        if segments[i][1] >= t0:
            out.append(segments[i][2])
        i += 1
    return " ".join(out)


def _heuristic(text, clip_duration, heat_value):
    low = text.lower()
    words = len(low.split())
    score = min(words / clip_duration / 2.5, 1.5)  # speech density
    score += min(sum(low.count(k) for k in KEYWORDS), 40) * 0.1
    score += min(sum(low.count(t) for t in REACTION_TAGS), 12) * 0.2
    if words < 10:  # silence / music only
        score -= 1.0
    score += 2.0 * heat_value
    if any(term in low for term in REJECT_TERMS):
        score -= 2.0
    return score


def _spaced_top(cands, k, min_gap):
    """Highest-scoring candidates at least min_gap seconds apart (so picks are different moments)."""
    chosen = []
    for c in sorted(cands, key=lambda c: c["score"], reverse=True):
        if all(abs(c["start"] - o["start"]) >= min_gap for o in chosen):
            chosen.append(c)
        if len(chosen) >= k:
            break
    return chosen


def _snap_to_sentence(start, segments, duration, clip_duration, window=6.0):
    """Start the clip where a caption line starts, so it doesn't open mid-word."""
    best, gap = start, window
    for t0, _, _ in segments:
        if abs(t0 - start) < gap:
            best, gap = t0, abs(t0 - start)
    return max(0.0, min(best, max(duration - clip_duration, 0.0)))


# --------------------------------------------------------------------------
# AI ranking
# --------------------------------------------------------------------------
def _ai_rank(candidates, n, source_title):
    lines = []
    for idx, c in enumerate(candidates, 1):
        lines.append(f'[{idx}] {int(c["start"])}s: {c["text"][:450]}')
    prompt = f"""You pick the most viral 30-second moments from a long YouTube video
to turn into YouTube Shorts.

VIDEO TITLE: {source_title}

Candidate moments (id, start time, what is said):
{chr(10).join(lines)}

Choose the {n} best moments. Good Shorts have: an immediate hook, a surprise,
a funny or emotional reaction, a strong opinion, a punchline or payoff, and make
sense without the rest of the video. Skip intros, outros, sponsor reads, filler
talk and moments that need earlier context.

Reply with ONLY valid JSON:
{{"picks":[{{"id":1,"start":12,"end":42,"hook_text":"...",
"score":9,"reason":"short reason"}}]}}
Use a 20-45 second range. Require a hook in the first 3 seconds, self-contained
context and a payoff. Skip intros, outros, sponsor reads and overlapping picks.
score is 1-10 viral potential. Best first."""
    data = _parse_json(_ask_groq(prompt))
    picks = []
    for p in data.get("picks", []):
        try:
            c = candidates[int(p["id"]) - 1]
        except Exception:
            continue
        if c not in [x["cand"] for x in picks]:
            start = max(float(p.get("start", c["start"])), c["start"])
            end = min(float(p.get("end", start + 30)), c["start"] + 45)
            if end - start < 20:
                end = start + 20
            picks.append({
                "cand": c,
                "start": start,
                "end": end,
                "hook_text": str(p.get("hook_text", "")),
                "score": p.get("score", 5),
                "reason": str(p.get("reason", "")),
            })
    return picks[:n]


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------
def pick_viral_moments(info, subtitle_anchor, duration, num_clips, clip_duration=30):
    """
    Returns up to num_clips dicts: {"start", "end", "score", "reason"} best first.
    May return fewer (or []) if there is not enough data - caller fills the rest.
    """
    segments = load_segments(subtitle_anchor)
    heat = _heat_lookup(info.get("heatmap"))
    seg_starts = [s[0] for s in segments]
    say(f"[PICKER] Signals: transcript={'yes' if segments else 'no'}, "
          f"most-replayed={'yes' if heat else 'no'}")

    if not segments and not heat:
        return []

    # ---- Heatmap only: take the most replayed spots ----
    if not segments:
        bins = [(float(b["start_time"]), float(b["end_time"]), float(b["value"]))
                for b in info["heatmap"]]
        top = max(b[2] for b in bins) or 1.0
        cands = []
        for s, e, v in bins:
            if v / top < 0.5:  # only genuine peaks count as "most replayed"
                continue
            centre = (s + e) / 2
            start = max(0.0, min(centre - clip_duration / 2, duration - clip_duration))
            cands.append({"start": start, "score": v})
        out = []
        for c in _spaced_top(cands, num_clips, clip_duration * 2):
            out.append({"start": c["start"], "end": c["start"] + clip_duration,
                        "score": round(c["score"] * 10, 1),
                        "reason": "One of the most replayed parts of the video"})
        return out

    # ---- Transcript (+ optional heatmap): score sliding windows ----
    cands = []
    t = 0.0
    while t + clip_duration <= duration + 0.001:
        text = _window_text(segments, seg_starts, t, t + clip_duration)
        h = heat(t + clip_duration / 2) if heat else 0.0
        cands.append({"start": t, "text": text, "score": _heuristic(text, clip_duration, h)})
        t += STEP
    if not cands:
        return []

    shortlist = _spaced_top(cands, min(max(num_clips * 4, 10), 15), clip_duration * 2)

    ranked = None
    try:
        ranked = _ai_rank(shortlist, num_clips, info.get("title", ""))
        if not ranked:
            raise ValueError("AI returned no usable picks")
    except Exception as e:
        say(f"[PICKER] AI ranking failed ({type(e).__name__}: {e}) - using energy score only")

    if ranked is None:
        ranked = [{"cand": c, "score": round(c["score"], 1),
                   "reason": "High-energy moment (speech, reactions, replays)"}
                  for c in shortlist[:num_clips]]

    out = []
    for r in ranked:
        requested_start = r.get("start", r["cand"]["start"])
        requested_end = r.get("end", requested_start + clip_duration)
        requested_duration = max(20.0, min(45.0, requested_end - requested_start))
        start = _snap_to_sentence(requested_start, segments, duration, requested_duration)
        end = min(start + requested_duration, duration)
        if any(start < prior["end"] and end > prior["start"] for prior in out):
            continue
        out.append({"start": start, "end": end, "score": r["score"],
                    "reason": r["reason"], "hook_text": r.get("hook_text", "")})
    return out