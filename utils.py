import pyttsx3
import threading
import time
import sys

# Global engine lock - ensures only one speech at a time
engine_lock = threading.Lock()

def speak(text):
    """SYNCHRONOUS speech output - waits for audio to complete"""
    if not text or text.strip() == "":
        return
    
    # Truncate very long responses
    if len(text) > 1000:
        text = text[:1000] + "..."
    
    print(f"\n[SPEAK OUT LOUD] {text[:100]}...")
    sys.stdout.flush()
    
    def speak_sync():
        """Run speech synchronously in a worker thread"""
        try:
            with engine_lock:  # Ensure only one speech at a time
                try:
                    # Create fresh engine for each speech (more reliable)
                    eng = pyttsx3.init()
                    eng.setProperty('rate', 220)  # Normal speaking speed
                    eng.setProperty('volume', 1.0)
                    
                    # Set voice
                    try:
                        voices = eng.getProperty('voices')
                        if voices:
                            eng.setProperty('voice', voices[0].id)
                    except:
                        pass
                    
                    print("[SPEAK] Playing audio NOW...")
                    sys.stdout.flush()
                    
                    eng.say(text)
                    eng.runAndWait()  # BLOCKS until done
                    
                    print("[SPEAK] [DONE] Audio complete")
                    sys.stdout.flush()
                    
                except Exception as e:
                    print(f"[SPEAK ERROR] {type(e).__name__}: {e}")
                    sys.stdout.flush()
        except Exception as e:
            print(f"[SPEAK LOCK ERROR] {e}")
            sys.stdout.flush()
    
    # Run in thread so it doesn't block main
    thread = threading.Thread(target=speak_sync, daemon=False)
    thread.start()
    thread.join(timeout=15)  # CRITICAL: Wait for thread to complete (max 15 seconds)