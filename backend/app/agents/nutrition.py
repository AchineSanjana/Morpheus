# app/agents/nutrition.py
from typing import Optional, Dict, Any
from . import BaseAgent, AgentContext, AgentResponse
from app.db import fetch_recent_logs
from app.llm_gemini import generate_gemini_text

DISCLAIMER = (
    "_This is general wellness guidance, not medical advice. "
    "For ongoing sleep or health concerns, consult a qualified clinician._"
)

class NutritionAgent(BaseAgent):
    """
    Wellness advisor focusing on caffeine, alcohol, and lifestyle factors.
    Tracks patterns in recent logs and explains how they may affect sleep.
    """
    name = "nutrition"

    async def handle(self, message: str, ctx: Optional[AgentContext] = None) -> AgentResponse:
        ctx = ctx or {}
        user = ctx.get("user")
        if not user:
            return {"agent": self.name, "text": "Please sign in first so I can review your logs."}

        # Pull last 7 days of logs
        logs = ctx.get("logs") or await fetch_recent_logs(user["id"], days=7)
        if not logs:
            return {"agent": self.name, "text": "I couldn’t find any recent sleep logs to analyze."}

        # Track lifestyle patterns
        caffeine_days = sum(1 for r in logs if r.get("caffeine_after3pm"))
        alcohol_days = sum(1 for r in logs if r.get("alcohol"))
        total_days = len(logs)

        summary = {
            "days": total_days,
            "caffeine_after3pm_days": caffeine_days,
            "alcohol_days": alcohol_days,
        }

        # Build a lifestyle-focused prompt
        prompt = f"""
        You are a supportive wellness advisor.
        A user has provided sleep logs. Your job is to explain how lifestyle factors like
        caffeine, alcohol, and exercise timing may influence their sleep.

        Data snapshot (last {total_days} nights):
        - Caffeine after 3pm on {caffeine_days}/{total_days} nights
        - Alcohol use on {alcohol_days}/{total_days} nights
        - (Note: exercise timing not logged directly, but you may mention general impact)

        Write a friendly and clear explanation:
        1. Summarize observed patterns (if any).
        2. Explain how caffeine, alcohol, and exercise timing can impact sleep quality.
        3. Give 2–3 simple suggestions to improve sleep hygiene in these areas.
        End with encouragement.
        """

        llm_response = await generate_gemini_text(prompt)

        if not llm_response:
            # Fallback if Gemini fails
            llm_response = (
                f"In the last {total_days} nights, you logged caffeine after 3pm on "
                f"{caffeine_days} nights and alcohol on {alcohol_days} nights. "
                "Both can reduce sleep quality and increase awakenings. "
                "Try limiting caffeine to before 3pm, reducing alcohol close to bedtime, "
                "and adding regular daytime exercise for better sleep."
            )

        text = f"{llm_response.strip()}\n\n{DISCLAIMER}"
        return {"agent": self.name, "text": text, "data": {"summary": summary, "sample": logs[-3:]}}
