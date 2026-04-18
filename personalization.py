"""
PERSONALIZATION ENGINE
Uses ML learning data to personalize responses and interactions
Makes the assistant feel like it truly knows the user
"""

from ml_learner import learner
import random

class PersonalizationEngine:
    """
    Takes learned data and personalizes:
    - Greetings
    - Response formats
    - Conversation tone
    - Suggestions
    - App/website recommendations
    """
    
    def __init__(self):
        self.learner = learner
    
    def personalize_greeting(self):
        """Get personalized greeting based on learned profile"""
        return self.learner.get_smart_greeting()
    
    def personalize_response(self, base_response, response_type="generic"):
        """Adapt response format based on user preferences"""
        format_type, score = self.learner.get_preferred_response_format()
        
        if format_type == "list":
            return self._format_as_list(base_response)
        elif format_type == "summary":
            return self._format_as_summary(base_response)
        elif format_type == "brief":
            return self._format_as_brief(base_response)
        else:
            return base_response
    
    def get_personalized_suggestion(self, context):
        """Suggest apps/websites based on learned preferences"""
        favorites = self.learner.get_favorite_websites(limit=3)
        
        if not favorites:
            return None
        
        # Pick a website user frequently uses in similar context
        for website, count, mode in favorites:
            if context.lower() in website.lower() or count > 2:
                return website
        
        return favorites[0][0]  # Return most used overall
    
    def get_recommended_mode(self):
        """Recommend the mode user most frequently uses"""
        preferred_mode, count = self.learner.get_preferred_mode()
        
        if preferred_mode and count > 2:
            return preferred_mode
        
        return None
    
    def should_offer_email_preset(self, recipient):
        """Suggest saved email presets if available"""
        presets = self.learner.get_email_preset(recipient=recipient)
        return len(presets) > 0
    
    def get_email_suggestions(self, recipient):
        """Get email preset suggestions for recipient"""
        return self.learner.get_email_preset(recipient=recipient)
    
    def personalize_tone(self):
        """Get communication style adapted to user"""
        profile = self.learner.get_personality_profile()
        traits = profile.get("primary_traits", [])
        
        tone_map = {
            "communicative": "friendly and conversational",
            "curious": "enthusiastic and informative",
            "creative": "imaginative and inspiring",
            "organized": "clear and structured",
            "relaxed": "casual and laid-back",
            "productive": "concise and action-focused"
        }
        
        for trait in traits:
            if trait in tone_map:
                return tone_map[trait]
        
        return "friendly and helpful"
    
    def get_personality_summary(self):
        """Get text summary of learned personality"""
        profile = self.learner.get_personality_profile()
        return profile.get("personality_summary", "Getting to know you...")
    
    def get_learning_stats(self):
        """Get learning progress statistics"""
        stats = self.learner.get_learning_progress()
        return stats
    
    def _format_as_list(self, response):
        """Format response as numbered list"""
        if isinstance(response, list):
            return "\n".join([f"{i+1}. {item}" for i, item in enumerate(response)])
        return response
    
    def _format_as_summary(self, response):
        """Format response as concise summary"""
        if isinstance(response, list):
            return " | ".join([str(item) for item in response[:3]])
        return response[:200] + "..." if len(str(response)) > 200 else response
    
    def _format_as_brief(self, response):
        """Format response as very brief answer"""
        if isinstance(response, list):
            return response[0] if response else "Done"
        return str(response)[:100]
    
    def get_personalized_app_suggestions(self):
        """Suggest apps to open based on context and time"""
        mode = self.get_recommended_mode()
        favorites = self.learner.get_favorite_websites(limit=5)
        
        suggestions = {
            "recommended_mode": mode,
            "favorite_websites": [f[0] for f in favorites]
        }
        
        return suggestions
    
    def get_next_likely_action(self, current_command):
        """Predict what user might do next based on patterns"""
        # Get daily patterns from learner
        try:
            conn = self.learner.db_path
            import sqlite3
            conn = sqlite3.connect(conn)
            cursor = conn.cursor()
            
            # Get most frequent commands around current time
            from datetime import datetime
            current_hour = datetime.now().hour
            
            cursor.execute('''
                SELECT command_type, frequency FROM daily_patterns 
                WHERE hour BETWEEN ? AND ?
                ORDER BY frequency DESC LIMIT 1
            ''', (current_hour, current_hour + 1))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return result[0]  # Most likely next command
        except:
            pass
        
        return None
    
    def create_personalized_context(self, command, mode=""):
        """Create personalized context for command processing"""
        profile = self.learner.get_personality_profile()
        stats = self.learner.get_learning_progress()
        
        context = {
            "user_personality": profile.get("primary_traits", []),
            "learned_traits": profile.get("all_traits", {}),
            "preferred_tone": self.personalize_tone(),
            "learning_level": stats.get("learning_level", 0),
            "total_commands": stats.get("total_commands", 0),
            "favorite_websites": [f[0] for f in self.learner.get_favorite_websites()],
            "email_presets_count": stats.get("email_presets", 0)
        }
        
        return context
    
    def speak_like_knows_them(self, message, context_type="generic"):
        """Add personality to spoken message"""
        profile = self.learner.get_personality_profile()
        traits = profile.get("primary_traits", [])
        
        personalization_map = {
            "communicative": [
                "I know you love staying connected, so ",
                "Since you're always in touch, ",
                "I remember you prefer quick communication, "
            ],
            "curious": [
                "I found something interesting for you: ",
                "Based on your curiosity, ",
                "I know you'd be interested in this: "
            ],
            "creative": [
                "I know you'll love this creative approach: ",
                "Based on your creative style, ",
                "I found something inspiring for you: "
            ],
            "organized": [
                "I've organized this for you: ",
                "Based on your preference for structure, ",
                "I know you like things organized, so "
            ],
            "relaxed": [
                "No rush, but here's something relaxing: ",
                "I know you prefer taking it easy, ",
                "Here's something chill for you: "
            ]
        }
        
        for trait in traits:
            if trait in personalization_map:
                prefix = random.choice(personalization_map[trait])
                return prefix + message
        
        return message
    
    def should_suggest_automation(self, command_type):
        """Check if should suggest automating repetitive commands"""
        return self.learner.get_should_automate(command_type)
    
    def get_automation_suggestion(self, command_type):
        """Generate automation suggestion based on frequency"""
        return f"I notice you do this frequently. Would you like me to automate '{command_type}' for you?"


# Create global personalization instance
personalizer = PersonalizationEngine()
