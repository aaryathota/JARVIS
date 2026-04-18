"""
JARVIS Dictation & Smart Message Handling
Automatic notepad dictation for large messages
"""

import os
import subprocess
import time
import threading

def open_notepad_for_dictation(text, title="JARVIS Message"):
    """
    Open notepad with text content for large messages
    Runs in background so voice assistant keeps responding
    """
    try:
        # Create a temporary text file
        temp_file = f"jarvis_dictation_{int(time.time())}.txt"
        
        # Write content to file
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(f"[{title}]\n")
            f.write("="*60 + "\n\n")
            f.write(text)
            f.write("\n\n" + "="*60)
            f.write(f"\n[Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}]")
        
        # Open in Notepad in separate thread (non-blocking)
        def open_file():
            try:
                subprocess.Popen(['notepad.exe', temp_file])
            except:
                pass
        
        thread = threading.Thread(target=open_file, daemon=True)
        thread.start()
        
        return True
    except Exception as e:
        print(f"[NOTEPAD ERROR] {e}")
        return False

def should_open_notepad(text):
    """
    Determine if response is large enough to warrant notepad
    Threshold: more than 75 characters (frequently)
    """
    if not text:
        return False
    
    # Check length - lowered to 75 chars for more frequent notepad opening
    if len(text) > 75:
        return True
    
    return False

def detect_sentence_intent(text):
    """
    Smart detection of user intent from natural text
    Returns detected features and confidence
    """
    text_lower = text.lower().strip()
    detections = []
    
    # Productivity
    productivity_words = {
        'todo': ['add', 'task', 'todo', 'list', 'complete', 'delete'],
        'calendar': ['schedule', 'meeting', 'event', 'calendar', 'remind', 'remind me'],
        'expense': ['spent', 'cost', 'expense', 'money', 'budget', 'spending', 'price']
    }
    
    # Entertainment
    entertainment_words = {
        'joke': ['joke', 'funny', 'laugh', 'laughter'],
        'trivia': ['trivia', 'quiz', 'question', 'facts'],
        'riddle': ['riddle', 'puzzle', 'brain teaser'],
        'game': ['game', 'play', 'let\'s play', 'gaming'],
        'meditation': ['meditation', 'meditate', 'relax', 'breathing', 'calm'],
    }
    
    # Developer
    developer_words = {
        'code': ['code', 'python', 'javascript', 'programming', 'explain code'],
        'git': ['git', 'commit', 'push', 'pull', 'branch'],
        'api': ['api', 'endpoint', 'test', 'request'],
        'error': ['error', 'bug', 'debug', 'syntax', 'exception']
    }
    
    # Media
    media_words = {
        'download': ['download', 'save video', 'download video', 'extract audio'],
        'convert': ['convert', 'format', 'transform'],
        'qr': ['qr', 'qr code', 'barcode']
    }
    
    # AI/ML  
    aiml_words = {
        'sentiment': ['sentiment', 'analyze tone', 'emotional', 'positive', 'negative'],
        'spam': ['spam', 'junk', 'suspicious', 'scam'],
        'translate': ['translate', 'translate to', 'in', 'language'],
        'image': ['image', 'photo', 'picture', 'recognize', 'detect']
    }
    
    # Communication
    communication_words = {
        'sms': ['sms', 'text message', 'send text'],
        'whatsapp': ['whatsapp', 'message'],
        'call': ['call', 'phone'],
        'email': ['email', 'mail', 'send email'],
        'social': ['post', 'twitter', 'facebook', 'social']
    }
    
    # System
    system_words = {
        'screenshot': ['screenshot', 'capture screen', 'screen shot'],
        'info': ['system info', 'computer info', 'my pc', 'system information'],
        'backup': ['backup', 'backup files'],
        'disk': ['disk space', 'storage', 'memory']
    }
    
    # Website Builder
    website_words = {
        'website': ['build website', 'create website', 'make website'],
        'app': ['create app', 'build app', 'web app'],
        'calculator': ['calculator']
    }
    
    all_categories = {
        'productivity': productivity_words,
        'entertainment': entertainment_words,
        'developer': developer_words,
        'media': media_words,
        'aiml': aiml_words,
        'communication': communication_words,
        'system': system_words,
        'website': website_words
    }
    
    for category, words_dict in all_categories.items():
        for feature, keywords in words_dict.items():
            for keyword in keywords:
                if keyword in text_lower:
                    confidence = len(keyword) / len(text_lower)  # Longer match = higher confidence
                    detections.append({
                        'category': category,
                        'feature': feature,
                        'keyword': keyword,
                        'confidence': min(1.0, confidence)
                    })
    
    # Sort by confidence
    detections.sort(key=lambda x: x['confidence'], reverse=True)
    
    return detections

def extract_context_from_sentence(text, feature_type):
    """
    Extract relevant context/parameters from natural sentence
    Different extraction for each feature type
    """
    text_lower = text.lower()
    context = {}
    
    if feature_type == 'todo':
        # Extract task and priority
        task = text.lower().replace('add', '').replace('task', '').replace('todo', '').strip()
        context['task'] = task
        context['priority'] = 'high' if 'urgent' in text_lower or 'important' in text_lower else 'normal'
    
    elif feature_type == 'expense':
        # Extract amount and category
        import re
        amounts = re.findall(r'\d+\.?\d*', text)
        context['amount'] = amounts[0] if amounts else '0'
        
        categories = ['food', 'transport', 'entertainment', 'shopping', 'utility', 'health']
        for cat in categories:
            if cat in text_lower:
                context['category'] = cat
                break
        
        context['description'] = text.lower().replace('spent', '').replace('spend', '').strip()
    
    elif feature_type == 'translate':
        # Extract text and language
        import re
        parts = text.lower().split(' to ')
        context['text'] = parts[0].replace('translate', '').strip() if len(parts) > 0 else ''
        context['language'] = parts[1].strip() if len(parts) > 1 else 'spanish'
    
    elif feature_type == 'sentiment':
        # Extract text to analyze
        context['text'] = text.lower().replace('analyze', '').replace('sentiment', '').replace('of', '').strip()
    
    elif feature_type == 'spam':
        # Extract text to check
        context['text'] = text.lower().replace('is', '').replace('this', '').replace('spam', '').strip()
    
    elif feature_type == 'remind':
        # Extract time and task
        import re
        time_match = re.search(r'(\d+)\s*(minutes?|hours?|seconds?)', text_lower)
        if time_match:
            context['time_value'] = time_match.group(1)
            context['time_unit'] = time_match.group(2)
        
        context['task'] = text.lower().replace('remind', '').replace('in', '').replace('to', '').strip()
    
    elif feature_type == 'schedule':
        # Extract event and time
        context['event'] = text.lower().replace('schedule', '').replace('meeting', '').replace('event', '').strip()
    
    return context

def is_conversational_response(message):
    """
    Detect if response is conversational (should NOT open notepad)
    vs informational (might need notepad)
    """
    conversational_indicators = [
        'i\'m', 'i am', 'you\'re', 'that\'s', 'here\'s',
        'let me', 'sure', 'okay', 'got it', 'done',
        'ok', 'yes', 'no', 'thanks', 'hello'
    ]
    
    message_lower = message.lower()[:50]  # Check first 50 chars
    
    for indicator in conversational_indicators:
        if indicator in message_lower:
            return True
    
    return False
