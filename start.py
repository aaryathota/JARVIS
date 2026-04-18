#!/usr/bin/env python3
"""
JARVIS - One-Click Starter
Double-click to run both server and voice assistant at once!
"""

import subprocess
import sys
import os
import time
import webbrowser
import threading

def main():
    print("=" * 70)
    print("🚀 JARVIS - Starting Complete System")
    print("=" * 70)
    print()
    print("[STARTUP] Starting Flask Web Server...")
    print("[STARTUP] This will automatically open the UI in your browser")
    print("[STARTUP] Then the voice assistant will start listening")
    print()
    
    # Get the project directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    
    try:
        print("[STARTUP - OPTION 1] Double Terminal Method (Recommended)")
        print()
        print("We'll open two terminal windows:")
        print("  1. Flask Server (UI backend)")
        print("  2. Voice Assistant (listening)")
        print()
        print("Starting servers...")
        print()
        
        # Start Flask server in a new terminal
        if sys.platform == 'win32':
            print("[TERMINAL 1] Opening Flask Server...")
            subprocess.Popen(
                f'start cmd /k "cd {project_dir} && python server.py"',
                shell=True
            )
            time.sleep(3)
            
            print("[TERMINAL 2] Opening Voice Assistant...")
            subprocess.Popen(
                f'start cmd /k "cd {project_dir} && python main.py"',
                shell=True
            )
            
            print()
            print("=" * 70)
            print("✅ System Started Successfully!")
            print("=" * 70)
            print()
            print("[RUNNING] Browser should open to: http://127.0.0.1:8000")
            print("[RUNNING] Voice Assistant is listening in the other terminal")
            print()
            print("Two windows opened:")
            print("  Window 1: Flask Server (backend)")
            print("  Window 2: Voice Assistant (voice/commands)")
            print()
            print("Close either window to stop that service")
            print("Close both to stop everything")
            print()
            print("This window will close in 10 seconds...")
            time.sleep(10)
        else:
            # For Linux/Mac
            print("[STARTUP] Non-Windows system detected")
            print("Running in current terminal...")
            
            os.system(f'cd {project_dir} && python server.py &')
            time.sleep(2)
            os.system(f'cd {project_dir} && python main.py')
    
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Stopping all services...")
        sys.exit(0)
    
    except Exception as e:
        print(f"[ERROR] {e}")
        print()
        print("Make sure you're in the correct directory and have installed dependencies:")
        print("  pip install -r requirements.txt")
        print()
        print("Manual start (if this doesn't work):")
        print("  Terminal 1: python server.py")
        print("  Terminal 2: python main.py")
        sys.exit(1)

if __name__ == '__main__':
    main()
