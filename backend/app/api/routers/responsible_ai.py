from fastapi import APIRouter, Header, HTTPException, Query, Request
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.db import get_current_user
from app.services.responsible_ai_service import (
    get_status as rai_get_status,
    validate as rai_validate,
    get_guidelines as rai_get_guidelines,
    get_audit_log as rai_get_audit_log,
)

router = APIRouter(prefix="/responsible-ai", tags=["responsible-ai"])


@router.get("/status")
async def get_responsible_ai_status():
    return rai_get_status()


@router.post("/validate")
async def validate_responsible_ai(
    payload: Dict[str, Any],
    authorization: str = Header(default=""),
):
    user = await get_current_user(authorization.replace("Bearer ", ""))
    if not user:
        raise HTTPException(401, "Unauthorized")

    text = (payload.get("text") or "").strip()
    if not text:
        raise HTTPException(400, "Text content is required")

    action_type = payload.get("action_type", "general_response")
    user_context = payload.get("user_context", {})
    data_sources = payload.get("data_sources", [])
    decision_factors = payload.get("decision_factors", {})

    try:
        results = await rai_validate(
            text=text,
            action_type=action_type,
            user_context=user_context,
            data_sources=data_sources,
            decision_factors=decision_factors,
        )
        return {
            "validation_results": results,
            "overall_passed": all(r.get("passed", False) for r in results.values() if isinstance(r, dict)),
            "timestamp": datetime.now().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Validation error: {str(e)}")


@router.get("/guidelines")
async def get_responsible_ai_guidelines():
    return rai_get_guidelines()


@router.get("/audit-log")
async def get_responsible_ai_audit_log(
    limit: int = Query(default=50, le=200),
    authorization: str = Header(default=""),
):
    user = await get_current_user(authorization.replace("Bearer ", ""))
    if not user:
        raise HTTPException(401, "Unauthorized")
    # In future, check admin status here
    return rai_get_audit_log(limit=limit, user_id=user.get("id"))
