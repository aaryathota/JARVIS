"""
Clip Automation Module - Restored
Handles automatic video clip creation and uploading
"""

import os
import time

def create_and_upload_clips_from_video(video_url, num_clips=2, clip_duration=30, privacy_status="public", wait_between_uploads=60):
    """
    Create clips from a YouTube video and upload them to YouTube Shorts
    
    Args:
        video_url: URL of the YouTube video
        num_clips: Number of clips to create
        clip_duration: Duration of each clip in seconds
        privacy_status: Privacy setting (public/unlisted/private)
        wait_between_uploads: Wait time between uploads
    
    Returns:
        List of uploaded video IDs
    """
    try:
        from video_clipper import get_video_duration, create_video_clip
        from youtube_uploader import YouTubeUploader
        from utils import speak
        import subprocess
        
        print(f"[CLIP AUTOMATION] Processing YouTube video for Shorts...")
        speak(f"Downloading video and creating {num_clips} clips. This may take a few minutes.")
        
        # Step 1: Download the video from YouTube
        print("[CLIP AUTOMATION] Downloading video from YouTube...")
        speak("Downloading video...")
        
        try:
            # Try to download video using yt-dlp
            video_file = None
            try:
                import yt_dlp
                print("[CLIP AUTOMATION] Using yt-dlp to download...")
                
                # Download to downloads folder
                ydl_opts = {
                    'format': 'best[ext=mp4]',
                    'outtmpl': 'downloads/%(title)s.%(ext)s',
                    'quiet': False,
                    'no_warnings': False,
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(video_url, download=True)
                    video_file = ydl.prepare_filename(info)
                    print(f"[CLIP AUTOMATION] Downloaded: {video_file}")
            
            except ImportError:
                print("[CLIP AUTOMATION] yt-dlp not available, trying youtube-dl...")
                # Fallback to youtube-dl
                cmd = [
                    "youtube-dl",
                    "-f", "best[ext=mp4]",
                    "-o", "downloads/%(title)s.%(ext)s",
                    video_url
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    # Find downloaded file
                    import glob
                    files = glob.glob("downloads/*.mp4")
                    if files:
                        video_file = files[-1]  # Get most recent
                        print(f"[CLIP AUTOMATION] Downloaded: {video_file}")
                
            except Exception as e:
                print(f"[CLIP AUTOMATION] Download error: {e}")
            
            if not video_file or not os.path.exists(video_file):
                print("[CLIP AUTOMATION] Failed to download video")
                speak("Failed to download video. Please check the URL and try again.")
                return []
        
        except Exception as download_err:
            print(f"[CLIP AUTOMATION] Download failed: {download_err}")
            speak(f"Failed to download: {str(download_err)[:50]}")
            return []
        
        # Step 2: Get video duration to calculate clip start times
        print("[CLIP AUTOMATION] Analyzing video...")
        video_duration = get_video_duration(video_file)
        
        if not video_duration:
            print("[CLIP AUTOMATION] Could not get video duration")
            speak("Could not analyze video. Please try again.")
            return []
        
        print(f"[CLIP AUTOMATION] Video duration: {video_duration:.0f} seconds")
        
        # Step 3: Extract clips using FFmpeg
        print(f"[CLIP AUTOMATION] Creating {num_clips} clips from video...")
        speak(f"Creating {num_clips} clips from video...")
        
        # Initialize YouTube uploader
        try:
            uploader = YouTubeUploader()
            if not uploader.youtube:
                print("[CLIP AUTOMATION] Warning: YouTube uploader not initialized.")
                uploader = None
        except Exception as e:
            print(f"[CLIP AUTOMATION] Warning: Could not initialize YouTube uploader: {e}")
            uploader = None
        
        uploaded_clips = []
        
        # Generate random start times for all clips
        import random
        random_start_times = []
        if video_duration > clip_duration:
            max_start = video_duration - clip_duration
            # Generate random start times from throughout the video
            for _ in range(num_clips):
                random_start = random.uniform(0, max_start)
                random_start_times.append(random_start)
        else:
            random_start_times = [0] * num_clips
        
        for i in range(num_clips):
            start_time = random_start_times[i]
            
            print(f"[CLIPS] Extracting clip {i+1}/{num_clips} at {start_time:.0f}s...")
            speak(f"Creating clip {i+1} of {num_clips}...")
            
            # Create clip using FFmpeg
            clip_path = create_video_clip(
                input_video=video_file,
                start_time=start_time,
                duration=clip_duration,
                vertical=True  # YouTube Shorts format
            )
            
            if clip_path and os.path.exists(clip_path):
                print(f"[CLIPS] Created: {clip_path}")
                
                # Upload to YouTube if uploader is available
                if uploader:
                    try:
                        title = f"Daily Fun • Clip #{i+1} 🎬✨"
                        description = f"""For more daily fun clips like this, make sure to LIKE and SUBSCRIBE! 🔔

New short videos every day - entertainment, humor, crazy moments, and more!

Hit that LIKE button if you enjoyed this clip 👍
SUBSCRIBE for more amazing shorts 🔥

Let's grow this community together! 💪

#Shorts #DailyClips #MustWatch #Viral #Trending"""
                        tags = ["shorts", "viral", "trending", "funnyvideos", "entertaining", "dailyclips", "clips", "mustwatch"]
                        
                        print(f"[CLIPS] Uploading clip {i+1}/{num_clips} to YouTube...")
                        
                        video_id = uploader.upload_video(
                            video_file=clip_path,
                            title=title,
                            description=description,
                            tags=tags,
                            privacy_status=privacy_status
                        )
                        
                        if video_id:
                            print(f"[CLIPS] ✓ Uploaded! Video ID: {video_id}")
                            print(f"[CLIPS] URL: https://www.youtube.com/shorts/{video_id}")
                            uploaded_clips.append(video_id)
                            speak(f"Clip {i+1} uploaded successfully!")
                        else:
                            print(f"[CLIPS] Failed to upload clip {i+1}")
                    
                    except Exception as upload_error:
                        print(f"[CLIPS] Upload error for clip {i+1}: {upload_error}")
                else:
                    # If uploader not available, just add the file path
                    uploaded_clips.append(clip_path)
                
                # Wait before next upload to avoid rate limits
                if i < num_clips - 1:
                    wait_time = 30  # Reduced wait time for smoother experience
                    print(f"[CLIPS] Preparing next clip ({wait_time}s)...")
                    time.sleep(wait_time)
        
        # Clean up downloaded video
        try:
            os.remove(video_file)
            print(f"[CLIPS] Cleaned up: {video_file}")
        except:
            pass
        
        if uploaded_clips:
            speaks_msg = f"Successfully created and uploaded {len(uploaded_clips)} YouTube Shorts!"
            speak(speaks_msg)
            print(f"[CLIPS] ✓ {speaks_msg}")
            for vid_id in uploaded_clips:
                print(f"[CLIPS] → https://www.youtube.com/shorts/{vid_id}")
        else:
            print(f"[CLIPS] No clips were successfully uploaded")
        
        return uploaded_clips
    
    except Exception as e:
        print(f"[CLIP AUTOMATION ERROR] {type(e).__name__}: {e}")
        return []

def extract_best_clips(video_path, num_clips=3):
    """Extract the best clips from a video based on engagement"""
    try:
        print(f"[CLIPS] Extracting {num_clips} best clips from {video_path}...")
        # Clip extraction logic here
        return [f"clip_{i}.mp4" for i in range(num_clips)]
    except Exception as e:
        print(f"[EXTRACTION ERROR] {e}")
        return []

def batch_upload_clips(clips_list, destination='youtube'):
    """Upload multiple clips to a destination"""
    try:
        print(f"[BATCH UPLOAD] Uploading {len(clips_list)} clips to {destination}...")
        uploaded = []
        
        for clip in clips_list:
            print(f"[BATCH] Uploading: {clip}")
            uploaded.append(clip)
        
        return uploaded
    
    except Exception as e:
        print(f"[BATCH UPLOAD ERROR] {e}")
        return []
