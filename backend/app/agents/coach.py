from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from . import BaseAgent, AgentContext, AgentResponse
from app.llm_gemini import generate_gemini_text
from app.db import fetch_recent_logs
import logging

# Configure logging for coach agent
logger = logging.getLogger(__name__)

DISCLAIMER = (
    "_This is educational guidance based on sleep science principles, not medical care. "
    "If you have severe insomnia, sleep apnea, or other serious sleep disorders, please consult a healthcare provider._"
)

# Enhanced safety detection patterns
SAFETY_PATTERNS = {
    "sleep_apnea": [
        r"stop breathing", r"gasping", r"choking", r"snoring loudly", 
        r"partner says I stop", r"wake up gasping"
    ],
    "chronic_insomnia": [
        r"can't sleep for (weeks|months)", r"insomnia for", r"sleepless for", 
        r"no sleep for", r"haven't slept in"
    ],
    "medical_concerns": [
        r"chest pain", r"heart racing", r"panic attacks", r"medication", 
        r"depression", r"anxiety disorder", r"bipolar"
    ],
    "urgent_symptoms": [
        r"hallucinations", r"microsleep", r"falling asleep driving", 
        r"can't function", r"suicidal"
    ]
}


class CoachAgent(BaseAgent):
    """
    Advanced sleep coaching agent for Morpheus Sleep AI.
    
    Functionality:
    - Generates personalized sleep improvement plans using CBT-I and other frameworks.
    - Tracks user habits and progress, adapting recommendations over time.
    - Detects urgent medical or safety concerns in user input and responds with disclaimers.
    - Applies responsible AI principles for inclusivity, transparency, and safety.
    
    Key attributes:
    - name: Agent identifier ('coach')
    - action_type: Used for responsible AI logging and transparency
    - coaching_frameworks: Supported sleep improvement methodologies
    - inclusive_coaching_principles: Ensures advice is accessible and culturally sensitive
    """
    name = "coach"

    def __init__(self):
        super().__init__()
        self.action_type = "sleep_coaching_plan"  # Used for responsible AI transparency
        # Supported coaching frameworks for sleep improvement
        self.coaching_frameworks = {
            "cbt_i": "Cognitive Behavioral Therapy for Insomnia",
            "sleep_hygiene": "Sleep Environment & Habits Optimization",
            "circadian": "Circadian Rhythm Regulation",
            "stress_management": "Stress & Anxiety Reduction for Sleep"
        }
        # Responsible AI: inclusive coaching principles
        self.inclusive_coaching_principles = {
            "cultural_sensitivity": "Adapt recommendations to different cultural sleep practices",
            "accessibility": "Provide alternatives for users with different abilities",
            "economic_inclusivity": "Offer free and low-cost solutions alongside premium options",
            "age_inclusivity": "Tailor advice for different age groups without stereotyping"
        }

    # ...existing code...

    async def _analyze_sleep_patterns(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Deep analysis of sleep patterns with trends and insights."""
        if not logs:
            return {}
        
        # Time series analysis
        durations = []
        bedtimes = []
        wake_times = []
        awakenings = []
        screen_times = []
        caffeine_nights = 0
        alcohol_nights = 0
        
        for log in logs:
            if log.get("duration_h"):
                durations.append(log["duration_h"])
            
            awakenings.append(log.get("awakenings", 0))
            screen_times.append(log.get("screen_time_min", 0))
            
            if log.get("caffeine_after3pm"):
                caffeine_nights += 1
            if log.get("alcohol"):
                alcohol_nights += 1
            
            # Parse bedtime for consistency analysis
            if log.get("bedtime"):
                try:
                    bt = datetime.fromisoformat(log["bedtime"])
                    bedtimes.append(bt.hour * 60 + bt.minute)  # minutes since midnight
                except:
                    pass
                    
            if log.get("wake_time"):
                try:
                    wt = datetime.fromisoformat(log["wake_time"])
                    wake_times.append(wt.hour * 60 + wt.minute)
                except:
                    pass

        # Calculate trends and patterns
        analysis = {
            "total_nights": len(logs),
            "avg_duration": round(sum(durations) / len(durations), 1) if durations else None,
            "duration_trend": self._calculate_trend(durations[-7:]) if len(durations) >= 3 else "stable",
            "avg_awakenings": round(sum(awakenings) / len(awakenings), 1),
            "awakening_trend": self._calculate_trend(awakenings[-7:]) if len(awakenings) >= 3 else "stable",
            "avg_screen_time": round(sum(screen_times) / len(screen_times), 1),
            "caffeine_frequency": round(caffeine_nights / len(logs) * 100, 1),
            "alcohol_frequency": round(alcohol_nights / len(logs) * 100, 1),
            "bedtime_consistency": self._calculate_consistency(bedtimes),
            "wake_consistency": self._calculate_consistency(wake_times),
            "sleep_efficiency": self._calculate_sleep_efficiency(logs),
            "problem_areas": self._identify_problem_areas(logs)
        }
        
        return analysis

    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate if values are improving, worsening, or stable."""
        if len(values) < 3:
            return "stable"
        
        # Simple linear trend
        first_half = sum(values[:len(values)//2]) / (len(values)//2)
        second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
        
        diff = second_half - first_half
        if abs(diff) < 0.2:
            return "stable"
        elif diff > 0:
            return "improving"
        else:
            return "declining"

    def _calculate_consistency(self, times: List[int]) -> Dict[str, Any]:
        """Calculate time consistency in minutes."""
        if len(times) < 2:
            return {"avg_deviation": 0, "rating": "excellent"}
        
        avg_time = sum(times) / len(times)
        deviations = [abs(t - avg_time) for t in times]
        avg_deviation = sum(deviations) / len(deviations)
        
        if avg_deviation < 30:
            rating = "excellent"
        elif avg_deviation < 60:
            rating = "good"
        elif avg_deviation < 90:
            rating = "fair"
        else:
            rating = "needs improvement"
            
        return {"avg_deviation": round(avg_deviation), "rating": rating}

    def _calculate_sleep_efficiency(self, logs: List[Dict[str, Any]]) -> Optional[float]:
        """Calculate sleep efficiency percentage."""
        efficiency_scores = []
        
        for log in logs:
            if log.get("duration_h") and log.get("awakenings") is not None:
                # Rough efficiency: duration / (duration + awakenings * 15min)
                sleep_time = log["duration_h"] * 60  # minutes
                wake_time = log["awakenings"] * 15  # assume 15min per awakening
                total_time = sleep_time + wake_time
                
                if total_time > 0:
                    efficiency = (sleep_time / total_time) * 100
                    efficiency_scores.append(efficiency)
        
        return round(sum(efficiency_scores) / len(efficiency_scores), 1) if efficiency_scores else None

    def _identify_problem_areas(self, logs: List[Dict[str, Any]]) -> List[str]:
        """Identify specific problem areas from the data."""
        problems = []
        
        # Duration issues
        short_sleeps = sum(1 for log in logs if log.get("duration_h", 8) < 6.5)
        if short_sleeps > len(logs) * 0.4:
            problems.append("insufficient_sleep_duration")
        
        # Fragmented sleep
        high_awakenings = sum(1 for log in logs if log.get("awakenings", 0) >= 3)
        if high_awakenings > len(logs) * 0.3:
            problems.append("fragmented_sleep")
        
        # Late caffeine
        late_caffeine = sum(1 for log in logs if log.get("caffeine_after3pm"))
        if late_caffeine > len(logs) * 0.5:
            problems.append("late_caffeine_intake")
        
        # Excessive screen time
        high_screen = sum(1 for log in logs if log.get("screen_time_min", 0) > 60)
        if high_screen > len(logs) * 0.4:
            problems.append("excessive_screen_time")
        
        # Alcohol impact
        frequent_alcohol = sum(1 for log in logs if log.get("alcohol"))
        if frequent_alcohol > len(logs) * 0.4:
            problems.append("frequent_alcohol_use")
            
        return problems

    def _generate_personalized_plan(self, analysis: Dict[str, Any], message: str) -> Dict[str, Any]:
        """Generate a comprehensive, personalized sleep improvement plan."""
        plan = {
            "primary_focus": [],
            "weekly_goals": [],
            "daily_habits": [],
            "troubleshooting": [],
            "timeline": "2-4 weeks",
            "success_metrics": []
        }
        
        problems = analysis.get("problem_areas", [])
        
        # Prioritize issues based on impact
        if "insufficient_sleep_duration" in problems:
            plan["primary_focus"].append({
                "area": "Sleep Duration",
                "current": f"{analysis.get('avg_duration', 'Unknown')}h average",
                "target": "7-9 hours nightly",
                "strategy": "Gradual bedtime adjustment by 15-30 minutes per week"
            })
            
        if "fragmented_sleep" in problems:
            plan["primary_focus"].append({
                "area": "Sleep Continuity", 
                "current": f"{analysis.get('avg_awakenings', 'Unknown')} awakenings/night",
                "target": "≤1 awakening per night",
                "strategy": "Sleep environment optimization and relaxation techniques"
            })
            
        if "late_caffeine_intake" in problems:
            plan["primary_focus"].append({
                "area": "Caffeine Management",
                "current": f"{analysis.get('caffeine_frequency', 0)}% of nights with late caffeine",
                "target": "0% caffeine after 2pm",
                "strategy": "Gradual cutoff time advancement"
            })
        
        # Generate weekly progression
        plan["weekly_goals"] = [
            "Week 1: Establish consistent wake time (±15 min daily)",
            "Week 2: Optimize sleep environment (darkness, temperature, noise)",
            "Week 3: Implement pre-sleep routine (60-90 min wind-down)",
            "Week 4: Fine-tune timing and troubleshoot remaining issues"
        ]
        
        # Daily habit recommendations
        consistency = analysis.get("bedtime_consistency", {})
        if consistency.get("rating") in ["fair", "needs improvement"]:
            plan["daily_habits"].append("Set phone alarm for bedtime routine start")
            
        if analysis.get("avg_screen_time", 0) > 30:
            plan["daily_habits"].extend([
                "Enable blue light filters 2 hours before bed",
                "Create phone-free bedroom policy"
            ])
            
        plan["daily_habits"].extend([
            "Get 10-30 minutes morning sunlight within 1 hour of waking",
            "No caffeine after 2pm (or 6 hours before target bedtime)",
            "Keep bedroom temperature 65-68°F (18-20°C)"
        ])
        
        return plan

    def _detect_safety_concerns(self, message: str) -> List[str]:
        """Enhanced safety detection with specific concern categories."""
        import re
        concerns = []
        text = message.lower()
        
        for category, patterns in SAFETY_PATTERNS.items():
            if any(re.search(pattern, text) for pattern in patterns):
                concerns.append(category)
                
        return concerns

    async def _handle_core(self, message: str, ctx: Optional[AgentContext] = None) -> AgentResponse:
        ctx = ctx or {}
        user = ctx.get("user")
        
        # Safety screening
        safety_concerns = self._detect_safety_concerns(message)
        safety_warnings = []
        
        if "urgent_symptoms" in safety_concerns:
            safety_warnings.append("⚠️ **URGENT**: Please seek immediate medical attention if you're experiencing severe symptoms.")
        elif "sleep_apnea" in safety_concerns:
            safety_warnings.append("💡 **Important**: Your symptoms may indicate sleep apnea. Please consult a doctor for proper evaluation.")
        elif "chronic_insomnia" in safety_concerns:
            safety_warnings.append("🏥 **Recommendation**: Chronic insomnia lasting months should be evaluated by a sleep specialist.")
        elif "medical_concerns" in safety_concerns:
            safety_warnings.append("🩺 **Note**: Sleep issues related to medications or mental health conditions require medical supervision.")

        # Get comprehensive sleep data
        logs = []
        if user:
            logs = ctx.get("logs") or await fetch_recent_logs(user["id"], days=14)  # Extended to 14 days
        
        # Perform deep analysis
        analysis = await self._analyze_sleep_patterns(logs)
        
        # Generate personalized coaching response
        if analysis and logs:
            # Enhanced LLM prompt with comprehensive context and responsible AI guidelines
            dn = (ctx or {}).get("display_name") or ""
            prompt = f"""
            You are Morpheus, an expert AI sleep coach with training in CBT-I (Cognitive Behavioral Therapy for Insomnia) and sleep science.
            
            IMPORTANT: Follow these responsible AI principles:
            - Use inclusive language that considers diverse backgrounds, ages, and abilities
            - Provide alternatives for users with different physical or economic capabilities
            - Acknowledge individual differences - avoid "everyone should" statements
            - Be transparent about data usage and AI limitations
            - Respect privacy - don't expose sensitive personal details
            - Offer both free and accessible solutions alongside premium options
            - Do not use nicknames or invented names for the user. If addressing the user by name, use this exact display name: {(dn or '').strip()}. Otherwise, address them neutrally as "you".
            
            A user is asking for sleep improvement guidance. Based on their comprehensive 14-day sleep analysis, create a detailed, personalized coaching response.
            
            **User's Sleep Analysis:**
            - Total nights logged: {analysis.get('total_nights', 0)}
            - Average sleep duration: {analysis.get('avg_duration', 'Unknown')} hours (trend: {analysis.get('duration_trend', 'unknown')})
            - Average nightly awakenings: {analysis.get('avg_awakenings', 'Unknown')} (trend: {analysis.get('awakening_trend', 'unknown')})
            - Sleep efficiency: {analysis.get('sleep_efficiency', 'Unknown')}%
            - Bedtime consistency: {analysis.get('bedtime_consistency', {}).get('rating', 'unknown')} (±{analysis.get('bedtime_consistency', {}).get('avg_deviation', 0)} min)
            - Wake time consistency: {analysis.get('wake_consistency', {}).get('rating', 'unknown')} (±{analysis.get('wake_consistency', {}).get('avg_deviation', 0)} min)
            - Average screen time before bed: {analysis.get('avg_screen_time', 0)} minutes
            - Late caffeine frequency: {analysis.get('caffeine_frequency', 0)}% of nights
            - Alcohol frequency: {analysis.get('alcohol_frequency', 0)}% of nights
            - Identified problem areas: {', '.join(analysis.get('problem_areas', [])) or 'None detected'}
            
            **User's Message:** "{message}"
            
            Create a comprehensive coaching response with these sections:
            
            1. **Personal Assessment (2-3 sentences):** Acknowledge their current sleep patterns and highlight both strengths and improvement areas from their data.
            
            2. **Priority Action Plan (3-4 specific items):** Based on their worst problem areas, give concrete, actionable steps with timelines. Be specific about what to do and when.
            
            3. **This Week's Focus:** One primary goal for the next 7 days with daily implementation steps.
            
            4. **Optimization Tips:** 2-3 advanced strategies tailored to their specific patterns (e.g., if they have late caffeine issues, give specific caffeine management advice).
            
            5. **Progress Tracking:** Tell them what metrics to watch and what improvements to expect by when.
            
            Make it personal, encouraging, and evidence-based. Use their actual numbers and trends. Be specific rather than generic.
            """
            
            llm_response = await generate_gemini_text(prompt)
            
        else:
            # Fallback for users without sufficient data
            llm_response = await self._generate_general_coaching_advice(message, (ctx or {}).get("display_name"))
        
        # Compile final response
        final_sections = []
        
        if safety_warnings:
            final_sections.append("\n".join(safety_warnings))
            
        if llm_response:
            final_sections.append(llm_response)
        else:
            final_sections.append("I'd love to help you improve your sleep! To give you the most personalized advice, please log a few nights of sleep data first. In the meantime, focus on consistent wake times and a relaxing bedtime routine.")
        
        # Add responsible AI transparency note
        transparency_note = self._generate_transparency_note(analysis, len(logs))
        if transparency_note:
            final_sections.append(transparency_note)
        
        final_sections.append(f"{DISCLAIMER}")
        
        # Prepare response data with transparency information
        response_data = {
            "safety_concerns": safety_concerns,
            "analysis": analysis,
            "coaching_framework": "cbt_i_enhanced",
            "decision_factors": self._get_decision_factors(analysis, message, safety_concerns),
            "data_sources_used": self._get_data_sources_used(logs, user),
            "personalization_level": "high" if analysis else "general",
            "alternatives_provided": True,
            "accessibility_considered": True
        }
        
        if analysis:
            response_data["plan"] = self._generate_personalized_plan(analysis, message)
        
        return {
            "agent": self.name, 
            "text": "\n\n".join(final_sections),
            "data": response_data
        }

    async def _generate_general_coaching_advice(self, message: str, display_name: Optional[str] = None) -> str:
        """Generate general advice for users without sleep data."""
        dn = (display_name or "").strip()
        prompt = f"""
        You are Morpheus, an AI sleep coach helping someone who hasn't logged detailed sleep data yet.
        
        IMPORTANT: Follow responsible AI principles:
        - Use inclusive language for all backgrounds and abilities
        - Provide both free and accessible solutions
        - Acknowledge individual differences
        - Be transparent that this is AI-generated advice
        - Do not use nicknames or invented names for the user. If addressing the user by name, use this exact display name: {dn}. Otherwise, address them neutrally as "you".
        
        User's message: "{message}"
        
        Provide helpful, general sleep improvement advice that covers:
        1. Sleep hygiene fundamentals (with accessible alternatives)
        2. Creating a bedtime routine (adaptable to different lifestyles)
        3. Environment optimization (budget-friendly options)
        4. Timing and consistency tips (flexible for different schedules)
        5. Encourage them to start tracking their sleep
        
        Keep it actionable, encouraging, and inclusive. Limit to 4-5 key points.
        """
        
        response = await generate_gemini_text(prompt)
        return response or "Focus on these fundamentals: consistent sleep schedule, cool dark bedroom, no screens 1 hour before bed, and no caffeine after 2pm. Start logging your sleep so I can give you personalized advice!"

    def _get_decision_factors(self, analysis: Dict[str, Any], message: str, safety_concerns: List[str]) -> Dict[str, Any]:
        """Get decision factors for transparency in AI recommendations"""
        factors = {}
        
        if analysis:
            factors["sleep_duration_trend"] = analysis.get("duration_trend", "unknown")
            factors["sleep_consistency"] = {
                "bedtime": analysis.get("bedtime_consistency", {}).get("rating", "unknown"),
                "wake_time": analysis.get("wake_consistency", {}).get("rating", "unknown")
            }
            factors["problem_areas"] = analysis.get("problem_areas", [])
            factors["sleep_efficiency"] = analysis.get("sleep_efficiency", "unknown")
            factors["lifestyle_factors"] = {
                "caffeine_frequency": analysis.get("caffeine_frequency", 0),
                "screen_time": analysis.get("avg_screen_time", 0),
                "alcohol_frequency": analysis.get("alcohol_frequency", 0)
            }
        
        factors["safety_screening"] = {
            "concerns_detected": safety_concerns,
            "urgent_referral_needed": "urgent_symptoms" in safety_concerns
        }
        
        factors["user_input_analysis"] = {
            "message_length": len(message),
            "specific_request": self._categorize_user_request(message)
        }
        
        return factors

    def _get_data_sources_used(self, logs: List[Dict[str, Any]], user: Optional[Dict[str, Any]]) -> List[str]:
        """Identify data sources used for transparency"""
        sources = []
        
        if logs:
            sources.append(f"sleep_logs_{len(logs)}_nights")
        if user:
            sources.append("user_profile")
        
        sources.extend([
            "cbt_i_framework",
            "sleep_science_evidence",
            "safety_screening_patterns"
        ])
        
        return sources

    def _generate_transparency_note(self, analysis: Dict[str, Any], log_count: int) -> Optional[str]:
        """Generate transparency note about AI decision-making"""
        if not analysis:
            return "**AI Transparency Note:** This response is generated based on general sleep science principles since no sleep data is available yet."
        
        note_parts = [
            f"**AI Transparency Note:** This personalized coaching is based on analysis of your {log_count} nights of sleep data",
        ]
        
        if analysis.get("problem_areas"):
            note_parts.append(f"focusing on your main challenges: {', '.join(analysis['problem_areas'][:2])}")
        
        note_parts.append("You have full control over your data and can modify or delete it anytime.")
        
        return " ".join(note_parts) + "."

    def _categorize_user_request(self, message: str) -> str:
        """Categorize the type of user request for decision factor transparency"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["help", "advice", "improve", "better"]):
            return "general_improvement_request"
        elif any(word in message_lower for word in ["insomnia", "can't sleep", "trouble sleeping"]):
            return "sleep_disorder_concern"
        elif any(word in message_lower for word in ["schedule", "routine", "habit"]):
            return "routine_optimization"
        elif any(word in message_lower for word in ["tired", "fatigue", "energy"]):
            return "energy_optimization"
        else:
            return "general_inquiry"

    def _get_data_sources(self, ctx: AgentContext) -> List[str]:
        """Override parent method to provide coach-specific data sources"""
        sources = super()._get_data_sources(ctx)
        
        # Add coach-specific sources
        sources.extend([
            "cbt_i_framework",
            "sleep_science_research",
            "safety_screening_database"
        ])
        
        return sources

    async def _apply_inclusive_coaching_principles(self, response_text: str) -> str:
        """Apply inclusive coaching principles to response text"""
        # Add inclusive language reminders
        inclusive_additions = []
        
        if "expensive" in response_text.lower() or "cost" in response_text.lower():
            inclusive_additions.append("*Budget-friendly alternatives are available for all recommendations.*")
        
        if "exercise" in response_text.lower() or "physical" in response_text.lower():
            inclusive_additions.append("*All physical recommendations can be adapted based on your abilities and mobility.*")
        
        if "bedroom" in response_text.lower() or "environment" in response_text.lower():
            inclusive_additions.append("*Environmental suggestions can be adapted to your living situation and resources.*")
        
        if inclusive_additions:
            response_text += "\n\n" + " ".join(inclusive_additions)
        
        return response_text