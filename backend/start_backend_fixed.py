#!/usr/bin/env python3
"""
Simple server script that stays running
"""
import sys
import os
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
os.environ['PYTHONPATH'] = str(current_dir)

if __name__ == "__main__":
    print("🚀 Starting Morpheus Backend Server (Fixed)")
    print("=" * 45)
    
    try:
        from app.main import app
        import uvicorn
        
        print("✅ FastAPI app loaded successfully")
        print("🌐 Starting server on http://localhost:8001")
        print("📡 CORS enabled for frontend")
        print("🎵 Audio generation endpoints available")
        print("🛑 Press Ctrl+C to stop")
        print("-" * 45)
        
        # Start the server without reload to prevent issues
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8001,
            reload=False,
            log_level="info"
        )
        
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")