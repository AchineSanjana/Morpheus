from typing import Dict, Any, List

from app.responsible_ai import responsible_ai


def get_status() -> Dict[str, Any]:
    try:
        return {
            "enabled": True,
            "version": "1.0.0",
            "features": {
                "fairness_checks": True,
                "transparency_tracking": True,
                "ethical_data_handling": True,
                "bias_detection": True,
                "inclusive_language": True,
            },
            "status": "operational",
        }
    except Exception as e:
        return {"enabled": False, "error": str(e)[:100]}


async def validate(
    *,
    text: str,
    action_type: str,
    user_context: Dict[str, Any],
    data_sources: List[str],
    decision_factors: Dict[str, Any],
) -> Dict[str, Any]:
    results = await responsible_ai.comprehensive_check(
        text=text,
        action_type=action_type,
        user_context=user_context,
        data_sources=data_sources,
        decision_factors=decision_factors,
    )

    # Serialize for JSON response
    serialized: Dict[str, Any] = {}
    for check_type, check_result in results.items():
        serialized[check_type] = {
            "passed": getattr(check_result, "passed", False),
            "risk_level": getattr(getattr(check_result, "risk_level", None), "value", None)
            or str(getattr(check_result, "risk_level", "")),
            "category": getattr(check_result, "category", check_type),
            "message": getattr(check_result, "message", ""),
            "suggestions": getattr(check_result, "suggestions", []),
            "metadata": getattr(check_result, "metadata", {}) or {},
        }

    return serialized


def get_guidelines() -> Dict[str, Any]:
    # Static guidelines; mirrors previous implementation
    return {
        "fairness": {
            "principle": "Ensure AI responses are fair and unbiased across all user demographics",
            "guidelines": [
                "Use inclusive language that considers diverse backgrounds",
                "Avoid stereotyping based on age, gender, culture, or socioeconomic status",
                "Provide alternatives for users with different abilities",
                "Offer both free and accessible solutions alongside premium options",
                "Acknowledge individual differences in responses",
            ],
            "examples": {
                "good": "Consider gentle exercises that work within your current abilities",
                "bad": "Just do these exercises - they're easy for everyone",
            },
        },
        "transparency": {
            "principle": "Be transparent about AI decision-making and data usage",
            "guidelines": [
                "Explain how recommendations were generated",
                "Disclose what data sources were used",
                "Acknowledge AI limitations and uncertainty",
                "Clearly identify AI-generated content",
                "Mention when human professional help is recommended",
            ],
            "examples": {
                "good": "Based on your 7 nights of sleep data, I noticed your bedtime varies by 2+ hours...",
                "bad": "You should change your bedtime routine",
            },
        },
        "ethical_data_handling": {
            "principle": "Protect user privacy and handle data ethically",
            "guidelines": [
                "Minimize data collection to essential sleep-related information",
                "Protect sensitive personal information",
                "Inform users about their data rights",
                "Ensure data security and confidentiality",
                "Obtain appropriate consent for data usage",
            ],
            "examples": {
                "good": "Your sleep data is securely stored and you can delete it anytime",
                "bad": "Sharing personal medical details in responses",
            },
        },
    }


def get_audit_log(*, limit: int, user_id: str) -> Dict[str, Any]:
    # Placeholder for future storage-backed audit log
    return {
        "message": "Audit logging would be implemented with proper admin authentication",
        "structure": {
            "timestamp": "ISO datetime",
            "user_id": "User identifier",
            "agent": "Which agent was used",
            "check_results": "Responsible AI check results",
            "risk_level": "Overall risk assessment",
            "action_taken": "Any corrective actions",
        },
        "note": "Full audit logging requires additional security and storage infrastructure",
        "limit": limit,
    }
