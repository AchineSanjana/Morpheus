import os
from dotenv import load_dotenv   # <- add
load_dotenv()                    # <- add

from supabase import create_client, Client
import httpx

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE = os.getenv("SUPABASE_SERVICE_ROLE", "")

# backend uses service role (server only). if empty, it will fall back to anon
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE or SUPABASE_ANON_KEY)

async def get_current_user(access_token: str | None):
    """Verify Supabase JWT (returns user dict or None)."""
    if not access_token:
        return None
    headers = {"Authorization": f"Bearer {access_token}", "apikey": SUPABASE_ANON_KEY}
    url = f"{SUPABASE_URL}/auth/v1/user"
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url, headers=headers)
        if r.status_code == 200:
            return r.json()
        return None
