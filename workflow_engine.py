import time
from actions import check_emails, create_reminder
from utils import speak

memory = {"emails": []}

def email_monitor():
    while True:
        emails = check_emails()

        new = [e for e in emails if e not in memory["emails"]]

        for e in new:
            speak(f"New email: {e}")

            if "meeting" in e.lower():
                create_reminder(f"Follow up {e}")

        memory["emails"] = emails
        time.sleep(120)

def daily_routine():
    while True:
        speak("Running background tasks")
        time.sleep(3600)

def smart_tasks():
    while True:
        hour = time.localtime().tm_hour

        if hour == 9:
            speak("Good morning. Checking your day.")

        time.sleep(300)

        
        
# -----------------------
# 📬 SMART EMAIL MONITOR (ADDED)
# -----------------------
from actions import check_emails_smart

def email_monitor_smart():
    while True:
        check_emails_smart(speak)
        time.sleep(120)