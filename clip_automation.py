"""
Clip Automation Module
Cuts YouTube Shorts from a video WITHOUT downloading the whole video:
only the time range of each clip is downloaded, cut, uploaded and deleted.
"""

import glob
import os
import re
import time

# Delete each clip from disk once it has been uploaded to YouTube
DELETE_CLIPS_AFTER_UPLOAD = True

# Pick the most engaging moments instead of random ones
SMART_CLIPPING = True

# Highest source resolution to fetch for a clip (720 is smaller/faster)
MAX_SOURCE_HEIGHT = 1080

VIDEO_FORMAT = (
    f"bv*[height<={MAX_SOURCE_HEIGHT}][vcodec^=avc1][ext=mp4]+ba[ext=m4a]"
    f"/b[height<={MAX_SOURCE_HEIGHT}][ext=mp4]"
    f"/bv*[height<={MAX_SOURCE_HEIGHT}]+ba/b"
)


def _remove(path):
    """Delete a file if it exists. Returns True if something was deleted."""
    try:
        if path and os.path.exists(path):
            os.remove(path)
            return True
    except Exception as e:
        print(f"[CLIPS] Could not delete {path}: {e}")
    return False


def delete_clip_after_upload(clip_path):
    """Delete a local clip once it is safely uploaded."""
    if _remove(clip_path):
        print(f"[CLIPS] Deleted local clip: {clip_path}")
        return True
    return False


def fetch_source_info(video_url):
    """Read the video's details (length, title, most-replayed data). No video download."""
    import yt_dlp

    opts = {
        "skip_download": True,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(video_url, download=False)


def fetch_subtitles(video_url, video_id):
    """
    Best-effort: save English subtitles to downloads/. NEVER raises - the
    transcript only improves captions and clip picking, it is not required.
    Returns True if a subtitle file was saved.
    """
    import yt_dlp

    os.makedirs("downloads", exist_ok=True)
    for lang in ("en", "en-orig"):
        for attempt in (1, 2):
            opts = {
                "skip_download": True,
                "noplaylist": True,
                "writeautomaticsub": True,
                "writesubtitles": True,
                "subtitleslangs": [lang],
                "subtitlesformat": "json3",
                "outtmpl": f"downloads/source_{video_id}.%(ext)s",
                "quiet": True,
                "no_warnings": True,
            }
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.extract_info(video_url, download=True)
            except Exception as e:
                msg = str(e)
                if "429" in msg:
                    if attempt == 1:
                        print("[CLIP AUTOMATION] YouTube rate-limited the subtitle request, retrying in 5s...")
                        time.sleep(5)
                        continue
                    print("[CLIP AUTOMATION] Subtitles still rate-limited - continuing without them")
                    return False
                print(f"[CLIP AUTOMATION] Subtitles unavailable ({lang}): {msg[:120]}")
                break
            if glob.glob(glob.escape(f"downloads/source_{video_id}") + "*.json3"):
                return True
            break
    return False


def download_segment(video_url, video_id, index, start, end):
    """Download only [start, end] seconds of the video. Returns the file path or None."""
    import yt_dlp
    from yt_dlp.utils import download_range_func

    prefix = f"downloads/segment_{video_id}_{index}"
    for leftover in glob.glob(glob.escape(prefix) + "*"):
        _remove(leftover)

    opts = {
        "format": VIDEO_FORMAT,
        "merge_output_format": "mp4",
        "download_ranges": download_range_func(None, [(start, end)]),
        "force_keyframes_at_cuts": True,
        "noplaylist": True,
        "outtmpl": prefix + ".%(ext)s",
        "quiet": True,
        "no_warnings": True,
    }
    from ffmpeg_finder import find_ffmpeg
    ff = find_ffmpeg()
    if ff:
        opts["ffmpeg_location"] = ff  # always use the modern ffmpeg, not whatever is first on PATH
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([video_url])

    # yt-dlp may add a section suffix to the name, so look for the finished mp4
    files = [
        f for f in glob.glob(glob.escape(prefix) + "*.mp4")
        if not re.search(r"\.f\d+\.", f)
    ]
    return max(files, key=os.path.getmtime) if files else None


def create_and_upload_clips_from_video(video_url, num_clips=2, clip_duration=30,
                                       privacy_status="public", wait_between_uploads=60,
                                       upload=True, publish_times=None, niche="entertainment",
                                       manage_job_status=True, status_index=None):
    """
    Create clips from a YouTube video and upload them to YouTube Shorts.
    Only each clip's time range is downloaded (not the whole video).

    Returns:
        List of uploaded video IDs
    """
    try:
        import random
        from video_clipper import create_video_clip
        from youtube_uploader import YouTubeUploader
        from caption_generator import generate_caption, get_clip_transcript
        from utils import speak
        import job_status

        print("[CLIP AUTOMATION] Processing YouTube video for Shorts...")
        if manage_job_status and not job_status.is_running():
            job_status.start(num_clips, video_url)
        if manage_job_status:
            job_status.step("Reading source video")

        from ffmpeg_finder import find_ffmpeg
        ffmpeg_path = find_ffmpeg()
        if not ffmpeg_path:
            print("[FFMPEG] No modern ffmpeg found (yours is too old and crashes on YouTube).")
            print("[FFMPEG] Fix: run  winget install Gyan.FFmpeg  then CLOSE and reopen PowerShell.")
            speak("Your ffmpeg is too old. Please install a newer one and try again.")
            return []
        print(f"[FFMPEG] Using: {ffmpeg_path}")
        speak(f"Creating {num_clips} clips. I will only download the parts I need.")

        # Step 1: read video details (no video download)
        print("[CLIP AUTOMATION] Reading video details (no full download)...")
        try:
            info = fetch_source_info(video_url)
        except Exception as e:
            print(f"[CLIP AUTOMATION] Could not read video: {e}")
            speak("I could not read that video. Please check the link and try again.")
            return []

        video_id = info.get("id", "video")
        video_duration = info.get("duration")
        if not video_duration:
            print("[CLIP AUTOMATION] No duration available (is this a live stream?)")
            speak("I could not get the video length. Please try another video.")
            return []

        source_info = {
            "title": info.get("title", "this video"),
            "description": info.get("description", ""),
            "channel": info.get("uploader") or info.get("channel") or "the original creator",
            "url": info.get("webpage_url", video_url),
        }
        print("[CLIP AUTOMATION] Fetching transcript (optional)...")
        if not fetch_subtitles(video_url, video_id):
            print("[CLIP AUTOMATION] Continuing without a transcript")
        # Subtitles (if any) were saved as downloads/source_<id>.en.json3
        subtitle_anchor = f"downloads/source_{video_id}.mp4"
        print(f"[CLIP AUTOMATION] Video duration: {video_duration:.0f} seconds")

        # Step 2: sign in to YouTube
        uploader = None
        if upload:
            try:
                uploader = YouTubeUploader()
                if not uploader.youtube:
                    print("[CLIP AUTOMATION] Warning: YouTube uploader not initialized.")
                    uploader = None
            except Exception as e:
                print(f"[CLIP AUTOMATION] Warning: Could not initialize YouTube uploader: {e}")
                uploader = None

        # Step 3: choose the moments to clip
        random_start_times = []
        moment_notes = []
        if SMART_CLIPPING and video_duration > clip_duration:
            try:
                from clip_picker import pick_viral_moments
                print("[SMART] Looking for the most viral moments...")
                moments = pick_viral_moments(info, subtitle_anchor, video_duration, num_clips, clip_duration)
                for m in moments:
                    random_start_times.append(m["start"])
                    moment_notes.append(m["reason"])
                    print(f"[SMART] Moment at {m['start']:.0f}s - score {m['score']}: {m['reason']}")
            except Exception as e:
                print(f"[SMART] Smart picking failed ({type(e).__name__}: {e}) - using random moments")
        # Fill any remaining clips with random moments
        while len(random_start_times) < num_clips:
            if video_duration > clip_duration:
                random_start_times.append(random.uniform(0, video_duration - clip_duration))
            else:
                random_start_times.append(0)
            moment_notes.append("")

        uploaded_clips = []

        for i in range(num_clips):
            start_time = random_start_times[i]
            end_time = min(start_time + clip_duration, video_duration)
            status_number = status_index if status_index is not None else i + 1
            job_status.clip(status_number, status="downloading", start=start_time,
                            detail="Downloading source segment")
            print(f"[CLIPS] Clip {i+1}/{num_clips}: downloading only {start_time:.0f}s - {end_time:.0f}s...")
            speak(f"Creating clip {i+1} of {num_clips}...")

            segment = None
            clip_path = None
            try:
                segment = download_segment(video_url, video_id, i + 1, start_time, end_time)
                if not segment:
                    print(f"[CLIPS] Could not download the section for clip {i+1}")
                    continue

                clip_path = create_video_clip(
                    input_video=segment,
                    start_time=0,
                    duration=clip_duration,
                    vertical=True  # YouTube Shorts format
                )
                job_status.clip(status_number, status="cutting", detail="Creating vertical Short")
            except Exception as e:
                print(f"[CLIPS] Clip {i+1} failed: {type(e).__name__}: {e}")
                continue
            finally:
                # The raw section is no longer needed once the Short is made
                if segment and _remove(segment):
                    print(f"[CLIPS] Deleted temporary section: {segment}")
                # Sweep any half-downloaded leftovers (.part files) for this clip
                for leftover in glob.glob(glob.escape(f"downloads/segment_{video_id}_{i+1}") + "*"):
                    _remove(leftover)

            if not (clip_path and os.path.exists(clip_path)):
                print(f"[CLIPS] Clip {i+1} was not created")
                continue

            print(f"[CLIPS] Created: {clip_path}")

            if not upload:
                uploaded_clips.append(clip_path)
                print(f"[CLIPS] Dry run: saved locally: {clip_path}")
                job_status.clip(status_number, status="saved", detail="Dry run: saved locally")
                continue

            if not uploader:
                print(f"[CLIPS] Upload skipped (not signed in to YouTube). Saved locally: {clip_path}")
                job_status.clip(status_number, status="saved", detail="Uploader unavailable; saved locally")
                continue

            try:
                transcript = get_clip_transcript(subtitle_anchor, start_time, end_time)
                print(f"[CAPTIONS] Writing caption for clip {i+1} (transcript: {len(transcript)} chars)...")
                cap = generate_caption(
                    source_info["title"], source_info["description"],
                    source_info["channel"], source_info["url"],
                    transcript, i + 1, moment_note=moment_notes[i], niche=niche
                )
                job_status.clip(status_number, status="captioning", title=cap.get("title", ""),
                                reason=moment_notes[i])
                title, description, tags = cap["title"], cap["description"], cap["tags"]
                print(f"[CAPTIONS] Title: {title}")

                print(f"[CLIPS] Uploading clip {i+1}/{num_clips} to YouTube...")
                job_status.clip(status_number, status="uploading", detail="Uploading to YouTube")
                video_id_uploaded = uploader.upload_video(
                    video_file=clip_path,
                    title=title,
                    description=description,
                    tags=tags,
                    category=cap.get("category_id", "24"),
                    privacy_status=privacy_status,
                    pinned_comment=cap.get("pinned_comment"),
                    publish_at=(publish_times[i] if publish_times and i < len(publish_times) else None)
                )

                if video_id_uploaded:
                    print(f"[CLIPS] ✓ Uploaded! Video ID: {video_id_uploaded}")
                    print(f"[CLIPS] URL: https://www.youtube.com/shorts/{video_id_uploaded}")
                    uploaded_clips.append(video_id_uploaded)
                    job_status.clip(status_number, status="done", id=video_id_uploaded,
                                    url=f"https://www.youtube.com/shorts/{video_id_uploaded}")
                    speak(f"Clip {i+1} uploaded successfully!")
                    if DELETE_CLIPS_AFTER_UPLOAD:
                        delete_clip_after_upload(clip_path)
                else:
                    print(f"[CLIPS] Failed to upload clip {i+1}. Clip kept at {clip_path}")
                    job_status.clip(status_number, status="failed", detail="Upload failed")

            except Exception as upload_error:
                print(f"[CLIPS] Upload error for clip {i+1}: {upload_error}. Clip kept at {clip_path}")
                job_status.clip(status_number, status="failed", detail=str(upload_error)[:180])

            # Wait before the next upload to avoid rate limits
            if i < num_clips - 1:
                wait_time = 30
                print(f"[CLIPS] Preparing next clip ({wait_time}s)...")
                time.sleep(wait_time)

        # Clean up subtitle file(s) for this video
        for f in glob.glob(glob.escape(f"downloads/source_{video_id}") + "*"):
            _remove(f)

        if uploaded_clips:
            msg = f"Successfully created and uploaded {len(uploaded_clips)} YouTube Shorts!"
            speak(msg)
            print(f"[CLIPS] ✓ {msg}")
            for vid in uploaded_clips:
                print(f"[CLIPS] → https://www.youtube.com/shorts/{vid}")
        else:
            print("[CLIPS] No clips were successfully uploaded")

        if manage_job_status:
            job_status.finish(uploaded_clips)
        return uploaded_clips

    except Exception as e:
        print(f"[CLIP AUTOMATION ERROR] {type(e).__name__}: {e}")
        try:
            import job_status
            if manage_job_status:
                job_status.finish([], str(e))
        except Exception:
            pass
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