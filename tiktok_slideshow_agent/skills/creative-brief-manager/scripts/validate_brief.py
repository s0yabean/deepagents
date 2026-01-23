"""
Creative Brief Validator - Validates Creative Brief JSON structure and required fields.

Ensures briefs meet the minimum requirements before storage and use.
"""

from typing import Dict, Any, List, Tuple
import json


REQUIRED_FIELDS = {
    "format_id": str,
    "tone": str,
}

OPTIONAL_FIELDS = {
    "topic_focus": str,
    "target_audience": str,
    "key_messaging": list,
    "image_arc": dict,
    "narrative_arc": dict,
    "product_positioning": dict,
    "slides": list,
    "font_style": str,
    "hooks": list,
}

ALL_VALID_FIELDS = list(REQUIRED_FIELDS.keys()) + list(OPTIONAL_FIELDS.keys())


def validate_creative_brief(brief_data: Any) -> Tuple[bool, List[str]]:
    """
    Validate a Creative Brief JSON structure.

    Args:
        brief_data: The data to validate (dict or JSON string)

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    # Parse JSON if string
    if isinstance(brief_data, str):
        try:
            brief_data = json.loads(brief_data)
        except json.JSONDecodeError as e:
            return False, [f"Invalid JSON: {str(e)}"]

    # Must be dict
    if not isinstance(brief_data, dict):
        return False, ["Brief must be a dictionary/JSON object"]

    # Check required fields
    for field, expected_type in REQUIRED_FIELDS.items():
        if field not in brief_data:
            errors.append(f"Missing required field: '{field}'")
        elif not isinstance(brief_data[field], expected_type):
            errors.append(
                f"Field '{field}' must be type {expected_type.__name__}, got {type(brief_data[field]).__name__}"
            )

    # Check optional fields types
    for field, expected_type in OPTIONAL_FIELDS.items():
        if field in brief_data and not isinstance(brief_data[field], expected_type):
            errors.append(
                f"Optional field '{field}' should be type {expected_type.__name__}, got {type(brief_data[field]).__name__}"
            )

    # Check for unknown fields
    for field in brief_data.keys():
        if field not in ALL_VALID_FIELDS:
            errors.append(f"Unknown field: '{field}' - will be ignored")

    return len(errors) == 0, errors


def validate_brief_for_agent(
    agent_type: str, brief_data: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    """
    Validate that a Creative Brief has fields needed by a specific agent.

    Args:
        agent_type: One of 'hook-agent', 'content-strategist', 'visual-designer', 'qa-specialist'
        brief_data: The Creative Brief to validate

    Returns:
        Tuple of (has_required_fields, list_of_missing_fields)
    """
    agent_field_requirements = {
        "hook-agent": ["hooks", "tone", "target_audience"],
        "content-strategist": ["narrative_arc", "key_messaging", "tone"],
        "visual-designer": ["image_arc", "tone", "format_id"],
        "qa-specialist": ["slides", "format_id", "tone"],
        "publisher": ["slides", "format_id"],
        "creative-director": ["format_id", "tone", "target_audience"],
    }

    required = agent_field_requirements.get(agent_type, [])
    missing = [f for f in required if f not in brief_data or brief_data[f] is None]

    return len(missing) == 0, missing


def get_brief_schema() -> Dict[str, Any]:
    """
    Get the complete JSON schema for Creative Brief validation.

    Returns:
        Dict representing the JSON schema
    """
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Creative Brief",
        "description": "Creative Brief structure for multi-agent content creation",
        "type": "object",
        "required": list(REQUIRED_FIELDS.keys()),
        "properties": {
            "format_id": {
                "type": "string",
                "description": "Content format identifier (e.g., 'transformation-story', 'how-to')",
            },
            "tone": {
                "type": "string",
                "description": "Content tone (e.g., 'energetic', 'professional', 'casual')",
            },
            "topic_focus": {
                "type": "string",
                "description": "Main topic or focus area",
            },
            "target_audience": {
                "type": "string",
                "description": "Target audience description",
            },
            "key_messaging": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of key messages to convey",
            },
            "image_arc": {
                "type": "object",
                "description": "Visual progression guidance",
            },
            "narrative_arc": {
                "type": "object",
                "description": "Story structure guidance",
            },
            "product_positioning": {
                "type": "object",
                "description": "How to handle promotional content",
            },
            "slides": {"type": "array", "description": "Slide definitions"},
            "font_style": {"type": "string", "description": "Font style specification"},
            "hooks": {"type": "array", "description": "Hook strategy guidelines"},
        },
    }

    return schema


# Example usage for testing
if __name__ == "__main__":
    valid_brief = {
        "format_id": "transformation-story",
        "tone": "energetic",
        "topic_focus": "fitness",
        "target_audience": "young professionals",
    }

    is_valid, errors = validate_creative_brief(valid_brief)
    print(f"Valid brief: {is_valid}")
    if errors:
        print(f"Errors: {errors}")

    # Test hook-agent requirements
    is_valid, missing = validate_brief_for_agent("hook-agent", valid_brief)
    print(f"Has hook-agent fields: {is_valid}")
    if missing:
        print(f"Missing: {missing}")
