# app/agents/coordinator.py
from typing import Optional
from . import BaseAgent, AgentContext, AgentResponse
from .analyst import AnalyticsAgent
from .coach import CoachAgent
from .information import InformationAgent
from .nutrition import NutritionAgent
from .addiction import AddictionAgent
from .storyteller import StoryTellerAgent
from app.llm_gemini import generate_gemini_text, gemini_ready  # Import the Gemini helper

WELCOME_MENU = [
    "• Log last night’s sleep",
    "• Analyze my last 7 days",
    "• Give me a 7-day improvement plan",
    "• What do reputable sources say about caffeine/screens/bedtime?",
    "• Tell me a bedtime story",
]

_ALLOWED = {"analytics", "coach", "information", "storyteller", "addiction"}

class CoordinatorAgent(BaseAgent):
    name = "coordinator"

    def __init__(self) -> None:
        super().__init__()
        self.action_type = "request_routing"  # For responsible AI transparency
        self.analyst = AnalyticsAgent()
        self.coach = CoachAgent()
        self.nutrition = NutritionAgent() #Amath
        self.addiction = AddictionAgent() #Amath
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
        # Add addiction detection
        if any(k in t for k in ["addict", "dependen", "craving", "alcohol", "nicotine", "smoking", "drinking", "quit", "stop", "withdrawal", "too much coffee", "too much alcohol"]):
            return "addiction"
        return "coach"  # default: help them with advice

    async def _intent_llm(self, message: str) -> Optional[str]:
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
            "- addiction: help with addiction/dependency issues (caffeine, alcohol, nicotine, digital)\n"
            "- storyteller: tell a calming, short bedtime story\n\n"
            f"User message: \"{message}\"\n\n"
            "Respond with just one word: analytics, coach, information, addiction, or storyteller."
        )

        try:
            raw = await generate_gemini_text(prompt, model_name="gemini-2.0-flash-exp") or ""
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

    async def _handle_core(self, message: str, ctx: Optional[AgentContext] = None) -> AgentResponse:
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

        # Check if this is an addiction-related query first
        if self.addiction._detect_addiction_context(message):
            return await self.addiction.handle(message, ctx)

        # 1) Try LLM for intent; 2) fallback to keywords
        intent = await self._intent_llm(message) or self._intent_keyword(message)

        # If the user wants coaching or analysis, compute analysis first
        if intent in ("analytics", "coach"):
            analysis_result = await self.analyst.handle(message, ctx)

            if intent == "analytics":
                return analysis_result
            
            # If the intent was coaching, add the analysis to the context and proceed.
            if "data" in analysis_result:
                ctx["analysis"] = analysis_result["data"]
            return await self.coach.handle(message, ctx)

        if intent == "information":
            return await self.info.handle(message, ctx)

        if intent == "storyteller":
            return await self.story.handle(message, ctx)

        if intent == "addiction":
            return await self.addiction.handle(message, ctx)

        # Default safety: coach
        return await self.coach.handle(message, ctx)
