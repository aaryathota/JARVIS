from db import clip_overlaps, init_db, save_clip, save_source


def test_overlapping_clips_are_rejected(tmp_path):
    database = str(tmp_path / "test.db")
    init_db(database)
    save_source({
        "video_id": "source-1",
        "channel_id": "channel-1",
        "channel_name": "Test",
        "title": "Test source",
        "url": "https://youtu.be/source-1",
        "published_at": "2026-11-12T00:00:00+00:00",
        "duration_seconds": 600,
    }, database)
    assert save_clip("source-1", 10, 40, path=database) is not None
    assert clip_overlaps("source-1", 20, 30, database)
    assert save_clip("source-1", 20, 30, path=database) is None
