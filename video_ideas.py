"""
Video Ideas Generator - Uses Groq to generate viral video ideas
"""
from groq import Groq
import json
from datetime import datetime

# Initialize Groq client
try:
    with open("groq_key.txt", "r") as f:
        GROQ_API_KEY = f.read().strip()
except:
    GROQ_API_KEY = None

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

def generate_video_ideas(topic="viral clips", num_ideas=3, content_type="streamer"):
    """
    Generate viral video ideas using Groq
    
    Args:
        topic: Topic for video ideas (default: viral clips)
        num_ideas: Number of ideas to generate
        content_type: Type of content (streamer, tutorial, comedy, trending, etc.)
    
    Returns:
        List of video ideas with descriptions
    """
    if not client:
        print("[VIDEO IDEAS] Error: Groq client not initialized")
        return []
    
    try:
        current_date = datetime.now().strftime("%B %d, %Y")
        
        prompt = f"""You are a viral content creator expert. Generate {num_ideas} creative and viral video ideas for {content_type} content.
Today is {current_date}.

For each idea, provide:
1. Title (catchy and clickable)
2. Description (2-3 sentences about the video)
3. Duration (estimated length in minutes)
4. Hook (first 10 seconds to grab attention)
5. Tags (5 relevant hashtags)

Focus on:
- Current trending topics
- Famous streamer moments or reactions
- Short-form content that goes viral
- High engagement potential
- Creative and unique angles

Format as JSON array with these exact fields: title, description, duration, hook, tags, estimated_views"""

        message = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            max_tokens=2000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        response_text = message.choices[0].message.content
        
        # Try to parse JSON from response
        try:
            # Find JSON array in response
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']') + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                ideas = json.loads(json_str)
                print(f"[VIDEO IDEAS] Generated {len(ideas)} ideas successfully")
                return ideas
        except json.JSONDecodeError:
            # Fallback: parse the text response
            print("[VIDEO IDEAS] Response parsed (text format)")
            return [{"title": f"Idea {i+1}", "description": response_text} for i in range(num_ideas)]
        
        return []
    
    except Exception as e:
        print(f"[VIDEO IDEAS ERROR] {str(e)}")
        return []


def get_trending_video_concepts():
    """Get trending video concepts for current date"""
    try:
        prompt = """What are the top 5 trending video concepts RIGHT NOW that would go viral on YouTube Shorts/TikTok?
Be specific about what's trending today. Format as JSON array with: concept, why_trending, potential_reach"""
        
        message = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            max_tokens=1500,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        response_text = message.choices[0].message.content
        print(f"[TRENDING] Got trending concepts")
        return response_text
    
    except Exception as e:
        print(f"[TRENDING ERROR] {str(e)}")
        return None


def create_video_script(topic, duration_minutes=1):
    """Generate a video script using Groq"""
    try:
        prompt = f"""Create a viral video script for a {duration_minutes} minute video about: {topic}

Requirements:
- Hook in first 3 seconds
- Engaging dialogue/narration
- Clear calls-to-action
- Include timing cues [0:00-0:03], [0:03-0:30], etc.
- B-roll suggestions
- Music/sound effect recommendations

Format clearly with timestamps."""
        
        message = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            max_tokens=1500,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        script = message.choices[0].message.content
        print(f"[SCRIPT] Generated script for: {topic}")
        return script
    
    except Exception as e:
        print(f"[SCRIPT ERROR] {str(e)}")
        return None


if __name__ == "__main__":
    # Test video idea generation
    print("Testing video idea generation...")
    ideas = generate_video_ideas(num_ideas=3, content_type="streamer")
    for idea in ideas:
        print(f"\n✓ {idea.get('title', 'Untitled')}")
        print(f"  {idea.get('description', '')}")
