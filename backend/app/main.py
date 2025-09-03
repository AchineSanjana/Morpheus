# app/main.py
import os, asyncio
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from .schemas import ChatRequest, SleepLogIn
from .db import get_current_user, insert_sleep_log, supabase
from starlette.concurrency import run_in_threadpool

# NEW: import the split agents
from app.agents.coordinator import CoordinatorAgent
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

async def _coordinator_reply(message: str, user: dict) -> dict:
    """
    Delegate to coordinator. The coordinator is now responsible for
    all routing and context enrichment.
    """
    ctx: AgentContext = {"user": user}
    # The pre-emptive analysis has been removed.
    # The coordinator will now decide when to call the analytics agent.
    return await coordinator.handle(message, ctx)

@app.post("/chat/stream")
async def chat_stream(req: ChatRequest, authorization: str = Header(default="")):
    user = await get_current_user(authorization.replace("Bearer ", ""))
    if not user:
        raise HTTPException(401, "Unauthorized")

    text = (req.message or "").strip()

    # The _is_greeting check is removed. The coordinator handles all cases.
    # Run the agent selection via coordinator
    result = await _coordinator_reply(text, user)
    reply = result.get("text", "")
    agent_name = result.get("agent", "coordinator")
    data = result.get("data", {})

    # persist conversation
    try:
        # Simplified logic: always try to insert user message if it exists,
        # and always insert the assistant's reply.
        messages_to_insert = []
        if text:
            messages_to_insert.append({
                "user_id": user["id"],
                "role": "user",
                "agent": "user",
                "content": req.message
            })
        
        messages_to_insert.append({
            "user_id": user["id"],
            "role": "assistant",
            "agent": agent_name,
            "content": reply
        })

        def _insert_messages():
            supabase.table("messages").insert(messages_to_insert).execute()
        
        await run_in_threadpool(_insert_messages)
    except Exception as e:
        # Log the error instead of silently passing
        print(f"ERROR: Could not persist chat messages. Reason: {e}")
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

    def _fetch():
        q = supabase.table("messages").select("*").eq("user_id", user["id"])
        if before:
            q = q.lt("created_at", before)
        if after:
            q = q.gt("created_at", after)
        # fetch newest first, then reverse to oldest→newest for UI display
        return q.order("created_at", desc=True).limit(limit).execute()
    
    res = await run_in_threadpool(_fetch)
    rows = res.data or []
    rows.sort(key=lambda r: r.get("created_at") or "")  # oldest → newest

    return {"messages": rows, "count": len(rows)}

@app.delete("/messages")
async def clear_messages(authorization: str = Header(default="")):
    user = await get_current_user(authorization.replace("Bearer ", ""))
    if not user:
        raise HTTPException(401, "Unauthorized")
    
    def _delete():
        supabase.table("messages").delete().eq("user_id", user["id"]).execute()

    await run_in_threadpool(_delete)
    return {"ok": True}
