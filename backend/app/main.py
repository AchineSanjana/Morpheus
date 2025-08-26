import os, asyncio
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from .schemas import ChatRequest, SleepLogIn
from .db import get_current_user, supabase
from . import agents

app = FastAPI(title="Morpheus API")

origins = [os.getenv("CORS_ORIGINS", "http://localhost:5173")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True, "app": "Morpheus"}

@app.post("/sleep-log")
async def upsert_sleep_log(payload: SleepLogIn, authorization: str = Header(default="")):
    user = await get_current_user(authorization.replace("Bearer ", ""))
    if not user:
        raise HTTPException(401, "Unauthorized")
    data = {**payload.dict(), "user_id": user["id"]}
    supabase.table("sleep_logs").insert(data).execute()
    return {"ok": True}

@app.post("/chat/stream")
async def chat_stream(req: ChatRequest, authorization: str = Header(default="")):
    user = await get_current_user(authorization.replace("Bearer ", ""))
    if not user:
        raise HTTPException(401, "Unauthorized")

    text = req.message.strip()
    intent = agents.classify_intent(text)
    user_id = user["id"]

    if intent == "analytics":
        reply = agents.analytics_agent(user_id)
    elif intent == "coach":
        reply = agents.coach_agent(user_id)
    elif intent == "ir":
        reply = agents.ir_agent(text)
    else:
        reply = ("Hi! I’m your sleep coordinator. I can analyze your last 7 days, "
                 "build a 1-week plan, or explain sleep concepts. What would you like?")

    supabase.table("messages").insert([{
        "user_id": user_id, "role": "user", "agent":"coordinator", "content": text
    }, {
        "user_id": user_id, "role": "assistant", "agent": intent, "content": reply
    }]).execute()

    async def gen():
        for i in range(0, len(reply), 64):
            yield reply[i:i+64]
            await asyncio.sleep(0.02)
    return StreamingResponse(gen(), media_type="text/plain")
