#!/usr/bin/env python3
"""
Test Instagram Reels Upload - One clip
"""
from instagram_clips import create_instagram_clips_from_youtube

print("="*60)
print("📱 INSTAGRAM REELS UPLOADER - TEST")
print("="*60)

# Example YouTube video URL - a short motivational clip
test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

print(f"\n🎬 Video URL: {test_url}")
print("⏱️  Number of clips: 1")
print("\nStarting upload...\n")

try:
    results = create_instagram_clips_from_youtube(test_url, num_clips=1)
    
    if results:
        print(f"\n✅ SUCCESS! Uploaded {len(results)} Instagram Reels!")
        for i, clip_file in enumerate(results, 1):
            print(f"   Reel {i}: {clip_file}")
    else:
        print("\n❌ Failed to upload. Check credentials and internet connection.")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
