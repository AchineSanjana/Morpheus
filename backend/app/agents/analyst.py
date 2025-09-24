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
    Enhanced analytics agent that provides comprehensive sleep pattern analysis
    with trends, insights, and actionable recommendations.
    """
    name = "analytics"

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
        high_screen_nights = sum(1 for log in logs if log.get("screen_time_min", 0) > 60)
        
        if caffeine_nights > len(logs) * 0.5:
            insights["concerns"].append(f"Frequent late caffeine ({caffeine_nights}/{len(logs)} nights)")
            insights["recommendations"].append("Avoid caffeine after 2pm for better sleep onset")
        
        if alcohol_nights > len(logs) * 0.3:
            insights["notable_patterns"].append(f"Alcohol consumption on {alcohol_nights}/{len(logs)} nights")
            insights["recommendations"].append("Consider alcohol's impact on sleep quality")
        
        if high_screen_nights > len(logs) * 0.4:
            insights["concerns"].append(f"Excessive screen time ({high_screen_nights}/{len(logs)} nights >60min)")
            insights["recommendations"].append("Implement screen curfew 1-2 hours before bed")
        
        return insights

    def _generate_trend_analysis(self, logs: List[Dict[str, Any]]) -> str:
        """Generate trend analysis text."""
        if len(logs) < 3:
            return "Need more data for trend analysis."
        
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
        
        return "; ".join(trends) if trends else "Sleep patterns are relatively stable"

    async def handle(self, message: str, ctx: Optional[AgentContext] = None) -> AgentResponse:
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
        
        # Build comprehensive report
        report_sections = []
        
        # Header
        report_sections.append(f"📊 **7-Day Sleep Analysis** ({len(logs)} nights logged)")
        
        # Core Metrics
        metrics = []
        if avg_duration:
            quality = "excellent" if avg_duration >= 8 else "good" if avg_duration >= 7 else "needs improvement"
            metrics.append(f"⏱️ **Sleep Duration**: {avg_duration}h avg ({quality})")
        
        if avg_awakenings is not None:
            quality = "excellent" if avg_awakenings <= 1 else "good" if avg_awakenings <= 2 else "concerning"
            metrics.append(f"🌙 **Night Awakenings**: {avg_awakenings} avg ({quality})")
        
        if sleep_efficiency:
            quality = "excellent" if sleep_efficiency >= 85 else "good" if sleep_efficiency >= 75 else "needs improvement"
            metrics.append(f"💤 **Sleep Efficiency**: {sleep_efficiency}% ({quality})")
        
        if avg_screen_time is not None:
            quality = "good" if avg_screen_time <= 30 else "moderate" if avg_screen_time <= 60 else "high"
            metrics.append(f"📱 **Pre-bed Screen Time**: {avg_screen_time}min ({quality})")
        
        report_sections.extend(metrics)
        
        # Consistency Analysis
        report_sections.append("\n⏰ **Schedule Consistency**:")
        if bedtime_consistency:
            report_sections.append(f"  • Bedtime: {bedtime_consistency['description']} (±{bedtime_consistency['avg_deviation']}min)")
        if waketime_consistency:
            report_sections.append(f"  • Wake Time: {waketime_consistency['description']} (±{waketime_consistency['avg_deviation']}min)")
        
        # Trends
        if trend_analysis and trend_analysis != "Sleep patterns are relatively stable":
            report_sections.append(f"\n📈 **Recent Trends**: {trend_analysis}")
        
        # Insights
        if insights["strengths"]:
            report_sections.append(f"\n🏆 **Strengths**: {', '.join(insights['strengths'])}")
        
        if insights["concerns"]:
            report_sections.append(f"\n⚠️ **Areas for Improvement**: {'; '.join(insights['concerns'])}")
        
        if insights["notable_patterns"]:
            report_sections.append(f"\n📋 **Notable Patterns**: {'; '.join(insights['notable_patterns'])}")
        
        # Recommendations
        if insights["recommendations"]:
            report_sections.append(f"\n🎯 **Recommendations**:")
            for rec in insights["recommendations"][:3]:  # Limit to top 3
                report_sections.append(f"  • {rec}")
        
        # Footer
        report_sections.append("\n💡 *Ask me about specific sleep challenges for personalized coaching!*")
        
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
            "trends": trend_analysis
        }
        
        return {
            "agent": self.name, 
            "text": "\n".join(report_sections),
            "data": {"summary": summary, "logs": logs[-3:]}  # Include recent logs for context
        }