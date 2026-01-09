import operator
from typing import Annotated, List, Optional, Dict, Any
from typing_extensions import TypedDict, NotRequired

from langchain.agents.middleware.types import AgentMiddleware

class Slide(TypedDict):
    slide_number: int
    type: str  # 'hook', 'content', 'cta'
    text: str
    image_path: str
    visual_notes: Optional[str]

ALLOWED_STATUSES = ["pending", "in_progress", "completed"]

def merge_todos(existing: Any, new_updates: Any) -> List[Dict[str, Any]]:
    """Strict merge reducer for todos."""
    if existing is None: existing = []
    if new_updates is None: return existing
    
    if not isinstance(new_updates, list):
        raise ValueError(f"Invalid todo update: Expected a list, got {type(new_updates).__name__}.")

    if not existing:
        return new_updates
        
    merged = []
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
            merged_item = new_item.copy()
            old_status = old_item.get('status', 'pending')
            new_status = new_item.get('status', 'pending')
            
            if old_status == "completed" and new_status != "completed":
                merged_item['status'] = "completed"
            elif old_status == "in_progress" and new_status == "pending":
                merged_item['status'] = "in_progress"
            
            merged.append(merged_item)
        else:
            merged.append(new_item)
            
    return merged

class AgentState(TypedDict):
    # Input
    topic: str
    project_id: str
    
    # Config (Loaded from project_id)
    slide_count: int
    tone: str
    font_style: str
    require_human_review: bool
    user_requirements: List[str]
    
    # Working Memory
    generated_hooks: List[str]
    selected_hook: str
    slides: List[Slide]
    
    # Planning
    todos: Annotated[List[Dict[str, Any]], merge_todos]
    
    # Output
    drive_folder_link: str
    logs: Annotated[List[str], operator.add]
