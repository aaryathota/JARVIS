"""
Video Clipper - Create short clips from long videos using FFmpeg
"""
from job_status import say
import os
import subprocess
import json
from datetime import datetime
import random
import shutil

os.makedirs("clips", exist_ok=True)
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")


def _settings():
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, ValueError):
        return {}


def _encoder(settings):
    requested = settings.get("encoder", "auto")
    if requested not in ("auto", "h264_nvenc", "libx264"):
        requested = "auto"
    if requested == "libx264":
        return requested
    try:
        result = subprocess.run(
            [_tool("ffmpeg"), "-hide_banner", "-encoders"],
            capture_output=True, text=True, timeout=10,
        )
        if "h264_nvenc" in result.stdout:
            return "h264_nvenc"
    except Exception:
        pass
    return "libx264"


def _drawtext(value, font, size, y):
    if not value:
        return ""
    escaped = str(value).replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
    font_part = f":fontfile='{font}'" if font else ""
    return f"drawtext=text='{escaped}'{font_part}:fontsize={size}:fontcolor=white:borderw=2:bordercolor=black@0.75:x=(w-text_w)/2:y={y}"


def _tool(name):
    """Use the newest ffmpeg/ffprobe found (see ffmpeg_finder), else PATH, else old location."""
    from ffmpeg_finder import find_ffmpeg, find_ffprobe
    found = find_ffmpeg() if name == "ffmpeg" else find_ffprobe()
    return found or shutil.which(name) or rf"C:\ffmpeg\bin\{name}.exe"


def get_video_duration(video_path):
    """Get duration of video in seconds using FFmpeg"""
    try:
        # Use full path to ffprobe
        ffprobe_path = _tool("ffprobe")
        cmd = [
            ffprobe_path,
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            duration = float(result.stdout.strip())
            say(f"[CLIPPER] Video duration: {duration:.1f} seconds")
            return duration
        else:
            say(f"[CLIPPER ERROR] FFprobe error: {result.stderr[:100]}")
            return None
    except Exception as e:
        say(f"[CLIPPER ERROR] Getting duration: {str(e)}")
        return None


def create_video_clip(input_video, start_time, duration=45, output_path=None, vertical=True):
    """
    Create a short clip from a video using FFmpeg
    
    Args:
        input_video: Path to input video
        start_time: Start time in seconds
        duration: Clip duration in seconds (default 45s)
        output_path: Output file path
        vertical: Create vertical 9:16 aspect ratio for YouTube Shorts (default True)
    
    Returns:
        Path to created clip or None
    """
    try:
        if not output_path:
            output_path = f"clips/clip_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        
        say(f"[CLIPPER] Creating clip: {start_time}s - {start_time + duration}s" + (" (Shorts format)" if vertical else ""))
        
        # FFmpeg command to extract clip
        ffmpeg_path = _tool("ffmpeg")
        
        settings = _settings().get("video", {})
        branding = _settings().get("branding", {})
        encoder = _encoder(settings)
        if vertical:
            width = int(settings.get("width", 1080))
            height = int(settings.get("height", 1920))
            blur = int(settings.get("blur_strength", 18))
            filter_complex = (
                f"[0:v]split=2[bg][fg];"
                f"[bg]scale={width}:{height}:force_original_aspect_ratio=increase,"
                f"crop={width}:{height},boxblur=luma_radius={blur}:luma_power=1[bgv];"
                f"[fg]scale={width}:{height}:force_original_aspect_ratio=decrease[fgv];"
                f"[bgv][fgv]overlay=(W-w)/2:(H-h)/2,"
                f"format=yuv420p"
            )
            for value, y in ((branding.get("watermark", ""), 42),
                             (branding.get("source_credit", ""), height - 76)):
                text_filter = _drawtext(value, branding.get("font", ""),
                                        int(branding.get("font_size", 44)), y)
                if text_filter:
                    filter_complex += f",{text_filter}"
            filter_complex += "[vout]"
            cmd = [
                ffmpeg_path,
                "-i", input_video,
                "-ss", str(start_time),
                "-t", str(duration),
                "-filter_complex", filter_complex,
                "-map", "[vout]",
                "-map", "0:a?",
                "-c:v", encoder,
                "-preset", "p4" if encoder == "h264_nvenc" else settings.get("preset", "fast"),
                "-crf", str(settings.get("crf", 23)),
                "-c:a", "aac",
                "-b:a", settings.get("audio_bitrate", "128k"),
                *( ["-af", "loudnorm=I=-14:LRA=11:TP=-1.5"] if settings.get("loudnorm", True) else [] ),
                "-y",  # Overwrite output
                output_path
            ]
        else:
            # Proper horizontal video: keep the original framing, cap at 1080p,
            # and use the same encoder / audio settings as the Shorts render
            cmd = [
                ffmpeg_path,
                "-i", input_video,
                "-ss", str(start_time),
                "-t", str(duration),
                "-vf", "scale=w='min(1920,iw)':h=-2,format=yuv420p",
                "-c:v", encoder,
                "-preset", "p4" if encoder == "h264_nvenc" else settings.get("preset", "fast"),
                "-crf", str(settings.get("crf", 23)),
                "-c:a", "aac",
                "-b:a", settings.get("audio_bitrate", "128k"),
                *( ["-af", "loudnorm=I=-14:LRA=11:TP=-1.5"] if settings.get("loudnorm", True) else [] ),
                "-y",  # Overwrite output
                output_path
            ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0 and os.path.exists(output_path):
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            say(f"[CLIPPER] ✓ Clip created: {output_path} ({size_mb:.1f}MB)")
            return output_path
        else:
            say(f"[CLIPPER] Error: {result.stderr[:200]}")
            return None
    
    except subprocess.TimeoutExpired:
        say("[CLIPPER] Timeout - clip too large")
        return None
    except Exception as e:
        say(f"[CLIPPER ERROR] {str(e)}")
        return None


def create_multiple_clips(input_video, num_clips=3, clip_duration=45):
    """
    Create multiple clips from different parts of a video
    
    Args:
        input_video: Path to input video
        num_clips: Number of clips to create
        clip_duration: Duration of each clip in seconds
    
    Returns:
        List of clip file paths
    """
    try:
        total_duration = get_video_duration(input_video)
        
        if not total_duration:
            say("[CLIPPER] Could not get video duration")
            return []
        
        say(f"[CLIPPER] Video duration: {total_duration}s, creating {num_clips} clips")
        
        clips = []
        
        # Skip first 10% and last 10% of video (typically intro/outro)
        min_start = int(total_duration * 0.1)
        max_start = int(total_duration * 0.9) - clip_duration
        
        if max_start <= min_start:
            say("[CLIPPER] Video too short for clipping")
            return []
        
        for i in range(num_clips):
            # Random start point
            start_time = random.randint(min_start, max_start)
            
            output_path = f"clips/clip_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            clip_path = create_video_clip(input_video, start_time, clip_duration, output_path)
            
            if clip_path:
                clips.append(clip_path)
        
        say(f"[CLIPPER] ✓ Created {len(clips)} clips")
        return clips
    
    except Exception as e:
        say(f"[CLIPPER ERROR] {str(e)}")
        return []


def create_highlight_clip(input_video, duration=30):
    """
    Create a clip from a random interesting part of the video
    
    Args:
        input_video: Path to input video
        duration: Clip duration in seconds
    
    Returns:
        Path to created clip or None
    """
    try:
        total_duration = get_video_duration(input_video)
        
        if not total_duration or total_duration < duration:
            say("[CLIPPER] Video too short")
            return None
        
        # Random start between 10% and 80% of video
        min_start = int(total_duration * 0.1)
        max_start = int(total_duration * 0.8) - duration
        start_time = random.randint(min_start, max_start)
        
        output_path = f"clips/highlight_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        
        return create_video_clip(input_video, start_time, duration, output_path)
    
    except Exception as e:
        say(f"[CLIPPER ERROR] {str(e)}")
        return None


if __name__ == "__main__":
    say("Video Clipper Ready")