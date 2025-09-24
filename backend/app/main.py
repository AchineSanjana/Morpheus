from dotenv import load_dotenv
load_dotenv()  # load backend/.env before importing anything that uses env vars
# app/main.py
import os, asyncio
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from .schemas import ChatRequest, SleepLogIn
from .db import get_current_user, insert_sleep_log, fetch_recent_logs, supabase

# NEW: import the split agents
from app.agents.coordinator import CoordinatorAgent
from app.agents.analyst import AnalyticsAgent
from app.agents import AgentContext

from typing import Optional, List
from fastapi import Query

app = FastAPI(title="Morpheus API")

# CORS for your Vite frontend
origins = [os.getenv("CORS_ORIGINS", "http://localhost:5173")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# instantiate agents once (cheap)
coordinator = CoordinatorAgent()
quick_analyst = AnalyticsAgent()  # used to precompute context sometimes

@app.get("/health")
def health():
    return {"ok": True, "app": "Morpheus"}

@app.post("/sleep-log")
async def upsert_sleep_log(payload: SleepLogIn, authorization: str = Header(default="")):
    user = await get_current_user(authorization.replace("Bearer ", ""))
    if not user:
        raise HTTPException(401, "Unauthorized")
    await insert_sleep_log(user["id"], payload.dict())
    return {"ok": True}

# ---------------------- CHAT ----------------------

def _is_greeting(text: str) -> bool:
    t = text.strip().lower()
    return t in {"", "hi", "hello", "hey", "hey!", "hello!", "hi!"}

async def _coordinator_reply(message: str, user: dict) -> dict:
    """
    Delegate to coordinator; optionally enrich context with quick analysis so the
    coach can personalize immediately on first turn.
    """
    ctx: AgentContext = {"user": user}
    # if the user asks for analysis/plan, preload summary for coach
    # (safe & fast: fetch 7 days once)
    try:
        analysis = await quick_analyst.handle("analyze last 7", {"user": user})
        if isinstance(analysis, dict):
            ctx["analysis"] = analysis.get("data")  # {"summary": {...}, ...}
    except Exception:
        pass

    # greeting / route handled inside CoordinatorAgent
    return await coordinator.handle(message, ctx)

@app.post("/chat/stream")
async def chat_stream(req: ChatRequest, authorization: str = Header(default="")):
    user = await get_current_user(authorization.replace("Bearer ", ""))
    if not user:
        raise HTTPException(401, "Unauthorized")

    text = (req.message or "").strip()

    # If first message or greeting, show menu-like opening from the coordinator
    if _is_greeting(text):
        text = ""  # CoordinatorAgent treats empty/hi/hello as greeting

    # Run the agent selection via coordinator
    result = await _coordinator_reply(text, user)
    reply = result.get("text", "")
    agent_name = result.get("agent", "coordinator")
    data = result.get("data", {})

    # persist conversation
    try:
        if text.strip():  # user actually typed something
            supabase.table("messages").insert([
                {
                    "user_id": user["id"],
                    "role": "user",
                    "agent": "user",
                    "content": req.message
                },
                {
                    "user_id": user["id"],
                    "role": "assistant",
                    "agent": agent_name,
                    "content": reply
                }
            ]).execute()
        else:  # greeting/empty case
            supabase.table("messages").insert({
                "user_id": user["id"],
                "role": "assistant",
                "agent": "coordinator",
                "content": reply
            }).execute()
    except Exception:
        pass

    async def gen():
        # stream in small chunks to feel chat-like
        chunk = 64
        for i in range(0, len(reply), chunk):
            yield reply[i:i+chunk]
            await asyncio.sleep(0.02)

    return StreamingResponse(gen(), media_type="text/plain")

@app.get("/messages")
async def list_messages(
    authorization: str = Header(default=""),
    limit: int = Query(200, ge=1, le=500),
    before: Optional[str] = Query(None, description="ISO timestamptz to fetch older messages"),
    after: Optional[str] = Query(None, description="ISO timestamptz to fetch newer messages"),
):
    user = await get_current_user(authorization.replace("Bearer ", ""))
    if not user:
        raise HTTPException(401, "Unauthorized")

    q = supabase.table("messages").select("*").eq("user_id", user["id"])
    if before:
        q = q.lt("created_at", before)
    if after:
        q = q.gt("created_at", after)
    # fetch newest first, then reverse to oldest→newest for UI display
    res = q.order("created_at", desc=True).limit(limit).execute()
    rows = res.data or []
    rows.sort(key=lambda r: r.get("created_at") or "")  # oldest → newest

    return {"messages": rows, "count": len(rows)}

@app.delete("/messages")
async def clear_messages(authorization: str = Header(default="")):
    user = await get_current_user(authorization.replace("Bearer ", ""))
    if not user:
        raise HTTPException(401, "Unauthorized")
    supabase.table("messages").delete().eq("user_id", user["id"]).execute()
    return {"ok": True}
