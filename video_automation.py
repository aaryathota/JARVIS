"""
Video Automation Workflow - Orchestrates video generation and YouTube uploads
"""
import os
import json
import sqlite3
from datetime import datetime, timedelta
import threading
import time

from video_ideas import generate_video_ideas, create_video_script
from simple_video_generator import generate_video_from_idea
from youtube_uploader import YouTubeUploader, setup_youtube_credentials_file
from utils import speak

# Database for tracking uploads
DB_FILE = "video_uploads.db"

def init_database():
    """Initialize SQLite database for tracking uploads"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS uploads (
                id INTEGER PRIMARY KEY,
                video_title TEXT,
                youtube_video_id TEXT,
                groq_idea_id TEXT,
                upload_date TIMESTAMP,
                status TEXT,
                view_count INTEGER DEFAULT 0,
                likes INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS video_ideas (
                id INTEGER PRIMARY KEY,
                title TEXT,
                description TEXT,
                generated_date TIMESTAMP,
                used BOOLEAN DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
        print("[VIDEO FLOW] Database initialized")
        return True
    
    except Exception as e:
        print(f"[VIDEO FLOW DB ERROR] {str(e)}")
        return False


class VideoAutomationWorkflow:
    def __init__(self, creatomate_key=None, creatomate_template=None, 
                 youtube_client_id=None, youtube_client_secret=None,
                 piapi_key=None, eleven_labs_key=None):
        """
        Initialize video automation workflow
        
        Args:
            creatomate_key: Deprecated - now using MoviePy
            creatomate_template: Deprecated - now using MoviePy
            youtube_client_id: YouTube OAuth client ID
            youtube_client_secret: YouTube OAuth client secret
            piapi_key: Pi API key (for additional features)
            eleven_labs_key: Eleven Labs API key (for voice-over)
        """
        self.piapi_key = piapi_key
        self.eleven_labs_key = eleven_labs_key
        
        # Initialize components
        init_database()
        
        # Setup YouTube
        if youtube_client_id and youtube_client_secret:
            setup_youtube_credentials_file(youtube_client_id, youtube_client_secret)
            self.youtube = YouTubeUploader()
        else:
            self.youtube = None
            print("[VIDEO FLOW] YouTube credentials not provided - skipping upload setup")
        
        self.is_running = False
        self.workflow_thread = None
    
    def save_video_idea(self, title, description):
        """Save generated video idea to database"""
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO video_ideas (title, description, generated_date, used)
                VALUES (?, ?, ?, 0)
            ''', (title, description, datetime.now()))
            
            conn.commit()
            conn.close()
            return True
        
        except Exception as e:
            print(f"[VIDEO FLOW SAVE ERROR] {str(e)}")
            return False
    
    def get_unused_idea(self):
        """Get an unused video idea from database"""
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, title, description FROM video_ideas 
                WHERE used = 0 
                LIMIT 1
            ''')
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                idea_id, title, description = result
                return {"id": idea_id, "title": title, "description": description}
            
            return None
        
        except Exception as e:
            print(f"[VIDEO FLOW FETCH ERROR] {str(e)}")
            return None
    
    def mark_idea_used(self, idea_id):
        """Mark idea as used in database"""
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('UPDATE video_ideas SET used = 1 WHERE id = ?', (idea_id,))
            
            conn.commit()
            conn.close()
            return True
        
        except Exception as e:
            print(f"[VIDEO FLOW UPDATE ERROR] {str(e)}")
            return False
    
    def log_upload(self, title, video_id, groq_idea_id=None):
        """Log successful video upload"""
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO uploads (video_title, youtube_video_id, groq_idea_id, upload_date, status)
                VALUES (?, ?, ?, ?, 'uploaded')
            ''', (title, video_id, groq_idea_id, datetime.now()))
            
            conn.commit()
            conn.close()
            return True
        
        except Exception as e:
            print(f"[VIDEO FLOW LOG ERROR] {str(e)}")
            return False
    
    def generate_and_upload_video(self, video_idea=None):
        """
        Complete workflow: Generate idea -> Create video -> Upload to YouTube
        
        Args:
            video_idea: Optional pre-generated idea dict
        
        Returns:
            Video ID if successful, None otherwise
        """
        try:
            # Step 1: Get video idea
            if not video_idea:
                print("[VIDEO FLOW] Generating new video idea...")
                ideas = generate_video_ideas(num_ideas=1, content_type="streamer")
                if not ideas:
                    print("[VIDEO FLOW] Failed to generate ideas")
                    return None
                video_idea = ideas[0]
            
            print(f"[VIDEO FLOW] Idea: {video_idea.get('title', 'Untitled')}")
            
            # Save idea to database
            self.save_video_idea(
                video_idea.get('title'),
                video_idea.get('description')
            )
            
            # Step 2: Create video using MoviePy (FREE!)
            print("[VIDEO FLOW] Creating video with MoviePy...")
            video_file = generate_video_from_idea(video_idea)
            
            if not video_file:
                print("[VIDEO FLOW] Failed to create video")
                return None
            
            print(f"[VIDEO FLOW] Video created: {video_file}")
            
            # Step 3: Upload to YouTube
            if not self.youtube:
                print("[VIDEO FLOW] YouTube not configured - skipping upload")
                return None
            
            print("[VIDEO FLOW] Uploading to YouTube...")
            
            tags = video_idea.get("tags", [])
            if isinstance(tags, str):
                tags = tags.split()
            
            video_id = self.youtube.upload_video(
                video_file=video_file,
                title=video_idea.get("title", "Untitled")[:100],
                description=video_idea.get("description", "")[:5000],
                tags=tags,
                category="25",  # Music category
                privacy_status="public"
            )
            
            if video_id:
                self.log_upload(
                    video_idea.get("title"),
                    video_id
                )
                print(f"[VIDEO FLOW] ✓ Complete! Video: https://www.youtube.com/watch?v={video_id}")
                return video_id
            
            return None
        
        except Exception as e:
            print(f"[VIDEO FLOW ERROR] {str(e)}")
            return None
    
    def batch_generate_videos(self, num_videos=3):
        """Generate and upload multiple videos"""
        results = []
        for i in range(num_videos):
            print(f"\n[VIDEO FLOW] Processing video {i+1}/{num_videos}")
            result = self.generate_and_upload_video()
            results.append(result)
            
            # Wait between uploads to avoid rate limiting
            if i < num_videos - 1:
                wait_time = 60  # 1 minute between uploads
                print(f"[VIDEO FLOW] Waiting {wait_time}s before next upload...")
                time.sleep(wait_time)
        
        print(f"\n[VIDEO FLOW] Batch complete! {len([r for r in results if r])} videos uploaded")
        return results
    
    def start_continuous_generation(self, interval_hours=24):
        """Start continuous video generation and uploading"""
        if self.is_running:
            print("[VIDEO FLOW] Already running")
            return False
        
        self.is_running = True
        interval_seconds = interval_hours * 3600
        
        def workflow_loop():
            while self.is_running:
                try:
                    print(f"\n[VIDEO FLOW] Starting scheduled generation cycle...")
                    self.generate_and_upload_video()
                    
                    print(f"[VIDEO FLOW] Next generation in {interval_hours} hour(s)")
                    time.sleep(interval_seconds)
                
                except Exception as e:
                    print(f"[VIDEO FLOW LOOP ERROR] {str(e)}")
                    time.sleep(300)  # Retry after 5 minutes
        
        self.workflow_thread = threading.Thread(target=workflow_loop, daemon=True)
        self.workflow_thread.start()
        print(f"[VIDEO FLOW] ✓ Continuous generation started (every {interval_hours} hour(s))")
        return True
    
    def stop_continuous_generation(self):
        """Stop continuous generation"""
        self.is_running = False
        print("[VIDEO FLOW] Continuous generation stopped")
    
    def get_upload_history(self, limit=10):
        """Get history of uploaded videos"""
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT video_title, youtube_video_id, upload_date, status
                FROM uploads
                ORDER BY upload_date DESC
                LIMIT ?
            ''', (limit,))
            
            results = cursor.fetchall()
            conn.close()
            
            history = []
            for row in results:
                history.append({
                    "title": row[0],
                    "video_id": row[1],
                    "date": row[2],
                    "status": row[3]
                })
            
            return history
        
        except Exception as e:
            print(f"[VIDEO FLOW HISTORY ERROR] {str(e)}")
            return []


# Global workflow instance
video_workflow = None

def initialize_video_workflow(config):
    """Initialize global video workflow with config"""
    global video_workflow
    
    try:
        video_workflow = VideoAutomationWorkflow(
            creatomate_key=config.get("creatomate_key"),
            creatomate_template=config.get("creatomate_template_id"),
            youtube_client_id=config.get("youtube_client_id"),
            youtube_client_secret=config.get("youtube_client_secret"),
            piapi_key=config.get("piapi_key"),
            eleven_labs_key=config.get("eleven_labs_key")
        )
        print("[VIDEO FLOW] ✓ Workflow initialized")
        return True
    
    except Exception as e:
        print(f"[VIDEO FLOW INIT ERROR] {str(e)}")
        return False


if __name__ == "__main__":
    # Test
    print("Testing video automation workflow...")
    
    # Configure with your keys
    config = {
        "creatomate_key": "your_creatomate_key",
        "creatomate_template_id": "your_template_id",
        "youtube_client_id": "your_client_id",
        "youtube_client_secret": "your_client_secret",
        "piapi_key": "your_piapi_key",
        "eleven_labs_key": "your_eleven_labs_key"
    }
    
    # initialize_video_workflow(config)
    # video_workflow.batch_generate_videos(num_videos=1)
