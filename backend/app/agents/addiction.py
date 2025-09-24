# app/agents/addiction.py
import re
from datetime import datetime, timedelta
from typing import Optional
from . import BaseAgent, AgentContext, AgentResponse
from app.llm_gemini import generate_gemini_text

DISCLAIMER = (
    "_This is supportive educational guidance, not medical or addiction treatment. "
    "If you struggle with addiction, please consult a qualified clinician or counselor._"
)

# Enhanced trigger patterns with severity levels
ADDICTION_PATTERNS = {
    "high_severity": [
        r"can't (stop|quit|live without)",
        r"(need|must have|have to have)",
        r"withdrawal",
        r"shaking|trembling",
        r"panic when (out of|without)",
    ],
    "medium_severity": [
        r"addicted to",
        r"dependent on",
        r"crave|craving",
        r"can't sleep without",
        r"multiple times (a day|daily)",
    ],
    "low_severity": [
        r"too much (coffee|alcohol|caffeine)",
        r"should (cut back|reduce)",
        r"probably drinking too much",
    ]
}

SUBSTANCE_PATTERNS = {
    "caffeine": ["coffee", "tea", "energy drink", "caffeine", "espresso", "latte"],
    "alcohol": ["wine", "beer", "vodka", "whiskey", "drinking", "alcohol", "cocktail"],
    "nicotine": ["smoking", "cigarette", "vaping", "nicotine", "tobacco", "juul"],
    "digital": ["phone", "social media", "scrolling", "screen time", "gaming"]
}

TRIGGERS = ["addict", "dependen", "craving", "alcohol", "caffeine", "nicotine", "smoking"]

class AddictionAgent(BaseAgent):
    """
    Supports users mentioning addictive behaviors (caffeine, alcohol, nicotine, etc.).
    Offers gentle, safe advice for reducing dependence and encourages professional help.
    Enhanced with severity assessment, personalized plans, and sleep correlation analysis.
    """
    name = "addiction"
    
    def __init__(self):
        super().__init__()
        self.action_type = "behavioral_change_suggestion"  # For responsible AI transparency

    def _detect_addiction_context(self, message: str) -> bool:
        """Check if user message contains addiction-related triggers."""
        t = message.lower()
        return any(k in t for k in TRIGGERS)

    def _assess_addiction_severity(self, message: str) -> tuple[str, list[str]]:
        """Detect severity level and substances mentioned."""
        t = message.lower()
        severity = "low_severity"
        substances = []
        
        # Check severity patterns (from high to low)
        for level, patterns in ADDICTION_PATTERNS.items():
            if any(re.search(pattern, t) for pattern in patterns):
                severity = level
                break
        
        # Detect substances
        for substance, keywords in SUBSTANCE_PATTERNS.items():
            if any(keyword in t for keyword in keywords):
                substances.append(substance)
        
        return severity, substances

    async def _get_user_addiction_history(self, user_id: str) -> dict:
        """Analyze user's sleep logs for addiction-related patterns."""
        try:
            # Import here to avoid circular imports
            from app.db import get_database
            
            # Mock implementation - replace with actual database query
            # This would query the user's sleep logs for the last 30 days
            logs = []  # await fetch_recent_logs(user_id, days=30)
            
            patterns = {
                "caffeine_frequency": sum(1 for log in logs if log.get("caffeine_after3pm", False)),
                "alcohol_frequency": sum(1 for log in logs if log.get("alcohol", False)),
                "avg_screen_time": sum(log.get("screen_time_min", 0) for log in logs) / len(logs) if logs else 0,
                "sleep_quality_correlation": self._analyze_substance_sleep_correlation(logs),
                "total_logs": len(logs)
            }
            
            return patterns
        except Exception:
            # Fallback if database query fails
            return {
                "caffeine_frequency": 0,
                "alcohol_frequency": 0,
                "avg_screen_time": 0,
                "sleep_quality_correlation": {},
                "total_logs": 0
            }

    def _analyze_substance_sleep_correlation(self, logs: list) -> dict:
        """Find correlations between substance use and poor sleep."""
        correlations = {}
        
        if not logs:
            return correlations
        
        # Caffeine correlation
        caffeine_nights = [log for log in logs if log.get("caffeine_after3pm", False)]
        non_caffeine_nights = [log for log in logs if not log.get("caffeine_after3pm", False)]
        
        if caffeine_nights and non_caffeine_nights:
            caffeine_avg_awakenings = sum(log.get("awakenings", 0) for log in caffeine_nights) / len(caffeine_nights)
            normal_avg_awakenings = sum(log.get("awakenings", 0) for log in non_caffeine_nights) / len(non_caffeine_nights)
            correlations["caffeine_impact"] = round(caffeine_avg_awakenings - normal_avg_awakenings, 1)
        
        # Alcohol correlation
        alcohol_nights = [log for log in logs if log.get("alcohol", False)]
        non_alcohol_nights = [log for log in logs if not log.get("alcohol", False)]
        
        if alcohol_nights and non_alcohol_nights:
            alcohol_avg_awakenings = sum(log.get("awakenings", 0) for log in alcohol_nights) / len(alcohol_nights)
            normal_avg_awakenings = sum(log.get("awakenings", 0) for log in non_alcohol_nights) / len(non_alcohol_nights)
            correlations["alcohol_impact"] = round(alcohol_avg_awakenings - normal_avg_awakenings, 1)
        
        return correlations

    def _generate_reduction_plan(self, substance: str, severity: str, user_patterns: dict) -> dict:
        """Create a personalized reduction plan."""
        plans = {
            "caffeine": {
                "high_severity": {
                    "timeline": "4-6 weeks",
                    "warning": "Gradual reduction is important to avoid withdrawal headaches.",
                    "steps": [
                        "Week 1-2: Replace 1 cup with decaf daily",
                        "Week 3-4: Move last coffee to before 2pm",
                        "Week 5-6: Reduce total intake by 50%"
                    ],
                    "alternatives": ["Green tea", "Herbal tea", "Sparkling water with lemon"],
                    "sleep_benefit": "Should see fewer night awakenings within 1-2 weeks"
                },
                "medium_severity": {
                    "timeline": "2-3 weeks", 
                    "steps": [
                        "Week 1: No caffeine after 2pm",
                        "Week 2: Replace afternoon coffee with tea",
                        "Week 3: Limit to 2 cups total per day"
                    ],
                    "alternatives": ["Decaf coffee", "Chai tea", "Herbal alternatives"],
                    "sleep_benefit": "Expect better sleep quality within 1 week"
                },
                "low_severity": {
                    "timeline": "1-2 weeks",
                    "steps": [
                        "Stop caffeine 6 hours before bedtime",
                        "Replace one daily cup with water or herbal tea"
                    ],
                    "sleep_benefit": "Minor improvements in falling asleep"
                }
            },
            "alcohol": {
                "high_severity": {
                    "timeline": "Medical supervision recommended",
                    "warning": "Alcohol withdrawal can be dangerous. Please consult a healthcare provider immediately.",
                    "steps": ["Seek professional medical guidance for safe withdrawal"],
                    "resources": ["Contact your doctor", "Call addiction helpline", "Visit urgent care if experiencing withdrawal symptoms"]
                },
                "medium_severity": {
                    "timeline": "3-4 weeks",
                    "steps": [
                        "Week 1: No alcohol 3 hours before bed",
                        "Week 2: Alcohol-free weekdays",
                        "Week 3-4: Limit to 2 drinks per week maximum"
                    ],
                    "alternatives": ["Sparkling water with lime", "Non-alcoholic beer", "Herbal tea"],
                    "sleep_benefit": "Deeper sleep and fewer awakenings within 2 weeks"
                },
                "low_severity": {
                    "timeline": "2-3 weeks",
                    "steps": [
                        "No alcohol 2 hours before bed",
                        "Limit to 1 drink per day maximum"
                    ],
                    "sleep_benefit": "Better REM sleep quality"
                }
            },
            "nicotine": {
                "high_severity": {
                    "timeline": "6-12 weeks with professional support",
                    "warning": "Consider nicotine replacement therapy or medical support.",
                    "steps": [
                        "Consult healthcare provider about cessation aids",
                        "Set a quit date within 2 weeks",
                        "Use gradual reduction or replacement therapy"
                    ],
                    "sleep_benefit": "Sleep quality improves significantly after 2-4 weeks"
                },
                "medium_severity": {
                    "timeline": "4-6 weeks",
                    "steps": [
                        "Week 1-2: No nicotine 2 hours before bed",
                        "Week 3-4: Reduce daily intake by 50%",
                        "Week 5-6: Continue gradual reduction"
                    ],
                    "sleep_benefit": "Less restless sleep within 2 weeks"
                }
            },
            "digital": {
                "high_severity": {
                    "timeline": "3-4 weeks",
                    "steps": [
                        "Week 1: No screens 1 hour before bed",
                        "Week 2: Use blue light filters after sunset",
                        "Week 3-4: Create phone-free bedroom policy"
                    ],
                    "alternatives": ["Reading", "Meditation", "Journaling"],
                    "sleep_benefit": "Faster sleep onset within 1 week"
                },
                "medium_severity": {
                    "timeline": "2-3 weeks",
                    "steps": [
                        "Week 1: No social media after 9pm",
                        "Week 2-3: Gradual reduction in evening screen time"
                    ]
                }
            }
        }
        
        return plans.get(substance, {}).get(severity, {})

    def _connect_to_sleep_impact(self, substances: list[str], user_patterns: dict) -> str:
        """Show specific sleep impact based on user's data."""
        impacts = []
        
        correlations = user_patterns.get('sleep_quality_correlation', {})
        
        if 'caffeine' in substances and correlations.get('caffeine_impact', 0) > 0:
            impacts.append(f"Your sleep data shows {correlations['caffeine_impact']:.1f} more awakenings on nights with late caffeine")
        
        if 'alcohol' in substances and correlations.get('alcohol_impact', 0) > 0:
            impacts.append(f"Alcohol appears to increase your night awakenings by {correlations['alcohol_impact']:.1f} times")
        
        if impacts:
            return "**Your Personal Sleep Impact:** " + "; ".join(impacts) + "\n\n"
        return ""

    def _should_check_progress(self, user_patterns: dict) -> bool:
        """Determine if we should ask about progress on previous addiction goals."""
        return (user_patterns.get('caffeine_frequency', 0) > 10 or 
                user_patterns.get('alcohol_frequency', 0) > 5)

    def _generate_progress_check(self, user_patterns: dict) -> str:
        """Generate a follow-up question about their reduction progress."""
        if user_patterns.get('caffeine_frequency', 0) > 10:
            return "\n\n💭 **Follow-up:** I notice you've logged caffeine after 3pm frequently. How has your reduction plan been going?"
        elif user_patterns.get('alcohol_frequency', 0) > 5:
            return "\n\n💭 **Follow-up:** How are you feeling about your alcohol reduction goals?"
        return ""

    async def _handle_core(self, message: str, ctx: Optional[AgentContext] = None) -> AgentResponse:
        """Handle addiction-related queries with enhanced intelligence and personalization."""
        ctx = ctx or {}
        user = ctx.get("user")
        
        # Assess severity and substances
        severity, substances = self._assess_addiction_severity(message)
        
        if not substances:
            return {
                "agent": self.name, 
                "text": "I can help with addiction concerns related to sleep. What substance or behavior would you like support with? (caffeine, alcohol, nicotine, or digital/screen time)"
            }
        
        # Get user's historical patterns if available
        user_patterns = {}
        if user:
            user_patterns = await self._get_user_addiction_history(user.get("id", ""))
        
        # Enhanced LLM prompt with context
        sleep_impact_text = self._connect_to_sleep_impact(substances, user_patterns)
        
        prompt = f"""
        You are an expert addiction support counselor specializing in sleep-related dependencies.
        
        User message: "{message}"
        Detected severity: {severity}
        Substances mentioned: {', '.join(substances)}
        
        User's recent patterns (last 30 days):
        - Caffeine after 3pm: {user_patterns.get('caffeine_frequency', 0)} times
        - Alcohol use: {user_patterns.get('alcohol_frequency', 0)} times
        - Average screen time: {user_patterns.get('avg_screen_time', 0):.1f} minutes
        - Total sleep logs: {user_patterns.get('total_logs', 0)}
        
        Provide a response that:
        1. Acknowledges their specific concern with empathy (2-3 sentences)
        2. References their actual usage patterns if available
        3. Gives specific, actionable advice for their situation
        4. Explains how this impacts their sleep quality
        5. Provides 2-3 immediate coping strategies
        6. Sets realistic expectations for improvement timeline
        
        Keep it supportive, non-judgmental, and focused on gradual progress.
        Use a warm, encouraging tone. Be specific rather than generic.
        """
        
        try:
            llm_response = await generate_gemini_text(prompt)
        except Exception:
            # Fallback response if LLM fails
            substance_text = ', '.join(substances)
            llm_response = f"""I understand you're concerned about your {substance_text} use and its impact on your sleep. This is a common concern, and taking the first step to address it shows real commitment to your health.
            
            Reducing {substance_text} gradually is usually the most sustainable approach. Your sleep quality should start improving within 1-2 weeks of making changes.
            
            Here are some immediate strategies you can try:
            • Start by avoiding {substance_text} 3-4 hours before bedtime
            • Replace your usual {substance_text} with a healthier alternative in the evening
            • Create a calming bedtime routine to ease the transition
            
            Remember, small consistent changes often lead to the best long-term results."""
        
        # Generate personalized reduction plans
        reduction_plans = {}
        for substance in substances:
            plan = self._generate_reduction_plan(substance, severity, user_patterns)
            if plan:
                reduction_plans[substance] = plan
        
        # Add progress check if appropriate
        progress_check = ""
        if self._should_check_progress(user_patterns):
            progress_check = self._generate_progress_check(user_patterns)
        
        # Combine response with sleep impact and progress check
        full_response = f"{sleep_impact_text}{llm_response}{progress_check}\n\n{DISCLAIMER}"
        
        return {
            "agent": self.name,
            "text": full_response,
            "data": {
                "severity": severity,
                "substances": substances,
                "reduction_plans": reduction_plans,
                "user_patterns": user_patterns,
                "sleep_correlations": user_patterns.get('sleep_quality_correlation', {})
            }
        }
