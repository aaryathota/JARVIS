import os

import instagram_export as ie


def test_short_is_saved_with_caption_text(tmp_path, monkeypatch):
    monkeypatch.setattr(ie, "EXPORT_DIR", str(tmp_path / "instagram_ready"))
    clip = tmp_path / "clip.mp4"
    clip.write_bytes(b"x" * 100)
    out = ie.save_for_instagram(str(clip), "Funny Moment!", "caption body #fun", "short")
    assert out and os.path.exists(out) and clip.exists()          # copied, original kept
    txt = open(os.path.splitext(out)[0] + ".txt", encoding="utf-8").read()
    assert "Funny Moment!" in txt and "caption body" in txt


def test_move_removes_original_and_names_never_collide(tmp_path, monkeypatch):
    monkeypatch.setattr(ie, "EXPORT_DIR", str(tmp_path / "ready"))
    paths = []
    for n in range(2):
        clip = tmp_path / f"c{n}.mp4"
        clip.write_bytes(b"x" * 10)
        paths.append(ie.save_for_instagram(str(clip), "same title", "", "short", move=True))
        assert not clip.exists()
    assert paths[0] != paths[1]


def test_proper_videos_and_missing_files_are_skipped_without_errors(tmp_path, monkeypatch):
    monkeypatch.setattr(ie, "EXPORT_DIR", str(tmp_path / "ready"))
    clip = tmp_path / "v.mp4"
    clip.write_bytes(b"x")
    assert ie.save_for_instagram(str(clip), "t", "c", "video") is None      # horizontal -> no Reel
    assert ie.save_for_instagram(str(tmp_path / "nope.mp4"), "t", "c", "short") is None
    assert not (tmp_path / "ready").exists()


def test_instagram_login_is_never_attempted(monkeypatch):
    import instagram_uploader as iu
    calls = []

    class FakeClient:
        def login(self, *a, **k):
            calls.append("login")

    monkeypatch.setattr(iu, "Client", FakeClient)
    monkeypatch.setenv("INSTAGRAM_USERNAME", "someone")
    monkeypatch.setenv("INSTAGRAM_PASSWORD", "secret")
    up = iu.InstagramUploader()
    assert calls == [] and up.is_authenticated is False
    assert up.authenticate() is False and calls == []