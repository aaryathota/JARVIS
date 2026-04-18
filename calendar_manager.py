"""
JARVIS Calendar Manager - Voice-controlled scheduling with actual reminders
"""

import json
import os
import threading
import time
import subprocess
from datetime import datetime, timedelta

CALENDAR_FILE = 'calendar_events.json'

class CalendarManager:
    def __init__(self):
        self.events = self.load_events()
        self.monitor_thread = None
        self.monitoring = False
        self.start_reminder_monitor()
    
    def load_events(self):
        if os.path.exists(CALENDAR_FILE):
            try:
                with open(CALENDAR_FILE, 'r') as f:
                    return json.load(f)
            except:
                return {'events': []}
        return {'events': []}
    
    def save_events(self):
        with open(CALENDAR_FILE, 'w') as f:
            json.dump(self.events, f, indent=2)
    
    def add_event(self, title, time_str, description=''):
        """Add calendar event"""
        event = {
            'title': title,
            'time': time_str,
            'description': description,
            'created': datetime.now().isoformat(),
            'reminder_sent': False
        }
        self.events['events'].append(event)
        self.save_events()
        return f"📅 Event scheduled: {title} at {time_str}"
    
    def list_events(self, days=7):
        """Show upcoming events"""
        if not self.events['events']:
            return "No events scheduled"
        
        event_list = f"Your calendar (Next {days} days):\n"
        for i, event in enumerate(self.events['events'], 1):
            event_list += f"{i}. {event['title']} - {event['time']}\n"
            if event['description']:
                event_list += f"   📝 {event['description']}\n"
        return event_list
    
    def delete_event(self, event_num):
        """Delete event"""
        try:
            event = self.events['events'].pop(int(event_num) - 1)
            self.save_events()
            return f"🗑️ Deleted: {event['title']}"
        except:
            return "Event not found"
    
    def remind_me_in(self, task, minutes):
        """Set reminder for later"""
        remind_time = (datetime.now() + timedelta(minutes=int(minutes))).isoformat()
        return self.add_event(f"Reminder: {task}", remind_time)
    
    def start_reminder_monitor(self):
        """Start background thread to check and trigger reminders"""
        if self.monitoring:
            return
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_reminders, daemon=True)
        self.monitor_thread.start()
    
    def stop_reminder_monitor(self):
        """Stop the reminder monitor"""
        self.monitoring = False
    
    def _monitor_reminders(self):
        """Background thread that checks for due reminders"""
        while self.monitoring:
            try:
                now = datetime.now()
                
                for event in self.events.get('events', []):
                    if event.get('reminder_sent'):
                        continue
                    
                    try:
                        event_time = datetime.fromisoformat(event['time'])
                        
                        # Check if reminder time has passed
                        if now >= event_time and not event.get('reminder_sent'):
                            self._trigger_reminder(event)
                            event['reminder_sent'] = True
                            self.save_events()
                    except:
                        pass
                
                time.sleep(10)  # Check every 10 seconds
            except Exception as e:
                print(f"[REMINDER ERROR] {e}")
                time.sleep(10)
    
    def _trigger_reminder(self, event):
        """Actually trigger the reminder with Windows notification and sound"""
        title = event.get('title', 'Reminder')
        description = event.get('description', '')
        
        print(f"\n🔔 REMINDER ALERT: {title}")
        if description:
            print(f"   Details: {description}")
        print()
        
        # Windows notification
        try:
            from win10toast import ToastNotifier
            notifier = ToastNotifier()
            notifier.show_toast(
                title="JARVIS REMINDER",
                msg=f"{title}\n{description}",
                duration=10,
                threaded=True
            )
        except:
            pass
        
        # Play sound
        try:
            import winsound
            winsound.Beep(1000, 500)  # 1000 Hz for 500ms
            time.sleep(0.2)
            winsound.Beep(1000, 500)
        except:
            pass
        
        # Also speak the reminder
        try:
            from utils import speak
            speak(f"Reminder: {title}")
        except:
            pass

calendar_manager = CalendarManager()
