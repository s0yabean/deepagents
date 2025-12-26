import operator
from typing import Annotated, List, TypedDict, Optional, Dict, Any, NotRequired

from langchain.agents.middleware.types import AgentMiddleware

class Slide(TypedDict):
    slide_number: int
    type: str  # 'hook', 'content', 'cta'
    text: str
    image_path: str
    visual_notes: Optional[str]

class AgentState(TypedDict):
    # Input
    topic: str
    project_id: str
    
    # Config (Loaded from project_id)
    slide_count: int
    tone: str
    font_style: str
    
    # Working Memory
    generated_hooks: List[str]
    selected_hook: str
    slides: List[Slide]
    
    # Output
    drive_folder_link: str
    logs: Annotated[List[str], operator.add]
