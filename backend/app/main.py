from dotenv import load_dotenv
load_dotenv()  # load backend/.env before importing anything that uses env vars
# app/main.py
import os, asyncio
from datetime import datetime
from fastapi import FastAPI, Header, HTTPException, File, UploadFile
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
import uuid
from pathlib import Path

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

# ---------------------- PROFILE MANAGEMENT ----------------------

@app.get("/profile/{user_id}")
async def get_profile(user_id: str, authorization: str = Header(default="")):
    user = await get_current_user(authorization.replace("Bearer ", ""))
    if not user or user["id"] != user_id:
        raise HTTPException(401, "Unauthorized")
    
    def _fetch_or_create():
        print(f"Attempting to fetch profile for user_id: {user_id}")
        try:
            # Try to fetch existing profile
            result = supabase.table("user_profile").select("*").eq("id", user_id).single().execute()
            print(f"Profile fetch result: {result}")
            if result.data:
                print(f"Found existing profile: {result.data}")
                return result.data
            else:
                print("No profile data returned, will create new profile")
                raise Exception("No rows returned")
        except Exception as e:
            print(f"Profile fetch error: {e}")
            error_str = str(e).lower()
            if "no rows returned" in error_str or "not found" in error_str or "pgrst116" in error_str:
                # Profile doesn't exist, create one
                print("Creating new profile...")
                try:
                    # Get user email from auth user data for better defaults
                    user_email = user.get("email", "")
                    username = user_email.split("@")[0] if user_email else f"user_{user_id[:8]}"
                    print(f"Creating profile with username: {username} for email: {user_email}")
                    
                    new_profile = {
                        "id": user_id,
                        "full_name": None,
                        "username": username,
                        "avatar_url": None
                    }
                    print(f"Inserting profile: {new_profile}")
                    create_result = supabase.table("user_profile").insert(new_profile).execute()
                    print(f"Profile creation result: {create_result}")
                    
                    if create_result.data and len(create_result.data) > 0:
                        print(f"Successfully created profile: {create_result.data[0]}")
                        return create_result.data[0]
                    else:
                        print("No data returned from profile creation")
                        return new_profile
                except Exception as create_error:
                    print(f"Failed to create profile: {create_error}")
                    print(f"Create error type: {type(create_error)}")
                    raise create_error
            else:
                print(f"Non-recoverable database error: {e}")
                raise e
    
    try:
        profile = await run_in_threadpool(_fetch_or_create)
        return profile
    except Exception as e:
        error_msg = str(e)
        print(f"Profile fetch/create error: {error_msg}")
        raise HTTPException(500, f"Database error: {error_msg}")

@app.put("/profile/{user_id}")
async def update_profile(user_id: str, updates: dict, authorization: str = Header(default="")):
    user = await get_current_user(authorization.replace("Bearer ", ""))
    if not user or user["id"] != user_id:
        raise HTTPException(401, "Unauthorized")
    
    # Only allow specific fields to be updated
    allowed_fields = {"full_name", "username", "avatar_url"}
    filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}
    
    if not filtered_updates:
        raise HTTPException(400, "No valid fields to update")
    
    def _update():
        result = supabase.table("user_profile").update(filtered_updates).eq("id", user_id).execute()
        return result.data[0] if result.data else None
    
    try:
        profile = await run_in_threadpool(_update)
        return profile
    except Exception as e:
        raise HTTPException(500, f"Database error: {str(e)}")

@app.post("/profile/{user_id}")
async def create_profile(user_id: str, authorization: str = Header(default="")):
    user = await get_current_user(authorization.replace("Bearer ", ""))
    if not user or user["id"] != user_id:
        raise HTTPException(401, "Unauthorized")
    
    def _create():
        # Check if profile already exists
        try:
            existing = supabase.table("user_profile").select("*").eq("id", user_id).single().execute()
            if existing.data:
                return existing.data  # Return existing profile
        except:
            pass  # Profile doesn't exist, create it
        
        # Create new profile
        user_email = user.get("email", "")
        username = user_email.split("@")[0] if user_email else f"user_{user_id[:8]}"
        
        new_profile = {
            "id": user_id,
            "full_name": None,
            "username": username,
            "avatar_url": None
        }
        result = supabase.table("user_profile").insert(new_profile).execute()
        return result.data[0] if result.data else new_profile
    
    try:
        profile = await run_in_threadpool(_create)
        return profile
    except Exception as e:
        error_msg = str(e)
        print(f"Profile creation error: {error_msg}")
        raise HTTPException(500, f"Failed to create profile: {error_msg}")

@app.get("/debug/table-check")
async def check_table(authorization: str = Header(default="")):
    user = await get_current_user(authorization.replace("Bearer ", ""))
    if not user:
        raise HTTPException(401, "Unauthorized")
    
    def _check():
        try:
            # Try to select from user_profile table
            result = supabase.table("user_profile").select("id").limit(1).execute()
            return {"table_exists": True, "sample_data": result.data}
        except Exception as e:
            return {"table_exists": False, "error": str(e)}
    
    try:
        check_result = await run_in_threadpool(_check)
        return check_result
    except Exception as e:
        return {"table_exists": False, "error": str(e)}

@app.post("/profile/{user_id}/avatar")
async def upload_avatar(
    user_id: str,
    avatar: UploadFile = File(...),
    authorization: str = Header(default="")
):
    user = await get_current_user(authorization.replace("Bearer ", ""))
    if not user or user["id"] != user_id:
        raise HTTPException(401, "Unauthorized")
    
    # Validate file type
    if not avatar.content_type or not avatar.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image")
    
    # Validate file size (5MB max)
    file_content = await avatar.read()
    if len(file_content) > 5 * 1024 * 1024:  # 5MB
        raise HTTPException(400, "File size must be less than 5MB")
    
    # Generate unique filename
    file_extension = Path(avatar.filename or "").suffix or ".jpg"
    filename = f"{user_id}/{uuid.uuid4()}{file_extension}"
    
    def _upload():
        # Delete old avatar if exists
        try:
            # Get current avatar
            profile = supabase.table("user_profile").select("avatar_url").eq("id", user_id).single().execute()
            if profile.data and profile.data.get("avatar_url"):
                old_url = profile.data["avatar_url"]
                # Extract filename from URL to delete old file
                if "/avatars/" in old_url:
                    old_filename = old_url.split("/avatars/")[-1]
                    supabase.storage.from_("avatars").remove([old_filename])
        except:
            pass  # Ignore errors when deleting old avatar
        
        # Upload new avatar
        try:
            result = supabase.storage.from_("avatars").upload(filename, file_content)
            # The upload response doesn't have an error attribute - if it fails, it raises an exception
        except Exception as upload_error:
            raise Exception(f"Upload failed: {str(upload_error)}")
        
        # Get public URL
        public_url_data = supabase.storage.from_("avatars").get_public_url(filename)
        public_url = public_url_data.publicUrl if hasattr(public_url_data, 'publicUrl') else public_url_data
        
        # Update profile with new avatar URL
        supabase.table("user_profile").update({"avatar_url": public_url}).eq("id", user_id).execute()
        
        return public_url
    
    try:
        avatar_url = await run_in_threadpool(_upload)
        return {"avatar_url": avatar_url}
    except Exception as e:
        raise HTTPException(500, f"Upload error: {str(e)}")

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

# ---------------------- RESPONSIBLE AI ENDPOINTS ----------------------

@app.get("/responsible-ai/status")
async def get_responsible_ai_status():
    """Get the status of responsible AI features"""
    try:
        from app.responsible_ai import responsible_ai
        return {
            "enabled": True,
            "version": "1.0.0",
            "features": {
                "fairness_checks": True,
                "transparency_tracking": True,
                "ethical_data_handling": True,
                "bias_detection": True,
                "inclusive_language": True
            },
            "status": "operational"
        }
    except ImportError:
        return {
            "enabled": False,
            "error": "Responsible AI module not available"
        }

@app.post("/responsible-ai/validate")
async def validate_responsible_ai(
    payload: dict,
    authorization: str = Header(default="")
):
    """Validate content against responsible AI guidelines"""
    user = await get_current_user(authorization.replace("Bearer ", ""))
    if not user:
        raise HTTPException(401, "Unauthorized")
    
    try:
        from app.responsible_ai import responsible_ai
        
        text = payload.get("text", "")
        action_type = payload.get("action_type", "general_response")
        user_context = payload.get("user_context", {})
        data_sources = payload.get("data_sources", [])
        decision_factors = payload.get("decision_factors", {})
        
        if not text:
            raise HTTPException(400, "Text content is required")
        
        results = await responsible_ai.comprehensive_check(
            text=text,
            action_type=action_type,
            user_context=user_context,
            data_sources=data_sources,
            decision_factors=decision_factors
        )
        
        # Convert to serializable format
        serialized_results = {}
        for check_type, check_result in results.items():
            serialized_results[check_type] = {
                "passed": check_result.passed,
                "risk_level": check_result.risk_level.value if hasattr(check_result.risk_level, 'value') else str(check_result.risk_level),
                "category": check_result.category,
                "message": check_result.message,
                "suggestions": check_result.suggestions,
                "metadata": check_result.metadata or {}
            }
        
        return {
            "validation_results": serialized_results,
            "overall_passed": all(r["passed"] for r in serialized_results.values()),
            "timestamp": datetime.now().isoformat()
        }
        
    except ImportError:
        raise HTTPException(503, "Responsible AI validation service not available")
    except Exception as e:
        raise HTTPException(500, f"Validation error: {str(e)}")

@app.get("/responsible-ai/guidelines")
async def get_responsible_ai_guidelines():
    """Get responsible AI guidelines and best practices"""
    return {
        "fairness": {
            "principle": "Ensure AI responses are fair and unbiased across all user demographics",
            "guidelines": [
                "Use inclusive language that considers diverse backgrounds",
                "Avoid stereotyping based on age, gender, culture, or socioeconomic status",
                "Provide alternatives for users with different abilities",
                "Offer both free and accessible solutions alongside premium options",
                "Acknowledge individual differences in responses"
            ],
            "examples": {
                "good": "Consider gentle exercises that work within your current abilities",
                "bad": "Just do these exercises - they're easy for everyone"
            }
        },
        "transparency": {
            "principle": "Be transparent about AI decision-making and data usage",
            "guidelines": [
                "Explain how recommendations were generated",
                "Disclose what data sources were used",
                "Acknowledge AI limitations and uncertainty",
                "Clearly identify AI-generated content",
                "Mention when human professional help is recommended"
            ],
            "examples": {
                "good": "Based on your 7 nights of sleep data, I noticed your bedtime varies by 2+ hours...",
                "bad": "You should change your bedtime routine"
            }
        },
        "ethical_data_handling": {
            "principle": "Protect user privacy and handle data ethically",
            "guidelines": [
                "Minimize data collection to essential sleep-related information",
                "Protect sensitive personal information",
                "Inform users about their data rights",
                "Ensure data security and confidentiality",
                "Obtain appropriate consent for data usage"
            ],
            "examples": {
                "good": "Your sleep data is securely stored and you can delete it anytime",
                "bad": "Sharing personal medical details in responses"
            }
        }
    }

@app.get("/responsible-ai/audit-log")
async def get_responsible_ai_audit_log(
    limit: int = Query(default=50, le=200),
    authorization: str = Header(default="")
):
    """Get audit log of responsible AI checks (admin only)"""
    user = await get_current_user(authorization.replace("Bearer ", ""))
    if not user:
        raise HTTPException(401, "Unauthorized")
    
    # This would typically check for admin privileges
    # For now, we'll return a mock audit log structure
    return {
        "message": "Audit logging would be implemented with proper admin authentication",
        "structure": {
            "timestamp": "ISO datetime",
            "user_id": "User identifier",
            "agent": "Which agent was used",
            "check_results": "Responsible AI check results",
            "risk_level": "Overall risk assessment",
            "action_taken": "Any corrective actions"
        },
        "note": "Full audit logging requires additional security and storage infrastructure"
    }
