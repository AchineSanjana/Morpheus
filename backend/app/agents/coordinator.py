# app/agents/coordinator.py
from typing import Optional
from . import BaseAgent, AgentContext, AgentResponse
from .analyst import AnalyticsAgent
from .coach import CoachAgent
from .information import InformationAgent
from .storyteller import StoryTellerAgent
from app.llm_gemini import generate_gemini_text, gemini_ready  # Gemini helpers

WELCOME_MENU = [
    "• Log last night’s sleep",
    "• Analyze my last 7 days",
    "• Give me a 7-day improvement plan",
    "• What do reputable sources say about caffeine/screens/bedtime?",
    "• Tell me a bedtime story",
]

_ALLOWED = {"analytics", "coach", "information", "storyteller"}

class CoordinatorAgent(BaseAgent):
    name = "coordinator"

    def __init__(self) -> None:
        self.analyst = AnalyticsAgent()
        self.coach = CoachAgent()
        self.info = InformationAgent()
        self.story = StoryTellerAgent()

    def _intent_keyword(self, msg: str) -> str:
        """Fallback keyword-based intent detection."""
        t = (msg or "").lower()
        if any(k in t for k in ["analy", "trend", "week", "report", "summary", "insight"]):
            return "analytics"
        if any(k in t for k in ["plan", "tips", "improve", "advice", "coach"]):
            return "coach"
        if any(k in t for k in ["caffeine", "coffee", "screen", "explain", "what is", "define", "tell me about"]):
            return "information"
        if any(k in t for k in ["story", "bedtime", "narrate", "fairytale"]):
            return "storyteller"
        return "coach"  # default: be helpful with advice

    def _intent_llm(self, message: str) -> Optional[str]:
        """
        Ask Gemini to choose among {'analytics','coach','information','storyteller'}.
        Returns a valid label or None on any issue (so we can fall back).
        """
        if not gemini_ready():
            return None

        prompt = (
            "You route user sleep questions to one of these agents:\n"
            "- analytics: analyze past sleep data, trends, summaries, reports\n"
            "- coach: give advice, plans, tips, how to improve sleep\n"
            "- information: factual info/definitions about sleep topics (caffeine, alcohol, screens, etc.)\n"
            "- storyteller: tell a calming, short bedtime story\n\n"
            f"User message: \"{message}\"\n\n"
            "Respond with just one word: analytics, coach, information, or storyteller."
        )

        try:
            raw = generate_gemini_text(prompt, model="gemini-1.5-flash") or ""
        except Exception:
            return None

        cleaned = (
            raw.strip()
               .lower()
               .replace("'", "")
               .replace('"', "")
               .replace(".", "")
               .split()
        )
        if not cleaned:
            return None
        choice = cleaned[0]
        return choice if choice in _ALLOWED else None

    async def handle(self, message: str, ctx: Optional[AgentContext] = None) -> AgentResponse:
        ctx = ctx or {}
        user = ctx.get("user")

        # Greeting / first message
        if not (message or "").strip() or (message or "").strip().lower() in {"hi", "hello", "hey"}:
            menu = "\n".join(WELCOME_MENU)
            text = (
                f"Hi{' ' + user.get('email') if user else ''}! I’m your sleep coordinator.\n\n"
                f"Here are some things you can try:\n{menu}\n\n"
                f"Or just ask in your own words — I’ll route it to the right agent."
            )
            return {"agent": self.name, "text": text}

        # 1) Try LLM for intent; 2) fallback to keywords
        intent = self._intent_llm(message) or self._intent_keyword(message)

        # If the user wants coaching or analysis, compute analysis first
        if intent in ("analytics", "coach"):
            analysis_result = await self.analyst.handle(message, ctx)

            if intent == "analytics":
                return analysis_result

            # attach analysis summary to ctx for the coach
            if isinstance(analysis_result, dict) and "data" in analysis_result:
                ctx["analysis"] = analysis_result["data"]
            return await self.coach.handle(message, ctx)

        if intent == "information":
            return await self.info.handle(message, ctx)

        if intent == "storyteller":
            return await self.story.handle(message, ctx)

        # Default safety: coach
        return await self.coach.handle(message, ctx)
