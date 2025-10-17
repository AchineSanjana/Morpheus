from pydantic import BaseModel
from typing import Optional, Any, Dict

class ChatRequest(BaseModel):
    """Request body for streaming chat endpoint."""
    message: str
    conversation_id: Optional[str] = None  # Optional conversation thread id

class SleepLogIn(BaseModel):
    """Sleep log entry input model for /sleep-log."""
    date: str
    bedtime: Optional[str] = None
    wake_time: Optional[str] = None
    awakenings: int = 0
    caffeine_after3pm: bool = False
    alcohol: bool = False
    screen_time_min: int = 0
    notes: Optional[str] = None

class PredictionRequest(BaseModel):
    """Model for prediction-related prompts (if used by agents)."""
    message: str
    user_data: Optional[Dict[str, Any]] = None
 
class InfoResponse(BaseModel):
    """Structured informational response from the information agent."""
    topic: str
    text: str

class AgentResponseModel(BaseModel):
    """Standard agent response shape used across agents."""
    agent: str
    text: str
    data: Optional[Dict[str, Any]] = None