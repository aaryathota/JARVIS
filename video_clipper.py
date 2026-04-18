"""
Video Clipper - Create short clips from long videos using FFmpeg
"""
import os
import subprocess
from datetime import datetime
import random

os.makedirs("clips", exist_ok=True)

def get_video_duration(video_path):
    """Get duration of video in seconds using FFmpeg"""
    try:
        # Use full path to ffprobe
        ffprobe_path = r"C:\ffmpeg\bin\ffprobe.exe"
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
            print(f"[CLIPPER] Video duration: {duration:.1f} seconds")
            return duration
        else:
            print(f"[CLIPPER ERROR] FFprobe error: {result.stderr[:100]}")
            return None
    except Exception as e:
        print(f"[CLIPPER ERROR] Getting duration: {str(e)}")
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
        
        print(f"[CLIPPER] Creating clip: {start_time}s - {start_time + duration}s" + (" (Shorts format)" if vertical else ""))
        
        # FFmpeg command to extract clip
        ffmpeg_path = r"C:\ffmpeg\bin\ffmpeg.exe"
        
        if vertical:
            # YouTube Shorts format: 1080x1920 (9:16 aspect ratio)
            filter_complex = "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2"
            cmd = [
                ffmpeg_path,
                "-i", input_video,
                "-ss", str(start_time),
                "-t", str(duration),
                "-vf", filter_complex,
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-c:a", "aac",
                "-b:a", "128k",
                "-y",  # Overwrite output
                output_path
            ]
        else:
            # Standard horizontal format
            cmd = [
                ffmpeg_path,
                "-i", input_video,
                "-ss", str(start_time),
                "-t", str(duration),
                "-c:v", "libx264",
                "-preset", "fast",
                "-c:a", "aac",
                "-y",  # Overwrite output
                output_path
            ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0 and os.path.exists(output_path):
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            print(f"[CLIPPER] ✓ Clip created: {output_path} ({size_mb:.1f}MB)")
            return output_path
        else:
            print(f"[CLIPPER] Error: {result.stderr[:200]}")
            return None
    
    except subprocess.TimeoutExpired:
        print("[CLIPPER] Timeout - clip too large")
        return None
    except Exception as e:
        print(f"[CLIPPER ERROR] {str(e)}")
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
            print("[CLIPPER] Could not get video duration")
            return []
        
        print(f"[CLIPPER] Video duration: {total_duration}s, creating {num_clips} clips")
        
        clips = []
        
        # Skip first 10% and last 10% of video (typically intro/outro)
        min_start = int(total_duration * 0.1)
        max_start = int(total_duration * 0.9) - clip_duration
        
        if max_start <= min_start:
            print("[CLIPPER] Video too short for clipping")
            return []
        
        for i in range(num_clips):
            # Random start point
            start_time = random.randint(min_start, max_start)
            
            output_path = f"clips/clip_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            clip_path = create_video_clip(input_video, start_time, clip_duration, output_path)
            
            if clip_path:
                clips.append(clip_path)
        
        print(f"[CLIPPER] ✓ Created {len(clips)} clips")
        return clips
    
    except Exception as e:
        print(f"[CLIPPER ERROR] {str(e)}")
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
            print("[CLIPPER] Video too short")
            return None
        
        # Random start between 10% and 80% of video
        min_start = int(total_duration * 0.1)
        max_start = int(total_duration * 0.8) - duration
        start_time = random.randint(min_start, max_start)
        
        output_path = f"clips/highlight_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        
        return create_video_clip(input_video, start_time, duration, output_path)
    
    except Exception as e:
        print(f"[CLIPPER ERROR] {str(e)}")
        return None


if __name__ == "__main__":
    print("Video Clipper Ready")
