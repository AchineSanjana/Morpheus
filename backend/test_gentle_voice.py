#!/usr/bin/env python3
"""
Test script for the gentle voice improvements
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.audio_service import audio_service

async def test_gentle_voice():
    """Test the gentle voice improvements"""
    
    print("🎵 Testing Gentle Voice Improvements for Morpheus Sleep App")
    print("=" * 60)
    
    # Test story text (short sample)
    test_story = """
    Once upon a time, in a peaceful meadow where lavender swayed gently in the evening breeze, 
    a small cottage nestled under ancient oak trees. The windows glowed with warm, golden light, 
    and inside, a cozy fireplace crackled softly. As the stars began to twinkle overhead, 
    all the woodland creatures settled in for a restful night's sleep.
    """
    
    print("📝 Test Story Text:")
    print(f"'{test_story.strip()}'")
    print()
    
    # Show current audio settings
    print("🎛️ Current Audio Settings:")
    for key, value in audio_service.settings.items():
        print(f"  {key}: {value}")
    print()
    
    # Test text preprocessing
    print("🔄 Testing Text Preprocessing for Gentle Speech:")
    processed_text = audio_service._preprocess_text_for_gentle_speech(test_story)
    print("Original vs Processed:")
    print(f"Original: {repr(test_story[:100])}...")
    print(f"Processed: {repr(processed_text[:100])}...")
    print()
    
    # Get audio metadata
    print("📊 Audio Metadata:")
    metadata = audio_service.get_audio_metadata(test_story)
    for key, value in metadata.items():
        if isinstance(value, dict):
            print(f"  {key}:")
            for sub_key, sub_value in value.items():
                print(f"    {sub_key}: {sub_value}")
        else:
            print(f"  {key}: {value}")
    print()
    
    # Test audio generation
    print("🎙️ Generating Test Audio...")
    try:
        audio_file = await audio_service.text_to_speech_file(
            test_story, 
            output_format="mp3",
            use_cache=False  # Don't use cache for testing
        )
        
        if audio_file and os.path.exists(audio_file):
            file_size = os.path.getsize(audio_file)
            print(f"✅ Audio generated successfully!")
            print(f"   File: {audio_file}")
            print(f"   Size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
            
            # Check if it's in the audio cache
            cache_dir = Path("audio_cache")
            if cache_dir.exists():
                cache_files = list(cache_dir.glob("*.mp3"))
                print(f"   Audio cache contains {len(cache_files)} files")
            
            print("\n🎧 You can now test the audio file:")
            print(f"   Play: {audio_file}")
            print("   Listen for:")
            print("   • Slower, more relaxed speech pace")
            print("   • Gentle pauses between sentences")
            print("   • Softer, more soothing voice tone")
            print("   • Natural breathing points")
            print("   • Smooth fade in/out effects")
            
        else:
            print("❌ Failed to generate audio file")
            
    except Exception as e:
        print(f"❌ Error generating audio: {e}")
    
    print("\n" + "=" * 60)
    print("✨ Gentle Voice Test Complete!")
    print("The voice should now be much more human-like and soothing for sleep.")

if __name__ == "__main__":
    asyncio.run(test_gentle_voice())