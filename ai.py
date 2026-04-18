"""
AI Module - Restored
Handles basic AI operations and decision making with context awareness
"""

import json
from groq import Groq
from conversation_memory import get_memory, add_to_memory, get_context_for_query

def ask_ai_text(prompt, max_tokens=500, use_context=True):
    """Query Groq API for text responses with optional context"""
    try:
        # Load credentials
        with open('credentials.json', 'r') as f:
            creds = json.load(f)
            groq_key = creds.get('groq_api_key', '')
        
        if not groq_key or groq_key.strip() == '':
            print("[GROQ] ERROR: No API key found in credentials.json")
            return None
        
        # Add conversation context if enabled
        enhanced_prompt = prompt
        if use_context:
            context = get_context_for_query(prompt)
            if context:
                enhanced_prompt = f"{context}\n\nUser query: {prompt}"
        
        # Call Groq API
        client = Groq(api_key=groq_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": enhanced_prompt}],
            max_tokens=max_tokens
        )
        
        result = response.choices[0].message.content
        print(f"[GROQ] Success: {len(result)} chars")
        
        # Store in conversation memory
        add_to_memory(prompt, result)
        
        return result
        
    except FileNotFoundError:
        print("[GROQ] ERROR: credentials.json not found")
    except json.JSONDecodeError:
        print("[GROQ] ERROR: credentials.json is not valid JSON")
    except KeyError as e:
        print(f"[GROQ] ERROR: {e} not found in credentials")
    except Exception as e:
        print(f"[GROQ] ERROR: {type(e).__name__}: {str(e)[:100]}")
    
    return None

def decide_action(query):
    """
    Provide advice/decision based on query using AI.
    Instead of returning action type, actually generate decision.
    """
    prompt = f"""You are a helpful decision-making assistant. 
The user is asking for advice or a decision. Provide a balanced, thoughtful response.

User's question: {query}

Provide a helpful response that considers pros and cons."""
    
    result = ask_ai_text(prompt, use_context=True)
    return result if result else "I need more information to help you decide."

def parse_intent(command):
    """Parse user command to determine intent"""
    keywords = {
        'weather': ['weather', 'temperature', 'forecast'],
        'time': ['time', 'what time', 'current time'],
        'reminder': ['remind', 'remember', 'set reminder'],
        'website': ['create website', 'build website', 'website'],
        'youtube': ['youtube', 'shorts', 'video'],
        'instagram': ['instagram', 'insta', 'reels'],
    }
    
    cmd_lower = command.lower()
    for intent, words in keywords.items():
        if any(word in cmd_lower for word in words):
            return intent
    
    return 'general'

def is_casual_query(command):
    """Check if command is casual conversation or question"""
    casual_words = ['hello', 'hi', 'hey', 'how are you', 'what is', 'tell me', 'why', 'how', 'what', 'should i', 'can i', 'could i']
    return any(word in command.lower() for word in casual_words)

def handle_casual_query(command):
    """Handle casual conversation and questions with AI"""
    # Quick responses for basic greetings only
    quick_responses = {
        'hello': "Hello! How can I help you today?",
        'hi': "Hi there! What can I do for you?",
        'hey': "Hey! What do you need?",
        'how are you': "I'm doing great! Ready to help you with anything.",
    }
    
    # Check for exact greeting match
    command_lower = command.lower().strip()
    for key, response in quick_responses.items():
        if command_lower == key or command_lower.startswith(key + ' '):
            return response
    
    # For all other queries, use AI to answer
    print("[AI] Using Groq AI for response")
    return ask_ai_text(command, use_context=True)
