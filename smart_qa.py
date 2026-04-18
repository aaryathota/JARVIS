"""
🧠 Smart Q&A System - Fetch, summarize, and combine information from multiple sources
"""

import requests
import json
import time
from datetime import datetime
import os
from threading import Thread

# Real-time API configurations
WEATHER_API = "https://api.open-meteo.com/v1/forecast"
NEWS_API_URL = "https://newsapi.org/v2/everything"
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")  # Set via environment
REQUEST_TIMEOUT = 3  # seconds

def fetch_and_summarize_articles(query, max_articles=3):
    """
    Fetch articles from multiple sources and provide summaries
    
    Args:
        query: User's question/search query
        max_articles: Number of articles to fetch
    
    Returns:
        List of dicts with title, summary, source, url
    """
    try:
        articles = []
        sources_tried = 0
        
        # Try to fetch from NewsAPI with timeout
        if NEWSAPI_KEY:
            try:
                response = requests.get(
                    NEWS_API_URL,
                    params={
                        "q": query,
                        "sortBy": "relevancy",
                        "language": "en",
                        "pageSize": max_articles,
                        "apiKey": NEWSAPI_KEY
                    },
                    timeout=REQUEST_TIMEOUT
                )
                
                if response.status_code == 200:
                    news_data = response.json()
                    for article in news_data.get("articles", [])[:max_articles]:
                        articles.append({
                            "title": article.get("title", ""),
                            "summary": article.get("description", "")[:200],
                            "source": article.get("source", {}).get("name", "NewsAPI"),
                            "url": article.get("url", ""),
                            "published": article.get("publishedAt", "")
                        })
                    sources_tried += 1
            except requests.exceptions.Timeout:
                print(f"[QA] NewsAPI timeout (>{REQUEST_TIMEOUT}s)")
            except requests.exceptions.ConnectionError:
                print(f"[QA] NewsAPI connection error")
            except Exception as e:
                print(f"[QA] NewsAPI error: {type(e).__name__}: {str(e)[:50]}")
        
        # Try Wikipedia API with timeout
        try:
            wiki_query = query.replace(" ", "_")
            wiki_response = requests.get(
                f"https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "titles": wiki_query,
                    "prop": "extracts",
                    "explaintext": True,
                    "format": "json",
                    "exintro": True,
                },
                timeout=REQUEST_TIMEOUT
            )
            
            if wiki_response.status_code == 200:
                wiki_data = wiki_response.json()
                pages = wiki_data.get("query", {}).get("pages", {})
                
                for page_id, page_data in pages.items():
                    if page_id != "-1":  # -1 means page not found
                        extract = page_data.get("extract", "")
                        if extract:
                            articles.append({
                                "title": page_data.get("title", "Wikipedia Page"),
                                "summary": extract[:300],
                                "source": "Wikipedia",
                                "url": f"https://en.wikipedia.org/wiki/{page_data.get('title', '')}",
                                "published": datetime.now().isoformat()
                            })
                sources_tried += 1
        except requests.exceptions.Timeout:
            print(f"[QA] Wikipedia timeout (>{REQUEST_TIMEOUT}s)")
        except requests.exceptions.ConnectionError:
            print(f"[QA] Wikipedia connection error")
        except Exception as e:
            print(f"[QA] Wikipedia error: {type(e).__name__}: {str(e)[:50]}")
        
        # Return collected articles
        print(f"[QA] Fetched {len(articles)} articles from {sources_tried} sources")
        return articles[:max_articles]
    
    except Exception as e:
        print(f"[QA] Error fetching articles: {type(e).__name__}: {str(e)[:50]}")
        return []


def get_real_time_data(query_type):
    """
    Get real-time data based on query type
    
    Args:
        query_type: Type of data (weather, news, stocks, etc.)
    
    Returns:
        Relevant real-time data summary
    """
    try:
        query_lower = query_type.lower()
        
        # Weather queries
        if any(word in query_lower for word in ["weather", "temperature", "forecast", "rain", "snow"]):
            return get_weather_data()
        
        # News queries
        if any(word in query_lower for word in ["news", "latest", "breaking", "trending", "today"]):
            return get_trending_news()
        
        # Stock queries
        if any(word in query_lower for word in ["stock", "bitcoin", "crypto", "price", "market"]):
            return get_market_data(query_type)
        
        return None
    
    except Exception as e:
        print(f"[QA] Error getting real-time data: {e}")
        return None


def get_weather_data():
    """Fetch current weather data"""
    try:
        # Get user's actual location
        try:
            from geolocation import get_user_location
            location_data = get_user_location()
            latitude = location_data.get('latitude', 40.7128)
            longitude = location_data.get('longitude', -74.0060)
        except:
            # Fallback to New York if geolocation fails
            latitude = 40.7128
            longitude = -74.0060
        
        # Using Open-Meteo (free, no API key needed)
        response = requests.get(
            WEATHER_API,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
                "temperature_unit": "fahrenheit"
            },
            timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            current = data.get("current", {})
            
            weather_text = f"Temperature: {current.get('temperature_2m')}°F, "
            weather_text += f"Humidity: {current.get('relative_humidity_2m')}%, "
            weather_text += f"Wind Speed: {current.get('wind_speed_10m')} mph"
            
            return weather_text
        
        return None
    except requests.exceptions.Timeout:
        print(f"[QA] Weather API timeout")
    except Exception as e:
        print(f"[QA] Weather fetch failed: {type(e).__name__}")
        return None


def get_trending_news():
    """Fetch trending news headlines"""
    try:
        if not NEWSAPI_KEY:
            return None
        
        response = requests.get(
            "https://newsapi.org/v2/top-headlines",
            params={
                "country": "us",
                "pageSize": 3,
                "apiKey": NEWSAPI_KEY
            },
            timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            headlines = []
            
            for article in data.get("articles", [])[:3]:
                headlines.append(f"• {article.get('title', '')}")
            
            return "Top Headlines:\n" + "\n".join(headlines)
        
        return None
    except requests.exceptions.Timeout:
        print(f"[QA] News API timeout")
    except Exception as e:
        print(f"[QA] News fetch failed: {type(e).__name__}")
        return None


def get_market_data(query):
    """Fetch market/crypto data (basic implementation)"""
    try:
        # Using free crypto API
        if "bitcoin" in query.lower() or "btc" in query.lower():
            response = requests.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={"ids": "bitcoin", "vs_currencies": "usd", "include_market_cap": "true"},
                timeout=REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                btc = data.get("bitcoin", {})
                return f"Bitcoin: ${btc.get('usd', 'N/A')} (Market Cap: ${btc.get('usd_market_cap', 'N/A')})"
        
        return None
    
    except requests.exceptions.Timeout:
        print(f"[QA] Crypto API timeout")
    except Exception as e:
        print(f"[QA] Market data fetch failed: {type(e).__name__}")
        return None


def compile_answer(query, articles, real_time_data=None):
    """
    Compile comprehensive answer from multiple sources
    
    Args:
        query: Original user query
        articles: List of fetched articles
        real_time_data: Real-time data summary
    
    Returns:
        Comprehensive answer string
    """
    try:
        answer = f"Based on multiple sources, here's what I found about '{query}':\n\n"
        
        # Add real-time data if available
        if real_time_data:
            answer += f"📊 Real-time Information:\n{real_time_data}\n\n"
        
        # Add article summaries
        if articles:
            answer += "📰 Key Information:\n"
            for i, article in enumerate(articles, 1):
                answer += f"\n{i}. {article.get('title', '')}\n"
                answer += f"   Source: {article.get('source', 'Unknown')}\n"
                if article.get('summary'):
                    answer += f"   Summary: {article.get('summary', '')}\n"
        
        return answer
    
    except Exception as e:
        print(f"[QA] Error compiling answer: {e}")
        return ""


def smart_answer_question(query):
    """
    Main function to provide smart answers to questions
    
    Args:
        query: User's question
    
    Returns:
        Comprehensive answer from multiple sources
    """
    try:
        print(f"[QA] Processing smart answer for: {query}")
        
        # Get real-time data first (faster, short timeout)
        real_time_data = get_real_time_data(query)
        
        # Fetch articles in parallel (conceptually)
        articles = fetch_and_summarize_articles(query, max_articles=3)
        
        # Compile comprehensive answer
        answer = compile_answer(query, articles, real_time_data)
        
        if not answer or answer.strip() == "":
            answer = "I'm having trouble finding detailed information about that. Can you provide more context?"
        
        return answer
    
    except Exception as e:
        print(f"[QA] Smart answer error: {type(e).__name__}: {str(e)[:50]}")
        return ""


def is_question(text):
    """Determine if text is likely a question"""
    question_words = ["what", "how", "when", "where", "why", "who", "which", "can", "will", "is", "are", "do", "does"]
    text_lower = text.lower().strip()
    
    # Check for question words or question mark
    if text_lower.endswith("?"):
        return True
    
    if any(text_lower.startswith(qw) for qw in question_words):
        return True
    
    return False


# Test function
if __name__ == "__main__":
    test_queries = [
        "What is machine learning?",
        "Tell me about climate change",
        "What's the weather?",
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")
        answer = smart_answer_question(query)
        print(answer)
        time.sleep(1)  # Rate limit
