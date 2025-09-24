# app/agents/coordinator.py
from typing import Optional
from . import BaseAgent, AgentContext, AgentResponse
from .analyst import AnalyticsAgent
from .coach import CoachAgent
from .information import InformationAgent
from .nutrition import NutritionAgent #Amath
from .addiction import AddictionAgent #Amath
from app.llm_gemini import generate_gemini_text  # Import the Gemini helper

WELCOME_MENU = [
    "• Log last night’s sleep",
    "• Analyze my last 7 days",
    "• Give me a 7-day improvement plan",
    "• What do reputable sources say about caffeine/screens/bedtime?",
]

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

    def _intent_keyword(self, msg: str) -> str:
        """Fallback keyword-based intent detection."""
        t = msg.lower()
        if any(k in t for k in ["analy", "trend", "week", "report", "summary"]):
            return "analytics"
        if any(k in t for k in ["plan", "tips", "improve", "advice", "coach"]):
            return "coach"
        if any(k in t for k in ["caffeine", "coffee", "screen", "explain", "what is", "define", "tell me about"]):
            return "information"
        if any(k in t for k in [
                "nutrition", "diet", "food", "meal", "eating",
                "caffeine", "coffee", "tea", "energy drink",
                "alcohol", "wine", "beer", "drink",
                "exercise", "workout", "gym", "training",
                "lifestyle", "habits", "routine"
                ]):
            return "nutrition" #Amath
        if any(k in t for k in ["addict", "quit", "craving", "dependence"]):
            return "addiction" #Amath
        return "coach"  # default: help them with advice

    async def _get_intent_with_llm(self, message: str) -> Optional[str]:
        """Use Gemini to determine the user's intent."""
        prompt = f"""
        You are an expert at routing user requests to the correct agent.
        Here are the available agents and their descriptions:
        - 'analytics': Use for requests about analyzing past sleep data, showing trends, summaries, or reports.
        - 'coach': Use for requests asking for advice, a sleep plan, tips, or general guidance on how to improve sleep.
        - 'information': Use for requests asking for factual information, definitions, or explanations about specific sleep-related topics (like caffeine, alcohol, screens, etc.).

        User message: "{message}"

        Based on the user message, which agent should handle this request?
        Respond with a single word: 'analytics', 'coach', or 'information'.
        """
        try:
            response = await generate_gemini_text(prompt)
            if response:
                # Clean up the response to get a single word
                cleaned_response = response.strip().lower().replace("'", "").replace('"', '').replace(".", "")
                if cleaned_response in ["analytics", "coach", "information"]:
                    return cleaned_response
        except Exception:
            return None
        return None

    async def _handle_core(self, message: str, ctx: Optional[AgentContext] = None) -> AgentResponse:
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

        # --- NEW: Intelligent Intent Detection ---
        # Try to get intent from the LLM first
        intent = await self._get_intent_with_llm(message)
        
        # If LLM fails or returns invalid response, fall back to keyword search
        if not intent:
            intent = self._intent_keyword(message)
        # --- END NEW ---

        # --- MODIFIED: Route based on the determined intent ---
        # If the user wants coaching or analysis, we need to run the analysis first.
        if intent in ["analytics", "coach"]:
            analysis_result = await self.analyst.handle(message, ctx)
            
            # If the intent was just analysis, return the result directly.
            if intent == "analytics":
                return analysis_result
            
            # If the intent was addiction, route to the addiction agent. - Amath
            if intent == "addiction":
                return await self.addiction.handle(message, ctx)

            # If the intent was coaching, add the analysis to the context and proceed.
            if "data" in analysis_result:
                ctx["analysis"] = analysis_result["data"]
            return await self.coach.handle(message, ctx)

        if intent == "information":
            return await self.info.handle(message, ctx)
        
        # Default to the coach agent if unsure
        return await self.coach.handle(message, ctx)
