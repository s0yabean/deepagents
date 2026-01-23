"""
Creative Brief Manager - Core brief storage and retrieval functionality.

This module provides efficient context-aware access to Creative Briefs.
Instead of passing full 2000-char JSON to every agent, store once and retrieve
only the fields needed for each specific task.

Usage Pattern:
    1. Store: store_creative_brief(brief_json) -> brief_id
    2. Reference: Pass brief_id in task descriptions
    3. Retrieve: get_brief_fields(brief_id, ["field1", "field2"]) -> filtered JSON
"""

import hashlib
import json
from typing import Dict, Any, List, Optional
from datetime import datetime


def generate_brief_id(brief_data: Dict[str, Any]) -> str:
    """Generate unique ID for a Creative Brief based on content hash and timestamp."""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    content_hash = hashlib.md5(
        json.dumps(brief_data, sort_keys=True).encode()
    ).hexdigest()[:8]
    return f"brief_{timestamp}_{content_hash}"


def store_creative_brief(
    brief_data: Dict[str, Any], storage: Optional[Dict[str, Dict]] = None
) -> Dict[str, Any]:
    """
    Store a Creative Brief and return its reference ID.

    Args:
        brief_data: The Creative Brief JSON to store
        storage: Optional external storage dict (for integration with AgentState)

    Returns:
        Dict with brief_id and summary
    """
    brief_id = generate_brief_id(brief_data)

    brief_summary = {
        "brief_id": brief_id,
        "format_id": brief_data.get("format_id", "unknown"),
        "topic_focus": brief_data.get("topic_focus", "N/A"),
        "image_arc_type": brief_data.get("image_arc", {}).get("type", "unknown")
        if isinstance(brief_data.get("image_arc"), dict)
        else "unknown",
        "tone": brief_data.get("tone", "unknown"),
        "slide_count": len(brief_data.get("slides", []))
        if isinstance(brief_data.get("slides"), list)
        else "N/A",
        "stored_at": datetime.utcnow().isoformat(),
    }

    if storage is not None:
        storage[brief_id] = {
            "full_brief": brief_data,
            "summary": brief_summary,
            "stored_at": datetime.utcnow().isoformat(),
        }

    return {"brief_id": brief_id, "summary": brief_summary, "stored": True}


def get_brief_fields(brief_data: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
    """
    Retrieve only specified fields from a Creative Brief.

    This is the key function for context efficiency - agents only get
    what they need, not the full 2000-char JSON.

    Args:
        brief_data: The full Creative Brief
        fields: List of field names to extract

    Returns:
        Dict containing only requested fields
    """
    if not fields:
        return {}

    result = {}
    for field in fields:
        if field in brief_data:
            result[field] = brief_data[field]

    return result


def get_creative_brief_summary(brief_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get a concise summary of a Creative Brief for task context.

    Use this when agent needs high-level understanding without full details.

    Args:
        brief_data: The full Creative Brief

    Returns:
        Summary dict with key fields
    """
    summary = {
        "format_id": brief_data.get("format_id", "unknown"),
        "tone": brief_data.get("tone", "unknown"),
        "target_audience": brief_data.get("target_audience", "general"),
        "key_messaging": brief_data.get("key_messaging", [])[:2],  # Top 2 messages
        "image_style_notes": brief_data.get("image_arc", {}).get("notes", "standard")
        if isinstance(brief_data.get("image_arc"), dict)
        else "standard",
    }

    return summary


def get_creative_brief_full(brief_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get the complete Creative Brief.

    Use this when agent needs full context (rare - most agents need only specific fields).

    Args:
        brief_data: The full Creative Brief

    Returns:
        Complete brief dict
    """
    return brief_data


def create_brief_from_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a Creative Brief from AgentState fields.

    This is the integration point - converts existing state fields into
    a structured brief that can be stored and referenced.

    Args:
        state: AgentState dict with topic, tone, slide_count, etc.

    Returns:
        Structured Creative Brief dict
    """
    brief = {
        "format_id": f"slides_{state.get('slide_count', 10)}_frames",
        "tone": state.get("tone", "professional"),
        "font_style": state.get("font_style", "modern"),
        "topic_focus": state.get("topic", "general"),
        "target_audience": "general",
        "key_messaging": state.get("user_requirements", [])[:3],
        "image_arc": {
            "type": "progressive",
            "notes": "Follow consistent visual style across slides",
        },
        "slides": [],
        "created_from_state": True,
        "original_state_keys": list(state.keys()),
    }

    return brief


# Example usage for testing
if __name__ == "__main__":
    sample_brief = {
        "format_id": "transformation-story",
        "tone": "energetic",
        "topic_focus": "fitness motivation",
        "target_audience": "young professionals",
        "key_messaging": ["Transform your body", "Build lasting habits"],
        "image_arc": {"type": "before-after", "notes": "Show transformation journey"},
    }

    result = store_creative_brief(sample_brief)
    print(f"Brief ID: {result['brief_id']}")
    print(f"Summary: {result['summary']}")

    fields = get_brief_fields(sample_brief, ["tone", "image_arc"])
    print(f"Filtered fields: {fields}")
