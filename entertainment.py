"""
JARVIS Entertainment Features - Games, jokes, meditation, trivia
"""

import random
import json
import os
from datetime import datetime

class Entertainment:
    def __init__(self):
        self.jokes = self.load_jokes()
        self.score = {'trivia': 0, '20q': 0}
    
    def load_jokes(self):
        return [
            "Why did the scarecrow win an award? Because he was outstanding in his field!",
            "I told my computer I needed a break, and now it won't stop sending me Kit-Kat ads.",
            "Why don't scientists trust atoms? Because they make up everything!",
            "What do you call a fake noodle? An impasta!",
            "Why did the math book look so sad? Because it had too many problems!",
            "I'm reading a book about anti-gravity. It's impossible to put down!",
            "Did you hear about the guy who invented Lifesavers? He made a mint!",
            "Where do boats go when they're sick? To the dock!",
            "What do you call a bear with no teeth? A gummy bear!",
            "Why did the cookie go to the doctor? Because it felt crumbly!",
        ]
    
    def tell_joke(self):
        """Tell a random joke"""
        joke = random.choice(self.jokes)
        return f"😂 {joke}"
    
    def play_trivia(self):
        """Single trivia question"""
        trivia = [
            {"q": "What is the capital of France?", "a": "paris", "options": "a) London, b) Paris, c) Berlin"},
            {"q": "What is 2 + 2?", "a": "4", "options": "a) 3, b) 4, c) 5"},
            {"q": "What color is the sky?", "a": "blue", "options": "a) Blue, b) Green, c) Red"},
            {"q": "How many continents are there?", "a": "7", "options": "a) 5, b) 6, c) 7"},
        ]
        q = random.choice(trivia)
        return f"🧠 Trivia: {q['q']}\n{q['options']}\n(Say your answer)"
    
    def play_twenty_questions(self):
        """Start a game of 20 questions"""
        items = ["apple", "elephant", "bicycle", "cloud", "guitar", "pyramid", "submarine"]
        target = random.choice(items)
        return f"🎯 I'm thinking of something... You have 20 questions! (Think: {target})"
    
    def meditation(self):
        """Guided meditation"""
        return """🧘 Guided Meditation - Close your eyes and breathe:

1. Breathe in slowly for 4 counts...
2. Hold for 4 counts...
3. Breathe out slowly for 4 counts...
4. Hold for 4 counts...

Repeat this 5 times. Focus on your breathing. Let thoughts pass like clouds.
Imagine a peaceful place - mountains, beach, or forest. Stay there for a moment."""
    
    def riddle(self):
        """Tell a riddle"""
        riddles = [
            {"riddle": "I speak without a mouth and hear without ears. What am I?", "answer": "an echo"},
            {"riddle": "What has keys but no lock?", "answer": "a piano"},
            {"riddle": "I'm tall when I'm young and short when I'm old. What am I?", "answer": "a candle"},
            {"riddle": "What gets wet while drying?", "answer": "a towel"},
        ]
        r = random.choice(riddles)
        return f"🤔 Riddle: {r['riddle']}\n(Answer: {r['answer']})"
    
    def word_game(self):
        """Word association game"""
        return "🎮 Word Game: I say a word, you say the first word that comes to mind!"

entertainment = Entertainment()
