from .db import supabase

def classify_intent(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ["analyz", "why", "trend", "week"]): return "analytics"
    if any(k in t for k in ["plan", "improve", "tips", "advice"]): return "coach"
    if any(k in t for k in ["what is", "explain", "meaning", "define"]): return "ir"
    return "coordinator"

def ir_agent(query: str) -> str:
    return ("Here’s a quick explanation based on our sleep knowledge notes. "
            "Keep a consistent bedtime/wake, cut caffeine after 3pm, and dim screens 60 mins before bed.")

def analytics_agent(user_id: str) -> str:
    res = supabase.table("sleep_logs").select("*").eq("user_id", user_id)\
                   .order("date", desc=True).limit(7).execute()
    logs = res.data or []
    if not logs:
        return "I don’t have sleep logs yet. Save last night and I’ll analyze your trends."
    n = len(logs)
    avg_screen = int(sum((l.get("screen_time_min") or 0) for l in logs)/n)
    return f"In your last {n} nights, average screen time before bed ≈ {avg_screen} min. Let’s aim under 30."

def coach_agent(user_id: str) -> str:
    return ("1-week plan:\n"
            "• Fix a target bedtime & wake time (±15 min).\n"
            "• Avoid caffeine after 3pm.\n"
            "• 60-min wind-down without screens.\n"
            "• If awake >20 min at night, leave bed until sleepy.")