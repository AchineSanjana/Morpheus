#!/usr/bin/env python3
"""
Simple audio file test server to verify audio files work
"""
import http.server
import socketserver
import os
from pathlib import Path

def test_audio_files():
    """Test if audio files exist and are valid"""
    print("🎵 Testing Audio Files Directly")
    print("=" * 35)
    
    audio_dir = Path("audio_cache")
    if not audio_dir.exists():
        print("❌ Audio cache directory doesn't exist")
        return False
    
    audio_files = list(audio_dir.glob("*.mp3"))
    print(f"📁 Found {len(audio_files)} audio files")
    
    if not audio_files:
        print("⚠️  No audio files found")
        print("💡 Try generating audio first with: python debug_audio_generation.py")
        return False
    
    # Check file sizes
    for audio_file in audio_files[:5]:  # Show first 5
        size = audio_file.stat().st_size
        print(f"   📄 {audio_file.name}: {size} bytes")
        
        if size < 1000:  # Less than 1KB is probably an error
            print(f"      ⚠️  File seems too small")
        else:
            print(f"      ✅ File size looks good")
    
    return len(audio_files) > 0

def start_simple_server():
    """Start a simple HTTP server to test audio playback"""
    print("\n🌐 Starting Simple Test Server")
    print("=" * 32)
    
    # Change to audio_cache directory
    os.chdir("audio_cache")
    
    # Start simple HTTP server
    PORT = 8080
    Handler = http.server.SimpleHTTPRequestHandler
    
    # Add CORS headers
    class CORSRequestHandler(Handler):
        def end_headers(self):
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', '*')
            super().end_headers()
    
    print(f"🚀 Starting server on http://localhost:{PORT}")
    print("📁 Serving files from audio_cache directory")
    print("\n🧪 Test URLs:")
    
    # List some test files
    audio_files = [f for f in os.listdir('.') if f.endswith('.mp3')]
    for i, filename in enumerate(audio_files[:3]):
        print(f"   🎵 http://localhost:{PORT}/{filename}")
    
    print(f"\n💡 Test these URLs in your browser or frontend!")
    print(f"🛑 Press Ctrl+C to stop server")
    
    try:
        with socketserver.TCPServer(("", PORT), CORSRequestHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")

def create_test_html():
    """Create a simple HTML test page"""
    print("\n📄 Creating Test HTML Page")
    print("=" * 28)
    
    audio_files = [f for f in os.listdir('audio_cache') if f.endswith('.mp3')]
    
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Audio Test Page</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .audio-test { margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }
        audio { width: 100%; margin: 10px 0; }
        .success { color: green; }
        .error { color: red; }
    </style>
</head>
<body>
    <h1>🎵 Audio File Test</h1>
    <p>This page tests if the generated audio files can be played in a browser.</p>
"""
    
    for filename in audio_files[:5]:  # Test first 5 files
        html_content += f"""
    <div class="audio-test">
        <h3>📄 {filename}</h3>
        <audio controls>
            <source src="http://localhost:8080/{filename}" type="audio/mpeg">
            Your browser does not support the audio element.
        </audio>
        <p>Direct link: <a href="http://localhost:8080/{filename}" target="_blank">http://localhost:8080/{filename}</a></p>
    </div>
"""
    
    html_content += """
    <div class="audio-test">
        <h3>🧪 Frontend Test</h3>
        <p>To test with your actual frontend:</p>
        <ol>
            <li>Update AudioPlayer.tsx to use: <code>http://localhost:8080/{filename}</code></li>
            <li>Or start your backend server properly</li>
            <li>Generate audio and test playback</li>
        </ol>
    </div>
    
    <script>
        // Test audio loading
        document.querySelectorAll('audio').forEach((audio, index) => {
            audio.addEventListener('loadstart', () => console.log(`Audio ${index} loading started`));
            audio.addEventListener('canplay', () => console.log(`Audio ${index} can play`));
            audio.addEventListener('error', (e) => console.error(`Audio ${index} error:`, e));
        });
    </script>
</body>
</html>"""
    
    with open("audio_test.html", "w") as f:
        f.write(html_content)
    
    print("✅ Created audio_test.html")
    print("🌐 Open http://localhost:8080/audio_test.html after starting the server")

if __name__ == "__main__":
    print("🎵 Audio File Test & Server")
    print("=" * 25)
    
    # Test if audio files exist
    if test_audio_files():
        # Create test HTML page  
        create_test_html()
        
        print("\n🚀 Ready to start test server!")
        print("💡 This will serve audio files on port 8080")
        
        response = input("\n❓ Start simple test server? (y/n): ").strip().lower()
        if response == 'y':
            start_simple_server()
        else:
            print("🔧 Manual testing:")
            print("   1. cd audio_cache")
            print("   2. python -m http.server 8080")
            print("   3. Open http://localhost:8080/audio_test.html")
    else:
        print("❌ No audio files to test")
        print("💡 Generate some audio first with debug_audio_generation.py")