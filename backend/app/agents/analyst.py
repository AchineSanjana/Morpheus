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

def _find_correlations(logs: List[Dict[str, Any]]) -> List[str]:
    """Analyzes logs to find correlations between habits and sleep quality."""
    insights = []
    
    # Add duration_h to logs for correlation analysis
    for log in logs:
        bt = _to_dt(log.get("bedtime"))
        wt = _to_dt(log.get("wake_time"))
        if bt and wt:
            log["duration_h"] = (wt - bt).total_seconds() / 3600.0
        else:
            log["duration_h"] = None

    # 1. Caffeine analysis
    caffeine_logs = [log for log in logs if log.get("caffeine_after3pm") and log.get("duration_h") is not None]
    no_caffeine_logs = [log for log in logs if not log.get("caffeine_after3pm") and log.get("duration_h") is not None]

    if len(caffeine_logs) >= 2 and len(no_caffeine_logs) >= 2:
        avg_dur_caffeine = _avg([log["duration_h"] for log in caffeine_logs])
        avg_dur_no_caffeine = _avg([log["duration_h"] for log in no_caffeine_logs])
        if avg_dur_caffeine is not None and avg_dur_no_caffeine is not None:
            diff = avg_dur_no_caffeine - avg_dur_caffeine
            if abs(diff) > 0.25: # Only show if difference is > 15 mins
                comparison = "more" if diff > 0 else "less"
                insights.append(f"On days without late caffeine, you slept **{abs(diff):.1f} hours {comparison}** on average.")

    # 2. Alcohol analysis
    alcohol_logs = [log for log in logs if log.get("alcohol") and log.get("awakenings") is not None]
    no_alcohol_logs = [log for log in logs if not log.get("alcohol") and log.get("awakenings") is not None]
    
    if len(alcohol_logs) >= 1 and len(no_alcohol_logs) >= 2:
        avg_awakenings_alcohol = _avg([log.get("awakenings", 0) for log in alcohol_logs])
        avg_awakenings_no_alcohol = _avg([log.get("awakenings", 0) for log in no_alcohol_logs])
        if avg_awakenings_alcohol is not None and avg_awakenings_no_alcohol is not None:
            if avg_awakenings_alcohol > avg_awakenings_no_alcohol + 0.5:
                insights.append(f"You had **more awakenings** on nights you drank alcohol.")

    # 3. Screen time analysis
    high_screen_logs = [log for log in logs if log.get("screen_time_min", 0) > 60 and log.get("duration_h") is not None]
    low_screen_logs = [log for log in logs if log.get("screen_time_min", 0) <= 60 and log.get("duration_h") is not None]

    if len(high_screen_logs) >= 2 and len(low_screen_logs) >= 2:
        avg_dur_high_screen = _avg([log["duration_h"] for log in high_screen_logs])
        avg_dur_low_screen = _avg([log["duration_h"] for log in low_screen_logs])
        if avg_dur_high_screen is not None and avg_dur_low_screen is not None:
            diff = avg_dur_low_screen - avg_dur_high_screen
            if diff > 0.25:
                insights.append(f"On nights with less screen time (<60min), you slept **{diff:.1f} hours longer**.")

    # 4. Bedtime consistency analysis
    bedtimes = [_to_dt(log.get("bedtime")) for log in logs if _to_dt(log.get("bedtime"))]
    if len(bedtimes) >= 4:
        # Calculate average bedtime (circular mean)
        minutes_in_day = 24 * 60
        radians = [(x.hour * 60 + x.minute) / minutes_in_day * 2 * math.pi for x in bedtimes]
        sin_avg = mean([math.sin(r) for r in radians])
        cos_avg = mean([math.cos(r) for r in radians])
        avg_rad = math.atan2(sin_avg, cos_avg)
        avg_total_minutes = (avg_rad / (2 * math.pi)) * minutes_in_day
        if avg_total_minutes < 0: avg_total_minutes += minutes_in_day

        consistent_logs = []
        inconsistent_logs = []
        for log in logs:
            bt = _to_dt(log.get("bedtime"))
            if not bt or log.get("duration_h") is None: continue
            
            log_total_minutes = bt.hour * 60 + bt.minute
            # Handle overnight wrap-around for comparison
            diff = abs(log_total_minutes - avg_total_minutes)
            minute_diff = min(diff, minutes_in_day - diff)

            if minute_diff <= 45: # Within a 45-min window of average
                consistent_logs.append(log)
            else:
                inconsistent_logs.append(log)
        
        if len(consistent_logs) >= 2 and len(inconsistent_logs) >= 2:
            avg_dur_consistent = _avg([log["duration_h"] for log in consistent_logs])
            avg_dur_inconsistent = _avg([log["duration_h"] for log in inconsistent_logs])
            if avg_dur_consistent is not None and avg_dur_inconsistent is not None:
                diff = avg_dur_consistent - avg_dur_inconsistent
                if diff > 0.25:
                    insights.append(f"When your bedtime was consistent, you slept **{diff:.1f} hours longer** on average.")

    return insights

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

        # --- NEW: Find correlations ---
        correlations = _find_correlations(logs)
        insights_text = ""
        if correlations:
            insights_list = "\n".join(f"• {insight}" for insight in correlations)
            insights_text = f"\n**Key Insights & Predictions**\n{insights_list}\n"
        # --- END NEW ---

        text = (
            f"**7-day snapshot**\n"
            f"• Sleep duration ≈ {summary['avg_duration_h']} h/night\n"
            f"• Awakenings ≈ {summary['avg_awakenings']}\n"
            f"• Screen time before bed ≈ {summary['avg_screen_min']} min\n"
            f"• Bedtime consistency ±{summary['bedtime_consistency_min']} min; "
            f"Wake consistency ±{summary['wake_consistency_min']} min\n"
            f"{insights_text}"
            f"Ask me: “Why was this week different?” or “Make me a plan.”"
        )
        return {"agent": self.name, "text": text, "data": {"summary": summary, "sample": logs[-3:]}}
