"""
Caption Generator
Builds a title, description and tags for each Short, based on what the clip
is actually about (source video title/description + the spoken words in the
clip's time window when subtitles are available).
"""

from job_status import say
import glob
import json
import os
import re
from dotenv import load_dotenv

load_dotenv()

GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
MAX_TITLE = 60
CORE_HASHTAGS = ["shorts", "youtubeshorts", "viral", "trending"]
CATEGORY_BY_NICHE = {
    "gaming": "20",
    "entertainment": "24",
    "music": "10",
    "science": "28",
    "technology": "28",
}


# --------------------------------------------------------------------------
# Transcript for the clip window
# --------------------------------------------------------------------------
def find_subtitle_file(video_file):
    """yt-dlp saves subs next to the video as <name>.<lang>.json3"""
    base = os.path.splitext(video_file)[0]
    matches = glob.glob(glob.escape(base) + ".en*.json3")
    return matches[0] if matches else None


def get_clip_transcript(video_file, start, end, max_chars=1500):
    """Return the words spoken between start and end (seconds), or ''."""
    path = find_subtitle_file(video_file)
    if not path:
        return ""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        parts = []
        for ev in data.get("events", []):
            t0 = ev.get("tStartMs", 0) / 1000.0
            t1 = t0 + ev.get("dDurationMs", 0) / 1000.0
            if t1 < start or t0 > end:
                continue
            text = "".join(s.get("utf8", "") for s in ev.get("segs", []) or [])
            text = text.replace("\n", " ").strip()
            if text:
                parts.append(text)
        return re.sub(r"\s+", " ", " ".join(parts)).strip()[:max_chars]
    except Exception as e:
        say(f"[CAPTIONS] Could not read subtitles: {e}")
        return ""


# --------------------------------------------------------------------------
# Groq call
# --------------------------------------------------------------------------
def _groq_key():
    key = os.getenv("GROQ_API_KEY")
    if key:
        return key
    try:
        with open("credentials.json", "r", encoding="utf-8-sig") as f:
            return json.load(f).get("groq_api_key", "")
    except Exception:
        return ""


def _ask_groq(prompt):
    from groq import Groq

    client = Groq(api_key=_groq_key())
    kwargs = dict(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000,
    )
    try:
        resp = client.chat.completions.create(
            extra_body={"reasoning_effort": "low"}, **kwargs
        )
    except TypeError:
        resp = client.chat.completions.create(**kwargs)
    return resp.choices[0].message.content or ""


def _parse_json(text):
    text = re.sub(r"```(?:json)?", "", text).strip()
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0)) if m else {}


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------
def _clean_tag(t):
    return re.sub(r"[^a-z0-9]", "", str(t).lower().lstrip("#"))


def _fallback(source_title, clip_number):
    words = [_clean_tag(w) for w in re.findall(r"[A-Za-z0-9]+", source_title)]
    words = [w for w in words if len(w) > 3][:4]
    return {
        "title": f"{source_title[:70].strip()} (Part {clip_number})",
        "titles": [f"{source_title[:55].strip()} (Part {clip_number})"],
        "hook": "Watch this moment from the video!",
        "hashtags": words,
        "pinned_comment": "What did you think about this moment?",
    }


def _pick_title(titles, source_title):
    """Prefer short, specific titles without inventing claims."""
    candidates = []
    for title in titles:
        clean = re.sub(r"[#\r\n]", "", str(title)).strip()
        if clean:
            candidates.append(clean[:MAX_TITLE])
    if not candidates:
        return source_title[:MAX_TITLE].strip()
    return max(candidates, key=lambda value: (
        len(value) <= 55,
        len(value.split()) >= 4,
        len(value),
    ))


def generate_caption(source_title, source_description, channel, source_url,
                     transcript, clip_number, moment_note="", niche="entertainment"):
    """
    Returns dict: title, description, tags  (ready for uploader.upload_video)
    """
    prompt = f"""You write titles and descriptions for YouTube Shorts clips.

SOURCE VIDEO TITLE: {source_title}
SOURCE CHANNEL: {channel}
SOURCE DESCRIPTION (may be long): {(source_description or '')[:600]}
WORDS SPOKEN IN THIS CLIP: {transcript or '(not available)'}
CLIP NUMBER: {clip_number}
WHY THIS MOMENT WAS PICKED: {moment_note or '(not available)'}

Write a scroll-stopping Shorts title and caption for THIS clip.
Rules:
- The title must accurately reflect what is in the clip. Do not invent events,
  quotes or claims. Curiosity and emotion are good; lying is not.
- Title candidates: write exactly 5 options, each under 60 characters, specific
    to the clip, strong hook, 1 emoji at most, and no hashtags. Never invent
    events, quotes, people or claims.
- hook: 1-2 punchy sentences for the description that tease the clip.
- hashtags: exactly 1 to 3 specific lowercase hashtags (no # symbol, no
    spaces) about the clip's topic or the person speaking. Do not use generic
    tags such as shorts, viral or trending; those are added automatically.
- pinned_comment: one natural question that invites replies without bait.

Reply with ONLY valid JSON, no other text:
{{"titles": ["...", "...", "...", "...", "..."], "best_index": 1,
"hook": "...", "hashtags": ["...", "..."], "pinned_comment": "..."}}"""

    try:
        data = _parse_json(_ask_groq(prompt))
        if not (data.get("titles") or data.get("title")):
            raise ValueError("model returned no title")
    except Exception as e:
        say(f"[CAPTIONS] AI caption failed ({type(e).__name__}: {e}), using fallback")
        data = _fallback(source_title, clip_number)

    titles = data.get("titles") or ([data["title"]] if data.get("title") else [])

    tags = list(CORE_HASHTAGS)
    for t in data.get("hashtags", []):
        t = _clean_tag(t)
        if t and t not in tags and len(tags) < len(CORE_HASHTAGS) + 3:
            tags.append(t)

    base_title = _pick_title(titles, source_title)
    title = base_title
    if len(base_title) + len(" #Shorts") <= MAX_TITLE:
        title = f"{base_title} #Shorts"
    title = title[:MAX_TITLE]

    hashtag_line = " ".join("#" + t for t in tags[:10])
    credit = f'Clip from "{source_title}" by {channel}\nOriginal video: {source_url}'
    description = f"{data.get('hook', '').strip()}\n\n{credit}\n\n{hashtag_line}".strip()

    return {
        "title": title,
        "title_candidates": titles[:5],
        "description": description,
        "tags": tags[:15],
        "pinned_comment": str(data.get("pinned_comment", "What did you think?"))[:500],
        "category_id": CATEGORY_BY_NICHE.get(str(niche).lower(), "24"),
    }