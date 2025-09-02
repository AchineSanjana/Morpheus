from typing import Optional, List, Dict, Any
from statistics import mean
from datetime import datetime
from . import BaseAgent, AgentContext, AgentResponse
from app.db import fetch_recent_logs
import math

def _to_dt(x: Any) -> Optional[datetime]:
    if isinstance(x, datetime):
        return x
    if isinstance(x, str):
        try:
            return datetime.fromisoformat(x)
        except Exception:
            return None
    return None

def _avg(nums: List[float]) -> Optional[float]:
    nums = [n for n in nums if isinstance(n, (int, float))]
    return round(mean(nums), 2) if nums else None

class AnalyticsAgent(BaseAgent):
    """
    Turns raw logs into digestible insights (duration, awakenings, consistency, etc.).
    """
    name = "analytics"

    async def handle(self, message: str, ctx: Optional[AgentContext] = None) -> AgentResponse:
        ctx = ctx or {}
        user = ctx.get("user")
        if not user:
            return {"agent": self.name, "text": "Please sign in first so I can read your logs."}

        logs: List[Dict[str, Any]] = ctx.get("logs") or await fetch_recent_logs(user["id"], days=7)
        if not logs:
            return {"agent": self.name, "text": "I couldn’t find logs in the last 7 days."}

        durations_h: List[float] = []
        awakenings: List[int] = []
        screen_min: List[int] = []
        bedtimes: List[datetime] = []
        waketimes: List[datetime] = []

        for r in logs:
            bt = _to_dt(r.get("bedtime"))
            wt = _to_dt(r.get("wake_time"))
            if bt: bedtimes.append(bt)
            if wt: waketimes.append(wt)
            if bt and wt:
                durations_h.append((wt - bt).total_seconds() / 3600.0)
            awakenings.append(int(r.get("awakenings", 0) or 0))
            screen_min.append(int(r.get("screen_time_min", 0) or 0))

        summary = {
            "nights": len(logs),
            "avg_duration_h": _avg(durations_h),
            "avg_awakenings": _avg(awakenings),
            "avg_screen_min": _avg(screen_min),
        }

        # simple “consistency” proxy = std-like spread of bedtimes (minutes)
        def _spread_mins(xs: List[datetime]) -> Optional[int]:
            if len(xs) < 2:
                return None
            # Convert time to radians for circular mean calculation
            minutes_in_day = 24 * 60
            radians = [(x.hour * 60 + x.minute) / minutes_in_day * 2 * math.pi for x in xs]
            
            sin_avg = mean([math.sin(r) for r in radians])
            cos_avg = mean([math.cos(r) for r in radians])
            
            # If all times are the same, r will be 1 and math.log(r) will be 0.
            # If times are very spread, r will be close to 0, and math.log(r) will be a large negative number.
            # Add a small epsilon to avoid math domain error if r is slightly > 1.0 due to float precision.
            r = min(math.sqrt(sin_avg**2 + cos_avg**2), 1.0)
            if r == 1.0:
                return 0 # No spread

            std_dev_rad = math.sqrt(-2 * math.log(r))
            
            # Convert standard deviation from radians to minutes
            spread_minutes = (std_dev_rad / (2 * math.pi)) * minutes_in_day
            return round(spread_minutes)

        summary["bedtime_consistency_min"] = _spread_mins(bedtimes)
        summary["wake_consistency_min"] = _spread_mins(waketimes)

        text = (
            f"**7-day snapshot**\n"
            f"• Sleep duration ≈ {summary['avg_duration_h']} h/night\n"
            f"• Awakenings ≈ {summary['avg_awakenings']}\n"
            f"• Screen time before bed ≈ {summary['avg_screen_min']} min\n"
            f"• Bedtime consistency ±{summary['bedtime_consistency_min']} min; "
            f"Wake consistency ±{summary['wake_consistency_min']} min\n\n"
            f"Ask me: “Why was this week different?” or “Make me a plan.”"
        )
        return {"agent": self.name, "text": text, "data": {"summary": summary, "sample": logs[-3:]}}
