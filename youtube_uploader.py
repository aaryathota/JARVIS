"""
YouTube Uploader - Handle video uploads to YouTube with authentication
"""
from job_status import say
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
import json
import time
from db import consume_quota
from datetime import datetime, timedelta

CORE_HASHTAGS = ["shorts", "youtubeshorts", "viral", "trending"]
UPLOAD_QUOTA_UNITS = 1600

# Files live next to this script, no matter which folder JARVIS is started from
_HERE = os.path.dirname(os.path.abspath(__file__))
_TOKEN_FILE = os.path.join(_HERE, "token.json")

# YouTube API scopes
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

class YouTubeUploader:
    def __init__(self, client_secrets_file=os.path.join(_HERE, "youtube_credentials.json")):
        """Initialize YouTube uploader with OAuth credentials"""
        self.client_secrets_file = client_secrets_file
        self.credentials = None
        self.youtube = None
        self.setup_youtube_client()
    
    def setup_youtube_client(self):
        """Authenticate and setup YouTube API client"""
        try:
            # Load existing credentials if available
            if os.path.exists(_TOKEN_FILE):
                self.credentials = Credentials.from_authorized_user_file(_TOKEN_FILE, SCOPES)
                say("[YOUTUBE] Loaded existing credentials")
            else:
                say("[YOUTUBE] No existing token, creating new flow...")
            
            # Refresh if needed
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                try:
                    self.credentials.refresh(Request())
                    say("[YOUTUBE] Credentials refreshed")
                except Exception as refresh_error:
                    # Token revoked/expired (e.g. 7-day limit in Testing mode): sign in again automatically
                    say(f"[YOUTUBE] Saved login no longer valid ({refresh_error}). Signing in again...")
                    self.credentials = None
                    if os.path.exists(_TOKEN_FILE):
                        os.remove(_TOKEN_FILE)
            
            # If no credentials, do OAuth flow
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired:
                    self.credentials.refresh(Request())
                else:
                    self.authenticate_user()
            
            # Save credentials for next time
            if self.credentials:
                with open(_TOKEN_FILE, "w", encoding="utf-8") as token:
                    token.write(self.credentials.to_json())
            
            # Build YouTube API client
            if self.credentials:
                self.youtube = build("youtube", "v3", credentials=self.credentials)
                say("[YOUTUBE] ✓ YouTube client ready")
                return True
            
            return False
        
        except Exception as e:
            say(f"[YOUTUBE SETUP ERROR] {str(e)}")
            return False
    
    def authenticate_user(self):
        """Authenticate user and get credentials"""
        try:
            if not os.path.exists(self.client_secrets_file):
                say(f"[YOUTUBE AUTH] Error: {self.client_secrets_file} not found")
                say("[YOUTUBE AUTH] Please save your client_id and client_secret to this file")
                return False
            
            flow = InstalledAppFlow.from_client_secrets_file(
                self.client_secrets_file, SCOPES)
            
            # Run local server for authentication
            self.credentials = flow.run_local_server(port=9999, open_browser=True)
            say("[YOUTUBE] ✓ User authenticated successfully")
            return True
        
        except Exception as e:
            say(f"[YOUTUBE AUTH ERROR] {str(e)}")
            return False
    
    def upload_video(self, video_file, title, description, tags=None, category="24",
                    privacy_status="public", playlist_id=None, publish_at=None,
                    pinned_comment=None, video_format="short"):
        """
        Upload video to YouTube
        
        Args:
            video_file: Path to video file
            title: Video title
            description: Video description
            tags: List of tags/hashtags
            category: Video category (25 = News & Politics, etc.)
            privacy_status: "public", "private", or "unlisted"
            playlist_id: Optional playlist to add video to
        
        Returns:
            Video ID or None
        """
        if not self.youtube:
            say("[YOUTUBE] Error: YouTube client not initialized")
            return None
        
        if not os.path.exists(video_file):
            say(f"[YOUTUBE] Error: File not found: {video_file}")
            return None
        
        try:
            say(f"[YOUTUBE] Uploading: {title}")
            quota_limit = int(os.getenv("YOUTUBE_DAILY_QUOTA_LIMIT", "10000"))
            if not consume_quota(UPLOAD_QUOTA_UNITS, quota_limit):
                say("[YOUTUBE] Daily API quota would be exceeded; upload deferred")
                return None

            upload_tags = []
            is_short = video_format != "video"  # proper videos don't get the Shorts/viral tags
            for tag in (CORE_HASHTAGS if is_short else []) + (tags or []):
                clean_tag = str(tag).lower().lstrip("#").strip()
                if clean_tag and clean_tag not in upload_tags:
                    upload_tags.append(clean_tag)
            hashtag_line = " ".join(f"#{tag}" for tag in upload_tags[:15 if is_short else 3])
            if hashtag_line and hashtag_line not in description:
                description = f"{description.rstrip()}\n\n{hashtag_line}"
            
            # Video metadata
            body = {
                "snippet": {
                    "title": title[:100],
                    "description": description[:5000],
                    "tags": upload_tags[:500],
                    "categoryId": category,
                    "defaultLanguage": "en",
                    "defaultAudioLanguage": "en"
                },
                "status": {
                    "privacyStatus": "private" if publish_at else privacy_status,
                    "notifySubscribers": False,
                    "madeForKids": False
                }
            }
            if publish_at:
                body["status"]["publishAt"] = publish_at
            
            # Schedule upload for later if needed
            # body["status"]["publishAt"] = (datetime.now() + timedelta(hours=1)).isoformat() + "Z"
            
            # Media upload
            media = MediaFileUpload(
                video_file,
                chunksize=1024*1024,  # 1MB chunks
                resumable=True,
                mimetype="video/mp4"
            )
            
            # Execute upload with resumable protocol
            request = self.youtube.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media,
                onBehalfOfContentOwner=None
            )
            
            # Upload with progress tracking
            response = None
            retries = 0
            while response is None:
                try:
                    status, response = request.next_chunk()
                    retries = 0
                    if status:
                        progress = int(status.progress() * 100)
                        say(f"[YOUTUBE] Upload progress: {progress}%")
                except HttpError as e:
                    status_code = getattr(e.resp, "status", 0)
                    if status_code in (429, 500, 502, 503, 504) and retries < 5:
                        delay = min(60, 2 ** retries)
                        retries += 1
                        say(f"[YOUTUBE] Temporary upload error ({status_code}); retrying in {delay}s")
                        time.sleep(delay)
                        continue
                    say(f"[YOUTUBE] Upload error ({status_code or 'unknown'}): {e}")
                    return None
            
            video_id = response.get("id")
            say(f"[YOUTUBE] ✓ Video uploaded successfully!")
            say(f"[YOUTUBE] Video ID: {video_id}")
            say(f"[YOUTUBE] URL: https://www.youtube.com/watch?v={video_id}")
            
            # Add to playlist if specified
            if playlist_id and video_id:
                self.add_to_playlist(playlist_id, video_id)
            if pinned_comment and video_id:
                self.post_pinned_comment(video_id, pinned_comment)
            
            return video_id
        
        except HttpError as e:
            if getattr(e.resp, "status", 0) == 403:
                say("[YOUTUBE] Public upload rejected with 403; check API project verification and channel permissions")
            say(f"[YOUTUBE UPLOAD ERROR] {e}")
            say(f"Error details: {e.content.decode('utf-8')}")
            return None

        except Exception as e:
            say(f"[YOUTUBE ERROR] {str(e)}")
            return None

    def post_pinned_comment(self, video_id, text):
        """Post a discussion prompt; pinning requires an additional API action."""
        try:
            request = self.youtube.commentThreads().insert(
                part="snippet",
                body={"snippet": {"videoId": video_id, "topLevelComment": {
                    "snippet": {"textOriginal": text[:10000]}
                }}}
            )
            response = request.execute()
            comment_id = response.get("snippet", {}).get("topLevelComment", {}).get("id")
            if comment_id:
                try:
                    self.youtube.comments().setModerationStatus(
                        id=comment_id, moderationStatus="published"
                    ).execute()
                except Exception:
                    pass
            say(f"[YOUTUBE] Comment posted for {video_id}")
            return True
        except Exception as error:
            say(f"[YOUTUBE COMMENT] Could not post comment: {error}")
            return False
    
    def add_to_playlist(self, playlist_id, video_id):
        """Add video to a YouTube playlist"""
        try:
            request = self.youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": video_id
                        }
                    }
                }
            )
            request.execute()
            say(f"[YOUTUBE] ✓ Video added to playlist: {playlist_id}")
            return True
        
        except Exception as e:
            say(f"[YOUTUBE PLAYLIST ERROR] {str(e)}")
            return False
    
    def create_playlist(self, title, description=""):
        """Create a new YouTube playlist"""
        try:
            body = {
                "snippet": {
                    "title": title,
                    "description": description
                },
                "status": {
                    "privacyStatus": "public"
                }
            }
            
            request = self.youtube.playlists().insert(
                part="snippet,status",
                body=body
            )
            response = request.execute()
            playlist_id = response.get("id")
            say(f"[YOUTUBE] ✓ Playlist created: {title}")
            return playlist_id
        
        except Exception as e:
            say(f"[YOUTUBE PLAYLIST CREATE ERROR] {str(e)}")
            return None
    
    def get_channel_info(self):
        """Get information about authenticated user's channel"""
        try:
            request = self.youtube.channels().list(
                part="snippet,statistics,contentDetails",
                mine=True
            )
            response = request.execute()
            
            if response.get("items"):
                channel = response["items"][0]
                info = {
                    "title": channel["snippet"]["title"],
                    "description": channel["snippet"]["description"],
                    "subscribers": channel["statistics"].get("subscriberCount", "N/A"),
                    "video_count": channel["statistics"].get("videoCount", "0"),
                    "view_count": channel["statistics"].get("viewCount", "0")
                }
                say(f"[YOUTUBE] Channel: {info['title']}")
                return info
            
            return None
        
        except Exception as e:
            say(f"[YOUTUBE CHANNEL ERROR] {str(e)}")
            return None
    
    def update_video_metadata(self, video_id, title=None, description=None, tags=None):
        """Update existing video metadata"""
        try:
            request = self.youtube.videos().list(
                part="snippet",
                id=video_id
            )
            response = request.execute()
            
            if response.get("items"):
                video = response["items"][0]
                snippet = video["snippet"]
                
                if title:
                    snippet["title"] = title
                if description:
                    snippet["description"] = description
                if tags:
                    snippet["tags"] = tags
                
                update_request = self.youtube.videos().update(
                    part="snippet",
                    body=video
                )
                update_request.execute()
                say(f"[YOUTUBE] ✓ Video metadata updated: {video_id}")
                return True
            
            return False
        
        except Exception as e:
            say(f"[YOUTUBE UPDATE ERROR] {str(e)}")
            return False


def setup_youtube_credentials_file(client_id, client_secret, redirect_uri="http://localhost:8080"):
    """Create YouTube credentials file from client ID and secret"""
    try:
        credentials_data = {
            "installed": {
                "client_id": client_id,
                "project_id": "your-project",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_secret": client_secret,
                "redirect_uris": [redirect_uri]
            }
        }
        
        with open(os.path.join(_HERE, "youtube_credentials.json"), "w") as f:
            json.dump(credentials_data, f, indent=2)
        
        say("[YOUTUBE] ✓ Credentials file created: youtube_credentials.json")
        return True
    
    except Exception as e:
        say(f"[YOUTUBE CREDENTIALS ERROR] {str(e)}")
        return False


if __name__ == "__main__":
    # Test YouTube uploader
    say("Testing YouTube uploader...")
    
    # Re example
    # setup_youtube_credentials_file("your_client_id", "your_client_secret")
    # uploader = YouTubeUploader()
    # video_id = uploader.upload_video(
    #     "test_video.mp4",
    #     "Test Video Title",
    #     "Test video description",
    #     tags=["test", "video"]
    # )