"""
AI Module - Restored
Handles basic AI operations and decision making with context awareness
"""

import json
import os
from groq import Groq
from dotenv import load_dotenv
from conversation_memory import get_memory, add_to_memory, get_context_for_query

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

DETAIL_PHRASES = (
    "in detail", "deep dive", "be thorough", "long answer", "step by step",
    "explain fully", "comprehensive",
)


def _wants_detail(prompt):
    lowered = prompt.lower()
    return any(phrase in lowered for phrase in DETAIL_PHRASES)

def ask_ai_text(prompt, max_tokens=None, use_context=True):
    """Query Groq API for text responses with optional context"""
    try:
        # Prefer the ignored .env file; keep credentials.json as a legacy fallback.
        groq_key = os.getenv("GROQ_API_KEY", "").strip()
        if not groq_key:
            try:
                with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credentials.json'), 'r', encoding='utf-8-sig') as f:
                    groq_key = json.load(f).get('groq_api_key', '').strip()
            except FileNotFoundError:
                pass
        
        if not groq_key or groq_key.strip() == '':
            print("[GROQ] ERROR: No GROQ_API_KEY found in .env or credentials.json")
            return None
        
        # Add conversation context if enabled
        enhanced_prompt = prompt
        if use_context:
            context = get_context_for_query(prompt)
            if context:
                enhanced_prompt = f"{context}\n\nUser query: {prompt}"

        detailed = _wants_detail(prompt)
        answer_style = (
            "Give a thorough, structured answer with useful detail."
            if detailed else
            "Answer concisely by default: 1-4 sentences or a short bullet list. "
            "Use only the most relevant and recent information. Do not add background "
            "the user did not request."
        )
        enhanced_prompt = (
            "You are JARVIS, a practical assistant. "
            f"{answer_style} If the user asks for current information, be clear about "
            "what is known and do not invent facts.\n\n" + enhanced_prompt
        )
        token_limit = max_tokens or (900 if detailed else 260)
        
        # Call Groq API
        client = Groq(api_key=groq_key)
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            extra_body={"reasoning_effort": "low"},
            messages=[{"role": "user", "content": enhanced_prompt}],
            max_tokens=token_limit
        )
        
        result = response.choices[0].message.content or ""
        print(f"[GROQ] Success: {len(result)} chars")
        
        # Store in conversation memory
        add_to_memory(prompt, result)
        
        return result
        
    except json.JSONDecodeError:
        print("[GROQ] ERROR: legacy credentials.json is not valid JSON")
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