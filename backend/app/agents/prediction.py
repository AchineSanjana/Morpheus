# app/agents/prediction.py
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import statistics
import os
import json
from . import BaseAgent, AgentContext, AgentResponse
from app.llm_gemini import generate_gemini_text
from app.db import fetch_recent_logs

class SleepPredictionAgent(BaseAgent):
    """AI-powered sleep prediction and optimization recommendations"""
    name = "prediction"
    
    def __init__(self):
        super().__init__()
        self.action_type = "predictive_analysis"  # For responsible AI transparency
        self.prediction_models = self._initialize_models()
    
    def _initialize_models(self) -> Dict[str, Any]:
        """Initialize prediction models with sensible defaults"""
        return {
            "sleep_quality": {
                "weights": {
                    "caffeine_after3pm": -1.2,
                    "alcohol": -0.8,
                    "screen_time": -0.01,  # per minute
                    "stress_level": -0.3,  # per point on 1-10 scale
                    "exercise_today": 0.5,
                    "consistency_bonus": 1.0,
                    "weekend_penalty": -0.3
                },
                "baseline": 7.0
            },
            "duration": {
                "weights": {
                    "caffeine_after3pm": -0.3,
                    "alcohol": -0.5,
                    "screen_time": -0.005,
                    "stress_level": -0.1,
                    "exercise_today": 0.2,
                    "age_factor": -0.02  # per year over 25
                },
                "baseline": 7.5
            }
        }
    
    async def predict_sleep_quality(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Predict tonight's sleep quality based on daily factors"""
        try:
            # Extract features
            features = self._extract_prediction_features(user_data)
            
            # Calculate predictions using rule-based model
            quality_score = self._calculate_quality_score(features)
            duration_pred = self._calculate_duration_prediction(features)
            
            # Analyze contributing factors
            factors_analysis = self._analyze_contributing_factors(features, user_data)
            
            return {
                "predicted_quality": self._categorize_quality(quality_score),
                "quality_score": round(quality_score, 1),
                "predicted_duration": round(duration_pred, 1),
                "confidence": self._calculate_confidence(features, user_data),
                "factors_analysis": factors_analysis,
                "recommendations": self._generate_recommendations(factors_analysis)
            }
        except Exception as e:
            # Fallback prediction
            return self._fallback_prediction(user_data)
    
    async def optimal_bedtime_recommendation(self, user_id: str, target_wake_time: str = "07:00") -> Dict[str, Any]:
        """AI-powered optimal bedtime suggestions"""
        try:
            # Get user's historical data
            logs = await fetch_recent_logs(user_id, days=30)
            
            if not logs:
                return self._default_bedtime_recommendation(target_wake_time)
            
            # Analyze user's sleep patterns
            user_profile = self._build_user_sleep_profile(logs)
            
            # Calculate optimal bedtime
            optimal_time = self._calculate_optimal_bedtime(user_profile, target_wake_time)
            
            return {
                "recommended_bedtime": optimal_time,
                "reasoning": self._generate_bedtime_reasoning(user_profile, optimal_time),
                "sleep_window": self._calculate_sleep_window(user_profile),
                "preparation_timeline": self._create_bedtime_timeline(optimal_time),
                "user_pattern_confidence": self._assess_pattern_confidence(logs)
            }
        except Exception as e:
            return self._default_bedtime_recommendation(target_wake_time)
    
    def _extract_prediction_features(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and normalize features for prediction"""
        current_time = datetime.now()
        
        return {
            "current_hour": current_time.hour,
            "day_of_week": current_time.weekday(),
            "is_weekend": current_time.weekday() >= 5,
            "caffeine_after3pm": bool(user_data.get("caffeine_after3pm", False)),
            "alcohol": bool(user_data.get("alcohol", False)),
            "screen_time_min": float(user_data.get("screen_time_min", 60)),
            "stress_level": float(user_data.get("stress_level", 5)),  # 1-10 scale
            "exercise_today": bool(user_data.get("exercise_today", False)),
            "avg_duration": float(user_data.get("avg_duration", 7.5)),
            "avg_quality": float(user_data.get("avg_quality", 7.0)),
            "recent_consistency": float(user_data.get("recent_consistency", 0.5)),
            "age": int(user_data.get("age", 30))
        }
    
    def _calculate_quality_score(self, features: Dict[str, Any]) -> float:
        """Calculate predicted sleep quality score (1-10)"""
        model = self.prediction_models["sleep_quality"]
        score = model["baseline"]
        
        # Apply feature weights
        if features["caffeine_after3pm"]:
            score += model["weights"]["caffeine_after3pm"]
        
        if features["alcohol"]:
            score += model["weights"]["alcohol"]
        
        score += model["weights"]["screen_time"] * features["screen_time_min"]
        score += model["weights"]["stress_level"] * features["stress_level"]
        
        if features["exercise_today"]:
            score += model["weights"]["exercise_today"]
        
        # Consistency bonus
        score += model["weights"]["consistency_bonus"] * features["recent_consistency"]
        
        # Weekend penalty (late bedtime tendency)
        if features["is_weekend"]:
            score += model["weights"]["weekend_penalty"]
        
        # Clamp to valid range
        return max(1.0, min(10.0, score))
    
    def _calculate_duration_prediction(self, features: Dict[str, Any]) -> float:
        """Calculate predicted sleep duration in hours"""
        model = self.prediction_models["duration"]
        duration = model["baseline"]
        
        # Apply feature weights
        if features["caffeine_after3pm"]:
            duration += model["weights"]["caffeine_after3pm"]
        
        if features["alcohol"]:
            duration += model["weights"]["alcohol"]
        
        duration += model["weights"]["screen_time"] * features["screen_time_min"]
        duration += model["weights"]["stress_level"] * features["stress_level"]
        
        if features["exercise_today"]:
            duration += model["weights"]["exercise_today"]
        
        # Age factor (sleep duration typically decreases with age)
        age_over_25 = max(0, features["age"] - 25)
        duration += model["weights"]["age_factor"] * age_over_25
        
        # Clamp to reasonable range
        return max(4.0, min(12.0, duration))
    
    def _categorize_quality(self, score: float) -> str:
        """Convert numeric score to quality category"""
        if score >= 8.5: return "excellent"
        elif score >= 7.0: return "good"
        elif score >= 5.5: return "fair"
        elif score >= 4.0: return "poor"
        else: return "very poor"
    
    def _analyze_contributing_factors(self, features: Dict[str, Any], user_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Analyze which factors are impacting tonight's prediction"""
        factors = {
            "positive_factors": [],
            "risk_factors": [],
            "neutral_factors": []
        }
        
        # Caffeine analysis
        if not features["caffeine_after3pm"]:
            factors["positive_factors"].append("No late caffeine consumption - supports natural sleep onset")
        else:
            factors["risk_factors"].append("Caffeine after 3pm may delay sleep and reduce quality")
        
        # Alcohol analysis
        if not features["alcohol"]:
            factors["positive_factors"].append("No alcohol consumption - promotes deeper sleep cycles")
        else:
            factors["risk_factors"].append("Alcohol may fragment sleep and reduce REM quality")
        
        # Screen time analysis
        if features["screen_time_min"] <= 30:
            factors["positive_factors"].append("Low screen time before bed - minimal blue light exposure")
        elif features["screen_time_min"] <= 90:
            factors["neutral_factors"].append("Moderate screen time - consider reducing 1-2 hours before bed")
        else:
            factors["risk_factors"].append("High screen time may suppress melatonin production")
        
        # Stress analysis
        if features["stress_level"] <= 3:
            factors["positive_factors"].append("Low stress levels - conducive to restful sleep")
        elif features["stress_level"] <= 6:
            factors["neutral_factors"].append("Moderate stress - consider relaxation techniques")
        else:
            factors["risk_factors"].append("High stress may cause difficulty falling asleep")
        
        # Exercise analysis
        if features["exercise_today"]:
            factors["positive_factors"].append("Exercise today - improves sleep quality and depth")
        else:
            factors["neutral_factors"].append("No exercise today - regular activity benefits sleep")
        
        # Weekend patterns
        if features["is_weekend"]:
            factors["neutral_factors"].append("Weekend pattern - maintain consistent sleep schedule")
        
        return factors
    
    def _calculate_confidence(self, features: Dict[str, Any], user_data: Dict[str, Any]) -> int:
        """Calculate prediction confidence as percentage"""
        confidence = 70  # Base confidence
        
        # Increase confidence with consistent patterns
        if features["recent_consistency"] > 0.7:
            confidence += 15
        elif features["recent_consistency"] < 0.3:
            confidence -= 10
        
        # Increase confidence with historical data
        if user_data.get("historical_logs_count", 0) > 14:
            confidence += 10
        elif user_data.get("historical_logs_count", 0) < 7:
            confidence -= 15
        
        # Decrease confidence for extreme values
        if features["stress_level"] > 8 or features["screen_time_min"] > 180:
            confidence -= 10
        
        return max(50, min(95, confidence))
    
    def _generate_recommendations(self, factors_analysis: Dict[str, List[str]]) -> List[str]:
        """Generate actionable recommendations to improve predicted sleep"""
        recommendations = []
        
        # Address risk factors
        risk_factors = factors_analysis.get("risk_factors", [])
        
        for risk in risk_factors:
            if "caffeine" in risk.lower():
                recommendations.append("🚫 Avoid caffeine after 2pm tomorrow to improve sleep onset")
            elif "alcohol" in risk.lower():
                recommendations.append("🍷 Consider limiting alcohol, especially within 3 hours of bedtime")
            elif "screen" in risk.lower():
                recommendations.append("📱 Enable night mode and reduce screen time 1-2 hours before bed")
            elif "stress" in risk.lower():
                recommendations.append("🧘 Try relaxation techniques: deep breathing, meditation, or gentle stretching")
        
        # Add general improvement suggestions
        if len(recommendations) == 0:
            recommendations.append("✨ Your factors look good! Maintain your current routine for optimal sleep")
        
        # Add one universal tip
        recommendations.append("🌙 Keep your bedroom cool (65-68°F) and dark for best sleep quality")
        
        return recommendations[:3]  # Limit to top 3 recommendations
    
    def _fallback_prediction(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Provide fallback prediction when main prediction fails"""
        return {
            "predicted_quality": "fair",
            "quality_score": 6.5,
            "predicted_duration": 7.0,
            "confidence": 60,
            "factors_analysis": {
                "positive_factors": ["Assessment based on general sleep health principles"],
                "risk_factors": [],
                "neutral_factors": ["Limited data available for detailed prediction"]
            },
            "recommendations": [
                "🌙 Maintain a consistent bedtime routine",
                "📱 Avoid screens 1 hour before bed",
                "🧘 Practice relaxation techniques"
            ]
        }
    
    def _build_user_sleep_profile(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build user's sleep pattern profile from historical data"""
        if not logs:
            return {}
        
        durations = [log.get("duration_h") for log in logs if log.get("duration_h")]
        bedtimes = []
        wake_times = []
        
        for log in logs:
            if log.get("bedtime"):
                try:
                    bt = datetime.fromisoformat(log["bedtime"])
                    bedtimes.append(bt.hour + bt.minute/60)
                except:
                    pass
            
            if log.get("wake_time"):
                try:
                    wt = datetime.fromisoformat(log["wake_time"])
                    wake_times.append(wt.hour + wt.minute/60)
                except:
                    pass
        
        profile = {
            "avg_duration": statistics.mean(durations) if durations else 7.5,
            "duration_std": statistics.stdev(durations) if durations and len(durations) > 1 else 1.0,
            "avg_bedtime": statistics.mean(bedtimes) if bedtimes else 23.0,
            "bedtime_std": statistics.stdev(bedtimes) if bedtimes and len(bedtimes) > 1 else 1.0,
            "avg_wake_time": statistics.mean(wake_times) if wake_times else 7.0,
            "consistency_score": self._calculate_consistency_score(logs),
            "total_logs": len(logs)
        }
        
        return profile
    
    def _calculate_consistency_score(self, logs: List[Dict[str, Any]]) -> float:
        """Calculate how consistent the user's sleep schedule is (0-1)"""
        if len(logs) < 2:
            return 0.5
        
        bedtime_consistency = 0.5
        duration_consistency = 0.5
        
        # Calculate bedtime consistency
        bedtimes = []
        for log in logs:
            if log.get("bedtime"):
                try:
                    bt = datetime.fromisoformat(log["bedtime"])
                    bedtimes.append(bt.hour + bt.minute/60)
                except:
                    pass
        
        if len(bedtimes) > 1:
            std = statistics.stdev(bedtimes)
            bedtime_consistency = max(0, 1 - (std / 3))  # 3 hours std = 0 consistency
        
        # Calculate duration consistency
        durations = [log.get("duration_h") for log in logs if log.get("duration_h")]
        if len(durations) > 1:
            std = statistics.stdev(durations)
            duration_consistency = max(0, 1 - (std / 2))  # 2 hours std = 0 consistency
        
        return (bedtime_consistency + duration_consistency) / 2
    
    def _calculate_optimal_bedtime(self, user_profile: Dict[str, Any], target_wake_time: str) -> str:
        """Calculate optimal bedtime based on user's patterns and target wake time"""
        try:
            # Parse target wake time
            wake_hour, wake_min = map(int, target_wake_time.split(":"))
            wake_decimal = wake_hour + wake_min/60
            
            # Get user's average sleep duration (with some buffer)
            avg_duration = user_profile.get("avg_duration", 7.5)
            optimal_duration = min(avg_duration + 0.5, 9.0)  # Add 30min buffer, cap at 9h
            
            # Calculate bedtime
            bedtime_decimal = wake_decimal - optimal_duration
            
            # Handle negative hours (bedtime previous day)
            if bedtime_decimal < 0:
                bedtime_decimal += 24
            
            # Convert back to time format
            bedtime_hour = int(bedtime_decimal)
            bedtime_min = int((bedtime_decimal - bedtime_hour) * 60)
            
            return f"{bedtime_hour:02d}:{bedtime_min:02d}"
            
        except Exception:
            # Fallback to 11 PM
            return "23:00"
    
    def _generate_bedtime_reasoning(self, user_profile: Dict[str, Any], optimal_time: str) -> str:
        """Generate explanation for bedtime recommendation"""
        avg_duration = user_profile.get("avg_duration", 7.5)
        consistency = user_profile.get("consistency_score", 0.5)
        
        reasoning = f"Based on your average sleep duration of {avg_duration:.1f} hours"
        
        if consistency > 0.7:
            reasoning += " and your consistent sleep patterns"
        elif consistency < 0.3:
            reasoning += " (though your schedule varies - try to be more consistent)"
        
        reasoning += f", sleeping at {optimal_time} should help you feel refreshed and maintain healthy sleep cycles."
        
        return reasoning
    
    def _calculate_sleep_window(self, user_profile: Dict[str, Any]) -> Dict[str, str]:
        """Calculate the optimal sleep window range"""
        avg_bedtime = user_profile.get("avg_bedtime", 23.0)
        std = user_profile.get("bedtime_std", 1.0)
        
        # Calculate range (±1 std deviation)
        early_time = max(20.0, avg_bedtime - std)  # Not earlier than 8 PM
        late_time = min(2.0, avg_bedtime + std)   # Not later than 2 AM
        
        def _time_format(decimal_hour: float) -> str:
            if decimal_hour >= 24:
                decimal_hour -= 24
            hour = int(decimal_hour)
            minute = int((decimal_hour - hour) * 60)
            return f"{hour:02d}:{minute:02d}"
        
        return {
            "earliest": _time_format(early_time),
            "latest": _time_format(late_time)
        }
    
    def _create_bedtime_timeline(self, optimal_bedtime: str) -> List[Dict[str, str]]:
        """Create a preparation timeline for optimal sleep"""
        try:
            # Parse optimal bedtime
            bed_hour, bed_min = map(int, optimal_bedtime.split(":"))
            bedtime = datetime.now().replace(hour=bed_hour, minute=bed_min, second=0, microsecond=0)
            
            # Create timeline
            timeline = []
            
            # 2 hours before: Last caffeine
            time_2h = bedtime - timedelta(hours=2)
            timeline.append({
                "time": time_2h.strftime("%H:%M"),
                "activity": "🚫 Last chance for caffeine - switch to herbal tea"
            })
            
            # 1.5 hours before: Last meal
            time_90m = bedtime - timedelta(minutes=90)
            timeline.append({
                "time": time_90m.strftime("%H:%M"),
                "activity": "🍽️ Finish eating - allow time for digestion"
            })
            
            # 1 hour before: Screen shutdown
            time_1h = bedtime - timedelta(hours=1)
            timeline.append({
                "time": time_1h.strftime("%H:%M"),
                "activity": "📱 Begin winding down - dim lights, reduce screen time"
            })
            
            # 30 minutes before: Relaxation
            time_30m = bedtime - timedelta(minutes=30)
            timeline.append({
                "time": time_30m.strftime("%H:%M"),
                "activity": "🧘 Start relaxation routine - reading, meditation, or gentle stretching"
            })
            
            # 15 minutes before: Final prep
            time_15m = bedtime - timedelta(minutes=15)
            timeline.append({
                "time": time_15m.strftime("%H:%M"),
                "activity": "🛏️ Final preparations - bathroom, set tomorrow's clothes"
            })
            
            # Bedtime
            timeline.append({
                "time": optimal_bedtime,
                "activity": "😴 Lights out - time for sleep"
            })
            
            return timeline
            
        except Exception:
            # Fallback timeline
            return [
                {"time": "21:00", "activity": "🚫 Last caffeine of the day"},
                {"time": "22:00", "activity": "📱 Begin reducing screen time"},
                {"time": "22:30", "activity": "🧘 Start relaxation routine"},
                {"time": "23:00", "activity": "😴 Bedtime"}
            ]
    
    def _assess_pattern_confidence(self, logs: List[Dict[str, Any]]) -> str:
        """Assess confidence in user's sleep patterns"""
        if len(logs) < 3:
            return "low"
        elif len(logs) < 7:
            return "moderate"
        else:
            consistency = self._calculate_consistency_score(logs)
            if consistency > 0.7:
                return "high"
            elif consistency > 0.4:
                return "moderate"
            else:
                return "low"
    
    def _default_bedtime_recommendation(self, target_wake_time: str) -> Dict[str, Any]:
        """Provide default bedtime recommendation for new users"""
        try:
            # Parse target wake time
            wake_hour, wake_min = map(int, target_wake_time.split(":"))
            wake_decimal = wake_hour + wake_min/60
            
            # Assume 8 hours of sleep
            bedtime_decimal = wake_decimal - 8
            if bedtime_decimal < 0:
                bedtime_decimal += 24
            
            bedtime_hour = int(bedtime_decimal)
            bedtime_min = int((bedtime_decimal - bedtime_hour) * 60)
            optimal_time = f"{bedtime_hour:02d}:{bedtime_min:02d}"
            
        except Exception:
            optimal_time = "23:00"
        
        return {
            "recommended_bedtime": optimal_time,
            "reasoning": "Recommended based on healthy 8-hour sleep duration. As we learn your patterns, recommendations will become more personalized.",
            "sleep_window": {"earliest": "22:00", "latest": "24:00"},
            "preparation_timeline": self._create_bedtime_timeline(optimal_time),
            "user_pattern_confidence": "low"
        }
    
    def _extract_wake_time(self, message: str) -> Optional[str]:
        """Extract wake time from user message"""
        import re
        
        # Look for time patterns like "7:00", "07:00", "7am", etc.
        time_patterns = [
            r'\b(\d{1,2}):(\d{2})\b',
            r'\b(\d{1,2})\s*am\b',
            r'\b(\d{1,2})\s*pm\b'
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, message.lower())
            if match:
                if ':' in pattern:
                    hour, minute = match.groups()
                    return f"{int(hour):02d}:{int(minute):02d}"
                else:
                    hour = int(match.group(1))
                    if 'pm' in match.group(0) and hour != 12:
                        hour += 12
                    elif 'am' in match.group(0) and hour == 12:
                        hour = 0
                    return f"{hour:02d}:00"
        
        return None
    
    def _gather_current_context(self, ctx: Optional[AgentContext]) -> Dict[str, Any]:
        """Gather current day context for prediction"""
        user_data = {
            "caffeine_after3pm": False,
            "alcohol": False,
            "screen_time_min": 60,
            "stress_level": 5,
            "exercise_today": False,
            "avg_duration": 7.5,
            "avg_quality": 7.0,
            "recent_consistency": 0.5,
            "age": 30,
            "historical_logs_count": 0
        }
        
        # Try to extract from context if available
        if ctx:
            user = ctx.get("user", {})
            logs = ctx.get("logs", [])
            
            if logs:
                user_data["historical_logs_count"] = len(logs)
                
                # Calculate averages from recent logs
                durations = [log.get("duration_h") for log in logs if log.get("duration_h")]
                if durations:
                    user_data["avg_duration"] = statistics.mean(durations)
                
                # Get most recent day's data for today's context
                if logs:
                    recent_log = logs[-1]
                    user_data.update({
                        "caffeine_after3pm": recent_log.get("caffeine_after3pm", False),
                        "alcohol": recent_log.get("alcohol", False),
                        "screen_time_min": recent_log.get("screen_time_min", 60),
                    })
        
        return user_data
    
    def _format_factors(self, factors_analysis: Dict[str, List[str]]) -> str:
        """Format factors analysis for display"""
        output = []
        
        if factors_analysis.get("positive_factors"):
            output.append("**✅ Positive Factors:**")
            for factor in factors_analysis["positive_factors"]:
                output.append(f"• {factor}")
        
        if factors_analysis.get("risk_factors"):
            output.append("\n**⚠️ Risk Factors:**")
            for factor in factors_analysis["risk_factors"]:
                output.append(f"• {factor}")
        
        if factors_analysis.get("neutral_factors"):
            output.append("\n**ℹ️ Considerations:**")
            for factor in factors_analysis["neutral_factors"]:
                output.append(f"• {factor}")
        
        return "\n".join(output)
    
    def _format_timeline(self, timeline: List[Dict[str, str]]) -> str:
        """Format timeline for display"""
        output = []
        for item in timeline:
            output.append(f"**{item['time']}** - {item['activity']}")
        return "\n".join(output)
    
    async def _handle_core(self, message: str, ctx: Optional[AgentContext] = None) -> AgentResponse:
        """Handle prediction requests with AI-enhanced insights"""
        user = ctx.get("user") if ctx else None
        message_lower = message.lower()
        
        try:
            # Determine prediction type from message
            if any(word in message_lower for word in ["tonight", "today", "sleep quality", "how will", "predict"]):
                # Sleep quality prediction
                user_data = self._gather_current_context(ctx)
                prediction = await self.predict_sleep_quality(user_data)
                
                # Generate AI explanation
                ai_explanation = await self._generate_ai_explanation(prediction, message)
                
                response_text = f"""## 🔮 Sleep Quality Prediction for Tonight

**Predicted Quality**: {prediction['predicted_quality'].title()} ({prediction['quality_score']}/10)
**Expected Duration**: {prediction['predicted_duration']} hours
**Confidence**: {prediction['confidence']}%

{ai_explanation}

### Contributing Factors:
{self._format_factors(prediction['factors_analysis'])}

### 💡 Recommendations:
{chr(10).join(f"• {rec}" for rec in prediction['recommendations'])}
"""
                
                return {
                    "agent": self.name,
                    "text": response_text,
                    "data": {
                        "prediction_type": "sleep_quality",
                        "prediction": prediction,
                        "timestamp": datetime.now().isoformat()
                    }
                }
                
            elif any(word in message_lower for word in ["bedtime", "when should", "optimal", "sleep time"]):
                # Bedtime optimization
                target_wake = self._extract_wake_time(message) or "07:00"
                user_id = user["id"] if user else "default"
                bedtime_rec = await self.optimal_bedtime_recommendation(user_id, target_wake)
                
                response_text = f"""## ⏰ Optimal Bedtime Recommendation

**Recommended Bedtime**: {bedtime_rec['recommended_bedtime']}
**For Wake Time**: {target_wake}
**Pattern Confidence**: {bedtime_rec['user_pattern_confidence'].title()}

### 🧠 Reasoning:
{bedtime_rec['reasoning']}

### 🎯 Your Optimal Sleep Window:
**Earliest**: {bedtime_rec['sleep_window']['earliest']} | **Latest**: {bedtime_rec['sleep_window']['latest']}

### 📅 Preparation Timeline:
{self._format_timeline(bedtime_rec['preparation_timeline'])}
"""
                
                return {
                    "agent": self.name,
                    "text": response_text,
                    "data": {
                        "prediction_type": "bedtime_optimization",
                        "recommendation": bedtime_rec,
                        "timestamp": datetime.now().isoformat()
                    }
                }
            
            else:
                # General prediction insights
                response_text = await self._generate_general_predictions(ctx)
                
                return {
                    "agent": self.name,
                    "text": response_text,
                    "data": {
                        "prediction_type": "general_insights",
                        "timestamp": datetime.now().isoformat()
                    }
                }
                
        except Exception as e:
            # Error fallback
            return {
                "agent": self.name,
                "text": "I'm sorry, I'm having trouble generating predictions right now. Please try asking about your sleep quality or optimal bedtime, and I'll do my best to help!",
                "data": {
                    "error": str(e),
                    "prediction_type": "error_fallback",
                    "timestamp": datetime.now().isoformat()
                }
            }
    
    async def _generate_ai_explanation(self, prediction: Dict[str, Any], user_message: str) -> str:
        """Use Gemini to generate human-friendly prediction explanations"""
        prompt = f"""You are an expert sleep scientist explaining a sleep quality prediction to a user.

User asked: "{user_message}"

Prediction details:
- Quality: {prediction['predicted_quality']} ({prediction['quality_score']}/10)
- Duration: {prediction['predicted_duration']} hours
- Confidence: {prediction['confidence']}%
- Key factors: {prediction['factors_analysis']}

Provide a brief, encouraging explanation (2-3 sentences) that:
1. Acknowledges their question
2. Explains the prediction in simple terms
3. Offers one key insight or tip

Keep it positive, scientific but accessible, and actionable.
"""
        
        explanation = await generate_gemini_text(prompt)
        return explanation or f"Based on your current patterns and today's activities, I predict your sleep quality will be {prediction['predicted_quality']} tonight. The main factors influencing this prediction are your recent sleep consistency and today's lifestyle choices."
    
    async def _generate_general_predictions(self, ctx: Optional[AgentContext]) -> str:
        """Generate general predictive insights"""
        user = ctx.get("user") if ctx else None
        logs = ctx.get("logs", []) if ctx else []
        
        if not logs:
            return """## 🔮 Sleep Predictions

I'd love to provide personalized sleep predictions! To get started, please:

• **Log a few nights of sleep data** - this helps me understand your patterns
• **Ask about tonight's sleep quality** - I can predict based on your daily activities
• **Request bedtime recommendations** - I'll suggest optimal timing for your schedule

Once you have some sleep logs, I can provide insights like:
- Predicted sleep quality based on daily factors
- Optimal bedtime recommendations
- Personalized sleep improvement strategies"""
        
        # Generate insights based on available data
        user_data = self._gather_current_context(ctx)
        
        recent_trend = "stable"
        if len(logs) >= 3:
            recent_durations = [log.get("duration_h", 0) for log in logs[-3:]]
            if recent_durations[0] and recent_durations[-1]:
                if recent_durations[-1] > recent_durations[0] + 0.5:
                    recent_trend = "improving"
                elif recent_durations[-1] < recent_durations[0] - 0.5:
                    recent_trend = "declining"
        
        consistency_score = self._calculate_consistency_score(logs)
        consistency_desc = "excellent" if consistency_score > 0.7 else "good" if consistency_score > 0.4 else "needs improvement"
        
        return f"""## 🔮 Your Sleep Prediction Overview

### 📊 Current Patterns:
• **Sleep Trend**: Your recent sleep duration is **{recent_trend}**
• **Consistency**: Your sleep schedule consistency is **{consistency_desc}**
• **Data Confidence**: Based on **{len(logs)} logged nights**

### 🎯 What I Can Predict:
• **Ask "How will I sleep tonight?"** - Get quality predictions based on today's activities
• **Ask "When should I go to bed?"** - Get personalized bedtime recommendations
• **Request specific insights** about factors affecting your sleep

### 💡 Quick Insight:
{self._get_quick_insight(logs, user_data)}

*The more sleep data you log, the more accurate my predictions become!*"""
    
    def _get_quick_insight(self, logs: List[Dict[str, Any]], user_data: Dict[str, Any]) -> str:
        """Generate a quick insight based on available data"""
        if not logs:
            return "Start logging your sleep to unlock personalized predictions and insights!"
        
        # Look for patterns in recent logs
        recent_logs = logs[-7:] if len(logs) >= 7 else logs
        
        caffeine_days = sum(1 for log in recent_logs if log.get("caffeine_after3pm"))
        alcohol_days = sum(1 for log in recent_logs if log.get("alcohol"))
        
        if caffeine_days > len(recent_logs) / 2:
            return "I notice frequent late caffeine consumption in your logs. Cutting caffeine after 2pm could significantly improve your sleep quality!"
        elif alcohol_days > 0:
            return "Alcohol appears in some of your recent logs. Consider alcohol-free nights to see if your sleep quality improves!"
        else:
            durations_for_avg = [log.get("duration_h", 0) for log in recent_logs if log.get("duration_h")]
            if durations_for_avg:
                avg_duration = statistics.mean(durations_for_avg)
                if avg_duration < 7:
                    return "Your average sleep duration is below the recommended 7-9 hours. Try going to bed 30 minutes earlier!"
                else:
                    return "Your sleep patterns look good! Keep maintaining your current routine for optimal rest."
            else:
                return "Start logging more detailed sleep data to unlock personalized insights!"