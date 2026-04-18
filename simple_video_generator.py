"""
Simple Video Generator - Generate short videos for YouTube Shorts and Instagram Reels
Uses MoviePy to create simple but engaging videos from ideas
"""

import os
import random
from datetime import datetime
from pathlib import Path

# Create videos directory if it doesn't exist
os.makedirs("videos", exist_ok=True)

def generate_video_from_idea(idea):
    """
    Generate a video from a video idea dict
    
    Args:
        idea: Dict containing title, description, tags, etc.
    
    Returns:
        Path to generated video file or None
    """
    try:
        from moviepy.editor import ColorClip, TextClip, concatenate_videoclips, CompositeVideoClip
        from moviepy.editor import AudioFileClip
        
        title = idea.get("title", "Untitled")
        description = idea.get("description", "")
        
        print(f"[VIDEO GEN] Generating video: {title}")
        
        # Create a simple video with text and background
        # Duration: 30-45 seconds
        duration = random.randint(30, 45)
        
        # Random background color
        bg_color = (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))
        
        # Create background clip
        bg_clip = ColorClip(size=(1920, 1080), color=bg_color).set_duration(duration)
        
        # Create title text clip
        try:
            title_clip = TextClip(
                txt=title[:50],  # Limit title length
                fontsize=70,
                color="white",
                font="Arial",
                method="caption",
                size=(1800, 300)
            ).set_duration(duration).set_position(("center", "center"))
        except Exception as e:
            print(f"[VIDEO GEN] Warning: Could not create title clip: {e}")
            # Fallback: create a simpler version
            title_clip = None
        
        # Create description text clip if available
        desc_clip = None
        if description:
            try:
                desc_clip = TextClip(
                    txt=description[:100],  # Limit description length
                    fontsize=40,
                    color="lightyellow",
                    font="Arial",
                    method="caption",
                    size=(1800, 200)
                ).set_duration(duration).set_position(("center", "bottom"))
            except Exception as e:
                print(f"[VIDEO GEN] Warning: Could not create description clip: {e}")
        
        # Compose clips
        if title_clip and desc_clip:
            final_clip = CompositeVideoClip([bg_clip, title_clip, desc_clip])
        elif title_clip:
            final_clip = CompositeVideoClip([bg_clip, title_clip])
        elif desc_clip:
            final_clip = CompositeVideoClip([bg_clip, desc_clip])
        else:
            final_clip = bg_clip
        
        # Generate output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"videos/video_{timestamp}.mp4"
        
        # Write video file
        print(f"[VIDEO GEN] Writing video to disk... (this may take a minute)")
        final_clip.write_videofile(
            output_path,
            fps=24,
            codec="libx264",
            audio=False,
            verbose=False,
            logger=None
        )
        
        print(f"[VIDEO GEN] ✓ Video generated: {output_path}")
        return output_path
    
    except ImportError:
        print("[VIDEO GEN] MoviePy not available, using fallback method...")
        return generate_video_from_idea_fallback(idea)
    
    except Exception as e:
        print(f"[VIDEO GEN ERROR] {type(e).__name__}: {str(e)}")
        return None


def generate_video_from_idea_fallback(idea):
    """
    Fallback video generation using FFmpeg directly
    Creates a simple video with static frame and audio
    """
    try:
        import subprocess
        import numpy as np
        from PIL import Image, ImageDraw, ImageFont
        
        title = idea.get("title", "Untitled")
        description = idea.get("description", "")
        
        print(f"[VIDEO GEN] Using FFmpeg fallback for: {title}")
        
        # Create a simple image frame
        width, height = 1920, 1080
        bg_color = (
            random.randint(50, 200),
            random.randint(50, 200),
            random.randint(50, 200)
        )
        
        img = Image.new("RGB", (width, height), bg_color)
        draw = ImageDraw.Draw(img)
        
        # Add text
        text = f"{title}\n\n{description}"
        
        # Simple text placement
        x, y = 100, 400
        draw.text((x, y), text, fill=(255, 255, 255))
        
        # Save frame as temporary image
        frame_path = "videos/temp_frame.png"
        img.save(frame_path)
        
        # Use FFmpeg to create video from image
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"videos/video_{timestamp}.mp4"
        duration = random.randint(30, 45)
        
        ffmpeg_cmd = [
            "ffmpeg",
            "-loop", "1",
            "-i", frame_path,
            "-c:v", "libx264",
            "-t", str(duration),
            "-pix_fmt", "yuv420p",
            "-y",
            output_path
        ]
        
        print(f"[VIDEO GEN] Creating {duration}s video...")
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            # Clean up temp frame
            if os.path.exists(frame_path):
                os.remove(frame_path)
            
            print(f"[VIDEO GEN] ✓ Video generated: {output_path}")
            return output_path
        else:
            print(f"[VIDEO GEN] FFmpeg error: {result.stderr[:200]}")
            return None
    
    except Exception as e:
        print(f"[VIDEO GEN FALLBACK ERROR] {str(e)}")
        return None


def generate_short_video(title="Short Clip", description="Auto-generated clip", duration=30):
    """
    Generate a short video optimized for YouTube Shorts and Instagram Reels
    
    Args:
        title: Video title
        description: Video description
        duration: Video duration in seconds (default 30s)
    
    Returns:
        Path to generated video file or None
    """
    try:
        from moviepy.editor import ColorClip, TextClip, CompositeVideoClip
        
        print(f"[SHORTS GEN] Creating short video: {title}")
        
        # YouTube Shorts aspect ratio: 9:16 (1080x1920)
        width, height = 1080, 1920
        
        # Random vibrant background color
        bg_color = (random.randint(60, 180), random.randint(60, 180), random.randint(60, 180))
        
        # Create background
        bg_clip = ColorClip(size=(width, height), color=bg_color).set_duration(duration)
        
        # Create title text
        try:
            title_clip = TextClip(
                txt=title[:40],
                fontsize=60,
                color="white",
                font="Arial",
                method="caption",
                size=(900, 400)
            ).set_duration(duration).set_position(("center", 200))
        except:
            title_clip = None
        
        # Create description text
        desc_clip = None
        if description:
            try:
                desc_clip = TextClip(
                    txt=description[:80],
                    fontsize=35,
                    color="lightyellow",
                    font="Arial",
                    method="caption",
                    size=(900, 300)
                ).set_duration(duration).set_position(("center", 1400))
            except:
                pass
        
        # Compose video
        if title_clip and desc_clip:
            final_clip = CompositeVideoClip([bg_clip, title_clip, desc_clip])
        elif title_clip:
            final_clip = CompositeVideoClip([bg_clip, title_clip])
        else:
            final_clip = bg_clip
        
        # Generate output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"videos/short_{timestamp}.mp4"
        
        print(f"[SHORTS GEN] Rendering {duration}s video...")
        final_clip.write_videofile(
            output_path,
            fps=24,
            codec="libx264",
            audio=False,
            verbose=False,
            logger=None
        )
        
        print(f"[SHORTS GEN] ✓ Short video generated: {output_path}")
        return output_path
    
    except ImportError:
        print("[SHORTS GEN] MoviePy not available, using FFmpeg fallback...")
        return generate_short_video_fallback(title, description, duration)
    
    except Exception as e:
        print(f"[SHORTS GEN ERROR] {str(e)}")
        return None


def generate_short_video_fallback(title="Short Clip", description="Auto-generated clip", duration=30):
    """
    Fallback short video generation using FFmpeg
    """
    try:
        import subprocess
        from PIL import Image, ImageDraw
        
        # Create image frame for YouTube Shorts (9:16 aspect ratio)
        width, height = 1080, 1920
        bg_color = (random.randint(60, 180), random.randint(60, 180), random.randint(60, 180))
        
        img = Image.new("RGB", (width, height), bg_color)
        draw = ImageDraw.Draw(img)
        
        # Add text
        text = f"{title}\n\n{description}"
        draw.text((50, 800), text, fill=(255, 255, 255))
        
        frame_path = "videos/temp_short_frame.png"
        img.save(frame_path)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"videos/short_{timestamp}.mp4"
        
        ffmpeg_cmd = [
            "ffmpeg",
            "-loop", "1",
            "-i", frame_path,
            "-c:v", "libx264",
            "-t", str(duration),
            "-pix_fmt", "yuv420p",
            "-y",
            output_path
        ]
        
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            if os.path.exists(frame_path):
                os.remove(frame_path)
            print(f"[SHORTS GEN] ✓ Short video generated: {output_path}")
            return output_path
        else:
            print(f"[SHORTS GEN] FFmpeg error: {result.stderr[:200]}")
            return None
    
    except Exception as e:
        print(f"[SHORTS GEN FALLBACK ERROR] {str(e)}")
        return None
