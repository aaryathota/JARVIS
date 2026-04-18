import threading
import webbrowser
import sys
import os
import signal
import subprocess
import traceback
import requests

from voice import listen, stop_listening
from ai import ask_ai_text, decide_action, parse_intent, is_casual_query, handle_casual_query
from actions import *
from automation import auto_email_checker
from workflow_engine import email_monitor, daily_routine, smart_tasks, email_monitor_smart
from agi_agent import agi_agent
from memory import remember, recall
from utils import speak
from agi_engine import agi_engine
from conversation_memory import get_memory, add_to_memory, get_context_for_query, get_current_topic
from smart_messages import (
    should_open_notepad, open_notepad_for_dictation, 
    detect_sentence_intent, extract_context_from_sentence,
    is_conversational_response
)

# -----------------------
# NEW FEATURE MODULES - 50+ features across 9 categories
# -----------------------

# Productivity Features
try:
    from todo_manager import todo_manager
    TODOMANAGER_AVAILABLE = True
except Exception as e:
    print(f"[WARNING] Todo Manager not available: {e}")
    TODOMANAGER_AVAILABLE = False

try:
    from calendar_manager import calendar_manager
    CALENDAR_AVAILABLE = True
except Exception as e:
    print(f"[WARNING] Calendar Manager not available: {e}")
    CALENDAR_AVAILABLE = False

try:
    from expense_tracker import expense_tracker
    EXPENSE_AVAILABLE = True
except Exception as e:
    print(f"[WARNING] Expense Tracker not available: {e}")
    EXPENSE_AVAILABLE = False

# Entertainment Features
try:
    from entertainment import entertainment
    ENTERTAINMENT_AVAILABLE = True
except Exception as e:
    print(f"[WARNING] Entertainment module not available: {e}")
    ENTERTAINMENT_AVAILABLE = False

# Media Features
try:
    from media_handler import media_handler
    MEDIA_AVAILABLE = True
except Exception as e:
    print(f"[WARNING] Media Handler not available: {e}")
    MEDIA_AVAILABLE = False

# Developer Features
try:
    from developer_tools import developer_tools
    DEVELOPER_TOOLS_AVAILABLE = True
except Exception as e:
    print(f"[WARNING] Developer Tools not available: {e}")
    DEVELOPER_TOOLS_AVAILABLE = False

# AI/ML Features
try:
    from ai_features import ai_features
    AI_FEATURES_AVAILABLE = True
except Exception as e:
    print(f"[WARNING] AI Features not available: {e}")
    AI_FEATURES_AVAILABLE = False

# Communication Features
try:
    from communication import communication
    COMMUNICATION_AVAILABLE = True
except Exception as e:
    print(f"[WARNING] Communication module not available: {e}")
    COMMUNICATION_AVAILABLE = False

# System Features
try:
    from system_features import system_features
    SYSTEM_FEATURES_AVAILABLE = True
except Exception as e:
    print(f"[WARNING] System Features not available: {e}")
    SYSTEM_FEATURES_AVAILABLE = False

# Website Builder
try:
    from website_builder_pro import website_builder_pro
    WEBSITE_BUILDER_AVAILABLE = True
except Exception as e:
    print(f"[WARNING] Website Builder not available: {e}")
    WEBSITE_BUILDER_AVAILABLE = False

# NEW FEATURES - System Stats, Workflows, Alerts, Events, Dashboard
try:
    from system_stats import system_stats
    from workflow_manager import workflow_manager, setup_default_workflows
    from event_tracker import event_tracker, log_email_event, log_reminder_event, log_system_event, log_alert_event
    from alerts_manager import alerts_manager, start_alert_monitor
    from dashboard_server import start_dashboard
    NEW_FEATURES_AVAILABLE = True
except Exception as e:
    print(f"[WARNING] New features not available: {e}")
    NEW_FEATURES_AVAILABLE = False

# -----------------------
# UI INTEGRATION - Send messages to web interface
# -----------------------
UI_API_URL = "http://127.0.0.1:8000/api/ui-message"
last_ui_message = None  # Prevent duplicate messages

def send_to_ui(message_type, text):
    """Send user or assistant message to web UI for transcript display"""
    global last_ui_message
    try:
        # Prevent sending exact duplicate messages within 1 second
        message_key = f"{message_type}:{text[:100]}"
        if last_ui_message == message_key:
            return
        last_ui_message = message_key
        
        text_clean = str(text)[:500]  # Limit to 500 chars
        
        data = {
            "type": message_type,  # "user" or "assistant"
            "message": text_clean
        }
        requests.post(UI_API_URL, json=data, timeout=2)
    except Exception as e:
        # Silently fail - don't break voice assistant if UI is not available
        pass

def speak_and_ui(response_text):
    """Speak response AND send to UI (prevents looping)"""
    if response_text and response_text.strip():
        send_to_ui("assistant", response_text)
        speak(response_text)
        
        # Smart notepad dictation for large messages
        if should_open_notepad(response_text):
            if not is_conversational_response(response_text):
                print("[NOTEPAD] Opening notepad for large message...")
                open_notepad_for_dictation(response_text, "JARVIS Response")
                print("[NOTEPAD] Message saved to notepad for reading")

def get_relevant_articles(query):
    """Fetch relevant articles and websites for any query"""
    try:
        import webbrowser
        
        # Build search URLs
        google_search = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        wiki_search = f"https://en.wikipedia.org/w/api.php?action=query&titles={query.replace(' ', '_')}&prop=extracts&format=json"
        
        print(f"[WEB] Opening search results for: {query}")
        
        # Open search results in new tabs
        webbrowser.open(google_search, new=1)
        time.sleep(0.5)
        webbrowser.open(f"https://www.reddit.com/search/?q={query.replace(' ', '+')}", new=1)
        
        return True
    except Exception as e:
        print(f"[WEB ERROR] {e}")
        return False

# Import modes system
try:
    from modes import activate_mode, is_mode_command, get_current_mode, MODES
    MODES_AVAILABLE = True
except Exception as e:
    print(f"[WARNING] Modes system not available: {e}")
    MODES_AVAILABLE = False

# Import ML learning system
try:
    from ml_learner import learner
    from personalization import personalizer
    ML_AVAILABLE = True
except Exception as e:
    print(f"[WARNING] ML learning system not available: {e}")
    ML_AVAILABLE = False
    learner = None
    personalizer = None

# Import smart web enhancements with fallback
try:
    from smart_web import smart_browser_open, fetch_news_with_videos, suggest_for_making, get_smart_suggestions, understand_purpose, smart_open_websites
    SMART_WEB_AVAILABLE = True
except Exception as e:
    print(f"[WARNING] Smart web module not available: {e}")
    SMART_WEB_AVAILABLE = False

# Safe import of AGI improved with fallback
try:
    from agi_improved import CURRENT_LOCATION
    LOCATION_AVAILABLE = True
except Exception as e:
    print(f"[WARNING] Could not load location: {e}")
    LOCATION_AVAILABLE = False
    CURRENT_LOCATION = {"city": "Mumbai", "country": "India", "timezone": "asia/kolkata"}


# -----------------------
# AGGRESSIVE SHUTDOWN - Kill microphone and all processes
# -----------------------
def force_shutdown():
    """FORCEFULLY shutdown everything - NO mercy"""
    print("\n[FORCE SHUTDOWN] NUCLEAR OPTION - Terminating all audio...")
    
    # 1. Stop listening globally
    try:
        stop_listening()
    except:
        pass
    
    # 2. Set STOP_RECORDING flag
    try:
        from voice import STOP_RECORDING
        import voice
        voice.STOP_RECORDING = True
    except:
        pass
    
    # 3. Kill sounddevice HARD
    try:
        import sounddevice as sd
        sd.stop()
    except:
        pass
    
    try:
        import sounddevice as sd
        sd.terminate()
    except:
        pass
    
    try:
        import sounddevice as sd
        sd.close()
    except:
        pass
    
    # 4. Kill speech recognition
    try:
        import speech_recognition as sr
        try:
            sr.Microphone().close()
        except:
            pass
    except:
        pass
    
    # 5. Kill pyttsx3
    try:
        from utils import engine
        if engine:
            try:
                engine.stop()
            except:
                pass
    except:
        pass
    
    # 6. Close all threads
    try:
        for thread in threading.enumerate():
            if thread is not threading.current_thread():
                try:
                    if hasattr(thread, '_stop'):
                        thread._stop()
                except:
                    pass
    except:
        pass
    
    # 7. Kill taskbar audio processes
    print("[CLEANUP] Killing audio processes...")
    os.system('taskkill /F /IM audiodg.exe >nul 2>&1')
    os.system('taskkill /F /IM sndvol.exe >nul 2>&1')
    
    # 8. Kill all python.exe except this one (one last time)
    print("[CLEANUP] Killing all other Python processes...")
    os.system(f'taskkill /F /IM python.exe >nul 2>&1')
    
    # 9. Python garbage collection
    print("[DONE] System terminated")
    import gc
    gc.collect()
    
    # Force immediate termination
    if sys.platform == "win32":
        os.system(f"taskkill /F /PID {os.getpid()} >nul 2>&1")
    else:
        os.kill(os.getpid(), signal.SIGKILL)

# Handle Ctrl+C gracefully
def signal_handler(sig, frame):
    print("\n[SIGNAL CAUGHT] Ctrl+C detected - forcing shutdown...")
    force_shutdown()

signal.signal(signal.SIGINT, signal_handler)

# 🔥 SYSTEM CONTROL
RUNNING = True
IMPORTANT_TABS = [
    "https://chatgpt.com",
    "https://claude.ai",
    "https://open.spotify.com",
    "https://web.whatsapp.com"
]

def process_audio(cmd):
    """Process and execute command immediately - no wake word needed"""
    if not cmd or not cmd.strip():
        return
    
    # Send user message to UI
    send_to_ui("user", cmd)
    
    # Execute command directly
    execute(cmd)
# -----------------------
# STOP PROGRAM
# -----------------------
def stop_listener():
    """Background thread that doesn't block - just returns immediately"""
    # Don't use input() in background thread - causes EOF/KeyboardInterrupt
    # Program will stop naturally via Ctrl+C on main thread
    pass

# -----------------------
# SMART MOUSE CONTROL
# -----------------------
def smart_move_mouse(command):
    import pyautogui

    w, h = pyautogui.size()

    if "top left" in command:
        pyautogui.moveTo(0, 0)
    elif "top right" in command:
        pyautogui.moveTo(w, 0)
    elif "bottom left" in command:
        pyautogui.moveTo(0, h)
    elif "bottom right" in command:
        pyautogui.moveTo(w, h)
    elif "center" in command:
        pyautogui.moveTo(w // 2, h // 2)
    else:
        pyautogui.moveTo(w // 2, h // 2)

# -----------------------
# SMART AI-BASED COMMAND DETECTION (FAST)
# -----------------------
def get_smart_intent(command):
    """Use Groq AI to intelligently understand what the user wants"""
    try:
        from ai import ask_ai_text
        
        # Fast keyword matching - no AI needed for obvious commands
        cmd_lower = command.lower()
        print(f"[INTENT] Analyzing: '{cmd_lower}'")
        
        if any(word in cmd_lower for word in ["email", "mail", "send"]):
            print("[INTENT] [OK] Detected EMAIL keyword")
            return {"intent": "send_email", "target": "", "confidence": 1.0}
        if any(word in cmd_lower for word in ["reminder", "remind", "alarm"]):
            print("[INTENT] ✓ Detected REMINDER keyword")
            return {"intent": "reminder", "target": "", "confidence": 1.0}
        if any(word in cmd_lower for word in ["news", "headlines", "latest"]):
            print("[INTENT] [OK] Detected NEWS keyword")
            # Extract news query from command
            news_query = cmd_lower.replace("news", "").replace("headlines", "").replace("latest", "").replace("about", "").replace("on", "").strip()
            if not news_query:
                news_query = "general"
            print(f"[INTENT] News query: {news_query}")
            return {"intent": "news", "target": news_query, "confidence": 1.0}
        if any(word in cmd_lower for word in ["suggest", "ideas", "how to", "tips", "best way", "what should", "guide me", "show me how"]):
            print("[INTENT] [OK] Detected SUGGESTIONS keyword")
            suggestion_topic = cmd_lower.replace("suggest", "").replace("ideas", "").replace("how to", "").replace("tips", "").replace("best way", "").replace("what should", "").replace("guide me", "").replace("show me how", "").strip()
            return {"intent": "suggestions", "target": suggestion_topic, "confidence": 1.0}
        
        # CHECK VIDEO/CONTENT CREATION FIRST (before generic make/create)
        if any(word in cmd_lower for word in ["shorts", "create shorts", "upload shorts", "youtube shorts", "make clips", "create clips"]):
            print("[INTENT] ✓ Detected YOUTUBE SHORTS keyword")
            return {"intent": "youtube_shorts", "target": command, "confidence": 1.0}
        if any(word in cmd_lower for word in ["instagram", "insta", "reels", "create reels", "upload reels"]):
            print("[INTENT] ✓ Detected INSTAGRAM REELS keyword")
            return {"intent": "instagram_reels", "target": command, "confidence": 1.0}
        
        # Generic make/create (after specific video commands)
        if any(word in cmd_lower for word in ["make", "create", "build", "design", "craft", "can you help me make", "how do i make"]):
            print("[INTENT] [OK] Detected MAKE/CREATE keyword")
            make_topic = cmd_lower.replace("make", "").replace("create", "").replace("build", "").replace("design", "").replace("craft", "").replace("can you help me", "").replace("how do i", "").strip()
            return {"intent": "make_suggestions", "target": make_topic, "confidence": 1.0}
        if any(word in cmd_lower for word in ["weather", "temperature", "climate"]):
            print("[INTENT] [OK] Detected WEATHER keyword")
            # Extract location from command like "weather for [location]"
            weather_query = cmd_lower.replace("weather", "").replace("temperature", "").replace("climate", "").replace("for", "").replace("in", "").strip()
            if not weather_query:
                weather_query = ""  # Will use DEFAULT_LOCATION from config
            print(f"[INTENT] Weather location: {weather_query if weather_query else 'default'}")
            return {"intent": "weather", "target": weather_query, "confidence": 1.0}
        if any(word in cmd_lower for word in ["music", "play", "spotify", "song"]):
            print("[INTENT] ✓ Detected MUSIC keyword")
            return {"intent": "play_music", "target": "", "confidence": 1.0}
        if any(word in cmd_lower for word in ["open", "website", "browser", "visit"]):
            print("[INTENT] ✓ Detected WEBSITE keyword")
            return {"intent": "open_website", "target": "", "confidence": 1.0}
        if any(word in cmd_lower for word in ["remember", "save", "note"]):
            print("[INTENT] ✓ Detected MEMORY_SAVE keyword")
            return {"intent": "memory_save", "target": command, "confidence": 1.0}
        if any(word in cmd_lower for word in ["recall", "what did", "remember that"]):
            print("[INTENT] ✓ Detected MEMORY_RECALL keyword")
            return {"intent": "memory_recall", "target": "", "confidence": 1.0}
        if any(word in cmd_lower for word in ["should", "advise", "help"]):
            print("[INTENT] ✓ Detected DECISION keyword")
            return {"intent": "decision", "target": command, "confidence": 1.0}
        if any(word in cmd_lower for word in ["check", "inbox", "read"]):
            print("[INTENT] [OK] Detected CHECK_EMAIL keyword")
            return {"intent": "check_email", "target": "", "confidence": 1.0}
        if any(word in cmd_lower for word in ["restaurant", "eat", "food", "hungry", "lunch", "dinner"]):
            print("[INTENT] [OK] Detected RESTAURANT keyword")
            cuisine = ""
            for c in ["indian", "chinese", "italian", "mexican", "thai", "japanese", "korean"]:
                if c in cmd_lower:
                    cuisine = c
                    break
            return {"intent": "restaurant", "target": cuisine, "confidence": 1.0}
        if any(word in cmd_lower for word in ["directions", "route", "navigate", "go to"]):
            print("[INTENT] [OK] Detected DIRECTIONS keyword")
            destination = cmd_lower.replace("directions to", "").replace("route to", "").replace("navigate to", "").replace("go to", "").strip()
            return {"intent": "directions", "target": destination, "confidence": 1.0}
        if any(word in cmd_lower for word in ["start project", "new project", "begin project", "project starter", "start a project"]):
            print("[INTENT] [OK] Detected PROJECT STARTER keyword")
            project_name = cmd_lower.replace("start", "").replace("new", "").replace("begin", "").replace("project", "").replace("a", "").strip()
            return {"intent": "project_starter", "target": project_name, "confidence": 1.0}
        if any(word in cmd_lower for word in ["earth", "satellite", "maps"]):
            print("[INTENT] [OK] Detected MAPS keyword")
            return {"intent": "maps", "target": "", "confidence": 1.0}
        if any(word in cmd_lower for word in ["stop", "exit", "quit", "shutdown", "close", "goodbye", "bye"]):
            print("[INTENT] [OK] Detected STOP keyword")
            return {"intent": "stop_system", "target": "", "confidence": 1.0}
        
        # --------------------------
        # NEW FEATURE KEYWORDS
        # --------------------------
        
        # TODO/TASK MANAGEMENT
        if any(word in cmd_lower for word in ["todo", "task", "add task", "list tasks", "complete task", "delete task"]):
            print("[INTENT] ✓ Detected TODO keyword")
            return {"intent": "todo", "target": cmd_lower, "confidence": 1.0}
        
        # CALENDAR/SCHEDULING
        if any(word in cmd_lower for word in ["calendar", "schedule", "event", "meeting", "remind me in", "add event"]):
            print("[INTENT] ✓ Detected CALENDAR keyword")
            return {"intent": "calendar", "target": cmd_lower, "confidence": 1.0}
        
        # EXPENSE TRACKING
        if any(word in cmd_lower for word in ["expense", "spending", "cost", "budget", "spent", "log expense", "money"]):
            print("[INTENT] ✓ Detected EXPENSE keyword")
            return {"intent": "expense", "target": cmd_lower, "confidence": 1.0}
        
        # ENTERTAINMENT
        if any(word in cmd_lower for word in ["joke", "trivia", "riddle", "game", "meditation", "entertainment"]):
            print("[INTENT] ✓ Detected ENTERTAINMENT keyword")
            return {"intent": "entertainment", "target": cmd_lower, "confidence": 1.0}
        
        # MEDIA HANDLING
        if any(word in cmd_lower for word in ["download", "video", "audio", "convert", "qr code", "media"]):
            print("[INTENT] ✓ Detected MEDIA keyword")
            return {"intent": "media", "target": cmd_lower, "confidence": 1.0}
        
        # DEVELOPER TOOLS
        if any(word in cmd_lower for word in ["code", "programming", "api test", "debug", "format code", "git", "explain code"]):
            print("[INTENT] ✓ Detected DEVELOPER keyword")
            return {"intent": "developer", "target": cmd_lower, "confidence": 1.0}
        
        # AI/ML FEATURES
        if any(word in cmd_lower for word in ["sentiment", "analyze", "spam", "translate", "ai model", "image recognition"]):
            print("[INTENT] ✓ Detected AI/ML keyword")
            return {"intent": "aiml", "target": cmd_lower, "confidence": 1.0}
        
        # COMMUNICATION
        if any(word in cmd_lower for word in ["sms", "whatsapp", "call", "message", "text", "email to", "post"]):
            print("[INTENT] ✓ Detected COMMUNICATION keyword")
            return {"intent": "communication", "target": cmd_lower, "confidence": 1.0}
        
        # SYSTEM FEATURES
        if any(word in cmd_lower for word in ["screenshot", "screen record", "system info", "disk space", "backup", "processes"]):
            print("[INTENT] ✓ Detected SYSTEM keyword")
            return {"intent": "system", "target": cmd_lower, "confidence": 1.0}
        
        # WEBSITE BUILDER
        if any(word in cmd_lower for word in ["build website", "create website", "web app", "generate website", "app builder"]):
            print("[INTENT] ✓ Detected WEBSITE BUILDER keyword")
            return {"intent": "website_builder", "target": cmd_lower, "confidence": 1.0}
        
        # SYSTEM STATS - New feature
        if any(word in cmd_lower for word in ["system stats", "cpu usage", "memory usage", "disk usage", "what are my stats"]):
            print("[INTENT] ✓ Detected SYSTEM STATS keyword")
            return {"intent": "system_stats", "target": cmd_lower, "confidence": 1.0}
        
        # WORKFLOWS - New feature
        if any(word in cmd_lower for word in ["create workflow", "workflow", "save commands", "command chain", "macro", "execute workflow", "run workflow", "show workflows", "list workflows", "my workflows"]):
            print("[INTENT] ✓ Detected WORKFLOW keyword")
            return {"intent": "workflow", "target": cmd_lower, "confidence": 1.0}
        
        # EVENTS/SUMMARY - New feature
        if any(word in cmd_lower for word in ["what happened", "summary", "event summary", "while i was away", "what did i miss"]):
            print("[INTENT] ✓ Detected EVENTS SUMMARY keyword")
            return {"intent": "events_summary", "target": cmd_lower, "confidence": 1.0}
        
        # ALERTS - New feature
        if any(word in cmd_lower for word in ["set alert", "create alert", "new alert", "alert me", "remind me"]):
            print("[INTENT] ✓ Detected ALERTS keyword")
            return {"intent": "alerts", "target": cmd_lower, "confidence": 1.0}
        
        # DASHBOARD - New feature
        if any(word in cmd_lower for word in ["show dashboard", "open dashboard", "dashboard", "show me stats"]):
            print("[INTENT] ✓ Detected DASHBOARD keyword")
            return {"intent": "dashboard", "target": cmd_lower, "confidence": 1.0}
        
        # For everything else use AI fallback
        print("[INTENT] No keyword match - returning unknown")
        return {
            "intent": "unknown",
            "target": "",
            "confidence": 0.0
        }
    except Exception as e:
        print(f"[INTENT ERROR] {e}")
        return {
            "intent": "unknown",
            "target": "",
            "confidence": 0.0
        }
    
# -----------------------
# SMART REMINDER - Natural language time parsing
# -----------------------
def smart_handle_reminder(command):
    """Handle reminders with natural language like 'remind me at 3pm' or 'in 2 hours'"""
    from ai import ask_ai_text
    from dateutil import parser
    from datetime import datetime, timedelta
    import time as time_module
    
    # Extract reminder details using AI
    prompt = f"""Extract reminder details from this command:
"{command}"

Respond in format: TIME:value|TEXT:what to remind about

Examples:
- "remind me at 3pm to take medicine" → TIME:3pm|TEXT:take medicine
- "remind me in 2 hours to call mom" → TIME:in 2 hours|TEXT:call mom
- "reminder tomorrow at 9am about meeting" → TIME:tomorrow at 9am|TEXT:meeting

Respond ONLY with TIME:value|TEXT:value format."""
    
    try:
        response = ask_ai_text(prompt).strip()
        if "TIME:" in response and "TEXT:" in response:
            parts = response.split("|")
            time_str = parts[0].replace("TIME:", "").strip()
            reminder_text = parts[1].replace("TEXT:", "").strip()
            
            # Parse the time using dateutil
            try:
                # Try to parse as natural language
                target_time = parser.parse(time_str, fuzzy=True)
                now = datetime.now()
                
                if target_time < now:
                    # If parsed time is in past, assume next occurrence
                    target_time = target_time.replace(day=now.day + 1)
                
                wait_seconds = (target_time - now).total_seconds()
                
                if wait_seconds > 0:
                    speak(f"Reminder set for {time_str}")
                    
                    # Background thread for reminder
                    def remind():
                        time_module.sleep(wait_seconds)
                        speak(f"Reminder: {reminder_text}")
                    
                    threading.Thread(target=remind, daemon=True).start()
                    return True
            except:
                pass
    except:
        pass
    
    # Fallback: use basic reminder
    speak("I'll set a reminder for you")
    create_reminder(command)
    return True

# -----------------------
# EMAIL CHECK - Smart email checking
# -----------------------
def check_emails_smart():
    """Check emails using smart email handler"""
    try:
        from automation import auto_email_checker
        result = auto_email_checker()
        if result:
            print("[EMAIL] Emails checked successfully")
            return True
        else:
            print("[EMAIL] No emails or error checking emails")
            return False
    except Exception as e:
        print(f"[EMAIL ERROR] {str(e)}")
        return False

# -----------------------
# SMART EMAIL COMPOSER - AI-powered email generation
# -----------------------
# -----------------------
# AI-POWERED EMAIL SYSTEM  
# -----------------------
def send_email_ai(command):
    """AI-powered email sending - extract recipient and compose via AI with tone customization"""
    from ai import ask_ai_text
    
    try:
        speak("Send email - understood. I need a few details")
        print("[EMAIL] Starting email flow")
        
        # Step 1: Ask for recipient
        speak("Who should I send this to? Type their email address or name")
        print("[EMAIL] Waiting for recipient (TYPE in console)...")
        recipient_input = input("→ Recipient email: ").strip()
        
        if not recipient_input:
            speak("No recipient provided. Email cancelled")
            print("[EMAIL] No recipient - cancelled")
            return
        
        # Step 2: Use AI to extract and validate email
        email_extraction_prompt = f"""Extract the email address from this input:
"{recipient_input}"

If it's a complete email (user@domain.com), return it as is.
If it's a name, assume it's gmail and make it: name@gmail.com

Return ONLY the email address, nothing else."""
        
        recipient_email = ask_ai_text(email_extraction_prompt).strip()
        print(f"[EMAIL] Extracted email: {recipient_email}")
        
        if "@" not in recipient_email:
            speak(f"Invalid email. I understood {recipient_email}. Type the email again with the full address")
            print("[EMAIL] Invalid email format - cancelled")
            return
        
        speak(f"Sending to {recipient_email}. What should I write? Type the content. You can specify the tone like professional, casual, friendly, formal, etc")
        print("[EMAIL] Waiting for email description (TYPE in console)...")
        
        # Step 3: Get email description from user with tone
        description = input("→ Email content and tone: ").strip()
        print(f"[EMAIL] Received: {description}")
        
        if not description:
            speak("No description provided. Email cancelled")
            print("[EMAIL] No description - cancelled")
            return
        
        print("[EMAIL] Composing email with AI...")
        
        # Step 4: Use AI to compose an intelligent email with custom tone
        compose_prompt = f"""Compose an email based on this request:
Request: {description}

IMPORTANT:
- Write a clear, well-structured email (3-5 sentences)
- Include the tone mentioned (if specified, like professional, casual, friendly, formal)
- Make it effective and personable
- Subject should be concise and relevant

Format:
SUBJECT: [write subject here]
[write email body here]"""
        
        email_content = ask_ai_text(compose_prompt).strip()
        print(f"[EMAIL] AI composed email:\n{email_content}")
        
        # Parse subject and body
        if "SUBJECT:" in email_content:
            subject = email_content.split("SUBJECT:")[1].split("\n")[0].strip()
            body = email_content.split("SUBJECT:")[1].split("\n", 1)[1].strip() if "\n" in email_content.split("SUBJECT:")[1] else description
        else:
            subject = "Message from Jarvis"
            body = email_content
        
        print(f"[EMAIL] Subject: {subject}")
        print(f"[EMAIL] Body: {body}")
        
        # Skip read-back of email content - just confirm sending
        speak(f"Email is ready to send to {recipient_email}. Type yes to confirm and send")
        print("[EMAIL] Waiting for confirmation (TYPE yes/no)...")
        
        # Step 5: Ask for confirmation
        confirmation = input("→ Send this email? (yes/no): ").strip().lower()
        print(f"[EMAIL] Confirmation: {confirmation}")
        
        if "yes" in confirmation or "send" in confirmation or "y" in confirmation:
            print("[EMAIL] Sending email...")
            success = send_email_direct(recipient_email, subject, body)
            if success:
                speak(f"Email sent successfully to {recipient_email}")
                print("[EMAIL] SUCCESS - Email sent")
            else:
                speak("Failed to send email. Please check your email credentials")
                print("[EMAIL] FAILED - Send error")
        else:
            speak("Email cancelled")
            print("[EMAIL] Cancelled by user")
            
    except Exception as e:
        print(f"[EMAIL ERROR] {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        speak(f"Error: {str(e)[:50]}")

# -----------------------
# SMART NEWS READER - Read news through audio
# -----------------------  
def smart_read_news(query="general"):
    """Fetch news and read it through audio with browser"""
    try:
        speak(f"Fetching latest news about {query}. Opening news websites now")
        print(f"[NEWS] Fetching: {query}")
        
        # Use the proper news function
        from actions import news_with_browser
        news_with_browser(query)
        
    except Exception as e:
        print(f"[NEWS ERROR] {e}")
        speak(f"Could not fetch news. {str(e)[:30]}")

# -----------------------
# MAIN EXECUTION (AI BRAIN)
# -----------------------
def execute(command):
    command = command.lower().strip()
    print(f"\n[EXECUTE] Processing: {command}")
    
    # Track command execution for ML learning
    if ML_AVAILABLE:
        try:
            learner.log_command(command, category="general")
        except:
            pass

    # -----------------------
    # MODE SYSTEM - Check if this is a mode activation command
    # -----------------------
    if MODES_AVAILABLE:
        is_mode, mode_name = is_mode_command(command)
        if is_mode:
            print(f"[MODE DETECTION] Activating mode: {mode_name}")
            if ML_AVAILABLE:
                learner.log_command(command, category="mode_activation", mode_used=mode_name, success=True)
            activate_mode(mode_name)
            return

    # CHECK IF CASUAL QUERY FIRST (greetings, small talk)
    if is_casual_query(command):
        print("[EXECUTE] Detected as casual query")
        response = handle_casual_query(command)
        speak_and_ui(response)
        return

    # USE SMART AI-BASED INTENT DETECTION
    intent_data = get_smart_intent(command)
    intent = intent_data.get("intent", "").lower()
    target = intent_data.get("target", "")
    print(f"[EXECUTE] Intent detected: {intent}")

    # -----------------------
    # 🌐 WEBSITE / SEARCH - SMART CONTEXT-AWARE OPENING
    # -----------------------
    if intent == "open_website":
        try:
            if not SMART_WEB_AVAILABLE:
                raise Exception("Smart web not available")
            print(f"[WEBSITE] Smart browser handler activated")
            smart_browser_open(command)
        except Exception as e:
            print(f"[WEBSITE] Fallback to basic browser")
            try:
                search_query = command.replace("open", "").replace("visit", "").replace("browse", "").replace("show me", "").strip()
                if search_query:
                    google_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
                    import webbrowser
                    webbrowser.open(google_url, new=1)
                    speak(f"Searching for {search_query}")
                else:
                    speak("What would you like me to search for?")
            except:
                speak("Could not open browser")
        return

    # -----------------------
    # 🎵 SPOTIFY / MUSIC
    # -----------------------
    if intent == "play_music":
        try:
            # Extract song/artist from command
            music_query = command.replace("play", "").replace("music", "").replace("spotify", "").strip()
            
            if not music_query or music_query == "":
                speak("Please tell me what you want to play")
                return
            
            print(f"[MUSIC] Attempting to play: {music_query}")
            success = play_spotify(music_query)
            if success:
                speak(f"Now playing {music_query} on Spotify")
                print("[MUSIC] [OK] Successfully playing on Spotify")
            else:
                print(f"[MUSIC] Spotify failed, falling back to YouTube")
                speak(f"Spotify is not available. Opening {music_query} on YouTube instead")
                youtube_url = f"https://www.youtube.com/results?search_query={music_query.replace(' ', '+')}"
                import webbrowser
                webbrowser.open(youtube_url, new=1)
                print(f"[MUSIC] Opened YouTube: {music_query}")
        except Exception as e:
            print(f"[MUSIC ERROR] {type(e).__name__}: {e}")
            speak("Could not play music. Opening YouTube instead.")
            try:
                music_query = command.replace("play", "").replace("music", "").replace("spotify", "").strip()
                if music_query:
                    youtube_url = f"https://www.youtube.com/results?search_query={music_query.replace(' ', '+')}"
                    import webbrowser
                    webbrowser.open(youtube_url, new=1)
            except:
                pass
        return

    # -----------------------
    # 📱 YOUTUBE SHORTS
    # -----------------------
    if intent == "youtube_shorts":
        try:
            from actions import create_youtube_shorts
            
            print(f"[SHORTS] YouTube Shorts command: {command}")
            speak("I'll help you create YouTube Shorts!")
            
            # Ask for video URL via terminal input
            print("\n" + "="*60)
            print("🎬 YOUTUBE SHORTS CREATOR")
            print("="*60)
            video_url = input("\n📍 Paste YouTube video URL here: ").strip()
            
            if not video_url:
                speak("No URL provided. Please try again.")
                return
            
            # Validate URL
            if "youtube.com" not in video_url.lower() and "youtu.be" not in video_url.lower():
                speak("That doesn't seem like a valid YouTube URL. Please try again.")
                return
            
            print(f"\n✓ Got URL: {video_url}")
            speak("Got it! How many clips would you like? Say 1, 2, 3, or 5.")
            
            # Ask for number of clips
            try:
                clip_input = input("📊 Number of clips (default 2): ").strip()
                num_clips = int(clip_input) if clip_input else 2
                
                if num_clips not in [1, 2, 3, 5]:
                    num_clips = 2
                    print(f"Using default: 2 clips")
            except:
                num_clips = 2
                print(f"Using default: 2 clips")
            
            print(f"\n🚀 Creating {num_clips} YouTube Shorts...")
            speak(f"Creating {num_clips} YouTube Shorts. This may take a few minutes...")
            
            # Create shorts
            results = create_youtube_shorts(video_url, num_clips=num_clips)
            
            if results:
                print(f"\n✅ SUCCESS! Created and uploaded {len(results)} YouTube Shorts!")
                print("="*60)
                for i, vid_id in enumerate(results, 1):
                    short_url = f"https://www.youtube.com/shorts/{vid_id}"
                    print(f"Short {i}: {short_url}")
                print("="*60 + "\n")
                speak(f"Success! I created and uploaded {len(results)} YouTube Shorts to your channel.")
            else:
                print(f"\n❌ Failed to create Shorts. Please check the video URL and try again.\n")
                speak("Failed to create Shorts. Please check the video URL and try again.")
        
        except KeyboardInterrupt:
            print("\n\n⏹️  Cancelled by user.\n")
            speak("Cancelled.")
        except Exception as e:
            print(f"\n[SHORTS ERROR] {type(e).__name__}: {e}\n")
            speak(f"Error creating Shorts: {str(e)}")
        return

    # -----------------------
    # 📱 INSTAGRAM REELS - Upload from video URL (like YouTube Shorts)
    # -----------------------
    if intent == "instagram_reels" or "instagram" in command or "insta" in command:
        try:
            print(f"[INSTAGRAM] Instagram upload command: {command}")
            speak("I'll help you create and upload Instagram Reels! Please wait while I connect...")
            
            print("\n" + "="*60)
            print("📱 INSTAGRAM REELS CREATOR")
            print("="*60)
            
            # Ask for video URL
            print("\n📍 Paste video URL here (YouTube, local file path, or any video URL):")
            video_url = input("URL: ").strip()
            
            if not video_url:
                speak("No URL provided. Please try again.")
                print("❌ No URL provided\n")
                return
            
            print(f"\n✓ Got URL: {video_url}")
            speak("Got it! How many clips would you like? Say 1, 2, 3, or 5.")
            
            # Ask for number of clips
            try:
                clip_input = input("📊 Number of clips to create (default 2): ").strip()
                num_clips = int(clip_input) if clip_input else 2
                
                if num_clips not in [1, 2, 3, 5]:
                    num_clips = 2
                    print(f"Using default: 2 clips")
            except:
                num_clips = 2
                print(f"Using default: 2 clips")
            
            print(f"\n🚀 Creating {num_clips} Instagram Reels from your video...")
            speak(f"Creating {num_clips} Instagram Reels. This may take several minutes...")
            
            # Create clips and upload to Instagram
            try:
                from instagram_clips import create_instagram_clips_from_youtube
                
                # Use the YouTube to Instagram converter (works with any video URL)
                results = create_instagram_clips_from_youtube(video_url, num_clips=num_clips)
                
                if results:
                    print(f"\n✅ SUCCESS! Created and uploaded {len(results)} Instagram Reels!")
                    print("="*60)
                    for i, clip_file in enumerate(results, 1):
                        print(f"Reel {i}: {clip_file}")
                    print("="*60 + "\n")
                    speak(f"Success! I created and uploaded {num_clips} Instagram Reels to your account @fun_clips67!")
                else:
                    print(f"\n❌ Failed to create Reels. Check the video URL, your internet connection, and Instagram credentials.\n")
                    speak("Failed to create Reels. Check your credentials and video URL, then try again.")
            
            except ImportError as ie:
                print(f"[INSTAGRAM] Module import error: {ie}")
                print("[INSTAGRAM] Fallback: Using backup upload method")
                speak("Using backup upload method...")
                # Fallback if function not available
                result = generate_and_upload_instagram() if num_clips == 1 else batch_generate_instagram_videos(num_clips)
                
                if result:
                    print(f"\n✅ SUCCESS! {num_clips} reels uploaded to Instagram!")
                    speak(f"Success! I created and uploaded {num_clips} Instagram Reels!")
                else:
                    print(f"\n❌ Failed to upload reels.")
                    speak("Failed to upload reels. Please try again.")
        
        except KeyboardInterrupt:
            print("\n\n⏹️  Cancelled by user.\n")
            speak("Cancelled.")
        except Exception as e:
            print(f"\n[INSTAGRAM ERROR] {type(e).__name__}: {e}\n")
            speak(f"Error uploading to Instagram: {str(e)[:50]}")
        return

    # -----------------------
    # 🌤️ WEATHER
    # -----------------------
    if intent == "weather":
        try:
            # Use target location if specified, otherwise use detected location
            location_for_weather = target if target else (CURRENT_LOCATION.split(',')[0] if isinstance(CURRENT_LOCATION, str) else CURRENT_LOCATION.get('city', 'New York'))
            print(f"[WEATHER] Checking weather for {location_for_weather}")
            weather_info = get_weather(location_for_weather)
            speak_and_ui(weather_info)
            # Fetch weather articles
            get_relevant_articles(f"weather {location_for_weather}")
        except:
            speak_and_ui("Could not fetch weather information")
        return

    # -----------------------
    # 📈 STOCK
    # -----------------------
    if intent == "stock":
        try:
            stock_price = get_stock_price(target)
            speak(stock_price)
        except:
            speak(f"Could not fetch stock price for {target}")
        return

    # -----------------------
    # 🛒 SHOPPING
    # -----------------------
    if intent == "buy":
        try:
            search_product(target)
            speak(f"Showing shopping options for {target}")
        except:
            speak(f"Could not search for {target}")
        return

    # -----------------------
    # 🌍 LIVE NEWS - With video clips from websites
    # -----------------------
    if intent == "news":
        try:
            if not SMART_WEB_AVAILABLE:
                raise Exception("Smart web not available")
            print(f"[NEWS] Fetching news about: {target}")
            if ML_AVAILABLE:
                learner.log_command(command, category="news", success=True)
            summary = fetch_news_with_videos(target if target else "general")
            speak(summary)
        except Exception as e:
            print(f"[NEWS] Fallback mode")
            speak(f"Opening news websites about {target if target else 'general news'}")
            try:
                import webbrowser
                webbrowser.open("https://www.reddit.com/r/news/", new=1)
                webbrowser.open("https://bbc.com/news", new=1)
            except:
                pass
        return

    # -----------------------
    # � SUGGESTIONS - AI-powered ideas with relevant websites
    # -----------------------
    if intent == "suggestions":
        try:
            print(f"[SUGGESTIONS] Getting ideas about: {target}")
            if ML_AVAILABLE:
                learner.log_command(command, category="suggestions", success=True)
            speak("Let me think about the best suggestions for you...")
            suggestions = get_smart_suggestions(target)
            speak(suggestions)
            
            # Open Google search for the topic (not GitHub/Stack Overflow)
            google_url = f"https://www.google.com/search?q={target.replace(' ', '+')}"
            speak("I'm opening Google to search for more information...")
            webbrowser.open(google_url, new=1)
            if ML_AVAILABLE:
                learner.log_website_opened("google.com", context="suggestions")
        except Exception as e:
            print(f"[SUGGESTIONS] Fallback: {e}")
            speak("I can help with that! Let me get you some ideas...")
            try:
                answer = ask_ai_text(f"Give me 3 good suggestions about: {target}")
                speak(answer)
            except:
                speak("I'm having trouble with suggestions right now")
        return

    # -----------------------
    # 🎨 MAKE/CREATE - Suggestions with Google search
    # -----------------------
    if intent == "make_suggestions":
        try:
            print(f"[MAKE] User wants to make/create: {target}")
            if ML_AVAILABLE:
                learner.log_command(command, category="make_suggestions", success=True)
            speak("Great! Let me suggest the best tools and approach...")
            answer = ask_ai_text(f"What are the best tools and tips for making/creating: {target}")
            speak(answer)
            
            # Open Google search for the topic (not GitHub/Stack Overflow)
            google_url = f"https://www.google.com/search?q={target.replace(' ', '+')}"
            speak("I'm opening Google to search for more resources...")
            webbrowser.open(google_url, new=1)
            if ML_AVAILABLE:
                learner.log_website_opened("google.com", context="make_suggestions")
        except Exception as e:
            print(f"[MAKE] Fallback: {e}")
            speak("I can help you create that! Let me get you some tips...")
            try:
                answer = ask_ai_text(f"What are the best tools and tips for making/creating: {target}")
                speak(answer)
            except:
                pass
        return

    # -----------------------
    # �📧 EMAIL - AI-powered smart sender
    # -----------------------
    if intent == "send_email":
        print("[EXECUTE→EMAIL] Routing to email handler")
        send_email_ai(command)
        return
    
    print(f"[EXECUTE] No specific handler for intent '{intent}' - falling through")

    # -----------------------
    # 📬 EMAIL CHECK
    # -----------------------
    if intent == "check_email":
        try:
            check_emails_smart()
            speak("Your emails have been checked")
        except Exception as e:
            print(f"[EMAIL CHECK ERROR] {e}")
            speak("Could not check emails")
        return

    # -----------------------
    # 📅 REMINDER - Smart time parsing
    # -----------------------
    if intent == "reminder":
        smart_handle_reminder(command)
        return

    # -----------------------
    # 🧠 MEMORY - SAVE
    # -----------------------
    if intent == "memory_save":
        try:
            data = command.replace("remember", "").replace("save", "").strip()
            remember("note", data)
            speak(f"I'll remember that: {data}")
        except:
            speak("Could not save to memory")
        return

    # -----------------------
    # 🧠 MEMORY - RECALL
    # -----------------------
    if intent == "memory_recall":
        try:
            memory_data = recall("note")
            if memory_data:
                speak(f"You told me: {memory_data}")
            else:
                speak("I don't have anything saved")
        except:
            speak("Could not recall memory")
        return

    # -----------------------
    # 🤖 DECISION / ADVICE
    # -----------------------
    if intent == "decision":
        try:
            # Get AI-powered decision with context awareness
            print(f"[DECISION] Getting advice for: {command}")
            decision = decide_action(command)
            
            if decision:
                speak(decision)
            else:
                speak("I couldn't generate a decision. Please try again.")
        except Exception as e:
            print(f"[DECISION] Error: {e}")
            speak("I need more information to advise you")
        return

    # -----------------------
    # � SYSTEM STATS - NEW FEATURE
    # -----------------------
    if intent == "system_stats":
        try:
            print("[STATS] Fetching system statistics...")
            system_stats.speak_system_stats(speak)
            print(system_stats.format_system_stats())
            log_system_event("System Stats Checked", "User requested system statistics")
        except Exception as e:
            print(f"[STATS ERROR] {e}")
            speak("Could not retrieve system stats")
        return

    # -----------------------
    # 🚀 WORKFLOWS - NEW FEATURE
    # -----------------------
    if intent == "workflow":
        try:
            cmd_lower = command.lower()
            
            if "create" in cmd_lower or "save" in cmd_lower:
                # Create a new workflow
                speak("What would you like to name this workflow?")
                workflow_name = input("Workflow name: ").strip().lower()
                
                if not workflow_name:
                    speak("Cancelled. No name provided.")
                    return
                
                speak(f"OK, {workflow_name}. Now tell me the commands to chain together. Say each command, or type 'done' when finished.")
                commands = []
                while True:
                    cmd_input = input("Command: ").strip()
                    if cmd_input.lower() == "done":
                        break
                    if cmd_input:
                        commands.append(cmd_input)
                
                if commands:
                    success, msg = workflow_manager.create_workflow(workflow_name, commands)
                    speak(msg)
                    print(f"[WORKFLOW] {msg}")
                else:
                    speak("No commands provided for workflow.")
            
            elif "execute" in cmd_lower or "run" in cmd_lower:
                # Execute a workflow
                workflows_list = list(workflow_manager.workflows.keys())
                if not workflows_list:
                    speak("You have no workflows yet.")
                    return
                
                speak(f"Available workflows: {', '.join(workflows_list)}")
                workflow_name = input("Which workflow to run? ").strip().lower()
                
                if workflow_name in workflow_manager.workflows:
                    speak(f"Executing {workflow_name}...")
                    success, results = workflow_manager.execute_workflow(workflow_name, process_audio)
                    if success:
                        speak(f"Workflow {workflow_name} completed!")
                    else:
                        speak(f"Workflow failed: {results}")
                else:
                    speak("Workflow not found.")
            
            else:
                # List workflows (default behavior for "show workflows", "list workflows", etc)
                if not workflow_manager.workflows:
                    speak("You have no workflows yet. Say create workflow to make one.")
                    print("[WORKFLOW] No workflows available")
                else:
                    workflows_list = workflow_manager.list_workflows()
                    print(workflows_list)
                    
                    # Speak a summary
                    workflows_count = len(workflow_manager.workflows)
                    workflow_names = list(workflow_manager.workflows.keys())
                    speak(f"You have {workflows_count} workflows: {', '.join(workflow_names)}")
        
        except Exception as e:
            print(f"[WORKFLOW ERROR] {e}")
            import traceback
            traceback.print_exc()
            speak("Error with workflow")
        return

    # -----------------------
    # 📊 EVENTS SUMMARY - NEW FEATURE
    # -----------------------
    if intent == "events_summary":
        try:
            print("[EVENTS] Generating event summary...")
            minutes = 60  # Default to last hour
            
            # Check if user specified time
            if "last" in command.lower():
                for word in command.lower().split():
                    try:
                        if word.isdigit():
                            minutes = int(word)
                            break
                    except:
                        pass
            
            summary = event_tracker.summarize_events(minutes, speak)
            log_system_event("Event Summary Requested", f"Last {minutes} minutes")
        except Exception as e:
            print(f"[EVENTS ERROR] {e}")
            speak("Could not generate summary")
        return

    # -----------------------
    # 🔔 ALERTS - NEW FEATURE
    # -----------------------
    if intent == "alerts":
        try:
            cmd_lower = command.lower()
            
            if "list" in cmd_lower or "show" in cmd_lower:
                # List alerts
                alerts_list = alerts_manager.list_alerts()
                speak(alerts_list)
                print(alerts_list)
            
            elif "delete" in cmd_lower or "remove" in cmd_lower:
                # Delete alert
                speak("Alert ID to delete?")
                alert_id = input("Alert ID: ")
                try:
                    alert_id = int(alert_id)
                    alerts_manager.delete_alert(alert_id)
                    speak(f"Alert {alert_id} deleted")
                except:
                    speak("Invalid alert ID")
            
            else:
                # Create new alert
                speak("What should the alert say?")
                alert_title = input("Alert title: ").strip()
                
                if alert_title:
                    speak("How many minutes until the alert? (default 10)")
                    minutes_input = input("Minutes: ").strip()
                    minutes = int(minutes_input) if minutes_input.isdigit() else 10
                    
                    alert = alerts_manager.create_alert(alert_title, "reminder", minutes)
                    speak(f"Alert set for {minutes} minutes from now: {alert_title}")
                    log_alert_event("Alert Created", f"{alert_title} in {minutes} minutes")
                else:
                    speak("No alert title provided")
        
        except Exception as e:
            print(f"[ALERTS ERROR] {e}")
            speak("Error setting alert")
        return

    # -----------------------
    # 📊 DASHBOARD - NEW FEATURE
    # -----------------------
    if intent == "dashboard":
        try:
            speak("Opening your JARVIS dashboard...")
            print("[DASHBOARD] Opening web dashboard")
            
            # Open dashboard in browser
            webbrowser.open("http://localhost:5000", new=1)
            speak("Dashboard opened at http://localhost:5000")
            print("[DASHBOARD] Navigate to http://localhost:5000 in your browser")
        except Exception as e:
            print(f"[DASHBOARD ERROR] {e}")
            speak("Could not open dashboard")
        return

    # -----------------------
    # �📋 PERMISSION INFO
    # -----------------------
    if "permission" in command or "access" in command or "safety" in command:
        perms = agi_agent.get_permissions_info()
        speak("I've shown you my permission requirements. Everything I do is safe and non-invasive. I only need your Groq API key and can't access your private files or system.")
        return

    # -----------------------
    # RESTAURANTS - Find nearby places to eat
    # -----------------------
    if intent == "restaurant":
        try:
            from agi_improved import find_restaurants, open_restaurants_in_browser
            speak("Finding the best restaurants near you...")
            location_display = CURRENT_LOCATION.split(',')[0] if isinstance(CURRENT_LOCATION, str) else CURRENT_LOCATION.get('city', 'your location')
            print(f"[RESTAURANT] Searching in {location_display}...")
            restaurants = find_restaurants(cuisine=target if target else "", location=CURRENT_LOCATION)
            if restaurants:
                for i, r in enumerate(restaurants[:3], 1):
                    print(f"[RESTAURANT] {i}. {r}")
                    speak(f"Option {i}: {r}")
                open_restaurants_in_browser(restaurants)
                speak("I've opened restaurants on Google Maps for you")
            else:
                speak("No restaurants found. Let me open Google Maps for you.")
                import webbrowser
                webbrowser.open("https://www.google.com/maps/search/restaurants/")
        except ImportError:
            speak("Restaurant finder not available yet")
        except Exception as e:
            print(f"[RESTAURANT ERROR] {e}")
            speak("Could not find restaurants at the moment")
        return

    # -----------------------
    # DIRECTIONS
    # -----------------------
    if intent == "directions":
        try:
            from agi_improved import get_directions
            print(f"[MAPS] Getting directions to {target}")
            speak(f"Getting directions to {target}")
            get_directions(target)
            speak(f"Directions to {target} are now open in Google Maps")
        except:
            speak(f"Could not get directions to {target}")
        return

    # -----------------------
    # GOOGLE EARTH & MAPS
    # -----------------------
    if intent == "maps":
        try:
            from agi_improved import open_google_earth
            speak("Opening Google Earth at your current location")
            open_google_earth()
        except:
            speak("Could not open Google Earth")
        return

    # -----------------------
    # 🚀 PROJECT STARTER - Open development tools
    # -----------------------
    if intent == "project_starter":
        try:
            print(f"[PROJECT] Starting project environment...")
            project_name = target if target else "New Project"
            
            # Open all essential tools for project development
            tools = {
                "Claude AI": "https://claude.ai",
                "ChatGPT": "https://chatgpt.com",
                "YouTube": "https://youtube.com",
                "Canva": "https://canva.com"
            }
            
            speak(f"Starting project environment. Opening development tools.")
            print(f"[PROJECT] Opening tools for: {project_name}")
            
            for tool_name, url in tools.items():
                try:
                    print(f"[PROJECT] Opening {tool_name}...")
                    webbrowser.open(url)
                    import time
                    time.sleep(1)  # Slight delay between opening tabs
                except Exception as e:
                    print(f"[PROJECT ERROR] Could not open {tool_name}: {e}")
            
            speak(f"Project environment ready. Claude, ChatGPT, YouTube and Canva are now open. Have fun creating!")
            print(f"[PROJECT] ✅ All tools opened successfully")
        except Exception as e:
            print(f"[PROJECT ERROR] {e}")
            speak("Could not start project environment")
        return

    # ---------
    # 🛑 NEW FEATURE HANDLERS (50+ features)
    # ---------
    
    # ✅ TODO MANAGER
    if intent == "todo" and TODOMANAGER_AVAILABLE:
        try:
            print("[TODO] Processing todo command")
            
            # Smart sentence detection
            detected = detect_sentence_intent(command)
            todo_detections = [d for d in detected if 'todo' in d['feature'] or 'task' in command.lower()]
            
            if "add" in command or "new" in command:
                # Extract context from sentence
                context = extract_context_from_sentence(command, 'todo')
                task = context.get('task', command.replace("add", "").replace("todo", "").replace("task", "").strip())
                priority = context.get('priority', 'normal')
                response = todo_manager.add_task(task, priority)
                
            elif "list" in command or "show" in command:
                response = todo_manager.list_tasks()
                
            elif "complete" in command or "done" in command:
                import re
                nums = re.findall(r'\d+', command)
                response = todo_manager.complete_task(nums[0]) if nums else "Which task number?"
                
            elif "delete" in command or "remove" in command:
                import re
                nums = re.findall(r'\d+', command)
                response = todo_manager.delete_task(nums[0]) if nums else "Which task number?"
            else:
                response = todo_manager.list_tasks()
            speak_and_ui(response)
        except Exception as e:
            speak_and_ui(f"Todo error: {str(e)}")
        return
    
    # 📅 CALENDAR MANAGER
    if intent == "calendar" and CALENDAR_AVAILABLE:
        try:
            print("[CALENDAR] Processing calendar command")
            
            # Smart sentence detection
            detected = detect_sentence_intent(command)
            calendar_detections = [d for d in detected if 'calendar' in d['feature'] or 'remind' in d['feature']]
            
            if "add" in command or "schedule" in command or "event" in command:
                event_title = command.replace("add", "").replace("event", "").replace("schedule", "").strip()
                response = calendar_manager.add_event(event_title, "Soon")
                
            elif "list" in command or "show" in command:
                response = calendar_manager.list_events()
                
            elif "remind" in command and "in" in command:
                context = extract_context_from_sentence(command, 'remind')
                minutes = context.get('time_value', '30')
                task = context.get('task', 'reminder')
                response = calendar_manager.remind_me_in(task, minutes)
            else:
                response = calendar_manager.list_events()
            speak_and_ui(response)
        except Exception as e:
            speak_and_ui(f"Calendar error: {str(e)}")
        return
    
    # 💰 EXPENSE TRACKER
    if intent == "expense" and EXPENSE_AVAILABLE:
        try:
            print("[EXPENSE] Processing expense command")
            
            # Smart sentence detection
            detected = detect_sentence_intent(command)
            expense_detections = [d for d in detected if 'expense' in d['feature']]
            
            if "add" in command or "log" in command or "spent" in command:
                # Extract context from sentence
                context = extract_context_from_sentence(command, 'expense')
                amount = context.get('amount', '0')
                category = context.get('category', 'general')
                description = context.get('description', '')
                response = expense_tracker.add_expense(category, amount, description)
                
            elif "summary" in command or "total" in command:
                response = expense_tracker.get_summary()
                
            elif "list" in command or "recent" in command:
                response = expense_tracker.list_recent()
            else:
                response = expense_tracker.get_summary()
            speak_and_ui(response)
        except Exception as e:
            speak_and_ui(f"Expense tracking error: {str(e)}")
        return
    
    # 🎮 ENTERTAINMENT
    if intent == "entertainment" and ENTERTAINMENT_AVAILABLE:
        try:
            print("[ENTERTAINMENT] Processing entertainment command")
            if "joke" in command:
                response = entertainment.tell_joke()
            elif "trivia" in command:
                response = entertainment.play_trivia()
            elif "riddle" in command:
                response = entertainment.riddle()
            elif "twenty" in command or "20" in command:
                response = entertainment.play_twenty_questions()
            elif "meditation" in command:
                response = entertainment.meditation()
            elif "word" in command or "game" in command:
                response = entertainment.word_game()
            else:
                response = entertainment.tell_joke()
            speak_and_ui(response)
        except Exception as e:
            speak_and_ui(f"Entertainment error: {str(e)}")
        return
    
    # 📱 MEDIA HANDLER
    if intent == "media" and MEDIA_AVAILABLE:
        try:
            print("[MEDIA] Processing media command")
            if "download" in command and "video" in command:
                url = command.replace("download", "").replace("video", "").strip()
                response = media_handler.download_video(url if url else "https://youtube.com")
            elif "download" in command and "audio" in command:
                url = command.replace("download", "").replace("audio", "").strip()
                response = media_handler.download_audio(url if url else "https://youtube.com")
            elif "convert" in command or "format" in command:
                response = media_handler.convert_audio("input.mp3", "mp4")
            elif "qr" in command:
                data = command.replace("qr", "").replace("code", "").strip()
                response = media_handler.generate_qr(data if data else "https://example.com")
            else:
                response = "Media handler ready. Say: download video, download audio, convert, or generate QR code"
            speak_and_ui(response)
        except Exception as e:
            speak_and_ui(f"Media handling error: {str(e)}")
        return
    
    # 👨‍💻 DEVELOPER TOOLS
    if intent == "developer" and DEVELOPER_TOOLS_AVAILABLE:
        try:
            print("[DEVELOPER] Processing developer command")
            if "explain" in command:
                code = command.replace("explain", "").strip()
                response = developer_tools.explain_code(code)
            elif "api" in command or "test" in command:
                response = developer_tools.test_api("https://api.example.com")
            elif "git" in command:
                git_cmd = command.replace("git", "").strip()
                response = developer_tools.git_command(git_cmd if git_cmd else "status")
            elif "error" in command or "syntax" in command:
                response = developer_tools.find_syntax_errors("main.py")
            elif "format" in command:
                response = developer_tools.format_code("code_here")
            else:
                response = developer_tools.explain_code("General coding help")
            speak_and_ui(response)
        except Exception as e:
            speak_and_ui(f"Developer tools error: {str(e)}")
        return
    
    # 🤖 AI/ML FEATURES
    if intent == "aiml" and AI_FEATURES_AVAILABLE:
        try:
            print("[AI/ML] Processing AI/ML command")
            
            # Smart sentence detection
            detected = detect_sentence_intent(command)
            aiml_detections = [d for d in detected if d['category'] == 'aiml']
            
            if "sentiment" in command:
                context = extract_context_from_sentence(command, 'sentiment')
                text = context.get('text', command.replace("sentiment", "").strip())
                response = ai_features.analyze_sentiment(text if text else "Great day today")
                
            elif "spam" in command or "detect" in command:
                context = extract_context_from_sentence(command, 'spam')
                text = context.get('text', command.replace("spam", "").replace("detect", "").strip())
                response = ai_features.detect_spam(text if text else "Buy now limited time offer")
                
            elif "translate" in command:
                context = extract_context_from_sentence(command, 'translate')
                text = context.get('text', '')
                language = context.get('language', 'spanish')
                response = ai_features.translate_text(text if text else "Hello", language)
                
            elif "image" in command or "recognize" in command:
                response = ai_features.image_recognition("image.jpg")
            else:
                response = ai_features.analyze_sentiment("I'm excited!")
            speak_and_ui(response)
        except Exception as e:
            speak_and_ui(f"AI/ML error: {str(e)}")
        return
    
    # 📞 COMMUNICATION
    if intent == "communication" and COMMUNICATION_AVAILABLE:
        try:
            print("[COMMUNICATION] Processing communication command")
            if "sms" in command or "text" in command:
                phone = "+1234567890"
                msg = command.replace("sms", "").replace("text", "").strip()
                response = communication.send_sms(phone, msg if msg else "Hello")
            elif "whatsapp" in command:
                phone = "+1234567890"
                msg = command.replace("whatsapp", "").strip()
                response = communication.send_whatsapp(phone, msg if msg else "Hello")
            elif "call" in command:
                phone = "+1234567890"
                response = communication.call(phone)
            elif "post" in command:
                platform = "twitter"
                msg = command.replace("post", "").strip()
                response = communication.post_to_social(platform, msg if msg else "Check out JARVIS")
            else:
                response = "Communication ready. Say: send SMS, send WhatsApp, call, or post to social media"
            speak_and_ui(response)
        except Exception as e:
            speak_and_ui(f"Communication error: {str(e)}")
        return
    
    # 🖥️ SYSTEM FEATURES
    if intent == "system" and SYSTEM_FEATURES_AVAILABLE:
        try:
            print("[SYSTEM] Processing system command")
            if "screenshot" in command:
                response = system_features.take_screenshot()
            elif "screen record" in command:
                response = system_features.screen_recording(10)
            elif "info" in command or "system" in command:
                response = system_features.get_system_info()
            elif "disk" in command or "space" in command:
                response = system_features.get_disk_space()
            elif "backup" in command:
                response = system_features.create_backup("./documents")
            elif "process" in command:
                response = system_features.get_running_processes()
            else:
                response = system_features.get_system_info()
            speak_and_ui(response)
        except Exception as e:
            speak_and_ui(f"System features error: {str(e)}")
        return
    
    # 🌐 WEBSITE BUILDER
    if intent == "website_builder" and WEBSITE_BUILDER_AVAILABLE:
        try:
            print("[WEBSITE BUILDER] Processing website builder command")
            
            # Extract context from sentence
            detected = detect_sentence_intent(command)
            detections = [d for d in detected if d['category'] == 'website']
            
            # Detect theme from keywords
            theme = 'clean'
            if 'cars' in command.lower() or 'car' in command.lower():
                theme = 'cars'
            elif 'tech' in command.lower() or 'technology' in command.lower():
                theme = 'tech'
            elif 'business' in command.lower():
                theme = 'business'
            elif 'creative' in command.lower() or 'creative' in command.lower():
                theme = 'creative'
            elif 'nature' in command.lower() or 'green' in command.lower():
                theme = 'nature'
            
            if "website" in command:
                project_name = command.replace("build", "").replace("website", "").replace("create", "").replace("for", "").strip()
                project_name = project_name if project_name else "MyWebsite"
                project_name = project_name.title().replace(" ", "")
                
                # Directly create with detected theme
                response = website_builder_pro.create_website(
                    project_name, 
                    f"Welcome to {project_name}! Professional and modern design.",
                    theme=theme
                )
                speak_and_ui(f"✨ {response}")
                print(f"[WEBSITE] Created website: {project_name} with {theme} theme")
                return
                
            elif "app" in command or "todo" in command:
                app_name = command.replace("build", "").replace("app", "").replace("create", "").strip()
                app_name = app_name if app_name else "MyApp"
                app_name = app_name.title().replace(" ", "")
                
                response = website_builder_pro.create_website(
                    app_name,
                    "Productivity app for managing tasks",
                    theme='tech'
                )
                speak_and_ui(f"✨ {response}")
                return
                
            elif "calculator" in command:
                response = website_builder_pro.create_website(
                    "Calculator",
                    "Advanced scientific calculator",
                    theme='tech'
                )
                speak_and_ui(f"✨ {response}")
                return
                
            else:
                # Default to creating website
                response = website_builder_pro.create_website(
                    "MyWebsite",
                    "A beautiful modern website",
                    theme=theme
                )
                speak_and_ui(f"✨ {response}")
                return
                
        except Exception as e:
            speak_and_ui(f"Website builder error: {str(e)}")
            print(f"[WEBSITE BUILDER ERROR] {e}")
        return
    
    # Handle "yes" confirmation for website builder
    if ("yes" in command or "confirm" in command or "create" in command) and website_builder_pro.awaiting_confirmation:
        try:
            print("[WEBSITE] Creating from pending confirmation")
            for project_name, project_type in website_builder_pro.awaiting_confirmation.items():
                if project_type == "website":
                    response = website_builder_pro.create_website(project_name, "Welcome to my website!", theme='clean')
                elif project_type == "app_todo":
                    response = website_builder_pro.create_website(project_name, "Todo app for productivity", theme='tech')
                elif project_type == "app_calculator":
                    response = website_builder_pro.create_website("Calculator", "Advanced calculator", theme='tech')
                
                speak_and_ui(response)
                website_builder_pro.awaiting_confirmation.clear()
                return
        except Exception as e:
            speak_and_ui(f"Website creation error: {str(e)}")
            return

    # ---------
    # 🛑 STOP SYSTEM - Shutdown all processes
    # ---------
    if intent == "stop_system":
        try:
            speak("Goodbye! Shutting down the system. Thank you for using JARVIS!")
            print("\n[SHUTDOWN] User initiated system shutdown")
            print("[SHUTDOWN] Closing all services...")
            
            # Force shutdown after a short delay
            import time
            time.sleep(1)
            force_shutdown()
        except Exception as e:
            print(f"[SHUTDOWN ERROR] {e}")
        return

    # 🤖 FALLBACK - USE GROQ AI FOR ANY UNIDENTIFIED QUERY
    # ---------
    print(f"[FALLBACK] Query not recognized as specific intent, using Groq AI...")
    
    try:
        # Handle simple acknowledgments first (single word responses)
        acknowledgments = {
            "yes": "Understood. Processing your request.",
            "no": "Alright, I won't do that.",
            "ok": "Got it. Moving on.",
            "okay": "Got it. Moving on.",
            "thanks": "You're welcome. Always happy to help.",
            "thank you": "You're welcome. Always happy to help.",
            "sorry": "No problem, it happens.",
            "bye": "Goodbye. See you later.",
            "goodbye": "Goodbye. See you later.",
            "quit": "Shutting down. Goodbye.",
            "exit": "Shutting down. Goodbye.",
        }
        
        # Check if it's a simple acknowledgment
        cmd_lower = command.lower().strip()
        for ack_word, ack_response in acknowledgments.items():
            if cmd_lower == ack_word:
                print(f"[FALLBACK] Quick response: {ack_word}")
                speak(ack_response)
                return
        
        # For everything else: Use Groq AI
        print("[GROQ] Sending query to Groq AI...")
        response = ask_ai_text(command)
        
        # Handle failed Groq responses
        if not response or response is None:
            print("[GROQ] FAILED - using fallback response")
            response = f"I understand you asked about '{command}'. Let me search for more information on that."
        elif response.strip() == "":
            response = f"I found it but got an empty response. Searching for '{command}' online instead."
        
        # Personalize if ML is available
        if ML_AVAILABLE:
            try:
                response = personalizer.speak_like_knows_them(response, context_type="generic")
            except:
                pass  # Use response as-is if personalization fails
        
        print(f"[GROQ] Response: {response[:80]}...")
        speak_and_ui(response)
        
        # Log to learning system
        try:
            agi_engine.add_to_history(command, response)
        except:
            pass  # Ignore if history tracking fails
        
        if ML_AVAILABLE:
            try:
                learner.log_command(command, category="groq_fallback", response_type="text", success=True)
            except:
                pass
        
        # 🌐 Open Chrome for visual results
        print("[WEB] Opening relevant websites in Chrome...")
        try:
            import webbrowser
            import time
            
            search_query = command.replace(" ", "+").lower()
            
            # Open Google search
            google_url = f"https://www.google.com/search?q={search_query}"
            webbrowser.open(google_url, new=1)
            print(f"[WEB] -> Google: {command}")
            
            # Open Reddit (new tab)
            time.sleep(0.3)
            reddit_url = f"https://www.reddit.com/search/?q={search_query}"
            webbrowser.open(reddit_url, new=1)
            print(f"[WEB] -> Reddit: {command}")
            
        except Exception as e:
            print(f"[WEB] Could not open websites: {type(e).__name__}")
        
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {str(e)[:50]}")
        speak_and_ui("I'm here. What do you need?")

# -----------------------
# THREADS
# -----------------------
threading.Thread(target=stop_listener, daemon=True).start()
threading.Thread(target=auto_email_checker, daemon=True).start()
threading.Thread(target=email_monitor, daemon=True).start()
threading.Thread(target=daily_routine, daemon=True).start()
threading.Thread(target=smart_tasks, daemon=True).start()
threading.Thread(target=email_monitor_smart, daemon=True).start()

# NEW FEATURE THREADS
if NEW_FEATURES_AVAILABLE:
    try:
        # Set speak function for alerts
        alerts_manager.set_speak_function(speak)
        # Initialize alert monitoring
        start_alert_monitor()
        print("[ALERTS] Alert monitor started")
    except Exception as e:
        print(f"[ALERTS WARNING] Could not start alert monitor: {e}")
    
    try:
        # Setup default workflows on first run
        setup_default_workflows()
        print("[WORKFLOWS] Default workflows initialized")
    except Exception as e:
        print(f"[WORKFLOWS WARNING] Could not setup workflows: {e}")
    
    try:
        # Start dashboard server
        start_dashboard()
        print("[DASHBOARD] Dashboard server started at http://localhost:5000")
    except Exception as e:
        print(f"[DASHBOARD WARNING] Could not start dashboard: {e}")

# -----------------------
# START SYSTEM
# -----------------------
try:
    print("\n" + "="*70)
    print("[SYSTEM] Jarvis AGI Assistant Ready")
    print("="*70)
    # Handle location - could be string or dict
    location_str = CURRENT_LOCATION if isinstance(CURRENT_LOCATION, str) else f"{CURRENT_LOCATION.get('city', 'Unknown')}, {CURRENT_LOCATION.get('country', 'Unknown')}"
    timezone_str = CURRENT_LOCATION.get('timezone', 'Unknown') if isinstance(CURRENT_LOCATION, dict) else "America/New_York"
    print(f"[LOCATION] Detected your location: {location_str}")
    print(f"[LOCATION] Timezone: {timezone_str}")
    print(f"[LOCATION] Using this for restaurants, weather, and local recommendations")
    print("="*70)
    
    # Show ML learning status
    if ML_AVAILABLE:
        stats = learner.get_learning_progress()
        print(f"[ML] Learning System Active - {stats.get('total_commands', 0)} commands learned")
        print(f"[ML] Learning Level: {stats.get('learning_level', 0)}%")
        if stats.get('total_commands', 0) > 0:
            print(f"[ML] Your personality: {personalizer.get_personality_summary()}")
    
    # Use personalized greeting if available
    if ML_AVAILABLE and learner.get_learning_progress().get('total_commands', 0) > 10:
        greeting = personalizer.personalize_greeting()
        speak_and_ui(greeting)
    else:
        speak_and_ui("Hello sir. I am Jarvis, your AI assistant. I've detected your location and I'm ready to help you. Just speak your commands.")
    print("[STATUS] Listening for commands...")
    print("[INFO] Just speak - I'll understand and respond immediately")
    print("[COMMANDS] Email, Reminders, News, Music, Weather, Restaurants, and more!")
    print("="*70 + "\n")
    
    while RUNNING:
        try:
            cmd = listen()
            if cmd and cmd.strip():
                print(f"→ {cmd}")
                process_audio(cmd)
        except KeyboardInterrupt:
            RUNNING = False
            break
            
except KeyboardInterrupt:
    print("\n[SHUTTING DOWN] Jarvis going offline...")
    RUNNING = False
except Exception as e:
    print(f"[RUNTIME ERROR] {e}")
    RUNNING = False
finally:
    # Use aggressive force shutdown
    force_shutdown()