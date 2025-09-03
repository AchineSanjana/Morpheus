from typing import Optional, Dict, Any
from . import BaseAgent, AgentContext, AgentResponse
from app.llm_gemini import generate_gemini_text

DISCLAIMER = (
    "This is educational guidance (not medical care). If you have severe trouble sleeping, "
    "loud snoring, breathing pauses, or insomnia >3 months, talk to a clinician."
)

RED_FLAGS = [
    ("apnea", ["snore", "gasp", "stop breathing"]),
    ("chronic_insomnia", ["> 3 months", "three months", "3 months"]),
]

def _plan_from_summary(summary: Dict[str, Any]) -> list[str]:
    tips: list[str] = []
    dur = summary.get("avg_duration_h")
    awak = summary.get("avg_awakenings")
    screen = summary.get("avg_screen_min")
    bed_spread = summary.get("bedtime_consistency_min")

    tips.append("Pick a **fixed wake-up time** and stick to it daily (anchor the clock).")
    tips.append("Start a **60–90 min wind-down** routine (dim lights, paper book, stretch, journal).")
    tips.append("Keep the bedroom **cool, dark, quiet**; bed for sleep only.")

    if screen and screen > 30:
        tips.append("Reduce screens in the last hour before bed; if needed, use night-shift + dim.")
    if dur and dur < 7.0:
        tips.append("Target **7–9 hours** in bed; shift in 15–30 min steps over a few nights.")
    if awak and awak >= 2:
        tips.append("If awake >20 min, do a brief reset in dim light, then return to bed.")
    if bed_spread and bed_spread > 45:
        tips.append("Tighten timing: keep bedtime within a **±30–45 min** window for a week.")

    tips.append("Avoid caffeine after **3 pm** and big meals late at night.")
    tips.append("Get **morning daylight** and some daytime movement (even a 10–20 min walk).")
    return tips

class CoachAgent(BaseAgent):
    """
    CBT-I style, gentle & actionable. Also adds lightweight safety guardrails.
    """
    name = "coach"

    def _flag_safety(self, message: str) -> list[str]:
        t = message.lower()
        hits = []
        for label, keys in RED_FLAGS:
            if any(k in t for k in keys):
                hits.append(label)
        return hits

    async def handle(self, message: str, ctx: Optional[AgentContext] = None) -> AgentResponse:
        ctx = ctx or {}
        summary = (ctx.get("analysis") or {}).get("summary")
        
        llm_response = None
        if summary:
            # If we have a data summary, ask the LLM to create a full, personalized plan.
            prompt = f"""
            You are a friendly, encouraging, and expert sleep coach.
            A user has asked for a sleep plan. Based on their 7-day sleep summary below, create a personalized and actionable sleep improvement plan.

            Your response should have three parts:
            1.  **A brief, positive opening (1-2 sentences):** Acknowledge their data and frame the opportunity for improvement positively.
            2.  **A prioritized action plan (3-5 bullet points):** Identify the most important areas for improvement from the data and provide specific, actionable tips. For each tip, briefly explain *why* it's important based on their data.
            3.  **A concluding sentence:** Offer encouragement.

            **User's 7-Day Sleep Summary:**
            - Average Sleep Duration: {summary.get('avg_duration_h', 'N/A')} hours/night
            - Average Awakenings: {summary.get('avg_awakenings', 'N/A')} per night
            - Average Screen Time Before Bed: {summary.get('avg_screen_min', 'N/A')} minutes
            - Bedtime Consistency: ±{summary.get('bedtime_consistency_min', 'N/A')} minutes
            - Wake Time Consistency: ±{summary.get('wake_consistency_min', 'N/A')} minutes

            Generate the full response now.
            """
            llm_response = await generate_gemini_text(prompt)

        # Fallback to the old rule-based plan if the LLM fails or there's no summary
        if not llm_response:
            tips = _plan_from_summary(summary if isinstance(summary, dict) else {})
            plan = "\n".join(f"• {t}" for t in tips)
            llm_response = f"Here’s a 7-day plan based on your recent logs:\n{plan}"

        final_text = f"{llm_response.strip()}\n\n_{DISCLAIMER}_"

        safety = self._flag_safety(message)
        if safety:
            final_text += "\n\n**Safety:** Please consult a clinician for red-flag symptoms."
        return {"agent": self.name, "text": final_text, "data": {"safety": safety}}
