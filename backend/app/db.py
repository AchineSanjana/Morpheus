from dotenv import load_dotenv
load_dotenv()
# app/db.py
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
import httpx
from supabase import create_client, Client
from starlette.concurrency import run_in_threadpool

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE = os.getenv("SUPABASE_SERVICE_ROLE", "")

if not SUPABASE_URL or not (SUPABASE_ANON_KEY or SUPABASE_SERVICE_ROLE):
    raise RuntimeError("Missing Supabase config in .env (SUPABASE_URL / keys)")

# Server uses service role if available; otherwise anon key (OK for local dev)
supabase: Client = create_client(
    SUPABASE_URL, SUPABASE_SERVICE_ROLE or SUPABASE_ANON_KEY
)

# ---------- Auth ----------

async def get_current_user(access_token: Optional[str]):
    """Verify Supabase JWT and return the user dict, or None."""
    if not access_token:
        return None
    headers = {"Authorization": f"Bearer {access_token}", "apikey": SUPABASE_ANON_KEY}
    url = f"{SUPABASE_URL}/auth/v1/user"
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url, headers=headers)
        if r.status_code == 200:
            return r.json()
        return None

# ---------- Sleep logs ----------

SLEEP_LOGS_TABLE = "sleep_logs"  # <-- change if you named it differently

def _iso(dt: datetime) -> str:
    """to ISO string without microseconds (Supabase friendly)."""
    return dt.replace(microsecond=0).isoformat()

def _parse_dt(v: Any) -> Optional[datetime]:
    if isinstance(v, datetime):
        return v
    if isinstance(v, str):
        try:
            return datetime.fromisoformat(v)
        except Exception:
            return None
    return None

async def insert_sleep_log(user_id: str, payload: Dict[str, Any]) -> None:
    """
    Insert a sleep log row. Expects keys like:
      date (YYYY-MM-DD), bedtime (ISO), wake_time (ISO),
      awakenings (int), caffeine_after3pm (bool), alcohol (bool),
      screen_time_min (int), notes (str)
    """
    row = dict(payload)
    row["user_id"] = user_id

    # (Optional) normalize datetimes if they came in as datetime objects
    if "bedtime" in row and isinstance(row["bedtime"], datetime):
        row["bedtime"] = _iso(row["bedtime"])
    if "wake_time" in row and isinstance(row["wake_time"], datetime):
        row["wake_time"] = _iso(row["wake_time"])

    # NOTE: supabase-py is sync; calling in async is okay for a small project
    await run_in_threadpool(supabase.table(SLEEP_LOGS_TABLE).insert(row).execute)

async def fetch_recent_logs(user_id: str, days: int = 7) -> List[Dict[str, Any]]:
    """
    Get the last N days of logs (ascending by date).
    Computes a convenience 'duration_h' if bedtime & wake_time are present.
    """
    since = (datetime.utcnow() - timedelta(days=days)).date().isoformat()

    def _fetch():
        return supabase.table(SLEEP_LOGS_TABLE) \
            .select("*") \
            .eq("user_id", user_id) \
            .gte("date", since) \
            .order("date", desc=False) \
            .execute()

    resp = await run_in_threadpool(_fetch)

    data: List[Dict[str, Any]] = resp.data or []

    for row in data:
        bt = _parse_dt(row.get("bedtime"))
        wt = _parse_dt(row.get("wake_time"))
        if bt and wt:
            row["duration_h"] = round((wt - bt).total_seconds() / 3600.0, 2)
        else:
            row["duration_h"] = None
    return data
