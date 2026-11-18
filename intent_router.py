"""
Intent Router - uses AI (Groq, free tier) to understand what the user wants.

Instead of matching keywords, one small LLM call reads the command (plus the
last bit of conversation) and returns:

    {
      "intent":       one of INTENTS below,
      "target":       the topic / place / person the command is about ("" if none),
      "confidence":   0.0 - 1.0,
      "open_browser": True only if a web page genuinely helps (see rules),
      "quick_reply":  a short reply for greetings / thanks / small talk ("" otherwise),
      "source":       "ai" | "fast" | "cache"
    }

It NEVER raises. If the AI is unavailable the caller gets None and falls back
to the old keyword detector, so nothing that worked before stops working.

Env switches:
  INTENT_ROUTER=off     use the old keyword matcher only
  ROUTER_MODEL=<model>  preferred Groq model (default: gpt-oss-20b, then others your account has)
"""

import json
import os
import re
import threading
import time

from video_format import normalize as normalize_format

HERE = os.path.dirname(os.path.abspath(__file__))

# intent -> one-line description the model sees. Names match the handlers in main.py.
INTENTS = {
    "chat": "Greetings, thanks, small talk, opinions, simple questions or facts "
            "that a short spoken answer fully handles (definitions, quick how-things-work, math, yes/no).",
    "research": "A BIG question that deserves sources: in-depth research, comparisons, buying decisions, "
                "complex multi-step how-tos, current-events deep dives.",
    "open_website": "User explicitly asks to open / visit / search a website or look something up online.",
    "play_music": "Play a song, artist, playlist or music.",
    "weather": "Weather or temperature for a place. target = the place ('' for current location).",
    "news": "Read / show the news. target = topic ('general' if none).",
    "send_email": "Write or send an email.",
    "check_email": "Check / read the inbox.",
    "reminder": "Set a reminder or alarm.",
    "calendar": "Calendar events, meetings, scheduling.",
    "alerts": "Create or manage alerts / notifications.",
    "todo": "To-do list and tasks.",
    "expense": "Track expenses, spending, budget.",
    "memory_save": "Remember / save a fact or note for later.",
    "memory_recall": "Recall something the user told JARVIS earlier.",
    "decision": "User wants advice to make a decision.",
    "suggestions": "User wants ideas / tips / suggestions on a topic. target = the topic.",
    "make_suggestions": "User wants help making or building something. target = what to make.",
    "restaurant": "Find places to eat. target = cuisine ('' if none).",
    "directions": "Directions or navigation. target = destination.",
    "maps": "Open Google Earth / satellite maps.",
    "project_starter": "Start a new coding project. target = project name.",
    "website_builder": "Build a website or web app.",
    "developer": "Developer tools: debug, format or explain code, git, API tests.",
    "aiml": "Sentiment analysis, translation, spam check, image recognition.",
    "media": "Download / convert media, QR codes.",
    "communication": "SMS, WhatsApp, calls, social posts.",
    "entertainment": "Jokes on request, trivia, riddles, games, meditation.",
    "system": "Screenshots, screen recording, system info, backups, processes.",
    "system_stats": "CPU / memory / disk usage stats.",
    "workflow": "Create, list or run workflows / macros.",
    "events_summary": "Summary of what happened while the user was away.",
    "dashboard": "Open or show the JARVIS dashboard.",
    "daily_clips": "Run the daily YouTube Shorts clipping batch across permitted channels.",
    "channel_management": "Add / remove / enable / disable a clipping channel.",
    "youtube_shorts": "Make and upload YouTube clips from a normal (not live) YouTube video, either as "
                      "Shorts (vertical) or as proper long-form horizontal videos.",
    "clip_live": "Clip a LIVE / ongoing YouTube stream (user mentions a live stream, a stream that is on "
                 "right now, or gives a /live/ link) into Shorts.",
    "instagram_reels": "Make or upload Instagram Reels.",
    "stop_system": "User clearly wants to shut JARVIS down (exit, quit, goodbye, shut down). "
                   "NOT for 'close the door' or 'stop the music'.",
}

# Intents whose handler needs the user's full sentence as `target`
PASS_COMMAND = {
    "instagram_reels", "youtube_shorts", "clip_live", "memory_save", "decision", "todo", "calendar",
    "expense", "entertainment", "media", "developer", "aiml", "communication", "system",
    "website_builder", "system_stats", "workflow", "events_summary", "alerts", "dashboard",
    "daily_clips", "channel_management",
}
# Intents whose handler needs `target` to be the extracted topic / place
USE_TARGET = {"news", "weather", "suggestions", "make_suggestions", "directions", "restaurant",
              "project_starter"}
# Only these may ever ask for a browser tab
BROWSER_INTENTS = {"research", "open_website", "suggestions", "make_suggestions"}  # "chat" = spoken answer is enough

CONFIDENCE_FLOOR = 0.55
STOP_CONFIDENCE = 0.9  # shutting down needs near-certainty

# Zero-cost replies for pure social messages (no AI call, never opens a browser)
_QUICK = {
    ("hi", "hello", "hey", "hey jarvis", "hi jarvis", "hello jarvis", "yo", "sup"):
        "Hello! How can I help you today?",
    ("thanks", "thank you", "thank you jarvis", "thanks jarvis", "thanks a lot", "thank you so much",
     "thx", "ty", "cheers"):
        "You're welcome. Always happy to help.",
    ("good morning", "good morning jarvis"): "Good morning! What can I do for you?",
    ("good afternoon", "good afternoon jarvis"): "Good afternoon! What can I do for you?",
    ("good evening", "good evening jarvis"): "Good evening! What can I do for you?",
    ("good night", "good night jarvis"): "Good night. Rest well.",
    ("how are you", "how are you jarvis", "how are you doing"):
        "I'm doing great! Ready to help you with anything.",
    ("ok", "okay", "cool", "nice", "great", "awesome", "alright", "got it"): "Got it.",
    ("sorry", "my bad"): "No problem, it happens.",
}
_QUICK_LOOKUP = {phrase: reply for phrases, reply in _QUICK.items() for phrase in phrases}

_cache = {}
_cache_lock = threading.Lock()
_CACHE_MAX = 200


def enabled():
    return os.getenv("INTENT_ROUTER", "on").strip().lower() not in {"off", "0", "false", "no"}


def _norm(command):
    return re.sub(r"[^a-z0-9 ]+", "", command.lower()).strip()


def _groq_key():
    key = os.getenv("GROQ_API_KEY", "").strip()
    if key:
        return key
    try:
        with open(os.path.join(HERE, "credentials.json"), "r", encoding="utf-8-sig") as f:
            return json.load(f).get("groq_api_key", "").strip()
    except Exception:
        return ""


def _recent_context():
    """Last couple of exchanges so 'yes do it' / 'play that' make sense."""
    try:
        from conversation_memory import get_memory
        mem = get_memory()
        hist = getattr(mem, "conversation_history", None) or getattr(mem, "history", None) or []
        lines = []
        for ex in list(hist)[-2:]:
            if isinstance(ex, dict):
                u = str(ex.get("user") or ex.get("user_input") or "")[:120]
                a = str(ex.get("assistant") or ex.get("ai_response") or ex.get("response") or "")[:160]
                if u:
                    lines.append(f"User: {u}\nJARVIS: {a}")
        return "\n".join(lines)
    except Exception:
        return ""


def _build_prompt(command, context):
    catalog = "\n".join(f'- "{k}": {v}' for k, v in INTENTS.items())
    recent = f"RECENT CONVERSATION:\n{context}\n" if context else ""
    return f"""You are the intent router of JARVIS, a voice assistant. Work out what the user MEANS
(not which words they used) and reply with ONLY one JSON object.

INTENTS:
{catalog}

JSON fields:
  "intent": one intent name from the list (use "chat" if nothing else fits)
  "target": the topic/place/destination the command is about, "" if none
  "confidence": number 0-1
  "open_browser": true or false
  "video_format": "short", "video" or ""   (only for youtube_shorts / clip_live / daily_clips)

RULES for "open_browser" (be strict - opening a tab is disruptive):
  - false for greetings, thanks, small talk, opinions, simple questions, definitions, quick facts,
    weather, anything a short spoken answer fully handles.
  - true ONLY when the user explicitly asks to open/search/show something online, OR the question is
    big enough that reading sources helps (deep research, comparisons, buying decisions,
    complex projects, in-depth current events).
  - Commands that run a feature (email, reminder, music, clips, todo...) are false.

"video_format" rules: "short" if the user says shorts / vertical; "video" if they say a proper / full /
long / normal / horizontal video (NOT just "from this video"); "" if they don't say (they will be asked).

Other rules:
  - A message containing a YouTube link plus words like live / stream / streaming now -> "clip_live".
  - Words like "close", "stop", "bye" inside another request do NOT mean stop_system.
  - "thank you", "thanks", "good morning" etc. are "chat" with open_browser false.

{recent}
USER COMMAND: {command}

JSON:"""


def _parse(text):
    if not text:
        return None
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


_PREFERRED_MODELS = ["openai/gpt-oss-20b", "llama-3.1-8b-instant", "llama-3.3-70b-versatile",
                     "openai/gpt-oss-120b"]
_dead_models = set()   # models Groq says no longer exist - never tried again this session
_model_order = None


def _models_to_try(client):
    """Preferred models that Groq actually offers right now (so retired ones are skipped)."""
    global _model_order
    if _model_order is None:
        env = os.getenv("ROUTER_MODEL", "").strip()
        order = [m for m in ([env] if env else []) + _PREFERRED_MODELS if m not in _dead_models]
        try:
            available = {m.id for m in client.models.list().data}
            live = [m for m in order if m in available]
            order = live or order
        except Exception:
            pass
        _model_order = order
    return list(_model_order)


def _call_groq(prompt):
    global _model_order
    key = _groq_key()
    if not key:
        return None
    from groq import Groq
    client = Groq(api_key=key, timeout=float(os.getenv("ROUTER_TIMEOUT", "8")), max_retries=0)
    for model in _models_to_try(client):
        try:
            kwargs = {}
            max_tokens = 160
            if model.startswith("openai/gpt-oss"):
                kwargs["extra_body"] = {"reasoning_effort": "low"}
                max_tokens = 400  # reasoning models spend tokens thinking before the JSON
            resp = client.chat.completions.create(
                model=model, temperature=0, max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}], **kwargs)
            data = _parse(resp.choices[0].message.content or "")
            if data:
                return data
        except Exception as e:
            msg = str(e).lower()
            if "404" in msg or "not found" in msg or "decommission" in msg or "does not exist" in msg:
                _dead_models.add(model)   # retired model: stop trying it
                _model_order = None
                print(f"[ROUTER] {model} is no longer available - skipping it from now on")
            else:
                print(f"[ROUTER] {model} failed: {type(e).__name__}: {str(e)[:80]}")
    return None


def route(command):
    """Return a routing dict, or None if the AI router is unavailable."""
    try:
        if not enabled():
            return None
        norm = _norm(command)
        if not norm:
            return None

        quick = _QUICK_LOOKUP.get(norm)
        if quick:
            return {"intent": "chat", "target": "", "confidence": 1.0, "open_browser": False,
                    "video_format": "", "quick_reply": quick, "source": "fast"}

        with _cache_lock:
            hit = _cache.get(norm)
        if hit and time.time() - hit[0] < 120:
            return dict(hit[1], source="cache")

        data = _call_groq(_build_prompt(command, _recent_context()))
        if not data:
            return None

        intent = str(data.get("intent", "chat")).strip().lower()
        if intent not in INTENTS:
            intent = "chat"
        try:
            confidence = float(data.get("confidence", 0))
        except (TypeError, ValueError):
            confidence = 0.0
        if confidence < CONFIDENCE_FLOOR:
            intent = "chat"
        if intent == "stop_system" and confidence < STOP_CONFIDENCE:
            intent = "chat"

        result = {
            "intent": intent,
            "target": str(data.get("target", "") or "").strip(),
            "confidence": confidence,
            "open_browser": bool(data.get("open_browser", False)) and intent in BROWSER_INTENTS,
            "video_format": (normalize_format(data.get("video_format"))
                             if intent in {"youtube_shorts", "clip_live", "daily_clips"} else "") or "",
            "quick_reply": "",
            "source": "ai",
        }
        with _cache_lock:
            if len(_cache) >= _CACHE_MAX:
                _cache.clear()
            _cache[norm] = (time.time(), result)
        return result
    except Exception as e:
        print(f"[ROUTER] unavailable: {type(e).__name__}: {str(e)[:80]}")
        return None


def to_intent_data(result, command):
    """Convert a route() result into the {intent, target, confidence} dict main.py expects."""
    intent = result["intent"]
    if intent in PASS_COMMAND:
        target = command
    elif intent in USE_TARGET:
        target = result["target"]
        if intent == "news" and not target:
            target = "general"
    else:
        target = ""
    return {"intent": intent, "target": target, "confidence": result["confidence"]}