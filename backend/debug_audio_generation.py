#!/usr/bin/env python3
"""
Test script to debug audio generation issues
"""
import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_audio_generation():
    """Test the audio generation endpoint functionality"""
    print("🐛 Debugging Audio Generation Issues")
    print("=" * 50)
    
    try:
        # Test 1: Check audio service import
        print("1. Testing audio service import...")
        from app.audio_service import audio_service
        print("✅ Audio service imported successfully")
        
        # Test 2: Check audio service status
        print("\n2. Checking audio service status...")
        from app.audio_service import TTS_AVAILABLE, PYTTSX3_AVAILABLE, GTTS_AVAILABLE
        print(f"   TTS engines available: {TTS_AVAILABLE}")
        print(f"   pyttsx3 available: {PYTTSX3_AVAILABLE}")
        print(f"   gTTS available: {GTTS_AVAILABLE}")
        print(f"   Settings: {audio_service.settings}")
        
        # Test 3: Test text-to-speech functionality
        print("\n3. Testing text-to-speech generation...")
        test_text = "Once upon a time, there was a gentle cat who loved to sleep."
        
        try:
            audio_file_path = await audio_service.text_to_speech_file(
                test_text, 
                output_format="mp3",
                use_cache=True
            )
            
            if audio_file_path:
                print(f"✅ Audio file generated: {audio_file_path}")
                
                # Test metadata
                metadata = audio_service.get_audio_metadata(test_text)
                print(f"✅ Metadata generated: {metadata}")
                
                # Test filename extraction
                if '/' in audio_file_path:
                    audio_filename = audio_file_path.split('/')[-1].replace('.mp3', '')
                else:
                    audio_filename = audio_file_path.split('\\')[-1].replace('.mp3', '')
                print(f"✅ Audio filename: {audio_filename}")
                
            else:
                print("❌ Audio file generation returned None")
                
        except Exception as e:
            print(f"❌ Audio generation failed: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # Test 4: Check audio cache directory
        print("\n4. Checking audio cache directory...")
        from pathlib import Path
        cache_dir = Path("audio_cache")
        if cache_dir.exists():
            cache_files = list(cache_dir.glob("*.mp3"))
            print(f"✅ Cache directory exists with {len(cache_files)} files")
        else:
            print("⚠️  Cache directory doesn't exist - will be created automatically")
            
        return True
        
    except Exception as e:
        print(f"❌ Critical error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_endpoint_simulation():
    """Simulate the endpoint request processing"""
    print("\n🔍 Simulating API Endpoint Processing")
    print("=" * 40)
    
    try:
        # Simulate request body
        story_text = "Once upon a time in a peaceful forest, there lived a wise old owl who helped other animals find restful sleep."
        
        print(f"📝 Story text length: {len(story_text)} characters")
        
        # Validation checks
        if not story_text:
            print("❌ Validation failed: Story text is required")
            return False
            
        if len(story_text) < 10:
            print("❌ Validation failed: Story text too short")
            return False
            
        if len(story_text) > 10000:
            print("❌ Validation failed: Story text too long")
            return False
            
        print("✅ All validation checks passed")
        
        # Test audio generation
        from app.audio_service import audio_service
        
        audio_file_path = await audio_service.text_to_speech_file(
            story_text, 
            output_format="mp3",
            use_cache=True
        )
        
        if not audio_file_path:
            print("❌ Failed to generate audio - got None")
            return False
            
        # Get audio metadata
        audio_metadata = audio_service.get_audio_metadata(story_text)
        
        # Extract filename
        if '/' in audio_file_path:
            audio_filename = audio_file_path.split('/')[-1].replace('.mp3', '')
        else:
            audio_filename = audio_file_path.split('\\')[-1].replace('.mp3', '')
        
        # Simulate successful response
        response = {
            "success": True,
            "audio_id": audio_filename,
            "metadata": audio_metadata,
            "message": "Audio generated successfully"
        }
        
        print("✅ Endpoint simulation successful!")
        print(f"   Response: {response}")
        return True
        
    except Exception as e:
        print(f"❌ Endpoint simulation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    async def main():
        print("🚀 Starting Audio Generation Debug Session\n")
        
        # Test basic functionality
        basic_test = await test_audio_generation()
        
        if basic_test:
            # Test endpoint simulation
            endpoint_test = await test_endpoint_simulation()
            
            if endpoint_test:
                print("\n🎉 All tests passed! Audio generation should work.")
                print("💡 If you're still getting errors, please share the specific error message.")
            else:
                print("\n❌ Endpoint simulation failed - check the error details above.")
        else:
            print("\n❌ Basic audio functionality failed - check TTS library installation.")
    
    asyncio.run(main())