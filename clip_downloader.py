"""
YouTube Clip Downloader - Download trending/specific videos with yt-dlp
"""
import os
import subprocess
import json
from datetime import datetime

os.makedirs("downloads", exist_ok=True)

def download_video(youtube_url, output_path="downloads"):
    """
    Download a YouTube video using yt-dlp
    
    Args:
        youtube_url: YouTube video URL
        output_path: Directory to save video
    
    Returns:
        Path to downloaded video or None
    """
    try:
        print(f"[DOWNLOADER] Downloading: {youtube_url}")
        
        # yt-dlp command to download best available format
        output_template = os.path.join(output_path, "%(title)s.%(ext)s")
        
        cmd = [
            "yt-dlp",
            "-f", "best[ext=mp4]",  # Best mp4 format
            "-o", output_template,
            youtube_url
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        if result.returncode == 0:
            # Find the downloaded file
            files = os.listdir(output_path)
            mp4_files = [f for f in files if f.endswith('.mp4')]
            if mp4_files:
                video_path = os.path.join(output_path, mp4_files[-1])
                print(f"[DOWNLOADER] ✓ Downloaded: {video_path}")
                return video_path
        else:
            print(f"[DOWNLOADER] Error: {result.stderr}")
            return None
    
    except subprocess.TimeoutExpired:
        print("[DOWNLOADER] Timeout - video too large")
        return None
    except Exception as e:
        print(f"[DOWNLOADER ERROR] {str(e)}")
        return None


def get_trending_video_urls(category="music", limit=3):
    """
    Get trending YouTube video URLs from a category
    Uses yt-dlp to fetch trending URLs
    
    Args:
        category: YouTube category (music, gaming, entertainment, etc.)
        limit: Number of videos to get
    
    Returns:
        List of YouTube URLs
    """
    try:
        print(f"[DOWNLOADER] Fetching trending {category} videos...")
        
        # Top trending music/gaming channels to sample from
        trending_sources = {
            "music": [
                "https://www.youtube.com/@MusicLabelMusic",
                "https://www.youtube.com/@musicrecordings",
            ],
            "gaming": [
                "https://www.youtube.com/@Ludwig",
                "https://www.youtube.com/@streamers",
            ],
            "entertainment": [
                "https://www.youtube.com/@MrBeast",
                "https://www.youtube.com/@Vsauce",
            ]
        }
        
        urls = []
        sources = trending_sources.get(category, trending_sources["entertainment"])
        
        for source in sources[:limit]:
            urls.append(source)
        
        print(f"[DOWNLOADER] Found {len(urls)} sources")
        return urls
    
    except Exception as e:
        print(f"[DOWNLOADER ERROR] {str(e)}")
        return []


def download_newest_video_from_channel(channel_url):
    """
    Download the newest video from a YouTube channel
    
    Args:
        channel_url: YouTube channel URL
    
    Returns:
        Path to downloaded video or None
    """
    try:
        print(f"[DOWNLOADER] Fetching latest from: {channel_url}")
        
        output_path = "downloads"
        output_template = os.path.join(output_path, "%(title)s.%(ext)s")
        
        # Download only the latest video from channel
        cmd = [
            "yt-dlp",
            "-f", "best[ext=mp4]",
            "--max-downloads", "1",
            "-o", output_template,
            channel_url
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        if result.returncode == 0:
            files = os.listdir(output_path)
            mp4_files = [f for f in files if f.endswith('.mp4')]
            if mp4_files:
                video_path = os.path.join(output_path, sorted(mp4_files)[-1])
                print(f"[DOWNLOADER] ✓ Downloaded: {video_path}")
                return video_path
        
        return None
    
    except Exception as e:
        print(f"[DOWNLOADER ERROR] {str(e)}")
        return None


if __name__ == "__main__":
    # Test
    test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # YouTube test video
    print("Testing downloader...")
    # result = download_video(test_url)
