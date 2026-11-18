import json
import math
import struct
import subprocess
import wave

import live_clipper as lc


def test_extract_youtube_url_keeps_case_and_ignores_other_text():
    assert lc.extract_youtube_url("clip https://www.youtube.com/live/AbCdEf12345?si=x now") == \
        "https://www.youtube.com/live/AbCdEf12345?si=x"
    assert lc.extract_youtube_url("see https://youtu.be/AbCdEf12345.") == "https://youtu.be/AbCdEf12345"
    assert lc.extract_youtube_url("no link here") is None


def test_hls_format_choice_prefers_muxed_720p_or_lower():
    info = {"formats": [
        {"url": "a", "protocol": "m3u8_native", "vcodec": "avc1", "acodec": "mp4a", "height": 360},
        {"url": "b", "protocol": "m3u8_native", "vcodec": "avc1", "acodec": "mp4a", "height": 720},
        {"url": "c", "protocol": "m3u8_native", "vcodec": "avc1", "acodec": "mp4a", "height": 1080},
        {"url": "d", "protocol": "https", "vcodec": "avc1", "acodec": "none", "height": 1080}]}
    assert lc._hls_inputs(info)[0] == ["b"]


def test_json3_roundtrip_is_readable_by_existing_caption_code(tmp_path):
    from caption_generator import get_clip_transcript
    words = [{"word": w, "start": i * 0.4, "end": i * 0.4 + 0.3}
             for i, w in enumerate("this is a very funny moment right here".split())]
    video = tmp_path / "live_x.mkv"
    video.write_bytes(b"")
    assert lc._write_json3(words, str(video.with_suffix(".en.json3")))
    assert "funny moment" in get_clip_transcript(str(video), 0, 10)


def test_loudest_window_is_found(tmp_path):
    rate = 8000
    wav_path = tmp_path / "t.wav"
    with wave.open(str(wav_path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
        frames = bytearray()
        for sec in range(60):
            amp = 20000 if 30 <= sec < 40 else 500   # loud burst at 30-40s
            for i in range(rate):
                frames += struct.pack("<h", int(amp * math.sin(i / 8)))
        w.writeframes(bytes(frames))
    mkv = tmp_path / "t.mkv"
    subprocess.run([lc._ffmpeg(), "-y", "-loglevel", "error", "-i", str(wav_path), str(mkv)], check=True)
    pick = lc._loudest_windows(str(mkv), 1, 10, 60)[0]
    assert 28 <= pick["start"] <= 31