from typing import Annotated, List, TypedDict, Optional, Any, NotRequired, Dict
import operator

class AgentState(TypedDict):
    """State schema for the QMDJ agent."""
    
    # QMDJ Specific Context
    chart_json: NotRequired[str]
    energy_json: NotRequired[str]
    current_question: NotRequired[str]
    
    # Analysis results
    specialist_findings: NotRequired[List[Dict[str, Any]]]
    final_reading: NotRequired[str]
    
    # Planning (Explicitly defined to handle concurrent updates)
    # Use a reducer that keeps the last update (y) to prevent InvalidUpdateError
ALLOWED_STATUSES = ["pending", "in_progress", "completed"]

def merge_todos(existing: Any, new_updates: Any) -> List[Dict[str, Any]]:
    """
    Smart merge reducer for todos with task attribution and strict validation.
    
    Strategy:
    1. Validate types strictly. Raise ValueError for garbage to provide feedback.
    2. Match items by 'content' AND 'owner' to allow agents to have their own "silos".
    3. Preserve progress (completed > in_progress > pending).
    4. Enforce status enums: pending, in_progress, completed.
    """
    # Initialize if None
    if existing is None: existing = []
    if new_updates is None: return existing
    
    # Strict Type Validation
    if not isinstance(new_updates, list):
        raise ValueError(f"Invalid todo update: Expected a list, got {type(new_updates).__name__}. "
                         "Please provide a list of dictionaries: [{'content': '...', 'status': '...', 'owner': '...'}]")

    if not existing:
        # Validate items in new list
        for item in new_updates:
            if not isinstance(item, dict) or 'content' not in item:
                raise ValueError("Invalid todo item: Each item must be a dictionary with at least a 'content' key.")
            status = item.get('status', 'pending')
            if status not in ALLOWED_STATUSES:
                raise ValueError(f"Invalid status '{status}'. Must be one of: {', '.join(ALLOWED_STATUSES)}")
        return new_updates
        
    merged = []
    # Create a lookup for existing items by (content, owner)
    existing_lookup = { (item.get('content'), item.get('owner')): item for item in existing if isinstance(item, dict) }
    
    for new_item in new_updates:
        if not isinstance(new_item, dict) or 'content' not in new_item:
            raise ValueError("Invalid todo item: Each item must be a dictionary with a 'content' key.")
            
        status = new_item.get('status', 'pending')
        if status not in ALLOWED_STATUSES:
            raise ValueError(f"Invalid status '{status}'. Must be one of: {', '.join(ALLOWED_STATUSES)}")

        key = (new_item.get('content'), new_item.get('owner'))
        old_item = existing_lookup.get(key)
        
        if old_item:
            # Merge status safely
            merged_item = new_item.copy()
            old_status = old_item.get('status', 'pending')
            new_status = new_item.get('status', 'pending')
            
            # Status priority: completed > in_progress > pending
            if old_status == "completed" and new_status != "completed":
                merged_item['status'] = "completed"
            elif old_status == "in_progress" and new_status == "pending":
                merged_item['status'] = "in_progress"
            
            merged.append(merged_item)
        else:
            # New task or content/owner changed
            merged.append(new_item)
            
    return merged

    # Planning (Explicitly defined to handle concurrent updates)
    # Use smart merge reducer
    todos: Annotated[List[Dict[str, Any]], merge_todos]
