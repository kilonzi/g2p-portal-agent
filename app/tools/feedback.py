from langchain_core.tools import tool
from typing import Literal, Dict, Any
from datetime import datetime
from loguru import logger
import json


@tool
async def record_user_preference(
    category: Literal["response_style", "technical_depth", "format_preference", "custom"],
    preference: str,
    user_id: str
) -> str:
    """
    Records a PERSONAL preference for the current user.
    These apply immediately and only affect this user.
    
    Args:
        category: Type of preference
        preference: The preference text (e.g., "Brief responses preferred")
        user_id: User identifier
    
    Examples:
        - category="response_style", preference="Keep responses under 100 words"
        - category="technical_depth", preference="Expert-level explanations"
    """
    logger.info(f"Recording personal preference for user {user_id}: {preference}")
    
    # In a real implementation, store in LangGraph memory:
    # store.put(("users", user_id, "preferences"), category, {"text": preference, "timestamp": datetime.now()})
    
    return f"""✅ **Preference Saved**

I've updated your personal settings:
- **Category**: {category.replace('_', ' ').title()}
- **Preference**: {preference}

This applies to **your conversations only** and takes effect immediately.

You can view all your preferences by asking "What are my preferences?" or update them anytime."""


@tool
async def suggest_global_improvement(
    category: Literal["response_accuracy", "citation_rules", "explanation_style", "domain_expertise"],
    suggestion: str,
    user_id: str
) -> str:
    """
    Submits a suggestion for GLOBAL system improvement.
    These are reviewed by admins before being applied to all users.
    
    Args:
        category: Type of improvement
        suggestion: The suggested behavior change
        user_id: User who submitted (for attribution)
    
    Examples:
        - "Always cite AlphaFold pLDDT confidence scores"
        - "Mention evolutionary conservation when discussing domains"
    """
    # Import store (can't be a parameter as it breaks Gemini function schema)
    from app.agents.orchestrator import store
    
    suggestion_id = f"GS-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    logger.info(f"Global suggestion {suggestion_id} submitted by user {user_id}: {suggestion}")
    
    # Store as PENDING in memory store
    namespace = ("global", "lessons", "pending")
    suggestion_data = {
        "suggestion": suggestion,
        "category": category,
        "submitted_by": user_id,
        "status": "pending_review",
        "timestamp": datetime.now().isoformat()
    }
    
    # Write to /memories/global/lessons/pending/{suggestion_id}
    await store.aput(namespace, suggestion_id, suggestion_data)
    
    logger.info(f"Stored pending suggestion {suggestion_id} at namespace {namespace}")
    
    return f"""💡 **Global Suggestion Submitted**

Thank you for helping improve the system! Your suggestion:
- **ID**: {suggestion_id}
- **Category**: {category.replace('_', ' ').title()}
- **Suggestion**: {suggestion}

**Status**: 🔍 Pending Admin Review

Global improvements are reviewed by administrators before being applied to ensure quality and prevent misuse. If approved, this will benefit all users. You'll be credited as the contributor!"""


@tool
async def get_user_preferences(user_id: str) -> str:
    """
    Retrieves the current user's saved preferences.
    
    Args:
        user_id: User identifier
    """
    # In real implementation:
    # prefs = store.get(("users", user_id, "preferences"))
    
    # Mock response for now
    return """### 👤 Your Preferences

**Response Style**
- Keep responses concise (under 150 words)

**Technical Level**
- Expert-level explanations

**Custom Instructions**
- None set yet

To update, say: "I prefer [preference]" or "From now on, [instruction]"
To reset, say: "Clear my preferences" """
