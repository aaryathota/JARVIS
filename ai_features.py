"""
JARVIS AI/ML Features - Image recognition, sentiment analysis, spam filter
"""

import json
import os
from groq import Groq

class AIFeatures:
    def __init__(self):
        self.spam_keywords = ['buy now', 'limited time', 'act now', 'free money', 'click here']
        try:
            with open('groq_key.txt', 'r') as f:
                api_key = f.read().strip()
            self.groq_client = Groq(api_key=api_key)
        except:
            self.groq_client = None
    
    def analyze_sentiment(self, text):
        """Analyze sentiment of text"""
        # Simple rule-based sentiment (would use BERT/transformers in production)
        positive_words = ['good', 'great', 'excellent', 'love', 'wonderful', 'happy']
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'angry', 'sad']
        
        text_lower = text.lower()
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if pos_count > neg_count:
            sentiment = "POSITIVE 😊"
        elif neg_count > pos_count:
            sentiment = "NEGATIVE 😞"
        else:
            sentiment = "NEUTRAL 😐"
        
        return f"💭 Sentiment Analysis: {sentiment}\nScore: {pos_count} positive, {neg_count} negative"
    
    def detect_spam(self, text):
        """Detect if text is spam"""
        keyword_count = sum(1 for keyword in self.spam_keywords if keyword.lower() in text.lower())
        
        if keyword_count > 2:
            return f"⚠️ LIKELY SPAM - Found {keyword_count} spam keywords"
        elif keyword_count > 0:
            return f"⚠️ POSSIBLE SPAM - Found {keyword_count} spam keywords"
        else:
            return "✓ Not spam"
    
    def extract_entities(self, text):
        """Extract named entities"""
        return f"""🏷️ Named Entities:
Text: {text}
[Entity extraction would identify: persons, locations, organizations, etc.]"""
    
    def image_recognition(self, image_path):
        """Recognize objects in image"""
        if os.path.exists(image_path):
            return f"""🖼️ Image Recognition:
Image: {image_path}
Objects: [Would use YOLO or similar]
Confidence: [Would show confidence scores]"""
        return f"❌ Image not found: {image_path}"
    
    def text_classification(self, text):
        """Classify text into categories"""
        categories = ['news', 'spam', 'personal', 'work', 'entertainment']
        return f"""📂 Text Classification:
Text: {text[:50]}...
Possible categories: {', '.join(categories)}
Top match: [Would show here]"""
    
    def generate_text(self, prompt, length=100):
        """Generate text using Groq API"""
        if not self.groq_client:
            return f"❌ Groq API not configured"
        
        try:
            message = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{
                    "role": "user",
                    "content": f"Generate {length} words on: {prompt}"
                }],
                max_tokens=500,
            )
            generated = message.choices[0].message.content.strip()
            return generated
        except Exception as e:
            return f"❌ Generation error: {str(e)}"
    
    def translate_text(self, text, target_language='spanish'):
        """Translate text using Groq API"""
        if not self.groq_client:
            return f"❌ Groq API not configured"
        
        try:
            message = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{
                    "role": "user",
                    "content": f"Translate this to {target_language}. Only respond with the translation, nothing else:\n{text}"
                }],
                max_tokens=500,
            )
            translation = message.choices[0].message.content.strip()
            return translation
        except Exception as e:
            return f"❌ Translation error: {str(e)}"

ai_features = AIFeatures()
