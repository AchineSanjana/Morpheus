#!/usr/bin/env python3
"""
Backend server startup script for Morpheus Sleep AI
"""
import sys
import os
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def start_backend():
    """Start the FastAPI backend server"""
    print("🚀 Starting Morpheus Backend Server")
    print("=" * 40)
    
    try:
        # Import required modules
        import uvicorn
        from app.main import app
        
        print("✅ FastAPI app loaded successfully")
        print("🌐 Starting server on http://localhost:8000")
        print("📡 CORS enabled for frontend on http://localhost:5173")
        print("🎵 Audio generation endpoints available")
        print("🛑 Press Ctrl+C to stop")
        print("-" * 40)
        
        # Start the server with proper reload configuration
        uvicorn.run(
            "app.main:app",  # Use import string for reload
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're in the backend directory")
        print("💡 Install uvicorn: pip install uvicorn")
        return False
        
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return False

if __name__ == "__main__":
    start_backend()