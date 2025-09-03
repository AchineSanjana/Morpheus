from pydantic import BaseModel
from typing import Optional, Dict, Any 

class ChatRequest(BaseModel):
    message: str

class SleepLogIn(BaseModel):
    date: str
    bedtime: Optional[str] = None
    wake_time: Optional[str] = None
    awakenings: int = 0
    caffeine_after3pm: bool = False
    alcohol: bool = False
    screen_time_min: int = 0
    notes: Optional[str] = None

#---------------
class InfoResponse(BaseModel):
    message: str
    details: Optional[Dict[str, Any]] = None

class AgentResponseModel(BaseModel):
    status: str
    data: Optional[Dict[str, Any]] = None