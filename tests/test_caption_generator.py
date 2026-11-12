import json

import caption_generator


def test_caption_has_core_tags_and_niche_category(monkeypatch):
    monkeypatch.setattr(
        caption_generator,
        "_ask_groq",
        lambda prompt: json.dumps({
            "titles": ["A specific gaming moment with context", "Short hook", "Option three", "Option four", "Option five"],
            "hook": "A real hook.",
            "hashtags": ["Minecraft", "StreamerName"],
            "pinned_comment": "Would you make the same move?",
        }),
    )
    result = caption_generator.generate_caption(
        "Gaming stream highlight", "", "StreamerName", "https://example.com", "We made the move.", 1, niche="gaming"
    )
    assert len(result["title"]) <= 60
    assert result["category_id"] == "20"
    assert all(tag in result["tags"] for tag in caption_generator.CORE_HASHTAGS)
    assert result["pinned_comment"]
