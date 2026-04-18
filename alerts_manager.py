"""
Custom Alerts System - Set and manage custom alerts
"""

import json
import os
import threading
import time
from datetime import datetime, timedelta

ALERTS_FILE = "custom_alerts.json"

class AlertsManager:
    def __init__(self):
        self.alerts = self.load_alerts()
        self.active_alerts = []
        self.speak_function = None
    
    def load_alerts(self):
        """Load alerts from file"""
        if os.path.exists(ALERTS_FILE):
            try:
                with open(ALERTS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_alerts(self):
        """Save alerts to file"""
        try:
            with open(ALERTS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.alerts, f, indent=2)
            return True
        except Exception as e:
            print(f"[ALERTS ERROR] Failed to save: {e}")
            return False
    
    def create_alert(self, title, alert_type="reminder", trigger_in_minutes=10, details=""):
        """
        Create a new alert
        alert_type: 'reminder', 'notification', 'warning', 'urgent'
        trigger_in_minutes: when to trigger the alert
        """
        trigger_time = (datetime.now() + timedelta(minutes=trigger_in_minutes)).strftime('%Y-%m-%d %H:%M:%S')
        
        alert = {
            'id': len(self.alerts) + 1,
            'title': title,
            'type': alert_type,
            'details': details,
            'trigger_time': trigger_time,
            'created_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'active',
            'triggered': False
        }
        
        self.alerts.append(alert)
        self.save_alerts()
        
        return alert
    
    def set_speak_function(self, func):
        """Set the speak function for alerts"""
        self.speak_function = func
    
    def delete_alert(self, alert_id):
        """Delete an alert"""
        self.alerts = [a for a in self.alerts if a['id'] != alert_id]
        self.save_alerts()
        return True
    
    def snooze_alert(self, alert_id, minutes=10):
        """Snooze an alert"""
        for alert in self.alerts:
            if alert['id'] == alert_id:
                new_trigger = (datetime.now() + timedelta(minutes=minutes)).strftime('%Y-%m-%d %H:%M:%S')
                alert['trigger_time'] = new_trigger
                alert['status'] = 'snoozed'
                self.save_alerts()
                return True
        return False
    
    def list_alerts(self):
        """List all active alerts"""
        if not self.alerts:
            return "No alerts set"
        
        output = "\n🔔 ACTIVE ALERTS\n"
        output += "="*60 + "\n"
        
        for alert in self.alerts:
            if alert['status'] != 'dismissed':
                status_icon = {
                    'reminder': '⏰',
                    'notification': '📬',
                    'warning': '⚠️',
                    'urgent': '🚨'
                }.get(alert['type'], '📌')
                
                output += f"{status_icon} {alert['title']} (ID: {alert['id']})\n"
                output += f"   Type: {alert['type']}\n"
                output += f"   Trigger: {alert['trigger_time']}\n"
                if alert.get('details'):
                    output += f"   Details: {alert['details']}\n"
                output += "\n"
        
        output += "="*60 + "\n"
        return output
    
    def check_alerts(self):
        """Check if any alerts need to be triggered (run in background)"""
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for alert in self.alerts:
            if alert['status'] in ['active', 'snoozed'] and not alert.get('triggered', False):
                if alert['trigger_time'] <= now:
                    self._trigger_alert(alert)
    
    def _trigger_alert(self, alert):
        """Trigger an alert"""
        alert['triggered'] = True
        alert['status'] = 'triggered'
        
        # Display alert
        alert_msg = f"\n🔔 ALERT TRIGGERED!\n"
        alert_msg += f"{'='*60}\n"
        alert_msg += f"🔹 {alert['title'].upper()}\n"
        alert_msg += f"Type: {alert['type']}\n"
        
        if alert.get('details'):
            alert_msg += f"Details: {alert['details']}\n"
        
        alert_msg += f"{'='*60}\n"
        
        print(alert_msg)
        
        # Speak alert if speak function available
        if self.speak_function:
            speak_msg = f"Alert! {alert['title']}"
            if alert['type'] == 'urgent':
                speak_msg = f"URGENT! {alert['title']}"
            self.speak_function(speak_msg)
        
        self.save_alerts()
    
    def get_alert_info(self, alert_id):
        """Get detailed info about an alert"""
        for alert in self.alerts:
            if alert['id'] == alert_id:
                output = f"\n📌 ALERT DETAILS (ID: {alert_id})\n"
                output += "="*60 + "\n"
                output += f"Title: {alert['title']}\n"
                output += f"Type: {alert['type']}\n"
                output += f"Status: {alert['status']}\n"
                output += f"Created: {alert['created_time']}\n"
                output += f"Trigger: {alert['trigger_time']}\n"
                if alert.get('details'):
                    output += f"Details: {alert['details']}\n"
                output += "="*60 + "\n"
                return output
        
        return "Alert not found"
    
    def dismiss_alert(self, alert_id):
        """Dismiss/clear an alert"""
        for alert in self.alerts:
            if alert['id'] == alert_id:
                alert['status'] = 'dismissed'
                self.save_alerts()
                return True
        return False
    
    def get_statistics(self):
        """Get alert statistics"""
        if not self.alerts:
            return "No alerts created yet"
        
        stats = {
            'total': len(self.alerts),
            'active': len([a for a in self.alerts if a['status'] == 'active']),
            'snoozed': len([a for a in self.alerts if a['status'] == 'snoozed']),
            'triggered': len([a for a in self.alerts if a['status'] == 'triggered']),
            'dismissed': len([a for a in self.alerts if a['status'] == 'dismissed'])
        }
        
        output = "\n📊 ALERTS STATISTICS\n"
        output += "="*60 + "\n"
        output += f"Total alerts: {stats['total']}\n"
        output += f"  • Active: {stats['active']}\n"
        output += f"  • Snoozed: {stats['snoozed']}\n"
        output += f"  • Triggered: {stats['triggered']}\n"
        output += f"  • Dismissed: {stats['dismissed']}\n"
        output += "="*60 + "\n"
        
        return output


# Global instance
alerts_manager = AlertsManager()

def start_alert_monitor():
    """Start monitoring alerts in background"""
    def monitor():
        while True:
            try:
                alerts_manager.check_alerts()
                time.sleep(10)  # Check every 10 seconds
            except Exception as e:
                print(f"[ALERTS MONITOR ERROR] {e}")
                time.sleep(30)
    
    thread = threading.Thread(target=monitor, daemon=True)
    thread.start()
    print("[ALERTS] Background monitor started")
