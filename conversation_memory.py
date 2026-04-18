"""
Conversation Memory Module
Tracks conversation context and topics for intelligent context-aware responses
"""

import json
import os
from datetime import datetime

CONV_FILE = "conversation_history.json"
MAX_HISTORY = 20  # Keep last 20 exchanges

class ConversationMemory:
    def __init__(self):
        self.history = self.load_history()
        self.current_topics = {}  # Track what we're discussing
    
    def load_history(self):
        """Load conversation history from file"""
        try:
            if os.path.exists(CONV_FILE):
                with open(CONV_FILE, 'r') as f:
                    return json.load(f)
        except:
            pass
        return []
    
    def save_history(self):
        """Save conversation history to file"""
        try:
            # Keep only last MAX_HISTORY exchanges
            history_to_save = self.history[-MAX_HISTORY:]
            with open(CONV_FILE, 'w') as f:
                json.dump(history_to_save, f, indent=2)
        except Exception as e:
            print(f"[MEMORY] Error saving history: {e}")
    
    def add_exchange(self, user_input, ai_response, topic=None):
        """Add a user-AI exchange to history"""
        exchange = {
            "timestamp": datetime.now().isoformat(),
            "user": user_input,
            "response": ai_response,
            "topic": topic
        }
        self.history.append(exchange)
        self.save_history()
        
        # Track current topic
        if topic:
            self.current_topics[topic] = {
                "last_mentioned": user_input,
                "timestamp": datetime.now().isoformat(),
                "context": ai_response
            }
    
    def get_last_topic(self):
        """Get the most recently discussed topic"""
        if not self.history:
            return None
        
        # Look backwards through history for last non-None topic
        for exchange in reversed(self.history):
            if exchange.get("topic"):
                return exchange["topic"]
        return None
    
    def get_context(self, topic=None):
        """Get conversation context for a topic or current topic"""
        if not topic:
            topic = self.get_last_topic()
        
        if not topic or topic not in self.current_topics:
            return None
        
        return self.current_topics[topic]
    
    def get_related_exchanges(self, topic, limit=5):
        """Get recent exchanges about a specific topic"""
        related = [ex for ex in self.history if ex.get("topic") == topic]
        return related[-limit:]
    
    def build_context_prompt(self, current_query, topic=None):
        """Build a context-aware prompt for Groq AI"""
        if not topic:
            topic = self.get_last_topic()
        
        context_info = ""
        
        if topic:
            context_info += f"Current topic being discussed: {topic}\n"
            context_info += "Recent conversation context:\n"
            
            related = self.get_related_exchanges(topic, limit=3)
            for exchange in related:
                context_info += f"- User: {exchange['user']}\n"
                context_info += f"  Assistant: {exchange['response'][:100]}...\n"
        
        # Add recent general context
        if self.history:
            context_info += "\nRecent exchanges:\n"
            for exchange in self.history[-3:]:
                if exchange.get("topic") != topic:  # Don't repeat topic info
                    context_info += f"- {exchange['user'][:50]}...\n"
        
        return context_info
    
    def extract_topic(self, query):
        """Extract or identify topic from query"""
        query_lower = query.lower()
        
        # Keywords to identify topics
        topic_keywords = {
            'fc26': ['fc 26', 'fc26', 'fifa'],
            'game': ['game', 'play', 'gaming'],
            'movie': ['movie', 'film', 'watch'],
            'tech': ['tech', 'computer', 'phone', 'gadget'],
            'money': ['buy', 'cost', 'price', 'expensive', 'afford'],
            'health': ['health', 'exercise', 'diet', 'sick'],
            'work': ['job', 'work', 'career', 'boss'],
            'relationship': ['friend', 'girlfriend', 'boyfriend', 'family'],
        }
        
        for topic, keywords in topic_keywords.items():
            if any(kw in query_lower for kw in keywords):
                return topic
        
        # If can't identify, try to extract key noun-like words
        words = query_lower.split()
        if len(words) > 2:
            # Return first significant word as topic
            stop_words = {'should', 'i', 'do', 'what', 'how', 'why', 'is', 'are', 'the', 'a', 'an', 'or', 'and'}
            for word in words:
                if word not in stop_words and len(word) > 3:
                    return word
        
        return "general"
    
    def clear_history(self):
        """Clear conversation history"""
        self.history = []
        self.current_topics = {}
        self.save_history()

# Global instance
_conv_memory = None

def get_memory():
    """Get or create conversation memory instance"""
    global _conv_memory
    if _conv_memory is None:
        _conv_memory = ConversationMemory()
    return _conv_memory

def add_to_memory(user_input, ai_response):
    """Add exchange to memory"""
    memory = get_memory()
    topic = memory.extract_topic(user_input)
    memory.add_exchange(user_input, ai_response, topic)

def get_context_for_query(query):
    """Get context for a query"""
    memory = get_memory()
    topic = memory.extract_topic(query)
    return memory.build_context_prompt(query, topic)

def recall_topic(topic):
    """Recall context about a topic"""
    memory = get_memory()
    return memory.get_context(topic)

def get_current_topic():
    """Get what we're currently talking about"""
    memory = get_memory()
    return memory.get_last_topic()
