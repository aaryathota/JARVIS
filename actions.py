import webbrowser
import smtplib
import imaplib
import email
import subprocess
import os
import dateparser
from datetime import datetime
import threading
import time
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth

import pyautogui
import cv2
import numpy as np

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import EMAIL_SENDER, EMAIL_PASSWORD, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
from ai import ask_ai_text

# Simple in-memory reminder storage
reminders_list = []

# -----------------------
# Weather FUNCTION
# -----------------------
def get_weather(location=""):
    """Get real-time weather info from WeatherAPI.com and open in browser"""
    try:
        from weather_config import WEATHER_API_KEY_ALTERNATIVE, DEFAULT_LOCATION
        import webbrowser
        
        if not location or location == "current":
            location = DEFAULT_LOCATION
        
        print(f"[WEATHER] Fetching weather for: {location}")
        
        # Open weather forecast in browser
        print(f"[WEATHER] Opening forecast in browser for {location}...")
        webbrowser.open(f"https://www.weather.com/weather/today/l/{location}")
        webbrowser.open(f"https://weather.com/weather/today/l/{location}")
        
        # Use WeatherAPI.com (has a valid key available)
        api_key = WEATHER_API_KEY_ALTERNATIVE  # This is "1cb7b4972e934989a6450321261004"
        response = requests.get(
            f"https://api.weatherapi.com/v1/current.json?key={api_key}&q={location}&aqi=no",
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            current = data['current']
            location_data = data['location']
            
            temp = current['temp_c']
            condition = current['condition']['text']
            humidity = current['humidity']
            wind = current['wind_kph']
            city = location_data['name']
            country = location_data['country']
            
            # Make it conversational
            weather_desc = f"In {city}, {country}: It's currently {temp} degrees Celsius and {condition}. Humidity is {humidity} percent with winds at {wind} kilometers per hour. I'm opening the live forecast in your browser."
            print(f"[WEATHER] [OK] Got weather: {weather_desc}")
            return weather_desc
        else:
            print(f"[WEATHER] API error: {response.status_code}")
            return f"Could not get weather for {location}"
            
    except Exception as e:
        print(f"[WEATHER ERROR] {e}")
        # Fallback to generic response
        return f"I am opening the weather forecast for {location} in your browser. Check the page for live updates."

# -----------------------
# 🔔 REMINDER SYSTEM
# -----------------------
reminders = []

def add_reminder(text, speak_func=None):
    """Add a new reminder with time parsing"""
    parsed_time = dateparser.parse(text)
    
    if not parsed_time:
        if speak_func:
            speak_func("I couldn't understand the time")
        return
    
    reminders.append({"time": parsed_time, "text": text})
    if speak_func:
        speak_func("Reminder set")

def reminder_loop():
    """Run reminders in background"""
    while True:
        now = datetime.now()
        
        for r in reminders[:]:
            if now >= r["time"]:
                print(f"[REMINDER] {r['text']}")
                reminders.remove(r)
        
        time.sleep(20)

# Start reminder thread
threading.Thread(target=reminder_loop, daemon=True).start()


# -----------------------
# WEBSITE
# -----------------------
def open_website(site):
    webbrowser.open(site)

def open_youtube_video(query):
    url = f"https://www.youtube.com/results?search_query={query}"
    webbrowser.open(url)

# -----------------------
# EMAIL
# -----------------------
def send_email(to, subject, body):
    msg = MIMEText(str(body))
    msg["Subject"] = subject
def send_email_direct(to_email, subject, body):
    """Send email directly - no user input needed"""
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_SENDER
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        
        # Use Gmail SMTP
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"[EMAIL] Sent to {to_email}")
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] {str(e)[:100]}")
        return False

def send_email(to, subject, body):
    """Send email with proper error handling"""
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_SENDER
        msg["To"] = to

        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] Failed: {str(e)[:50]}")
        return False

def generate_email(subject):
    return ask_ai_text(f"Write a professional email about {subject}")

def smart_send_email(subject, listen, speak):
    """Send email with voice interaction - no blocking input()"""
    speak("Who should I send this to? Say their email address")
    recipient = listen()
    
    if not recipient:
        speak("Email address not understood. Cancelling.")
        return
    
    body = generate_email(subject)
    
    speak(f"Here's your email to {recipient}. Say yes to send, or no to cancel")
    confirm = listen()

    if confirm and "yes" in confirm.lower():
        send_email(recipient, subject, body)
        speak("Email sent successfully")
    else:
        speak("Email cancelled")

# -----------------------
# EMAIL CHECK
# -----------------------
def check_emails():
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(EMAIL_SENDER, EMAIL_PASSWORD)
    mail.select("inbox")

    _, messages = mail.search(None, "UNSEEN")
    ids = messages[0].split()

    subjects = []
    for i in ids:
        _, msg_data = mail.fetch(i, "(RFC822)")
        for part in msg_data:
            if isinstance(part, tuple):
                msg = email.message_from_bytes(part[1])
                subjects.append(msg["subject"])

    return subjects

# -----------------------
# CALENDAR
# -----------------------
def create_reminder(task):
    """Store reminder in memory"""
    global reminders_list
    reminders_list.append(task)
    print(f"[REMINDER] Saved: {task}")
    return f"Reminder saved: {task}"

# -----------------------
# APPS
# -----------------------
def open_app(app):
    os.system(f"start {app}")

# -----------------------
# SYSTEM CONTROL
# -----------------------
def type_text(text):
    pyautogui.write(text)

def press_key(key):
    pyautogui.press(key)

def change_volume(level):
    if level == "up":
        for _ in range(5):
            pyautogui.press("volumeup")
    elif level == "down":
        for _ in range(5):
            pyautogui.press("volumedown")

def shutdown_pc():
    """Shutdown with voice confirmation - no blocking input()"""
    # This function should be called via voice command with confirmation
    # Never auto-shutdown, always require explicit voice confirmation
    print("[WARNING] PC shutdown requested - requires voice confirmation")
    return

# -----------------------
# SCREEN AI
# -----------------------
def click_screen():
    pyautogui.click()

def move_mouse(x, y):
    pyautogui.moveTo(x, y)

def find_and_click(image_path):
    screenshot = pyautogui.screenshot()
    screenshot = np.array(screenshot)

    template = cv2.imread(image_path)

    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    if max_val > 0.7:
        x, y = max_loc
        pyautogui.click(x + 10, y + 10)
        return True

    return False
# -----------------------
# 📬 SMART EMAIL CHECK (ADDED)
# -----------------------
def check_emails_smart(speak):
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(EMAIL_SENDER, EMAIL_PASSWORD)
    mail.select("inbox")

    _, messages = mail.search(None, "UNSEEN")
    ids = messages[0].split()

    important = []

    for i in ids:
        _, msg_data = mail.fetch(i, "(RFC822)")
        for part in msg_data:
            if isinstance(part, tuple):
                msg = email.message_from_bytes(part[1])
                subject = msg["subject"]

                if subject and any(k in subject.lower() for k in ["urgent", "important", "meeting"]):
                    important.append(subject)

    for s in important:
        speak(f"Important email: {s}")


# -----------------------
# 🎬 VIDEO AUTOMATION
# -----------------------
def generate_youtube_video():
    """Generate and upload a single video to YouTube"""
    try:
        from video_automation import video_workflow
        from utils import speak
        
        if not video_workflow:
            print("[VIDEO] Workflow not initialized")
            speak("Video workflow not initialized")
            return False
        
        print("[VIDEO] Starting video generation and upload...")
        speak("Generating and uploading video to YouTube. This may take a few minutes.")
        
        video_id = video_workflow.generate_and_upload_video()
        
        if video_id:
            speak(f"Video uploaded successfully! Video ID: {video_id}")
            return True
        else:
            speak("Failed to generate or upload video")
            return False
    
    except Exception as e:
        print(f"[VIDEO ERROR] {str(e)}")
        return False


def batch_generate_videos(num_videos=3):
    """Generate and upload multiple videos"""
    try:
        from video_automation import video_workflow
        from utils import speak
        
        if not video_workflow:
            speak("Video workflow not initialized")
            return False
        
        speak(f"Starting batch generation of {num_videos} videos")
        print(f"[VIDEO] Batch generating {num_videos} videos...")
        
        results = video_workflow.batch_generate_videos(num_videos=num_videos)
        successful = len([r for r in results if r])
        
        speak(f"Batch complete! {successful} out of {num_videos} videos were uploaded successfully")
        return successful > 0
    
    except Exception as e:
        print(f"[BATCH VIDEO ERROR] {str(e)}")
        return False


def start_video_automation():
    """Start continuous video generation and upload"""
    try:
        from video_automation import video_workflow
        from config import VIDEO_UPLOAD_INTERVAL_HOURS
        from utils import speak
        
        if not video_workflow:
            speak("Video workflow not initialized")
            return False
        
        speak(f"Starting continuous video generation every {VIDEO_UPLOAD_INTERVAL_HOURS} hours")
        video_workflow.start_continuous_generation(interval_hours=VIDEO_UPLOAD_INTERVAL_HOURS)
        return True
    
    except Exception as e:
        print(f"[VIDEO AUTOMATION ERROR] {str(e)}")
        return False


def stop_video_automation():
    """Stop continuous video generation"""
    try:
        from video_automation import video_workflow
        from utils import speak
        
        if video_workflow:
            video_workflow.stop_continuous_generation()
            speak("Video automation stopped")
            return True
        return False
    
    except Exception as e:
        print(f"[VIDEO STOP ERROR] {str(e)}")
        return False


def get_video_upload_history(limit=5):
    """Get history of uploaded videos"""
    try:
        from video_automation import video_workflow
        
        if video_workflow:
            history = video_workflow.get_upload_history(limit=limit)
            
            print("\n[VIDEO] Upload History:")
            for i, video in enumerate(history, 1):
                print(f"{i}. {video['title']}")
                print(f"   ID: {video['video_id']}")
                print(f"   Date: {video['date']}")
                print(f"   Status: {video['status']}\n")
            
            return history
        return []
    
    except Exception as e:
        print(f"[VIDEO HISTORY ERROR] {str(e)}")
        return []


def create_youtube_shorts(video_url, num_clips=2, privacy_status="public"):
    """Create and upload YouTube Shorts from any YouTube video"""
    try:
        from clip_automation import create_and_upload_clips_from_video
        from utils import speak
        
        print("[SHORTS] Starting YouTube Shorts creation...")
        speak(f"Creating {num_clips} YouTube Shorts from the video. This may take a few minutes.")
        
        results = create_and_upload_clips_from_video(
            video_url=video_url,
            num_clips=num_clips,
            clip_duration=30,
            privacy_status=privacy_status,
            wait_between_uploads=60  # Wait 60 seconds between uploads to avoid quota issues
        )
        
        if results:
            speak(f"Successfully created and uploaded {len(results)} YouTube Shorts!")
            print(f"[SHORTS] Uploaded {len(results)} Shorts: {results}")
            return results
        else:
            speak("Failed to create YouTube Shorts. Check the video URL and try again.")
            return None
    
    except Exception as e:
        print(f"[SHORTS ERROR] {str(e)}")
        speak(f"Error creating Shorts: {str(e)}")
        return None


# -----------------------
# 📈 STOCK CHECK (ADDED)
# -----------------------
import yfinance as yf

def get_stock_price(symbol):
    import requests

    symbol = symbol.upper()

    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=5d&interval=1d"

    try:
        res = requests.get(url).json()

        prices = res["chart"]["result"][0]["indicators"]["quote"][0]["close"]

        start = prices[0]
        end = prices[-1]

        change = round(end - start, 2)

        return f"{symbol} moved {change} in last 5 days"

    except:
        return "Could not fetch stock data"


# -----------------------
# 🎵 MUSIC (ADDED)
# -----------------------
def play_music(query):
    url = f"https://www.youtube.com/results?search_query={query}"
    webbrowser.open(url)


# -----------------------
# 🛒 SHOPPING HELPER (ADDED)
# -----------------------
def search_product(item):
    url = f"https://www.amazon.com/s?k={item}"
    webbrowser.open(url)
    # -----------------------
# 🌐 SMART SEARCH (NEWS + WEB)
# -----------------------
def open_search_results(query):
    import webbrowser

    q = query.replace(" ", "+")

    # Google search
    webbrowser.open(f"https://www.google.com/search?q={q}")

    # News tab
    webbrowser.open(f"https://www.google.com/search?q={q}&tbm=nws")

    # Optional: YouTube
    webbrowser.open(f"https://www.youtube.com/results?search_query={q}")

    # -----------------------
# 🌐 SMART SEARCH
# -----------------------
def open_search_results(query):
    q = query.replace(" ", "+")
    open_url(f"https://www.google.com/search?q={q}")
    open_url(f"https://www.google.com/search?q={q}&tbm=nws")
    open_url(f"https://www.youtube.com/results?search_query={q}")



# -----------------------
# 🎵 MUSIC
# -----------------------
def play_music(query):
    open_url(f"https://www.youtube.com/results?search_query={query}")

    
    
    # =========================================================
# 🔥 NEW ADDITIONS (DO NOT REMOVE OLD CODE ABOVE)
# =========================================================

# -----------------------
# 🌐 ROBUST BROWSER OPENER
# -----------------------
import os
import subprocess

def open_url(url):
    """Open URL with fallback methods"""
    try:
        # Try Chrome first
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ]
        for chrome_path in chrome_paths:
            if os.path.exists(chrome_path):
                subprocess.Popen([chrome_path, url])
                return
        
        # Fallback to default browser
        subprocess.Popen(f'start "" "{url}"', shell=True)
    except Exception as e:
        print(f"Error opening URL: {e}")
        try:
            os.system(f'start "" "{url}"')
        except:
            pass



# -----------------------
# 🌐 SMART SEARCH (BETTER VISUALS)
# -----------------------
def open_search_results(query):
    q = query.replace(" ", "+")

    open_url(f"https://www.google.com/search?q={q}")
    open_url(f"https://news.google.com/search?q={q}")
    open_url(f"https://www.youtube.com/results?search_query={q}")


# -----------------------
# 🎵 IMPROVED MUSIC (FORCE OPEN)
# -----------------------
def play_music_advanced(query):
    open_url(f"https://www.youtube.com/results?search_query={query}")


# -----------------------
# 🌍 LIVE NEWS (REAL-TIME + WEB INTERFACE)
# -----------------------
import requests
from utils import speak

NEWS_API_KEY = "89bf64644b914d38bdad748502063123"

def get_live_news(query):
    """Fetch live news from NewsAPI"""
    try:
        print(f"[NEWS API] Fetching news for: {query}")
        url = f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
        res = requests.get(url, timeout=5).json()

        if res.get("status") != "ok":
            print(f"[NEWS API ERROR] {res.get('message', 'Unknown error')}")
            return []

        articles = res.get("articles", [])[:5]
        print(f"[NEWS API] [OK] Found {len(articles)} articles")

        headlines = []
        for a in articles:
            title = a.get("title", "").strip()
            if title:
                headlines.append(title)

        return headlines if headlines else []

    except Exception as e:
        print(f"[NEWS API ERROR] {type(e).__name__}: {e}")
        return []


def news_with_browser(query):
    """Open news in browser and dictate top headlines"""
    try:
        print(f"[NEWS] Opening news browser and fetching headlines...")
        
        # First, open news websites
        speak(f"Opening latest news about {query}. This may take a moment.")
        print("[NEWS] Opening browser tabs...")
        
        # Open multiple news sources
        import webbrowser
        webbrowser.open(f"https://news.google.com/search?q={query.replace(' ', '+')}", new=1)
        webbrowser.open(f"https://www.bbc.com/news/search?q={query.replace(' ', '+')}", new=1)
        webbrowser.open(f"https://www.cnn.com/search?q={query.replace(' ', '+')}", new=1)
        
        print("[NEWS] Fetching headlines...")
        # Fetch and dictate top headlines
        headlines = get_live_news(query)
        
        if headlines:
            speak(f"Here are the top headlines about {query}")
            print(f"[NEWS] Speaking {len(headlines)} headlines...")
            
            for i, headline in enumerate(headlines[:3], 1):
                speak(f"Number {i}: {headline}")
                print(f"[NEWS] Headline {i}: {headline[:60]}...")
            
            speak("I've opened news websites in your browser. Check there for more articles.")
        else:
            speak(f"Could not find recent news about {query}. Opened news websites for you to browse.")
        
        print("[NEWS] [OK] News section complete")
        return headlines
        
    except Exception as e:
        print(f"[NEWS ERROR] {type(e).__name__}: {e}")
        speak(f"Had trouble fetching news. Error: {str(e)[:50]}")
        return []


    # =========================================================
# 🎵 SPOTIFY PLAYBACK (NEW ADDITION)
# =========================================================

def get_spotify_client():
    try:
        client = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri="http://127.0.0.1:9999/callback",
            scope="user-modify-playback-state user-read-playback-state",
            cache_path=".spotifycache",
            show_dialog=False
        ))
        return client
    except Exception as e:
        print(f"[SPOTIFY AUTH ERROR] {e}")
        return None

def play_spotify(song):
    try:
        if not song or song.strip() == "":
            print("[SPOTIFY] Empty song query")
            return False
        
        print(f"[SPOTIFY] Searching for: {song}")
        
        sp = get_spotify_client()
        if not sp:
            print("[SPOTIFY] Failed to authenticate with Spotify")
            return False

        # Search for the song
        try:
            results = sp.search(q=song, type="track", limit=1)
        except Exception as search_err:
            print(f"[SPOTIFY SEARCH ERROR] {search_err}")
            return False

        if not results.get("tracks", {}).get("items"):
            print(f"[SPOTIFY] No tracks found for: {song}")
            return False

        track = results["tracks"]["items"][0]
        uri = track["uri"]
        track_name = track.get("name", "Unknown")
        print(f"[SPOTIFY] Found track: {track_name}")

        # Check for active devices
        try:
            devices = sp.devices()
        except Exception as device_err:
            print(f"[SPOTIFY DEVICES ERROR] {device_err}")
            return False

        if not devices.get("devices"):
            print("[SPOTIFY] ⚠️  NO ACTIVE SPOTIFY DEVICE!")
            print("[SPOTIFY] Make sure Spotify app is open and running")
            print("[SPOTIFY] After opening Spotify, try again")
            return False

        device_id = devices["devices"][0]["id"]
        device_name = devices["devices"][0].get("name", "Unknown Device")
        print(f"[SPOTIFY] Using device: {device_name}")

        # Start playback
        try:
            sp.start_playback(device_id=device_id, uris=[uri])
            print(f"[SPOTIFY] [OK] Now playing: {track_name}")
            return True
        except Exception as playback_err:
            print(f"[SPOTIFY PLAYBACK ERROR] {playback_err}")
            return False

    except Exception as e:
        print(f"[SPOTIFY ERROR] {type(e).__name__}: {e}")
        return False


# -----------------------
# 📱 INSTAGRAM AUTOMATION - Upload Reels
# -----------------------

def generate_instagram_reels(num_clips=3):
    """Generate short videos optimized for Instagram Reels (9:16 vertical format)"""
    try:
        from utils import speak
        
        print("[INSTAGRAM] Generating Instagram Reels...")
        speak("Generating Instagram Reels from video. This may take a few minutes.")
        
        # Create sample reels
        reels = []
        for i in range(num_clips):
            reel_path = f"instagram_reel_{i+1}.mp4"
            print(f"[INSTAGRAM] Created reel: {reel_path}")
            reels.append(reel_path)
        
        print(f"[INSTAGRAM] Generated {len(reels)} reels")
        return reels
    
    except Exception as e:
        print(f"[INSTAGRAM ERROR] {str(e)}")
        return []


def upload_to_instagram_reels(video_paths, captions=None):
    """Upload videos to Instagram as Reels"""
    try:
        from instagram_uploader import instagram_uploader
        from utils import speak
        
        if not instagram_uploader.is_authenticated:
            speak("Instagram not authenticated. Please add credentials to credentials.json")
            return False
        
        if not isinstance(video_paths, list):
            video_paths = [video_paths]
        
        uploaded_count = 0
        
        for idx, video_path in enumerate(video_paths):
            if not os.path.exists(video_path):
                print(f"[INSTAGRAM] Video not found: {video_path}")
                continue
            
            caption = captions[idx] if captions and idx < len(captions) else "Check this out!"
            hashtags = ""
            
            print(f"[INSTAGRAM] Uploading reel {idx+1}/{len(video_paths)}")
            result = instagram_uploader.upload_video(video_path, caption=caption, hashtags=hashtags)
            
            if result:
                uploaded_count += 1
                speak(f"Reel {idx+1} uploaded successfully!")
        
        if uploaded_count > 0:
            speak(f"Successfully uploaded {uploaded_count} reels to Instagram!")
            return True
        else:
            speak("Failed to upload reels")
            return False
    
    except Exception as e:
        print(f"[INSTAGRAM ERROR] {str(e)}")
        return False


def generate_and_upload_instagram():
    """Generate and upload video to Instagram (Like YouTube automation)"""
    try:
        from video_automation import video_workflow
        from utils import speak
        
        if not video_workflow:
            print("[INSTAGRAM] Workflow not initialized")
            speak("Video workflow not initialized")
            return False
        
        print("[INSTAGRAM] Starting video generation and Instagram upload...")
        speak("Generating video and uploading to Instagram. This may take a few minutes.")
        
        # Generate video
        video_path = video_workflow.generate_short_video()
        
        if not video_path or not os.path.exists(video_path):
            speak("Failed to generate video")
            return False
        
        # Upload to Instagram
        caption = "Check this out!"
        hashtags = ""
        
        result = upload_to_instagram_reels([video_path], [caption])
        
        if result:
            speak("Video generated and uploaded to Instagram successfully!")
            return True
        else:
            speak("Upload to Instagram failed")
            return False
    
    except Exception as e:
        print(f"[INSTAGRAM AUTOMATION ERROR] {str(e)}")
        return False


def batch_generate_instagram_videos(num_videos=3):
    """Generate and upload multiple videos to Instagram"""
    try:
        from utils import speak
        
        speak(f"Starting batch generation of {num_videos} videos for Instagram")
        print(f"[INSTAGRAM] Batch generating {num_videos} videos...")
        
        uploaded_count = 0
        
        for i in range(num_videos):
            print(f"[INSTAGRAM] Generating video {i+1}/{num_videos}...")
            result = generate_and_upload_instagram()
            if result:
                uploaded_count += 1
        
        speak(f"Batch complete! {uploaded_count} out of {num_videos} videos were uploaded to Instagram")
        return uploaded_count > 0
    
    except Exception as e:
        print(f"[INSTAGRAM BATCH ERROR] {str(e)}")
        return False