"""
Weather API Configuration
Get a FREE API key from: https://openweathermap.org/api (free tier available)
Sign up -> Generate API key -> Paste below
"""

# Get free API key at: https://openweathermap.org/api
WEATHER_API_KEY = ""  # Add your weather API key here

# Get free API key at: https://www.weatherapi.com/ (alternative, more generous free tier)
WEATHER_API_KEY_ALTERNATIVE = "1cb7b4972e934989a6450321261004"

# Default to OpenWeatherMap
WEATHER_API_PROVIDER = "openweathermap"  # or "weatherapi"

# User location (for weather queries) - dynamically detected
try:
    from geolocation import get_user_location, format_location_string
    _weather_location = get_user_location()
    DEFAULT_LOCATION = _weather_location.get('city', 'Your City')
except:
    DEFAULT_LOCATION = "Your City"  # Fallback to generic location
