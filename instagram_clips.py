"""
Instagram Clips Converter - Convert YouTube videos to Instagram Reels
Properly optimizes videos for Instagram format
"""

import os
import sys
from pathlib import Path

def download_youtube_video(youtube_url):
    """Download YouTube video to local file"""
    try:
        import yt_dlp
        
        output_path = "temp_youtube_video"
        
        # Simplified options that work reliably
        ydl_opts = {
            'format': 'best',
            'outtmpl': output_path,
            'quiet': False,
            'no_warnings': False,
            'socket_timeout': 30,
        }
        
        print(f"[CLIPS] Downloading video from YouTube...")
        print(f"[CLIPS] URL: {youtube_url}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("[CLIPS] Starting download...")
            info = ydl.extract_info(youtube_url, download=True)
            
            # Get the actual filename that was downloaded
            filename = ydl.prepare_filename(info)
            print(f"[CLIPS] Downloaded to: {filename}")
            
            if os.path.exists(filename):
                print(f"[CLIPS] File size: {os.path.getsize(filename) / 1024 / 1024:.1f} MB")
                return filename
            else:
                print(f"[CLIPS] File not found: {filename}")
                return None
    
    except ImportError:
        print("[CLIPS] yt-dlp not installed. Installing...")
        os.system("pip install -q yt-dlp")
        return download_youtube_video(youtube_url)
    
    except Exception as e:
        print(f"[CLIPS] Download error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None


def convert_for_instagram(video_file):
    """Convert video to Instagram Reels format (9:16 vertical, 3-90 seconds)"""
    try:
        from moviepy.editor import VideoFileClip
        
        print(f"[CLIPS] Converting video to Instagram format...")
        
        # Load video
        clip = VideoFileClip(video_file)
        duration = clip.duration
        
        print(f"[CLIPS] Original duration: {duration:.1f}s")
        
        # Instagram Reels: 3-90 seconds, 9:16 aspect ratio
        max_duration = 60  # Use 60s clips for Instagram
        if duration > max_duration:
            print(f"[CLIPS] Trimming to {max_duration}s...")
            clip = clip.subclip(0, max_duration)
        
        # Get dimensions and resize to 9:16 for Instagram vertical
        w, h = clip.size
        if w > h:  # Landscape - need to crop to vertical
            # Crop to 9:16 aspect ratio
            target_height = h
            target_width = int(target_height * 9 / 16)
            x_center = w / 2
            x1 = int(x_center - target_width / 2)
            x2 = int(x_center + target_width / 2)
            clip = clip.crop(x1=x1, x2=x2)
            print(f"[CLIPS] Cropped to 9:16 vertical format")
        
        # Save as MP4
        output_file = "instagram_reel_temp.mp4"
        print(f"[CLIPS] Saving as: {output_file}")
        clip.write_videofile(output_file, verbose=False, logger=None, audio=True)
        
        clip.close()
        print(f"[CLIPS] Converted successfully!")
        return output_file
    
    except ImportError:
        print("[CLIPS] moviepy not installed. Installing...")
        os.system("pip install -q moviepy")
        return convert_for_instagram(video_file)
    
    except Exception as e:
        print(f"[CLIPS] Conversion failed: {e}")
        return None


def create_instagram_clips_from_youtube(youtube_url, num_clips=2):
    """
    Make Instagram-READY Reels from a video link. NO Instagram login is ever attempted
    (automated logins can get an account banned).

    Uses the same smart pipeline as YouTube Shorts - best moments only, vertical 9:16,
    captions burned in - and saves the results to the instagram_ready/ folder, with a
    caption text file next to each one. Upload them yourself, then delete them.
    Returns the list of saved file paths.
    """
    try:
        from clip_automation import create_and_upload_clips_from_video
        return create_and_upload_clips_from_video(
            video_url=youtube_url, num_clips=num_clips, clip_duration=30,
            upload=False, instagram_only=True, video_format="short") or []
    except Exception as e:
        print(f"[CLIPS] Error: {e}")
        return []


# Alias for compatibility
def upload_instagram_clips_from_video(video_url, num_clips=2):
    """Alias for create_instagram_clips_from_youtube"""
    return create_instagram_clips_from_youtube(video_url, num_clips)