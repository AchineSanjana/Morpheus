# app/agents/coordinator.py
from typing import Optional
# Import base agent interfaces and response/context types
from . import BaseAgent, AgentContext, AgentResponse
# Import all specialized sub-agents that handle different user intents
from .analyst import AnalyticsAgent
from .coach import CoachAgent
from .information import InformationAgent
from .nutrition import NutritionAgent
from .addiction import AddictionAgent
from .storyteller import StoryTellerAgent
from .prediction import SleepPredictionAgent
from app.llm_gemini import generate_gemini_text, gemini_ready  # Import the Gemini helper

# Predefined welcome menu to show when user first interacts with the system
WELCOME_MENU = [
    "• Log last night's sleep",
    "• Analyze my last 7 days",
    "• Give me a 7-day improvement plan",
    "• Predict tonight's sleep quality",
    "• Get optimal bedtime recommendation",
    "• What do reputable sources say about caffeine/screens/bedtime?",
    "• Get lifestyle guidance from my logs (caffeine/alcohol)",
    "• Tell me a bedtime story",
]

# Allowed agent types (helps validate LLM intent classification)
_ALLOWED = {"analytics", "coach", "information", "nutrition", "storyteller", "addiction", "prediction"}

class CoordinatorAgent(BaseAgent):
    """Central routing agent that decides which sub-agent should handle the user's request"""
    name = "coordinator"

    def __init__(self) -> None:
        super().__init__()
        self.action_type = "request_routing"  # For responsible AI transparency
        
        # Initialize all domain-specific agents
        self.analyst = AnalyticsAgent() # Janiru
        self.coach = CoachAgent() # Janiru
        self.nutrition = NutritionAgent() # Amath - Personalized health guidance
        self.addiction = AddictionAgent() # Amath - Handles dependency-related requests
        self.info = InformationAgent() # Shenali - Provides factual information
        self.story = StoryTellerAgent() # Sanjana - Generates bedtime stories
        self.prediction = SleepPredictionAgent() # Shenali - Forecasts sleep quality

    def _intent_keyword(self, msg: str) -> str:
        """Fallback keyword-based intent detection with addiction gating."""
        t = (msg or "").lower()
        # Analytics
        if any(k in t for k in ["analy", "trend", "week", "report", "summary", "insight"]):
            return "analytics"

        # Prediction keywords
        if any(k in t for k in ["predict", "tonight", "tomorrow", "quality", "bedtime", "when should", "optimal"]):
            return "prediction"

        # Addiction only when explicit dependency/quit cues exist
        try:
            if self.addiction._detect_addiction_context(msg):
                return "addiction"
        except Exception:
            pass # Continue if addiction detection fails safely

        # Nutrition vs Information split
        # If user shows personal context or asks for personalized/lifestyle help, send to nutrition
        personal_cues = ["my ", "i ", "i'm", "i am", "based on my", "my logs", "last night", "last week", "should i", "what should i"]
        lifestyle_terms = ["caffeine", "coffee", "alcohol", "diet", "food", "eating", "exercise", "workout", "screens", "screen"]
        if any(term in t for term in lifestyle_terms):
            # If the message refers to user's own habits → Nutrition
            if any(cue in t for cue in personal_cues):
                return "nutrition"
            # If asking general info → Information
            if any(k in t for k in ["explain", "what is", "define", "tell me about", "effect of", "impact of", "how does"]):
                return "information"
            # Default fallback → Nutrition (safe assumption for personalization)
            return "nutrition"

       # Identify coaching requests
        if any(k in t for k in ["plan", "tips", "improve", "advice", "coach"]):
            return "coach"

        return "coach"  # Default fallback if no other match

    async def _intent_llm(self, message: str) -> Optional[str]:
        """
        Ask Gemini to choose among {'analytics','coach','information','storyteller'}.
        Returns a valid label or None on any issue (so we can fall back).
        """
        if not gemini_ready():
            return None # Skip if LLM not initialized

        # Build structured prompt for LLM intent routing
        prompt = (
            "Route the user's sleep message to exactly one agent:\n"
            "- analytics: analyze past data, trends, summaries, reports\n"
            "- coach: advice, plans, tips to improve sleep\n"
            "- information: neutral facts/definitions about topics (sleep science, caffeine/alcohol/screens in general)\n"
            "- nutrition: personalized lifestyle guidance using the user's logs (caffeine timing, alcohol days, exercise); use only when the user seeks personal advice or refers to their logs or own habits\n"
            "- addiction: ONLY if message indicates dependency or quitting (e.g., 'addicted', 'can't stop', 'withdrawal', 'craving', 'too much', 'need to quit')\n"
            "- prediction: sleep quality predictions, bedtime recommendations, forecasting tonight's sleep\n"
            "- storyteller: short calming bedtime story\n\n"
            f"User message: \"{message}\"\n\n"
            "Respond with just one word: analytics, coach, information, nutrition, addiction, prediction, or storyteller."
        )

        try:
            # Use default preferred model (gemini-2.5-flash) with automatic fallbacks
             # Ask Gemini model for routing suggestion
            raw = await generate_gemini_text(prompt) or ""
        except Exception:
            return None # Fail gracefully

        # Clean and normalize model output
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
        if choice not in _ALLOWED:
            return None # Invalid result ignored

        # Guard: demote false-positive addiction unless explicit dependency cues exist
        if choice == "addiction" and not self.addiction._detect_addiction_context(message):
            t = (message or "").lower()
            if any(k in t for k in ["caffeine", "coffee", "alcohol", "nicotine", "smoking", "screen", "screens"]):
                # If message relates to substances but lacks dependency terms
                personal_cues = ["my ", "i ", "i'm", "i am", "based on my", "my logs", "last night", "last week", "should i", "what should i"]
                if any(cue in t for cue in personal_cues):
                    return "nutrition" # Personal context → nutrition
                return "information" # General context → information
            return "coach" # Otherwise, route to coach

        return choice

    async def _handle_core(self, message: str, ctx: Optional[AgentContext] = None) -> AgentResponse:
        # Main routing logic that delegates user queries to appropriate agents
        ctx = ctx or {}
        user = ctx.get("user")

        # Handle greeting or empty message → show intro menu
        if not (message or "").strip() or (message or "").strip().lower() in {"hi", "hello", "hey"}:
            menu = "\n".join(WELCOME_MENU)
            dn = (ctx.get("display_name") or "").strip()
            name_part = f" {dn}" if dn else ""
            text = (
                f"Hi{name_part}! I’m your sleep coordinator.\n\n"
                f"Here are some things you can try:\n{menu}\n\n"
                f"Or just ask in your own words — I’ll route it to the right agent."
            )
            return {"agent": self.name, "text": text}

        # Check if this is an addiction-related query first
        if self.addiction._detect_addiction_context(message):
            return await self.addiction.handle(message, ctx)

        # 1) Try LLM for intent; 2) fallback to keywords
        intent = await self._intent_llm(message) or self._intent_keyword(message)

         # --- INTENT HANDLING SECTION ---

        # If the user wants coaching or analysis, compute analysis first
        if intent in ("analytics", "coach"):
            analysis_result = await self.analyst.handle(message, ctx)

             # If purely analytical request, return directly
            if intent == "analytics":
                return analysis_result
            
            # If the intent was coaching, add the analysis to the context and proceed.
            if "data" in analysis_result:
                ctx["analysis"] = analysis_result["data"]
            return await self.coach.handle(message, ctx)

        # Information Agent → factual explanations
        if intent == "information":
            return await self.info.handle(message, ctx)

        # Nutrition Agent → personalized lifestyle guidance
        if intent == "nutrition":
            return await self.nutrition.handle(message, ctx)

        # Storyteller Agent → generate bedtime stories
        if intent == "storyteller":
            return await self.story.handle(message, ctx)

        # Addiction Agent → handle dependency/quit-related requests
        if intent == "addiction":
            return await self.addiction.handle(message, ctx)

        # Prediction Agent → forecast tonight’s sleep quality
        if intent == "prediction":
            return await self.prediction.handle(message, ctx)

        # Default fallback → Coach agent (covers general improvement tips)
        return await self.coach.handle(message, ctx)
