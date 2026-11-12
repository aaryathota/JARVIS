"""Environment-backed configuration for JARVIS."""

import os

from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = os.getenv("MODEL_NAME", "llama-3.1-8b-instant")

EMAIL_SENDER = os.getenv("EMAIL_SENDER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:9999/callback")

# ========================
# VIDEO AUTOMATION CONFIG
# ========================
# Creatomate (Video Generator)
CREATOMATE_API_KEY = os.getenv("CREATOMATE_API_KEY", "")
CREATOMATE_TEMPLATE_ID = os.getenv("CREATOMATE_TEMPLATE_ID", "")

# YouTube (Video Upload)
YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID", "")
YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET", "")
YOUTUBE_REDIRECT_URI = os.getenv("YOUTUBE_REDIRECT_URI", "http://localhost:9999/")

# Eleven Labs (Voice-over Generation)
ELEVEN_LABS_API_KEY = os.getenv("ELEVEN_LABS_API_KEY", "")

# PiAPI (Additional content features)
PIAPI_KEY = os.getenv("PIAPI_KEY", "")

# Video Automation Settings
VIDEO_UPLOAD_INTERVAL_HOURS = 24  # Generate and upload a video every 24 hours
VIDEO_GENERATION_ENABLED = False  # Set to True to enable automatic video generation
AUTO_UPLOAD_TO_YOUTUBE = False  # Set to True to automatically upload videos
VIDEO_CATEGORY = os.getenv("VIDEO_CATEGORY", "24")
VIDEO_PRIVACY = os.getenv("VIDEO_PRIVACY", "public")
VIDEO_BATCH_SIZE = int(os.getenv("VIDEO_BATCH_SIZE", "1"))