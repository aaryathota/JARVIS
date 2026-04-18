"""
YouTube Uploader - Handle video uploads to YouTube with authentication
"""
import pickle
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
import json
from datetime import datetime, timedelta

# YouTube API scopes
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

class YouTubeUploader:
    def __init__(self, client_secrets_file="youtube_credentials.json"):
        """Initialize YouTube uploader with OAuth credentials"""
        self.client_secrets_file = client_secrets_file
        self.credentials = None
        self.youtube = None
        self.setup_youtube_client()
    
    def setup_youtube_client(self):
        """Authenticate and setup YouTube API client"""
        try:
            # Load existing credentials if available
            if os.path.exists("youtube_token.pickle"):
                with open("youtube_token.pickle", "rb") as token:
                    self.credentials = pickle.load(token)
                print("[YOUTUBE] Loaded existing credentials")
            else:
                print("[YOUTUBE] No existing token, creating new flow...")
            
            # Refresh if needed
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                self.credentials.refresh(Request())
                print("[YOUTUBE] Credentials refreshed")
            
            # If no credentials, do OAuth flow
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired:
                    self.credentials.refresh(Request())
                else:
                    self.authenticate_user()
            
            # Save credentials for next time
            if self.credentials:
                with open("youtube_token.pickle", "wb") as token:
                    pickle.dump(self.credentials, token)
            
            # Build YouTube API client
            if self.credentials:
                self.youtube = build("youtube", "v3", credentials=self.credentials)
                print("[YOUTUBE] ✓ YouTube client ready")
                return True
            
            return False
        
        except Exception as e:
            print(f"[YOUTUBE SETUP ERROR] {str(e)}")
            return False
    
    def authenticate_user(self):
        """Authenticate user and get credentials"""
        try:
            if not os.path.exists(self.client_secrets_file):
                print(f"[YOUTUBE AUTH] Error: {self.client_secrets_file} not found")
                print("[YOUTUBE AUTH] Please save your client_id and client_secret to this file")
                return False
            
            flow = InstalledAppFlow.from_client_secrets_file(
                self.client_secrets_file, SCOPES)
            
            # Run local server for authentication
            self.credentials = flow.run_local_server(port=9999, open_browser=True)
            print("[YOUTUBE] ✓ User authenticated successfully")
            return True
        
        except Exception as e:
            print(f"[YOUTUBE AUTH ERROR] {str(e)}")
            return False
    
    def upload_video(self, video_file, title, description, tags=None, category="25", 
                    privacy_status="public", playlist_id=None):
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
            print("[YOUTUBE] Error: YouTube client not initialized")
            return None
        
        if not os.path.exists(video_file):
            print(f"[YOUTUBE] Error: File not found: {video_file}")
            return None
        
        try:
            print(f"[YOUTUBE] Uploading: {title}")
            
            # Video metadata
            body = {
                "snippet": {
                    "title": title[:100],
                    "description": description[:5000],
                    "tags": (tags or [])[:500],
                    "categoryId": category,
                    "defaultLanguage": "en",
                    "defaultAudioLanguage": "en"
                },
                "status": {
                    "privacyStatus": privacy_status,
                    "notifySubscribers": False,
                    "madeForKids": False
                }
            }
            
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
            while response is None:
                try:
                    status, response = request.next_chunk()
                    if status:
                        progress = int(status.progress() * 100)
                        print(f"[YOUTUBE] Upload progress: {progress}%")
                except HttpError as e:
                    print(f"[YOUTUBE] Upload error: {e}")
                    return None
            
            video_id = response.get("id")
            print(f"[YOUTUBE] ✓ Video uploaded successfully!")
            print(f"[YOUTUBE] Video ID: {video_id}")
            print(f"[YOUTUBE] URL: https://www.youtube.com/watch?v={video_id}")
            
            # Add to playlist if specified
            if playlist_id and video_id:
                self.add_to_playlist(playlist_id, video_id)
            
            return video_id
        
        except HttpError as e:
            print(f"[YOUTUBE UPLOAD ERROR] {e}")
            print(f"Error details: {e.content.decode('utf-8')}")
            return None
        
        except Exception as e:
            print(f"[YOUTUBE ERROR] {str(e)}")
            return None
    
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
            print(f"[YOUTUBE] ✓ Video added to playlist: {playlist_id}")
            return True
        
        except Exception as e:
            print(f"[YOUTUBE PLAYLIST ERROR] {str(e)}")
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
            print(f"[YOUTUBE] ✓ Playlist created: {title}")
            return playlist_id
        
        except Exception as e:
            print(f"[YOUTUBE PLAYLIST CREATE ERROR] {str(e)}")
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
                print(f"[YOUTUBE] Channel: {info['title']}")
                return info
            
            return None
        
        except Exception as e:
            print(f"[YOUTUBE CHANNEL ERROR] {str(e)}")
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
                print(f"[YOUTUBE] ✓ Video metadata updated: {video_id}")
                return True
            
            return False
        
        except Exception as e:
            print(f"[YOUTUBE UPDATE ERROR] {str(e)}")
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
        
        with open("youtube_credentials.json", "w") as f:
            json.dump(credentials_data, f, indent=2)
        
        print("[YOUTUBE] ✓ Credentials file created: youtube_credentials.json")
        return True
    
    except Exception as e:
        print(f"[YOUTUBE CREDENTIALS ERROR] {str(e)}")
        return False


if __name__ == "__main__":
    # Test YouTube uploader
    print("Testing YouTube uploader...")
    
    # Re example
    # setup_youtube_credentials_file("your_client_id", "your_client_secret")
    # uploader = YouTubeUploader()
    # video_id = uploader.upload_video(
    #     "test_video.mp4",
    #     "Test Video Title",
    #     "Test video description",
    #     tags=["test", "video"]
    # )
