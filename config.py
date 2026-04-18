MODEL_NAME = "llama-3.1-8b-instant"

EMAIL_SENDER = "aaryathota2@gmail.com"
EMAIL_PASSWORD = "tpgmzpubsehtfbwe"
SPOTIFY_CLIENT_ID = "9f64fb3b523a47b6a43f7d3e0075b683"
SPOTIFY_CLIENT_SECRET = "95298b7002424b28bd77f16d778a178f"
SPOTIFY_REDIRECT_URI = "http://127.0.0.1:9999/callback"

# ========================
# VIDEO AUTOMATION CONFIG
# ========================
# Creatomate (Video Generator)
CREATOMATE_API_KEY = "8a0b8fdbd7f34a0ea7699951000c5be1f916f1f405eb9b213ab4053ac53fbc0ae8c99f160656ebf0e3845d73ce842f46"  # Add your Creatomate API key here
CREATOMATE_TEMPLATE_ID = "4e9d03cb-eada-480d-a4d8-c70032eb6487"  # Add your Creatomate template ID here

# YouTube (Video Upload)
YOUTUBE_CLIENT_ID = "484461843626-j7kramh3ou246oect77i8i9pkv12c112.apps.googleusercontent.com"  # Add your YouTube OAuth Client ID
YOUTUBE_CLIENT_SECRET = "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"  # Add your YouTube OAuth Client Secret
YOUTUBE_REDIRECT_URI = "http://localhost:9999/"  # OAuth redirect URI

# Eleven Labs (Voice-over Generation)
ELEVEN_LABS_API_KEY = "sk_ee793f480fcb2d6628016bbbe8950e885db672473960b7f5"  # Add your Eleven Labs API key here

# PiAPI (Additional content features)
PIAPI_KEY = "10431f0e2f5d333b7f59c8e179948fe57de4263ed19a1e4dbab211f9ad6ede5f"  # Add your PiAPI key here

# Video Automation Settings
VIDEO_UPLOAD_INTERVAL_HOURS = 24  # Generate and upload a video every 24 hours
VIDEO_GENERATION_ENABLED = False  # Set to True to enable automatic video generation
AUTO_UPLOAD_TO_YOUTUBE = False  # Set to True to automatically upload videos
VIDEO_CATEGORY = "25"  # YouTube category (25=News & Politics, 10=Music, 28=Science & Technology, etc.)
VIDEO_PRIVACY = "public"  # public, unlisted, or private
VIDEO_BATCH_SIZE = 1  # Number of videos to generate in batch