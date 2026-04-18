"""
YouTube to Instagram - With Video Trimming
Download, trim to 60 seconds, and upload to Instagram
"""

import sys
import os

print("=" * 70)
print("YOUTUBE TO INSTAGRAM (WITH TRIMMING)")
print("=" * 70)
print()

youtube_url = "https://www.youtube.com/watch?v=mAAbqIbTsG8"

try:
    print(f"[STEP 1] Downloading YouTube video...")
    import yt_dlp
    
    output_file = "youtube_video"
    ydl_opts = {
        'format': 'best',
        'outtmpl': output_file,
        'quiet': False,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=True)
        video_file = ydl.prepare_filename(info)
    
    if not os.path.exists(video_file):
        print(f"ERROR: Video file not found")
        sys.exit(1)
    
    file_size = os.path.getsize(video_file) / 1024 / 1024
    print(f"[OK] Downloaded: {video_file} ({file_size:.1f} MB)")
    print()
    
    print("[STEP 2] Trimming video for Instagram (60 seconds)...")
    from moviepy.editor import VideoFileClip
    
    clip = VideoFileClip(video_file)
    duration = clip.duration
    print(f"[INFO] Original duration: {duration:.1f} seconds")
    
    # Instagram Reels: 3-90 seconds, trim to 60s using subclip (not subclipped)
    if duration > 60:
        print(f"[INFO] Trimming to 60 seconds...")
        clip_trimmed = clip.subclip(0, 60)  # Fixed: subclip not subclipped
    else:
        clip_trimmed = clip
    
    trimmed_file = "instagram_video_trim.mp4"
    print(f"[INFO] Rendering trimmed video...")
    clip_trimmed.write_videofile(trimmed_file, verbose=False, logger=None, audio=True)
    
    clip.close()
    clip_trimmed.close()
    
    print(f"[OK] Trimmed video: {trimmed_file}")
    print()
    
    print("[STEP 3] Authenticating to Instagram...")
    from instagram_uploader import InstagramUploader
    
    uploader = InstagramUploader()
    if not uploader.is_authenticated:
        print("ERROR: Instagram authentication failed")
        sys.exit(1)
    
    print(f"[OK] Authenticated as: @{uploader.username}")
    print()
    
    print("[STEP 4] Uploading to Instagram Reels...")
    
    result = uploader.upload_video(
        trimmed_file,
        caption="Check this out!"
    )
    
    print()
    if result:
        print("=" * 70)
        print("SUCCESS! VIDEO UPLOADED TO INSTAGRAM REELS!")
        print("=" * 70)
        print()
        print(f"Account: @{uploader.username}")
        print("Your reel is now live on Instagram!")
        print()
        
        # Clean up
        for file in [video_file, trimmed_file]:
            try:
                if os.path.exists(file):
                    os.remove(file)
                    print(f"[CLEANUP] Removed: {file}")
            except:
                pass
    else:
        print("ERROR: Upload failed")
        sys.exit(1)

except ImportError as e:
    print(f"ERROR: Missing package: {e}")
    print("Installing...")
    os.system("pip install -q yt-dlp instagrapi moviepy")
    print("Please run again")
    sys.exit(1)

except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
