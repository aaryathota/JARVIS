"""
YouTube to Instagram Reel Upload
Download video from YouTube and upload directly to Instagram
"""

import sys
import os

print("=" * 70)
print("YOUTUBE TO INSTAGRAM REEL UPLOAD")
print("=" * 70)
print()

youtube_url = "https://www.youtube.com/watch?v=mAAbqIbTsG8"

try:
    print(f"[VIDEO] Downloading from: {youtube_url}")
    print()
    
    print("[STEP 1] Downloading YouTube video...")
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
        print(f"ERROR: Video file not found: {video_file}")
        sys.exit(1)
    
    file_size = os.path.getsize(video_file) / 1024 / 1024
    print(f"[OK] Downloaded: {video_file} ({file_size:.1f} MB)")
    print()
    
    print("[STEP 2] Initializing Instagram uploader...")
    from instagram_uploader import InstagramUploader
    
    uploader = InstagramUploader()
    if not uploader.is_authenticated:
        print("ERROR: Instagram authentication failed")
        sys.exit(1)
    
    print(f"[OK] Authenticated as: @{uploader.username}")
    print()
    
    print("[STEP 3] Uploading to Instagram Reels...")
    
    result = uploader.upload_video(
        video_file,
        caption="Check this out!"
    )
    
    print()
    if result:
        print("=" * 70)
        print("SUCCESS! VIDEO UPLOADED TO INSTAGRAM!")
        print("=" * 70)
        print()
        print(f"Account: @{uploader.username}")
        print("Your reel is now live on Instagram!")
        print()
        
        # Clean up
        try:
            os.remove(video_file)
            print(f"[CLEANUP] Removed: {video_file}")
        except:
            pass
    else:
        print("ERROR: Upload failed")
        sys.exit(1)

except ImportError as e:
    print(f"ERROR: Missing package: {e}")
    print("Installing required packages...")
    os.system("pip install -q yt-dlp instagrapi moviepy")
    print("Please run the script again")
    sys.exit(1)

except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
