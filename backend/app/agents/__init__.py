# app/agents/__init__.py
from typing import Any, Dict, Optional, TypedDict

class AgentContext(Dict[str, Any]):
    """
    Shared context passed into agents.
    Example keys:
        {
          "user": {"id": "...", "email": "..."},
          "logs": [...],          # recent sleep logs
          "analysis": {...}       # precomputed metrics
        }
    """

class AgentResponse(TypedDict, total=False):
    """
    Standard format returned by every agent.
    Fields:
        agent: which agent handled it ("coach", "analytics", etc.)
        text: plain response string
        data: optional structured payload (dict) with extra info
    """
    agent: str
    text: str
    data: Dict[str, Any]

class BaseAgent:
    """
    All agents inherit from this.
    They must implement an async handle() method.
    """
    name: str = "base"

    async def handle(
        self,
        message: str,
        ctx: Optional[AgentContext] = None
    ) -> AgentResponse:
        raise NotImplementedError("Agent must implement handle()")
