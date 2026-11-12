"""
Automation Module - Restored
Handles automatic tasks like email checking
"""

import threading
import time

def auto_email_checker():
    """Compatibility no-op: email is never checked automatically."""
    print("[EMAIL] Automatic email checking is disabled; use an explicit command.")

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
        from control import is_cancelled

        while not is_cancelled():
            time.sleep(interval_seconds)
            if is_cancelled():
                break
            try:
                function()
                print(f"[TASK] {task_name} executed")
            except Exception as e:
                print(f"[TASK ERROR] {task_name}: {e}")
    
    thread = threading.Thread(target=scheduler, daemon=True)
    thread.start()
