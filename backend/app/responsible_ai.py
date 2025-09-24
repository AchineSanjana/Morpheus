# app/responsible_ai.py
"""
Responsible AI middleware for Morpheus Sleep AI Assistant
Implements fairness, transparency, and ethical data handling checks
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

# Configure logging for responsible AI monitoring
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ResponsibleAICheck:
    """Result of a responsible AI check"""
    passed: bool
    risk_level: RiskLevel
    category: str
    message: str
    suggestions: List[str]
    metadata: Dict[str, Any] = None

class ResponsibleAIMiddleware:
    """
    Centralized responsible AI checking system for all agents
    Ensures fairness, transparency, and ethical data handling
    """
    
    def __init__(self):
        self.fairness_patterns = self._init_fairness_patterns()
        self.transparency_required_actions = self._init_transparency_actions()
        self.privacy_sensitive_data = self._init_privacy_patterns()
        
    def _init_fairness_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns that could indicate bias or unfairness"""
        return {
            "age_bias": [
                r"\b(too old|too young|at your age|elderly|senior)\b",
                r"\byoung people|older people\b",
            ],
            "gender_bias": [
                r"\b(men|women|male|female) (are|should|need to|typically)\b",
                r"\bgender-specific\b",
            ],
            "cultural_bias": [
                r"\b(all people|everyone|typical|normal) (from|in) [A-Z][a-z]+\b",
                r"\bcultural assumptions\b",
            ],
            "socioeconomic_bias": [
                r"\b(poor|rich|wealthy|low-income|high-income) people\b",
                r"\bexpensive solutions only\b",
            ],
            "accessibility_bias": [
                r"\bjust (walk|run|exercise|go to gym)\b",
                r"\bsimply (avoid|stop|change)\b",
            ],
            "medical_assumptions": [
                r"\ball patients with\b",
                r"\beveryone with your condition\b",
            ]
        }
    
    def _init_transparency_actions(self) -> List[str]:
        """Actions that require transparency explanations"""
        return [
            "personalized_recommendation",
            "data_analysis",
            "pattern_detection",
            "risk_assessment",
            "behavioral_change_suggestion",
            "sleep_coaching_plan"
        ]
    
    def _init_privacy_patterns(self) -> Dict[str, List[str]]:
        """Patterns for detecting privacy-sensitive information"""
        return {
            "personal_identifiers": [
                r"\b\d{3}-\d{2}-\d{4}\b",  # SSN-like patterns
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
                r"\b\d{10,}\b",  # Phone numbers
            ],
            "medical_details": [
                r"\bmedication:|prescription:|diagnosis:",
                r"\bdoctor said|physician|specialist|therapist",
            ],
            "location_data": [
                r"\baddress:|live at|located at",
                r"\bGPS|coordinates|latitude|longitude",
            ],
            "financial_info": [
                r"\bincome:|salary:|credit card|bank account",
                r"\$\d+,?\d*\.?\d{0,2}",  # Dollar amounts
            ]
        }

    async def check_fairness(self, text: str, user_context: Dict[str, Any]) -> ResponsibleAICheck:
        """
        Check for potential bias and fairness issues in AI responses
        """
        issues = []
        suggestions = []
        risk_level = RiskLevel.LOW
        
        # Check for biased language patterns
        for bias_type, patterns in self.fairness_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    issues.append(f"Potential {bias_type.replace('_', ' ')} detected: {matches[0]}")
                    risk_level = RiskLevel.MEDIUM
        
        # Check for inclusive language
        inclusive_score = self._calculate_inclusive_language_score(text)
        if inclusive_score < 0.7:
            issues.append("Response may not be sufficiently inclusive")
            suggestions.append("Use more inclusive language that considers diverse backgrounds")
            risk_level = RiskLevel.MEDIUM
        
        # Check for accessibility considerations
        accessibility_score = self._check_accessibility_considerations(text)
        if accessibility_score < 0.8:
            issues.append("Response may not consider accessibility needs")
            suggestions.append("Include alternatives for users with different abilities")
        
        # Check for personalization without stereotyping
        if self._contains_stereotyping(text, user_context):
            issues.append("Response may contain stereotyping")
            suggestions.append("Provide personalized advice based on individual data, not assumptions")
            risk_level = RiskLevel.HIGH
        
        if not issues:
            suggestions.append("Response appears fair and unbiased")
        
        # Log fairness check
        logger.info(f"Fairness check completed - Issues: {len(issues)}, Risk: {risk_level.value}")
        
        return ResponsibleAICheck(
            passed=len(issues) == 0,
            risk_level=risk_level,
            category="fairness",
            message="; ".join(issues) if issues else "Fairness check passed",
            suggestions=suggestions,
            metadata={
                "inclusive_score": inclusive_score,
                "accessibility_score": accessibility_score,
                "bias_types_detected": [bias for bias in self.fairness_patterns.keys() 
                                      if any(re.search(p, text, re.IGNORECASE) 
                                           for p in self.fairness_patterns[bias])]
            }
        )
    
    async def check_transparency(self, 
                               text: str, 
                               action_type: str, 
                               data_sources: List[str],
                               decision_factors: Dict[str, Any]) -> ResponsibleAICheck:
        """
        Ensure transparency in AI decision-making and data usage
        """
        issues = []
        suggestions = []
        risk_level = RiskLevel.LOW
        
        # Check if transparency is required for this action
        requires_transparency = action_type in self.transparency_required_actions
        
        if requires_transparency:
            # Check for explanation of reasoning
            if not self._contains_explanation(text):
                issues.append("Response lacks explanation of AI reasoning")
                suggestions.append("Add explanation of how recommendations were generated")
                risk_level = RiskLevel.MEDIUM
            
            # Check for data source disclosure
            if not self._contains_data_source_info(text):
                issues.append("Response doesn't disclose data sources used")
                suggestions.append("Mention what data was analyzed to generate this response")
                risk_level = RiskLevel.MEDIUM
            
            # Check for uncertainty acknowledgment
            if not self._acknowledges_limitations(text):
                issues.append("Response doesn't acknowledge AI limitations")
                suggestions.append("Include disclaimer about AI limitations and when to seek human help")
                risk_level = RiskLevel.MEDIUM
        
        # Check for clear action attribution
        if not self._has_clear_attribution(text):
            issues.append("Response doesn't clearly identify it's from AI")
            suggestions.append("Make it clear this is AI-generated advice")
            risk_level = RiskLevel.LOW
        
        # Verify decision factors are explained
        if decision_factors and not self._explains_decision_factors(text, decision_factors):
            issues.append("Key decision factors not explained to user")
            suggestions.append("Explain what factors influenced this recommendation")
            risk_level = RiskLevel.MEDIUM
        
        if not issues:
            suggestions.append("Response meets transparency requirements")
        
        # Log transparency check
        logger.info(f"Transparency check completed - Action: {action_type}, Issues: {len(issues)}")
        
        return ResponsibleAICheck(
            passed=len(issues) == 0,
            risk_level=risk_level,
            category="transparency",
            message="; ".join(issues) if issues else "Transparency check passed",
            suggestions=suggestions,
            metadata={
                "action_type": action_type,
                "data_sources": data_sources,
                "decision_factors": list(decision_factors.keys()) if decision_factors else [],
                "requires_transparency": requires_transparency
            }
        )
    
    async def check_ethical_data_handling(self, 
                                        text: str,
                                        user_data: Dict[str, Any],
                                        data_retention_policy: str = "default") -> ResponsibleAICheck:
        """
        Ensure ethical handling of user data and privacy protection
        """
        issues = []
        suggestions = []
        risk_level = RiskLevel.LOW
        
        # Check for potential data leakage in response
        privacy_violations = self._detect_privacy_violations(text)
        if privacy_violations:
            issues.extend(privacy_violations)
            risk_level = RiskLevel.HIGH
            suggestions.append("Remove or anonymize sensitive information")
        
        # Check for appropriate data minimization
        if not self._follows_data_minimization(user_data):
            issues.append("More data collected than necessary for sleep coaching")
            suggestions.append("Only collect data essential for sleep improvement")
            risk_level = RiskLevel.MEDIUM
        
        # Check for consent compliance
        if not self._has_appropriate_consent_language(text):
            issues.append("Response lacks appropriate consent language")
            suggestions.append("Include information about data usage and user rights")
            risk_level = RiskLevel.MEDIUM
        
        # Check for data security mentions when handling sensitive info
        if self._handles_sensitive_data(user_data) and not self._mentions_security(text):
            issues.append("No security assurance for sensitive data handling")
            suggestions.append("Mention data security measures when handling sensitive information")
            risk_level = RiskLevel.MEDIUM
        
        # Check for user control and rights information
        if not self._mentions_user_rights(text):
            issues.append("Response doesn't inform about user data rights")
            suggestions.append("Include information about user's right to access, modify, or delete data")
            risk_level = RiskLevel.LOW
        
        if not issues:
            suggestions.append("Ethical data handling requirements met")
        
        # Log ethical data handling check
        logger.info(f"Ethical data handling check completed - Issues: {len(issues)}, Risk: {risk_level.value}")
        
        return ResponsibleAICheck(
            passed=len(issues) == 0,
            risk_level=risk_level,
            category="ethical_data_handling",
            message="; ".join(issues) if issues else "Ethical data handling check passed",
            suggestions=suggestions,
            metadata={
                "privacy_violations": privacy_violations,
                "data_retention_policy": data_retention_policy,
                "sensitive_data_detected": self._handles_sensitive_data(user_data),
                "data_types": list(user_data.keys()) if user_data else []
            }
        )
    
    async def comprehensive_check(self,
                                text: str,
                                action_type: str,
                                user_context: Dict[str, Any],
                                data_sources: List[str] = None,
                                decision_factors: Dict[str, Any] = None) -> Dict[str, ResponsibleAICheck]:
        """
        Run all responsible AI checks and return comprehensive results
        """
        results = {}
        
        # Run all checks in parallel for efficiency
        fairness_check = await self.check_fairness(text, user_context)
        transparency_check = await self.check_transparency(
            text, action_type, data_sources or [], decision_factors or {}
        )
        ethical_check = await self.check_ethical_data_handling(
            text, user_context
        )
        
        results = {
            "fairness": fairness_check,
            "transparency": transparency_check,
            "ethical_data_handling": ethical_check
        }
        
        # Determine overall risk level
        risk_levels = [check.risk_level for check in results.values()]
        overall_risk = max(risk_levels, key=lambda x: ["low", "medium", "high", "critical"].index(x.value))
        
        # Log comprehensive check
        logger.info(f"Comprehensive responsible AI check completed - Overall risk: {overall_risk.value}")
        
        results["overall"] = ResponsibleAICheck(
            passed=all(check.passed for check in results.values()),
            risk_level=overall_risk,
            category="comprehensive",
            message="Comprehensive responsible AI check completed",
            suggestions=[],
            metadata={
                "timestamp": datetime.now().isoformat(),
                "checks_run": list(results.keys()),
                "overall_passed": all(check.passed for check in results.values())
            }
        )
        
        return results
    
    # Helper methods for specific checks
    
    def _calculate_inclusive_language_score(self, text: str) -> float:
        """Calculate how inclusive the language is (0.0 to 1.0)"""
        inclusive_terms = [
            "everyone", "all people", "individuals", "people", "users",
            "may", "might", "could", "consider", "explore", "options"
        ]
        exclusive_terms = [
            "all women", "all men", "typical", "normal", "standard",
            "everyone should", "you must", "always", "never"
        ]
        
        inclusive_count = sum(1 for term in inclusive_terms if term in text.lower())
        exclusive_count = sum(1 for term in exclusive_terms if term in text.lower())
        
        if inclusive_count + exclusive_count == 0:
            return 0.8  # Neutral default
        
        return inclusive_count / (inclusive_count + exclusive_count + 1)
    
    def _check_accessibility_considerations(self, text: str) -> float:
        """Check if response considers accessibility needs"""
        accessible_language = [
            "alternative", "option", "adapt", "modify", "accommodate",
            "if you're able", "as comfortable", "within your abilities"
        ]
        
        inaccessible_language = [
            "just", "simply", "easy", "quick", "obviously", "clearly"
        ]
        
        accessible_count = sum(1 for term in accessible_language if term in text.lower())
        inaccessible_count = sum(1 for term in inaccessible_language if term in text.lower())
        
        if accessible_count + inaccessible_count == 0:
            return 0.9  # Neutral default, slightly positive
        
        return (accessible_count + 1) / (accessible_count + inaccessible_count + 1)
    
    def _contains_stereotyping(self, text: str, user_context: Dict[str, Any]) -> bool:
        """Check if response contains stereotyping based on user attributes"""
        stereotyping_patterns = [
            r"people like you",
            r"given your (age|gender|background)",
            r"typical for someone who",
            r"most (men|women|people) your age"
        ]
        
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in stereotyping_patterns)
    
    def _contains_explanation(self, text: str) -> bool:
        """Check if response contains explanation of reasoning"""
        explanation_indicators = [
            "based on", "because", "due to", "analysis shows", "data indicates",
            "considering your", "taking into account", "the reason", "this suggests"
        ]
        
        return any(indicator in text.lower() for indicator in explanation_indicators)
    
    def _contains_data_source_info(self, text: str) -> bool:
        """Check if response mentions data sources"""
        data_source_indicators = [
            "your sleep logs", "based on your data", "from your records",
            "your sleep history", "tracking shows", "your patterns"
        ]
        
        return any(indicator in text.lower() for indicator in data_source_indicators)
    
    def _acknowledges_limitations(self, text: str) -> bool:
        """Check if response acknowledges AI limitations"""
        limitation_indicators = [
            "disclaimer", "not medical advice", "consult", "healthcare provider",
            "limitations", "may not apply", "individual results", "seek professional"
        ]
        
        return any(indicator in text.lower() for indicator in limitation_indicators)
    
    def _has_clear_attribution(self, text: str) -> bool:
        """Check if response clearly identifies as AI-generated"""
        attribution_indicators = [
            "ai", "algorithm", "automated", "system", "morpheus",
            "sleep coach", "digital assistant"
        ]
        
        return any(indicator in text.lower() for indicator in attribution_indicators)
    
    def _explains_decision_factors(self, text: str, decision_factors: Dict[str, Any]) -> bool:
        """Check if key decision factors are explained"""
        if not decision_factors:
            return True
        
        factors_mentioned = 0
        for factor in decision_factors.keys():
            if factor.lower() in text.lower():
                factors_mentioned += 1
        
        return factors_mentioned >= len(decision_factors) * 0.5  # At least 50% of factors mentioned
    
    def _detect_privacy_violations(self, text: str) -> List[str]:
        """Detect potential privacy violations in text"""
        violations = []
        
        for category, patterns in self.privacy_sensitive_data.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    violations.append(f"Potential {category.replace('_', ' ')} exposure detected")
        
        return violations
    
    def _follows_data_minimization(self, user_data: Dict[str, Any]) -> bool:
        """Check if data collection follows minimization principle"""
        essential_fields = {
            "sleep_duration", "bedtime", "wake_time", "sleep_quality",
            "awakenings", "user_id", "date"
        }
        
        if not user_data:
            return True
        
        collected_fields = set(user_data.keys())
        unnecessary_fields = collected_fields - essential_fields
        
        return len(unnecessary_fields) <= 3  # Allow some flexibility
    
    def _has_appropriate_consent_language(self, text: str) -> bool:
        """Check for appropriate consent and privacy language"""
        consent_indicators = [
            "with your permission", "you can opt out", "data usage",
            "privacy", "consent", "your choice", "control"
        ]
        
        return any(indicator in text.lower() for indicator in consent_indicators)
    
    def _handles_sensitive_data(self, user_data: Dict[str, Any]) -> bool:
        """Check if user data contains sensitive information"""
        sensitive_fields = [
            "medical_conditions", "medications", "mental_health",
            "personal_notes", "location", "financial_info"
        ]
        
        return any(field in user_data for field in sensitive_fields)
    
    def _mentions_security(self, text: str) -> bool:
        """Check if response mentions security measures"""
        security_indicators = [
            "secure", "encrypted", "protected", "safe", "security",
            "confidential", "privacy", "safeguarded"
        ]
        
        return any(indicator in text.lower() for indicator in security_indicators)
    
    def _mentions_user_rights(self, text: str) -> bool:
        """Check if response mentions user data rights"""
        rights_indicators = [
            "delete", "modify", "access", "export", "control",
            "rights", "manage", "update", "remove"
        ]
        
        return any(indicator in text.lower() for indicator in rights_indicators)

# Global instance for use across the application
responsible_ai = ResponsibleAIMiddleware()