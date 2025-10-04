#!/usr/bin/env python3
"""
Test audio file serving from the backend
"""
import requests
import json

def test_audio_serving():
    """Test audio file serving endpoint"""
    print("🎵 Testing Audio File Serving")
    print("=" * 35)
    
    # First, generate an audio file
    print("1. Creating audio file...")
    story_text = "Once upon a time, there was a gentle cat who loved to nap in the sunshine."
    
    try:
        # Generate audio
        response = requests.post(
            "http://localhost:8000/audio/generate",
            json={"text": story_text},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to generate audio: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
        data = response.json()
        audio_id = data.get('audio_id')
        print(f"✅ Audio generated: {audio_id}")
        
        # Now test serving the audio file
        print("\n2. Testing audio file serving...")
        audio_url = f"http://localhost:8000/audio/{audio_id}"
        
        # Test with HEAD request first
        head_response = requests.head(audio_url, timeout=10)
        print(f"   HEAD request: {head_response.status_code}")
        
        if head_response.status_code == 200:
            print("✅ Audio file accessible")
            print(f"   Content-Type: {head_response.headers.get('content-type')}")
            print(f"   Content-Length: {head_response.headers.get('content-length')} bytes")
            
            # Test actual GET request
            get_response = requests.get(audio_url, timeout=10)
            print(f"   GET request: {get_response.status_code}")
            
            if get_response.status_code == 200:
                print("✅ Audio file download successful")
                print(f"   Downloaded {len(get_response.content)} bytes")
                return True
            else:
                print(f"❌ GET request failed: {get_response.status_code}")
                return False
        else:
            print(f"❌ HEAD request failed: {head_response.status_code}")
            print(f"   Response: {head_response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - server not running")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_browser_access():
    """Test browser-style access patterns"""
    print("\n🌐 Testing Browser-Style Access")
    print("=" * 32)
    
    # Test OPTIONS request (CORS preflight)
    try:
        # First generate a test audio file
        response = requests.post(
            "http://localhost:8000/audio/generate",
            json={"text": "Hello world"},
            timeout=10
        )
        
        if response.status_code == 200:
            audio_id = response.json().get('audio_id')
            audio_url = f"http://localhost:8000/audio/{audio_id}"
            
            # Test OPTIONS request
            options_response = requests.options(audio_url)
            print(f"OPTIONS request: {options_response.status_code}")
            
            if options_response.status_code == 200:
                print("✅ CORS preflight successful")
                
                # Test with browser-like headers
                headers = {
                    'Origin': 'http://localhost:5173',
                    'Referer': 'http://localhost:5173/',
                    'User-Agent': 'Mozilla/5.0 (Test Browser)'
                }
                
                browser_response = requests.get(audio_url, headers=headers)
                print(f"Browser-style GET: {browser_response.status_code}")
                
                if browser_response.status_code == 200:
                    print("✅ Browser-style access successful")
                    return True
                else:
                    print(f"❌ Browser-style access failed: {browser_response.status_code}")
                    return False
            else:
                print(f"❌ CORS preflight failed: {options_response.status_code}")
                return False
        else:
            print("❌ Could not generate test audio")
            return False
            
    except Exception as e:
        print(f"❌ Browser access test error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🎵 Audio Serving Test Suite\n")
    
    # Test basic audio serving
    basic_test = test_audio_serving()
    
    if basic_test:
        # Test browser-style access
        browser_test = test_browser_access()
        
        if browser_test:
            print("\n🎉 All audio serving tests passed!")
            print("✅ Frontend should be able to play audio files")
            print("\n💡 Next steps:")
            print("   1. Start your frontend: npm run dev")
            print("   2. Test in browser: ask for a bedtime story")
            print("   3. Click 'Generate Audio' button")
            print("   4. Audio player should work!")
        else:
            print("\n⚠️  Browser-style access has issues")
            print("   Frontend might still have trouble playing audio")
    else:
        print("\n❌ Basic audio serving failed")
        print("   Check if server is running on port 8000")