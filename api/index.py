"""
Vercel Python Function entrypoint exposing the FastAPI app at /api/*.

This adjusts sys.path so we can import the backend package and then
re-exports FastAPI's ASGI app as `app` for Vercel to detect.
"""
import os
import sys
from pathlib import Path

# Add the backend directory to Python path so `from app.main import app` works
ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Optional: signal we're running on Vercel
os.environ.setdefault("VERCEL", "1")

# Import the FastAPI app from the backend
from app.main import app  # noqa: E402  (import after path tweaks)
