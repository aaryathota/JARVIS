"""
Context Router Module - Restored
Routes user requests to appropriate handlers based on context
"""

def is_youtube_request(command):
    """Check if command is explicitly asking for YouTube"""
    youtube_keywords = ['youtube', 'ytube', 'yt channel', 'video channel', 'youtube video']
    cmd_lower = command.lower()
    return any(keyword in cmd_lower for keyword in youtube_keywords)

def get_youtube_alternative(search_query):
    """Get alternative search engine result if YouTube isn't explicitly requested"""
    alternatives = {
        'learn': 'https://www.khanacademy.org/search?q=',
        'news': 'https://news.google.com/search?q=',
        'research': 'https://scholar.google.com/scholar?q=',
    }
    
    for key, url in alternatives.items():
        if key in search_query.lower():
            return url + search_query.replace(' ', '+')
    
    # Default to Google
    return f"https://www.google.com/search?q={search_query.replace(' ', '+')}"

def route_and_open(url):
    """Route URL to appropriate opener"""
    import webbrowser
    try:
        webbrowser.open(url)
        print(f"[ROUTER] Opened: {url}")
        return url
    except Exception as e:
        print(f"[ROUTER ERROR] {e}")
        return None

def detect_context(command):
    """Detect the context of the command"""
    contexts = {
        'youtube': ['youtube', 'video', 'channel', 'shorts'],
        'social': ['facebook', 'twitter', 'instagram', 'tiktok'],
        'search': ['search', 'find', 'look up', 'research'],
        'news': ['news', 'headlines', 'current events'],
    }
    
    cmd_lower = command.lower()
    for context, keywords in contexts.items():
        if any(keyword in cmd_lower for keyword in keywords):
            return context
    
    return 'general'

def route_command(command):
    """Route command to appropriate handler"""
    context = detect_context(command)
    
    routing_map = {
        'youtube': 'handle_youtube',
        'social': 'handle_social_media',
        'search': 'handle_search',
        'news': 'handle_news',
        'general': 'handle_general',
    }
    
    handler = routing_map.get(context, 'handle_general')
    print(f"[ROUTER] Routing to: {handler} (context: {context})")
    return handler
