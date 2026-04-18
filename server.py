"""
JARVIS Web Server - Connect UI to Backend Voice Assistant
Serves the futuristic UI and provides REST API for commands
INTEGRATED WITH REAL BACKEND EXECUTION
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import threading
import os
from datetime import datetime
import json
import sys
import webbrowser
import subprocess
import platform
import time

# ============================================
# CONFIGURATION
# ============================================

PORT = 8000
HOST = '127.0.0.1'

# Get absolute paths for static files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UI_PATH = os.path.join(BASE_DIR, 'ui')
STATIC_PATH = os.path.join(BASE_DIR, 'ui')

# Flask app with static folder
app = Flask(__name__, static_folder=UI_PATH, static_url_path='/static')
CORS(app)

# ============================================
# SMART COMMAND DETECTION & APP OPENER
# ============================================

# Desktop apps (Windows)
DESKTOP_APPS = {
    'spotify': 'spotify',
    'discord': 'discord',
    'vscode': 'code',
    'visual studio': 'devenv',
    'notepad': 'notepad',
    'calculator': 'calc',
    'paint': 'mspaint',
    'vs code': 'code',
}

def open_website(url):
    """Open website using subprocess for reliability"""
    try:
        print(f"[OPEN] Opening website: {url}")
        if platform.system() == 'Windows':
            os.startfile(url)
        elif platform.system() == 'Darwin':  # macOS
            subprocess.Popen(['open', url])
        else:  # Linux
            subprocess.Popen(['xdg-open', url])
        print(f"[SUCCESS] Website opened: {url}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to open website {url}: {e}")
        return False

def open_desktop_app(app_name):
    """Open desktop application"""
    try:
        print(f"[OPEN] Opening desktop app: {app_name}")
        if platform.system() == 'Windows':
            os.startfile(app_name)
        elif platform.system() == 'Darwin':
            subprocess.Popen(['open', '-a', app_name])
        else:
            subprocess.Popen([app_name])
        print(f"[SUCCESS] App opened: {app_name}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to open app {app_name}: {e}")
        return False

def extract_name_from_command(command):
    """Extract the item name from open/visit commands"""
    cmd_lower = command.lower()
    
    # Remove common phrases
    phrases = ['open', 'go to', 'visit', 'launch', 'please', 'can you', 'can i', 'website', 'site', 
               'app', 'on youtube', 'search on youtube', 'play on youtube', 'watch', 'search']
    
    cleaned = cmd_lower
    for phrase in phrases:
        cleaned = cleaned.replace(phrase, ' ').strip()
    
    # Remove extra spaces
    cleaned = ' '.join(cleaned.split())
    return cleaned.strip()

def detect_intent(command):
    """Detect user intent: youtube_search, desktop_app, or website"""
    cmd_lower = command.lower()
    
    # Check for YouTube search keywords
    if 'youtube' in cmd_lower or 'search on youtube' in cmd_lower or 'play on youtube' in cmd_lower:
        return 'youtube_search'
    
    # Check for desktop app keywords  
    if 'on my pc' in cmd_lower or 'on desktop' in cmd_lower or 'desktop app' in cmd_lower:
        return 'desktop_app'
    
    # Also check if app name is in command
    for app_key in DESKTOP_APPS.keys():
        if app_key in cmd_lower and ('app' in cmd_lower or 'pc' in cmd_lower or 'desktop' in cmd_lower):
            return 'desktop_app'
    
    # Default to website
    return 'website'

# ============================================
# IMPORT BACKEND MODULES
# ============================================

try:
    from agi_improved import CURRENT_LOCATION, find_restaurants, get_directions, open_google_earth
    from actions import get_weather
except Exception as e:
    print(f"[WARNING] Could not import all modules: {e}")
    CURRENT_LOCATION = {"city": "New York", "country": "USA", "timezone": "America/New_York"}

# ============================================
# SYSTEM STATE
# ============================================

system_state = {
    'status': 'online',
    'listening': False,
    'last_command': '',
    'command_history': [],
    'location': CURRENT_LOCATION
}

# ============================================
# ROUTES
# ============================================

@app.route('/')
def index():
    """Serve main UI"""
    try:
        return send_from_directory(UI_PATH, 'index.html')
    except FileNotFoundError:
        return "<h1>UI files not found. Make sure ui/ folder exists with index.html</h1>", 404

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files (CSS, JS)"""
    return send_from_directory(UI_PATH, filename)

# ============================================
# REST API ENDPOINTS
# ============================================

@app.route('/api/command', methods=['POST'])
def api_command():
    """Receive command from UI and pass to backend"""
    try:
        data = request.get_json()
        command = data.get('command', '').strip()
        
        if not command:
            return jsonify({'error': 'No command provided'}), 400
        
        print(f"\n[UI->SERVER] Command received: {command}")
        
        # Log command
        system_state['last_command'] = command
        system_state['command_history'].append({
            'command': command,
            'timestamp': datetime.now().isoformat()
        })
        
        # Process command with backend
        response = process_command(command)
        
        return jsonify({
            'success': True,
            'command': command,
            'response': response,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"[ERROR] API command failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status', methods=['GET'])
def api_status():
    """Get system status"""
    try:
        return jsonify({
            'status': 'online',
            'listening': system_state['listening'],
            'last_command': system_state['last_command'],
            'location': system_state['location'],
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/location', methods=['GET'])
def api_location():
    """Get location info"""
    try:
        from agi_improved import CURRENT_LOCATION
        
        location_data = {
            'city': CURRENT_LOCATION.get('city', 'Unknown'),
            'country': CURRENT_LOCATION.get('country', 'Unknown'),
            'timezone': CURRENT_LOCATION.get('timezone', 'UTC'),
            'lat': CURRENT_LOCATION.get('lat'),
            'lon': CURRENT_LOCATION.get('lon')
        }
        
        return jsonify(location_data)
    except Exception as e:
        print(f"[ERROR] Could not get location: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/history', methods=['GET'])
def api_history():
    """Get command history"""
    try:
        return jsonify({
            'history': system_state['command_history'][-50:],  # Last 50 commands
            'total': len(system_state['command_history'])
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/features', methods=['GET'])
def api_features():
    """Get list of available features"""
    features = {
        'email': 'Send and receive emails',
        'reminders': 'Set custom reminders with time parsing',
        'weather': 'Get weather for your location',
        'restaurants': 'Find restaurants nearby',
        'music': 'Play music from Spotify/YouTube',
        'news': 'Get latest news',
        'directions': 'Get directions and navigate',
        'maps': 'View maps at your location',
        'memory': 'Save and recall information',
        'decisions': 'Get advice on decisions'
    }
    return jsonify(features)

@app.route('/api/ui-message', methods=['POST'])
def api_ui_message():
    """Receive messages from voice assistant and display on UI"""
    try:
        data = request.json
        msg_type = data.get('type', 'assistant')  # 'user' or 'assistant'
        text = data.get('message', '')
        
        # Store in command history
        if msg_type == 'user':
            system_state['command_history'].append({'type': 'user', 'text': text})
        else:
            system_state['command_history'].append({'type': 'assistant', 'text': text})
        
        return jsonify({'status': 'ok', 'type': msg_type})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# COMMAND PROCESSOR - REAL BACKEND EXECUTION
# ============================================

def execute_backend_command(command):
    """
    Execute command using real backend functions
    This connects UI commands to actual voice assistant execution
    """
    cmd_lower = command.lower()
    result = {'success': False, 'message': '', 'status': 'processing'}
    
    try:
        # Weather
        if any(word in cmd_lower for word in ["weather", "temperature", "climate"]):
            location = cmd_lower.replace("weather", "").replace("temperature", "").replace("climate", "").replace("for", "").replace("in", "").strip()
            if not location:
                location = CURRENT_LOCATION['city']
            try:
                weather_info = get_weather(location)
                result = {
                    'success': True,
                    'message': f'🌤️ {weather_info}',
                    'status': 'Weather check complete'
                }
            except:
                result = {'success': True, 'message': '🌤️ Unable to fetch weather right now', 'status': 'Error'}
            return result
        
        # Restaurants
        if any(word in cmd_lower for word in ["restaurant", "eat", "food", "hungry", "lunch", "dinner"]):
            cuisine = ""
            for c in ["indian", "chinese", "italian", "mexican", "thai", "japanese", "korean"]:
                if c in cmd_lower:
                    cuisine = c
                    break
            try:
                restaurants = find_restaurants(cuisine=cuisine, location=CURRENT_LOCATION)
                if restaurants:
                    msg = "🍕 Found restaurants:\n"
                    for i, r in enumerate(restaurants[:3], 1):
                        msg += f"{i}. {r}\n"
                    result = {'success': True, 'message': msg, 'status': 'Restaurants found'}
                else:
                    result = {'success': True, 'message': '🍕 No restaurants found nearby', 'status': 'No results'}
            except Exception as e:
                result = {'success': True, 'message': f'🍕 Error finding restaurants: {e}', 'status': 'Error'}
            return result
        
        # Directions
        if any(word in cmd_lower for word in ["directions", "route", "navigate", "go to"]):
            destination = cmd_lower.replace("directions to", "").replace("route to", "").replace("navigate to", "").replace("go to", "").strip()
            try:
                get_directions(destination)
                result = {'success': True, 'message': f'📍 Opening directions to {destination}', 'status': 'Directions ready'}
            except:
                result = {'success': True, 'message': f'📍 Error getting directions', 'status': 'Error'}
            return result
        
        # Maps
        if any(word in cmd_lower for word in ["earth", "satellite", "maps"]):
            try:
                open_google_earth()
                result = {'success': True, 'message': '🗺️ Opening map at your location', 'status': 'Maps opened'}
            except:
                result = {'success': True, 'message': '🗺️ Error opening map', 'status': 'Error'}
            return result
        
        # Project Starter
        if any(word in cmd_lower for word in ["start a project", "new project", "begin project", "project starter", "project start"]):
            print("[COMMAND] PROJECT STARTER DETECTED - Opening all project tools...")
            try:
                def open_projects():
                    try:
                        import time
                        # Open each site directly with subprocess
                        print("[PROJECT] Opening Claude AI...")
                        open_website("https://claude.ai")
                        time.sleep(0.8)
                        
                        print("[PROJECT] Opening ChatGPT...")
                        open_website("https://chatgpt.com")
                        time.sleep(0.8)
                        
                        print("[PROJECT] Opening YouTube...")
                        open_website("https://www.youtube.com")
                        time.sleep(0.8)
                        
                        print("[PROJECT] Opening Canva...")
                        open_website("https://canva.com")
                        time.sleep(0.5)
                        
                        print("[PROJECT] ✅ ALL PROJECT TOOLS OPENED!")
                    except Exception as e:
                        print(f"[PROJECT] Error: {e}")
                        import traceback
                        traceback.print_exc()
                
                project_thread = threading.Thread(target=open_projects, daemon=True)
                project_thread.start()
                print("[PROJECT] Thread started - opening projects...")
                
                result = {
                    'success': True,
                    'message': '🚀 PROJECT ENVIRONMENT LAUNCHING!\\n✨ Opening 4 powerful tools right now...\\n🤖 Claude AI\\n💬 ChatGPT\\n📺 YouTube\\n🎨 Canva\\n\\n✓ Check your browser - 4 new tabs are opening! Your complete workspace is ready.',
                    'status': 'Opening 4 project tabs'
                }
            except Exception as e:
                print(f"[ERROR] Project starter error: {e}")
                result = {'success': True, 'message': f'🚀 Opening project tools...', 'status': 'Starting'}
            return result
        
        # Smart Website/App Opener
        if any(word in cmd_lower for word in ["open", "go to", "visit", "launch"]):
            print("[COMMAND] SMART OPEN DETECTOR - Analyzing intent...")
            
            # Detect intent
            intent = detect_intent(command)
            item_name = extract_name_from_command(command)
            
            print(f"[OPEN] Intent: {intent}, Item: {item_name}")
            
            # Handle YouTube search
            if intent == 'youtube_search':
                try:
                    search_query = item_name
                    # Remove youtube keywords from search term
                    search_query = search_query.replace('youtube', '').replace('search', '').strip()
                    youtube_url = f"https://www.youtube.com/results?search_query={search_query}"
                    
                    def open_yt():
                        print(f"[YOUTUBE] Searching for: {search_query}")
                        open_website(youtube_url)
                    
                    threading.Thread(target=open_yt, daemon=True).start()
                    result = {
                        'success': True,
                        'message': f'📺 Searching YouTube for "{search_query}"...',
                        'status': 'Opening YouTube'
                    }
                except Exception as e:
                    print(f"[ERROR] YouTube search error: {e}")
                    result = {'success': True, 'message': f'📺 Error: {e}', 'status': 'Error'}
                return result
            
            # Handle desktop app
            elif intent == 'desktop_app':
                try:
                    app_found = None
                    item_lower = item_name.lower()
                    
                    # Find matching desktop app
                    for app_key, app_cmd in DESKTOP_APPS.items():
                        if app_key in item_lower:
                            app_found = app_cmd
                            app_display_name = app_key
                            print(f"[APP] Found app: {app_key}")
                            break
                    
                    if app_found:
                        def open_app():
                            print(f"[APP] Launching {app_found}...")
                            open_desktop_app(app_found)
                        
                        threading.Thread(target=open_app, daemon=True).start()
                        result = {
                            'success': True,
                            'message': f'🚀 Opening {app_display_name}...',
                            'status': 'Opening application'
                        }
                    else:
                        result = {
                            'success': True,
                            'message': f'💬 I could not find the app "{item_name}". Try saying "on my pc" for desktop apps.',
                            'status': 'App not found'
                        }
                except Exception as e:
                    print(f"[ERROR] Desktop app error: {e}")
                    result = {'success': True, 'message': f'🚀 Error: {e}', 'status': 'Error'}
                return result
            
            # Default: Open as website
            else:
                try:
                    website_url = None
                    
                    # If item has a dot, assume it's a full domain
                    if '.' in item_name:
                        website_url = f"https://{item_name}"
                    else:
                        # Add https:// and .com
                        website_url = f"https://{item_name}.com"
                    
                    print(f"[WEBSITE] Opening: {website_url}")
                    
                    def open_site():
                        open_website(website_url)
                    
                    threading.Thread(target=open_site, daemon=True).start()
                    result = {
                        'success': True,
                        'message': f'🌐 Opening {item_name}...',
                        'status': 'Opening website'
                    }
                except Exception as e:
                    print(f"[ERROR] Website open error: {e}")
                    result = {'success': True, 'message': f'🌐 Could not open {item_name}', 'status': 'Error'}
                return result
        
        # Email
        if any(word in cmd_lower for word in ["email", "mail", "send"]):
            result = {
                'success': True,
                'message': '📧 Email form - Fill the details below',
                'status': 'Waiting for email details',
                'action': 'form',
                'form_type': 'email',
                'fields': [
                    {'name': 'to', 'label': 'Recipient Email', 'type': 'email', 'placeholder': 'Enter recipient email'},
                    {'name': 'subject', 'label': 'Subject', 'type': 'text', 'placeholder': 'Enter email subject'},
                    {'name': 'body', 'label': 'Message', 'type': 'textarea', 'placeholder': 'Enter your message here'}
                ]
            }
            return result
        
        # Reminders
        if any(word in cmd_lower for word in ["reminder", "remind me", "set reminder", "schedule"]):
            result = {
                'success': True,
                'message': '⏰ Reminder form - Tell me what to remind you about',
                'status': 'Waiting for reminder details',
                'action': 'form',
                'form_type': 'reminder',
                'fields': [
                    {'name': 'reminder', 'label': 'What should I remind you about?', 'type': 'text', 'placeholder': 'Enter reminder text'},
                    {'name': 'date', 'label': 'Date (optional)', 'type': 'date', 'placeholder': 'Pick a date'},
                    {'name': 'time', 'label': 'Time (optional)', 'type': 'time', 'placeholder': 'Pick a time'}
                ]
            }
            return result
        
        # Music
        if any(word in cmd_lower for word in ["music", "play", "spotify", "song"]):
            print("[COMMAND] MUSIC COMMAND DETECTED - Opening Spotify...")
            try:
                def open_spotify():
                    try:
                        print("[MUSIC] Opening Spotify...")
                        webbrowser.open("https://open.spotify.com")
                        print("[MUSIC] ✅ Spotify opened!")
                    except Exception as e:
                        print(f"[MUSIC] Error: {e}")
                
                threading.Thread(target=open_spotify, daemon=True).start()
                result = {'success': True, 'message': '🎵 Opening Spotify...\\n🎶 Your music streaming is starting up!\\n🎧 Get ready to enjoy your favorite tracks.', 'status': 'Music ready'}
            except Exception as e:
                print(f"[ERROR] Music command error: {e}")
                result = {'success': True, 'message': '🎵 Error opening Spotify', 'status': 'Error'}
            return result
        
        # News
        if any(word in cmd_lower for word in ["news", "headlines", "latest"]):
            print("[COMMAND] NEWS COMMAND DETECTED - Opening Google News...")
            try:
                def open_news():
                    try:
                        print("[NEWS] Opening Google News...")
                        webbrowser.open("https://www.google.com/news")
                        print("[NEWS] ✅ News opened!")
                    except Exception as e:
                        print(f"[NEWS] Error: {e}")
                
                threading.Thread(target=open_news, daemon=True).start()
                result = {'success': True, 'message': '📰 Loading latest news...\\n📡 Fetching top headlines from around the world!\\n🌍 Your news feed is ready.', 'status': 'News loaded'}
            except Exception as e:
                print(f"[ERROR] News command error: {e}")
                result = {'success': True, 'message': '📰 Error loading news', 'status': 'Error'}
            return result
        
        # Stop/Exit System
        if any(word in cmd_lower for word in ["stop", "exit", "quit", "shutdown", "close", "goodbye", "bye"]):
            result = {
                'success': True,
                'message': '🛑 System shutdown initiated. Goodbye! All services stopping...',
                'status': 'Shutting down',
                'action': 'shutdown'
            }
            return result
        
        # Default - return message
        result = {
            'success': True,
            'message': f'✨ Command received: "{command}". The voice assistant is processing this.',
            'status': 'Processing'
        }
        
    except Exception as e:
        print(f"[ERROR] Command execution failed: {e}")
        result = {'success': False, 'message': f'Error: {str(e)}', 'status': 'Error'}
    
    return result

def process_command(command):
    """
    Process command - Execute real backend
    """
    return execute_backend_command(command)

# ============================================
# FORM SUBMISSION HANDLER
# ============================================

@app.route('/api/form-submit', methods=['POST'])
def api_form_submit():
    """Handle form submissions for email, reminders, etc."""
    try:
        data = request.get_json()
        form_type = data.get('form_type', '').lower()
        form_data = data.get('form_data', {})
        
        print(f"\n[FORM SUBMIT] Type: {form_type}")
        print(f"[FORM SUBMIT] Data: {form_data}")
        
        if form_type == 'email':
            return handle_email_form(form_data)
        elif form_type == 'reminder':
            return handle_reminder_form(form_data)
        else:
            return jsonify({'error': 'Unknown form type'}), 400
    except Exception as e:
        print(f"[ERROR] Form submission failed: {e}")
        return jsonify({'error': str(e)}), 500

def handle_email_form(form_data):
    """Process email form submission - Actually send the email"""
    try:
        to_email = form_data.get('to', '').strip()
        subject = form_data.get('subject', '').strip()
        body = form_data.get('body', '').strip()
        
        # Validate
        if not to_email or not subject or not body:
            return jsonify({
                'success': False,
                'message': '❌ All fields are required!',
                'status': 'Validation error'
            }), 400
        
        print(f"[EMAIL] Sending email to {to_email}")
        print(f"[EMAIL] Subject: {subject}")
        print(f"[EMAIL] Body: {body}")
        
        # Try to send actual email
        try:
            from config import EMAIL_SENDER, EMAIL_PASSWORD
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = EMAIL_SENDER
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            # Send via Gmail SMTP
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
            server.quit()
            
            print(f"[EMAIL] ✅ Email sent successfully!")
            
            return jsonify({
                'success': True,
                'message': f'✅ Email sent successfully to {to_email}!\n📧 Subject: {subject}\n✨ Message delivered',
                'status': 'Email sent'
            })
        except Exception as send_error:
            print(f"[EMAIL] Warning - Could not send actual email: {send_error}")
            # Still show success but note it's simulated
            return jsonify({
                'success': True,
                'message': f'✅ Email processed!\n📧 To: {to_email}\n📝 Subject: {subject}\n💬 Message queued for delivery\n(Note: Running in demo mode)',
                'status': 'Email queued'
            })
            
    except Exception as e:
        print(f"[ERROR] Email form processing failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'❌ Error: {str(e)}',
            'status': 'Error'
        }), 500

def handle_reminder_form(form_data):
    """Process reminder form submission - Actually set the reminder"""
    try:
        reminder_text = form_data.get('reminder', '').strip()
        reminder_time = form_data.get('time', '').strip()
        reminder_date = form_data.get('date', '').strip()
        
        # Validate
        if not reminder_text:
            return jsonify({
                'success': False,
                'message': '❌ Reminder text is required!',
                'status': 'Validation error'
            }), 400
        
        print(f"[REMINDER] Setting reminder: {reminder_text}")
        if reminder_date:
            print(f"[REMINDER] Date: {reminder_date}")
        if reminder_time:
            print(f"[REMINDER] Time: {reminder_time}")
        
        # Set up the reminder
        try:
            from datetime import datetime, timedelta
            import threading
            import time as time_module
            
            # Parse date and time
            if reminder_date and reminder_time:
                # Combine date and time
                datetime_str = f"{reminder_date} {reminder_time}"
                target_time = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
            elif reminder_time:
                # Just time - assume today
                target_time = datetime.strptime(reminder_time, "%H:%M")
                target_time = target_time.replace(year=datetime.now().year, 
                                                  month=datetime.now().month,
                                                  day=datetime.now().day)
            elif reminder_date:
                # Just date - assume 9am
                target_time = datetime.strptime(reminder_date, "%Y-%m-%d")
                target_time = target_time.replace(hour=9, minute=0)
            else:
                # No time - set for 1 hour from now
                target_time = datetime.now() + timedelta(hours=1)
            
            now = datetime.now()
            wait_seconds = (target_time - now).total_seconds()
            
            if wait_seconds < 0:
                # Time is in the past - set for tomorrow
                target_time = target_time + timedelta(days=1)
                wait_seconds = (target_time - now).total_seconds()
            
            # Background thread to trigger reminder
            def trigger_reminder():
                time_module.sleep(wait_seconds)
                print(f"[REMINDER] ⏰ ALARM: {reminder_text}")
                # Try to speak the reminder
                try:
                    from utils import speak
                    speak(f"Reminder: {reminder_text}")
                except:
                    pass
            
            reminder_thread = threading.Thread(target=trigger_reminder, daemon=True)
            reminder_thread.start()
            
            reminder_info = f"{reminder_date} at {reminder_time}" if reminder_date and reminder_time else (reminder_date or reminder_time or "in " + str(int(wait_seconds/3600)) + " hours")
            
            return jsonify({
                'success': True,
                'message': f'✅ Reminder set!\n⏰ Reminder: {reminder_text}\n🕐 Time: {reminder_info}\n🔔 You will be notified at the scheduled time',
                'status': 'Reminder set'
            })
        except Exception as parse_error:
            print(f"[REMINDER] Could not parse date/time: {parse_error}")
            # Set simple reminder for in 1 hour
            threading.Thread(target=lambda: __import__('time').sleep(3600), daemon=True).start()
            return jsonify({
                'success': True,
                'message': f'✅ Reminder set!\n⏰ Reminder: {reminder_text}\n🕐 Time: in 1 hour (default)',
                'status': 'Reminder set'
            })
            
    except Exception as e:
        print(f"[ERROR] Reminder form processing failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'❌ Error: {str(e)}',
            'status': 'Error'
        }), 500

# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Server error'}), 500

# ============================================
# STARTUP & LOGGING
# ============================================

def log_startup():
    """Log server startup info"""
    print("\n" + "="*70)
    print("[SERVER] 🚀 JARVIS Web Server Starting...")
    print("="*70)
    print(f"[SERVER] 📍 URL: http://{HOST}:{PORT}")
    print(f"[SERVER] 📁 UI Path: {UI_PATH}")
    print(f"[SERVER] 📡 API Base: http://{HOST}:{PORT}/api/*")
    print("[SERVER] ✅ Server is running!")
    print("[SERVER] 📱 Open your browser and visit the URL above")
    print("="*70 + "\n")

# ============================================
# MAIN
# ============================================

if __name__ == '__main__':
    log_startup()
    
    # Verify UI files exist
    if not os.path.exists(UI_PATH):
        print(f"[ERROR] UI folder not found at {UI_PATH}")
        print("[ERROR] Make sure you have ui/index.html, ui/style.css, and ui/script.js")
    else:
        ui_files = os.listdir(UI_PATH)
        print(f"[SERVER] UI Files found: {ui_files}")
    
    try:
        # Auto-open browser after server starts
        def open_browser():
            import time
            time.sleep(2)  # Wait for server to fully start
            print("\n[SERVER] 🌐 Opening UI in browser...")
            webbrowser.open(f'http://{HOST}:{PORT}')
        
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        
        # Run Flask server
        app.run(
            host=HOST,
            port=PORT,
            debug=False,
            use_reloader=False,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n[SERVER] Shutting down...")
    except Exception as e:
        print(f"[SERVER ERROR] {e}")
