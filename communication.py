"""
Communication Module - Restored
Handles communications like SMS, emails, messages
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json

class Communication:
    def __init__(self):
        self.name = "Communication Module"
        self.email_config = self.load_email_config()
    
    def load_email_config(self):
        """Load email configuration"""
        try:
            from config import EMAIL_SENDER, EMAIL_PASSWORD
            return {
                'sender': EMAIL_SENDER,
                'password': EMAIL_PASSWORD
            }
        except Exception as e:
            print(f"[COMMUNICATION] Email config error: {e}")
            return None
    
    def send_email(self, recipient, subject, body):
        """Send an email"""
        try:
            if not self.email_config:
                print("[COMMUNICATION] Email not configured")
                return False
            
            msg = MIMEMultipart()
            msg['From'] = self.email_config['sender']
            msg['To'] = recipient
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.email_config['sender'], self.email_config['password'])
                server.send_message(msg)
            
            print(f"[COMMUNICATION] Email sent to {recipient}")
            return True
        
        except Exception as e:
            print(f"[COMMUNICATION ERROR] {e}")
            return False
    
    def send_sms(self, phone, message):
        """Send an SMS (requires SMS service)"""
        print(f"[COMMUNICATION] SMS to {phone}: {message}")
        return True
    
    def send_message(self, contact, message, method='email'):
        """Send a message via specified method"""
        if method == 'email':
            return self.send_email(contact, "Message", message)
        elif method == 'sms':
            return self.send_sms(contact, message)
        else:
            print("[COMMUNICATION] Unknown method")
            return False

# Global communication instance
communication = Communication()
