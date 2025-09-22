# app/agents/addiction.py
from typing import Optional
from . import BaseAgent, AgentContext, AgentResponse
from app.llm_gemini import generate_gemini_text

DISCLAIMER = (
    "_This is supportive educational guidance, not medical or addiction treatment. "
    "If you struggle with addiction, please consult a qualified clinician or counselor._"
)

TRIGGERS = ["addict", "dependen", "craving", "alcohol", "caffeine", "nicotine", "smoking"]

class AddictionAgent(BaseAgent):
    """
    Supports users mentioning addictive behaviors (caffeine, alcohol, nicotine, etc.).
    Offers gentle, safe advice for reducing dependence and encourages professional help.
    """
    name = "addiction"

    def _detect_addiction_context(self, message: str) -> bool:
        """Check if user message contains addiction-related triggers."""
        t = message.lower()
        return any(k in t for k in TRIGGERS)

    async def handle(self, message: str, ctx: Optional[AgentContext] = None) -> AgentResponse:
        ctx = ctx or {}
        if not self._detect_addiction_context(message):
            return {
                "agent": self.name,
                "text": "I didn’t detect addiction-related concerns in your message.",
            }

        # LLM prompt for structured advice
        prompt = f"""
        You are a supportive wellness advisor. A user is asking about addiction or dependence.

        User message: "{message}"

        Write a structured response with three parts:
        1. **Acknowledgment** (1–2 sentences): Empathize and normalize their concern.
        2. **Safe, practical steps** (3–4 bullet points): Provide beginner-level strategies 
           for reducing or managing addictive behaviors (like caffeine, alcohol, nicotine).
           Keep it gentle, encouraging, and not medicalized.
        3. **Encouragement**: End with a positive, supportive note.
        """

        llm_response = await generate_gemini_text(prompt)

        if not llm_response:
            # Fallback if Gemini fails
            llm_response = (
                "It sounds like you're concerned about dependence. "
                "Here are a few ideas that might help:\n"
                "• Start by reducing gradually instead of quitting abruptly.\n"
                "• Replace the habit with a healthier routine (like tea instead of coffee, or a walk instead of a drink).\n"
                "• Keep a journal of triggers and patterns.\n"
                "• Reach out for support from a friend or professional if it feels overwhelming.\n\n"
                "You're not alone — small steps add up!"
            )

        text = f"{llm_response.strip()}\n\n{DISCLAIMER}"
        return {"agent": self.name, "text": text, "data": {"triggered": True}}
