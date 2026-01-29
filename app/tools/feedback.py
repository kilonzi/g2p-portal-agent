from langchain_core.tools import tool
from typing import Literal, Dict, Any
from datetime import datetime
from loguru import logger
import json
import os

MEMORY_ROOT = "./.memory"

def _get_user_pref_path(user_id: str) -> str:
    path = os.path.join(MEMORY_ROOT, "users", user_id, "preferences.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path

def _get_global_suggestion_path(suggestion_id: str) -> str:
    path = os.path.join(MEMORY_ROOT, "global", "lessons", "pending", f"{suggestion_id}.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path

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
    
    file_path = _get_user_pref_path(user_id)
    
    # Load existing or create new
    current_prefs = {}
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                current_prefs = json.load(f)
        except Exception:
            pass # Start fresh if corrupted
            
    # Update
    current_prefs[category] = {
        "text": preference,
        "timestamp": datetime.now().isoformat()
    }
    
    # Save
    with open(file_path, "w") as f:
        json.dump(current_prefs, f, indent=2)
    
    return f"""✅ **Preference Saved**

I've updated your personal settings:
- **Category**: {category.replace('_', ' ').title()}
- **Preference**: {preference}

This applies to **your conversations only** and takes effect immediately.
(Saved to: `{file_path}`)

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
    suggestion_id = f"GS-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    logger.info(f"Global suggestion {suggestion_id} submitted by user {user_id}: {suggestion}")
    
    data = {
        "id": suggestion_id,
        "suggestion": suggestion,
        "category": category,
        "submitted_by": user_id,
        "status": "pending_review",
        "timestamp": datetime.now().isoformat()
    }
    
    file_path = _get_global_suggestion_path(suggestion_id)
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)
    
    return f"""💡 **Global Suggestion Submitted**

Thank you for helping improve the system! Your suggestion:
- **ID**: {suggestion_id}
- **Category**: {category.replace('_', ' ').title()}
- **Suggestion**: {suggestion}

**Status**: 🔍 Pending Admin Review
(Saved to: `{file_path}`)

Global improvements are reviewed by administrators before being applied to all users."""


@tool
async def get_user_preferences(user_id: str) -> str:
    """
    Retrieves the current user's saved preferences.
    
    Args:
        user_id: User identifier
    """
    file_path = _get_user_pref_path(user_id)
    if not os.path.exists(file_path):
        return """### 👤 Your Preferences
        
No custom preferences set yet. 
To set one, say: "I prefer [preference]"."""

    with open(file_path, "r") as f:
        prefs = json.load(f)
        
    output = "### 👤 Your Preferences\n\n"
    for cat, data in prefs.items():
        output += f"**{cat.replace('_', ' ').title()}**\n"
        output += f"- {data['text']}\n\n"
        
    output += "\nTo update, say: \"I prefer [preference]\"."
    return output

def get_global_preferences() -> str:
    """
    Reads ALL approved global lessons from disk to inject into System Prompt.
    Not an async tool because it's used at startup/initialization.
    """
    approved_dir = os.path.join(MEMORY_ROOT, "global", "lessons", "approved")
    
    if not os.path.exists(approved_dir):
        return "No global lessons approved yet."
        
    lessons = []
    try:
        for filename in os.listdir(approved_dir):
            if filename.endswith(".json"):
                with open(os.path.join(approved_dir, filename), "r") as f:
                    data = json.load(f)
                    # Format: "* [Category] Suggestion (Contributor)"
                    line = f"* [{data.get('category', 'General')}] {data.get('suggestion', '')}"
                    lessons.append(line)
    except Exception as e:
        logger.error(f"Failed to load global lessons: {e}")
        return "Error loading global lessons."
        
    if not lessons:
        return "No global lessons approved yet."
        
    return "\n".join(lessons)
