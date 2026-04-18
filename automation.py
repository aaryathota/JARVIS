"""
Automation Module - Restored
Handles automatic tasks like email checking
"""

import threading
import time

def auto_email_checker():
    """Automatically check email in the background"""
    try:
        while True:
            # Check email periodically (every 5 minutes)
            time.sleep(300)
            
            print("[EMAIL] Background email check...")
            # Implement email checking if needed
            
    except Exception as e:
        print(f"[AUTOMATION ERROR] {e}")

def auto_backup():
    """Automatically backup important files"""
    try:
        import shutil
        import os
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = f"backups/backup_{timestamp}"
        
        files_to_backup = ['credentials.json', 'config.py']
        
        if not os.path.exists('backups'):
            os.makedirs('backups')
        
        for file in files_to_backup:
            if os.path.exists(file):
                shutil.copy(file, backup_dir)
                print(f"[BACKUP] Backed up {file}")
    
    except Exception as e:
        print(f"[BACKUP ERROR] {e}")

def schedule_task(task_name, interval_seconds, function):
    """Schedule a task to run at intervals"""
    def scheduler():
        while True:
            time.sleep(interval_seconds)
            try:
                function()
                print(f"[TASK] {task_name} executed")
            except Exception as e:
                print(f"[TASK ERROR] {task_name}: {e}")
    
    thread = threading.Thread(target=scheduler, daemon=True)
    thread.start()
