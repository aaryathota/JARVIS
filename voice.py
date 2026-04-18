import sounddevice as sd
import scipy.io.wavfile as wavfile
import speech_recognition as sr
import threading
import os
import signal

# Global flags
LISTENING_ACTIVE = True
mic = None
recognizer = None
STOP_RECORDING = False

def stop_listening():
    """NUCLEAR OPTION - Stop ALL audio recording"""
    global LISTENING_ACTIVE, mic, recognizer, STOP_RECORDING
    LISTENING_ACTIVE = False
    STOP_RECORDING = True
    
    print("[VOICE] Closing audio devices...")
    
    # 1. Shut down sounddevice recording
    try:
        sd.stop()
    except:
        pass
    
    try:
        sd.terminate()
    except:
        pass
    
    try:
        sd.close()
    except:
        pass
    
    # 2. Close microphone device
    try:
        if mic is not None:
            try:
                mic.close()
            except:
                pass
            mic = None
    except:
        pass
    
    # 3. Clear recognizer
    try:
        recognizer = None
    except:
        pass
    
    print("[VOICE] Audio devices closed")

def listen():
    global LISTENING_ACTIVE, mic, recognizer, STOP_RECORDING
    
    # RESET the stop flag at start of listening - THIS IS CRITICAL FOR CONTINUOUS LISTENING
    STOP_RECORDING = False
    
    # Don't listen if stopped
    if not LISTENING_ACTIVE:
        return ""
    
    # Fresh recognizer each time
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 3000
    recognizer.pause_threshold = 1.0

    try:
        # Open microphone
        if not LISTENING_ACTIVE:
            return ""
            
        mic = sr.Microphone()
        
        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.3)
            audio_data = recognizer.listen(source, timeout=5, phrase_time_limit=8)

        # Process audio
        text = recognizer.recognize_google(audio_data).lower()
        print(f"[You said:] {text}")
        return text

    except sr.WaitTimeoutError:
        return ""

    except sr.UnknownValueError:
        return ""

    except sr.RequestError as e:
        print(f"[API ERROR] {str(e)[:40]}")
        return ""
    
    except KeyboardInterrupt:
        LISTENING_ACTIVE = False
        STOP_RECORDING = True
        return ""

    except Exception as e:
        err_str = str(e)[:50]
        if "already" in err_str.lower() or "device" in err_str.lower():
            # Device error - will retry next iteration
            pass
        else:
            print(f"[ERROR] {err_str}")
        return ""
    
    finally:
        # Simple cleanup: Close microphone device gracefully
        try:
            if mic is not None:
                try:
                    mic.close()
                except:
                    pass
        except:
            pass
