#!/usr/bin/env python3
"""
Test client for the audio generation endpoint
"""
import requests
import json

def test_audio_endpoint():
    """Test the /audio/generate endpoint"""
    print("🌐 Testing Audio Generation API Endpoint")
    print("=" * 45)
    
    # Test data
    story_text = "Once upon a time, in a peaceful garden, there lived a gentle butterfly who helped flowers bloom under the moonlight."
    
    payload = {
        "text": story_text
    }
    
    print(f"📝 Story text: {story_text[:50]}...")
    print(f"🌐 Endpoint: http://localhost:8000/audio/generate")
    
    try:
        response = requests.post(
            "http://localhost:8000/audio/generate",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success! Audio generated")
            print(f"   Audio ID: {data.get('audio_id')}")
            print(f"   Duration: {data.get('metadata', {}).get('estimated_duration_minutes')} minutes")
            print(f"   Word Count: {data.get('metadata', {}).get('word_count')} words")
            
            # Test that we can access the audio file
            audio_id = data.get('audio_id')
            if audio_id:
                audio_url = f"http://localhost:8000/audio/{audio_id}"
                print(f"🎵 Audio URL: {audio_url}")
                
                # Try to access the audio file
                audio_response = requests.head(audio_url)
                if audio_response.status_code == 200:
                    print("✅ Audio file is accessible")
                else:
                    print(f"⚠️  Audio file status: {audio_response.status_code}")
            
            return True
            
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - is the server running?")
        print("💡 Start server with: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        return False
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def show_frontend_instructions():
    """Show instructions for testing from frontend"""
    print("\n🖥️  Frontend Testing Instructions:")
    print("=" * 35)
    print("1. Make sure backend server is running:")
    print("   cd backend")
    print("   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    print()
    print("2. Start frontend (in another terminal):")
    print("   cd frontend")
    print("   npm run dev")
    print()
    print("3. Test the workflow:")
    print("   - Go to http://localhost:5173")
    print("   - Sign in to your account")
    print("   - Send: 'Tell me a bedtime story'")
    print("   - Wait for story text to appear")
    print("   - Click: '🎵 Generate Audio' button")
    print("   - Audio player should appear with controls")
    print()
    print("4. Expected behavior:")
    print("   ✅ Story appears immediately (no waiting)")
    print("   ✅ Generate Audio button shows up")
    print("   ✅ Clicking button shows loading spinner")
    print("   ✅ Audio player appears after generation")
    print("   ✅ You can play/pause and see progress")

if __name__ == "__main__":
    print("🚀 Audio Generation API Test\n")
    
    success = test_audio_endpoint()
    
    if success:
        print("\n🎉 API endpoint is working!")
        print("✅ Your audio-on-demand feature is ready!")
    else:
        print("\n💡 Server needs to be started first.")
    
    show_frontend_instructions()