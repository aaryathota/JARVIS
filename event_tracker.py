"""
Event Summary Module - Track and summarize events while away
"""

import json
import os
from datetime import datetime, timedelta

EVENTS_LOG_FILE = "events_log.json"

class EventTracker:
    def __init__(self):
        self.events = self.load_events()
        self.last_summary_time = None
    
    def load_events(self):
        """Load event log from file"""
        if os.path.exists(EVENTS_LOG_FILE):
            try:
                with open(EVENTS_LOG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_events(self):
        """Save events to file"""
        try:
            with open(EVENTS_LOG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.events, f, indent=2)
            return True
        except Exception as e:
            print(f"[EVENTS ERROR] Failed to save: {e}")
            return False
    
    def add_event(self, event_type, title, details=""):
        """Add an event to the log"""
        event = {
            'type': event_type,  # email, reminder, alert, task, system, etc.
            'title': title,
            'details': details,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'read': False
        }
        
        self.events.append(event)
        self.save_events()
        return event
    
    def get_events_since(self, minutes=30):
        """Get events from the last N minutes"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        cutoff_str = cutoff_time.strftime('%Y-%m-%d %H:%M:%S')
        
        recent_events = []
        for event in self.events:
            event_time = event.get('timestamp', '')
            if event_time >= cutoff_str:
                recent_events.append(event)
        
        return recent_events
    
    def get_unread_events(self):
        """Get all unread events"""
        return [e for e in self.events if not e.get('read', False)]
    
    def mark_as_read(self, index=None):
        """Mark events as read"""
        if index is not None:
            if 0 <= index < len(self.events):
                self.events[index]['read'] = True
        else:
            # Mark all as read
            for event in self.events:
                event['read'] = True
        
        self.save_events()
    
    def summarize_events(self, minutes=None, speak_function=None):
        """Summarize recent events"""
        if minutes is None:
            # Get events since last summary or last hour
            recent_events = self.get_events_since(60)
        else:
            recent_events = self.get_events_since(minutes)
        
        if not recent_events:
            msg = "You don't have any recent events"
            if speak_function:
                speak_function(msg)
            return msg
        
        # Group events by type
        grouped = {}
        for event in recent_events:
            event_type = event.get('type', 'other')
            if event_type not in grouped:
                grouped[event_type] = []
            grouped[event_type].append(event)
        
        # Build summary
        summary = f"\n📊 SUMMARY - Events from the last {minutes or 60} minutes\n"
        summary += "="*60 + "\n"
        
        for event_type, events in grouped.items():
            summary += f"\n📌 {event_type.upper()} ({len(events)})\n"
            for event in events:
                summary += f"  • {event['title']}\n"
                if event.get('details'):
                    summary += f"    {event['details']}\n"
        
        summary += "\n" + "="*60 + "\n"
        
        # Speak summary
        if speak_function:
            spoken_summary = f"Here's what happened: "
            
            for event_type, events in grouped.items():
                spoken_summary += f"{len(events)} {event_type}. "
                for event in events[:2]:  # Only speak first 2 of each type
                    spoken_summary += f"{event['title']}. "
            
            speak_function(spoken_summary)
        
        print(summary)
        return summary
    
    def clear_old_events(self, days=7):
        """Clear events older than N days"""
        cutoff_time = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff_time.strftime('%Y-%m-%d %H:%M:%S')
        
        original_count = len(self.events)
        self.events = [e for e in self.events if e.get('timestamp', '') >= cutoff_str]
        
        deleted = original_count - len(self.events)
        self.save_events()
        
        return deleted
    
    def get_event_stats(self):
        """Get event statistics"""
        if not self.events:
            return "No events recorded yet"
        
        grouped = {}
        for event in self.events:
            event_type = event.get('type', 'other')
            grouped[event_type] = grouped.get(event_type, 0) + 1
        
        stats = "\n📈 EVENT STATISTICS\n"
        stats += "="*60 + "\n"
        stats += f"Total events: {len(self.events)}\n"
        stats += f"Unread events: {len(self.get_unread_events())}\n\n"
        
        stats += "Breakdown by type:\n"
        for event_type, count in sorted(grouped.items(), key=lambda x: x[1], reverse=True):
            stats += f"  • {event_type}: {count}\n"
        
        stats += "="*60 + "\n"
        
        return stats


# Global instance
event_tracker = EventTracker()

# Helper functions for integration with main.py
def log_email_event(sender, subject):
    """Log an email event"""
    event_tracker.add_event(
        'email',
        f"Email from {sender}",
        f"Subject: {subject}"
    )

def log_reminder_event(title, details=""):
    """Log a reminder event"""
    event_tracker.add_event('reminder', title, details)

def log_system_event(title, details=""):
    """Log a system event"""
    event_tracker.add_event('system', title, details)

def log_task_event(title, details=""):
    """Log a task event"""
    event_tracker.add_event('task', title, details)

def log_alert_event(title, details=""):
    """Log an alert event"""
    event_tracker.add_event('alert', title, details)
