import intent_router as ir


def _fake(answer):
    ir._cache.clear()
    ir._call_groq = lambda prompt: answer


def test_greetings_and_thanks_need_no_ai_and_never_open_browser():
    ir._call_groq = lambda p: (_ for _ in ()).throw(AssertionError("AI must not be called"))
    for text in ("hello", "Thank you!", "good morning", "how are you"):
        r = ir.route(text)
        assert r["intent"] == "chat" and not r["open_browser"] and r["quick_reply"]


def test_only_big_topics_may_open_browser():
    _fake({"intent": "weather", "confidence": 0.95, "open_browser": True})
    assert ir.route("how hot is it")["open_browser"] is False
    _fake({"intent": "chat", "confidence": 0.95, "open_browser": True})
    assert ir.route("tell me a fun fact")["open_browser"] is False
    _fake({"intent": "research", "confidence": 0.9, "open_browser": True})
    assert ir.route("compare ev batteries in depth")["open_browser"] is True


def test_bad_or_shaky_answers_downgrade_to_chat():
    _fake({"intent": "made_up", "confidence": 0.99, "open_browser": True})
    assert ir.route("blah")["intent"] == "chat"
    _fake({"intent": "todo", "confidence": 0.2})
    assert ir.route("hmm")["intent"] == "chat"
    _fake({"intent": "stop_system", "confidence": 0.7})
    assert ir.route("close the door")["intent"] == "chat"


def test_ai_unavailable_returns_none_so_keywords_take_over():
    ir._cache.clear()
    ir._call_groq = lambda p: None
    assert ir.route("play some music") is None


def test_target_format_matches_existing_handlers():
    r = {"intent": "weather", "target": "Pune", "confidence": 0.9}
    assert ir.to_intent_data(r, "weather in pune")["target"] == "Pune"
    r = {"intent": "clip_live", "target": "", "confidence": 0.9}
    assert ir.to_intent_data(r, "clip https://youtu.be/x")["target"] == "clip https://youtu.be/x"