#!/usr/bin/env python3
"""
Test and fix audio generation issues
"""
import asyncio
import sys
import os
import tempfile
from pathlib import Path

# Add current directory to path
sys.path.insert(0, '.')

async def test_audio_generation_step_by_step():
    """Test each step of audio generation to find the issue"""
    print("🔧 Diagnosing Audio Generation Issues")
    print("=" * 45)
    
    try:
        # Step 1: Test gTTS directly
        print("1. Testing gTTS directly...")
        from gtts import gTTS
        
        test_text = "This is a test of the audio generation system."
        tts = gTTS(text=test_text, lang='en', slow=True)
        
        # Create temp file
        temp_file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
        temp_path = temp_file.name
        temp_file.close()
        
        tts.save(temp_path)
        print(f"✅ gTTS direct test successful: {temp_path}")
        print(f"   File size: {Path(temp_path).stat().st_size} bytes")
        
        # Step 2: Test audio service
        print("\n2. Testing audio service...")
        from app.audio_service import audio_service
        
        audio_file_path = await audio_service.text_to_speech_file(
            test_text,
            output_format="mp3",
            use_cache=True
        )
        
        if audio_file_path:
            print(f"✅ Audio service test successful: {audio_file_path}")
            if Path(audio_file_path).exists():
                size = Path(audio_file_path).stat().st_size
                print(f"   File exists, size: {size} bytes")
            else:
                print("❌ File path returned but file doesn't exist")
        else:
            print("❌ Audio service returned None")
            
        # Step 3: Test metadata generation
        print("\n3. Testing metadata generation...")
        metadata = audio_service.get_audio_metadata(test_text)
        print(f"✅ Metadata: {metadata}")
        
        # Step 4: Test the API endpoint logic
        print("\n4. Testing API endpoint logic...")
        
        # Simulate what the endpoint does
        story_text = "Once upon a time, there was a gentle cat who loved peaceful naps."
        
        if not story_text:
            print("❌ Story text validation failed")
            return False
            
        if len(story_text) < 10:
            print("❌ Story text too short")
            return False
            
        if len(story_text) > 10000:
            print("❌ Story text too long")
            return False
            
        print("✅ Validation passed")
        
        # Generate audio
        api_audio_file = await audio_service.text_to_speech_file(
            story_text, 
            output_format="mp3",
            use_cache=True
        )
        
        if not api_audio_file:
            print("❌ API-style audio generation failed")
            return False
            
        print(f"✅ API-style generation successful: {api_audio_file}")
        
        # Get metadata
        api_metadata = audio_service.get_audio_metadata(story_text)
        
        # Extract filename
        if '/' in api_audio_file:
            audio_filename = api_audio_file.split('/')[-1].replace('.mp3', '')
        else:
            audio_filename = api_audio_file.split('\\')[-1].replace('.mp3', '')
            
        print(f"✅ Audio filename: {audio_filename}")
        
        # Simulate API response
        response = {
            "success": True,
            "audio_id": audio_filename,
            "metadata": api_metadata,
            "message": "Audio generated successfully"
        }
        
        print(f"✅ API response: {response}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in step-by-step test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_endpoint_directly():
    """Test the actual API endpoint"""
    print("\n🌐 Testing API Endpoint Directly")
    print("=" * 35)
    
    try:
        import requests
        
        # Test if server is running
        try:
            health_response = requests.get("http://localhost:8000/audio/status", timeout=5)
            print(f"Health check: {health_response.status_code}")
            if health_response.status_code == 200:
                print("✅ Server is responding")
            else:
                print("⚠️ Server responding but with issues")
        except requests.exceptions.ConnectionError:
            print("❌ Server not reachable - is it running?")
            return False
        
        # Test audio generation endpoint
        payload = {
            "text": "This is a test story for audio generation."
        }
        
        response = requests.post(
            "http://localhost:8000/audio/generate",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Audio generation status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Audio generation endpoint working!")
            print(f"   Audio ID: {data.get('audio_id')}")
            print(f"   Metadata: {data.get('metadata')}")
            
            # Test accessing the audio file
            audio_id = data.get('audio_id')
            if audio_id:
                audio_url = f"http://localhost:8000/audio/{audio_id}"
                audio_response = requests.head(audio_url, timeout=10)
                print(f"Audio file access: {audio_response.status_code}")
                
                if audio_response.status_code == 200:
                    print("✅ Audio file accessible")
                else:
                    print("❌ Audio file not accessible")
            
            return True
        else:
            print(f"❌ Audio generation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Endpoint test error: {str(e)}")
        return False

if __name__ == "__main__":
    async def main():
        print("🔧 Audio Generation Diagnosis & Fix")
        print("=" * 38)
        
        # Test step by step
        step_by_step_ok = await test_audio_generation_step_by_step()
        
        if step_by_step_ok:
            print("\n✅ Step-by-step tests passed!")
            
            # Test actual endpoint
            endpoint_ok = await test_endpoint_directly()
            
            if endpoint_ok:
                print("\n🎉 All tests passed! Audio generation should work.")
                print("\n💡 If frontend still can't play audio, check:")
                print("   1. CORS headers in browser dev tools")
                print("   2. Audio URL in frontend (should be http://localhost:8000/audio/{id})")
                print("   3. Network requests in browser dev tools")
            else:
                print("\n❌ Endpoint test failed - server issues")
        else:
            print("\n❌ Basic audio generation failed")
            print("💡 Check gTTS installation and internet connection")
    
    asyncio.run(main())