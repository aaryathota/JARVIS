"""
Geolocation and Time Module - Get user's real location and current time
"""

import requests
from datetime import datetime
import pytz

def get_user_location():
    """Get user's actual IP-based location"""
    try:
        # Using free geolocation API
        response = requests.get('https://ipapi.co/json/', timeout=3)
        
        if response.status_code == 200:
            data = response.json()
            location = {
                "city": data.get('city', 'Unknown'),
                "country": data.get('country_name', 'Unknown'),
                "latitude": data.get('latitude', 0),
                "longitude": data.get('longitude', 0),
                "timezone": data.get('timezone', 'UTC'),
                "country_code": data.get('country_code', 'US'),
            }
            print(f"[LOCATION] Detected: {location['city']}, {location['country']}")
            return location
    except requests.exceptions.Timeout:
        print("[LOCATION] Timeout - using fallback")
    except Exception as e:
        print(f"[LOCATION] Error: {type(e).__name__}")
    
    # Fallback location
    return {
        "city": "Your City",
        "country": "Your Country",
        "latitude": 0,
        "longitude": 0,
        "timezone": "UTC",
        "country_code": "US",
    }


def get_current_time():
    """Get current time formatted nicely"""
    try:
        now = datetime.now()
        return {
            "time": now.strftime("%I:%M %p"),  # 02:30 PM format
            "date": now.strftime("%A, %B %d, %Y"),  # Monday, April 14, 2026
            "hour": now.hour,
            "minute": now.minute,
            "timestamp": now.isoformat(),
            "year": now.year,
            "month": now.month,
            "day": now.day,
        }
    except Exception as e:
        print(f"[TIME] Error: {e}")
        return {}


def get_time_in_timezone(timezone_str):
    """Get current time in specific timezone"""
    try:
        tz = pytz.timezone(timezone_str)
        now = datetime.now(tz)
        return {
            "time": now.strftime("%I:%M %p"),
            "date": now.strftime("%A, %B %d, %Y"),
            "timezone": timezone_str,
        }
    except Exception as e:
        print(f"[TIMEZONE] Error: {e}")
        return get_current_time()


def format_location_string(location_dict):
    """Format location dictionary to string"""
    if isinstance(location_dict, dict):
        return f"{location_dict.get('city', 'Unknown')}, {location_dict.get('country', 'Unknown')}"
    return str(location_dict)


if __name__ == "__main__":
    print("Testing geolocation and time module:\n")
    
    location = get_user_location()
    print(f"Location: {format_location_string(location)}")
    
    time_info = get_current_time()
    print(f"Time: {time_info.get('time')}")
    print(f"Date: {time_info.get('date')}")
