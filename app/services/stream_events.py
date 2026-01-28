"""
Simplified, frontend-friendly streaming events.

Event Types:
- thinking: AI reasoning, decisions, planning
- action: Tool execution, specialist delegation
- content: Final message content
- meta: Control signals (start, end, error, title)

Each event has:
- event_id: Unique identifier
- visibility: "minimal", "standard", or "advanced"
- display_*: Pre-formatted display content
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List


def generate_event_id() -> str:
    """Generate unique event ID."""
    return f"evt_{uuid.uuid4().hex[:12]}"


def format_sse_event(event_type: str, data: Dict[str, Any]) -> str:
    """
    Format event as standard SSE with UTF-8 emojis.
    
    Returns:
        event: <type>
        data: <json>
        
    """
    # Ensure UTF-8 emojis are preserved
    json_data = json.dumps(data, ensure_ascii=False)
    return f"event: {event_type}\ndata: {json_data}\n\n"


# ===== CORE EVENT EMITTERS =====

def emit_stream_start(
    stream_id: str,
    expected_events: Optional[List[str]] = None,
    estimated_duration_ms: Optional[int] = None
) -> str:
    """Send stream manifest before streaming begins."""
    data = {
        "event_id": generate_event_id(),
        "stream_id": stream_id,
        "expected_events": expected_events or ["action", "content", "meta"],
        "transparency_support": ["minimal", "standard", "advanced"],
        "timestamp": datetime.now().isoformat()
    }
    if estimated_duration_ms:
        data["estimated_duration_ms"] = estimated_duration_ms
    return format_sse_event("meta", data)


def emit_thinking(
    thinking_type: str,
    summary: str,
    details: Optional[Dict[str, Any]] = None,
    visibility: str = "advanced"
) -> str:
    """
    Emit AI reasoning/decision event.
    
    Args:
        thinking_type: "decision", "planning", "analyzing"
        summary: Brief description for display
        details: Full details for advanced mode
        visibility: "minimal", "standard", "advanced"
    """
    data = {
        "event_id": generate_event_id(),
        "type": thinking_type,
        "visibility": visibility,
        "display_summary": summary,
        "timestamp": datetime.now().isoformat()
    }
    if details:
        data["details"] = details
    return format_sse_event("thinking", data)


def emit_action(
    action_type: str,
    display_title: str,
    display_icon: str,
    status: str,
    action_id: Optional[str] = None,
    display_summary: Optional[str] = None,
    visibility: str = "standard",
    raw_data: Optional[Dict[str, Any]] = None
) -> str:
    """
    Emit tool/specialist action event.
    
    Args:
        action_type: "tool", "delegation", "api_call"
        display_title: "Fetching Gene Information", "Genetic Discovery Specialist"
        display_icon: "🔧", "🧬"
        status: "running", "success", "failed"
        action_id: Unique ID for tracking (tool_id, subagent_id)
        display_summary: Human-readable summary
        visibility: Which mode should show this
        raw_data: Full details for advanced mode
    """
    data = {
        "event_id": generate_event_id(),
        "type": action_type,
        "visibility": visibility,
        "display_title": display_title,
        "display_icon": display_icon,
        "display_status": status,
        "timestamp": datetime.now().isoformat()
    }
    
    if action_id:
        data["action_id"] = action_id
    if display_summary:
        data["display_summary"] = display_summary
    if raw_data:
        data["raw_data"] = raw_data
    
    return format_sse_event("action", data)


def emit_content(
    text: str,
    is_final: bool = False,
    source: Optional[str] = None,
    visibility: str = "minimal"
) -> str:
    """
    Emit message content.
    
    Args:
        text: The actual content
        is_final: Is this the final complete message?
        source: Where it came from (for debugging)
        visibility: Always "minimal" for content
    """
    data = {
        "event_id": generate_event_id(),
        "visibility": visibility,
        "text": text,
        "is_final": is_final,
        "timestamp": datetime.now().isoformat()
    }
    if source:
        data["source"] = source
    return format_sse_event("content", data)


def emit_meta(
    meta_type: str,
    payload: Optional[Dict[str, Any]] = None
) -> str:
    """
    Emit control/metadata signal.
    
    Args:
        meta_type: "title", "end", "error"
        payload: Type-specific data
    """
    data = {
        "event_id": generate_event_id(),
        "type": meta_type,
        "timestamp": datetime.now().isoformat()
    }
    if payload:
        data.update(payload)
    return format_sse_event("meta", data)


# ===== SIMPLIFIED TOOL/SUBAGENT MAPPINGS =====

TOOL_INFO = {
    "get_gene_dossier": {
        "icon": "📊",
        "title": "Fetching Gene Information",
        "description": "Retrieves comprehensive gene data"
    },
    "get_protein_features": {
        "icon": "🧬",
        "title": "Analyzing Protein Features",
        "description": "Analyzes domains and motifs"
    },
    "fetch_alphafold_access": {
        "icon": "🔮",
        "title": "Getting AlphaFold Structure",
        "description": "Retrieves predicted structure"
    },
    "check_clinvar_status": {
        "icon": "🩺",
        "title": "Checking ClinVar",
        "description": "Validates variant pathogenicity"
    },
    "align_isoforms": {
        "icon": "🔀",
        "title": "Aligning Isoforms",
        "description": "Compares splice variants"
    },
    "map_variant_to_canonical": {
        "icon": "🗺️",
        "title": "Mapping Variant",
        "description": "Maps to canonical sequence"
    },
    "fetch_pdb_file": {
        "icon": "📥",
        "title": "Downloading PDB Structure",
        "description": "Fetches experimental structure"
    },
    "run_python_analysis": {
        "icon": "🐍",
        "title": "Running Custom Analysis",
        "description": "Executes specialized code"
    },
    "task": {
        "icon": "🔧",
        "title": "Delegating to Specialist",
        "description": "Assigning to domain expert"
    }
}

SUBAGENT_INFO = {
    "genetic-discovery-agent": {
        "icon": "🧬",
        "title": "Genetic Discovery Specialist"
    },
    "structural-biology-agent": {
        "icon": "🔬",
        "title": "Structural Biology Expert"
    },
    "variant-analyst-agent": {
        "icon": "🩺",
        "title": "Variant Analysis Specialist"
    }
}


def get_tool_info(tool_name: str) -> Dict[str, str]:
    """Get display info for a tool."""
    return TOOL_INFO.get(tool_name, {
        "icon": "🔧",
        "title": tool_name,
        "description": f"Executes {tool_name}"
    })


def get_subagent_info(subagent_type: str) -> Dict[str, str]:
    """Get display info for a subagent."""
    return SUBAGENT_INFO.get(subagent_type, {
        "icon": "🤖",
        "title": subagent_type
    })


def format_args_summary(args: Dict[str, Any]) -> str:
    """Convert args to human-readable string."""
    parts = []
    for key, value in args.items():
        if key in ["gene_symbol", "gene"]:
            parts.append(f"Gene: {value}")
        elif key in ["uniprot_id", "protein_id"]:
            parts.append(f"Protein: {value}")
        elif key == "variant":
            parts.append(f"Variant: {value}")
        elif key not in ["description", "task_description", "subagent_type"]:
            parts.append(f"{key}: {value}")
    return " | ".join(parts) if parts else ""
