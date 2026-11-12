import time
from actions import create_reminder
from utils import speak

memory = {"emails": []}

def email_monitor():
    """Legacy hook retained without automatic inbox access."""
    print("[EMAIL] Automatic email monitoring is disabled; ask to read emails.")

def daily_routine():
    from control import is_cancelled

    while not is_cancelled():
        speak("Running background tasks")
        time.sleep(3600)

def smart_tasks():
    from control import is_cancelled

    while not is_cancelled():
        hour = time.localtime().tm_hour

        if hour == 9:
            speak("Good morning. Checking your day.")

        time.sleep(300)

        
        
# -----------------------
# 📬 SMART EMAIL MONITOR (ADDED)
# -----------------------
from actions import check_emails_smart

def email_monitor_smart():
    """Legacy hook retained without automatic inbox access."""
    print("[EMAIL] Automatic email monitoring is disabled; ask to read emails.")