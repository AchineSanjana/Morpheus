# app/agents/nutrition.py
from typing import Optional, Dict, Any, List
from . import BaseAgent, AgentContext, AgentResponse
from app.db import fetch_recent_logs
from app.llm_gemini import generate_gemini_text

# Disclaimer added to every AI response for transparency and safety
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
    
    def __init__(self):
        super().__init__()
        # Defines what kind of action this agent performs (for explainability)
        self.action_type = "personalized_recommendation"  # For responsible AI transparency

    async def _handle_core(self, message: str, ctx: Optional[AgentContext] = None) -> AgentResponse:
        ctx = ctx or {} # Context may contain user data and recent logs
        user = ctx.get("user")
        # Require user authentication to access personal logs
        if not user:
            return {"agent": self.name, "text": "Please sign in first so I can review your logs."}

        # Pull last 7 days of logs (prefer provided logs in context)
        logs: List[Dict[str, Any]] = ctx.get("logs") or await fetch_recent_logs(user["id"], days=7)
        if not logs:
            return {"agent": self.name, "text": "I couldn’t find any recent sleep logs to analyze."}

        # Track lifestyle patterns (augmentable with analytics summary if already computed)
        total_days = len(logs)
        caffeine_days = sum(1 for r in logs if r.get("caffeine_after3pm"))
        alcohol_days = sum(1 for r in logs if r.get("alcohol"))
        high_screen_days = sum(1 for r in logs if (r.get("screen_time_min", 0) or 0) > 60)

        # Create a summary of key behavior patterns
        summary: Dict[str, Any] = {
            "days": total_days,
            "caffeine_after3pm_days": caffeine_days,
            "alcohol_days": alcohol_days,
            "high_screen_time_days": high_screen_days,
        }

        # If Analytics summary is present in context, include helpful fields
        analysis = ctx.get("analysis") or {}
        if isinstance(analysis, dict):
            # Coordinator stores analysis_result["data"], which includes a 'summary' dict
            analysis_summary = analysis.get("summary") if isinstance(analysis.get("summary"), dict) else None
            if analysis_summary:
                # Non-destructive merge of selected metrics
                for k in (
                    "avg_duration_h", "avg_awakenings", "avg_screen_time_min", "sleep_efficiency",
                    "alcohol_nights", "nicotine_nights", "nights"
                ):
                    if k in analysis_summary and analysis_summary[k] is not None:
                        summary[k] = analysis_summary[k]

        # Build a lifestyle-focused prompt
        prompt = f"""
        You are a supportive wellness advisor focused on lifestyle factors and sleep.
        Use the data snapshot to provide personalized, practical guidance.

        Data snapshot (last {total_days} nights):
        - Caffeine after 3pm: {caffeine_days}/{total_days} nights
        - Alcohol use: {alcohol_days}/{total_days} nights
        - High screen time (>60 min pre-bed): {high_screen_days}/{total_days} nights
        - Averages (if provided): duration={summary.get('avg_duration_h')}h, awakenings={summary.get('avg_awakenings')}, screen={summary.get('avg_screen_time_min')}min, efficiency={summary.get('sleep_efficiency')}%

        Please respond with:
        1) Brief patterns you notice and their likely impact on sleep (caffeine timing, alcohol near bedtime, evening screens).
        2) 2–3 tailored, simple suggestions the user can try next week (e.g., adjust caffeine cut-off, reduce alcohol close to bed, screen curfew).
        3) Keep it friendly, actionable, and concise. Avoid medical language.
        """

        llm_response = await generate_gemini_text(prompt)

        # Data-driven fallback if Gemini fails
        recommendations: List[str] = []
        if not llm_response:
            if caffeine_days > 0:
                cut_hour = "2pm" if caffeine_days / max(total_days, 1) >= 0.5 else "3pm"
                recommendations.append(f"Stop caffeine after {cut_hour} and track whether sleep onset improves.")
            if alcohol_days > 0:
                recommendations.append("Avoid alcohol within 3–4 hours of bedtime to reduce awakenings.")
            if high_screen_days > 0:
                recommendations.append("Set a 60–90 minute screen curfew before bed (use warm/dim lighting).")
            if not recommendations:
                recommendations.append("Keep a regular sleep schedule and aim for consistent wind-down routines.")

            llm_response = (
                f"Here's what your recent logs suggest: caffeine after 3pm on {caffeine_days}/{total_days} nights, "
                f"alcohol on {alcohol_days}/{total_days}, and higher pre-bed screen time on {high_screen_days}/{total_days}. "
                "These can delay sleep and fragment rest. Try the suggestions below for the next week to see what helps.\n\n"
                + "\n".join(f"• {r}" for r in recommendations)
            )
        else:
            # Optionally keep a simple heuristic list for transparency even with LLM
            if caffeine_days > 0:
                recommendations.append("Limit caffeine to the morning/early afternoon (cut-off 2–3pm).")
            if alcohol_days > 0:
                recommendations.append("Avoid alcohol within 3–4 hours of bedtime.")
            if high_screen_days > 0:
                recommendations.append("Create an evening screen curfew (60–90 minutes before bed).")

        text = f"{llm_response.strip()}\n\n{DISCLAIMER}"
        return {
            "agent": self.name,
            "text": text,
            "data": {
                "summary": summary,
                "sample": logs[-3:],
                "recommendations": recommendations[:3] if recommendations else []
            }
        }
