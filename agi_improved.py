"""
AGI Improved Module - Restored
Advanced location and navigation services
"""

import webbrowser
import json

# Default location (will be overridden by dynamic detection)
CURRENT_LOCATION = "Your Current Location"

def get_current_location():
    """Get current user location - dynamically detected"""
    try:
        from geolocation import get_user_location, format_location_string
        location_data = get_user_location()
        detected = format_location_string(location_data)
        if detected and detected != "Unknown, Unknown":
            return detected
    except Exception as e:
        print(f"[LOCATION_DEBUG] Error in get_current_location: {e}")
    
    # Fallback approaches
    try:
        from config import DEFAULT_LOCATION
        return DEFAULT_LOCATION
    except:
        pass
    
    return CURRENT_LOCATION

def find_restaurants(location="", cuisine="", num_results=5):
    """Find restaurants based on location and cuisine"""
    try:
        print(f"[RESTAURANTS] Searching for {cuisine} restaurants in {location}...")
        
        if not location:
            location = get_current_location()
        
        # Open Google Maps search for restaurants
        search_query = f"{cuisine} restaurants in {location}" if cuisine else f"restaurants in {location}"
        url = f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}"
        
        print(f"[RESTAURANTS] Opening: {url}")
        webbrowser.open(url)
        
        return {
            'location': location,
            'cuisine': cuisine,
            'results_url': url,
            'num_results': num_results
        }
    
    except Exception as e:
        print(f"[RESTAURANTS ERROR] {e}")
        return None

def open_restaurants_in_browser(location="", cuisine=""):
    """Open restaurant search in browser"""
    return find_restaurants(location, cuisine)

def get_directions(origin="", destination=""):
    """Get directions from origin to destination"""
    try:
        print(f"[DIRECTIONS] Getting directions from {origin} to {destination}...")
        
        if not origin:
            origin = get_current_location()
        
        # Create Google Maps directions URL
        url = f"https://www.google.com/maps/dir/{origin.replace(' ', '+')}/{destination.replace(' ', '+')}"
        
        print(f"[DIRECTIONS] Opening: {url}")
        webbrowser.open(url)
        
        return {
            'origin': origin,
            'destination': destination,
            'directions_url': url
        }
    
    except Exception as e:
        print(f"[DIRECTIONS ERROR] {e}")
        return None

def open_google_earth():
    """Open Google Earth"""
    try:
        print("[EARTH] Opening Google Earth...")
        url = f"https://earth.google.com/web/"
        webbrowser.open(url)
        return True
    
    except Exception as e:
        print(f"[EARTH ERROR] {e}")
        return False

def get_location_recommendations(location=""):
    """Get recommendations for a location"""
    try:
        if not location:
            location = get_current_location()
        
        print(f"[RECOMMENDATIONS] Getting recommendations for {location}...")
        url = f"https://www.google.com/maps/search/things+to+do+in+{location.replace(' ', '+')}"
        
        webbrowser.open(url)
        return url
    
    except Exception as e:
        print(f"[RECOMMENDATIONS ERROR] {e}")
        return None

def navigate_to_location(location):
    """Navigate to a specific location"""
    try:
        print(f"[NAV] Navigating to {location}...")
        url = f"https://www.google.com/maps/search/{location.replace(' ', '+')}"
        webbrowser.open(url)
        return True
    
    except Exception as e:
        print(f"[NAV ERROR] {e}")
        return False

def search_nearby(search_term=""):
    """Search for nearby places"""
    try:
        location = get_current_location()
        print(f"[NEARBY] Searching for {search_term} near {location}...")
        
        url = f"https://www.google.com/maps/search/{search_term.replace(' ', '+')}+near+{location.replace(' ', '+')}"
        webbrowser.open(url)
        return url
    
    except Exception as e:
        print(f"[NEARBY ERROR] {e}")
        return None
