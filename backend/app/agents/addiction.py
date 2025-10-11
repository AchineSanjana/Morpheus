# app/agents/addiction.py
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple
from . import BaseAgent, AgentContext, AgentResponse
from app.llm_gemini import generate_gemini_text, gemini_ready

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
        r"multiple pots of coffee",
        r"blackout",
        r"can't function without",
    ],
    "medium_severity": [
        r"addicted to",
        r"dependent on",
        r"crave|craving",
        r"can't sleep without",
        r"multiple times (a day|daily)",
        r"too much every day",
        r"habit is out of control",
    ],
    "low_severity": [
        r"too much (coffee|alcohol|caffeine)",
        r"should (cut back|reduce)",
        r"probably drinking too much",
        r"might be having too much",
        r"starting to worry about",
    ]
}

SUBSTANCE_PATTERNS = {
    "caffeine": [
        "coffee", "coffe",  # include common typo
        "tea", "energy drink",
        "caffeine", "caffine", "caffiene", "cafine", "cafeine",  # common misspellings
        "espresso", "latte", "cappuccino", "red bull", "monster"
    ],
    "alcohol": ["wine", "beer", "vodka", "whiskey", "drinking", "alcohol", "cocktail", "rum", "gin", "tequila"],
    "nicotine": ["smoking", "cigarette", "vaping", "nicotine", "tobacco", "juul", "e-cigarette", "cigar"],
    "digital": ["phone", "social media", "scrolling", "screen time", "gaming", "netflix", "youtube", "tiktok", "instagram"]
}

TRIGGERS = [
    "addict",      # addicted / addiction
    "dependen",    # dependent / dependency
    "craving",     # cravings
    "withdrawal",  # withdrawal symptoms
    "quit",        # intent to quit
]

# Intervention levels for different severities
INTERVENTION_LEVELS = {
    "high_severity": "REFERRAL",
    "medium_severity": "SUPPORTIVE", 
    "low_severity": "EDUCATIONAL"
}

class AddictionAgent(BaseAgent):
    """
    Enhanced addiction support agent that provides:
    - Severity assessment and appropriate intervention levels
    - Personalized reduction plans based on user data
    - Sleep correlation analysis
    - Progress tracking and follow-up
    - Professional referrals when needed
    """
    name = "addiction"
    
    def __init__(self):
        super().__init__()
        self.action_type = "behavioral_change_suggestion"  # For responsible AI transparency

    def _detect_addiction_context(self, message: str) -> bool:
        """Enhanced addiction context detection."""
        if not message:
            return False
            
        t = message.lower()
        # Neutral info-seeking phrasing should not trigger addiction by itself
        neutral_info_phrases = [
            "tell me about", "what is", "what are", "explain", "definition of",
            "effects of", "effect of", "impact of", "how does", "why does"
        ]
        if any(p in t for p in neutral_info_phrases):
            # Only consider addiction if explicit dependency cues also exist
            if not any(trigger in t for trigger in TRIGGERS):
                return False
        
        # Direct trigger words
        if any(trigger in t for trigger in TRIGGERS):
            return True
            
        # Substance + concerning pattern combinations
        concerning_phrases = [
            "too much", "can't stop", "every day", "multiple times", 
            "worry about", "problem with", "bad habit", "need to quit"
        ]
        
        has_substance = any(
            any(keyword in t for keyword in keywords) 
            for keywords in SUBSTANCE_PATTERNS.values()
        )
        
        has_concern = any(phrase in t for phrase in concerning_phrases)
        
        return has_substance and has_concern

    def _assess_addiction_severity(self, message: str) -> Tuple[str, List[str]]:
        """Enhanced severity assessment with better pattern matching."""
        if not message:
            return "low_severity", []
            
        t = message.lower()
        severity = "low_severity"
        substances = []
        
        # Check severity patterns (from high to low priority)
        for level in ["high_severity", "medium_severity", "low_severity"]:
            patterns = ADDICTION_PATTERNS.get(level, [])
            if any(re.search(pattern, t, re.IGNORECASE) for pattern in patterns):
                severity = level
                break
        
        # Detect substances with enhanced matching
        for substance, keywords in SUBSTANCE_PATTERNS.items():
            if any(keyword in t for keyword in keywords):
                substances.append(substance)
        
        # Context-based severity adjustment
        if substances and len(substances) > 2:
            # Multiple substances indicate higher severity
            if severity == "low_severity":
                severity = "medium_severity"
        
        return severity, substances

    async def _get_user_addiction_history(self, user_id: str) -> Dict[str, Any]:
        """Enhanced user pattern analysis with better error handling."""
        if not user_id:
            return self._get_default_patterns()
            
        try:
            # Import here to avoid circular imports
            from app.db import get_database
            
            # In a real implementation, this would query the database
            # For now, return mock data that simulates realistic patterns
            logs = []  # await fetch_recent_logs(user_id, days=30)
            
            if not logs:
                return self._get_default_patterns()
            
            patterns = {
                "caffeine_frequency": sum(1 for log in logs if log.get("caffeine_after3pm", False)),
                "alcohol_frequency": sum(1 for log in logs if log.get("alcohol", False)),
                "avg_screen_time": sum(log.get("screen_time_min", 0) for log in logs) / len(logs) if logs else 0,
                "sleep_quality_correlation": self._analyze_substance_sleep_correlation(logs),
                "total_logs": len(logs),
                "recent_trend": self._calculate_usage_trend(logs),
                "worst_sleep_nights": self._identify_worst_sleep_correlation(logs)
            }
            
            return patterns
            
        except Exception as e:
            # Log the error but don't expose it to the user
            print(f"Error fetching user addiction history: {e}")
            return self._get_default_patterns()

    def _get_default_patterns(self) -> Dict[str, Any]:
        """Return default patterns when user data is unavailable."""
        return {
            "caffeine_frequency": 0,
            "alcohol_frequency": 0,
            "avg_screen_time": 0,
            "sleep_quality_correlation": {},
            "total_logs": 0,
            "recent_trend": "stable",
            "worst_sleep_nights": []
        }

    def _calculate_usage_trend(self, logs: List[Dict[str, Any]]) -> str:
        """Calculate whether substance use is increasing, decreasing, or stable."""
        if len(logs) < 7:
            return "insufficient_data"
            
        # Split logs into first and second half
        mid_point = len(logs) // 2
        first_half = logs[:mid_point]
        second_half = logs[mid_point:]
        
        first_usage = sum(1 for log in first_half if log.get("caffeine_after3pm", False) or log.get("alcohol", False))
        second_usage = sum(1 for log in second_half if log.get("caffeine_after3pm", False) or log.get("alcohol", False))
        
        if second_usage > first_usage * 1.2:
            return "increasing"
        elif second_usage < first_usage * 0.8:
            return "decreasing"
        else:
            return "stable"

    def _identify_worst_sleep_correlation(self, logs: List[Dict[str, Any]]) -> List[str]:
        """Identify which substances correlate with the worst sleep nights."""
        if not logs:
            return []
            
        # Find nights with poor sleep (high awakenings or low quality)
        poor_sleep_nights = [
            log for log in logs 
            if log.get("awakenings", 0) > 3 or log.get("sleep_quality", 5) < 3
        ]
        
        if not poor_sleep_nights:
            return []
        
        correlations = []
        total_poor_nights = len(poor_sleep_nights)
        
        # Check caffeine correlation
        caffeine_poor_nights = sum(1 for log in poor_sleep_nights if log.get("caffeine_after3pm", False))
        if caffeine_poor_nights > total_poor_nights * 0.6:
            correlations.append("caffeine")
            
        # Check alcohol correlation  
        alcohol_poor_nights = sum(1 for log in poor_sleep_nights if log.get("alcohol", False))
        if alcohol_poor_nights > total_poor_nights * 0.6:
            correlations.append("alcohol")
            
        return correlations

    def _analyze_substance_sleep_correlation(self, logs: List[Dict[str, Any]]) -> Dict[str, float]:
        """Enhanced correlation analysis with statistical significance."""
        correlations = {}
        
        if not logs or len(logs) < 5:
            return correlations
        
        # Caffeine correlation analysis
        caffeine_nights = [log for log in logs if log.get("caffeine_after3pm", False)]
        non_caffeine_nights = [log for log in logs if not log.get("caffeine_after3pm", False)]
        
        if caffeine_nights and non_caffeine_nights and len(caffeine_nights) >= 3:
            caffeine_avg_awakenings = sum(log.get("awakenings", 0) for log in caffeine_nights) / len(caffeine_nights)
            normal_avg_awakenings = sum(log.get("awakenings", 0) for log in non_caffeine_nights) / len(non_caffeine_nights)
            correlations["caffeine_impact"] = round(caffeine_avg_awakenings - normal_avg_awakenings, 1)
            
            # Sleep quality impact
            caffeine_avg_quality = sum(log.get("sleep_quality", 5) for log in caffeine_nights) / len(caffeine_nights)
            normal_avg_quality = sum(log.get("sleep_quality", 5) for log in non_caffeine_nights) / len(non_caffeine_nights)
            correlations["caffeine_quality_impact"] = round(normal_avg_quality - caffeine_avg_quality, 1)
        
        # Alcohol correlation analysis
        alcohol_nights = [log for log in logs if log.get("alcohol", False)]
        non_alcohol_nights = [log for log in logs if not log.get("alcohol", False)]
        
        if alcohol_nights and non_alcohol_nights and len(alcohol_nights) >= 3:
            alcohol_avg_awakenings = sum(log.get("awakenings", 0) for log in alcohol_nights) / len(alcohol_nights)
            normal_avg_awakenings = sum(log.get("awakenings", 0) for log in non_alcohol_nights) / len(non_alcohol_nights)
            correlations["alcohol_impact"] = round(alcohol_avg_awakenings - normal_avg_awakenings, 1)
            
            # Sleep quality impact
            alcohol_avg_quality = sum(log.get("sleep_quality", 5) for log in alcohol_nights) / len(alcohol_nights)
            normal_avg_quality = sum(log.get("sleep_quality", 5) for log in non_alcohol_nights) / len(non_alcohol_nights)
            correlations["alcohol_quality_impact"] = round(normal_avg_quality - alcohol_avg_quality, 1)
        
        return correlations

    def _generate_reduction_plan(self, substance: str, severity: str, user_patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced reduction plans with personalization based on user patterns."""
        plans = {
            "caffeine": {
                "high_severity": {
                    "timeline": "4-6 weeks",
                    "warning": "⚠️ Gradual reduction is important to avoid withdrawal headaches and fatigue.",
                    "steps": [
                        "Week 1-2: Replace 1 cup with half-caff daily",
                        "Week 3-4: Move last coffee to before 2pm", 
                        "Week 5-6: Reduce total intake by 50%",
                        "Consider decaf alternatives for afternoon cravings"
                    ],
                    "alternatives": ["Green tea (lower caffeine)", "Herbal tea", "Sparkling water with lemon", "Decaf coffee"],
                    "sleep_benefit": "Should see fewer night awakenings within 1-2 weeks",
                    "withdrawal_management": ["Stay hydrated", "Get adequate sleep", "Consider acetaminophen for headaches"]
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
                    "warning": "🚨 Alcohol withdrawal can be dangerous. Please consult a healthcare provider immediately.",
                    "steps": ["Seek professional medical guidance for safe withdrawal"],
                    "resources": [
                        "Contact your doctor immediately",
                        "Call SAMHSA National Helpline: 1-800-662-4357",
                        "Visit urgent care if experiencing withdrawal symptoms",
                        "Consider inpatient or outpatient treatment programs"
                    ]
                },
                "medium_severity": {
                    "timeline": "3-4 weeks",
                    "steps": [
                        "Week 1: No alcohol 3 hours before bed",
                        "Week 2: Alcohol-free weekdays", 
                        "Week 3-4: Limit to 2 drinks per week maximum"
                    ],
                    "alternatives": ["Sparkling water with lime", "Non-alcoholic beer", "Herbal tea", "Mocktails"],
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
                    "sleep_benefit": "Sleep quality improves significantly after 2-4 weeks",
                    "resources": ["Quitline: 1-800-QUIT-NOW", "Nicotine replacement therapy", "Prescription medications"]
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
                    "alternatives": ["Reading", "Meditation", "Journaling", "Audiobooks"],
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
        
        plan = plans.get(substance, {}).get(severity, {})
        
        # Personalize based on user patterns
        if plan and user_patterns.get("total_logs", 0) > 0:
            plan = self._personalize_plan(plan, substance, user_patterns)
            
        return plan

    def _personalize_plan(self, plan: Dict[str, Any], substance: str, user_patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Personalize reduction plan based on user's historical patterns."""
        personalized = plan.copy()
        
        # Add personalized insights
        if substance == "caffeine" and user_patterns.get("caffeine_frequency", 0) > 15:
            personalized["personal_note"] = f"Based on your logs showing frequent late caffeine use ({user_patterns['caffeine_frequency']} times recently), focus especially on the afternoon cutoff time."
            
        if substance == "alcohol" and user_patterns.get("alcohol_frequency", 0) > 10:
            personalized["personal_note"] = f"Your sleep logs show alcohol use on {user_patterns['alcohol_frequency']} recent nights. The reduction plan will likely show quick sleep improvements."
            
        # Add correlation insights
        correlations = user_patterns.get("sleep_quality_correlation", {})
        if correlations:
            impact_key = f"{substance}_impact"
            if impact_key in correlations and correlations[impact_key] > 0.5:
                personalized["motivation"] = f"Your data shows {substance} increases your night awakenings by {correlations[impact_key]:.1f} times - reducing it should directly improve your sleep!"
                
        return personalized

    def _connect_to_sleep_impact(self, substances: List[str], user_patterns: Dict[str, Any]) -> str:
        """Show specific sleep impact based on user's data with enhanced insights."""
        if not substances:
            return ""
            
        impacts = []
        correlations = user_patterns.get('sleep_quality_correlation', {})
        
        for substance in substances:
            impact_key = f"{substance}_impact"
            quality_key = f"{substance}_quality_impact"  
            
            if impact_key in correlations and correlations[impact_key] > 0:
                impacts.append(f"**{substance.title()}**: +{correlations[impact_key]:.1f} more awakenings per night")
                
            if quality_key in correlations and correlations[quality_key] > 0:
                impacts.append(f"**{substance.title()}**: -{correlations[quality_key]:.1f} sleep quality points")
        
        # Add trend information
        trend = user_patterns.get("recent_trend", "")
        if trend == "increasing":
            impacts.append("📈 **Trend**: Your usage appears to be increasing recently")
        elif trend == "decreasing": 
            impacts.append("📉 **Trend**: Good news - your usage has been decreasing!")
            
        # Add worst correlation nights
        worst_nights = user_patterns.get("worst_sleep_nights", [])
        if worst_nights:
            substances_text = " and ".join(worst_nights)
            impacts.append(f"🔍 **Pattern**: {substances_text} appears on 60%+ of your worst sleep nights")
        
        if impacts:
            return "**📊 Your Personal Sleep Impact:**\n" + "\n".join(f"• {impact}" for impact in impacts) + "\n\n"
        return ""

    def _should_check_progress(self, user_patterns: Dict[str, Any]) -> bool:
        """Enhanced progress checking logic."""
        return (user_patterns.get('caffeine_frequency', 0) > 10 or 
                user_patterns.get('alcohol_frequency', 0) > 5 or
                user_patterns.get('total_logs', 0) > 14)  # More than 2 weeks of data

    def _generate_progress_check(self, user_patterns: Dict[str, Any]) -> str:
        """Generate personalized follow-up questions about progress."""
        checks = []
        
        if user_patterns.get('caffeine_frequency', 0) > 10:
            checks.append("How has your caffeine reduction plan been going? Any challenges with afternoon cravings?")
            
        if user_patterns.get('alcohol_frequency', 0) > 5:
            checks.append("How are you feeling about your alcohol reduction goals? Notice any sleep improvements?")
            
        trend = user_patterns.get("recent_trend", "")
        if trend == "increasing":
            checks.append("I notice your usage might be increasing - what challenges are you facing?")
        elif trend == "decreasing":
            checks.append("Great job on reducing your usage! What strategies have been working best for you?")
            
        if checks:
            return f"\n\n💭 **Follow-up**: {' '.join(checks)}"
        return ""

    def _get_crisis_resources(self, substances: List[str]) -> List[str]:
        """Provide crisis resources based on substance type."""
        resources = [
            "🚨 **Immediate Help**: If experiencing severe withdrawal, call 911",
            "📞 **SAMHSA National Helpline**: 1-800-662-4357 (free, confidential, 24/7)",
            "🏥 **Find Treatment**: samhsa.gov/find-help/national-helpline"
        ]
        
        if "alcohol" in substances:
            resources.extend([
                "🍺 **Alcoholics Anonymous**: aa.org",
                "⚡ **Crisis Text Line**: Text HOME to 741741"
            ])
            
        if "nicotine" in substances:
            resources.extend([
                "🚭 **Quitline**: 1-800-QUIT-NOW",
                "💊 **FDA-approved medications**: Talk to your doctor"
            ])
            
        return resources

    async def _handle_core(self, message: str, ctx: Optional[AgentContext] = None) -> AgentResponse:
        """Enhanced core handler with better error handling and personalization."""
        ctx = ctx or {}
        user = ctx.get("user")
        
        # Assess severity and substances
        severity, substances = self._assess_addiction_severity(message)
        
        # If no specific substance detected, show a generic support chooser
        if not substances:
            return {
                "agent": self.name,
                "text": (
                    "I'm here to help with addiction concerns related to sleep. "
                    "I can provide support for:\n"
                    "• ☕ **Caffeine** (coffee, tea, energy drinks)\n"
                    "• 🍷 **Alcohol** dependency issues\n"
                    "• 🚬 **Nicotine** and tobacco use\n"
                    "• 📱 **Digital/Screen time** addiction\n\n"
                    "What would you like support with today?"
                )
            }
        
        # Get user's historical patterns
        user_patterns = {}
        if user and user.get("id"):
            user_patterns = await self._get_user_addiction_history(user.get("id"))
        
        # Handle high severity cases with crisis resources
        if severity == "high_severity":
            crisis_resources = self._get_crisis_resources(substances)
            crisis_text = "\n".join(crisis_resources)
            
            return {
                "agent": self.name,
                "text": (
                    f"I'm concerned about the severity of what you're describing with {', '.join(substances)}. "
                    "Your safety is the top priority, and withdrawal from some substances can be medically dangerous.\n\n"
                    f"{crisis_text}\n\n"
                    "Please reach out to a healthcare provider or crisis line immediately. "
                    "I'm here to support you, but professional medical guidance is essential right now.\n\n"
                    f"{DISCLAIMER}"
                ),
                "data": {
                    "severity": severity,
                    "substances": substances,
                    "intervention_level": "CRISIS",
                    "requires_immediate_attention": True
                }
            }
        
        # Generate enhanced LLM response
        sleep_impact_text = self._connect_to_sleep_impact(substances, user_patterns)
        
        prompt = self._build_llm_prompt(message, severity, substances, user_patterns)
        
        llm_response = ""
        if gemini_ready():
            try:
                llm_response = await generate_gemini_text(prompt, model_name="gemini-2.0-flash-exp")
            except Exception as e:
                print(f"Error calling Gemini API in addiction agent: {e}")
                # Fallback response
                llm_response = self._generate_fallback_response(substances, severity)
        else:
            llm_response = self._generate_fallback_response(substances, severity)
        
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
        
        # Format reduction plans for display
        plans_text = self._format_reduction_plans(reduction_plans)
        
        # Combine response
        full_response = f"{sleep_impact_text}{llm_response}\n\n{plans_text}{progress_check}\n\n{DISCLAIMER}"
        
        return {
            "agent": self.name,
            "text": full_response,
            "data": {
                "severity": severity,
                "substances": substances,
                "reduction_plans": reduction_plans,
                "user_patterns": user_patterns,
                "sleep_correlations": user_patterns.get('sleep_quality_correlation', {}),
                "intervention_level": INTERVENTION_LEVELS.get(severity, "EDUCATIONAL")
            }
        }

    def _build_llm_prompt(self, message: str, severity: str, substances: List[str], user_patterns: Dict[str, Any]) -> str:
        """Build comprehensive LLM prompt with context."""
        return f"""
        You are an expert addiction support counselor specializing in sleep-related dependencies.
        
        User message: "{message}"
        Detected severity: {severity}
        Substances mentioned: {', '.join(substances)}
        
        User's recent patterns (last 30 days):
        - Caffeine after 3pm: {user_patterns.get('caffeine_frequency', 0)} times
        - Alcohol use: {user_patterns.get('alcohol_frequency', 0)} times  
        - Average screen time: {user_patterns.get('avg_screen_time', 0):.1f} minutes
        - Total sleep logs: {user_patterns.get('total_logs', 0)}
        - Usage trend: {user_patterns.get('recent_trend', 'unknown')}
        
        Provide a response that:
        1. Acknowledges their specific concern with empathy (2-3 sentences)
        2. References their actual usage patterns if available
        3. Gives specific, actionable advice for their situation
        4. Explains how this impacts their sleep quality
        5. Provides 2-3 immediate coping strategies
        6. Sets realistic expectations for improvement timeline
        
        Keep it supportive, non-judgmental, and focused on gradual progress.
        Use a warm, encouraging tone. Be specific rather than generic.
        Limit to 150-200 words for the main response.
        """

    def _generate_fallback_response(self, substances: List[str], severity: str) -> str:
        """Generate fallback response when LLM is unavailable."""
        substance_text = ', '.join(substances)
        
        if severity == "high_severity":
            return (
                f"I understand you're struggling with {substance_text} dependency, and it takes courage to reach out. "
                "This level of concern suggests you may benefit from professional support. "
                f"Reducing {substance_text} gradually is usually the safest approach, but medical guidance is important for your situation."
            )
        elif severity == "medium_severity":
            return (
                f"Thank you for sharing your concerns about {substance_text}. Many people struggle with similar issues, "
                "and recognizing the impact on your sleep is an important first step. "
                f"Reducing {substance_text} gradually is usually the most sustainable approach, and your sleep quality should start improving within 1-2 weeks of making changes."
            )
        else:
            return (
                f"I appreciate you bringing up your concerns about {substance_text}. "
                "Making small, consistent changes is often the most effective approach. "
                f"Even modest reductions in {substance_text} can lead to noticeable improvements in sleep quality."
            )

    def _format_reduction_plans(self, reduction_plans: Dict[str, Dict[str, Any]]) -> str:
        """Format reduction plans for user display."""
        if not reduction_plans:
            return ""
            
        formatted_plans = []
        
        for substance, plan in reduction_plans.items():
            if not plan:
                continue
                
            plan_text = f"### 🎯 {substance.title()} Reduction Plan\n"
            
            if "warning" in plan:
                plan_text += f"⚠️ **Important**: {plan['warning']}\n\n"
                
            if "timeline" in plan:
                plan_text += f"**Timeline**: {plan['timeline']}\n\n"
                
            if "steps" in plan:
                plan_text += "**Steps**:\n"
                for i, step in enumerate(plan["steps"], 1):
                    plan_text += f"{i}. {step}\n"
                plan_text += "\n"
                
            if "alternatives" in plan:
                plan_text += f"**Healthy Alternatives**: {', '.join(plan['alternatives'])}\n\n"
                
            if "sleep_benefit" in plan:
                plan_text += f"**Expected Sleep Improvement**: {plan['sleep_benefit']}\n\n"
                
            if "personal_note" in plan:
                plan_text += f"**Personal Insight**: {plan['personal_note']}\n\n"
                
            if "motivation" in plan:
                plan_text += f"**Your Motivation**: {plan['motivation']}\n\n"
                
            if "resources" in plan:
                plan_text += "**Resources**:\n"
                for resource in plan["resources"]:
                    plan_text += f"• {resource}\n"
                plan_text += "\n"

            # Add quick, practical suggestions regardless of severity or LLM response
            quick_suggestions = self._get_quick_suggestions(substance)
            if quick_suggestions:
                plan_text += "**Quick Suggestions**:\n"
                for tip in quick_suggestions:
                    plan_text += f"• {tip}\n"
                plan_text += "\n"
                
            formatted_plans.append(plan_text)
        
        return "\n".join(formatted_plans) if formatted_plans else ""

    def _get_quick_suggestions(self, substance: str) -> List[str]:
        """Provide 3-5 actionable tips to begin cutting back today."""
        s = (substance or "").lower()
        if s == "caffeine":
            return [
                "Set a hard cutoff at least 6 hours before bedtime",
                "Swap one daily coffee/energy drink for water or herbal tea",
                "Keep decaf or low‑caffeine options ready for afternoon cravings",
                "Track headaches and sleep for 1 week while reducing",
                "Avoid caffeine on an empty stomach to reduce rebound cravings"
            ]
        if s == "alcohol":
            return [
                "Plan 3–5 alcohol‑free nights per week",
                "Replace the evening drink with a relaxing ritual (tea, shower, reading)",
                "Hydrate: 1 glass of water per alcoholic drink",
                "Avoid alcohol within 3 hours of bedtime",
                "Set a weekly limit and log drinks to stay accountable"
            ]
        if s == "nicotine":
            return [
                "Delay the first nicotine use by 30 minutes each day",
                "Use nicotine replacement (patch/gum/lozenge) to taper safely",
                "Identify and avoid evening trigger zones (sofa+phone, gaming setup)",
                "Practice a 4‑7‑8 breath or short walk when an urge hits",
                "Make the bedroom a nicotine‑free space"
            ]
        if s == "digital":
            return [
                "Create a phone‑free bedroom; charge the device outside",
                "Set “No screens” 60 minutes before bed (use Focus/Do Not Disturb)",
                "Switch phone to grayscale to reduce novelty seeking",
                "Replace scrolling with a 10–15 minute wind‑down routine",
                "Uninstall or log out of the most tempting apps before bedtime"
            ]
        return []