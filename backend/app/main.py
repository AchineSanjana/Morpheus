from dotenv import load_dotenv
load_dotenv()  # load backend/.env before importing anything that uses env vars
# app/main.py
import os, asyncio
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
from fastapi import FastAPI, Header, HTTPException, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from pathlib import Path
import re
from .schemas import ChatRequest, SleepLogIn
from .db import get_current_user, insert_sleep_log, supabase
from starlette.concurrency import run_in_threadpool

# NEW: import the split agents
from app.agents.coordinator import CoordinatorAgent
from app.agents import AgentContext

# Security imports
from app.security_middleware import security_middleware, add_security_headers, rate_limit_error_handler
from app.security_config import security_config

from typing import Optional, List
from fastapi import Query
import uuid
from pathlib import Path

app = FastAPI(title="Morpheus API")

# Security middleware - add before CORS
app.middleware("http")(add_security_headers)

# CORS for your Vite frontend
origins = [os.getenv("CORS_ORIGINS", "http://localhost:5173")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security exception handlers
@app.exception_handler(429)
async def rate_limit_handler(request: Request, exc: HTTPException):
    return rate_limit_error_handler(request, exc)

# instantiate agents once (cheap)
coordinator = CoordinatorAgent()

# Routers
try:
    from app.api.routers.responsible_ai import router as responsible_ai_router
    app.include_router(responsible_ai_router)
except Exception as e:
    logger.warning(f"Responsible AI router not loaded: {e}")

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
            # Try to fetch existing profile (should exist due to database trigger)
            result = supabase.table("user_profile").select("*").eq("id", user_id).single().execute()
            print(f"Profile fetch result: {result}")
            if result.data:
                print(f"Found existing profile: {result.data}")
                return result.data
            else:
                print("No profile data returned, will create as fallback")
                raise Exception("No rows returned")
        except Exception as e:
            print(f"Profile fetch error: {e}")
            error_str = str(e).lower()
            if "no rows returned" in error_str or "not found" in error_str or "pgrst116" in error_str:
                # Profile doesn't exist - this shouldn't happen with the trigger, but create as fallback
                print("Creating profile as fallback (trigger may have failed)...")
                try:
                    user_email = user.get("email", "")
                    username = user_email.split("@")[0] if user_email else f"user_{user_id[:8]}"
                    print(f"Creating fallback profile with username: {username} for email: {user_email}")
                    
                    new_profile = {
                        "id": user_id,
                        "full_name": None,
                        "username": username,
                        "avatar_url": None
                    }
                    print(f"Inserting fallback profile: {new_profile}")
                    create_result = supabase.table("user_profile").insert(new_profile).execute()
                    print(f"Fallback profile creation result: {create_result}")
                    
                    if create_result.data and len(create_result.data) > 0:
                        print(f"Successfully created fallback profile: {create_result.data[0]}")
                        return create_result.data[0]
                    else:
                        print("No data returned from fallback profile creation")
                        return new_profile
                except Exception as create_error:
                    print(f"Failed to create fallback profile: {create_error}")
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

@app.get("/debug/profile-stats")
async def profile_stats(authorization: str = Header(default="")):
    """Debug endpoint to check if automatic profile creation is working"""
    user = await get_current_user(authorization.replace("Bearer ", ""))
    if not user:
        raise HTTPException(401, "Unauthorized")
    
    def _get_stats():
        try:
            # Count total auth users
            auth_count_result = supabase.rpc('count_auth_users').execute()
            total_auth_users = auth_count_result.data if auth_count_result.data else 0
            
            # Count total profiles  
            profile_result = supabase.table("user_profile").select("id", count="exact").execute()
            total_profiles = profile_result.count if hasattr(profile_result, 'count') else len(profile_result.data or [])
            
            # Get recent profiles
            recent_profiles = supabase.table("user_profile").select("id, username, created_at").order("created_at", desc=True).limit(5).execute()
            
            # Check if trigger exists
            trigger_check = supabase.rpc('check_trigger_exists', {'trigger_name': 'on_auth_user_created'}).execute()
            trigger_exists = trigger_check.data if trigger_check.data else False
            
            return {
                "total_auth_users": total_auth_users,
                "total_profiles": total_profiles,
                "profiles_vs_users_match": total_auth_users == total_profiles,
                "recent_profiles": recent_profiles.data,
                "trigger_exists": trigger_exists,
                "automatic_creation_working": total_auth_users == total_profiles
            }
        except Exception as e:
            return {"error": str(e), "details": "Could not fetch profile statistics"}
    
    try:
        stats = await run_in_threadpool(_get_stats)
        return stats
    except Exception as e:
        return {"error": str(e)}

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

async def _coordinator_reply(message: str, user: dict, history: Optional[List[dict]] = None) -> dict:
    """
    Delegate to coordinator. The coordinator is now responsible for
    all routing and context enrichment.
    """
    ctx: AgentContext = {"user": user}
    # Enrich context with a safe display name (no nicknames)
    display_name = None
    try:
        def _fetch_display_name():
            # Prefer profile full_name, then username
            res = supabase.table("user_profile").select("full_name,username").eq("id", user["id"]).single().execute()
            data = res.data or {}
            name = (data.get("full_name") or "").strip() or (data.get("username") or "").strip()
            if name:
                return name
            # Fallback: email prefix
            email = (user.get("email") or "").strip()
            return email.split("@")[0] if email else None
        display_name = await run_in_threadpool(_fetch_display_name)
    except Exception:
        # Silent fallback
        display_name = None

    if display_name:
        ctx["display_name"] = display_name

    # Attach recent conversation history (if provided)
    if history:
        # Limit to last 20 messages to keep prompt small
        ctx["history"] = history[-20:]

    # The pre-emptive analysis has been removed.
    # The coordinator will now decide when to call the analytics agent.
    return await coordinator.handle(message, ctx)

def _generate_conversation_title(first_user_message: str) -> str:
    text = (first_user_message or "").strip()
    if not text:
        return "New conversation"
    # Simple heuristic: first 6-8 words, sentence-cased
    words = re.split(r"\s+", text)
    snippet = " ".join(words[:8])
    snippet = re.sub(r"[\r\n]+", " ", snippet)[:60]
    if snippet:
        return snippet[:1].upper() + snippet[1:]
    return "New conversation"

@app.post("/chat/stream")
async def chat_stream(request: Request, req: ChatRequest, authorization: str = Header(default="")):
    # Security validation
    await security_middleware.validate_request_security(request, req.message or "")
    
    user = await get_current_user(authorization.replace("Bearer ", ""))
    if not user:
        raise HTTPException(401, "Unauthorized")

    text = (req.message or "").strip()
    conversation_id = (req.conversation_id or "").strip() or None

    # Determine or create conversation id before generating so we can fetch history
    conversation_id = (req.conversation_id or "").strip() or None
    conv_id = conversation_id
    conv_title_created: Optional[str] = None
    if not conv_id:
        # No conversation supplied: create a brand-new one for this user
        conv_id = str(uuid.uuid4())
        conv_title_created = _generate_conversation_title(text)

        def _create_conversation():
            supabase.table("conversations").insert({
                "id": conv_id,
                "user_id": user["id"],
                "title": conv_title_created
            }).execute()
        try:
            await run_in_threadpool(_create_conversation)
        except Exception as e:
            # If creation races/existed, ignore
            logger.info(f"Conversation create ignored: {e}")
    else:
        # A conversation_id was provided. Ensure it exists and is owned by this user.
        # If missing, create it. If owned by a different user, fork a new conversation for this user.
        def _ensure_conversation():
            try:
                res = supabase.table("conversations").select("id,user_id").eq("id", conv_id).single().execute()
                data = getattr(res, "data", None) or res
            except Exception:
                data = None

            # If the conversation doesn't exist, create it with a derived title
            if not data:
                title = _generate_conversation_title(text)
                supabase.table("conversations").insert({
                    "id": conv_id,
                    "user_id": user["id"],
                    "title": title or "Recovered conversation"
                }).execute()
                return {"conv_id": conv_id, "title": title}

            # If it exists but belongs to another user, create a new conversation for this user
            if data.get("user_id") != user["id"]:
                new_id = str(uuid.uuid4())
                title = _generate_conversation_title(text)
                supabase.table("conversations").insert({
                    "id": new_id,
                    "user_id": user["id"],
                    "title": title or "New conversation"
                }).execute()
                return {"conv_id": new_id, "title": title}

            # Owned by current user and exists: nothing to do
            return {"conv_id": conv_id, "title": None}

        try:
            ensured = await run_in_threadpool(_ensure_conversation)
            if ensured and ensured.get("conv_id") and ensured.get("conv_id") != conv_id:
                conv_id = ensured["conv_id"]
            if ensured and ensured.get("title"):
                conv_title_created = ensured["title"]
        except Exception as e:
            # If ensure fails, fallback to a new conversation to avoid FK errors
            logger.warning(f"Failed to ensure conversation exists/owned. Creating new. Reason: {e}")
            conv_id = str(uuid.uuid4())
            conv_title_created = _generate_conversation_title(text)
            def _create_fallback():
                supabase.table("conversations").insert({
                    "id": conv_id,
                    "user_id": user["id"],
                    "title": conv_title_created
                }).execute()
            try:
                await run_in_threadpool(_create_fallback)
            except Exception as ce:
                logger.info(f"Conversation fallback create ignored: {ce}")

    # Fetch recent history for this conversation
    history: List[dict] = []
    def _fetch_history():
        return supabase.table("messages").select("role,agent,content,created_at").eq("conversation_id", conv_id).eq("user_id", user["id"]).order("created_at", desc=False).limit(50).execute()
    try:
        hres = await run_in_threadpool(_fetch_history)
        rows = hres.data or []
        # Normalize
        for r in rows:
            history.append({
                "role": r.get("role"),
                "agent": r.get("agent"),
                "content": r.get("content")
            })
    except Exception:
        history = []

    # The coordinator handles routing; include history in context
    result = await _coordinator_reply(text, user, history)
    reply = result.get("text", "")
    agent_name = result.get("agent", "coordinator")
    data = result.get("data", {})

    # Persist conversation and messages
    logger.info(f"Attempting to persist messages for conversation_id: {conv_id}")
    try:
        # Insert messages
        messages_to_insert = []
        if text:
            messages_to_insert.append({
                "user_id": user["id"],
                "conversation_id": conv_id,
                "role": "user",
                "agent": "user",
                "content": req.message
            })
        messages_to_insert.append({
            "user_id": user["id"],
            "conversation_id": conv_id,
            "role": "assistant",
            "agent": agent_name,
            "content": reply
        })

        def _insert_messages():
            supabase.table("messages").insert(messages_to_insert).execute()
        await run_in_threadpool(_insert_messages)
        logger.info(f"Successfully persisted messages for conversation_id: {conv_id}")
    except Exception as e:
        print(f"ERROR: Could not persist chat messages. Reason: {e}")
        logger.error(f"ERROR: Could not persist chat messages for conversation_id: {conv_id}. Reason: {e}")
        pass

    async def gen():
        # First, send a JSON metadata line with the agent so the UI can adapt rendering
        meta = {
            "text": "",
            "data": {
                "agent": agent_name,
                "conversation_id": conv_id,
                **({"conversation_title": conv_title_created} if conv_title_created else {})
            },
            "responsible_ai_checks": result.get("responsible_ai_checks"),
            "responsible_ai_passed": result.get("responsible_ai_passed"),
            "responsible_ai_risk_level": result.get("responsible_ai_risk_level"),
        }
        yield (json.dumps(meta) + "\n")
        # Then stream the reply in small chunks to feel chat-like
        chunk = 64
        for i in range(0, len(reply), chunk):
            yield reply[i:i+chunk]
            await asyncio.sleep(0.02)

    return StreamingResponse(gen(), media_type="text/plain")

# ---------------------- CONVERSATIONS ----------------------

@app.get("/conversations")
async def list_conversations(authorization: str = Header(default="")):
    user = await get_current_user(authorization.replace("Bearer ", ""))
    if not user:
        raise HTTPException(401, "Unauthorized")

    def _fetch():
        return supabase.table("conversations").select("id,title,created_at,updated_at").eq("user_id", user["id"]).order("updated_at", desc=True).execute()

    res = await run_in_threadpool(_fetch)
    return {"conversations": res.data or []}

@app.post("/conversations/recover")
async def recover_conversations(authorization: str = Header(default="")):
    """
    Finds and restores conversations that have messages but are missing the
    main conversation entry. This is a recovery mechanism for orphaned data.
    """
    user = await get_current_user(authorization.replace("Bearer ", ""))
    if not user:
        raise HTTPException(401, "Unauthorized")

    def _recover():
        # 1. Find all distinct conversation_ids from messages for the current user
        msg_convos_res = supabase.rpc('get_distinct_conversation_ids_for_user', {"p_user_id": user["id"]}).execute()
        
        if not msg_convos_res.data:
            return {"recovered": 0, "details": "No message history found."}
            
        message_convo_ids = {item['conversation_id'] for item in msg_convos_res.data}

        # 2. Find all existing conversation_ids from the conversations table for the user
        convos_res = supabase.table("conversations").select("id").eq("user_id", user["id"]).execute()
        existing_convo_ids = {item['id'] for item in convos_res.data}

        # 3. Find the difference -> these are the orphaned conversations
        orphaned_ids = list(message_convo_ids - existing_convo_ids)
        
        if not orphaned_ids:
            return {"recovered": 0, "details": "No orphaned conversations found."}

        # 4. For each orphaned ID, fetch its first message to generate a title
        recovered_conversations = []
        for convo_id in orphaned_ids:
            first_msg_res = supabase.table("messages").select("content").eq("conversation_id", convo_id).eq("user_id", user["id"]).order("created_at", desc=False).limit(1).execute()
            if first_msg_res.data:
                first_message = first_msg_res.data[0]["content"]
                title = _generate_conversation_title(first_message)
                recovered_conversations.append({
                    "id": convo_id,
                    "user_id": user["id"],
                    "title": title
                })

        # 5. Batch insert the recovered conversations
        if recovered_conversations:
            supabase.table("conversations").insert(recovered_conversations).execute()
        
        return {"recovered": len(recovered_conversations), "details": f"Successfully recovered {len(recovered_conversations)} conversations."}

    try:
        result = await run_in_threadpool(_recover)
        return result
    except Exception as e:
        logger.error(f"Conversation recovery failed: {e}")
        raise HTTPException(500, f"Database error during recovery: {str(e)}")


@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, authorization: str = Header(default="")):
    user = await get_current_user(authorization.replace("Bearer ", ""))
    if not user:
        raise HTTPException(401, "Unauthorized")

    def _fetch():
        # Verify ownership; if conversation row is missing but messages exist,
        # recover gracefully by creating a placeholder conversation.
        try:
            conv = supabase.table("conversations").select("id").eq("id", conversation_id).eq("user_id", user["id"]).single().execute()
        except Exception:
            conv = None

        if not conv or not getattr(conv, "data", None):
            # Check if there are messages for this conversation and user
            try:
                msgs_probe = supabase.table("messages").select("id,role,agent,content,created_at,user_id").eq("conversation_id", conversation_id).eq("user_id", user["id"]).order("created_at", desc=False).limit(100).execute()
                rows = (msgs_probe.data or [])
            except Exception:
                rows = []

            if rows:
                # Create a recovered conversation row so future lookups succeed
                try:
                    # Derive a sensible title from the first user message if available
                    first_user_msg = next((r.get("content") for r in rows if (r.get("role") == "user" and r.get("content"))), "")
                    title = _generate_conversation_title(first_user_msg)
                    supabase.table("conversations").insert({
                        "id": conversation_id,
                        "user_id": user["id"],
                        "title": title or "Recovered conversation"
                    }).execute()
                except Exception:
                    # Ignore if it already exists or cannot be created; we'll still return messages
                    pass
                # Return the probed rows in the same shape as a Supabase response
                return {"data": [
                    {k: v for k, v in r.items() if k in {"id", "role", "agent", "content", "created_at"}}
                    for r in rows
                ]}
            # No conversation and no messages -> real not found
            raise Exception("not found")

        # Conversation exists and is owned by user; fetch messages
        msgs = supabase.table("messages").select("id,role,agent,content,created_at").eq("conversation_id", conversation_id).order("created_at", desc=False).execute()
        return msgs

    try:
        res = await run_in_threadpool(_fetch)
        # res can be a Supabase response (with .data) or a dict we returned above
        data = getattr(res, "data", None)
        if data is None and isinstance(res, dict):
            data = res.get("data", [])
        return {"messages": data or []}
    except Exception as e:
        logger.error(f"get_conversation error for {conversation_id}: {e}")
        # Include brief error detail to help debugging during development
        raise HTTPException(404, f"Conversation not found: {str(e)}")

@app.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, authorization: str = Header(default="")):
    user = await get_current_user(authorization.replace("Bearer ", ""))
    if not user:
        raise HTTPException(401, "Unauthorized")

    def _delete():
        # Verify ownership first
        conv = supabase.table("conversations").select("id,user_id").eq("id", conversation_id).eq("user_id", user["id"]).single().execute()
        if not getattr(conv, "data", None):
            raise HTTPException(404, "Conversation not found")
        # Delete only this user's messages for the conversation
        supabase.table("messages").delete().eq("conversation_id", conversation_id).eq("user_id", user["id"]).execute()
        # Then delete the conversation
        supabase.table("conversations").delete().eq("id", conversation_id).eq("user_id", user["id"]).execute()
    await run_in_threadpool(_delete)
    return {"ok": True}

# ---------------------- DEBUG: CONVERSATION STATE ----------------------

@app.get("/debug/conversation-state")
async def debug_conversation_state(authorization: str = Header(default="")):
    """Lightweight debug endpoint to inspect user's conversation/message state.
    Returns conversation ids and per-conversation message counts.
    """
    user = await get_current_user(authorization.replace("Bearer ", ""))
    if not user:
        raise HTTPException(401, "Unauthorized")

    def _inspect():
        # Conversations for user
        conv_res = supabase.table("conversations").select("id,title,created_at,updated_at").eq("user_id", user["id"]).order("updated_at", desc=True).execute()
        conversations = conv_res.data or []

        # Message counts per conversation
        counts = {}
        for c in conversations:
            cid = c.get("id")
            try:
                mres = supabase.table("messages").select("id", count="exact").eq("conversation_id", cid).eq("user_id", user["id"]).execute()
                counts[cid] = getattr(mres, "count", None) or 0
            except Exception:
                counts[cid] = -1  # indicates query error

        return {"conversations": conversations, "message_counts": counts}

    try:
        data = await run_in_threadpool(_inspect)
        return data
    except Exception as e:
        logger.error(f"debug_conversation_state error: {e}")
        raise HTTPException(500, f"Debug error: {str(e)}")

@app.patch("/conversations/{conversation_id}")
async def rename_conversation(conversation_id: str, payload: dict, authorization: str = Header(default="")):
    user = await get_current_user(authorization.replace("Bearer ", ""))
    if not user:
        raise HTTPException(401, "Unauthorized")
    new_title = (payload.get("title") or "").strip()
    if not new_title:
        raise HTTPException(400, "Title required")

    def _rename():
        supabase.table("conversations").update({"title": new_title}).eq("id", conversation_id).eq("user_id", user["id"]).execute()
    await run_in_threadpool(_rename)
    return {"ok": True}

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
# moved to app/api/routers/responsible_ai.py

# Audio endpoints
@app.options("/audio/{audio_id}")
async def audio_options(audio_id: str):
    """Handle CORS preflight for audio files"""
    return JSONResponse(
        content={"message": "OK"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
            "Access-Control-Allow-Headers": "*"
        }
    )

@app.get("/audio/{audio_id}")
async def serve_audio_file(audio_id: str, request: Request):
    """Serve audio files with security validation"""
    try:
        # Lighter security validation for audio files (they're public content)
        # await security_middleware.validate_request_security(request)
        
        # Validate audio ID format (should be hash)
        if not re.match(r'^[a-f0-9]{32}$', audio_id):
            raise HTTPException(400, "Invalid audio ID format")
        
        # Find audio file
        audio_file = Path(f"audio_cache/{audio_id}.mp3")
        if not audio_file.exists():
            raise HTTPException(404, "Audio file not found")
        
        # Security check - ensure file is in allowed directory
        if not str(audio_file.resolve()).startswith(str(Path("audio_cache").resolve())):
            raise HTTPException(403, "Access denied")
        
        # Serve file with appropriate headers including CORS
        return FileResponse(
            audio_file,
            media_type="audio/mpeg",
            headers={
                "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
                "Content-Disposition": f"inline; filename=story_{audio_id}.mp3",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
                "Access-Control-Allow-Headers": "*"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving audio file: {e}")
        raise HTTPException(500, "Audio service error")

# Consolidated: keep the secure /audio/generate implementation below and remove duplicate above

@app.post("/audio/cleanup")
async def cleanup_audio_cache(request: Request):
    """Manual audio cache cleanup endpoint"""
    try:
        # Security validation
        await security_middleware.validate_request_security(request)
        
        # Import audio service here to avoid circular imports
        from app.audio_service import audio_service
        
        # Cleanup old files
        audio_service.cleanup_old_cache(max_age_days=7)
        
        return {"message": "Audio cache cleaned up successfully"}
        
    except Exception as e:
        logger.error(f"Cache cleanup error: {e}")
        raise HTTPException(500, "Cleanup failed")

@app.get("/audio/status")
async def get_audio_status():
    """Get audio service status"""
    try:
        from app.audio_service import audio_service
        
        cache_dir = Path("audio_cache")
        cache_files = list(cache_dir.glob("*.mp3")) + list(cache_dir.glob("*.wav"))
        status = audio_service.get_status() if hasattr(audio_service, 'get_status') else {}
        return {
            "service_available": True,
            "cache_directory": str(cache_dir),
            "cached_files_count": len(cache_files),
            "audio_settings": audio_service.settings,
            "provider": status.get("provider"),
            "selected_voice": status.get("selected_voice"),
            "providers_available": status.get("providers_available"),
            "features": {
                "text_to_speech": True,
                "caching": True,
                "multiple_formats": True,
                "bedtime_optimized": True
            }
        }
    except Exception as e:
        return {
            "service_available": False,
            "error": str(e)[:100],
            "message": "Audio service not available"
        }

@app.post("/audio/generate")
async def generate_audio_from_text(request: Request):
    """Generate audio from story text on-demand"""
    try:
        # Security validation
        await security_middleware.validate_request_security(request)
        
        # Get request body
        body = await request.json()
        story_text = body.get("text", "").strip()
        
        if not story_text:
            raise HTTPException(400, "Story text is required")
        
        if len(story_text) < 10:
            raise HTTPException(400, "Story text too short for audio generation")
        
        if len(story_text) > 10000:  # Reasonable limit for TTS
            raise HTTPException(400, "Story text too long for audio generation")
        
        # Import audio service
        from app.audio_service import audio_service
        
        # Generate audio file
        audio_file_path = await audio_service.text_to_speech_file(
            story_text, 
            output_format="mp3",
            use_cache=True
        )
        
        if not audio_file_path:
            raise HTTPException(500, "Failed to generate audio")
        
        # Get audio metadata
        audio_metadata = audio_service.get_audio_metadata(story_text)
        
        # Extract just the filename for secure serving
        audio_filename = audio_file_path.split('/')[-1].replace('.mp3', '') if '/' in audio_file_path else audio_file_path.split('\\')[-1].replace('.mp3', '')
        
        logger.info(f"Audio generated on-demand - Duration: {audio_metadata['estimated_duration_minutes']} min")
        
        return {
            "success": True,
            "audio_id": audio_filename,
            "metadata": audio_metadata,
            "message": "Audio generated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating audio: {str(e)[:100]}")
        raise HTTPException(500, "Audio generation failed")
