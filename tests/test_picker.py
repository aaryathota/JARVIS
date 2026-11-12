import json

import clip_picker


def test_ai_rank_clamps_clip_length_and_keeps_hook(monkeypatch):
    monkeypatch.setattr(
        clip_picker,
        "_ask_groq",
        lambda prompt: json.dumps({"picks": [{
            "id": 1, "start": 10, "end": 80,
            "hook_text": "Wait for the payoff", "score": 9,
            "reason": "self-contained reaction",
        }]}),
    )
    result = clip_picker._ai_rank([{"start": 5, "text": "A complete moment"}], 1, "Test")
    assert 20 <= result[0]["end"] - result[0]["start"] <= 45
    assert result[0]["hook_text"] == "Wait for the payoff"


def test_sponsor_language_is_penalized():
    sponsor = clip_picker._heuristic("Sponsored by this brand", 30, 0)
    reaction = clip_picker._heuristic("No way, that was incredible", 30, 0)
    assert sponsor < reaction
