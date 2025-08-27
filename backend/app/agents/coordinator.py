# app/agents/coordinator.py
from typing import Optional
from . import BaseAgent, AgentContext, AgentResponse
from .analyst import AnalyticsAgent
from .coach import CoachAgent
from .information import InformationAgent

WELCOME_MENU = [
    "• Log last night’s sleep",
    "• Analyze my last 7 days",
    "• Give me a 7-day improvement plan",
    "• What do reputable sources say about caffeine/screens/bedtime?",
]

class CoordinatorAgent(BaseAgent):
    name = "coordinator"

    def __init__(self) -> None:
        self.analyst = AnalyticsAgent()
        self.coach = CoachAgent()
        self.info = InformationAgent()

    def _intent(self, msg: str) -> str:
        t = msg.lower()
        if any(k in t for k in ["analy", "trend", "week", "report", "summary"]):
            return "analytics"
        if any(k in t for k in ["plan", "tips", "improve", "advice", "coach"]):
            return "coach"
        if any(k in t for k in ["caffeine", "coffee", "screen", "explain", "what is", "define"]):
            return "information"
        return "coach"  # default: help them with advice

    async def handle(self, message: str, ctx: Optional[AgentContext] = None) -> AgentResponse:
        ctx = ctx or {}
        user = ctx.get("user")

        # Greeting / first message
        if not message.strip() or message.strip().lower() in {"hi", "hello", "hey"}:
            menu = "\n".join(WELCOME_MENU)
            text = (
                f"Hi{' ' + user.get('email') if user else ''}! I’m your sleep coordinator.\n\n"
                f"Here are some things you can try:\n{menu}\n\n"
                f"Or just ask in your own words — I’ll route it to the right agent."
            )
            return {"agent": self.name, "text": text}

        # Route based on intent
        intent = self._intent(message)
        if intent == "analytics":
            return await self.analyst.handle(message, ctx)
        if intent == "information":
            return await self.info.handle(message, ctx)
        return await self.coach.handle(message, ctx)
