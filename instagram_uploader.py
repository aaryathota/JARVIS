"""
JARVIS Instagram Uploader - Automatically upload videos and images to Instagram
"""

import os
import json
import time
import threading
import logging
from datetime import datetime
from pathlib import Path

# Suppress instagrapi logging and set UTF-8 encoding
logging.getLogger('instagrapi').setLevel(logging.CRITICAL)
os.environ['PYTHONIOENCODING'] = 'utf-8'

try:
    from instagrapi import Client
except ImportError:
    print("[INSTAGRAM ERROR] instagrapi not installed. Run: pip install instagrapi")
    Client = None

class InstagramUploader:
    def __init__(self):
        """Initialize Instagram uploader with credentials"""
        self.client = None
        self.username = None
        self.password = None
        self.is_authenticated = False
        self.upload_history = []
        
        if not Client:
            print("[INSTAGRAM] instagrapi library not available")
            return
        
        self.load_credentials()
        self.authenticate()
    
    def load_credentials(self):
        """Load Instagram credentials from file"""
        try:
            # Try to load from credentials.json
            if os.path.exists('credentials.json'):
                with open('credentials.json', 'r', encoding='utf-8') as f:
                    creds = json.load(f)
                    self.username = creds.get('instagram_username')
                    self.password = creds.get('instagram_password')
            
            # Try to load from environment or config
            if not self.username:
                self.username = os.getenv('INSTAGRAM_USERNAME')
                self.password = os.getenv('INSTAGRAM_PASSWORD')
            
            if self.username and self.password:
                print(f"[INSTAGRAM] Credentials loaded for: {self.username}")
            else:
                print("[INSTAGRAM] No credentials found. Set INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD")
        
        except Exception as e:
            print(f"[INSTAGRAM ERROR] Failed to load credentials: {e}")
    
    def authenticate(self):
        """Authenticate with Instagram"""
        try:
            if not self.username or not self.password:
                print("[INSTAGRAM] Cannot authenticate - missing credentials")
                return False
            
            if not Client:
                print("[INSTAGRAM] Client not available")
                return False
            
            print("[INSTAGRAM] Logging in to Instagram...")
            self.client = Client()
            
            # Suppress output during login
            import io
            import sys
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            
            try:
                # Redirect output to suppress instagrapi's verbose output
                sys.stdout = io.StringIO()
                sys.stderr = io.StringIO()
                self.client.login(self.username, self.password)
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr
            
            self.is_authenticated = True
            print(f"[INSTAGRAM] [OK] Authenticated as {self.username}")
            return True
        
        except Exception as e:
            self.is_authenticated = False
            error_msg = str(e)[:100]  # Truncate long error messages
            print(f"[INSTAGRAM ERROR] Authentication failed: {error_msg}")
            print("[INSTAGRAM] Tip: Ensure credentials are correct in credentials.json")
            return False
    
    def upload_video(self, video_path, caption="", hashtags=""):
        """Upload a video to Instagram (Reel)"""
        try:
            if not self.is_authenticated:
                print("[INSTAGRAM] Not authenticated - cannot upload")
                return False
            
            if not os.path.exists(video_path):
                print(f"[INSTAGRAM] Video not found: {video_path}")
                return False
            
            # Combine caption and hashtags
            full_caption = f"{caption}\n\n{hashtags}" if hashtags else caption
            
            print(f"[INSTAGRAM] Uploading video: {video_path}")
            if full_caption:
                print(f"[INSTAGRAM] Caption: {full_caption[:50]}...")
            
            # Upload as Reel (video)
            media = self.client.video_upload(
                video_path,
                caption=full_caption
            )
            
            if media:
                upload_info = {
                    'timestamp': datetime.now().isoformat(),
                    'type': 'video',
                    'file': video_path,
                    'caption': full_caption,
                    'media_id': media.pk,
                    'url': f"https://instagram.com/p/{media.pk}/"
                }
                self.upload_history.append(upload_info)
                self.save_upload_history()
                
                print(f"[INSTAGRAM] [OK] Video uploaded successfully!")
                print(f"[INSTAGRAM] URL: {upload_info['url']}")
                return True
            else:
                print("[INSTAGRAM] Upload failed - no media returned")
                return False
        
        except Exception as e:
            error_msg = str(e)[:100]
            print(f"[INSTAGRAM ERROR] Video upload failed: {error_msg}")
            return False
    
    def upload_image(self, image_path, caption="", hashtags=""):
        """Upload an image to Instagram"""
        try:
            if not self.is_authenticated:
                print("[INSTAGRAM] Not authenticated - cannot upload")
                return False
            
            if not os.path.exists(image_path):
                print(f"[INSTAGRAM] Image not found: {image_path}")
                return False
            
            # Combine caption and hashtags
            full_caption = f"{caption}\n\n{hashtags}" if hashtags else caption
            
            print(f"[INSTAGRAM] Uploading image: {image_path}")
            if full_caption:
                print(f"[INSTAGRAM] Caption: {full_caption[:50]}...")
            
            # Upload photo
            media = self.client.photo_upload(
                image_path,
                caption=full_caption
            )
            
            if media:
                upload_info = {
                    'timestamp': datetime.now().isoformat(),
                    'type': 'image',
                    'file': image_path,
                    'caption': full_caption,
                    'media_id': media.pk,
                    'url': f"https://instagram.com/p/{media.pk}/"
                }
                self.upload_history.append(upload_info)
                self.save_upload_history()
                
                print(f"[INSTAGRAM] [OK] Image uploaded successfully!")
                print(f"[INSTAGRAM] URL: {upload_info['url']}")
                return True
            else:
                print("[INSTAGRAM] Upload failed - no media returned")
                return False
        
        except Exception as e:
            error_msg = str(e)[:100]
            print(f"[INSTAGRAM ERROR] Image upload failed: {error_msg}")
            return False
    
    def upload_carousel(self, media_paths, caption="", hashtags=""):
        """Upload multiple images/videos as carousel"""
        try:
            if not self.is_authenticated:
                print("[INSTAGRAM] Not authenticated")
                return False
            
            # Verify all files exist
            for path in media_paths:
                if not os.path.exists(path):
                    print(f"[INSTAGRAM] File not found: {path}")
                    return False
            
            full_caption = f"{caption}\n\n{hashtags}" if hashtags else caption
            
            print(f"[INSTAGRAM] Uploading carousel with {len(media_paths)} items...")
            
            # Upload carousel
            media = self.client.album_upload(
                media_paths,
                caption=full_caption
            )
            
            if media:
                upload_info = {
                    'timestamp': datetime.now().isoformat(),
                    'type': 'carousel',
                    'files': media_paths,
                    'caption': full_caption,
                    'media_id': media.pk,
                    'url': f"https://instagram.com/p/{media.pk}/"
                }
                self.upload_history.append(upload_info)
                self.save_upload_history()
                
                print(f"[INSTAGRAM] [OK] Carousel uploaded successfully!")
                print(f"[INSTAGRAM] URL: {upload_info['url']}")
                return True
            else:
                print("[INSTAGRAM] Upload failed")
                return False
        
        except Exception as e:
            error_msg = str(e)[:100]
            print(f"[INSTAGRAM ERROR] Carousel upload failed: {error_msg}")
            return False
    
    def upload_story(self, media_path, caption=""):
        """Upload to Instagram Story (expires after 24 hours)"""
        try:
            if not self.is_authenticated:
                print("[INSTAGRAM] Not authenticated")
                return False
            
            if not os.path.exists(media_path):
                print(f"[INSTAGRAM] File not found: {media_path}")
                return False
            
            print(f"[INSTAGRAM] Uploading to Story: {media_path}")
            
            # Upload story
            media = self.client.story_upload(media_path)
            
            if media:
                upload_info = {
                    'timestamp': datetime.now().isoformat(),
                    'type': 'story',
                    'file': media_path,
                    'expires_at': (datetime.now().timestamp() + 86400),  # 24 hours
                }
                self.upload_history.append(upload_info)
                self.save_upload_history()
                
                print(f"[INSTAGRAM] [OK] Story uploaded successfully!")
                print(f"[INSTAGRAM] Expires in 24 hours")
                return True
            else:
                print("[INSTAGRAM] Story upload failed")
                return False
        
        except Exception as e:
            error_msg = str(e)[:100]
            print(f"[INSTAGRAM ERROR] Story upload failed: {error_msg}")
            return False
    
    def schedule_upload(self, video_path, caption="", hashtags="", upload_type="video"):
        """Schedule upload for later"""
        try:
            scheduled_info = {
                'timestamp': datetime.now().isoformat(),
                'type': upload_type,
                'file': video_path,
                'caption': caption,
                'hashtags': hashtags,
                'status': 'scheduled'
            }
            
            print(f"[INSTAGRAM] Upload scheduled:")
            print(f"   File: {video_path}")
            print(f"   Type: {upload_type}")
            print(f"   Caption: {caption}")
            
            return scheduled_info
        
        except Exception as e:
            print(f"[INSTAGRAM ERROR] Scheduling failed: {e}")
            return False
    
    def get_upload_history(self):
        """Get all uploaded media history"""
        try:
            if os.path.exists('instagram_upload_history.json'):
                with open('instagram_upload_history.json', 'r') as f:
                    return json.load(f)
            return []
        except:
            return []
    
    def save_upload_history(self):
        """Save upload history to file"""
        try:
            with open('instagram_upload_history.json', 'w') as f:
                json.dump(self.upload_history, f, indent=2)
        except Exception as e:
            print(f"[INSTAGRAM ERROR] Failed to save history: {e}")
    
    def get_account_stats(self):
        """Get account statistics"""
        try:
            if not self.is_authenticated:
                return None
            
            user_info = self.client.account_info()
            
            stats = {
                'username': user_info.username,
                'full_name': user_info.full_name,
                'follower_count': user_info.follower_count,
                'following_count': user_info.following_count,
                'media_count': user_info.media_count,
                'biography': user_info.biography,
                'website': user_info.website
            }
            
            return stats
        
        except Exception as e:
            print(f"[INSTAGRAM ERROR] Failed to get stats: {e}")
            return None


# Note: Create instance on-demand in instagram_clips.py to avoid slow authentication during module import
