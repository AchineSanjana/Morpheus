from typing import Optional, List, Dict, Any
from statistics import mean
from datetime import datetime
import math
from . import BaseAgent, AgentContext, AgentResponse
from app.db import fetch_recent_logs

def _to_dt(x: Any) -> Optional[datetime]:
    """Parse various datetime formats to datetime object."""
    if isinstance(x, datetime):
        return x
    if isinstance(x, str):
        try:
            return datetime.fromisoformat(x.replace('Z', '+00:00'))
        except:
            return None
    return None

def _avg(nums: List[float]) -> Optional[float]:
    """Safe average calculation."""
    return round(mean(nums), 1) if nums else None


class AnalyticsAgent(BaseAgent):
    """
    Analytics agent for Morpheus Sleep AI.
    
    Functionality:
    - Analyzes user sleep logs to extract patterns, trends, and actionable insights.
    - Calculates averages, trends (improving/worsening/stable), and consistency ratings.
    - Provides recommendations based on detected sleep issues and progress.
    - Ensures responsible AI transparency by logging analysis actions.
    
    Key attributes:
    - name: Agent identifier ('analytics')
    - action_type: Used for responsible AI logging and transparency
    """
    name = "analytics"

    def __init__(self):
        super().__init__()
        self.action_type = "data_analysis"  # Used for responsible AI transparency

    # ...existing code...

    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate if values are improving, worsening, or stable."""
        if len(values) < 3:
            return "stable"
        
        # Simple linear trend analysis
        first_half = sum(values[:len(values)//2]) / (len(values)//2)
        second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
        
        diff = second_half - first_half
        if abs(diff) < 0.2:
            return "stable"
        elif diff > 0:
            return "improving" if "duration" in str(values) else "worsening"  # More awakenings = worse
        else:
            return "worsening" if "duration" in str(values) else "improving"

    def _calculate_consistency_rating(self, times: List[int]) -> Dict[str, Any]:
        """Calculate timing consistency with detailed rating."""
        if len(times) < 2:
            return {"avg_deviation": 0, "rating": "excellent", "description": "Perfect consistency"}
        
        avg_time = sum(times) / len(times)
        deviations = [abs(t - avg_time) for t in times]
        avg_deviation = sum(deviations) / len(deviations)
        
        if avg_deviation < 30:
            rating = "excellent"
            description = "Very consistent timing"
        elif avg_deviation < 60:
            rating = "good"
            description = "Mostly consistent"
        elif avg_deviation < 90:
            rating = "fair"
            description = "Some variability"
        else:
            rating = "needs improvement"
            description = "Highly variable timing"
            
        return {
            "avg_deviation": round(avg_deviation),
            "rating": rating,
            "description": description
        }

    def _calculate_sleep_efficiency(self, logs: List[Dict[str, Any]]) -> Optional[float]:
        """Calculate sleep efficiency percentage."""
        efficiency_scores = []
        
        for log in logs:
            if log.get("duration_h") and log.get("awakenings") is not None:
                # Efficiency: actual sleep time / time in bed
                sleep_time = log["duration_h"] * 60  # minutes
                wake_time = log["awakenings"] * 15  # assume 15min per awakening
                total_time = sleep_time + wake_time
                
                if total_time > 0:
                    efficiency = (sleep_time / total_time) * 100
                    efficiency_scores.append(min(efficiency, 100))  # Cap at 100%
        
        return round(sum(efficiency_scores) / len(efficiency_scores), 1) if efficiency_scores else None

    def _identify_patterns_and_insights(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Identify key patterns and generate insights."""
        insights = {
            "strengths": [],
            "concerns": [],
            "recommendations": [],
            "notable_patterns": []
        }
        
        if not logs:
            return insights
        
        # Duration analysis
        durations = [log.get("duration_h") for log in logs if log.get("duration_h")]
        if durations:
            avg_duration = sum(durations) / len(durations)
            short_nights = sum(1 for d in durations if d < 6.5)
            long_nights = sum(1 for d in durations if d > 9)
            
            if avg_duration >= 7.5:
                insights["strengths"].append(f"Good average sleep duration ({avg_duration:.1f}h)")
            elif avg_duration < 6.5:
                insights["concerns"].append(f"Insufficient sleep duration ({avg_duration:.1f}h average)")
                insights["recommendations"].append("Aim for 7-9 hours nightly by adjusting bedtime")
            
            if short_nights > len(logs) * 0.4:
                insights["concerns"].append(f"Frequent short nights ({short_nights}/{len(logs)} nights <6.5h)")
        
        # Awakening analysis
        awakenings = [log.get("awakenings", 0) for log in logs]
        avg_awakenings = sum(awakenings) / len(awakenings)
        
        if avg_awakenings <= 1:
            insights["strengths"].append("Good sleep continuity (low awakenings)")
        elif avg_awakenings >= 3:
            insights["concerns"].append(f"Fragmented sleep ({avg_awakenings:.1f} awakenings/night)")
            insights["recommendations"].append("Focus on sleep environment optimization")
        
        # Lifestyle factor analysis
        caffeine_nights = sum(1 for log in logs if log.get("caffeine_after3pm"))
        alcohol_nights = sum(1 for log in logs if log.get("alcohol"))
        # Nicotine may not exist in schema; support common keys if present
        nicotine_keys = ("nicotine", "nicotine_use", "tobacco", "smoked", "cigarettes")
        def _has_nicotine(l: Dict[str, Any]) -> bool:
            for k in nicotine_keys:
                if k in l:
                    v = l.get(k)
                    # treat truthy bools or positive numbers as nicotine use
                    if isinstance(v, (int, float)):
                        if v > 0:
                            return True
                    elif isinstance(v, str):
                        if v.strip().lower() in {"yes", "true", "y", "1"}:
                            return True
                    elif v:  # truthy
                        return True
            return False
        nicotine_nights = sum(1 for log in logs if _has_nicotine(log))
        high_screen_nights = sum(1 for log in logs if log.get("screen_time_min", 0) > 60)
        
        if caffeine_nights > len(logs) * 0.5:
            insights["concerns"].append(f"Frequent late caffeine ({caffeine_nights}/{len(logs)} nights)")
            insights["recommendations"].append("Avoid caffeine after 2pm for better sleep onset")
        
        if alcohol_nights > len(logs) * 0.3:
            insights["notable_patterns"].append(f"Alcohol consumption on {alcohol_nights}/{len(logs)} nights")
            insights["recommendations"].append("Consider alcohol's impact on sleep quality; avoid alcohol 3–4 hours before bed")

        # Nicotine insights (if any nicotine data is present in logs)
        if nicotine_nights > 0:
            if nicotine_nights > len(logs) * 0.3:
                insights["concerns"].append(f"Nicotine use on {nicotine_nights}/{len(logs)} nights")
                insights["recommendations"].append("Avoid nicotine within 3–4 hours of bedtime; reduce overall use for sleep quality")
            else:
                insights["notable_patterns"].append(f"Occasional nicotine use on {nicotine_nights}/{len(logs)} nights")
        
        if high_screen_nights > len(logs) * 0.4:
            insights["concerns"].append(f"Excessive screen time ({high_screen_nights}/{len(logs)} nights >60min)")
            insights["recommendations"].append("Implement screen curfew 1-2 hours before bed")
        
        return insights

    def _generate_trend_analysis(self, logs: List[Dict[str, Any]]) -> List[str]:
        """Generate trend analysis as a list of individual trends."""
        if len(logs) < 3:
            return ["Need more data for trend analysis"]
        
        # Analyze recent vs older data
        mid_point = len(logs) // 2
        recent_logs = logs[mid_point:]
        older_logs = logs[:mid_point]
        
        recent_duration = _avg([log.get("duration_h") for log in recent_logs if log.get("duration_h")])
        older_duration = _avg([log.get("duration_h") for log in older_logs if log.get("duration_h")])
        
        recent_awakenings = _avg([log.get("awakenings", 0) for log in recent_logs])
        older_awakenings = _avg([log.get("awakenings", 0) for log in older_logs])
        
        trends = []
        
        if recent_duration and older_duration:
            duration_change = recent_duration - older_duration
            if abs(duration_change) > 0.3:
                direction = "increased" if duration_change > 0 else "decreased"
                trends.append(f"Sleep duration has {direction} by {abs(duration_change):.1f}h recently")
        
        if recent_awakenings and older_awakenings:
            awakening_change = recent_awakenings - older_awakenings
            if abs(awakening_change) > 0.5:
                direction = "increased" if awakening_change > 0 else "decreased"
                trends.append(f"Night awakenings have {direction} recently")
        
        return trends if trends else ["Sleep patterns are relatively stable"]

    def _generate_predictive_insights(self, logs: List[Dict[str, Any]], summary: Dict[str, Any]) -> str:
        """Generate predictive insights based on recent patterns"""
        insights = []
        
        # Trend-based predictions
        recent_logs = logs[-3:] if len(logs) >= 3 else logs
        duration_trend = self._calculate_trend([log.get("duration_h", 0) for log in logs[-7:] if log.get("duration_h")])
        
        if duration_trend == "improving":
            insights.append("• Your sleep duration trend is **improving** - maintain current habits!")
        elif duration_trend == "worsening":
            insights.append("• Your sleep duration is **declining** - consider earlier bedtimes")
        
        # Lifestyle factor predictions
        recent_caffeine = sum(1 for log in recent_logs if log.get("caffeine_after3pm"))
        recent_alcohol = sum(1 for log in recent_logs if log.get("alcohol"))
        
        if recent_caffeine > len(recent_logs) * 0.5:
            insights.append("• **Risk alert:** Frequent late caffeine may continue impacting sleep quality")
        
        if recent_alcohol > 0:
            insights.append("• **Consider:** Alcohol-free nights to improve sleep depth and continuity")
        
        # Weekly pattern prediction
        avg_duration = summary.get("avg_duration", 0)
        if avg_duration > 0:
            if avg_duration >= 7.5:
                insights.append("• **Forecast:** Continue current routine for sustained good sleep")
            elif avg_duration < 6.5:
                insights.append("• **Recommendation:** Add 30-60 minutes to nightly sleep target")
        
        # Consistency prediction
        bedtime_consistency = summary.get("bedtime_consistency", {}).get("rating", "")
        if bedtime_consistency == "needs improvement":
            insights.append("• **Focus area:** Improving schedule consistency will enhance sleep quality")
        
        return "\n".join(insights) if insights else "Continue tracking for personalized predictions!"

    def _generate_predictive_insights(self, logs: List[Dict[str, Any]], summary: Dict[str, Any]) -> str:
        """Generate predictive insights based on recent patterns"""
        insights = []
        
        # Trend-based predictions
        recent_logs = logs[-3:] if len(logs) >= 3 else logs
        duration_trend = self._calculate_trend([log.get("duration_h", 0) for log in logs[-7:] if log.get("duration_h")])
        
        if duration_trend == "improving":
            insights.append("• Your sleep duration trend is **improving** - maintain current habits!")
        elif duration_trend == "worsening":
            insights.append("• Your sleep duration is **declining** - consider earlier bedtimes")
        
        # Lifestyle factor predictions
        recent_caffeine = sum(1 for log in recent_logs if log.get("caffeine_after3pm"))
        recent_alcohol = sum(1 for log in recent_logs if log.get("alcohol"))
        
        if recent_caffeine > len(recent_logs) * 0.5:
            insights.append("• **Risk alert:** Frequent late caffeine may continue impacting sleep quality")
        
        if recent_alcohol > 0:
            insights.append("• **Consider:** Alcohol-free nights to improve sleep depth and continuity")
        
        # Weekly pattern prediction
        avg_duration = summary.get("avg_duration", 0)
        if avg_duration > 0:
            if avg_duration >= 7.5:
                insights.append("• **Forecast:** Continue current routine for sustained good sleep")
            elif avg_duration < 6.5:
                insights.append("• **Recommendation:** Add 30-60 minutes to nightly sleep target")
        
        # Consistency prediction
        bedtime_consistency = summary.get("bedtime_consistency", {}).get("rating", "")
        if bedtime_consistency == "needs improvement":
            insights.append("• **Focus area:** Improving schedule consistency will enhance sleep quality")
        
        return "\n".join(insights) if insights else "Continue tracking for personalized predictions!"

    async def _handle_core(self, message: str, ctx: Optional[AgentContext] = None) -> AgentResponse:
        """Generate comprehensive 7-day sleep analytics with trends and insights."""
        ctx = ctx or {}
        user = ctx.get("user")
        if not user:
            return {"agent": self.name, "text": "Please sign in first so I can access your sleep data."}

        logs: List[Dict[str, Any]] = ctx.get("logs") or await fetch_recent_logs(user["id"], days=7)
        if not logs:
            return {"agent": self.name, "text": "No sleep data found for the last 7 days. Start logging your sleep to get insights!"}

        # Extract data for analysis
        durations_h = [r.get("duration_h") for r in logs if r.get("duration_h")]
        awakenings = [r.get("awakenings", 0) for r in logs]
        screen_time = [r.get("screen_time_min", 0) for r in logs]
        bedtimes = [_to_dt(r.get("bedtime")) for r in logs if _to_dt(r.get("bedtime"))]
        waketimes = [_to_dt(r.get("wake_time")) for r in logs if _to_dt(r.get("wake_time"))]

        # Lifestyle factors (explicitly compute alcohol and nicotine series)
        alcohol_flags = [bool(r.get("alcohol")) for r in logs]
        nicotine_keys = ("nicotine", "nicotine_use", "tobacco", "smoked", "cigarettes")
        def _has_nicotine(l: Dict[str, Any]) -> bool:
            for k in nicotine_keys:
                if k in l:
                    v = l.get(k)
                    if isinstance(v, (int, float)) and v > 0:
                        return True
                    if isinstance(v, str) and v.strip().lower() in {"yes", "true", "y", "1"}:
                        return True
                    if isinstance(v, bool) and v:
                        return True
            return False
        nicotine_flags = [_has_nicotine(r) for r in logs]

        # Calculate core metrics
        avg_duration = _avg(durations_h)
        avg_awakenings = _avg(awakenings)
        avg_screen_time = _avg(screen_time)
        
        # Sleep efficiency
        sleep_efficiency = self._calculate_sleep_efficiency(logs)
        
        # Timing consistency
        bedtime_mins = [(bt.hour * 60 + bt.minute) % (24 * 60) for bt in bedtimes]
        waketime_mins = [(wt.hour * 60 + wt.minute) % (24 * 60) for wt in waketimes]
        
        bedtime_consistency = self._calculate_consistency_rating(bedtime_mins)
        waketime_consistency = self._calculate_consistency_rating(waketime_mins)
        
        # Insights and patterns
        insights = self._identify_patterns_and_insights(logs)
        trend_analysis = self._generate_trend_analysis(logs)
        
    # Build comprehensive report as a single formatted string
        report_parts = []
        
        # Header
        report_parts.append(f"📊 **7-Day Sleep Analysis** ({len(logs)} nights logged)\n")
        
        # Core Metrics Section
        report_parts.append("**📈 Key Metrics:**\n")
        if avg_duration:
            quality = "excellent" if avg_duration >= 8 else "good" if avg_duration >= 7 else "needs improvement"
            report_parts.append(f"• **Sleep Duration**: {avg_duration}h avg ({quality}) 🌙\n")
        
        if avg_awakenings is not None:
            quality = "excellent" if avg_awakenings <= 1 else "good" if avg_awakenings <= 2 else "concerning"
            report_parts.append(f"• **Night Awakenings**: {avg_awakenings} avg ({quality}) 💤\n")
        
        if sleep_efficiency:
            quality = "excellent" if sleep_efficiency >= 85 else "good" if sleep_efficiency >= 75 else "needs improvement"
            report_parts.append(f"• **Sleep Efficiency**: {sleep_efficiency}% ({quality}) 🎯\n")
        
        if avg_screen_time is not None:
            quality = "good" if avg_screen_time <= 30 else "moderate" if avg_screen_time <= 60 else "high"
            report_parts.append(f"• **Pre-bed Screen Time**: {avg_screen_time}min ({quality}) 📱\n")

        # Alcohol & Nicotine summary
        alcohol_nights = sum(1 for f in alcohol_flags if f)
        nicotine_nights = sum(1 for f in nicotine_flags if f)
        report_parts.append("\n**🍷 Alcohol & 🚬 Nicotine:**\n")
        report_parts.append(f"• **Alcohol nights**: {alcohol_nights}/{len(logs)}\n")
        if any(nicotine_flags):
            report_parts.append(f"• **Nicotine nights**: {nicotine_nights}/{len(logs)}\n")
        else:
            report_parts.append("• **Nicotine nights**: no data logged\n")

        # Optional correlation snapshots
        def _avg_on(mask: List[bool], series: List[float]) -> Optional[float]:
            vals = [series[i] for i, m in enumerate(mask) if m and series[i] is not None]
            return round(sum(vals)/len(vals), 2) if vals else None
        def _avg_on_int(mask: List[bool], series: List[int]) -> Optional[float]:
            vals = [series[i] for i, m in enumerate(mask) if m]
            return round(sum(vals)/len(vals), 2) if vals else None

        if len(logs) >= 3:
            dur_on_alc = _avg_on(alcohol_flags, [r.get("duration_h") for r in logs])
            dur_off_alc = _avg_on([not f for f in alcohol_flags], [r.get("duration_h") for r in logs])
            awk_on_alc = _avg_on_int(alcohol_flags, [int(r.get("awakenings", 0)) for r in logs])
            awk_off_alc = _avg_on_int([not f for f in alcohol_flags], [int(r.get("awakenings", 0)) for r in logs])
            alc_corr_lines = []
            if dur_on_alc is not None and dur_off_alc is not None:
                diff = round(dur_on_alc - dur_off_alc, 2)
                if abs(diff) >= 0.2:
                    direction = "shorter" if diff < 0 else "longer"
                    alc_corr_lines.append(f"On alcohol nights, sleep tends to be {abs(diff)}h {direction}.")
            if awk_on_alc is not None and awk_off_alc is not None:
                diff = round(awk_on_alc - awk_off_alc, 2)
                if abs(diff) >= 0.3:
                    direction = "more" if diff > 0 else "fewer"
                    alc_corr_lines.append(f"On alcohol nights, there are {abs(diff)} {direction} awakenings.")
            if alc_corr_lines:
                report_parts.append("\n**🔍 Alcohol correlation:**\n" + "\n".join(f"• {l}" for l in alc_corr_lines) + "\n")

            if any(nicotine_flags):
                dur_on_nic = _avg_on(nicotine_flags, [r.get("duration_h") for r in logs])
                dur_off_nic = _avg_on([not f for f in nicotine_flags], [r.get("duration_h") for r in logs])
                awk_on_nic = _avg_on_int(nicotine_flags, [int(r.get("awakenings", 0)) for r in logs])
                awk_off_nic = _avg_on_int([not f for f in nicotine_flags], [int(r.get("awakenings", 0)) for r in logs])
                nic_corr_lines = []
                if dur_on_nic is not None and dur_off_nic is not None:
                    diff = round(dur_on_nic - dur_off_nic, 2)
                    if abs(diff) >= 0.2:
                        direction = "shorter" if diff < 0 else "longer"
                        nic_corr_lines.append(f"On nicotine nights, sleep tends to be {abs(diff)}h {direction}.")
                if awk_on_nic is not None and awk_off_nic is not None:
                    diff = round(awk_on_nic - awk_off_nic, 2)
                    if abs(diff) >= 0.3:
                        direction = "more" if diff > 0 else "fewer"
                        nic_corr_lines.append(f"On nicotine nights, there are {abs(diff)} {direction} awakenings.")
                if nic_corr_lines:
                    report_parts.append("\n**🔍 Nicotine correlation:**\n" + "\n".join(f"• {l}" for l in nic_corr_lines) + "\n")
        
        # Schedule Consistency Section
        report_parts.append("\n**⏰ Schedule Consistency:**\n")
        if bedtime_consistency:
            report_parts.append(f"• **Bedtime**: {bedtime_consistency['description']} (±{bedtime_consistency['avg_deviation']}min)\n")
        if waketime_consistency:
            report_parts.append(f"• **Wake Time**: {waketime_consistency['description']} (±{waketime_consistency['avg_deviation']}min)\n")
        
        # Recent Trends Section
        if trend_analysis and trend_analysis != ["Sleep patterns are relatively stable"]:
            report_parts.append("\n**📈 Recent Trends:**\n")
            for trend in trend_analysis:
                report_parts.append(f"• {trend}\n")
        
        # Strengths Section
        if insights["strengths"]:
            report_parts.append("\n**🏆 Strengths:**\n")
            for strength in insights["strengths"]:
                report_parts.append(f"• {strength}\n")
        
        # Areas for Improvement Section
        if insights["concerns"]:
            report_parts.append("\n**⚠️ Areas for Improvement:**\n")
            for concern in insights["concerns"]:
                report_parts.append(f"• {concern}\n")
        
        # Notable Patterns Section
        if insights["notable_patterns"]:
            report_parts.append("\n**📋 Notable Patterns:**\n")
            for pattern in insights["notable_patterns"]:
                report_parts.append(f"• {pattern}\n")
        
        # Recommendations Section
        if insights["recommendations"]:
            report_parts.append("\n**🎯 Recommendations:**\n")
            for rec in insights["recommendations"][:3]:  # Limit to top 3
                report_parts.append(f"• {rec}\n")
        
        # Footer
        report_parts.append("\n💡 *Ask me about specific sleep challenges for personalized coaching!*")
        
        # Join all parts into final report
        final_report = "".join(report_parts)
        
        # Create summary data for other agents
        summary = {
            "nights": len(logs),
            "avg_duration_h": avg_duration,
            "avg_awakenings": avg_awakenings,
            "avg_screen_time_min": avg_screen_time,
            "sleep_efficiency": sleep_efficiency,
            "bedtime_consistency": bedtime_consistency,
            "waketime_consistency": waketime_consistency,
            "insights": insights,
            "alcohol_nights": alcohol_nights,
            "nicotine_nights": nicotine_nights,
            "trends": trend_analysis
        }
        
        # Add predictive insights if we have enough data
        if len(logs) >= 7:
            predictive_insights = self._generate_predictive_insights(logs, summary)
            final_report += f"\n\n**🔮 Predictive Insights:**\n{predictive_insights}\n"
        
        return {
            "agent": self.name, 
            "text": final_report,
            "data": {"summary": summary, "logs": logs[-3:]}  # Include recent logs for context
        }