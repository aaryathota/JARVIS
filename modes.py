"""
ASSISTANT MODES SYSTEM
Different modes with unique speaking styles and app configurations
"""

import webbrowser
import subprocess
import os
import threading
from utils import speak

# Global current mode (default to minimalist)
CURRENT_MODE = "minimalist"

MODES = {
    "work": {
        "name": "Work Mode",
        "tone": "professional",
        "greeting": "Switching to Work Mode. I am now in professional mode, ready to assist with your productivity tasks.",
        "apps": ["vscode", "docker"],
        "websites": ["claude.ai", "chatgpt.com", "google.com"],
        "speaking_style": "formal",
        "opening_message": "Opening work environment: VS Code, Docker, Claude AI, ChatGPT, and Google.",
    },
    "study": {
        "name": "Study Mode",
        "tone": "educational",
        "greeting": "Entering Study Mode. I'll help you learn and research with detailed explanations.",
        "apps": [],
        "websites": ["youtube.com", "khanacademy.org", "udemy.com", "docs.google.com"],
        "speaking_style": "educational",
        "opening_message": "Opening educational resources: YouTube tutorials, Khan Academy, Udemy, and Google Docs.",
    },
    "creative": {
        "name": "Creative Mode",
        "tone": "enthusiastic",
        "greeting": "Let's get creative! I'm now in Creative Mode - super excited to help you bring your ideas to life!",
        "apps": [],
        "websites": ["canva.com", "figma.com", "pinterest.com", "adobe.com", "notion.so"],
        "speaking_style": "casual",
        "opening_message": "Fired up! Opening creative tools: Canva, Figma, Pinterest, Adobe, and Notion. Let's make something amazing!",
    },
    "developer": {
        "name": "Developer Mode",
        "tone": "technical",
        "greeting": "Developer Mode activated. Standing by for coding tasks and debugging.",
        "apps": ["vscode", "docker"],
        "websites": ["github.com", "stackoverflow.com", "replit.com"],
        "speaking_style": "technical",
        "opening_message": "Dev environment ready: VS Code, Docker, GitHub, Stack Overflow, and Replit loaded.",
    },
    "chill": {
        "name": "Chill Mode",
        "tone": "casual",
        "greeting": "Yo, let's relax. Chill Mode is on - time to kick back and have some fun!",
        "apps": [],
        "websites": ["youtube.com", "netflix.com", "spotify.com", "reddit.com"],
        "speaking_style": "casual",
        "opening_message": "All set for some relaxation: YouTube, Netflix, Spotify, and Reddit ready to go. Enjoy!",
    },
    "research": {
        "name": "Research Mode",
        "tone": "analytical",
        "greeting": "Research Mode activated. I will provide detailed, thorough analysis and insights.",
        "apps": [],
        "websites": ["scholar.google.com", "wikipedia.org", "reddit.com", "medium.com", "notion.so"],
        "speaking_style": "detailed",
        "opening_message": "Research environment prepared: Google Scholar, Wikipedia, Reddit, Medium, and Notion ready for deep investigation.",
    },
    "content": {
        "name": "Content Mode",
        "tone": "creative",
        "greeting": "Content Creation Mode engaged! Let's make some engaging, creative content!",
        "apps": [],
        "websites": ["youtube.com", "tiktok.com", "medium.com", "twitter.com", "notion.so"],
        "speaking_style": "expressive",
        "opening_message": "Content creation suite loaded: YouTube, TikTok, Medium, Twitter, and Notion. Time to create magic!",
    },
    "minimalist": {
        "name": "Minimalist Mode",
        "tone": "brief",
        "greeting": "Minimalist Mode. Minimal talking. Direct answers.",
        "apps": [],
        "websites": [],
        "speaking_style": "brief",
        "opening_message": "Minimalist Mode engaged.",
    },
}

def open_apps_for_mode(apps_list):
    """Open VS Code and Docker from desktop"""
    def open_in_background():
        for app in apps_list:
            try:
                if app.lower() == "vscode":
                    # Open VS Code
                    try:
                        subprocess.Popen(["code"])
                        print("[MODES] Opened VS Code")
                    except:
                        # Try alternative paths
                        try:
                            subprocess.Popen("C:\\Users\\Aarya Raghu Thota\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe")
                        except:
                            print("[MODES] Could not find VS Code")
                
                elif app.lower() == "docker":
                    # Open Docker Desktop
                    try:
                        subprocess.Popen(["docker-desktop"])
                        print("[MODES] Opening Docker Desktop")
                    except:
                        try:
                            subprocess.Popen("C:\\Program Files\\Docker\\Docker\\Docker Desktop.exe")
                        except:
                            print("[MODES] Could not find Docker Desktop")
            except Exception as e:
                print(f"[MODES] Error opening {app}: {e}")
            
            import time
            time.sleep(1.5)
    
    threading.Thread(target=open_in_background, daemon=True).start()

def open_websites_for_mode(websites_list):
    """Open websites in browser"""
    def open_in_background():
        for website in websites_list:
            try:
                if not website.startswith("http"):
                    website = f"https://{website}"
                print(f"[MODES] Opening: {website[:50]}")
                webbrowser.open(website, new=1)
                import time
                time.sleep(1.5)
            except Exception as e:
                print(f"[MODES] Error opening {website}: {e}")
    
    threading.Thread(target=open_in_background, daemon=True).start()

def activate_mode(mode_name):
    """Activate a specific mode"""
    global CURRENT_MODE
    
    mode_name = mode_name.lower().strip()
    
    if mode_name not in MODES:
        available = ", ".join(MODES.keys())
        speak(f"Mode not recognized. Available modes: {available}")
        print(f"[MODES] Available: {available}")
        return False
    
    mode = MODES[mode_name]
    CURRENT_MODE = mode_name
    
    print(f"\n{'='*70}")
    print(f"[MODES] Activating: {mode['name'].upper()}")
    print(f"{'='*70}\n")
    
    # Greet the user
    speak(mode["greeting"])
    print(f"[MODES GREETING] {mode['greeting']}")
    
    # Open apps
    if mode["apps"]:
        print(f"[MODES] Opening apps: {', '.join(mode['apps'])}")
        open_apps_for_mode(mode["apps"])
    
    # Open websites
    if mode["websites"]:
        print(f"[MODES] Opening websites: {', '.join(mode['websites'][:3])}...")
        speak(mode["opening_message"])
        open_websites_for_mode(mode["websites"])
    else:
        if mode_name != "minimalist":
            speak(mode["opening_message"])
    
    print(f"[MODES] {mode_name.upper()} mode activated")
    print(f"[MODES] Speaking style: {mode['speaking_style']}\n")
    
    return True

def get_mode_response(command, response):
    """Adjust response based on current mode's speaking style"""
    mode = MODES.get(CURRENT_MODE, MODES["normal"])
    speaking_style = mode.get("speaking_style", "normal")
    
    # For now, just return the response as-is
    # In future, could use AI to rephrase based on tone
    return response

def is_mode_command(command):
    """Check if command is a mode activation"""
    cmd_lower = command.lower()
    
    for mode_name in MODES.keys():
        if f"{mode_name} mode" in cmd_lower or cmd_lower == mode_name:
            return True, mode_name
    
    return False, None

def get_current_mode():
    """Get current mode info"""
    return CURRENT_MODE, MODES.get(CURRENT_MODE, MODES["minimalist"])

def list_all_modes():
    """List all available modes"""
    modes_list = []
    for mode_name, mode_info in MODES.items():
        modes_list.append(f"{mode_info['name']}: {mode_info['tone']} tone")
    return modes_list
