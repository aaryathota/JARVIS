"""
SMART WEB BROWSER CONTROLLER
AI-powered intelligent website routing, news with video clips, and context-based suggestions
"""

import webbrowser
import requests
from ai import ask_ai_text
from utils import speak
import threading
import time

# Website knowledge base for context matching
WEBSITE_DATABASE = {
    "coding": {
        "primary": ["stackoverflow.com", "github.com", "codesandbox.io", "replit.com"],
        "ai_help": ["claude.ai", "chatgpt.com", "perplexity.ai"],
        "tutorials": ["freecodecamp.org", "codecademy.com", "udemy.com"]
    },
    "design": {
        "primary": ["canva.com", "figma.com", "adobe.com", "dribbble.com"],
        "inspiration": ["pinterest.com", "behance.net"],
        "tutorials": ["skillshare.com", "udemy.com"]
    },
    "writing": {
        "primary": ["grammarly.com", "notion.so", "medium.com"],
        "blogs": ["dev.to", "hashnode.com"],
        "tools": ["hemingwayapp.com"]
    },
    "video": {
        "primary": ["youtube.com", "vimeo.com", "dailymotion.com"],
        "editing": ["capcut.com", "filmora.com"],
        "hosting": ["uploadcare.com"]
    },
    "music": {
        "primary": ["spotify.com", "musicbrainz.org"],
        "creation": ["soundcloud.com", "bandcamp.com"],
        "finding": ["genius.com"]
    },
    "learning": {
        "primary": ["coursera.org", "udemy.com", "skillshare.com"],
        "videos": ["youtube.com", "khanacademy.org"],
        "interactive": ["codecademy.com", "freecodecamp.org"]
    },
    "news": {
        "mainstream": ["bbc.com", "cnn.com", "reuters.com", "apnews.com"],
        "tech": ["techcrunch.com", "theverge.com", "wired.com", "arstechnica.com"],
        "video": ["youtube.com/results?search_query=news", "reddit.com/r/news"],
        "trending": ["reddit.com", "hackernews.com", "producthunt.com"]
    },
    "business": {
        "primary": ["linkedin.com", "bloomberg.com", "forbes.com"],
        "startup": ["producthunt.com", "angel.co"],
        "finance": ["coinbase.com", "investing.com"]
    },
    "entertainment": {
        "streaming": ["netflix.com", "disneyplus.com", "hbomax.com", "primevideo.com"],
        "social": ["tiktok.com", "instagram.com", "youtube.com"],
        "culture": ["rotten tomatoes.com"]
    }
}

def understand_purpose(command):
    """Use AI to understand what the user actually wants to do"""
    try:
        prompt = f"""Analyze this command and identify the user's PURPOSE and WEBSITES to open:
"{command}"

Respond in format:
PURPOSE: [what are they trying to do]
WEBSITES: [comma separated list of relevant websites]
SEARCH_TERM: [if they need to search for something]

Example 1: "I want to make a nice flyer"
PURPOSE: graphic design
WEBSITES: canva.com, figma.com
SEARCH_TERM: flyer templates

Example 2: "Help me learn Python"
PURPOSE: programming education
WEBSITES: freecodecamp.org, codecademy.com, claude.ai
SEARCH_TERM: python tutorial for beginners

Only respond with PURPOSE:|WEBSITES:|SEARCH_TERM: format."""

        response = ask_ai_text(prompt).strip()
        
        # Parse response
        result = {
            "purpose": "",
            "websites": [],
            "search_term": ""
        }
        
        for line in response.split("\n"):
            if "PURPOSE:" in line:
                result["purpose"] = line.split("PURPOSE:")[1].strip()
            elif "WEBSITES:" in line:
                websites_str = line.split("WEBSITES:")[1].strip()
                result["websites"] = [w.strip() for w in websites_str.split(",") if w.strip()]
            elif "SEARCH_TERM:" in line:
                result["search_term"] = line.split("SEARCH_TERM:")[1].strip()
        
        return result
    except Exception as e:
        print(f"[SMART_WEB] Purpose detection error: {e}")
        return {"purpose": "general", "websites": [], "search_term": ""}

def smart_open_websites(websites_list, delay=1.5):
    """Open multiple websites with smart delays"""
    print(f"[SMART_WEB] Opening {len(websites_list)} websites...")
    
    def open_in_background():
        for i, website in enumerate(websites_list, 1):
            try:
                # Add protocol if missing
                if not website.startswith("http"):
                    website = f"https://{website}"
                
                print(f"[SMART_WEB] {i}. Opening: {website[:60]}...")
                webbrowser.open(website, new=1)
                
                if i < len(websites_list):
                    time.sleep(delay)  # Delay between opening tabs
            except Exception as e:
                print(f"[SMART_WEB] Error opening {website}: {e}")
    
    # Run in background thread so it doesn't block
    threading.Thread(target=open_in_background, daemon=True).start()

def get_smart_suggestions(topic):
    """Get AI-powered suggestions for how to do something and open relevant websites"""
    try:
        prompt = f"""User wants suggestions about: "{topic}"

Provide:
1. 3-5 specific, actionable suggestions (numbered)
2. Best tools/websites to help them (with URLs)
3. Quick tips

Make it practical and immediately useful. Keep suggestions brief and concrete."""
        
        suggestions = ask_ai_text(prompt)
        return suggestions
    except Exception as e:
        print(f"[SUGGESTIONS] Error: {e}")
        return "I can help, but I'm having trouble generating suggestions right now."

def fetch_news_with_videos(query="general"):
    """Fetch news from multiple sources including video news"""
    try:
        print(f"[NEWS] Opening news sources about: {query}")
        
        # News sources to open
        news_sources = [
            f"https://www.reddit.com/r/news/",  # News discussions
            f"https://www.bbc.com/news/" if "tech" not in query.lower() else "https://www.techcrunch.com/",
            f"https://www.google.com/news/search?q={query.replace(' ', '+')}&hl=en-US&gl=US&ceid=US%3Aen",
        ]
        
        print(f"[NEWS] Opening {len(news_sources)} news sources...")
        
        # Open news in browser - IMPORTANT: Do this in background thread to not block
        def open_sources():
            for i, source in enumerate(news_sources):
                try:
                    print(f"[NEWS] Opening {i+1}: {source[:60]}...")
                    webbrowser.open(source, new=1)
                    time.sleep(1.5)
                except Exception as e:
                    print(f"[NEWS] Could not open {source}: {e}")
        
        # Run in background thread
        threading.Thread(target=open_sources, daemon=True).start()
        
        return f"Opening news sources about {query}. Check your browser."
            
    except Exception as e:
        print(f"[NEWS ERROR] {e}")
        return "Opening news for you now..."

def smart_browser_open(command):
    """
    Intelligently open websites based on user command
    - Restricts YouTube unless explicitly mentioned
    - Opens relevant websites based on context
    - Provides suggestions when appropriate
    """
    try:
        from context_router import is_youtube_request, get_youtube_alternative, route_and_open
        
        cmd_lower = command.lower()
        
        # Extract the core command (what they want to do/search for)
        search_query = cmd_lower.replace("open", "").replace("visit", "").replace("browse", "").replace("show me", "").replace("find", "").strip()
        
        # CHECK 1: Is YouTube explicitly mentioned?
        if is_youtube_request(command):
            print("[SMART_WEB] YouTube explicitly requested - opening YouTube")
            url = f"https://www.youtube.com/results?search_query={search_query.replace(' ', '+')}"
            webbrowser.open(url, new=1)
            speak(f"Opening YouTube for {search_query}")
            return
        
        # If they said "video" or similar but NOT "youtube" explicitly, use alternatives
        if "video" in cmd_lower and not is_youtube_request(command):
            print("[SMART_WEB] Video search (restricting from YouTube)")
            alternatives = get_youtube_alternative(search_query)
            speak(f"Searching for videos on alternative platforms")
            smart_open_websites(alternatives[:2])
            return
        
        # CHECK 2: Are they asking for suggestions?
        if any(word in cmd_lower for word in ["suggest", "ideas", "how to", "tips", "best way", "guide"]):
            print("[SMART_WEB] Suggestion request")
            suggestions = get_smart_suggestions(search_query)
            speak(suggestions)
            
            # Open relevant websites based on purpose
            purpose_info = understand_purpose(search_query)
            if purpose_info["websites"]:
                smart_open_websites(purpose_info["websites"][:3])
            return
        
        # CHECK 3: Use smart purpose detection
        print("[SMART_WEB] Analyzing purpose...")
        purpose_info = understand_purpose(command)
        
        print(f"[SMART_WEB] Purpose: {purpose_info['purpose']}")
        print(f"[SMART_WEB] Websites: {purpose_info['websites']}")
        print(f"[SMART_WEB] Search: {purpose_info['search_term']}")
        
        # Open the suggested websites
        if purpose_info["websites"]:
            smart_open_websites(purpose_info["websites"][:4])  # Limit to 4 sites
        else:
            # If no websites detected, offer default search
            if search_query:
                google_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
                webbrowser.open(google_url, new=1)
                speak(f"Searching for {search_query}")
            else:
                speak("What would you like me to open?")
                
    except Exception as e:
        print(f"[SMART_WEB ERROR] {e}")
        try:
            speak("Opening that for you now")

            webbrowser.open("https://www.google.com", new=1)
        except:
            pass

def suggest_for_making(topic):
    """When user wants to MAKE something, suggest relevant tools and open them"""
    try:
        print(f"[MAKE_SUGGESTIONS] User wants to make: {topic}")
        
        prompt = f"""User wants to create/make: "{topic}"

Provide:
1. Best tools/software to use (with websites)
2. Quick 5-minute tips to get started
3. Common beginner mistakes to avoid

Be specific with tool recommendations."""
        
        suggestions = ask_ai_text(prompt)
        speak(suggestions)
        
        # Now intelligently open relevant websites
        purpose_info = understand_purpose(f"I want to make {topic}")
        if purpose_info["websites"]:
            speak("Opening the best tools for this now...")
            smart_open_websites(purpose_info["websites"][:5])
        
        return suggestions
    except Exception as e:
        print(f"[MAKE_SUGGESTIONS ERROR] {e}")
        return "I can help you make that!"
