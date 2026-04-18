"""
PERSONALIZED ML LEARNER
Learns from every interaction and adapts to your preferences
Tracks patterns, preferences, and personality traits
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import threading
import time

class PersonalMLLearner:
    """
    Machine Learning system that learns from user preferences & patterns
    Uses SQLite for efficient storage and querying
    """
    
    def __init__(self, db_path="user_learning.db"):
        self.db_path = db_path
        self.init_database()
        self.personality_score = {}
        self.load_personality()
    
    def init_database(self):
        """Initialize SQLite database with learning tables"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")  # Enable WAL mode for concurrent access
        conn.execute("PRAGMA busy_timeout=5000")  # 5 second timeout
        cursor = conn.cursor()
        
        # Command history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS command_history (
                id INTEGER PRIMARY KEY,
                timestamp DATETIME,
                command TEXT,
                category TEXT,
                mode_used TEXT,
                response_type TEXT,
                success BOOLEAN
            )
        ''')
        
        # Mode preferences table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mode_preferences (
                id INTEGER PRIMARY KEY,
                mode TEXT,
                usage_count INTEGER DEFAULT 0,
                last_used DATETIME,
                average_session_length REAL DEFAULT 0,
                preferred_time TIME
            )
        ''')
        
        # Website preferences table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS website_preferences (
                id INTEGER PRIMARY KEY,
                website TEXT UNIQUE,
                open_count INTEGER DEFAULT 0,
                context TEXT,
                preferred_mode TEXT
            )
        ''')
        
        # Response format preferences table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS response_preferences (
                id INTEGER PRIMARY KEY,
                format_type TEXT,
                preference_score REAL DEFAULT 0.5,
                usage_count INTEGER DEFAULT 0
            )
        ''')
        
        # Email presets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_presets (
                id INTEGER PRIMARY KEY,
                recipient TEXT,
                preset_name TEXT,
                subject_template TEXT,
                body_template TEXT,
                tone TEXT,
                usage_count INTEGER DEFAULT 0
            )
        ''')
        
        # Personality traits table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS personality_traits (
                id INTEGER PRIMARY KEY,
                trait_name TEXT UNIQUE,
                score REAL DEFAULT 0.5,
                confidence REAL DEFAULT 0.1
            )
        ''')
        
        # Communication style table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS communication_style (
                id INTEGER PRIMARY KEY,
                style_name TEXT UNIQUE,
                score REAL DEFAULT 0.5
            )
        ''')
        
        # Daily patterns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_patterns (
                id INTEGER PRIMARY KEY,
                day_of_week TEXT,
                hour INTEGER,
                command_type TEXT,
                frequency INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _safe_db_operation(self, operation_func, max_retries=3, operation_name=""):
        """
        Safe database operation with retry logic for handling locks
        Uses exponential backoff to avoid overwhelming the database
        """
        for attempt in range(max_retries):
            try:
                return operation_func()
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e):
                    if attempt < max_retries - 1:
                        # Exponential backoff: 50ms, 100ms, 200ms
                        wait_time = (50 * (2 ** attempt)) / 1000
                        time.sleep(wait_time)
                    else:
                        # Silently fail on last attempt - don't block user
                        return None
                else:
                    raise
            except Exception as e:
                # Don't spam errors, just fail silently
                return None
        return None
    
    def log_command(self, command, category, mode_used="", response_type="text", success=True):
        """Log a command execution for learning"""
        def operation():
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA busy_timeout=2000")
            cursor = conn.cursor()
            
            # Insert command history
            cursor.execute('''
                INSERT INTO command_history 
                (timestamp, command, category, mode_used, response_type, success)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (datetime.now(), command, category, mode_used, response_type, success))
            
            # Update personality traits inline
            traits = {}
            if "email" in category.lower():
                traits["communicative"] = 0.1
            if "research" in category.lower() or "news" in category.lower():
                traits["curious"] = 0.1
            if "project" in category.lower() or "create" in category.lower():
                traits["creative"] = 0.1
            if "weather" in category.lower() or "reminder" in category.lower():
                traits["organized"] = 0.1
            if "music" in category.lower() or "chill" in category.lower():
                traits["relaxed"] = 0.1
            
            for trait, increment in traits.items():
                cursor.execute('''
                    INSERT OR IGNORE INTO personality_traits (trait_name, score, confidence)
                    VALUES (?, 0.5, 0.1)
                ''', (trait,))
                cursor.execute('''
                    UPDATE personality_traits 
                    SET score = MIN(1.0, score + ?),
                        confidence = MIN(1.0, confidence + 0.05)
                    WHERE trait_name = ?
                ''', (increment, trait))
            
            # Update mode preference inline
            if mode_used:
                cursor.execute('''
                    INSERT OR IGNORE INTO mode_preferences (mode, usage_count, last_used)
                    VALUES (?, 1, ?)
                ''', (mode_used, datetime.now()))
                cursor.execute('''
                    UPDATE mode_preferences 
                    SET usage_count = usage_count + 1, last_used = ?
                    WHERE mode = ?
                ''', (datetime.now(), mode_used))
            
            # Update daily patterns inline
            now = datetime.now()
            day_name = now.strftime("%A")
            hour = now.hour
            cursor.execute('''
                INSERT OR IGNORE INTO daily_patterns (day_of_week, hour, command_type, frequency)
                VALUES (?, ?, ?, 1)
            ''', (day_name, hour, category))
            cursor.execute('''
                UPDATE daily_patterns 
                SET frequency = frequency + 1
                WHERE day_of_week = ? AND hour = ? AND command_type = ?
            ''', (day_name, hour, category))
            
            conn.commit()
            conn.close()
        
        # Use safe operation with retry logic
        self._safe_db_operation(operation, operation_name="log_command")
    
    def log_website_opened(self, website, context="", mode_used=""):
        """Track when websites are opened"""
        def operation():
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA busy_timeout=2000")
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR IGNORE INTO website_preferences (website, context, preferred_mode)
                VALUES (?, ?, ?)
            ''', (website, context, mode_used))
            
            cursor.execute('''
                UPDATE website_preferences 
                SET open_count = open_count + 1, preferred_mode = ?
                WHERE website = ?
            ''', (mode_used, website))
            
            conn.commit()
            conn.close()
        
        self._safe_db_operation(operation, operation_name="log_website")
    
    def log_response_preference(self, format_type, user_satisfaction=0.5):
        """Learn which response formats user prefers"""
        def operation():
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA busy_timeout=2000")
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR IGNORE INTO response_preferences (format_type, preference_score)
                VALUES (?, ?)
            ''', (format_type, user_satisfaction))
            
            # Exponential smoothing: new_score = 0.7 * old_score + 0.3 * new_score
            cursor.execute('''
                UPDATE response_preferences 
                SET preference_score = preference_score * 0.7 + ? * 0.3,
                    usage_count = usage_count + 1
                WHERE format_type = ?
            ''', (user_satisfaction, format_type))
            
            conn.commit()
            conn.close()
        
        self._safe_db_operation(operation, operation_name="log_response_pref")
    
    def save_email_preset(self, recipient, preset_name, subject, body, tone="professional"):
        """Save user's email presets for quick sending"""
        def operation():
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA busy_timeout=2000")
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO email_presets 
                (recipient, preset_name, subject_template, body_template, tone)
                VALUES (?, ?, ?, ?, ?)
            ''', (recipient, preset_name, subject, body, tone))
            
            conn.commit()
            conn.close()
        
        self._safe_db_operation(operation, operation_name="save_email")
        # Print only on success, silently fail on lock
        return True
    
    def get_email_preset(self, recipient=None, preset_name=None):
        """Retrieve saved email presets"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if preset_name:
                cursor.execute('''
                    SELECT subject_template, body_template, tone 
                    FROM email_presets 
                    WHERE preset_name = ?
                ''', (preset_name,))
            elif recipient:
                cursor.execute('''
                    SELECT preset_name, subject_template, body_template, tone 
                    FROM email_presets 
                    WHERE recipient = ?
                ''', (recipient,))
            
            result = cursor.fetchall()
            conn.close()
            return result
        except Exception as e:
            print(f"[ML] Error retrieving email preset: {e}")
            return []
    
    def get_preferred_response_format(self):
        """Get user's preferred response format (list, summary, detailed, brief)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT format_type, preference_score 
                FROM response_preferences 
                ORDER BY preference_score DESC 
                LIMIT 1
            ''')
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return result[0], result[1]  # format_type, score
            else:
                return "summary", 0.5  # Default
        except Exception as e:
            print(f"[ML] Error getting response format: {e}")
            return "summary", 0.5
    
    def get_preferred_mode(self):
        """Get user's most-used mode"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT mode, usage_count 
                FROM mode_preferences 
                ORDER BY usage_count DESC 
                LIMIT 1
            ''')
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return result[0], result[1]  # mode, usage_count
            else:
                return None, 0
        except Exception as e:
            print(f"[ML] Error getting preferred mode: {e}")
            return None, 0
    
    def get_favorite_websites(self, limit=5):
        """Get most frequently used websites"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT website, open_count, preferred_mode 
                FROM website_preferences 
                ORDER BY open_count DESC 
                LIMIT ?
            ''', (limit,))
            
            results = cursor.fetchall()
            conn.close()
            return results
        except Exception as e:
            print(f"[ML] Error getting favorite websites: {e}")
            return []
    def _update_personality_traits(self, command, category):
        """Analyze command and update personality traits - DEPRECATED: Inlined in log_command"""
        # This method is kept for backward compatibility but not used
        pass
    
    def _update_mode_preference(self, mode_used):
        """Update mode usage statistics - DEPRECATED: Inlined in log_command"""
        # This method is kept for backward compatibility but not used
        pass
    
    def _update_daily_patterns(self, command_type):
        """Track when user typically uses commands - DEPRECATED: Inlined in log_command"""
        # This method is kept for backward compatibility but not used
        pass
    
    def load_personality(self):
        """Load personality traits into memory for quick access"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT trait_name, score, confidence FROM personality_traits')
            traits = cursor.fetchall()
            conn.close()
            
            self.personality_score = {trait[0]: {"score": trait[1], "confidence": trait[2]} 
                                     for trait in traits}
        except Exception as e:
            print(f"[ML] Error loading personality: {e}")
    
    def get_personality_profile(self):
        """Get user's learned personality profile"""
        self.load_personality()
        
        if not self.personality_score:
            return {
                "primary_traits": [],
                "personality_summary": "Getting to know you better..."
            }
        
        # Sort by confidence and score
        sorted_traits = sorted(
            self.personality_score.items(),
            key=lambda x: x[1]["score"] * x[1]["confidence"],
            reverse=True
        )
        
        primary = [t[0] for t in sorted_traits[:3] if t[1]["score"] > 0.5]
        
        summary = self._generate_personality_summary(primary)
        
        return {
            "primary_traits": primary,
            "personality_summary": summary,
            "all_traits": self.personality_score
        }
    
    def _generate_personality_summary(self, traits):
        """Generate personality description from traits"""
        if not traits:
            return "I'm still learning about you..."
        
        trait_descriptions = {
            "communicative": "You're very communicative and like staying in touch",
            "curious": "You're curious and love exploring new information",
            "creative": "You're creative and love building new things",
            "organized": "You're very organized and like planning ahead",
            "relaxed": "You enjoy taking it easy and relaxing when needed",
            "productive": "You're highly productive and focused on getting things done"
        }
        
        descriptions = [trait_descriptions.get(t, f"You're {t}") for t in traits if t in trait_descriptions]
        
        if len(descriptions) >= 2:
            return ". ".join(descriptions[:2]) + ". You're becoming more predictable to me."
        elif descriptions:
            return descriptions[0] + ". I'm learning more about you."
        else:
            return "I'm still learning about who you are..."
    
    def get_learning_progress(self):
        """Get statistics about learning progress"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM command_history')
            total_commands = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM website_preferences')
            unique_websites = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM mode_preferences')
            modes_used = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM email_presets')
            email_presets = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT COUNT(*) FROM personality_traits 
                WHERE confidence > 0.3
            ''')
            learned_traits = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "total_commands": total_commands,
                "unique_websites": unique_websites,
                "modes_used": modes_used,
                "email_presets": email_presets,
                "learned_traits": learned_traits,
                "learning_level": min(100, int((total_commands / 50) * 100))  # 50 commands = 100% level
            }
        except Exception as e:
            print(f"[ML] Error getting learning progress: {e}")
            return {}
    
    def get_smart_greeting(self):
        """Generate personalized greeting based on learned profile"""
        profile = self.get_personality_profile()
        traits = profile.get("primary_traits", [])
        
        time_of_day = datetime.now().hour
        if 5 <= time_of_day < 12:
            time_greeting = "Good morning"
        elif 12 <= time_of_day < 17:
            time_greeting = "Good afternoon"
        else:
            time_greeting = "Good evening"
        
        greetings = {
            "communicative": f"{time_greeting}! Ready to help you stay connected?",
            "curious": f"{time_greeting}! I found something interesting you might like!",
            "creative": f"{time_greeting}! Want to create something amazing today?",
            "organized": f"{time_greeting}! Your schedule is all set and ready to go.",
            "relaxed": f"{time_greeting}! How about we take it easy today?",
        }
        
        for trait in traits:
            if trait in greetings:
                return greetings[trait]
        
        return f"{time_greeting}! I'm getting to know you better."
    
    def get_should_automate(self, command_type):
        """Determine if this command should be automated based on frequency"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT COUNT(*) FROM command_history 
                WHERE category = ? AND timestamp > datetime('now', '-7 days')
            ''', (command_type,))
            
            recent_count = cursor.fetchone()[0]
            conn.close()
            
            # If done 3+ times in last week, offer automation
            return recent_count >= 3
        except Exception as e:
            print(f"[ML] Error checking automation: {e}")
            return False


# Create global learner instance
learner = PersonalMLLearner()
