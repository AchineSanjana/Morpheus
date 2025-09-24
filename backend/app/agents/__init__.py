# app/agents/__init__.py
from typing import Any, Dict, Optional, TypedDict, List
import logging

# Import the responsible AI middleware
try:
    from app.responsible_ai import responsible_ai, ResponsibleAICheck, RiskLevel
except ImportError:
    # Fallback if responsible_ai module is not available
    responsible_ai = None
    ResponsibleAICheck = None
    RiskLevel = None

logger = logging.getLogger(__name__)

class AgentContext(Dict[str, Any]):
    """
    Shared context passed into agents.
    Example keys:
        {
          "user": {"id": "...", "email": "..."},
          "logs": [...],          # recent sleep logs
          "analysis": {...}       # precomputed metrics
        }
    """

class AgentResponse(TypedDict, total=False):
    """
    Standard format returned by every agent.
    Fields:
        agent: which agent handled it ("coach", "analytics", etc.)
        text: plain response string
        data: optional structured payload (dict) with extra info
        responsible_ai_checks: results of responsible AI validation
        responsible_ai_passed: whether all responsible AI checks passed
        responsible_ai_risk_level: overall risk level from responsible AI checks
    """
    agent: str
    text: str
    data: Dict[str, Any]
    responsible_ai_checks: Dict[str, Any]
    responsible_ai_passed: bool
    responsible_ai_risk_level: str

class BaseAgent:
    """
    All agents inherit from this.
    They must implement an async handle() method.
    Now includes responsible AI validation for all responses.
    """
    name: str = "base"

    def __init__(self):
        self.enable_responsible_ai = True  # Can be disabled for testing
        self.action_type = "general_response"  # Override in subclasses

    async def handle(
        self,
        message: str,
        ctx: Optional[AgentContext] = None
    ) -> AgentResponse:
        """
        Main handler that wraps the agent's core logic with responsible AI checks
        """
        # Get the core response from the agent
        response = await self._handle_core(message, ctx)
        
        # Apply responsible AI checks if enabled
        if self.enable_responsible_ai and responsible_ai:
            responsible_ai_results = await self._apply_responsible_ai_checks(
                response, message, ctx or {}
            )
            
            # Add responsible AI results to response
            response["responsible_ai_checks"] = responsible_ai_results
            response["responsible_ai_passed"] = responsible_ai_results.get("overall", {}).get("passed", True)
            response["responsible_ai_risk_level"] = responsible_ai_results.get("overall", {}).get("risk_level", "low")
            
            # If critical issues found, modify response
            if response["responsible_ai_risk_level"] == "critical":
                response = await self._handle_critical_ai_issues(response, responsible_ai_results)
        
        return response

    async def _handle_core(
        self,
        message: str,
        ctx: Optional[AgentContext] = None
    ) -> AgentResponse:
        """
        Core agent logic - to be implemented by subclasses
        This replaces the old handle() method
        """
        raise NotImplementedError("Agent must implement _handle_core()")

    async def _apply_responsible_ai_checks(
        self,
        response: AgentResponse,
        original_message: str,
        ctx: AgentContext
    ) -> Dict[str, Any]:
        """
        Apply comprehensive responsible AI checks to the agent response
        """
        try:
            # Extract decision factors from the response data
            decision_factors = response.get("data", {}).get("decision_factors", {})
            
            # Data sources used (can be overridden by subclasses)
            data_sources = self._get_data_sources(ctx)
            
            # Run comprehensive responsible AI check
            checks = await responsible_ai.comprehensive_check(
                text=response["text"],
                action_type=self.action_type,
                user_context=ctx,
                data_sources=data_sources,
                decision_factors=decision_factors
            )
            
            # Convert to serializable format
            serializable_checks = {}
            for check_type, check_result in checks.items():
                serializable_checks[check_type] = {
                    "passed": check_result.passed,
                    "risk_level": check_result.risk_level.value if hasattr(check_result.risk_level, 'value') else str(check_result.risk_level),
                    "category": check_result.category,
                    "message": check_result.message,
                    "suggestions": check_result.suggestions,
                    "metadata": check_result.metadata or {}
                }
            
            return serializable_checks
            
        except Exception as e:
            logger.error(f"Error in responsible AI checks: {e}")
            return {
                "error": {
                    "passed": False,
                    "risk_level": "medium",
                    "category": "system_error",
                    "message": f"Responsible AI check failed: {str(e)}",
                    "suggestions": ["Manual review recommended"],
                    "metadata": {}
                }
            }

    async def _handle_critical_ai_issues(
        self,
        response: AgentResponse,
        responsible_ai_results: Dict[str, Any]
    ) -> AgentResponse:
        """
        Handle responses with critical responsible AI issues
        """
        # Collect all critical issues
        critical_issues = []
        suggestions = []
        
        for check_type, check_result in responsible_ai_results.items():
            if check_result.get("risk_level") == "critical":
                critical_issues.append(check_result.get("message", "Critical issue detected"))
                suggestions.extend(check_result.get("suggestions", []))
        
        # Modify response to address critical issues
        response["text"] = (
            "I apologize, but I need to modify my response to ensure it meets our responsible AI guidelines. "
            f"{response['text']}\n\n"
            "**Important Disclaimers:**\n"
            "- This is AI-generated educational guidance, not medical advice\n"
            "- Individual results may vary based on personal circumstances\n"
            "- Please consult healthcare providers for serious sleep disorders\n"
            "- Your privacy and data security are our top priorities\n"
            "- You have full control over your data and can modify or delete it anytime"
        )
        
        # Add metadata about the modification
        if "data" not in response:
            response["data"] = {}
        response["data"]["responsible_ai_modification"] = {
            "modified": True,
            "critical_issues": critical_issues,
            "modifications_made": suggestions
        }
        
        return response

    def _get_data_sources(self, ctx: AgentContext) -> List[str]:
        """
        Get list of data sources used - can be overridden by subclasses
        """
        sources = []
        if ctx.get("logs"):
            sources.append("user_sleep_logs")
        if ctx.get("user"):
            sources.append("user_profile")
        if ctx.get("analysis"):
            sources.append("sleep_analysis")
        return sources

    # Backward compatibility method
    async def handle_legacy(
        self,
        message: str,
        ctx: Optional[AgentContext] = None
    ) -> AgentResponse:
        """
        Legacy handle method for backward compatibility
        """
        return await self.handle(message, ctx)
